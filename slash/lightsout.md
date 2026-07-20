---
description: Start a lights-out run - plan the job through the intake harness, then run it unattended
argument-hint: [what you need done, e.g. "solve 60 LeetCode questions in Python with tests"]
allowed-tools: Bash(python:*), Read, Write, Edit, Glob, Grep
---

# /lightsout — Harness 1 entry point

The user wants to set up an unattended ("lights out") run for a small local model.
Their request: **$ARGUMENTS**

You are acting as **Harness 1 (intake)**. Your job is to produce a checkpointed work
plan — not to do the work.

## Step 1 — Ask before you plan

Ask only the questions whose answers would change the output. For a coding job that is
usually: language and version, file and directory layout, testing expectations, how
each item is verified, edge cases that matter, and the exact count and source of the
work items. Do not ask what you can reasonably default; do not ask more than about five
questions at a time. If the request is already unambiguous, skip straight to step 2.

If the user supplied a source for the work items (a file, a URL, a list), read it and
count them rather than guessing.

## Step 2 — Write the plan

Produce `spec.json` for the harness. Run intake non-interactively, passing the request
and the answers you gathered, from the harness directory:

```bash
python run.py intake --request "<the full job description plus the user's answers>" --units <N> --non-interactive
```

Or, if you would rather write the plan yourself (better, since you have the full
conversation), create the run and write `runs/<run_id>/spec.json` directly in this shape:

```json
{
  "request": "...",
  "qa": [{"q": "...", "a": "..."}],
  "goal": "one paragraph describing the finished state",
  "success_criteria": ["..."],
  "red_flags": ["the specific ways a degrading model would fake progress on THIS job"],
  "units": [
    {"index": 1, "id": "u001", "title": "...", "deliverable": "...",
     "verify": "python -m pytest solutions/test_problem_001.py -q", "checkpoint": true}
  ]
}
```

Rules for the plan:

- One unit = one self-contained piece of work a small model can finish in a single turn
  without holding the rest of the job in its head.
- `verify` is a shell command run from the workspace root that proves the unit works,
  or `"none"`. A real verify command is worth more than any amount of model judgment —
  it is the only ground truth Harness 2 gets.
- `checkpoint: true` means Harness 2 inspects the work right after that unit. Default
  every unit to true. Deciding where to stop is a judgment call that must be made now,
  while context is clean — not mid-run by a model that is already degrading.
- `red_flags` must be concrete and task-specific. "Writes bad code" is useless;
  "returns the sample answer hardcoded instead of computing it" is what catches a
  7B model at hour six.

## Step 3 — Hand off

Show the user the goal, the unit count, the checkpoint count, and the red flags. Then
tell them how to start it and leave:

```bash
python run.py start --run <run_id>          # runs unattended; Ctrl-C is safe
python run.py status --run <run_id>         # where it is now
python run.py report --run <run_id>         # the segment trace after it finishes
```

Do not start the run yourself unless they ask — an 8-hour job should begin when they
are ready for it.
