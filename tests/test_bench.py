"""Tests for the problem banks and the evaluator.

The CodingBat-style bank is the fixture set here. Its problems are small enough to
solve correctly inside a test, which makes them the right thing to check the evaluator
against: if a genuinely correct solution does not score 100%, the evaluator is broken,
and every accuracy number the harness reports would be wrong.
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

from bench import core                                    # noqa: E402
from lightsout import benchrun, detectors, evaluator, worker   # noqa: E402
from lightsout.state import Run                           # noqa: E402

BANK_DIR = Path(__file__).resolve().parent.parent / "bench" / "problems"
HAS_BANK = (BANK_DIR / "leetcode_style.json").exists()
skip_no_bank = unittest.skipUnless(
    HAS_BANK, "problem bank not built -- run `python -m bench.generate`")


def _rmtree(path):
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


@skip_no_bank
class TestBankIntegrity(unittest.TestCase):
    """A corpus that grades a model all night has to be right before it is used."""

    @classmethod
    def setUpClass(cls):
        cls.lc = evaluator.load_bank("leetcode_style")
        cls.cb = evaluator.load_bank("codingbat_style")

    def test_tier_counts(self):
        counts = {}
        for p in self.lc:
            counts[p["difficulty"]] = counts.get(p["difficulty"], 0) + 1
        self.assertEqual(counts.get("easy"), 200)
        self.assertEqual(counts.get("medium"), 200)
        self.assertEqual(counts.get("hard"), 200)
        self.assertEqual(len(self.lc), 600)

    def test_ids_are_unique(self):
        ids = [p["id"] for p in self.lc + self.cb]
        self.assertEqual(len(ids), len(set(ids)))

    def test_every_problem_is_complete(self):
        for p in self.lc + self.cb:
            self.assertTrue(p["statement"].strip(), p["id"])
            self.assertIn("def solve(", p["signature"], p["id"])
            self.assertGreaterEqual(len(p["tests"]), 4, p["id"])
            for case in p["tests"]:
                self.assertIsInstance(case["input"], list, p["id"])
                self.assertIn("output", case, p["id"])

    def test_no_problem_has_a_constant_answer(self):
        """A problem whose answer never changes can be passed by printing a constant."""
        for p in self.lc + self.cb:
            outs = {json.dumps(c["output"], sort_keys=True) for c in p["tests"]}
            self.assertGreater(len(outs), 1, "%s (%s) is degenerate" % (p["id"], p["title"]))

    def test_difficulty_tiers_are_actually_graded(self):
        """Hard problems should not be a relabelling of the easy ones."""
        fams = {d: {p["family"] for p in self.lc if p["difficulty"] == d}
                for d in ("easy", "medium", "hard")}
        self.assertFalse(fams["easy"] & fams["hard"], "easy and hard share a family")
        self.assertGreaterEqual(len(fams["hard"]), 10)

    def test_banks_cover_many_families(self):
        self.assertGreaterEqual(len({p["family"] for p in self.lc}), 50)
        self.assertGreaterEqual(len({p["family"] for p in self.cb}), 5)


@skip_no_bank
class TestEvaluator(unittest.TestCase):
    """Correct code must score 100%, and nothing else may."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.problems = {p["id"]: p for p in evaluator.load_bank("codingbat_style")}

    def tearDown(self):
        _rmtree(self.tmp)

    def _write(self, body):
        path = self.tmp / "sol.py"
        path.write_text(body, encoding="utf-8")
        return path

    def _find(self, title):
        for p in self.problems.values():
            if p["title"] == title:
                return p
        self.skipTest("no CodingBat problem titled %r" % title)

    def test_a_correct_solution_scores_full_marks(self):
        p = self._find("Sum Double")
        path = self._write("def solve(a, b):\n"
                           "    return (a + b) * 2 if a == b else a + b\n")
        r = evaluator.evaluate_file(path, p)
        self.assertTrue(r["ok"], r)
        self.assertEqual(r["passed"], r["total"])
        self.assertEqual(r["rate"], 1.0)

    def test_several_correct_solutions_across_the_bank(self):
        cases = [
            ("Count Evens", "def solve(nums):\n    return sum(1 for x in nums if x % 2 == 0)\n"),
            ("Double Char", "def solve(s):\n    return ''.join(c * 2 for c in s)\n"),
            ("Big Diff", "def solve(nums):\n"
                         "    return max(nums) - min(nums) if nums else 0\n"),
            ("Has22", "def solve(nums):\n"
                      "    return any(nums[i] == 2 and nums[i+1] == 2 "
                      "for i in range(len(nums)-1))\n"),
            ("Word Length", "def solve(words):\n    return {w: len(w) for w in words}\n"),
        ]
        for title, body in cases:
            p = self._find(title)
            r = evaluator.evaluate_file(self._write(body), p)
            self.assertTrue(r["ok"], "%s: %s" % (title, evaluator.format_failures(r)))

    def test_a_wrong_solution_does_not_pass(self):
        p = self._find("Count Evens")
        r = evaluator.evaluate_file(self._write("def solve(nums):\n    return 0\n"), p)
        self.assertFalse(r["ok"])
        self.assertLess(r["rate"], 1.0)
        self.assertTrue(r["failures"])

    def test_a_stub_scores_zero(self):
        p = self._find("Count Evens")
        r = evaluator.evaluate_file(
            self._write("def solve(nums):\n    raise NotImplementedError\n"), p)
        self.assertEqual(r["passed"], 0)
        self.assertFalse(r["ok"])

    def test_an_infinite_loop_is_contained(self):
        """A runaway solution must cost one unit, not the night."""
        p = self._find("Count Evens")
        r = evaluator.evaluate_file(
            self._write("def solve(nums):\n    while True:\n        pass\n"),
            p, timeout=4)
        self.assertFalse(r["ok"])
        self.assertIn("timed out", r["error"])

    def test_a_file_that_does_not_import_is_reported(self):
        p = self._find("Count Evens")
        r = evaluator.evaluate_file(self._write("this is not python("), p)
        self.assertFalse(r["ok"])
        self.assertIn("import failed", r["error"])

    def test_a_missing_solve_is_reported(self):
        p = self._find("Count Evens")
        r = evaluator.evaluate_file(self._write("def other(x):\n    return x\n"), p)
        self.assertFalse(r["ok"])
        self.assertIn("solve", r["error"])

    def test_a_missing_file_is_not_a_crash(self):
        p = self._find("Count Evens")
        r = evaluator.evaluate_file(self.tmp / "nope.py", p)
        self.assertFalse(r["ok"])
        self.assertIn("does not exist", r["error"])

    def test_exiting_the_process_does_not_fake_a_pass(self):
        p = self._find("Count Evens")
        r = evaluator.evaluate_file(
            self._write("import sys\nsys.exit(0)\ndef solve(nums):\n    return 0\n"), p)
        self.assertFalse(r["ok"])


