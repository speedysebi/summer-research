"""Deterministic failure detectors -- the non-model half of Harness 2.

A small model judging another small model is itself unreliable, and it degrades under
exactly the conditions you most need it to work. So the sentinel's verdict is the WORST
of (these checks, the model's opinion). These fire on measurable facts, never on
judgment, and any one of them can force a HALT on its own.

Each detector returns a Signal. `severity` is the score ceiling it imposes: a signal
with severity 30 means "no matter what the judge says, this checkpoint scores <= 30".
"""
from __future__ import annotations

import re

STUB_PATTERNS = [
    (r"\bNotImplementedError\b", "raises NotImplementedError", 30),
    (r"^\s*pass\s*(#.*)?$", "bare `pass` body", 55),
    (r"\bTODO\b|\bFIXME\b|\bXXX\b", "TODO/FIXME marker left in output", 65),
    (r"^\s*\.\.\.\s*$", "ellipsis placeholder body", 45),
    (r"your (code|implementation) here", "placeholder comment", 30),
    (r"rest of (the )?(code|implementation|function)", "elided implementation", 30),
    (r"^\s*//\s*\.\.\.", "elided code comment", 40),
]

WEAK_TEST_PATTERNS = [
    (r"assert\s+True\b", "assert True", 35),
    (r"assert\s+\w+\s+is\s+not\s+None\s*$", "assertion only checks non-None", 65),
    (r"def\s+test_\w+\([^)]*\):\s*\n\s*pass", "empty test body", 30),
]


class Signal:
    def __init__(self, name, detail, severity, evidence=None):
        self.name = name
        self.detail = detail
        self.severity = severity
        self.evidence = evidence or []

    def to_dict(self):
        return {
            "name": self.name,
            "detail": self.detail,
            "severity": self.severity,
            "evidence": self.evidence[:5],
        }

    def __repr__(self):
        return "<Signal %s sev=%d>" % (self.name, self.severity)


def _line_hits(text, patterns, flags=re.M | re.I):
    hits = []
    for pattern, label, severity in patterns:
        for m in re.finditer(pattern, text, flags):
            line = text[: m.start()].count("\n") + 1
            hits.append((label, severity, "line %d: %s" % (line, m.group(0).strip()[:80])))
    return hits


def detect_stubs(new_text):
    hits = _line_hits(new_text, STUB_PATTERNS)
    if not hits:
        return None
    worst = min(h[1] for h in hits)
    labels = sorted({h[0] for h in hits})
    return Signal("stub", "placeholder work: " + ", ".join(labels), worst,
                  [h[2] for h in hits])


def detect_weak_tests(new_text):
    hits = _line_hits(new_text, WEAK_TEST_PATTERNS)
    if not hits:
        return None
    worst = min(h[1] for h in hits)
    labels = sorted({h[0] for h in hits})
    return Signal("test_gaming", "tests that cannot fail: " + ", ".join(labels), worst,
                  [h[2] for h in hits])


def detect_repetition(new_text, min_line_len=12, threshold=6):
    """A looping model emits the same line over and over. Cheap and very reliable."""
    counts = {}
    for raw in new_text.splitlines():
        line = raw.strip()
        if len(line) >= min_line_len and not line.startswith(("+++", "---", "@@")):
            counts[line] = counts.get(line, 0) + 1
    worst = [(c, l) for l, c in counts.items() if c >= threshold]
    if not worst:
        return None
    worst.sort(reverse=True)
    count, line = worst[0]
    sev = 25 if count >= threshold * 2 else 50
    return Signal("repetition", "line repeated %d times (generation loop)" % count, sev,
                  [line[:100]])


def detect_truncation(files):
    """Output cut off mid-structure: unbalanced delimiters or a dangling last line."""
    bad = []
    for path, text in files.items():
        if not text.strip():
            continue
        opens = text.count("(") + text.count("[") + text.count("{")
        closes = text.count(")") + text.count("]") + text.count("}")
        if abs(opens - closes) > 2:
            bad.append("%s: %d unclosed delimiters" % (path, opens - closes))
            continue
        last = text.rstrip().splitlines()[-1].strip() if text.strip() else ""
        if last.endswith((",", "\\", "=", "+", "(", "{", "[")) or last.endswith("def"):
            bad.append("%s: file ends mid-statement (%r)" % (path, last[-40:]))
    if not bad:
        return None
    return Signal("truncation", "output was cut off", 40, bad)


def detect_no_work(written_files, changed_files, claimed_deliverable, is_replay=False):
    """The model said it finished but produced nothing -- a common small-model lie.

    Two distinct cases, and conflating them causes false HALTs:
      * wrote no files at all            -> hard failure
      * wrote files identical to what was already there -> suspicious, but legitimate
        when Harness 3 has just rewound and the unit is being replayed.
    """
    if not written_files:
        return Signal("no_work", "unit reported complete but emitted no files", 20,
                      ["expected: " + str(claimed_deliverable)[:120]])
    if not changed_files and not is_replay:
        return Signal("redundant_work",
                      "wrote %d file(s) but nothing changed on disk" % len(written_files),
                      60, [", ".join(list(written_files)[:3])])
    return None


def detect_deletion(diff_text, threshold=40):
    """Large deletions mid-run usually mean the model is bulldozing earlier work."""
    removed = sum(1 for l in diff_text.splitlines()
                  if l.startswith("-") and not l.startswith("---"))
    added = sum(1 for l in diff_text.splitlines()
                if l.startswith("+") and not l.startswith("+++"))
    if removed >= threshold and removed > added * 2:
        return Signal("destructive_edit",
                      "deleted %d lines while adding only %d" % (removed, added), 35,
                      ["net loss of %d lines" % (removed - added)])
    return None


def detect_verify_failure(verify_result):
    """A failing verify command is ground truth -- it outranks any model opinion."""
    if not verify_result or verify_result.get("skipped"):
        return None
    if verify_result.get("returncode", 0) == 0:
        return None
    tail = (verify_result.get("output") or "")[-400:]
    return Signal("verify_failed",
                  "verify command exited %s" % verify_result.get("returncode"),
                  35, [tail])


def detect_wrong_answer(verify_result):
    """Graded correctness from the evaluator.

    A pass rate is the strongest signal in the system: it is measured, not judged.
    Scored proportionally so "failed two edge cases" and "nothing works" are not the
    same event -- the first is a NOTE, the second stops the run.
    """
    if not verify_result or verify_result.get("skipped"):
        return None
    rate = verify_result.get("pass_rate")
    if rate is None or rate >= 1.0:
        return None
    ceiling = int(round(rate * 70))          # a full pass is required to clear the floor
    tail = (verify_result.get("output") or "")[-300:]
    return Signal("wrong_answer", "only %d%% of the tests pass" % round(rate * 100),
                  ceiling, [tail])


def run_all(new_text, files, changed_files, diff_text, verify_result, deliverable,
            is_replay=False):
    """Run every detector. Returns (signals, score_ceiling)."""
    signals = [s for s in (
        detect_stubs(new_text),
        detect_weak_tests(new_text),
        detect_repetition(new_text),
        detect_truncation(files),
        detect_no_work(files, changed_files, deliverable, is_replay),
        detect_deletion(diff_text),
        detect_verify_failure(verify_result),
        detect_wrong_answer(verify_result),
    ) if s is not None]
    ceiling = min([s.severity for s in signals], default=100)
    return signals, ceiling
