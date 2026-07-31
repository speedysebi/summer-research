# Lights-out harness

A supervision harness for running a **small local model unattended for hours**. It
assumes the model will degrade — because over an 8-hour stretch a 7B model always does
— and makes that recoverable instead of fatal.

Three harnesses:

| | | |
|---|---|---|
| **1. Intake** | `lightsout/harness1_intake.py` | You state the job; the model asks what it needs; the answers become a checkpointed work plan. |
| **2. Sentinel** | `lightsout/harness2_sentinel.py` | Runs out-of-context at every checkpoint. Scores the work. Notes minor decay, **halts** on real failure. |
| **3. Recovery** | `lightsout/harness3_recovery.py` | Reads the sentinel's trail, finds where the rot started, rewinds the workspace past it, and restarts with a corrective directive. |

The result is a sawtooth — the run advances, decays, rewinds past the decay, and
advances again from known-good ground:

```
segment 1   units   1 -> 13   ############~
segment 2   units  12 -> 25   #############~
segment 3   units  24 -> 37   #############~
segment 4   units  36 -> 40   #####

legend: # >=75 clean   ~ 45-74 degrading   . <45 failed
```

No dependencies. Python 3.9+ and `git`, stdlib only otherwise.
Tests: `python -m unittest discover tests` (61 tests)

---

## Quick start

```bash
# 1. See the whole thing work with no model server running at all.
python run.py demo --units 40

# 2. Point it at your local model.
#    Edit config.json: provider.kind = "ollama", set the model names.

# 3. Check the setup BEFORE you lose a night to a typo in a model name.
python run.py doctor

# 4a. Or skip intake entirely and run the built-in benchmark.
python run.py bench --difficulty easy --count 200
python run.py start
python run.py score        # graded against hidden tests

# 4b. Plan a real job (Harness 1 — this is the interactive part).
python run.py intake
python run.py intake --items-file examples/problems.txt   # when you have the list

# 5. Start it and walk away.
python run.py start

# 6. Later.
python run.py status                      # where it is now
python run.py report                      # the segment trace
python run.py analyze --csv scores.csv    # research metrics + data to plot
```

`python run.py demo` runs the full pipeline against a built-in fake model that degrades
on a fixed schedule. It is how you test changes to the sentinel or the recovery logic
without burning hours of GPU time, and it is the fastest way to see what the system
does.

---

## The three harnesses

### Harness 1 — Intake (`run.py intake`, or `/lightsout`)

