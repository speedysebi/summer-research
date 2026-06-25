"""HARNESS 1 -- Intake.

The only part of the system a human talks to. You state the job ("I have 60 LeetCode
questions I need solved"), the model asks whatever it needs to ask, and then it turns
the answers into a machine-readable plan.

The plan is not just a task list. It also fixes, up front and in writing:

  * the goal, in one paragraph        -> Harness 3 reads this to know what it is restoring
  * success criteria                  -> what "done and correct" means
  * red flags                         -> the task-specific ways THIS job tends to go wrong,
                                         which become Harness 2's watch list
  * work units, each with a verify    -> the atoms of work
  * which units are checkpoints       -> "every single time it should stop"

That last one matters most. The checkpoint schedule is decided here, before any code is
written, by the part of the system that still has a clean context. Deciding where to
stop while you are mid-run is exactly the judgment call a degrading model gets wrong.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from .llm import Client

INTAKE_SYSTEM = """You are the intake planner for an unattended ("lights out") coding run.
A small local model will do the actual work for hours with nobody watching, so anything
ambiguous now becomes silent garbage later.

Ask about what would change the output: language and version, file layout, testing
expectations, edge cases, style constraints, what "done" means per item, and the exact
count and source of the work items. Do not ask about things you can reasonably default.
Reply with JSON only."""

QUESTION_PROMPT = """ASK_QUESTIONS

The user's request:
---
{request}
---
{prior}

Ask the questions you still need answered before an unsupervised model could do this
job correctly. At most {max_q} questions, each one a single sentence. If you already
have everything you need, return an empty list and set "ready": true.

Reply with JSON only:
{{"ready": <true|false>, "questions": ["...", "..."]}}"""

PLAN_SYSTEM = """You decompose an agreed-on coding job into a checkpointed work plan for
an unattended run driven by a small local model. Reply with JSON only."""

# When the work items are already known (a file of 60 LeetCode problems, a list of
# modules to reformat), do NOT ask the model to enumerate them. A 7B model asked for 60
# JSON objects truncates somewhere in the thirties and you find out four hours later.
# It only supplies the framing; the units are built from the list verbatim.
ITEMS_PROMPT = """The user's request:
---
{request}
---

Clarifying Q&A:
---
{qa}
---

The work items are already enumerated ({count} of them). Here are the first few:
{sample}

Do not restate the items. Supply only the framing for the run.

"verify_template" is a shell command proving one item works, run from the workspace
root, with {{n}} for the 1-based item number and {{slug}} for a filesystem-safe version
of the item's text (e.g. "python -m pytest tests/test_{{n:03d}}.py -q"). Use "none" if
there is no way to check an item automatically.

"deliverable_template" describes what one finished item looks like, same placeholders.

Reply with JSON only:
{{
  "goal": "one paragraph describing the finished state",
  "success_criteria": ["..."],
  "red_flags": ["the specific ways a degrading model would fake progress on THIS job"],
  "deliverable_template": "...",
  "verify_template": "..."
}}"""

PLAN_PROMPT = """The user's request:
---
{request}
---

Clarifying Q&A:
---
{qa}
---
TOTAL_UNITS: {total_units}

Produce the work plan. Rules:

* Each unit is ONE self-contained piece of work a small model can finish in a single
  turn without holding the rest of the job in its head.
* "verify" is a shell command that proves that unit works, run from the workspace root
  (e.g. "python -m pytest solutions/test_problem_001.py -q"), or the string "none".
* "checkpoint": true means the quality sentinel inspects the work right after this unit.
  Default to true for every unit unless units are individually tiny.
* "red_flags" are the specific ways a degrading model would fake progress on THIS job --
  be concrete, not generic.

