"""Workspace snapshots, backed by git.

Rewinding is the whole point of Harness 3, so every checkpoint gets a commit. A
rewind is then `git checkout <sha>` -- cheap, exact, and it gives Harness 2 a real
diff to judge instead of a pile of whole files.

Abandoned work is never destroyed: before rewinding, the failed segment is tagged
`attempt/<n>`, so the failure traces stay available for analysis afterwards.
"""
from __future__ import annotations

import subprocess
from pathlib import Path


class GitError(RuntimeError):
    pass


class Workspace:
    def __init__(self, path):
        self.path = Path(path)
        self.path.mkdir(parents=True, exist_ok=True)

    # -- plumbing ----------------------------------------------------------- #
    def _git(self, *args, check=True):
        proc = subprocess.run(
            ["git"] + list(args),
            cwd=str(self.path),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        if check and proc.returncode != 0:
            raise GitError("git %s failed: %s" % (" ".join(args), proc.stderr.strip()))
        return proc.stdout.strip()

    def init(self):
        if (self.path / ".git").exists():
            return
        self._git("init", "-q")
        self._git("config", "user.email", "harness@lightsout.local")
        self._git("config", "user.name", "lights-out harness")
        self._git("config", "core.autocrlf", "false")
        gitignore = self.path / ".gitignore"
        if not gitignore.exists():
            gitignore.write_text("__pycache__/\n*.pyc\n.venv/\n", encoding="utf-8")
        readme = self.path / "README.md"
        if not readme.exists():
            readme.write_text("# workspace\n\nProduced by the lights-out harness.\n",
                              encoding="utf-8")
        self.commit("harness: initial empty workspace", allow_empty=True)

    # -- snapshots ---------------------------------------------------------- #
    def commit(self, message, allow_empty=False):
        self._git("add", "-A")
        args = ["commit", "-q", "-m", message]
        if allow_empty:
            args.insert(1, "--allow-empty")
        proc = subprocess.run(
            ["git"] + args, cwd=str(self.path),
            capture_output=True, text=True, encoding="utf-8", errors="replace",
        )
        if proc.returncode != 0 and "nothing to commit" not in (proc.stdout + proc.stderr):
            raise GitError("commit failed: " + (proc.stderr or proc.stdout).strip())
        return self.head()

    def head(self):
        return self._git("rev-parse", "HEAD")

    def has_commits(self):
        proc = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=str(self.path),
            capture_output=True, text=True,
        )
        return proc.returncode == 0

    def tag(self, name, sha=None):
        args = ["tag", "-f", name]
        if sha:
            args.append(sha)
        self._git(*args)

    def diff(self, from_sha, to_sha="HEAD", max_chars=20000):
        if not from_sha:
            out = self._git("show", "--stat", "--patch", to_sha)
        else:
            out = self._git("diff", from_sha, to_sha)
        if len(out) > max_chars:
            out = out[:max_chars] + "\n... [diff truncated by harness] ..."
        return out

    def changed_files(self, from_sha, to_sha="HEAD"):
        if not from_sha:
            return [f for f in self._git("ls-files").splitlines() if f]
        out = self._git("diff", "--name-only", from_sha, to_sha)
        return [f for f in out.splitlines() if f]

    def restore(self, sha):
        """Hard-reset the working tree back to `sha`. Caller must tag first."""
        self._git("checkout", "-q", "--detach", sha)
        self._git("reset", "-q", "--hard", sha)
        self._git("clean", "-qfd")
        return self.head()

    def read_file(self, relpath, max_chars=8000):
        p = self.path / relpath
        if not p.exists():
            return ""
        text = p.read_text(encoding="utf-8", errors="replace")
        return text[:max_chars]
