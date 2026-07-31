"""Build the problem banks.

    python -m bench.generate            rebuild bench/problems/*.json
    python -m bench.generate --check    validate without writing

Expected outputs come from running each family's reference solution, so a broken
problem fails here rather than silently marking a model wrong all night. Two gates
run on every problem before it is written:

  * the reference must execute on every generated input
  * the outputs must not all be identical -- a problem whose answer never changes
    tests nothing, and a model can pass it by printing a constant
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from . import (codingbat, core, families_easy, families_hard, families_hard2,
               families_hard3, families_medium, families_medium2)

OUT_DIR = Path(__file__).resolve().parent / "problems"

TIERS = {
    "easy": [families_easy],
    "medium": [families_medium, families_medium2],
    "hard": [families_hard, families_hard2, families_hard3],
}
TARGET = 200


def build_tier(modules):
    problems = []
    for mod in modules:
        problems += core.expand(core.collect(mod))
    return core.interleave(problems)


def validate(p, cases):
    if not cases:
        return "produced no test cases"
    outs = {json.dumps(c["output"], sort_keys=True) for c in cases}
    if len(outs) == 1:
        return "every case returns the same answer (%s)" % list(outs)[0][:40]
    return None


def emit(problems, prefix, seed0):
    out, failures = [], []
    for i, p in enumerate(problems):
        pid = "%s%03d" % (prefix, i + 1)
        try:
            cases = core.make_cases(p, seed=seed0 + i)
        except Exception as e:                       # noqa: BLE001 - report, don't stop
            failures.append((p["title"], "%s: %s" % (type(e).__name__, e)))
            continue
        problem_error = validate(p, cases)
        if problem_error:
            failures.append((p["title"], problem_error))
            continue
        out.append({
            "id": pid,
            "title": p["title"],
            "difficulty": p["difficulty"],
            "family": p["family"],
            "topics": p["topics"],
            "statement": p["statement"],
            "signature": p["signature"],
            "examples": cases[:2],
            "tests": cases,
        })
    return out, failures


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true", help="validate without writing")
    ap.add_argument("--target", type=int, default=TARGET,
                    help="problems per difficulty tier (default 200)")
    args = ap.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    all_failures = []
    banks = {}

    seed = 100000
    for tier, modules in TIERS.items():
        pool = build_tier(modules)
        built, failures = emit(pool, tier[0], seed)
        seed += 10000
        all_failures += [("%s/%s" % (tier, t), e) for t, e in failures]
        if len(built) < args.target:
            all_failures.append((tier, "only %d usable problems, need %d"
                                 % (len(built), args.target)))
        banks[tier] = built[:args.target]

    cb_pool = core.interleave(core.expand(core.collect(codingbat)))
    cb, cb_failures = emit(cb_pool, "w", seed)
    all_failures += [("codingbat/%s" % t, e) for t, e in cb_failures]
    banks["codingbat"] = cb

    for tier, built in banks.items():
        cases = sum(len(p["tests"]) for p in built)
        fams = len({p["family"] for p in built})
        print("%-10s %4d problems  %3d families  %5d test cases"
              % (tier, len(built), fams, cases))

    if all_failures:
        print("\n%d problem(s) rejected:" % len(all_failures))
        for title, err in all_failures[:25]:
            print("   %-46s %s" % (title[:46], err[:70]))

    if args.check:
        print("\n--check: nothing written")
        return 1 if all_failures else 0

    combined = banks["easy"] + banks["medium"] + banks["hard"]
    (OUT_DIR / "leetcode_style.json").write_text(
        json.dumps(combined, indent=1), encoding="utf-8")
    (OUT_DIR / "codingbat_style.json").write_text(
        json.dumps(banks["codingbat"], indent=1), encoding="utf-8")

    index = [{"id": p["id"], "title": p["title"], "difficulty": p["difficulty"],
              "family": p["family"], "topics": p["topics"]}
             for p in combined + banks["codingbat"]]
    (OUT_DIR / "index.json").write_text(json.dumps(index, indent=1), encoding="utf-8")

    print("\nwrote %d LeetCode-style + %d CodingBat-style problems to %s"
          % (len(combined), len(banks["codingbat"]), OUT_DIR))
    return 1 if all_failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
