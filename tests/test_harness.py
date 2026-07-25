"""Test suite. Stdlib unittest, no dependencies:  python -m unittest discover tests -v

The point of these is threshold tuning. The sentinel and recovery policies are full of
numbers you will want to move while doing research, and most of them can be moved into a
configuration that quietly supervises nothing. These pin the behavior that must survive.
"""
from __future__ import annotations

import json
import os
import shutil
import stat
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from lightsout import detectors, harness1_intake, harness3_recovery, worker  # noqa: E402
from lightsout.config import load_config                                     # noqa: E402
from lightsout.llm import extract_json                                       # noqa: E402
from lightsout.state import Run                                              # noqa: E402
from lightsout.workspace import Workspace                                    # noqa: E402



def _rmtree(path):
    """Remove a tree containing a git repo on Windows.

    git marks objects in .git/objects read-only, and plain rmtree fails on them.
    `ignore_errors=True` hides that and silently leaks a repo per test -- after a few
    runs the temp directory is full of them and the suite slows to a crawl.
    """
    def _force(func, target, _exc):
        try:
            os.chmod(target, stat.S_IWRITE)
            func(target)
        except OSError:
            pass

    if sys.version_info >= (3, 12):
        shutil.rmtree(path, onexc=_force)
    else:
        shutil.rmtree(path, onerror=lambda f, t, e: _force(f, t, e))


GOOD = '''def solve(nums):
    total = 0
    for v in nums:
        total += v
    return total


def test_solve():
    assert solve([1, 2, 3]) == 6
'''


class TestDetectors(unittest.TestCase):
    """The deterministic half of Harness 2 -- these must not be fooled."""

    def test_clean_code_produces_no_signals(self):
        sigs, ceiling = detectors.run_all(
            GOOD, {"a.py": GOOD}, ["a.py"], "+" + GOOD,
            {"skipped": True, "returncode": 0}, "a.py")
        self.assertEqual(sigs, [], "clean code should not trip any detector")
        self.assertEqual(ceiling, 100)

    def test_not_implemented_forces_hard_halt(self):
        s = detectors.detect_stubs("def solve(x):\n    raise NotImplementedError\n")
        self.assertIsNotNone(s)
        self.assertLessEqual(s.severity, 45, "stub must fall under the hard floor")

    def test_todo_is_only_a_note_not_a_halt(self):
        s = detectors.detect_stubs("def solve(x):\n    # TODO: edge case\n    return x\n")
        self.assertIsNotNone(s)
        self.assertGreater(s.severity, 45, "a TODO alone should not halt the run")
        self.assertLess(s.severity, 70, "...but it should not pass clean either")

    def test_tests_that_cannot_fail(self):
        for src in ("def test_x():\n    assert True\n",
                    "def test_x():\n    pass\n"):
            self.assertIsNotNone(detectors.detect_weak_tests(src), src)

    def test_generation_loop(self):
        looped = "    # handled above\n" * 12
        s = detectors.detect_repetition(looped)
        self.assertIsNotNone(s)
        self.assertEqual(s.name, "repetition")

    def test_repetition_ignores_normal_short_lines(self):
        normal = GOOD + "\n" + GOOD.replace("solve", "solve2")
        self.assertIsNone(detectors.detect_repetition(normal))

    def test_truncated_output(self):
        s = detectors.detect_truncation({"a.py": "def f(:\n    x = [1, 2,"})
        self.assertIsNotNone(s)

    def test_no_files_is_worse_than_no_diff(self):
        none_written = detectors.detect_no_work({}, [], "a.py", is_replay=False)
        self.assertEqual(none_written.name, "no_work")
        self.assertLessEqual(none_written.severity, 45)

        redundant = detectors.detect_no_work({"a.py": GOOD}, [], "a.py", is_replay=False)
        self.assertEqual(redundant.name, "redundant_work")
        self.assertGreater(redundant.severity, none_written.severity)

    def test_replay_suppresses_redundant_work(self):
        """Harness 3 deliberately redoes known-good units; that is not fake progress."""
        self.assertIsNone(
            detectors.detect_no_work({"a.py": GOOD}, [], "a.py", is_replay=True))

    def test_bulldozing_earlier_work(self):
        diff = "\n".join("-old line %d" % i for i in range(60)) + "\n+one new line"
        self.assertIsNotNone(detectors.detect_deletion(diff))

    def test_failing_verify_is_a_signal(self):
        s = detectors.detect_verify_failure(
            {"skipped": False, "returncode": 1, "output": "2 failed"})
        self.assertIsNotNone(s)
        self.assertIsNone(detectors.detect_verify_failure(
            {"skipped": False, "returncode": 0, "output": "ok"}))


