"""HARNESS 3 -- Recovery. Fires only when Harness 2 calls HALT.

The insight this harness is built around: the checkpoint that HALTs is almost never
where things actually went wrong. By the time output collapses into stubs, the model
has usually been drifting for several units. So recovery does not rewind to the failure
-- it rewinds past the onset.

Four steps:

  1. READ BACK    Every sentinel report and journal event from this run, plus the goal
                  from Harness 1. This is why Harness 2 writes a note even when it
                  passes a checkpoint: those notes are the trail of where the rot began.

  2. LOCALIZE     Walk backwards from the HALT through the score series to the last
                  checkpoint that was genuinely clean. The first sub-par checkpoint
                  after that is the onset.

  3. DIAGNOSE     A fresh model call gets the score series, the notes, and the goal, and
                  produces a root cause plus a corrective directive that will be injected
                  into every worker prompt after the restart.

  4. REWIND       Tag the abandoned segment (nothing is deleted), reset the workspace to
                  the chosen checkpoint's commit, and move the cursor back. Returning to
                  a point BEFORE the onset, with overlap, is what produces the sawtooth:

                      segment 1:  units  1 -> 15   HALT
                      segment 2:  units 12 -> 27   HALT
                      segment 3:  units 15 -> 35   ...

Repeated failure from the same target escalates the rewind depth, so the system does not
sit in a loop re-failing from an anchor that was never actually clean.
"""
from __future__ import annotations

from .llm import Client

RECOVERY_SYSTEM = """You diagnose failures in unattended coding runs driven by small local
models. You are given the quality history of a run that just stopped: a score per
checkpoint and the auditor's notes. Find where the degradation actually began -- usually
several checkpoints before the collapse -- and write a directive that prevents a repeat.

The directive is prepended to every future worker prompt. It must be concrete and
imperative, about behavior, not encouragement. Reply with JSON only."""

RECOVERY_PROMPT = """PROJECT GOAL (from intake, before any work started)
{goal}

SUCCESS CRITERIA
{criteria}

CHECKPOINT HISTORY (oldest first)
{history}

HALT WAS TRIGGERED AT
  checkpoint {cp} / unit {unit} ({title})
  reasons: {reasons}
  failure modes: {modes}
  evidence: {evidence}

PRIOR RECOVERIES IN THIS RUN
{priors}

Diagnose and reply with JSON only:
{{"diagnosis": "what went wrong and from roughly which checkpoint the decline started",
  "onset_checkpoint": <int, the checkpoint number where degradation began>,
  "root_cause": "context_saturation"|"ambiguous_spec"|"task_too_large"|"model_capability"|"compounding_error"|"other",
  "corrective_directive": "imperative instructions injected into every later worker prompt",
  "confidence": <0.0-1.0>}}"""


def _format_history(reports):
    lines = []
    for r in reports:
        note = r.get("note") or ""
        modes = ",".join(r.get("failure_modes") or []) or "-"
        lines.append("cp%-3d seg%-2d unit %-4d score %-3d %-5s modes=%-28s %s"
                     % (r["checkpoint"], r.get("segment", 1), r["unit_index"],
                        r["score"], r["verdict"], modes, note[:90]))
    return "\n".join(lines) or "(no checkpoints)"


def find_onset(reports, good_threshold):
    """Walk back from the end to the last genuinely clean checkpoint.

    Returns (onset_report, anchor_report). The anchor is the last checkpoint that was
    clean; the onset is the first degraded one after it.
    """
    anchor = None
    onset = None
    for r in reversed(reports[:-1]):          # skip the HALT itself
        if r["verdict"] == "PASS" and r["score"] >= good_threshold:
            anchor = r
            break
        onset = r
    if onset is None:
        onset = reports[-1]
    return onset, anchor


