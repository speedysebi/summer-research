"""The worker: executes one unit of the plan. This is the part that degrades.

The worker gets a deliberately narrow context -- the goal, the one unit in front of it,
and any corrective directive Harness 3 left behind. It does NOT get the transcript of
everything it has already done, because that accumulation is the main thing that rots a
small model's output over a long run.

File output uses a block protocol rather than JSON, because small models reliably mangle
code inside JSON string escapes but handle delimiters fine:

    <<<FILE path/to/file.py>>>
    ...file contents...
    <<<END>>>
"""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

from .llm import Client

FILE_BLOCK = re.compile(r"<<<FILE\s+(?P<path>[^\n>]+?)\s*>>>\n(?P<body>.*?)<<<END>>>",
                        re.S)

WORKER_SYSTEM = """You are a coding worker in an unattended run. You do exactly one unit
of work per turn, completely, and then stop.

Emit every file you create or change as a block:

<<<FILE relative/path.ext>>>
(the complete file contents -- never a fragment, never a diff, never an ellipsis)
<<<END>>>

Rules that are checked automatically after every unit:
  * No TODO, FIXME, `pass` bodies, `...` placeholders, or NotImplementedError.
  * Never write "rest of the implementation unchanged" -- always emit the whole file.
  * Tests must assert concrete expected values, not `is not None` or `True`.
  * Do not modify or delete files belonging to other units.
Violating these stops the entire run, so finish the work or say plainly that you cannot."""

WORKER_PROMPT = """PROJECT GOAL
{goal}

SUCCESS CRITERIA
{criteria}

UNIT_INDEX: {index}
UNIT_ID: {uid}
UNIT_TITLE: {title}
DELIVERABLE: {deliverable}
VERIFY_COMMAND: {verify}
{statement}{directive}{notes}{existing}
Do this one unit now. Emit the complete file(s) using the <<<FILE ...>>> protocol."""


def _fmt_block(header, body):
    return "\n%s\n%s\n" % (header, body) if body else ""


def build_prompt(spec, unit, state, workspace):
    directive = _fmt_block(
        "CORRECTIVE DIRECTIVE (issued by recovery after an earlier failure -- follow it exactly)",
        state.get("corrective_directive", ""),
    )
    notes = _fmt_block(
        "RECENT QUALITY NOTES (fix these tendencies)",
        "\n".join("- " + n for n in state.get("carried_notes", [])[-3:]),
    )
    existing = ""
    files = sorted(p.name for p in Path(workspace.path).rglob("*")
                   if p.is_file() and ".git" not in p.parts)
    if files:
        shown = files[-12:]
        existing = _fmt_block(
            "FILES ALREADY IN THE WORKSPACE (do not rewrite these)",
            "\n".join("- " + f for f in shown)
            + ("\n- ... and %d more" % (len(files) - len(shown)) if len(files) > len(shown) else ""),
        )
    statement = _fmt_block("PROBLEM", unit.get("statement", ""))
    return WORKER_PROMPT.format(
        statement=statement,
        goal=spec["goal"],
        criteria="\n".join("- " + c for c in spec["success_criteria"]) or "- (none stated)",
        index=unit["index"], uid=unit["id"], title=unit["title"],
        deliverable=unit["deliverable"], verify=unit["verify"],
        directive=directive, notes=notes, existing=existing,
    )


def parse_files(text):
    """Pull <<<FILE>>> blocks out of a model reply. Returns {relpath: contents}."""
    out = {}
    for m in FILE_BLOCK.finditer(text or ""):
        path = m.group("path").strip().strip('"').strip("'").replace("\\", "/")
        if not path or path.startswith("/") or ".." in path.split("/"):
            continue  # refuse absolute paths and traversal
        out[path] = m.group("body")
    return out


def write_files(workspace, files):
    written = []
    for relpath, body in files.items():
        dest = Path(workspace.path) / relpath
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(body, encoding="utf-8")
        written.append(relpath)
    return written


def run_verify(cfg, workspace, command):
    if not command or command.strip().lower() in ("none", "n/a", ""):
        return {"skipped": True, "command": command, "returncode": 0, "output": ""}
    if not cfg["run"].get("allow_verify_exec", True):
        return {"skipped": True, "command": command, "returncode": 0,
                "output": "(verify execution disabled in config)"}
    try:
        proc = subprocess.run(
            command, shell=True, cwd=str(workspace.path),
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            timeout=cfg["run"].get("verify_timeout_s", 120),
        )
        out = ((proc.stdout or "") + (proc.stderr or ""))[-4000:]
        return {
            "skipped": False, "command": command, "returncode": proc.returncode,
            "output": out, "pass_rate": _parse_pass_rate(out),
        }
    except subprocess.TimeoutExpired:
        return {"skipped": False, "command": command, "returncode": 124,
                "output": "verify command timed out"}
    except Exception as e:                       # noqa: BLE001 - never kill the run here
        return {"skipped": False, "command": command, "returncode": 1,
                "output": "verify could not run: %s" % e}


PASS_RE = re.compile(r"(\d+)\s*/\s*(\d+)\s+passed")


def _parse_pass_rate(output):
    """Pull "12/16 passed" out of the evaluator's output.

    A partial pass rate is a far better signal than a bare exit code: it separates
    "wrote nothing that runs" from "got the edge cases wrong", and it is what the
    decay curve is plotted from.
    """
    m = PASS_RE.search(output or "")
    if not m:
        return None
    passed, total = int(m.group(1)), int(m.group(2))
    return round(passed / total, 4) if total else 0.0


def execute_unit(cfg, run, spec, unit, state, workspace):
    """Run one unit. Returns a result dict; does not commit or judge."""
    client = Client(cfg, "worker", run_dir=run.root)
    prompt = build_prompt(spec, unit, state, workspace)
    reply = client.chat(WORKER_SYSTEM, prompt)

    files = parse_files(reply)
    written = write_files(workspace, files)
    verify = run_verify(cfg, workspace, unit["verify"])

    return {
        "unit_id": unit["id"],
        "index": unit["index"],
        "title": unit["title"],
        "raw_reply": reply,
        "files": files,
        "written": written,
        "verify": verify,
    }
