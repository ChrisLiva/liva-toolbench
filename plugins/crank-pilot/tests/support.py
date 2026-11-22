"""Helpers for the crank-pilot tests: an effort directory and the command run against it."""

import contextlib
import http.client
import json
import os
import signal
import subprocess
import sys
import tempfile
import threading
import time
import unittest
import urllib.error
import urllib.request
from pathlib import Path

PLUGIN = Path(__file__).resolve().parent.parent
BIN = PLUGIN / "bin" / "crank-pilot"

QUESTIONS = {
    "kind": "questions", "phase": "spec", "title": "Round 1",
    "agenda": {"settled": ["Storage"], "open": ["Toggle place", "First visit"], "current": "Toggle place"},
    "questions": [
        {"id": "q1", "title": "Where does the toggle live?", "body": "Pick one.",
         "recommendation": "Header: fewest clicks.",
         "options": [{"id": "a", "label": "Header"}, {"id": "b", "label": "Settings"}], "recommended": "a"},
        {"id": "q2", "title": "Name the storage key", "body": "Free text.", "recommendation": "`theme`"},
    ],
}

READBACK = {
    "kind": "readback", "phase": "spec", "title": "Spec: dark mode toggle",
    "agenda": {"settled": [], "open": ["Readback of the spec"], "current": "Readback of the spec"},
    "artifact": "spec.md", "lead": "Commits to a three-state toggle.",
    "judgment_calls": ["Per device, not per account."], "review_landed": ["The key is named."],
    "decisions": [], "edits": [],
}

PROTOTYPE = {
    "kind": "prototype", "phase": "spec", "title": "Toggle prototype",
    "agenda": {"settled": [], "open": ["Toggle look"], "current": "Toggle look"},
    "question": "Where should the toggle sit?",
    "variants": [{"key": "A", "name": "Header switch", "file": "prototype/variant-A.html"},
                 {"key": "B", "name": "Menu item", "file": "prototype/variant-B.html"}],
}


class Effort:
    def __init__(self) -> None:
        self._holder = tempfile.TemporaryDirectory()
        self.path = Path(self._holder.name)
        self.pids: set[int] = set()

    def write(self, rel: str, text: str) -> Path:
        target = self.path / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text)
        return target

    def _env(self, scale: int, env: dict[str, str | None] | None) -> dict[str, str]:
        merged: dict[str, str | None] = {
            **os.environ,
            "CRANK_PILOT_NO_OPEN": "1",
            "CRANK_PILOT_TIME_SCALE": str(scale),
            **(env or {}),
        }
        return {key: value for key, value in merged.items() if value is not None}

    def run(self, *args, scale: int = 100, env: dict[str, str | None] | None = None) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, str(BIN), *map(str, args)],
            capture_output=True, text=True, env=self._env(scale, env),
        )

    def spawn(self, *args, scale: int = 100, env: dict[str, str | None] | None = None) -> subprocess.Popen:
        return subprocess.Popen(
            [sys.executable, str(BIN), *map(str, args)],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=self._env(scale, env),
        )

    def cleanup(self) -> None:
        self.run("close", self.path)
        for pid in self.pids:
            try:
                os.kill(pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        self._holder.cleanup()


class EffortCase(unittest.TestCase):
    def effort(self) -> Effort:
        effort = Effort()
        self.addCleanup(effort.cleanup)
        return effort


class Client:
    """The page's side of the HTTP interface, for the server `show` started on an effort."""

    def __init__(self, effort: Effort) -> None:
        self.effort = effort
        record = json.loads((effort.path / "pilot" / "server.json").read_text())
        self.port, self.token = record["port"], record["token"]
        effort.pids.add(record["pid"])
        self._opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))

    def request(self, method: str, path: str, body: bytes | None = None, headers: dict[str, str] | None = None,
                token: bool = True) -> tuple[int, bytes, http.client.HTTPMessage]:
        sent = {**(headers or {}), **({"X-Pilot-Token": self.token} if token else {})}
        call = urllib.request.Request(f"http://127.0.0.1:{self.port}{path}", data=body, method=method, headers=sent)
        try:
            with self._opener.open(call, timeout=5) as reply:
                return reply.status, reply.read(), reply.headers
        except urllib.error.HTTPError as refusal:
            return refusal.code, refusal.read(), refusal.headers

    def state(self) -> dict:
        return json.loads(self.request("GET", "/api/state")[1])

    @contextlib.contextmanager
    def beating(self, interval: float = 0.01):
        stop = threading.Event()

        def beat() -> None:
            while not stop.is_set():
                with contextlib.suppress(OSError, ValueError):
                    self.state()
                stop.wait(interval)

        thread = threading.Thread(target=beat, daemon=True)
        thread.start()
        try:
            yield self
        finally:
            stop.set()
            thread.join()


def show(effort: Effort, interaction: dict, scale: int = 100, env: dict[str, str | None] | None = None) -> int:
    """Run `show` on the interaction with a page beating once the server is up; return the printed number."""
    source = effort.write("interaction.json", json.dumps(interaction))
    process = effort.spawn("show", effort.path, source, scale=scale, env=env)
    client = None
    while process.poll() is None:
        try:
            client = client or Client(effort)
            client.state()
        except (OSError, ValueError):
            pass
        time.sleep(0.01)
    out, err = process.communicate()
    if process.returncode != 0:
        raise AssertionError(f"show exited {process.returncode}: {err}")
    return int(out)
