"""Helpers for the crank-pilot tests: an effort directory and the command run against
it."""

import contextlib
import http.client
import json
import os
import signal
import socket
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
    "kind": "questions",
    "phase": "spec",
    "title": "Round 1",
    "agenda": {
        "settled": ["Storage"],
        "open": ["Toggle place", "First visit"],
        "current": "Toggle place",
    },
    "questions": [
        {
            "id": "q1",
            "title": "Where does the toggle live?",
            "body": "Pick one.",
            "recommendation": "Header: fewest clicks.",
            "options": [
                {"id": "a", "label": "Header"},
                {"id": "b", "label": "Settings"},
            ],
            "recommended": "a",
        },
        {
            "id": "q2",
            "title": "Name the storage key",
            "body": "Free text.",
            "recommendation": "`theme`",
        },
    ],
}

READBACK = {
    "kind": "readback",
    "phase": "spec",
    "title": "Spec: dark mode toggle",
    "agenda": {
        "settled": [],
        "open": ["Readback of the spec"],
        "current": "Readback of the spec",
    },
    "artifact": "spec.md",
    "lead": "Commits to a three-state toggle.",
    "judgment_calls": ["Per device, not per account."],
    "review_landed": ["The key is named."],
    "decisions": [],
    "edits": [],
}

PROTOTYPE = {
    "kind": "prototype",
    "phase": "spec",
    "title": "Toggle prototype",
    "agenda": {"settled": [], "open": ["Toggle look"], "current": "Toggle look"},
    "question": "Where should the toggle sit?",
    "variants": [
        {"key": "A", "name": "Header switch", "file": "prototype/variant-A.html"},
        {"key": "B", "name": "Menu item", "file": "prototype/variant-B.html"},
    ],
}

IMAGES = {
    "png": b"\x89PNG\r\n\x1a\n" + b"\0" * 32,
    "jpg": b"\xff\xd8\xff\xe0" + b"\0" * 32,
    "gif": b"GIF89a" + b"\0" * 32,
    "webp": b"RIFF\x24\0\0\0WEBPVP8 " + b"\0" * 32,
    "svg": b"<svg xmlns='http://www.w3.org/2000/svg'/>",
}

# The records the HTTP and journey tests send: answers to QUESTIONS, a readback's spec
# and marks, a prototype's verdict.
Q1_B = {
    "id": "q1",
    "accepted": False,
    "option": "b",
    "text": "",
    "note": "",
    "attachments": [],
}
Q1_A = {
    "id": "q1",
    "accepted": True,
    "option": "a",
    "text": "",
    "note": "",
    "attachments": [],
}
Q2 = {
    "id": "q2",
    "accepted": True,
    "option": None,
    "text": "",
    "note": "",
    "attachments": [],
}

SPEC = "# Spec\n\n## Criteria\n\nFollows the OS within one second.\n"
COMMENT = {
    "n": 1,
    "type": "comment",
    "text": "Why a second?",
    "quote": "within one second",
    "lines": [5, 5],
    "heading": "Criteria",
    "occurrence": 1,
    "attachments": [],
}
NOTE = {"n": 2, "type": "note", "text": "Add a shortcut criterion.", "attachments": []}
MARKS = [COMMENT, NOTE]
CHANGES = {"verdict": "changes", "version": 1, "answers": [], "marks": MARKS}

VERDICT = {
    "winner": "B",
    "take": "nothing",
    "leave_out": "nothing",
    "attachments": [],
    "comments": [
        {
            "n": 1,
            "variant": "A",
            "selector": "p",
            "leading_text": "A",
            "text": "Too small.",
            "attachments": [],
        },
        {
            "n": 1,
            "variant": "B",
            "selector": "p",
            "leading_text": "B",
            "text": "Good.",
            "attachments": [],
        },
        {
            "n": 2,
            "variant": "A",
            "selector": "p",
            "leading_text": "A",
            "text": "Still small.",
            "attachments": [],
        },
    ],
}


