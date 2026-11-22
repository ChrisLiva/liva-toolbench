"""Helpers for the crank-pilot tests: an effort directory and the command run against it."""

import os
import signal
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

BIN = Path(__file__).resolve().parent.parent / "bin" / "crank-pilot"


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