@skip_no_bank
class TestBenchRun(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())

    def tearDown(self):
        _rmtree(self.tmp)

    def test_spec_units_carry_statement_and_verify(self):
        spec = benchrun.build_spec(difficulty="easy", count=5)
        self.assertEqual(len(spec["units"]), 5)
        for u in spec["units"]:
            self.assertTrue(u["statement"].strip())
            self.assertIn("def solve(", u["statement"])
            self.assertIn("eval-one", u["verify"])
            self.assertEqual(u["difficulty"], "easy")
            self.assertTrue(u["checkpoint"])

    def test_selection_respects_difficulty_and_count(self):
        for tier in ("easy", "medium", "hard"):
            spec = benchrun.build_spec(difficulty=tier, count=3)
            self.assertTrue(all(u["difficulty"] == tier for u in spec["units"]))

    def test_scoring_a_workspace_with_real_solutions(self):
        run = Run.create(self.tmp)
        spec = benchrun.build_spec(bank="codingbat_style", count=3)
        run.save_spec(spec)
        (run.workspace / "solutions").mkdir(parents=True, exist_ok=True)

        problems = evaluator.all_problems()
        # write a correct solution for the first unit only
        first = spec["units"][0]
        ref_body = _reference_for(problems[first["problem_id"]]["title"])
        if ref_body is None:
            self.skipTest("no canned reference for %r" % first["title"])
        (run.workspace / ("solutions/%s.py" % first["problem_id"])).write_text(
            ref_body, encoding="utf-8")

        scores = benchrun.score_workspace(run, timeout=15)
        self.assertEqual(len(scores), 3)
        self.assertTrue(scores[0]["ok"], scores[0])
        self.assertFalse(scores[1]["ok"])
        self.assertIn("does not exist", scores[1]["error"])
        rendered = benchrun.render_scores(scores)
        self.assertIn("solved", rendered)


