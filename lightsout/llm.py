"""Provider abstraction. Stdlib only -- no pip install required.

Three kinds:
  ollama  -> POST {base_url}/api/chat            (local Ollama)
  openai  -> POST {base_url}/v1/chat/completions (llama.cpp server, LM Studio, vLLM, ...)
  mock    -> scripted local fake, used by `run.py demo` to exercise all three
             harnesses (including a realistic degradation curve) with no model running.

Every harness constructs its OWN Client. Harness 2's sentinel client never sees the
worker's message history -- it only ever receives the artifacts it is asked to judge.
That isolation is the point: the critic must not inherit the context that went bad.
"""
from __future__ import annotations

import json
import re
import time
import urllib.error
import urllib.request
from pathlib import Path


class LLMError(RuntimeError):
    pass


# --------------------------------------------------------------------------- #
# Tolerant JSON extraction. Small models fence, prefix, and trail their JSON.
# --------------------------------------------------------------------------- #
def extract_json(text):
    if not text:
        return None
    fenced = re.findall(r"```(?:json)?\s*(.*?)```", text, re.S)
    candidates = [f.strip() for f in fenced] + [text.strip()]
    for cand in candidates:
        try:
            return json.loads(cand)
        except Exception:
            pass
        # Balanced-delimiter scan: find the first complete object or array.
        for opener, closer in (("{", "}"), ("[", "]")):
            start = cand.find(opener)
            while start != -1:
                depth, in_str, esc = 0, False, False
                for i in range(start, len(cand)):
                    ch = cand[i]
                    if in_str:
                        if esc:
                            esc = False
                        elif ch == "\\":
                            esc = True
                        elif ch == '"':
                            in_str = False
                        continue
                    if ch == '"':
                        in_str = True
                    elif ch == opener:
                        depth += 1
                    elif ch == closer:
                        depth -= 1
                        if depth == 0:
                            try:
                                return json.loads(cand[start:i + 1])
                            except Exception:
                                break
                start = cand.find(opener, start + 1)
    return None


def _post_json(url, payload, headers, timeout):
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


class Client:
    """One client per role. Stateless: no history is retained between calls."""

    def __init__(self, cfg, role, run_dir=None):
        self.cfg = cfg
        self.pcfg = cfg["provider"]
        self.role = role
        self.kind = self.pcfg["kind"]
        self.model = self.pcfg.get(role + "_model") or self.pcfg.get("worker_model")
        self.run_dir = Path(run_dir) if run_dir else None
        self.calls = 0

    # -- public ------------------------------------------------------------- #
    def chat(self, system, user, temperature=None, max_tokens=None):
        if self.role == "sentinel":
            temp = self.pcfg["sentinel_temperature"]
        else:
            temp = self.pcfg["temperature"]
        if temperature is not None:
            temp = temperature
        max_tokens = max_tokens or self.pcfg["max_tokens"]
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ]
        self.calls += 1

        if self.kind == "mock":
            return _MockBrain(self).respond(system, user)

        last_err = None
        for attempt in range(self.pcfg.get("retries", 3)):
            try:
                if self.kind == "ollama":
                    return self._ollama(messages, temp, max_tokens)
                if self.kind == "openai":
                    return self._openai(messages, temp, max_tokens)
                raise LLMError("unknown provider kind: " + str(self.kind))
            except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError) as e:
                last_err = e
                time.sleep(2 ** attempt)
        raise LLMError("%s call failed after retries: %s" % (self.kind, last_err))

    def chat_json(self, system, user, **kw):
        """Chat, then parse JSON out of whatever came back. One repair retry."""
        raw = self.chat(system, user, **kw)
        parsed = extract_json(raw)
        if parsed is not None:
            return parsed
        repair = (
            "Your previous reply was not valid JSON. Reply with ONLY the JSON object, "
            "no prose, no code fences.\n\nPrevious reply:\n" + raw[:4000]
        )
        raw2 = self.chat(system, repair, **kw)
        return extract_json(raw2)

    # -- providers ---------------------------------------------------------- #
    def _ollama(self, messages, temp, max_tokens):
        url = self.pcfg["base_url"].rstrip("/") + "/api/chat"
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temp,
                "num_ctx": self.pcfg["num_ctx"],
                "num_predict": max_tokens,
            },
        }
        out = _post_json(url, payload, {"Content-Type": "application/json"},
                         self.pcfg["timeout_s"])
        return (out.get("message") or {}).get("content", "")

    def _openai(self, messages, temp, max_tokens):
        url = self.pcfg["base_url"].rstrip("/") + "/v1/chat/completions"
        headers = {"Content-Type": "application/json"}
        if self.pcfg.get("api_key"):
            headers["Authorization"] = "Bearer " + self.pcfg["api_key"]
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temp,
            "max_tokens": max_tokens,
        }
        out = _post_json(url, payload, headers, self.pcfg["timeout_s"])
        return out["choices"][0]["message"]["content"]


