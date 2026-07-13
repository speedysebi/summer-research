"""Preflight check. Run this before you walk away.

Every failure this catches is one that would otherwise surface at 2am, four hours into
a run, as a wall of identical errors. The expensive one is the sentinel: if the judge
model cannot reliably emit JSON, the harness degrades to "no supervision at all" and
still looks like it is working.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import urllib.error
import urllib.request

from .llm import Client, extract_json

OK, WARN, FAIL = "ok", "warn", "FAIL"


class Check:
    def __init__(self, name, status, detail=""):
        self.name, self.status, self.detail = name, status, detail

    def line(self):
        mark = {"ok": "  ok  ", "warn": " warn ", "FAIL": " FAIL "}[self.status]
        return "[%s] %-26s %s" % (mark, self.name, self.detail)


def _http_get(url, timeout=10, api_key=""):
    headers = {"Authorization": "Bearer " + api_key} if api_key else {}
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def available_models(pcfg):
    base = pcfg["base_url"].rstrip("/")
    if pcfg["kind"] == "ollama":
        data = _http_get(base + "/api/tags", api_key=pcfg.get("api_key", ""))
        return [m["name"] for m in data.get("models", [])]
    data = _http_get(base + "/v1/models", api_key=pcfg.get("api_key", ""))
    return [m["id"] for m in data.get("data", [])]


def run_doctor(cfg, deep=True):
    checks = []
    pcfg = cfg["provider"]

    # --- tooling ----------------------------------------------------------- #
    if shutil.which("git"):
        ver = subprocess.run(["git", "--version"], capture_output=True, text=True)
        checks.append(Check("git", OK, ver.stdout.strip()))
    else:
        checks.append(Check("git", FAIL, "not on PATH -- snapshots and rewind need it"))

    if pcfg["kind"] == "mock":
        checks.append(Check("provider", WARN,
                            "kind=mock -- this is the simulator, not a real model"))
        return checks

    # --- provider reachable ------------------------------------------------ #
    models = []
    try:
        models = available_models(pcfg)
        checks.append(Check("provider reachable", OK,
                            "%s at %s (%d models)" % (pcfg["kind"], pcfg["base_url"],
                                                      len(models))))
    except (urllib.error.URLError, OSError, KeyError, json.JSONDecodeError) as e:
        checks.append(Check("provider reachable", FAIL,
                            "%s at %s: %s" % (pcfg["kind"], pcfg["base_url"], e)))
        return checks

    # The server answering does not mean it can serve anything. An empty list from
    # Ollama means nothing is pulled, and every call will 404 four hours from now.
    if not models:
        if pcfg["kind"] == "ollama":
            checks.append(Check("models pulled", FAIL,
                                "the server is up but has no models -- "
                                "`ollama pull %s`" % pcfg.get("worker_model", "<model>")))
        else:
            checks.append(Check("models pulled", WARN,
                                "server listed no models; cannot verify names"))

    # --- each role's model present ----------------------------------------- #
    roles = ["intake", "worker", "sentinel", "recovery"]
    for role in roles:
        name = pcfg.get(role + "_model")
        if not name:
            checks.append(Check(role + " model", FAIL, "not configured"))
        elif not models:
            checks.append(Check(role + " model", WARN, "%s (unverified)" % name))
        elif name not in models:
            near = [m for m in models if m.split(":")[0] == str(name).split(":")[0]]
            hint = ("  did you mean: " + ", ".join(near[:3])) if near else ""
            checks.append(Check(role + " model", FAIL, "%r not pulled%s" % (name, hint)))
        else:
            checks.append(Check(role + " model", OK, str(name)))

    if pcfg.get("worker_model") == pcfg.get("sentinel_model"):
        checks.append(Check("judge independence", WARN,
                            "sentinel uses the same model as the worker -- a bigger "
                            "judge catches much more"))

    if not deep:
        return checks

    # --- round trips ------------------------------------------------------- #
    for role in ["worker", "sentinel"]:
        name = pcfg.get(role + "_model")
        if not name or (models and name not in models):
            continue
        try:
            client = Client(cfg, role)
            if role == "sentinel":
                # The one that actually matters: can the judge emit parseable JSON?
                raw = client.chat(
                    "You reply with JSON only.",
                    'Reply with exactly: {"score": 100, "verdict": "PASS"}',
                    max_tokens=200)
                parsed = extract_json(raw)
                if isinstance(parsed, dict) and "score" in parsed:
                    checks.append(Check("sentinel JSON round trip", OK,
                                        "parsed %r" % (parsed,)))
                else:
                    checks.append(Check("sentinel JSON round trip", FAIL,
                                        "unparseable -- the judge will fail open; "
                                        "use a bigger sentinel model. got: %r"
                                        % (raw[:120],)))
            else:
                raw = client.chat("You are terse.", "Reply with the single word: ready",
                                  max_tokens=50)
                if raw.strip():
                    checks.append(Check("worker round trip", OK,
                                        "%d chars in reply" % len(raw)))
                else:
                    checks.append(Check("worker round trip", FAIL, "empty reply"))
        except Exception as e:                    # noqa: BLE001 - report, never raise
            checks.append(Check(role + " round trip", FAIL, str(e)[:160]))

    # --- settings worth knowing about -------------------------------------- #
    if cfg["run"].get("allow_verify_exec", True):
        checks.append(Check("verify exec", WARN,
                            "units will run their verify command with shell=True"))
    else:
        checks.append(Check("verify exec", WARN,
                            "disabled -- the sentinel loses its only ground truth"))

    ctx = pcfg.get("num_ctx", 0)
    if ctx and ctx < 8192:
        checks.append(Check("context window", WARN,
                            "num_ctx=%d is small; long units may truncate" % ctx))

    return checks


def render(checks):
    lines = [c.line() for c in checks]
    fails = sum(1 for c in checks if c.status == FAIL)
    warns = sum(1 for c in checks if c.status == WARN)
    lines.append("")
    if fails:
        lines.append("%d check(s) FAILED -- fix these before starting a long run." % fails)
    elif warns:
        lines.append("Ready to run. %d warning(s) above are worth a look." % warns)
    else:
        lines.append("Ready to run.")
    return "\n".join(lines), fails
