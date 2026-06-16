"""Durable run state.

An 8-hour unattended run has to survive a crash, a reboot, and a rewind, so every
fact the harnesses need lives on disk, not in memory:

  runs/<run_id>/
    spec.json         Harness 1 output: goal, criteria, red flags, work units
    state.json        cursor, attempts, rolling score baseline, rewind history
    journal.jsonl     append-only event log -- the thing Harness 3 reads back
    checkpoints/      one JSON sentinel report per checkpoint
    workspace/        the actual code being produced (a git repo; see workspace.py)
    mock_state.json   only when provider.kind == "mock"
"""
from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path


def utcnow():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def new_run_id():
    return datetime.now().strftime("run_%Y%m%d_%H%M%S")


class Run:
    def __init__(self, root):
        self.root = Path(root)
        self.run_id = self.root.name

    # -- lifecycle ---------------------------------------------------------- #
    @classmethod
    def create(cls, runs_dir, run_id=None):
        run_id = run_id or new_run_id()
        root = Path(runs_dir) / run_id
        (root / "checkpoints").mkdir(parents=True, exist_ok=True)
        (root / "workspace").mkdir(parents=True, exist_ok=True)
        r = cls(root)
        r.save_state(r.fresh_state())
        return r

    @classmethod
    def open(cls, runs_dir, run_id):
        root = Path(runs_dir) / run_id
        if not root.exists():
            raise FileNotFoundError("no such run: " + str(root))
        return cls(root)

    @classmethod
    def latest(cls, runs_dir):
        runs = sorted(p for p in Path(runs_dir).glob("run_*") if p.is_dir())
        if not runs:
            raise FileNotFoundError("no runs in " + str(runs_dir))
        return cls(runs[-1])

    def fresh_state(self):
        return {
            "run_id": self.run_id,
            "created": utcnow(),
            "status": "intake",       # intake | running | halted | recovering | done | budget
            "cursor": 0,              # index into spec["units"] of the NEXT unit to run
            "segment": 1,             # incremented on every recovery restart
            "segment_start": 0,       # cursor the current segment began at
            "attempts": {},           # unit_id -> attempt count
            "baseline": None,         # EMA of sentinel scores
            "consecutive_notes": 0,
            "halts": 0,
            "rewinds": [],            # [{from, to, segment, reason, depth}]
            "corrective_directive": "",
            "carried_notes": [],      # recent sentinel NOTEs fed back into the worker
            "started_wall": None,
            "elapsed_s": 0.0,
            "last_checkpoint_sha": None,
        }

    # -- paths -------------------------------------------------------------- #
    @property
    def spec_path(self):
        return self.root / "spec.json"

    @property
    def state_path(self):
        return self.root / "state.json"

    @property
    def journal_path(self):
        return self.root / "journal.jsonl"

    @property
    def workspace(self):
        return self.root / "workspace"

    @property
    def checkpoints_dir(self):
        return self.root / "checkpoints"

    # -- spec --------------------------------------------------------------- #
    def save_spec(self, spec):
        self.spec_path.write_text(json.dumps(spec, indent=2), encoding="utf-8")

    def load_spec(self):
        if not self.spec_path.exists():
            raise FileNotFoundError(
                "run %s has no spec.json -- run harness 1 (intake) first" % self.run_id
            )
        return json.loads(self.spec_path.read_text(encoding="utf-8"))

    # -- state -------------------------------------------------------------- #
    def save_state(self, state):
        tmp = self.state_path.with_suffix(".tmp")
        tmp.write_text(json.dumps(state, indent=2), encoding="utf-8")
        tmp.replace(self.state_path)

    def load_state(self):
        return json.loads(self.state_path.read_text(encoding="utf-8"))

    # -- journal ------------------------------------------------------------ #
    def event(self, kind, **fields):
        rec = {"ts": utcnow(), "mono": time.time(), "kind": kind}
        rec.update(fields)
        with self.journal_path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(rec) + "\n")
        return rec

    def journal(self):
        if not self.journal_path.exists():
            return []
        out = []
        for line in self.journal_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line:
                try:
                    out.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
        return out

    # -- checkpoint reports ------------------------------------------------- #
    def save_checkpoint(self, index, report):
        p = self.checkpoints_dir / ("cp_%04d.json" % index)
        p.write_text(json.dumps(report, indent=2), encoding="utf-8")
        return p

    def checkpoint_reports(self):
        reports = []
        for p in sorted(self.checkpoints_dir.glob("cp_*.json")):
            try:
                reports.append(json.loads(p.read_text(encoding="utf-8")))
            except json.JSONDecodeError:
                pass
        return reports
