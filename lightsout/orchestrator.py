"""The lights-out loop: run units, checkpoint, halt, recover, resume.

    for each unit from the cursor:
        worker executes it                      (worker.py)
        commit a snapshot
        if the unit is a checkpoint:
            HARNESS 2 judges it                 (harness2_sentinel.py)
              PASS -> continue
              NOTE -> carry the note into later worker prompts, continue
              HALT -> HARNESS 3 rewinds         (harness3_recovery.py)
                      cursor jumps backwards; loop continues from there

Everything is written to disk as it happens, so killing the process and running
`resume` picks up at the same cursor with the same baseline and directive.
"""
from __future__ import annotations

import time

from . import harness2_sentinel, harness3_recovery, worker
from .workspace import Workspace


def run_lights_out(cfg, run, quiet=False, provider_from_config=False):
    spec = run.load_spec()
    state = run.load_state()
    units = spec["units"]

    # A run is pinned to the provider it started with. Resuming an overnight job
    # against a different model than it began on would silently invalidate the whole
    # score history, so config.json does not get to change it mid-run.
    if state.get("provider") and not provider_from_config:
        if state["provider"] != cfg["provider"] and not quiet:
            print("note: using the provider this run started with (%s/%s); "
                  "pass --provider-from-config to override"
                  % (state["provider"]["kind"], state["provider"].get("worker_model")))
        cfg = dict(cfg)
        cfg["provider"] = state["provider"]
    else:
        state["provider"] = cfg["provider"]

    ws = Workspace(run.workspace)
    ws.init()
    if not state.get("initial_sha"):
        # The empty-workspace commit: Harness 3's last-resort rewind target when no
        # checkpoint in the run was ever clean.
        state["initial_sha"] = ws.head()
    if state.get("last_checkpoint_sha") is None:
        state["last_checkpoint_sha"] = ws.head()

    state["status"] = "running"
    if not state.get("started_wall"):
        state["started_wall"] = time.time()
    run.save_state(state)

    budget_s = float(cfg["run"]["wall_clock_budget_h"]) * 3600.0
    started = time.time()
    prior_elapsed = float(state.get("elapsed_s") or 0.0)
    consecutive_errors = 0

    run.event("run_start", cursor=state["cursor"], segment=state["segment"],
              total_units=len(units), budget_h=cfg["run"]["wall_clock_budget_h"])

    def log(msg):
        if not quiet:
            print(msg, flush=True)

    log("\n=== LIGHTS OUT: %s ===" % run.run_id)
    log("%d units, budget %.1f h, starting at unit %d (segment %d)\n"
        % (len(units), cfg["run"]["wall_clock_budget_h"], state["cursor"] + 1,
           state["segment"]))

    while state["cursor"] < len(units):
        elapsed = prior_elapsed + (time.time() - started)
        state["elapsed_s"] = elapsed
        if elapsed > budget_s:
            state["status"] = "budget"
            run.save_state(state)
            run.event("budget_exhausted", elapsed_s=elapsed, cursor=state["cursor"])
            log("\nWall-clock budget exhausted at unit %d." % (state["cursor"] + 1))
            return state

        if state.get("halts", 0) >= cfg["run"]["max_halts"]:
            state["status"] = "halted"
            run.save_state(state)
            run.event("max_halts_reached", halts=state["halts"])
            log("\nMax halts (%d) reached -- stopping for a human."
                % cfg["run"]["max_halts"])
            return state

        unit = units[state["cursor"]]
        attempts = state["attempts"].get(unit["id"], 0)
        log("[seg %d] unit %d/%d  %s"
            % (state["segment"], unit["index"], len(units), unit["title"]))

        try:
            result = worker.execute_unit(cfg, run, spec, unit, state, ws)
        except Exception as e:                    # noqa: BLE001 - a crash must not end the night
            run.event("unit_error", unit_index=unit["index"], error=str(e))
            log("    worker error: %s" % e)
            state["attempts"][unit["id"]] = attempts + 1
            consecutive_errors += 1
            # An unreachable or misconfigured model server fails every unit the same
            # way. Churning through the rest of the plan producing nothing is worse
            # than stopping, so break the circuit instead of burning the night.
            if consecutive_errors >= cfg["run"].get("max_consecutive_errors", 3):
                state["status"] = "error"
                run.save_state(state)
                run.event("aborted", reason="%d consecutive worker errors" % consecutive_errors,
                          last_error=str(e), cursor=state["cursor"])
                log("\nAborting: %d units in a row failed to execute (%s).\n"
                    "The model provider is probably unreachable or misconfigured -- "
                    "check config.json, then `python run.py resume --run %s`."
                    % (consecutive_errors, e, run.run_id))
                return state
            if attempts + 1 >= cfg["run"]["max_attempts_per_unit"]:
                state["cursor"] += 1
            run.save_state(state)
            continue

        consecutive_errors = 0
        state["attempts"][unit["id"]] = attempts + 1
        ws.commit("unit %d: %s" % (unit["index"], unit["title"][:60]))
        run.event("unit_done", unit_index=unit["index"], unit_id=unit["id"],
                  files=result["written"], verify_rc=result["verify"].get("returncode"),
                  pass_rate=result["verify"].get("pass_rate"),
                  problem_id=unit.get("problem_id"), difficulty=unit.get("difficulty"),
                  segment=state["segment"], sha=ws.head())
        rate = result["verify"].get("pass_rate")
        log("    wrote %s%s" % (", ".join(result["written"]) or "(no files)",
                                "" if rate is None else "   tests %d%%" % round(rate * 100)))

        if not unit["checkpoint"]:
            state["cursor"] += 1
            run.save_state(state)
            continue

        # ---- HARNESS 2 ---------------------------------------------------- #
        report = harness2_sentinel.evaluate(cfg, run, spec, unit, result, ws, state)
        log("    checkpoint %d: %s score=%d%s"
            % (report["checkpoint"], report["verdict"], report["score"],
               ("  <- " + report["note"]) if report["note"] else ""))

        if report["verdict"] == "HALT":
            state["status"] = "recovering"
            run.save_state(state)
            # ---- HARNESS 3 ------------------------------------------------ #
            state = harness3_recovery.recover(cfg, run, spec, state, ws, report,
                                              quiet=quiet)
            run.save_state(state)
            continue

        if report["verdict"] == "NOTE":
            note = report["note"] or report["advice"]
            if note:
                state.setdefault("carried_notes", []).append(note)
            state["last_checkpoint_sha"] = report["sha"]
        else:
            state["carried_notes"] = []
            state["last_checkpoint_sha"] = report["sha"]

        state["cursor"] += 1
        run.save_state(state)

    state["status"] = "done"
    state["elapsed_s"] = prior_elapsed + (time.time() - started)
    run.save_state(state)
    run.event("run_complete", units=len(units), segments=state["segment"],
              halts=state.get("halts", 0), elapsed_s=state["elapsed_s"])
    log("\n=== COMPLETE === %d units, %d segments, %d halts, %.1f min"
        % (len(units), state["segment"], state.get("halts", 0),
           state["elapsed_s"] / 60.0))
    return state