The only part a human talks to. You describe the job ("I have 60 LeetCode questions I
need solved"), the model asks whatever it needs, and the answers get compiled into
`runs/<id>/spec.json`:

- **goal** — one paragraph. Harness 3 reads this later to know what it is restoring.
- **success_criteria** — what "done and correct" means.
- **red_flags** — the task-specific ways *this* job goes wrong. This becomes the
  sentinel's watch list, and it is the highest-leverage field in the file.
- **units** — the atoms of work, each with a `verify` shell command.
- **checkpoint** — which units the sentinel inspects.

That last field is the point of doing intake at all. The checkpoint schedule is decided
up front, by the part of the system that still has a clean context. Deciding when to
stop and check yourself is exactly the judgment a degrading model gets wrong.

There is also a Claude Code slash command in `slash/lightsout.md` — see *Installing
`/lightsout`* below. It is the better way to do intake, because Claude has your whole
conversation and can read the source of the work items rather than guessing at them.

### Harness 2 — Sentinel (`lightsout/harness2_sentinel.py`)

Runs at every checkpoint. Two things make it work:

**It is out of context.** The sentinel gets a fresh client and sees only artifacts — the
goal, the git diff since the last checkpoint, the files touched, the verify output. It
never sees the worker's reasoning or its explanations. A critic that inherits the bad
context inherits the bad conclusions with it, which is why "ask the model to check its
own work" fails exactly when you need it.

**It does not trust the model alone.** `detectors.py` runs first — deterministic checks
for stubs, `NotImplementedError`, TODO markers, tests that cannot fail, generation
loops, truncated output, files that changed nothing, and large deletions. Each imposes
a score ceiling, and the final score is the *worse* of detector ceiling and model
judgment. A sentinel model that has itself gone soft still cannot wave through a
stubbed-out file. A failing `verify` command outranks every opinion in the system.

Three verdicts:

- **PASS** — continue.
- **NOTE** — log it, carry the concern into the worker's next prompt, continue.
- **HALT** — stop the run, hand control to Harness 3.

HALT fires on any of four conditions, and the third is the one that matters most:

1. a hard detector signal (stub, no work, failed verify),
2. score below `hard_floor` (absolute badness),
3. score far below the **rolling baseline** — *relative* decay, the difference between
   "this is bad" and "this is getting worse", which is what you actually asked for,
4. `consecutive_notes_halt` sub-par checkpoints in a row — the slow bleed that never
   trips an absolute threshold.

The baseline only updates on PASS. Letting failures drag it down would make the run
tolerate more and more garbage as the night went on.

### Harness 3 — Recovery (`lightsout/harness3_recovery.py`)

Fires only on HALT. Built around one observation: **the checkpoint that halts is almost
never where things went wrong.** By the time output collapses into stubs, the model has
been drifting for several units.

1. **Read back** — every sentinel report and journal event, plus the goal from Harness 1.
   This is why Harness 2 writes a note even when it passes a checkpoint: those notes are
   the trail of where the rot began.
2. **Localize** — walk backwards through the score series to the last genuinely clean
   checkpoint (the *anchor*). The first degraded checkpoint after it is the *onset*.
3. **Diagnose** — a fresh model call gets the score series, the notes, and the goal, and
   returns a root cause plus a **corrective directive**. If it names an earlier onset
   than the score walk found, the earlier one wins — rewinding too far is cheap, not far
   enough is not.
4. **Rewind** — tag the abandoned segment, `git checkout` the anchor's commit, move the
   cursor back, inject the directive into every later worker prompt.

**Nothing is deleted.** The abandoned segment is tagged `attempt/<n>-units-<a>-to-<b>`
before the reset, so every failure trace stays in the repo for analysis afterwards —
which for a research project is usually the data you actually wanted.

If the same anchor fails repeatedly, the rewind depth escalates (`overlap_escalation`),
so the system backs off further instead of looping on an anchor that was never as clean
as it scored. If *no* checkpoint in the run was ever clean, it resets to the empty
workspace and starts over with the directive, rather than building on poisoned files.

---

## Getting research data out

`python run.py analyze` turns the journal into the numbers a run is actually for:

```
THROUGHPUT
  units delivered   40 / 40
  units executed    49   (9 discarded by rewinds)
  efficiency        81.6%  (delivered / executed)
  runway per attempt [13, 14, 14, 5]  mean 11.5 units before degrading

WHO CAUGHT WHAT  (is the sentinel model earning its GPU time?)
  detectors only    12 checkpoints the model judge scored too high
  model only        0 checkpoints the detectors could not see

DECAY PROFILE  (mean score by depth into a segment)
  +0    92.0 ##################
  +11   92.0 ##################
  +12   65.0 #############
```

Three things worth pulling out of that:

- **Runway** — how many units this model manages before it degrades. That is the
  headline number for "is a 7B model usable for this job at all", and it is what you
  compare across models and prompt strategies.
- **Efficiency** — delivered work over executed work. Rewinding costs you real compute;
  this is the price of the safety net, and it is the number to argue about when tuning
  `good_threshold` and `base_overlap`.
- **Who caught what** — how often the deterministic detectors scored a checkpoint lower
  than the sentinel model did. If that number is high, your judge model is not pulling
  its weight and the detectors are doing the supervision. If it is zero, the judge is
  catching things the checks cannot see and is worth the GPU time.

`--csv` writes one row per checkpoint (score, model score, detector ceiling, verdict,
baseline, failure modes) — that is the file you plot.

---

## Preflight

`python run.py doctor` before a long run. It checks git, that the provider answers,
that **every role's model is actually pulled** (a server that is up but empty will 404
every call four hours from now), and — the one that matters — that the sentinel model
can emit parseable JSON. A judge that cannot produce JSON fails open: the harness keeps
running and looks fine while supervising nothing. Exits nonzero, so you can gate a run
on it.

---

## Giving it the work items directly

For "I have 60 LeetCode questions", do not make the model enumerate them:

```bash
python run.py intake --items-file problems.txt
```