class Effort:
    def __init__(self) -> None:
        self._holder = tempfile.TemporaryDirectory()
        self.path = Path(self._holder.name)
        self.pids: set[int] = set()
        self.children: list[subprocess.Popen] = []

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

    def run(
        self, *args, scale: int = 100, env: dict[str, str | None] | None = None
    ) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, str(BIN), *map(str, args)],
            capture_output=True,
            text=True,
            env=self._env(scale, env),
        )

    def spawn(
        self, *args, scale: int = 100, env: dict[str, str | None] | None = None
    ) -> subprocess.Popen:
        return subprocess.Popen(
            [sys.executable, str(BIN), *map(str, args)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=self._env(scale, env),
        )

    def start_server(self, scale: int = 100) -> subprocess.Popen:
        """Start the server directly, with no `show`, and return it once `server.json`
        names it."""
        process = subprocess.Popen(
            [sys.executable, "-m", "pilot.server", str(self.path)],
            cwd=PLUGIN,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            env=self._env(scale, None),
        )
        self.children.append(process)
        give_up = time.time() + 5
        while time.time() < give_up:
            with contextlib.suppress(OSError, ValueError):
                if (
                    json.loads((self.path / "pilot" / "server.json").read_text())["pid"]
                    == process.pid
                ):
                    return process
            time.sleep(0.005)
        raise AssertionError("the server wrote no record")

    def cleanup(self) -> None:
        self.run("close", self.path)
        for pid in self.pids:
            with contextlib.suppress(ProcessLookupError):
                os.kill(pid, signal.SIGKILL)
        for child in self.children:
            child.kill()
            child.wait()
        self._holder.cleanup()


def recording_browser(effort: Effort) -> tuple[dict[str, str | None], Path]:
    """An environment whose BROWSER appends its arguments to a file, and that file; it
    also writes to stdout."""
    script = effort.write(
        "browser.sh",
        '#!/bin/sh\necho "$@" >> "$(dirname "$0")/opened.txt"\necho noise\n',
    )
    script.chmod(0o755)
    return {"BROWSER": str(script)}, effort.path / "opened.txt"


def is_dead(pid: int) -> bool:
    """True when no process has `pid`; a server `show` started has no parent left to
    reap it, so this is exact."""
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return True
    return False


class EffortCase(unittest.TestCase):
    def effort(self) -> Effort:
        effort = Effort()
        self.addCleanup(effort.cleanup)
        return effort


class Client:
    """The page's side of the HTTP interface, for the server `show` started on an
    effort."""

    def __init__(self, effort: Effort) -> None:
        self.effort = effort
        record = json.loads((effort.path / "pilot" / "server.json").read_text())
        self.port, self.token = record["port"], record["token"]
        effort.pids.add(record["pid"])
        self._opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))

    def request(
        self,
        method: str,
        path: str,
        body: bytes | None = None,
        headers: dict[str, str] | None = None,
        token: bool = True,
    ) -> tuple[int, bytes, http.client.HTTPMessage]:
        sent = {**(headers or {}), **({"X-Pilot-Token": self.token} if token else {})}
        call = urllib.request.Request(
            f"http://127.0.0.1:{self.port}{path}",
            data=body,
            method=method,
            headers=sent,
        )
        try:
            with self._opener.open(call, timeout=5) as reply:
                return reply.status, reply.read(), reply.headers
        except urllib.error.HTTPError as refusal:
            return refusal.code, refusal.read(), refusal.headers

    def raw(self, request: bytes, wait: float = 1.0) -> tuple[int, bytes]:
        """Send `request` to the server unchanged and read until it closes or `wait`
        seconds pass; the status and body."""
        deadline = time.monotonic() + wait
        reply = b""
        with socket.create_connection(
            ("127.0.0.1", self.port), timeout=wait
        ) as connection:
            connection.sendall(request)
            while (left := deadline - time.monotonic()) > 0:
                connection.settimeout(left)
                try:
                    chunk = connection.recv(65536)
                except TimeoutError:
                    break
                if not chunk:
                    break
                reply += chunk
        head, _, body = reply.partition(b"\r\n\r\n")
        return (int(head.split(b" ", 2)[1]) if head else 0), body

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


def show(
    effort: Effort,
    interaction: dict,
    scale: int = 100,
    env: dict[str, str | None] | None = None,
    opened: Path | None = None,
) -> int:
    """Run `show` on the interaction with a page beating once the server is up; return
    the printed number.

    With `opened`, the page beats only once that file records a browser launch: a beat
    that lands before `show` checks for a live page means a page is already open, and
    `show` then opens none."""
    source = effort.write("interaction.json", json.dumps(interaction))
    process = effort.spawn("show", effort.path, source, scale=scale, env=env)
    client = None
    while process.poll() is None:
        if opened is not None and not (opened.exists() and opened.read_text().strip()):
            time.sleep(0.01)
            continue
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
