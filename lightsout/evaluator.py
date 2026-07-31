"""Correctness evaluation against the problem banks.

This is the piece that makes the whole harness measurable. Harness 2 judges *quality* --
does this look like real work. The evaluator judges *correctness* -- does it actually
compute the right answer. Those are different questions, and the second one is ground
truth: a solution that fails its tests is wrong no matter how good it looks.

Each candidate runs in a separate process with a timeout, so an infinite loop or a
`sys.exit` in generated code costs one unit rather than the night.

As a command, this is what a unit's `verify` runs:

    python -m lightsout.evaluator <problem_id> <path/to/solution.py>

exiting 0 when every test passes. As a library, `evaluate_file` returns the detail the
sentinel and the analysis use.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

BANK_DIR = Path(__file__).resolve().parent.parent / "bench" / "problems"
_CACHE = {}


# --------------------------------------------------------------------------- #
# Bank loading
# --------------------------------------------------------------------------- #
def load_bank(name="leetcode_style"):
    if name not in _CACHE:
        path = BANK_DIR / ("%s.json" % name)
        if not path.exists():
            raise FileNotFoundError(
                "problem bank %s not found -- run `python -m bench.generate`" % path)
        _CACHE[name] = json.loads(path.read_text(encoding="utf-8"))
    return _CACHE[name]


def all_problems():
    out = {}
    for bank in ("leetcode_style", "codingbat_style"):
        try:
            for p in load_bank(bank):
                out[p["id"]] = p
        except FileNotFoundError:
            pass
    return out


def get_problem(problem_id):
    problems = all_problems()
    if problem_id not in problems:
        raise KeyError("no problem with id %r" % problem_id)
    return problems[problem_id]


def select(difficulty=None, family=None, limit=None, bank="leetcode_style"):
    out = [p for p in load_bank(bank)
           if (difficulty is None or p["difficulty"] == difficulty)
           and (family is None or p["family"] == family)]
    return out[:limit] if limit else out


# --------------------------------------------------------------------------- #
# The runner, executed in a child process
# --------------------------------------------------------------------------- #
RUNNER = r'''
import json, sys, importlib.util

spec_path, cases_path = sys.argv[1], sys.argv[2]
cases = json.loads(open(cases_path, encoding="utf-8").read())

spec = importlib.util.spec_from_file_location("candidate", spec_path)
mod = importlib.util.module_from_spec(spec)
try:
    spec.loader.exec_module(mod)
except BaseException as e:
    print(json.dumps({"fatal": "import failed: %s: %s" % (type(e).__name__, e)}))
    sys.exit(0)

fn = getattr(mod, "solve", None)
if not callable(fn):
    print(json.dumps({"fatal": "no callable named solve() was defined"}))
    sys.exit(0)

results = []
for i, case in enumerate(cases):
    try:
        got = fn(*json.loads(json.dumps(case["input"])))
        ok = got == case["output"]
        # json round trip: tuples and other shapes compare equal to their list form
        if not ok:
            try:
                ok = json.loads(json.dumps(got)) == case["output"]
            except (TypeError, ValueError):
                ok = False
        results.append({"i": i, "ok": bool(ok),
                        "got": repr(got)[:200] if not ok else None})
    except BaseException as e:
        results.append({"i": i, "ok": False,
                        "got": "raised %s: %s" % (type(e).__name__, str(e)[:120])})
print(json.dumps({"results": results}))
'''


def evaluate_file(path, problem, timeout=20, python=None):
    """Run one candidate solution against one problem's tests.

    Returns {passed, total, rate, ok, failures, error}. Never raises for a bad
    candidate -- a crash is a failing result, not an exception here.
    """
    path = Path(path)
    if not path.exists():
        return _result(0, len(problem["tests"]), [], "solution file does not exist")

    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        runner = Path(tmp) / "_runner.py"
        cases = Path(tmp) / "_cases.json"
        runner.write_text(RUNNER, encoding="utf-8")
        cases.write_text(json.dumps(problem["tests"]), encoding="utf-8")
        try:
            proc = subprocess.run(
                [python or sys.executable, str(runner), str(path), str(cases)],
                capture_output=True, text=True, encoding="utf-8", errors="replace",
                timeout=timeout,
            )
        except subprocess.TimeoutExpired:
            return _result(0, len(problem["tests"]), [],
                           "timed out after %ss (likely an infinite loop)" % timeout)

    if proc.returncode != 0 and not proc.stdout.strip():
        return _result(0, len(problem["tests"]), [],
                       "runner exited %s: %s" % (proc.returncode,
                                                 (proc.stderr or "")[-200:]))
    try:
        payload = json.loads(proc.stdout.strip().splitlines()[-1])
    except (ValueError, IndexError):
        return _result(0, len(problem["tests"]), [],
                       "unreadable runner output: %s" % (proc.stdout or "")[-200:])

    if "fatal" in payload:
        return _result(0, len(problem["tests"]), [], payload["fatal"])

    results = payload["results"]
    passed = sum(1 for r in results if r["ok"])
    failures = []
    for r in results:
        if not r["ok"]:
            case = problem["tests"][r["i"]]
            failures.append({
                "input": case["input"],
                "expected": case["output"],
                "got": r["got"],
            })
    return _result(passed, len(results), failures, None)


def _result(passed, total, failures, error):
    return {
        "passed": passed,
        "total": total,
        "rate": round(passed / total, 4) if total else 0.0,
        "ok": total > 0 and passed == total,
        "failures": failures[:3],
        "error": error,
    }


def format_failures(result, limit=2):
    """A short, model-readable explanation of what went wrong."""
    if result["error"]:
        return result["error"]
    lines = []
    for f in result["failures"][:limit]:
        args = ", ".join(json.dumps(a) for a in f["input"])
        lines.append("solve(%s) -> %s, expected %s"
                     % (args[:120], f["got"], json.dumps(f["expected"])[:80]))
    return "; ".join(lines)


# --------------------------------------------------------------------------- #
def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if len(argv) < 2:
        print("usage: python -m lightsout.evaluator <problem_id> <solution.py>",
              file=sys.stderr)
        return 2
    problem_id, path = argv[0], argv[1]
    try:
        problem = get_problem(problem_id)
    except (KeyError, FileNotFoundError) as e:
        print(str(e), file=sys.stderr)
        return 2

    result = evaluate_file(path, problem)
    print("%s  %s  %d/%d passed"
          % (problem_id, problem["title"], result["passed"], result["total"]))
    if not result["ok"]:
        print(format_failures(result, limit=3))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
