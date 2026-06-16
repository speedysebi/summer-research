"""Configuration loading and defaults for the lights-out harness."""
from __future__ import annotations

import copy
import json
from pathlib import Path

DEFAULTS = {
    "provider": {
        # kind: "ollama" | "openai" (any OpenAI-compatible server) | "mock"
        "kind": "ollama",
        "base_url": "http://localhost:11434",
        "api_key": "",
        # Roles can point at different models. The sentinel deliberately may be a
        # different (or larger) model than the worker -- it is the thing judging.
        "intake_model": "qwen2.5-coder:7b",
        "worker_model": "qwen2.5-coder:7b",
        "sentinel_model": "qwen2.5-coder:7b",
        "recovery_model": "qwen2.5-coder:7b",
        "temperature": 0.2,
        "sentinel_temperature": 0.0,
        "max_tokens": 4096,
        "num_ctx": 8192,
        "timeout_s": 600,
        "retries": 3,
    },
    "run": {
        "wall_clock_budget_h": 8.0,
        "max_attempts_per_unit": 2,
        "max_halts": 8,
        "max_consecutive_errors": 3,  # provider unreachable -> abort instead of churning
        "checkpoint_every": 1,      # sentinel cadence; harness 1 may mark units explicitly
        "allow_verify_exec": True,  # run each unit's verify command in the workspace
        "verify_timeout_s": 120,
    },
    "sentinel": {
        "hard_floor": 45,             # score under this -> HALT
        "note_floor": 70,             # score under this -> NOTE (logged, run continues)
        "baseline_drop": 20,          # this far under the rolling baseline -> HALT
        "ema_alpha": 0.4,             # rolling baseline smoothing
        "consecutive_notes_halt": 3,  # slow bleed detector
        "good_threshold": 75,         # "clean or only minor worsening" -> safe rewind target
    },
    "recovery": {
        "base_overlap": 1,        # good units re-done on restart (the overlap in 1-15, 12-27)
        "overlap_escalation": 4,  # extra rewind each time we fail from the same target again
        "max_rewind_depth": 25,
    },
    "mock": {
        # Only used by provider.kind == "mock": where the fake worker starts degrading,
        # and how much further it gets after each recovery.
        "first_failure_unit": 15,
        "improvement_per_recovery": 12,
        "decay_window": 2,
    },
}


def _deep_merge(base: dict, override: dict) -> dict:
    out = copy.deepcopy(base)
    for k, v in (override or {}).items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _deep_merge(out[k], v)
        else:
            out[k] = v
    return out


def load_config(path: str | Path | None = None) -> dict:
    """Load config.json (if present) merged over DEFAULTS."""
    cfg = copy.deepcopy(DEFAULTS)
    if path is None:
        candidate = Path(__file__).resolve().parent.parent / "config.json"
        path = candidate if candidate.exists() else None
    if path:
        p = Path(path)
        if not p.exists():
            raise FileNotFoundError(f"config not found: {p}")
        cfg = _deep_merge(cfg, json.loads(p.read_text(encoding="utf-8")))
    return cfg