One item per line (`1. Two Sum`, `- Two Sum`, and bare lines all work; `#` comments
and blank lines are ignored), or a JSON array. See `examples/problems.txt`.
The list is authoritative — the model is asked only for the goal, the success criteria,
the red flags, and a `verify_template` / `deliverable_template` with `{n}` and `{slug}`
placeholders. Asking a 7B model for 60 JSON objects gets you about thirty-five of them
and a truncated brace, and you find out four hours later.

---

## The problem bank

The repository ships a corpus to run the harness against:

| bank | count | what it is |
|---|---|---|
| `easy` | 200 | one pass, one idea, no auxiliary structure |
| `medium` | 200 | needs a data structure, a second pass, or a non-obvious invariant |
| `hard` | 200 | 2-D DP, graphs with weights, backtracking, monotonic stacks, bitmask DP |
| `codingbat_style` | 110 | short warm-ups, below `easy` |

710 problems, 73 families, ~11,200 test cases. These are **LeetCode-style**, not
LeetCode: original statements written to the same shape, so there is no scraped or
copyrighted text in the repo.

**The problems are generated, and that is the point.** `bench/families_*.py` define
families with a parameterised reference solution; `bench/generate.py` runs each
reference against generated inputs to produce the expected outputs. Nobody hand-writes
an expected answer, so a wrong answer in the bank is a build failure rather than a
model silently marked wrong for eight hours.

Two gates run on every problem before it is written:

- the reference must execute on every generated input, and
- **the outputs must not all be identical.** A problem whose answer never changes can
  be passed by returning a constant, so it tests nothing. This gate rejected fifteen
  problems during the build — "is this sorted" over random lists is always False,
  perfect numbers never appear in a random draw, a random UDLR walk never returns to
  the origin. Each needed a generator that actually reaches both branches.

Rebuild with `python -m bench.generate`, or check without writing:

```bash
python -m bench.generate --check
```

---

## Evaluating the model as it goes

Harness 2 judges whether work *looks* right. The evaluator judges whether it *is*
right, and that is ground truth.

`python run.py bench` builds a run straight from the bank — Harness 1's
non-conversational path, since the bank already defines what done means. Every unit
gets a `verify` that runs its hidden tests:

```
python run.py eval-one e042 solutions/e042.py
```

Each candidate runs in a separate process with a timeout, so an infinite loop or a
`sys.exit` in generated code costs one unit rather than the night.

The measured pass rate then flows through the whole system:

- **as a graded detector signal** — `detect_wrong_answer` sets the score ceiling to
  `rate × 70`, so "failed two edge cases" is a NOTE and "nothing works" is a HALT.
  Partial credit matters: a binary pass/fail throws away most of the signal.
- **into the journal**, per unit, so `analyze` can plot accuracy against how deep into
  a segment the model was. That curve is the measured version of the decay this whole
  project is about:

```
MEASURED CORRECTNESS  (from the problem bank's hidden tests)
  solved outright   87 / 140  (62.1%)
  mean pass rate    71.4% of test cases
    easy     n=100  solved  78.0%   mean pass  84.2%
    medium   n=40   solved  22.5%   mean pass  39.6%
  accuracy by depth into a segment:
    +0   100.0% ####################
    +11   92.3% ##################
    +12    6.2% #
```

- **`python run.py score`** re-grades a finished workspace from scratch, which is how
  you check a run after the fact rather than trusting what it logged at the time.

---

## Layout

```
run.py                       CLI: intake / bench / start / resume / status /
                                  report / analyze / score / doctor / demo
config.json                  provider, thresholds, budgets
lightsout/
  config.py                  defaults + merge
  llm.py                     ollama / openai-compatible / mock providers, tolerant JSON parsing
  state.py                   durable run state (spec, cursor, journal, checkpoints)
  workspace.py               git-backed snapshots, rewind, tagging
  detectors.py               deterministic failure detectors (Harness 2's non-model half)
  harness1_intake.py         HARNESS 1
  worker.py                  executes one unit (the part that degrades)
  harness2_sentinel.py       HARNESS 2
  harness3_recovery.py       HARNESS 3
  orchestrator.py            the lights-out loop
  analysis.py                research metrics over the journal
  doctor.py                  preflight checks
  evaluator.py               runs a candidate against a problem's hidden tests
  benchrun.py                turns the bank into a run spec; scores a workspace
bench/
  core.py                    family registry, input generators, case builder
  families_easy.py           easy tier
  families_medium*.py        medium tier
  families_hard*.py          hard tier
  codingbat.py               warm-up tier
  generate.py                builds problems/*.json, with the validity gates
  problems/*.json            the generated banks (600 + 110)
tests/test_harness.py        detectors, recovery policy, rewind, end-to-end
tests/test_bench.py          bank integrity and the evaluator
examples/problems.txt        sample work-item list for --items-file
slash/lightsout.md           Claude Code slash command -- the /tool front door to Harness 1
runs/<run_id>/
  spec.json                  Harness 1 output
  state.json                 cursor, baseline, rewind history, active directive
  journal.jsonl              append-only event log -- what Harness 3 reads back
  checkpoints/cp_NNNN.json   one sentinel report per checkpoint
  workspace/                 the code being produced (a git repo)
```

