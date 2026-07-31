"""Turn the problem banks into a run spec.

This is Harness 1's non-conversational path. The work items are already enumerated and
already have a machine-checkable definition of done, so there is nothing to ask about:
the spec is built directly, and every unit gets a `verify` that runs the evaluator.

That gives the run something the conversational path cannot: ground truth at every
checkpoint. Harness 2 stops guessing whether the work looks right and is told whether
it is right.
"""
from __future__ import annotations

import json
from pathlib import Path

from . import evaluator

ROOT = Path(__file__).resolve().parent.parent

GOAL = ("Solve every problem in the assigned set. Each problem gets its own file "
        "defining a function named solve() with the given signature, and each solution "
        "must pass the problem's hidden test cases exactly.")

CRITERIA = [
    "Every problem has a solution file defining solve()",
    "Every solution passes all of its test cases",
    "Solutions handle the stated edge cases, including empty inputs",
    "No placeholder, stubbed or hard-coded-answer implementations",
]

RED_FLAGS = [
    "Returning a hard-coded constant that happens to pass the examples",
    "Special-casing the example inputs instead of implementing the rule",
    "solve() raising NotImplementedError or containing only pass",
    "Reusing the previous problem's solution unchanged",
    "Claiming a problem is done without writing its file",
    "Ignoring the empty-input case the statement specifies",
]


def _verify_for(problem_id, rel_path):
    """A verify command that runs the evaluator from the workspace.

    The workspace is a scratch directory somewhere else entirely, so the harness path
    is baked in absolutely rather than relying on the caller's PYTHONPATH.
    """
    return 'python "%s" %s %s' % (
        (ROOT / "run.py").as_posix(), "eval-one " + problem_id, rel_path)


def build_spec(difficulty=None, count=None, bank="leetcode_style", family=None,
               shuffle_seed=None):
    problems = evaluator.select(difficulty=difficulty, family=family, bank=bank)
    if shuffle_seed is not None:
        import random
        random.Random(shuffle_seed).shuffle(problems)
    if count:
        problems = problems[:count]
    if not problems:
        raise SystemExit("no problems matched that selection")

    units = []
    for i, p in enumerate(problems, start=1):
        rel = "solutions/%s.py" % p["id"]
        units.append({
            "index": i,
            "id": p["id"],
            "problem_id": p["id"],
            "difficulty": p["difficulty"],
            "title": p["title"],
            "statement": _statement(p),
            "deliverable": "%s defining %s" % (rel, p["signature"]),
            "verify": _verify_for(p["id"], rel),
            "checkpoint": True,
        })

    tiers = sorted({p["difficulty"] for p in problems})
    return {
        "request": "Solve %d %s problems from the built-in bank."
                   % (len(problems), "/".join(tiers)),
        "qa": [],
        "goal": GOAL,
        "success_criteria": CRITERIA,
        "red_flags": RED_FLAGS,
        "units": units,
    }


def _statement(p):
    lines = [p["statement"], "", "Write exactly this function: %s" % p["signature"]]
    if p.get("examples"):
        lines.append("")
        lines.append("Examples:")
        for ex in p["examples"][:2]:
            args = ", ".join(json.dumps(a) for a in ex["input"])
            lines.append("  solve(%s) == %s" % (args[:110], json.dumps(ex["output"])[:80]))
    return "\n".join(lines)


def score_workspace(run, bank_ids=None, timeout=20):
    """Re-evaluate everything in a finished workspace. Returns per-problem results."""
    spec = run.load_spec()
    out = []
    problems = evaluator.all_problems()
    for unit in spec["units"]:
        pid = unit.get("problem_id")
        if not pid or pid not in problems:
            continue
        if bank_ids and pid not in bank_ids:
            continue
        path = run.workspace / ("solutions/%s.py" % pid)
        result = evaluator.evaluate_file(path, problems[pid], timeout=timeout)
        out.append({
            "problem_id": pid,
            "index": unit["index"],
            "title": unit["title"],
            "difficulty": unit.get("difficulty", "?"),
            "passed": result["passed"],
            "total": result["total"],
            "rate": result["rate"],
            "ok": result["ok"],
            "error": result["error"],
        })
    return out


def render_scores(scores):
    if not scores:
        return "no benchmark units in this run (build one with `run.py bench`)"
    solved = sum(1 for s in scores if s["ok"])
    attempted = sum(1 for s in scores if s["total"] and (s["passed"] or not s["error"]))
    lines = ["=== BENCHMARK SCORE ===",
             "solved            %d / %d  (%.1f%%)"
             % (solved, len(scores), 100.0 * solved / len(scores))]

    by_tier = {}
    for s in scores:
        by_tier.setdefault(s["difficulty"], []).append(s)
    for tier in ("easy", "medium", "hard", "warmup"):
        if tier not in by_tier:
            continue
        rows = by_tier[tier]
        ok = sum(1 for r in rows if r["ok"])
        mean_rate = sum(r["rate"] for r in rows) / len(rows)
        lines.append("  %-8s %3d/%-3d solved   mean test pass rate %.1f%%"
                     % (tier, ok, len(rows), mean_rate * 100))

    missing = [s for s in scores if s["error"] == "solution file does not exist"]
    if missing:
        lines.append("\n%d problem(s) have no solution file at all" % len(missing))
    failed = [s for s in scores if not s["ok"] and s not in missing]
    if failed:
        lines.append("\nfirst failures:")
        for s in failed[:8]:
            lines.append("  %-6s %-40s %2d/%-2d  %s"
                         % (s["problem_id"], s["title"][:40], s["passed"], s["total"],
                            (s["error"] or "")[:40]))
    return "\n".join(lines)