# --------------------------------------------------------------------------- #
# Mock brain: a deterministic small-model simulator with a degradation curve.
# --------------------------------------------------------------------------- #
class _MockBrain:
    """Simulates a small model that works, then quietly rots.

    Health decays once the unit index passes `first_failure_unit`. Each completed
    recovery pushes that point later (the corrective directive helped), which is what
    produces the characteristic sawtooth: 1->15, 12->27, 15->35.
    """

    def __init__(self, client):
        self.client = client
        self.mcfg = client.cfg.get("mock", {})
        self.path = (client.run_dir / "mock_state.json") if client.run_dir else None

    def _state(self):
        if self.path and self.path.exists():
            return json.loads(self.path.read_text(encoding="utf-8"))
        return {"recoveries": 0}

    def respond(self, system, user):
        role = self.client.role
        if role == "intake":
            return self._intake(user)
        if role == "worker":
            return self._worker(user)
        if role == "sentinel":
            return self._sentinel(user)
        if role == "recovery":
            return self._recovery(user)
        return "ok"

    # intake ---------------------------------------------------------------- #
    def _intake(self, user):
        if "verify_template" in user:
            # framing-only request: the item list is authoritative, not the model
            return json.dumps({
                "goal": "Solve every listed problem, one file each, with real tests.",
                "success_criteria": [
                    "Every listed item has a working solution file",
                    "No placeholder or stubbed implementations",
                ],
                "red_flags": [
                    "Solution body replaced with a placeholder",
                    "Tests that assert nothing",
                    "Skipping an item and claiming it was done",
                ],
                "deliverable_template": "solutions/{n:03d}_{slug}.py with solve() and tests",
                "verify_template": "none",
            })
        if "ASK_QUESTIONS" in user:
            return json.dumps({
                "ready": True,
                "questions": [
                    "Which language should the solutions be written in?",
                    "Should each solution ship with unit tests?",
                    "Do you want time/space complexity documented per solution?",
                ],
            })
        n = 40
        m = re.search(r"TOTAL_UNITS:\s*(\d+)", user)
        if m:
            n = int(m.group(1))
        units = []
        for i in range(1, n + 1):
            units.append({
                "id": "u%03d" % i,
                "title": "Problem %d" % i,
                "deliverable": "solutions/problem_%03d.py containing solve() plus tests" % i,
                "verify": "none",
                "checkpoint": True,
            })
        return json.dumps({
            "goal": "Solve the requested problem set, one file per problem, with tests.",
            "success_criteria": [
                "Every problem has a working solution file",
                "No placeholder or stubbed implementations",
                "Each solution documents its complexity",
            ],
            "red_flags": [
                "Solution body replaced with TODO or pass",
                "Tests that assert nothing",
                "Claiming a problem is solved without producing the file",
                "Repeating the previous problem's solution verbatim",
            ],
            "units": units,
        })

    # worker ---------------------------------------------------------------- #
    def _worker(self, user):
        m = re.search(r"UNIT_INDEX:\s*(\d+)", user)
        idx = int(m.group(1)) if m else 1
        m2 = re.search(r"UNIT_TITLE:\s*(.+)", user)
        title = m2.group(1).strip() if m2 else "Problem"
        st = self._state()
        fail_at = (self.mcfg.get("first_failure_unit", 15)
                   + st.get("recoveries", 0) * self.mcfg.get("improvement_per_recovery", 12))
        window = self.mcfg.get("decay_window", 3)
        # Benchmark runs name the target file in the deliverable; honour it so the
        # evaluator finds the solution where it expects to.
        m3 = re.search(r"DELIVERABLE:\s*(\S+\.py)", user)
        if m3:
            return self._bench_worker(m3.group(1), idx, fail_at, window, title)
        path = "solutions/problem_%03d.py" % idx

        if idx < fail_at - window:
            # healthy output
            body = (
                '"""%s -- O(n) time, O(1) space."""\n\n\n' % title
                + "def solve(nums):\n"
                + "    total = 0\n"
                + "    for value in nums:\n"
                + "        total += value * %d\n" % idx
                + "    return total\n\n\n"
                + "def test_solve():\n"
                + "    assert solve([1, 2, 3]) == 6 * %d\n" % idx
            )
        elif idx < fail_at:
            # minor worsening -> NOTE
            body = (
                '"""%s."""\n\n\n' % title
                + "def solve(nums):\n"
                + "    # TODO: handle the empty input case\n"
                + "    return sum(nums) * %d\n\n\n" % idx
                + "def test_solve():\n"
                + "    assert solve([1, 2, 3]) is not None\n"
            )
        else:
            # hard failure -> HALT
            body = (
                '"""%s."""\n\n\n' % title
                + "def solve(nums):\n"
                + "    raise NotImplementedError  # TODO\n\n\n"
                + "def test_solve():\n"
                + "    pass  # TODO\n"
                + "    # handled above\n" * 12
            )
        return "<<<FILE %s>>>\n%s<<<END>>>\nDone with %s." % (path, body, title)

    def _bench_worker(self, path, idx, fail_at, window, title):
        """A stand-in solver for bank problems.

        It cannot actually solve them, so it returns a plausible wrong answer while
        healthy and degrades into stubs past the failure point. That is what is needed
        to exercise the evaluator wiring: the measured pass rate, not the prose, is
        what stops the run.
        """
        if idx < fail_at - window:
            body = ('"""%s."""\n\n\ndef solve(*args):\n'
                    "    values = args[0] if args else []\n"
                    "    try:\n"
                    "        return sum(values)\n"
                    "    except TypeError:\n"
                    "        return values\n") % title
        elif idx < fail_at:
            body = ('"""%s."""\n\n\ndef solve(*args):\n'
                    "    # TODO: handle the empty input case\n"
                    "    return 0\n") % title
        else:
            body = ('"""%s."""\n\n\ndef solve(*args):\n'
                    "    raise NotImplementedError  # TODO\n") % title
        return "<<<FILE %s>>>\n%s<<<END>>>\nDone with %s." % (path, body, title)

    # sentinel -------------------------------------------------------------- #
    def _sentinel(self, user):
        # Judge ONLY the diff section. The prompt also restates the red flags, which
        # mention "TODO" -- scoring against those would flag every clean checkpoint.
        m = re.search(r"DIFF SINCE LAST CHECKPOINT\n---\n(.*?)\n---", user, re.S)
        body = m.group(1) if m else user
        bad = body.count("NotImplementedError") + body.count("pass  # TODO")
        todos = body.count("TODO")
        if bad:
            return json.dumps({
                "score": 25,
                "verdict": "HALT",
                "failure_modes": ["stub", "test_gaming"],
                "evidence": ["solve() raises NotImplementedError",
                             "test body is `pass`"],
                "note": "Worker is emitting stubs and empty tests instead of solutions.",
                "advice": "Restart from the last clean checkpoint; require a runnable "
                          "solve() and a test with a real assertion.",
            })
        if todos:
            return json.dumps({
                "score": 66,
                "verdict": "NOTE",
                "failure_modes": ["quality_decay"],
                "evidence": ["TODO left in solution body",
                             "assertion weakened to `is not None`"],
                "note": "Edges are being skipped and assertions are getting weaker.",
                "advice": "Tighten the assertion requirement in the worker prompt.",
            })
        return json.dumps({
            "score": 92,
            "verdict": "PASS",
            "failure_modes": [],
            "evidence": ["solve() implemented", "test asserts a concrete value"],
            "note": "",
            "advice": "",
        })

    # recovery -------------------------------------------------------------- #
    def _recovery(self, user):
        if self.path:
            st = self._state()
            st["recoveries"] = st.get("recoveries", 0) + 1
            self.path.write_text(json.dumps(st), encoding="utf-8")
        return json.dumps({
            "diagnosis": "Output quality decayed gradually (TODOs, weakened assertions) "
                         "before collapsing into NotImplementedError stubs. Degradation "
                         "began at the first NOTE checkpoint, not at the HALT.",
            "root_cause": "context_saturation",
            "corrective_directive": (
                "Write a complete, runnable solve() for every problem. Never emit TODO, "
                "pass, or NotImplementedError. Every test must assert a concrete expected "
                "value. Work on one problem at a time and do not reference earlier problems."
            ),
            "confidence": 0.8,
        })