Everything is written to disk as it happens. Kill the process at any point and
`python run.py resume` picks up at the same cursor, with the same baseline and the same
corrective directive.

---

## Configuration

The knobs worth knowing, all in `config.json`:

| Key | Default | What it does |
|---|---|---|
| `provider.kind` | `ollama` | `ollama`, `openai` (llama.cpp / LM Studio / vLLM), or `mock` |
| `provider.sentinel_model` | 14b | **Worth making bigger than the worker.** The judge should be harder to fool than the thing it judges. |
| `run.wall_clock_budget_h` | 8.0 | Stops cleanly when the night is over |
| `run.max_halts` | 8 | After this many recoveries, stop and wait for a human |
| `run.max_consecutive_errors` | 3 | Units failing to execute back-to-back (unreachable model server) aborts the run |
| `sentinel.hard_floor` | 45 | Absolute score that triggers HALT |
| `sentinel.note_floor` | 70 | Below this is a NOTE |
| `sentinel.baseline_drop` | 20 | Points below the rolling baseline that counts as decay |
| `sentinel.consecutive_notes_halt` | 3 | Slow-bleed trigger |
| `sentinel.good_threshold` | 75 | Bar a checkpoint must clear to be a rewind anchor. Lower to ~65 to accept "minor worsening" anchors and rewind less far. |
| `recovery.base_overlap` | 1 | Units redone on restart. `1` restarts *at* the anchor unit; `0` restarts just after it. |
| `recovery.overlap_escalation` | 4 | Extra rewind each time the same anchor fails again |

### Tuning for a smaller model

A 3B model needs a shorter leash than a 14B one: smaller units in the plan, a
`verify` command on every unit, `note_floor` raised, and `consecutive_notes_halt`
lowered to 2. The sentinel and recovery models should be the largest ones you can
afford to keep loaded, since a run is only as good as its judge.

---

## Installing `/lightsout`

Copy the slash command where Claude Code will find it:

```powershell
Copy-Item "slash\lightsout.md" "$env:USERPROFILE\.claude\commands\lightsout.md"
```

Then `/lightsout solve 60 LeetCode questions in Python with tests` runs Harness 1 as a
conversation, and writes the `spec.json` the rest of the system consumes.

---

## Notes and caveats

- **`verify` commands execute.** Units run their verify command with `shell=True` inside
  the workspace. That is the point — it is the only ground truth the sentinel gets — but
  it means the plan should come from you, not from an untrusted source. Set
  `run.allow_verify_exec: false` to disable.
- **The worker gets a deliberately narrow context**: the goal, the one unit, and the
  active directive. It does not get a transcript of everything it has already done,
  because that accumulation is the main thing that rots a small model over a long run.
- **File output uses a block protocol**, not JSON — small models reliably mangle code
  inside JSON string escapes but handle `<<<FILE path>>> … <<<END>>>` fine.
- **A run is pinned to the provider it started with.** `state.json` records the
  provider block at first start, and `resume` uses it even if `config.json` has changed
  since — resuming an overnight job against a different model would silently invalidate
  the whole score history. `--provider-from-config` overrides.
- **An unreachable model server aborts the run** rather than churning through the plan
  producing nothing. Fix the config and `resume`.
- **The workspace is a git repo.** If you point a run at a directory that is already a
  repo, it will use it; snapshots are ordinary commits on whatever branch is checked out,
  and rewinds detach the HEAD.
