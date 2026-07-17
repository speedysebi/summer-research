#!/usr/bin/env python3
"""Lights-out harness CLI.

    python run.py intake                    Harness 1: describe the job, answer questions
    python run.py start                     run lights out from the plan
    python run.py resume                    continue an interrupted run
    python run.py status                    where the run is right now
    python run.py report                    the segment trace (1->15, 12->27, 15->35)
    python run.py analyze                   research metrics: runway, waste, decay profile
    python run.py doctor                    preflight the provider before an 8-hour run
    python run.py demo                      full end-to-end on the mock provider

Every command takes --run <run_id> (defaults to the most recent) and --config <path>.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from lightsout import analysis, doctor, harness1_intake, orchestrator  # noqa: E402
from lightsout.config import load_config                           # noqa: E402
from lightsout.state import Run                                    # noqa: E402

RUNS_DIR = Path(__file__).resolve().parent / "runs"


def _get_run(args, create=False):
    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    if create:
        return Run.create(RUNS_DIR, args.run)
    if args.run:
        return Run.open(RUNS_DIR, args.run)
    return Run.latest(RUNS_DIR)


# --------------------------------------------------------------------------- #
def cmd_intake(args):
    cfg = load_config(args.config)
    run = _get_run(args, create=True)
    print("run id: %s" % run.run_id)
    items = None
    if args.items_file:
        items = harness1_intake.load_items(args.items_file)
        print("loaded %d work items from %s" % (len(items), args.items_file))
    harness1_intake.run_intake(
        cfg, run,
        request=args.request,
        total_units=args.units,
        interactive=not args.non_interactive,
        items=items,
    )
    print("\nNext:  python run.py start --run %s" % run.run_id)


def cmd_start(args):
    cfg = load_config(args.config)
    run = _get_run(args)
    orchestrator.run_lights_out(cfg, run, quiet=args.quiet,
                                provider_from_config=args.provider_from_config)


def cmd_resume(args):
    cfg = load_config(args.config)
    run = _get_run(args)
    st = run.load_state()
    print("resuming %s at unit %d (segment %d, status was %s)"
          % (run.run_id, st["cursor"] + 1, st["segment"], st["status"]))
    orchestrator.run_lights_out(cfg, run, quiet=args.quiet,
                                provider_from_config=args.provider_from_config)


def cmd_status(args):
    run = _get_run(args)
    st = run.load_state()
    try:
        spec = run.load_spec()
        total = len(spec["units"])
        goal = spec["goal"]
    except FileNotFoundError:
        total, goal = 0, "(no plan yet -- run intake)"
    reports = run.checkpoint_reports()
    print("run:        %s" % run.run_id)
    print("status:     %s" % st["status"])
    print("goal:       %s" % goal[:100])
    print("progress:   unit %d / %d   segment %d" % (st["cursor"], total, st["segment"]))
    print("halts:      %d    rewinds: %d" % (st.get("halts", 0), len(st.get("rewinds", []))))
    print("baseline:   %s" % (round(st["baseline"], 1) if st.get("baseline") else "n/a"))
    print("elapsed:    %.1f min" % ((st.get("elapsed_s") or 0) / 60.0))
    if st.get("corrective_directive"):
        print("directive:  %s" % st["corrective_directive"][:160])
    if reports:
        print("\nlast checkpoints:")
        for r in reports[-8:]:
            print("  cp%-4d unit %-4d %-5s score %-3d  %s"
                  % (r["checkpoint"], r["unit_index"], r["verdict"], r["score"],
                     (r["note"] or "")[:60]))


def cmd_report(args):
    """The sawtooth: what each segment covered and why it stopped."""
    run = _get_run(args)
    st = run.load_state()
    reports = run.checkpoint_reports()
    events = run.journal()

    segments = {}
    for r in reports:
        seg = r.get("segment", 1)
        s = segments.setdefault(seg, {"first": r["unit_index"], "last": r["unit_index"],
                                      "scores": [], "halt": None})
        s["first"] = min(s["first"], r["unit_index"])
        s["last"] = max(s["last"], r["unit_index"])
        s["scores"].append(r["score"])
        if r["verdict"] == "HALT":
            s["halt"] = r

    rewinds = {rw["segment"]: rw for rw in st.get("rewinds", [])}

    print("\n=== SEGMENT TRACE: %s ===" % run.run_id)
    print("(each line is one attempt; overlap is Harness 3 redoing known-good work)\n")
    for seg in sorted(segments):
        s = segments[seg]
        avg = sum(s["scores"]) / len(s["scores"])
        bar = "".join("#" if x >= 75 else ("~" if x >= 45 else ".") for x in s["scores"])
        line = ("segment %-2d  units %3d -> %-3d  avg %5.1f  %s"
                % (seg, s["first"], s["last"], avg, bar))
        print(line)
        rw = rewinds.get(seg)
        if rw:
            print("            HALT: %s" % (rw.get("reason") or "")[:88])
            print("            cause: %-22s onset unit %s, rewound to %s (depth %s)"
                  % (rw.get("root_cause"), rw.get("onset_index"),
                     rw.get("to_index"), rw.get("depth")))
            print("            kept:  %s" % rw.get("abandoned_tag"))
        print()

    print("legend: # >=75 clean   ~ 45-74 degrading   . <45 failed")
    total_cp = len(reports)
    halted = sum(1 for r in reports if r["verdict"] == "HALT")
    noted = sum(1 for r in reports if r["verdict"] == "NOTE")
    print("\ncheckpoints: %d   passes: %d   notes: %d   halts: %d"
          % (total_cp, total_cp - halted - noted, noted, halted))
    print("status: %s   final cursor: unit %d" % (st["status"], st["cursor"]))
    if args.json:
        print("\n" + json.dumps({"segments": segments, "rewinds": st.get("rewinds", []),
                                 "events": len(events)}, indent=2, default=str))


def cmd_analyze(args):
    cfg = load_config(args.config)
    run = _get_run(args)
    summary = analysis.summarize(run, note_floor=cfg["sentinel"]["note_floor"])
    print(analysis.render(summary))
    if args.csv:
        n = analysis.to_csv(run, args.csv)
        print("\nwrote %d checkpoint rows to %s" % (n, args.csv))
    if args.json:
        print("\n" + json.dumps(summary, indent=2))


def cmd_doctor(args):
    cfg = load_config(args.config)
    checks = doctor.run_doctor(cfg, deep=not args.quick)
    text, fails = doctor.render(checks)
    print(text)
    sys.exit(1 if fails else 0)


def cmd_demo(args):
    """End-to-end proof that all three harnesses fire, with no model server needed."""
    cfg = load_config(args.config)
    cfg["provider"]["kind"] = "mock"
    cfg["run"]["wall_clock_budget_h"] = 0.2
    cfg["run"]["max_halts"] = 4

    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    run = Run.create(RUNS_DIR, args.run or None)
    print("=== DEMO (mock provider) -- run %s ===" % run.run_id)

    harness1_intake.run_intake(
        cfg, run,
        request="I have %d LeetCode questions I need you to solve, one file each, "
                "with tests." % args.units,
        total_units=args.units,
        interactive=False,
    )
    orchestrator.run_lights_out(cfg, run, quiet=args.quiet)

    class A:
        pass
    a = A()
    a.run, a.config, a.json = run.run_id, args.config, False
    cmd_report(a)


# --------------------------------------------------------------------------- #
def main():
    p = argparse.ArgumentParser(prog="run.py", description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--config", default=None, help="path to config.json")
    p.add_argument("--run", default=None, help="run id (default: most recent)")

    # Accept --run/--config on either side of the subcommand. SUPPRESS keeps the
    # subparser from clobbering a value given before it.
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--config", default=argparse.SUPPRESS)
    common.add_argument("--run", default=argparse.SUPPRESS)

    sub = p.add_subparsers(dest="cmd", required=True, parser_class=lambda **kw:
                           argparse.ArgumentParser(parents=[common], **kw))

    s = sub.add_parser("intake", help="Harness 1: plan the job")
    s.add_argument("--request", default=None, help="skip the prompt and pass the job inline")
    s.add_argument("--units", type=int, default=None, help="hint: how many work units")
    s.add_argument("--non-interactive", action="store_true",
                   help="do not stop to ask questions (records them unanswered)")
    s.add_argument("--items-file", default=None,
                   help="file of work items, one per line or a JSON array -- the list "
                        "is authoritative, so the model is never asked to enumerate it")
    s.set_defaults(func=cmd_intake)

    s = sub.add_parser("start", help="run lights out")
    s.add_argument("--quiet", action="store_true")
    s.add_argument("--provider-from-config", action="store_true",
                   help="use config.json's provider instead of the one the run started with")
    s.set_defaults(func=cmd_start)

    s = sub.add_parser("resume", help="continue an interrupted run")
    s.add_argument("--quiet", action="store_true")
    s.add_argument("--provider-from-config", action="store_true",
                   help="use config.json's provider instead of the one the run started with")
    s.set_defaults(func=cmd_resume)

    s = sub.add_parser("status", help="current position and recent checkpoints")
    s.set_defaults(func=cmd_status)

    s = sub.add_parser("report", help="segment trace / sawtooth")
    s.add_argument("--json", action="store_true")
    s.set_defaults(func=cmd_report)

    s = sub.add_parser("analyze", help="research metrics for a run")
    s.add_argument("--csv", default=None, help="also write per-checkpoint rows here")
    s.add_argument("--json", action="store_true")
    s.set_defaults(func=cmd_analyze)

    s = sub.add_parser("doctor", help="preflight the provider and config")
    s.add_argument("--quick", action="store_true", help="skip model round trips")
    s.set_defaults(func=cmd_doctor)

    s = sub.add_parser("demo", help="end-to-end on the mock provider")
    s.add_argument("--units", type=int, default=40)
    s.add_argument("--quiet", action="store_true")
    s.set_defaults(func=cmd_demo)

    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