def choose_rewind_target(cfg, state, reports, anchor):
    """Pick the unit index to restart from, escalating if we have been here before.

    `target_index` is a 0-based cursor, and unit indices are 1-based, so a target of
    N means "the next unit to run is unit N+1". With base_overlap = 1 the restart
    therefore redoes the anchor unit itself, which is what creates the overlap in
    1->15, 12->27, 15->35.
    """
    rcfg = cfg["recovery"]
    anchor_index = anchor["unit_index"] if anchor else 0

    # How many times have we already rewound to roughly this anchor? Failing again
    # from the same place means the anchor was not as clean as it scored, so back off
    # further rather than looping on it.
    repeats = sum(1 for rw in state.get("rewinds", [])
                  if abs(rw.get("anchor_index", -999) - anchor_index) <= 2)
    depth = rcfg["base_overlap"] + repeats * rcfg["overlap_escalation"]
    depth = min(depth, rcfg["max_rewind_depth"])

    target_index = max(0, anchor_index - depth)

    # Newest clean checkpoint at or before the target supplies the commit to restore.
    restore = None
    for r in reports:
        if r["unit_index"] <= target_index and r["score"] >= cfg["sentinel"]["good_threshold"]:
            restore = r
    return target_index, depth, repeats, restore, anchor_index