Reply with JSON only:
{{
  "goal": "one paragraph describing the finished state",
  "success_criteria": ["...", "..."],
  "red_flags": ["...", "..."],
  "units": [
    {{"id": "u001", "title": "...", "deliverable": "...", "verify": "...", "checkpoint": true}}
  ]
}}"""


def _ask(prompt):
    try:
        return input(prompt)
    except EOFError:
        return ""


def run_intake(cfg, run, request=None, answers=None, max_rounds=3, max_q=5,
               total_units=None, interactive=True, items=None):
    """Harness 1. Returns the spec dict (already saved to the run).

    `items` is an optional pre-enumerated list of work items (one string each). When
    given, the units are built from it verbatim and the model only supplies the framing.
    """
    client = Client(cfg, "intake", run_dir=run.root)

    if request is None:
        print("\n=== HARNESS 1: INTAKE ===")
        print("Describe the job. Finish with an empty line.\n")
        lines = []
        while True:
            line = _ask("> ")
            if not line.strip():
                break
            lines.append(line)
        request = "\n".join(lines).strip()
    if not request:
        raise SystemExit("no request given")

    run.event("intake_request", request=request)

    qa = list(answers or [])          # [{"q":..., "a":...}]
    rounds = 0
    while rounds < max_rounds:
        prior = ""
        if qa:
            prior = "\nAlready answered:\n" + "\n".join(
                "Q: %s\nA: %s" % (p["q"], p["a"]) for p in qa
            )
        resp = client.chat_json(
            INTAKE_SYSTEM,
            QUESTION_PROMPT.format(request=request, prior=prior, max_q=max_q),
        ) or {}
        questions = [q for q in (resp.get("questions") or []) if str(q).strip()]
        if not questions:
            break
        if not interactive:
            # Unattended intake: record the questions as unanswered and move on with
            # defaults. The spec notes them so you can see what it had to guess at.
            for q in questions:
                qa.append({"q": q, "a": "(unanswered -- intake ran non-interactively; "
                                        "model chose a sensible default)"})
            break
        print("\n--- the model needs to know: ---")
        for q in questions:
            print("\nQ: %s" % q)
            a = _ask("A: ").strip()
            qa.append({"q": q, "a": a or "(no preference -- you decide)"})
        rounds += 1
        if resp.get("ready"):
            break

    run.event("intake_qa", qa=qa, rounds=rounds)

    qa_text = "\n".join("Q: %s\nA: %s" % (p["q"], p["a"]) for p in qa) or "(none)"

    if items:
        sample = "\n".join("  %d. %s" % (i, t) for i, t in enumerate(items[:5], 1))
        if len(items) > 5:
            sample += "\n  ... and %d more" % (len(items) - 5)
        framing = client.chat_json(
            PLAN_SYSTEM,
            ITEMS_PROMPT.format(request=request, qa=qa_text,
                                count=len(items), sample=sample),
        ) or {}
        plan = dict(framing)
        plan["units"] = _units_from_items(items, framing)
    else:
        plan = client.chat_json(
            PLAN_SYSTEM,
            PLAN_PROMPT.format(request=request, qa=qa_text,
                               total_units=total_units or "as many as the job needs"),
            max_tokens=cfg["provider"]["max_tokens"] * 2,
        )
    if not plan or not plan.get("units"):
        raise SystemExit("intake failed: the model did not return a usable unit list")

    spec = _normalize(plan, request, qa, cfg)
    run.save_spec(spec)

    st = run.load_state()
    st["status"] = "planned"
    run.save_state(st)
    run.event("intake_plan", units=len(spec["units"]),
              checkpoints=sum(1 for u in spec["units"] if u["checkpoint"]))

    print("\n=== PLAN ===")
    print("Goal: %s" % spec["goal"])
    print("Units: %d   Checkpoints: %d"
          % (len(spec["units"]), sum(1 for u in spec["units"] if u["checkpoint"])))
    print("Red flags the sentinel will watch for:")
    for rf in spec["red_flags"]:
        print("  - %s" % rf)
    print("\nSaved to %s" % run.spec_path)
    return spec


def _slug(text, maxlen=40):
    out = re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")
    return (out[:maxlen].rstrip("_") or "item")


def _fill(template, n, slug, fallback):
    """Expand {n}, {n:03d} and {slug} in an intake template."""
    if not template or not str(template).strip():
        return fallback
    try:
        return str(template).format(n=n, slug=slug)
    except (KeyError, IndexError, ValueError):
        return str(template)


def _units_from_items(items, framing):
    """Build units from a known item list. The list is authoritative, not the model."""
    deliverable_t = framing.get("deliverable_template") or ""
    verify_t = framing.get("verify_template") or "none"
    units = []
    for i, title in enumerate(items, start=1):
        slug = _slug(str(title))
        units.append({
            "id": "u%03d" % i,
            "title": str(title).strip(),
            "deliverable": _fill(deliverable_t, i, slug, "complete work for: %s" % title),
            "verify": _fill(verify_t, i, slug, "none"),
            "checkpoint": True,
        })
    return units


def load_items(path):
    """Read work items from a file: one per line, or a JSON array of strings."""
    text = Path(path).read_text(encoding="utf-8")
    stripped = text.strip()
    if stripped.startswith("["):
        data = json.loads(stripped)
        return [str(x).strip() for x in data if str(x).strip()]
    items = []
    for line in text.splitlines():
        line = line.strip()
        # tolerate "1. Two Sum", "- Two Sum", "1) Two Sum"
        line = re.sub(r"^\s*(?:[-*]|\d+[.)])\s*", "", line)
        if line and not line.startswith("#"):
            items.append(line)
    return items


def _normalize(plan, request, qa, cfg):
    """Small models return sloppy shapes. Force the schema before anything depends on it."""
    every = max(1, int(cfg["run"].get("checkpoint_every", 1)))
    units = []
    for i, u in enumerate(plan.get("units") or [], start=1):
        if isinstance(u, str):
            u = {"title": u}
        checkpoint = u.get("checkpoint")
        if checkpoint is None:
            checkpoint = (i % every == 0)
        verify = (u.get("verify") or "none").strip()
        units.append({
            "index": i,
            "id": str(u.get("id") or ("u%03d" % i)),
            "title": str(u.get("title") or ("Unit %d" % i)),
            "deliverable": str(u.get("deliverable") or u.get("title") or ""),
            "verify": verify,
            "checkpoint": bool(checkpoint),
        })
    if units and not units[-1]["checkpoint"]:
        units[-1]["checkpoint"] = True      # always inspect the final state
    return {
        "request": request,
        "qa": qa,
        "goal": str(plan.get("goal") or request)[:4000],
        "success_criteria": [str(s) for s in (plan.get("success_criteria") or [])],
        "red_flags": [str(s) for s in (plan.get("red_flags") or [])],
        "units": units,
    }
