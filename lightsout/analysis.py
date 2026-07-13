"""Analysis over a finished (or running) run.

The journal and the checkpoint reports already hold everything; this turns them into
the numbers you actually want out of a research run:

  throughput      how far the model got before each collapse
  waste           how much completed work got thrown away by rewinds
  judge value     how often the deterministic detectors caught something the sentinel
                  model missed -- i.e. whether the sentinel model is earning its GPU time
  decay profile   score as a function of distance into a segment, which is the curve
                  the whole project is about
"""
from __future__ import annotations

import csv
import statistics
from collections import Counter


def _mean(xs):
    return statistics.fmean(xs) if xs else 0.0


def summarize(run, note_floor=70):
    state = run.load_state()
    reports = run.checkpoint_reports()
    events = run.journal()
    try:
        total_units = len(run.load_spec()["units"])
    except FileNotFoundError:
        total_units = 0

    done_events = [e for e in events if e["kind"] == "unit_done"]
    attempted = len(done_events)
    completed = state.get("cursor", 0)
    discarded = max(0, attempted - completed)

    scores = [r["score"] for r in reports]
    halts = [r for r in reports if r["verdict"] == "HALT"]

    # How far the model got each time before it degraded. This is the headline number:
    # it is the model's usable runway under this harness, measured in units.
    segments = {}
    for r in reports:
        segments.setdefault(r.get("segment", 1), []).append(r)
    runway = []
    for seg in sorted(segments):
        rs = segments[seg]
        first, last = min(x["unit_index"] for x in rs), max(x["unit_index"] for x in rs)
        runway.append(last - first + 1)

    # Who actually caught the problems? Only count a "catch" when one side flagged the
    # checkpoint as sub-par and the other did not. Comparing the raw numbers instead
    # would count every clean checkpoint (model 92 < ceiling 100) as a model catch.
    caught_by_detector = sum(
        1 for r in reports
        if r.get("detector_ceiling", 100) < note_floor
        and r.get("model_score", 100) >= note_floor)
    caught_by_model = sum(
        1 for r in reports
        if r.get("model_score", 100) < note_floor
        and r.get("detector_ceiling", 100) >= note_floor)
    caught_by_both = sum(
        1 for r in reports
        if r.get("detector_ceiling", 100) < note_floor
        and r.get("model_score", 100) < note_floor)

    modes = Counter()
    for r in reports:
        for m in r.get("failure_modes") or []:
            modes[m] += 1

    # Decay profile: mean score by how deep into a segment the checkpoint was.
    by_depth = {}
    for seg, rs in segments.items():
        base = min(x["unit_index"] for x in rs)
        for r in rs:
            by_depth.setdefault(r["unit_index"] - base, []).append(r["score"])
    decay = {d: round(_mean(v), 1) for d, v in sorted(by_depth.items())}

    elapsed = state.get("elapsed_s") or 0.0
    return {
        "run_id": run.run_id,
        "status": state.get("status"),
        "total_units": total_units,
        "units_completed": completed,
        "units_attempted": attempted,
        "units_discarded": discarded,
        "efficiency": round(completed / attempted, 3) if attempted else 0.0,
        "segments": len(segments),
        "halts": len(halts),
        "rewinds": len(state.get("rewinds", [])),
        "runway_units": runway,
        "mean_runway": round(_mean(runway), 1),
        "checkpoints": len(reports),
        "mean_score": round(_mean(scores), 1),
        "min_score": min(scores) if scores else None,
        "score_stdev": round(statistics.pstdev(scores), 1) if len(scores) > 1 else 0.0,
        "caught_by_detector_only": caught_by_detector,
        "caught_by_model_only": caught_by_model,
        "caught_by_both": caught_by_both,
        "flagged_total": caught_by_detector + caught_by_model + caught_by_both,
        "failure_modes": dict(modes.most_common()),
        "root_causes": dict(Counter(rw.get("root_cause", "unknown")
                                    for rw in state.get("rewinds", []))),
        "decay_profile": decay,
        "elapsed_s": round(elapsed, 1),
        "sec_per_unit": round(elapsed / attempted, 1) if attempted else 0.0,
        "worker_errors": sum(1 for e in events if e["kind"] == "unit_error"),
    }


def to_csv(run, path):
    """One row per checkpoint -- feed this straight into a plot."""
    reports = run.checkpoint_reports()
    cols = ["checkpoint", "segment", "unit_index", "score", "model_score",
            "detector_ceiling", "verdict", "baseline_before", "failure_modes", "note"]
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(cols)
        for r in reports:
            w.writerow([
                r.get("checkpoint"), r.get("segment"), r.get("unit_index"),
                r.get("score"), r.get("model_score"), r.get("detector_ceiling"),
                r.get("verdict"),
                round(r["baseline_before"], 1) if r.get("baseline_before") else "",
                "|".join(r.get("failure_modes") or []),
                (r.get("note") or "").replace("\n", " "),
            ])
    return len(reports)


def render(summary):
    s = summary
    out = []
    out.append("=== ANALYSIS: %s ===" % s["run_id"])
    out.append("status            %s" % s["status"])
    out.append("")
    out.append("THROUGHPUT")
    out.append("  units delivered   %d / %d" % (s["units_completed"], s["total_units"]))
    out.append("  units executed    %d   (%d discarded by rewinds)"
               % (s["units_attempted"], s["units_discarded"]))
    out.append("  efficiency        %.1f%%  (delivered / executed)" % (s["efficiency"] * 100))
    out.append("  runway per attempt %s  mean %.1f units before degrading"
               % (s["runway_units"], s["mean_runway"]))
    out.append("  %.1f s/unit, %.1f min total" % (s["sec_per_unit"], s["elapsed_s"] / 60.0))
    out.append("")
    out.append("QUALITY")
    out.append("  checkpoints       %d   halts %d   rewinds %d"
               % (s["checkpoints"], s["halts"], s["rewinds"]))
    out.append("  score             mean %.1f  min %s  stdev %.1f"
               % (s["mean_score"], s["min_score"], s["score_stdev"]))
    if s["failure_modes"]:
        out.append("  failure modes     " + ", ".join(
            "%s x%d" % (k, v) for k, v in s["failure_modes"].items()))
    if s["root_causes"]:
        out.append("  root causes       " + ", ".join(
            "%s x%d" % (k, v) for k, v in s["root_causes"].items()))
    out.append("")
    out.append("WHO CAUGHT WHAT  (of %d sub-par checkpoints; is the judge earning its GPU time?)"
               % s["flagged_total"])
    out.append("  both agreed       %d" % s["caught_by_both"])
    out.append("  detectors only    %d  the model judge scored these as fine"
               % s["caught_by_detector_only"])
    out.append("  model only        %d  the detectors could not see these"
               % s["caught_by_model_only"])
    if s["flagged_total"] and not s["caught_by_model_only"]:
        out.append("  -> the judge model caught nothing the checks missed; "
                   "a bigger sentinel model, or none at all")
    out.append("")
    out.append("DECAY PROFILE  (mean score by depth into a segment)")
    if s["decay_profile"]:
        depths = sorted(s["decay_profile"])
        for d in depths:
            v = s["decay_profile"][d]
            bar = "#" * int(round(v / 5.0))
            out.append("  +%-3d %5.1f %s" % (d, v, bar))
    else:
        out.append("  (no checkpoints yet)")
    if s["worker_errors"]:
        out.append("\nworker errors      %d" % s["worker_errors"])
    return "\n".join(out)