class TestJSONExtraction(unittest.TestCase):
    """Small models never return clean JSON. The parser has to cope."""

    def test_shapes_small_models_actually_emit(self):
        want = {"score": 80, "verdict": "PASS"}
        for raw in (
            '{"score": 80, "verdict": "PASS"}',
            '```json\n{"score": 80, "verdict": "PASS"}\n```',
            'Sure! Here is my assessment:\n{"score": 80, "verdict": "PASS"}\nHope that helps.',
            '```\n{"score": 80, "verdict": "PASS"}\n```\n\nLet me know if...',
        ):
            self.assertEqual(extract_json(raw), want, raw[:40])

    def test_nested_braces_and_strings(self):
        raw = 'note: {"a": {"b": [1,2]}, "s": "has } brace"}'
        self.assertEqual(extract_json(raw), {"a": {"b": [1, 2]}, "s": "has } brace"})

    def test_unparseable_returns_none(self):
        self.assertIsNone(extract_json("I cannot do that."))
        self.assertIsNone(extract_json(""))


class TestWorkerProtocol(unittest.TestCase):
    def test_parses_file_blocks(self):
        reply = "ok\n<<<FILE a/b.py>>>\nprint(1)\n<<<END>>>\ndone"
        self.assertEqual(worker.parse_files(reply), {"a/b.py": "print(1)\n"})

    def test_rejects_path_traversal_and_absolute_paths(self):
        for bad in ("../../etc/passwd", "/etc/passwd"):
            reply = "<<<FILE %s>>>\nx\n<<<END>>>" % bad
            self.assertEqual(worker.parse_files(reply), {}, bad)

    def test_multiple_files_in_one_reply(self):
        reply = ("<<<FILE a.py>>>\n1\n<<<END>>>\n"
                 "<<<FILE b.py>>>\n2\n<<<END>>>")
        self.assertEqual(sorted(worker.parse_files(reply)), ["a.py", "b.py"])

    def test_verify_none_is_skipped_not_run(self):
        cfg = load_config()
        with tempfile.TemporaryDirectory() as d:
            ws = Workspace(Path(d))
            self.assertTrue(worker.run_verify(cfg, ws, "none")["skipped"])
            self.assertTrue(worker.run_verify(cfg, ws, "")["skipped"])