def _reference_for(title):
    return {
        "Sleep In": "def solve(weekday, vacation):\n    return (not weekday) or vacation\n",
        "Monkey Trouble": "def solve(a, b):\n    return a == b\n",
        "Hello Name": "def solve(s):\n    return 'Hello ' + s + '!'\n",
        "String Times": "def solve(s, n):\n    return s * n\n",
        "First Last Six": "def solve(nums):\n"
                          "    return bool(nums) and (nums[0] == 6 or nums[-1] == 6)\n",
        "Count Evens": "def solve(nums):\n"
                       "    return sum(1 for x in nums if x % 2 == 0)\n",
        "Cigar Party": "def solve(n, flag):\n"
                       "    return n >= 40 and (flag or n <= 60)\n",
        "Double23": "def solve(nums):\n"
                    "    return any(nums[i] == nums[i+1] for i in range(len(nums)-1))\n",
        "Word Count": "def solve(words):\n"
                      "    out = {}\n"
                      "    for w in words:\n"
                      "        out[w] = out.get(w, 0) + 1\n"
                      "    return out\n",
    }.get(title)


class TestPassRateSignal(unittest.TestCase):
    """The measured pass rate has to reach the sentinel as a graded signal."""

    def test_parsing_the_evaluator_output(self):
        self.assertEqual(worker._parse_pass_rate("e001 Something  12/16 passed"), 0.75)
        self.assertEqual(worker._parse_pass_rate("0/16 passed"), 0.0)
        self.assertEqual(worker._parse_pass_rate("16/16 passed"), 1.0)
        self.assertIsNone(worker._parse_pass_rate("no rate here"))
        self.assertIsNone(worker._parse_pass_rate(None))

    def test_full_marks_raises_no_signal(self):
        self.assertIsNone(detectors.detect_wrong_answer(
            {"skipped": False, "returncode": 0, "pass_rate": 1.0, "output": ""}))

    def test_partial_credit_is_graded_not_binary(self):
        """Two failed edge cases and total failure must not score the same."""
        near = detectors.detect_wrong_answer(
            {"skipped": False, "returncode": 1, "pass_rate": 0.9, "output": ""})
        none = detectors.detect_wrong_answer(
            {"skipped": False, "returncode": 1, "pass_rate": 0.0, "output": ""})
        self.assertIsNotNone(near)
        self.assertIsNotNone(none)
        self.assertGreater(near.severity, none.severity)
        self.assertLessEqual(none.severity, 45, "a total failure must be able to halt")

    def test_a_skipped_verify_raises_no_signal(self):
        self.assertIsNone(detectors.detect_wrong_answer({"skipped": True}))
        self.assertIsNone(detectors.detect_wrong_answer(None))


class TestGeneratorGates(unittest.TestCase):
    """The build-time gates that keep a broken problem out of the bank."""

    def test_degenerate_problems_are_rejected(self):
        from bench.generate import validate
        constant = [{"input": [[1]], "output": 0}, {"input": [[2]], "output": 0}]
        self.assertIsNotNone(validate({}, constant))
        varied = [{"input": [[1]], "output": 1}, {"input": [[2]], "output": 2}]
        self.assertIsNone(validate({}, varied))
        self.assertIsNotNone(validate({}, []))

    def test_interleave_keeps_a_truncated_bank_diverse(self):
        problems = ([{"family": "a"}] * 50) + ([{"family": "b"}] * 50)
        mixed = core.interleave(problems)
        first20 = [p["family"] for p in mixed[:20]]
        self.assertIn("a", first20)
        self.assertIn("b", first20)


if __name__ == "__main__":
    unittest.main(verbosity=2)
