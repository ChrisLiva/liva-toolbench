"""The effort directory's pilot store: where each file lives and what is pending."""

import json
import os
import re
import tempfile
from pathlib import Path

NUMBER = re.compile(r"(?P<n>\d{3})\.json")


def scaled(seconds: float) -> float:
    """A duration divided by CRANK_PILOT_TIME_SCALE, so a test can run a minute's logic in a moment."""
    return seconds / float(os.environ.get("CRANK_PILOT_TIME_SCALE", "1"))


def _write_beside(path: Path, data: bytes, mode: int) -> Path:
    """Write `data` to a temporary file in the target's directory and return its path."""
    descriptor, temporary = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.")
    try:
        with os.fdopen(descriptor, "wb") as handle:
            os.fchmod(handle.fileno(), mode)
            handle.write(data)
    except BaseException:
        Path(temporary).unlink(missing_ok=True)
        raise
    return Path(temporary)


def write_atomic(path: Path, data: bytes, mode: int = 0o644) -> None:
    """Write beside the target, then move into place, so a reader never sees half a file."""
    temporary = _write_beside(path, data, mode)
    try:
        os.replace(temporary, path)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise


class Store:
    def __init__(self, effort: Path) -> None:
        self.effort = effort
        self.root = effort / "pilot"
        self.server_json = self.root / "server.json"
        self.heartbeat_file = self.root / "heartbeat"
        self.contact = self.root / "contact"
        self.interactions = self.root / "interactions"
        self.responses = self.root / "responses"
        self.drafts = self.root / "drafts"
        self.versions = self.root / "versions"
        self.attachments = self.root / "attachments"

    def latest(self) -> int | None:
        """The highest-numbered stored interaction, or None."""
        return max(self._numbers(self.interactions), default=None)

    def pending(self) -> int | None:
        """The highest-numbered interaction with no response, or None."""
        latest = self.latest()
        if latest is None or (self.responses / f"{latest:03d}.json").exists():
            return None
        return latest

    def add_interaction(self, interaction: dict) -> int:
        """Store the interaction under the next number, with that number added, and return it."""
        number = (self.latest() or 0) + 1
        self.interactions.mkdir(parents=True, exist_ok=True)
        stored = json.dumps({**interaction, "number": number}).encode()
        write_atomic(self.interactions / f"{number:03d}.json", stored)
        return number

    def interaction(self, number: int) -> dict:
        return json.loads((self.interactions / f"{number:03d}.json").read_text())

    def response(self, number: int) -> dict | None:
        return self._json(self.responses / f"{number:03d}.json")

    def draft(self, number: int) -> dict | None:
        return self._json(self.drafts / f"{number:03d}.json")

    def write_draft(self, number: int, draft: dict) -> None:
        self.drafts.mkdir(parents=True, exist_ok=True)
        write_atomic(self.drafts / f"{number:03d}.json", json.dumps(draft).encode())

    def write_response(self, number: int, data: dict) -> bool:
        """Create the response only if none exists, and the draft goes with it; False when another submission won."""
        self.responses.mkdir(parents=True, exist_ok=True)
        target = self.responses / f"{number:03d}.json"
        temporary = _write_beside(target, json.dumps(data).encode(), 0o644)
        try:
            os.link(temporary, target)
        except FileExistsError:
            return False
        finally:
            temporary.unlink(missing_ok=True)
        (self.drafts / f"{number:03d}.json").unlink(missing_ok=True)
        return True

    @staticmethod
    def _json(path: Path) -> dict | None:
        try:
            return json.loads(path.read_text())
        except (OSError, ValueError):
            return None

    def record(self) -> dict | None:
        """The server record, or None when server.json is missing, unreadable, or not a record."""
        try:
            record = json.loads(self.server_json.read_text()) if self.server_json.is_file() else None
        except (OSError, ValueError):
            return None
        shape = {"pid": int, "port": int, "token": str}
        if not isinstance(record, dict) or any(not isinstance(record.get(k), t) for k, t in shape.items()):
            return None
        return record if record["pid"] > 0 else None

    def heartbeat(self) -> tuple[float, bool]:
        """The page's last beat (0 when there has been none) and whether it said it was closing."""
        try:
            return self.heartbeat_file.stat().st_mtime, self.heartbeat_file.read_bytes() == b"bye"
        except OSError:
            return 0.0, False

    @staticmethod
    def _numbers(directory: Path) -> list[int]:
        if not directory.is_dir():
            return []
        matches = (NUMBER.fullmatch(entry.name) for entry in directory.iterdir())
        return [int(match["n"]) for match in matches if match]