class TestIntakeItems(unittest.TestCase):
    """A known item list is authoritative -- the model never enumerates 60 things."""

    def test_units_built_verbatim_from_items(self):
        items = ["Two Sum", "Add Two Numbers", "Longest Substring"]
        units = harness1_intake._units_from_items(items, {
            "deliverable_template": "solutions/{n:03d}_{slug}.py",
            "verify_template": "python -m pytest tests/test_{n:03d}.py -q",
        })
        self.assertEqual(len(units), 3)
        self.assertEqual(units[0]["title"], "Two Sum")
        self.assertEqual(units[0]["deliverable"], "solutions/001_two_sum.py")
        self.assertEqual(units[2]["verify"], "python -m pytest tests/test_003.py -q")

    def test_missing_templates_fall_back_safely(self):
        units = harness1_intake._units_from_items(["X"], {})
        self.assertEqual(units[0]["verify"], "none")
        self.assertIn("X", units[0]["deliverable"])

    def test_item_file_formats(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "items.txt"
            p.write_text("# leetcode\n1. Two Sum\n- Add Two Numbers\n\n3) Median\n",
                         encoding="utf-8")
            self.assertEqual(harness1_intake.load_items(p),
                             ["Two Sum", "Add Two Numbers", "Median"])
            j = Path(d) / "items.json"
            j.write_text(json.dumps(["A", "B"]), encoding="utf-8")
            self.assertEqual(harness1_intake.load_items(j), ["A", "B"])


def _report(cp, unit, score, verdict, segment=1):
    return {"checkpoint": cp, "unit_index": unit, "score": score, "verdict": verdict,
            "segment": segment, "sha": "sha%d" % cp, "note": "", "failure_modes": []}


class TestRecoveryPolicy(unittest.TestCase):
    """Harness 3 must rewind past the ONSET, not to the halt."""

    def setUp(self):
        self.cfg = load_config()
        # a clean run that decays: units 1-10 good, 11-12 degrading, 13 collapses
        self.reports = (
            [_report(i, i, 92, "PASS") for i in range(1, 11)]
            + [_report(11, 11, 66, "NOTE"), _report(12, 12, 60, "NOTE"),
               _report(13, 13, 20, "HALT")]
        )

    def test_anchor_is_last_clean_checkpoint_not_the_halt(self):
        onset, anchor = harness3_recovery.find_onset(self.reports, 75)
        self.assertEqual(anchor["unit_index"], 10, "anchor must be the last clean unit")
        self.assertEqual(onset["unit_index"], 11, "onset is the first degraded unit")

    def test_rewind_lands_before_the_degradation(self):
        _, anchor = harness3_recovery.find_onset(self.reports, 75)
        state = {"rewinds": []}
        target, depth, repeats, restore, anchor_idx = \
            harness3_recovery.choose_rewind_target(self.cfg, state, self.reports, anchor)
        self.assertLess(target, 11, "must restart before the first degraded unit")
        self.assertEqual(anchor_idx, 10)
        self.assertIsNotNone(restore, "a clean snapshot must be chosen to restore")
        self.assertGreaterEqual(restore["score"], 75)

    def test_repeated_failure_at_same_anchor_backs_off_further(self):
        _, anchor = harness3_recovery.find_onset(self.reports, 75)
        state = {"rewinds": []}
        first, d1, _, _, _ = harness3_recovery.choose_rewind_target(
            self.cfg, state, self.reports, anchor)
        state["rewinds"].append({"anchor_index": 10})
        second, d2, _, _, _ = harness3_recovery.choose_rewind_target(
            self.cfg, state, self.reports, anchor)
        self.assertGreater(d2, d1, "depth must escalate on a repeat failure")
        self.assertLess(second, first, "and land further back")

    def test_rewind_depth_is_capped(self):
        _, anchor = harness3_recovery.find_onset(self.reports, 75)
        state = {"rewinds": [{"anchor_index": 10} for _ in range(50)]}
        _, depth, _, _, _ = harness3_recovery.choose_rewind_target(
            self.cfg, state, self.reports, anchor)
        self.assertLessEqual(depth, self.cfg["recovery"]["max_rewind_depth"])

    def test_run_with_no_clean_checkpoint_has_no_anchor(self):
        bad = [_report(1, 1, 30, "NOTE"), _report(2, 2, 20, "HALT")]
        onset, anchor = harness3_recovery.find_onset(bad, 75)
        self.assertIsNone(anchor, "nothing clean means no anchor to trust")


class TestWorkspaceRewind(unittest.TestCase):
    """Rewind must actually restore files -- and must never destroy the failed work."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.ws = Workspace(Path(self.tmp) / "ws")
        self.ws.init()

    def tearDown(self):
        _rmtree(self.tmp)

    def test_restore_removes_work_done_after_the_snapshot(self):
        (self.ws.path / "good.py").write_text("good", encoding="utf-8")
        good_sha = self.ws.commit("good")

        (self.ws.path / "bad.py").write_text("bad", encoding="utf-8")
        self.ws.commit("bad")
        self.assertTrue((self.ws.path / "bad.py").exists())

        self.ws.tag("attempt/1")
        self.ws.restore(good_sha)
        self.assertTrue((self.ws.path / "good.py").exists(), "good work must survive")
        self.assertFalse((self.ws.path / "bad.py").exists(), "bad work must be rolled back")

    def test_abandoned_work_is_recoverable_from_its_tag(self):
        (self.ws.path / "good.py").write_text("good", encoding="utf-8")
        good_sha = self.ws.commit("good")
        (self.ws.path / "bad.py").write_text("bad", encoding="utf-8")
        self.ws.commit("bad")
        self.ws.tag("attempt/1")
        self.ws.restore(good_sha)
        # the failure trace is still in the repo -- that is the research data
        self.assertIn("bad.py", self.ws._git("show", "--name-only", "attempt/1"))

    def test_diff_reports_only_changes_since_the_snapshot(self):
        (self.ws.path / "a.py").write_text("a", encoding="utf-8")
        sha = self.ws.commit("a")
        (self.ws.path / "b.py").write_text("b", encoding="utf-8")
        self.ws.commit("b")
        self.assertEqual(self.ws.changed_files(sha, "HEAD"), ["b.py"])


class TestAnalysisAttribution(unittest.TestCase):
    """The "who caught what" metric decides whether the judge model is worth running."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.run = Run.create(self.tmp)
        self.run.save_spec({"goal": "g", "success_criteria": [], "red_flags": [],
                            "units": [{"index": i, "id": "u%d" % i, "title": "t",
                                       "deliverable": "d", "verify": "none",
                                       "checkpoint": True} for i in range(1, 5)]})

    def tearDown(self):
        _rmtree(self.tmp)

    def _cp(self, n, model_score, ceiling):
        self.run.save_checkpoint(n, {
            "checkpoint": n, "unit_index": n, "segment": 1,
            "score": min(model_score, ceiling), "model_score": model_score,
            "detector_ceiling": ceiling, "verdict": "PASS", "note": "",
            "failure_modes": [], "sha": "s%d" % n})

    def test_clean_checkpoints_are_not_counted_as_catches(self):
        """A model score of 92 under a ceiling of 100 is a pass, not a detection."""
        from lightsout import analysis
        self._cp(1, 92, 100)
        self._cp(2, 95, 100)
        s = analysis.summarize(self.run, note_floor=70)
        self.assertEqual(s["flagged_total"], 0)
        self.assertEqual(s["caught_by_model_only"], 0)
        self.assertEqual(s["caught_by_detector_only"], 0)

    def test_attribution_splits_correctly(self):
        from lightsout import analysis
        self._cp(1, 92, 30)    # detectors caught it, judge said fine
        self._cp(2, 40, 100)   # judge caught it, detectors blind
        self._cp(3, 35, 30)    # both
        self._cp(4, 90, 100)   # clean
        s = analysis.summarize(self.run, note_floor=70)
        self.assertEqual(s["caught_by_detector_only"], 1)
        self.assertEqual(s["caught_by_model_only"], 1)
        self.assertEqual(s["caught_by_both"], 1)
        self.assertEqual(s["flagged_total"], 3)


class TestEndToEnd(unittest.TestCase):
    """The whole loop on the mock provider: it must recover and finish."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())

    def tearDown(self):
        _rmtree(self.tmp)

    def _run(self, units=30):
        from lightsout import orchestrator
        cfg = load_config()
        cfg["provider"]["kind"] = "mock"
        cfg["run"]["wall_clock_budget_h"] = 0.5
        run = Run.create(self.tmp)
        harness1_intake.run_intake(cfg, run, request="%d problems" % units,
                                   total_units=units, interactive=False)
        state = orchestrator.run_lights_out(cfg, run, quiet=True)
        return run, state

    def test_degrading_model_still_finishes_the_job(self):
        run, state = self._run(30)
        self.assertEqual(state["status"], "done")
        self.assertEqual(state["cursor"], 30, "every unit must be delivered")
        self.assertGreater(state["halts"], 0, "the mock should have degraded at least once")

    def test_recovery_produces_overlapping_segments(self):
        """The sawtooth: each segment restarts before the previous one ended."""
        run, state = self._run(30)
        rewinds = state["rewinds"]
        self.assertTrue(rewinds, "expected at least one rewind")
        for rw in rewinds:
            self.assertLess(rw["to_index"], rw["from_index"],
                            "a rewind must move backwards")
            self.assertLessEqual(rw["to_index"], rw["onset_index"],
                                 "must restart at or before the degradation onset")

    def test_failed_segments_are_preserved_as_tags(self):
        run, state = self._run(30)
        ws = Workspace(run.workspace)
        tags = ws._git("tag").split()
        self.assertEqual(len(tags), len(state["rewinds"]),
                         "every abandoned segment must be recoverable")

    def test_final_output_is_clean(self):
        """After recovery, the delivered files must not contain the failure markers."""
        run, _ = self._run(30)
        files = list((run.workspace / "solutions").glob("*.py"))
        self.assertEqual(len(files), 30)
        for f in files:
            text = f.read_text(encoding="utf-8")
            self.assertNotIn("NotImplementedError", text, f.name)
            self.assertNotIn("TODO", text, f.name)

    def test_analysis_reports_the_discarded_work(self):
        from lightsout import analysis
        run, state = self._run(30)
        s = analysis.summarize(run)
        self.assertEqual(s["units_completed"], 30)
        self.assertGreater(s["units_attempted"], 30, "rewinds mean redoing work")
        self.assertGreater(s["units_discarded"], 0)
        self.assertLess(s["efficiency"], 1.0, "efficiency must account for the waste")

    def test_state_survives_a_simulated_crash(self):
        from lightsout import orchestrator
        cfg = load_config()
        cfg["provider"]["kind"] = "mock"
        cfg["run"]["wall_clock_budget_h"] = 0.0005      # die almost immediately
        run = Run.create(self.tmp)
        harness1_intake.run_intake(cfg, run, request="20 problems", total_units=20,
                                   interactive=False)
        first = orchestrator.run_lights_out(cfg, run, quiet=True)
        self.assertEqual(first["status"], "budget")
        mid_cursor = first["cursor"]
        self.assertGreater(mid_cursor, 0)

        # reopen from disk, as a fresh process would
        reopened = Run(run.root)
        cfg["run"]["wall_clock_budget_h"] = 0.5
        second = orchestrator.run_lights_out(cfg, reopened, quiet=True)
        self.assertEqual(second["status"], "done")
        self.assertEqual(second["cursor"], 20)


if __name__ == "__main__":
    unittest.main(verbosity=2)