def recover(cfg, run, spec, state, workspace, halt_report, quiet=False):
    """Harness 3. Mutates and returns `state`, with the workspace rewound."""
    reports = run.checkpoint_reports()
    scfg = cfg["sentinel"]

    def emit(msg):
        if not quiet:
            print(msg, flush=True)

    emit("\n=== HARNESS 3: RECOVERY ===")
    emit("HALT at unit %d (%s) -- score %d"
          % (halt_report["unit_index"], halt_report["unit_title"], halt_report["score"]))
    for reason in halt_report["halt_reasons"]:
        emit("  reason: %s" % reason)

    # --- 2. localize ------------------------------------------------------- #
    onset, anchor = find_onset(reports, scfg["good_threshold"])
    emit("  degradation onset: checkpoint %s (unit %s)"
          % (onset.get("checkpoint"), onset.get("unit_index")))
    emit("  last clean anchor: %s"
          % ("checkpoint %s (unit %s, score %s)"
             % (anchor["checkpoint"], anchor["unit_index"], anchor["score"])
             if anchor else "none -- no checkpoint in this run was clean"))

    # --- 3. diagnose ------------------------------------------------------- #
    priors = "\n".join(
        "segment %s: rewound unit %s -> %s (%s)"
        % (rw.get("segment"), rw.get("from_index"), rw.get("to_index"), rw.get("reason", "")[:70])
        for rw in state.get("rewinds", [])
    ) or "(none -- this is the first failure)"

    client = Client(cfg, "recovery", run_dir=run.root)
    diag = client.chat_json(
        RECOVERY_SYSTEM,
        RECOVERY_PROMPT.format(
            goal=spec["goal"],
            criteria="\n".join("- " + c for c in spec["success_criteria"]) or "- (none)",
            history=_format_history(reports),
            cp=halt_report["checkpoint"], unit=halt_report["unit_index"],
            title=halt_report["unit_title"],
            reasons="; ".join(halt_report["halt_reasons"]) or "(none recorded)",
            modes=", ".join(halt_report["failure_modes"]) or "(none)",
            evidence=" | ".join(halt_report["evidence"][:4]) or "(none)",
            priors=priors,
        ),
    ) or {}

    directive = str(diag.get("corrective_directive") or "").strip()
    if not directive:
        # Recovery model failed us too -- fall back to the sentinel's own advice.
        directive = (halt_report.get("advice")
                     or "Produce complete, runnable code for every unit. No placeholders, "
                        "no stubs, no weakened tests.")

    # The model may have spotted an earlier onset than the score walk did; trust the
    # earlier of the two, since rewinding too far is cheap and too little is not.
    try:
        model_onset = int(diag.get("onset_checkpoint"))
        for r in reports:
            if r["checkpoint"] == model_onset and r["unit_index"] < onset["unit_index"]:
                onset = r
                anchor = next((a for a in reversed(reports)
                               if a["unit_index"] < r["unit_index"]
                               and a["score"] >= scfg["good_threshold"]), anchor)
                break
    except (TypeError, ValueError):
        pass

    # --- 4. rewind --------------------------------------------------------- #
    target_index, depth, repeats, restore, anchor_index = choose_rewind_target(
        cfg, state, reports, anchor)

    from_index = halt_report["unit_index"]
    segment = state.get("segment", 1)

    # Preserve the abandoned work before touching anything.
    tag = "attempt/%d-units-%d-to-%d" % (segment, state.get("segment_start", 0) + 1, from_index)
    try:
        workspace.tag(tag)
    except Exception as e:                        # noqa: BLE001 - tagging is best effort
        emit("  (could not tag abandoned segment: %s)" % e)

    if restore:
        restore_sha = restore["sha"]
        workspace.restore(restore_sha)
        emit("  workspace restored to checkpoint %s (%s)"
              % (restore["checkpoint"], restore_sha[:8]))
    elif state.get("initial_sha"):
        # Nothing in this run was ever clean. Go all the way back to the empty
        # workspace and start over with the corrective directive -- leaving the bad
        # files in place would poison every later unit.
        restore_sha = state["initial_sha"]
        workspace.restore(restore_sha)
        target_index = 0
        emit("  no clean checkpoint in this run -- restored to the empty workspace (%s)"
              % restore_sha[:8])
    else:
        restore_sha = None
        emit("  no snapshot to restore -- keeping current files, rewinding cursor only")

    # Units being replayed get a fresh attempt budget. Their old failures belong to
    # the segment we just abandoned, and carrying the counts forward would make the
    # loop skip past units on their first stumble in the new segment.
    for u in spec["units"]:
        if u["index"] > target_index:
            state.get("attempts", {}).pop(u["id"], None)

    state["segment"] = segment + 1
    state["segment_start"] = target_index
    state["cursor"] = target_index
    state["corrective_directive"] = directive
    state["consecutive_notes"] = 0
    state["baseline"] = None                 # re-establish the baseline after a rewind
    state["halts"] = state.get("halts", 0) + 1
    state["last_checkpoint_sha"] = restore_sha
    state["carried_notes"] = []
    state["status"] = "running"
    state.setdefault("rewinds", []).append({
        "segment": segment,
        "from_index": from_index,
        "to_index": target_index,
        "anchor_index": anchor_index,
        "onset_index": onset.get("unit_index"),
        "depth": depth,
        "repeats_at_anchor": repeats,
        "restore_sha": restore_sha,
        "abandoned_tag": tag,
        "root_cause": str(diag.get("root_cause") or "unknown"),
        "diagnosis": str(diag.get("diagnosis") or "")[:1000],
        "reason": "; ".join(halt_report["halt_reasons"])[:300],
        "directive": directive[:1000],
    })

    run.event("recovery", segment=segment, from_index=from_index, to_index=target_index,
              anchor_index=anchor_index, onset_index=onset.get("unit_index"),
              depth=depth, root_cause=str(diag.get("root_cause") or "unknown"),
              diagnosis=str(diag.get("diagnosis") or "")[:500],
              directive=directive[:500], abandoned_tag=tag, restore_sha=restore_sha)

    emit("  diagnosis: %s" % (str(diag.get("diagnosis") or "(none)")[:200]))
    emit("  root cause: %s" % diag.get("root_cause", "unknown"))
    emit("  directive: %s" % directive[:200])
    emit("  REWIND: unit %d -> unit %d (depth %d, abandoned work kept at tag %s)"
          % (from_index, target_index, depth, tag))
    emit("  resuming as segment %d\n" % state["segment"])
    return state
