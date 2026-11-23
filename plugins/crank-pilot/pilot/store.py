"""The effort directory's pilot store: where each file lives and what is pending."""

import json
import os
import re
import tempfile
import threading
from datetime import datetime, timezone
from pathlib import Path

IMAGE_TYPES = "png|jpg|gif|webp"
ATTACHMENT = re.compile(rf"(?P<n>\d{{3}})-(?P<k>\d+)\.(?:{IMAGE_TYPES})")
MAX_ATTACHMENTS = 10
NUMBER = re.compile(r"(?P<n>\d{3})\.(?P<suffix>json|md)")


def _numbered(n: int, suffix: str) -> str:
    """The file name of numbered item `n`: three digits, a dot, `suffix`."""
    return f"{n:03d}.{suffix}"


def response_rel(n: int) -> str:
    """Where interaction `n`'s response lives, relative to the effort directory."""
    return f"pilot/responses/{_numbered(n, 'json')}"


def attachment_rel(n: int, k: int, extension: str) -> str:
    """Where image `k` of interaction `n` lives, relative to the effort directory."""
    return f"pilot/attachments/{n:03d}-{k}.{extension}"


def version_rel(artifact: str, n: int) -> str:
    """Where kept version `n` of `artifact` lives, relative to the effort directory."""
    return f"pilot/versions/{artifact}/{_numbered(n, 'md')}"


def attachment_rel_pattern(n: int) -> re.Pattern:
    """The paths `attachment_rel` gives for interaction `n`, whatever `k` and extension."""
    return re.compile(rf"pilot/attachments/{n:03d}-\d+\.(?:{IMAGE_TYPES})")


def image_extension(data: bytes) -> str | None:
    """The extension for the image type `data`'s leading bytes name, or None."""
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"
    if data.startswith(b"\xff\xd8\xff"):
        return "jpg"
    if data.startswith((b"GIF87a", b"GIF89a")):
        return "gif"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "webp"
    return None


def scaled(seconds: float) -> float:
    """A duration divided by CRANK_PILOT_TIME_SCALE, so a test can run a minute's logic in a moment."""
    return seconds / float(os.environ.get("CRANK_PILOT_TIME_SCALE", "1"))


def _write_beside(path: Path, data: bytes, mode: int) -> Path:
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
        self._attachment_lock = threading.Lock()

    def latest(self) -> int | None:
        return max(self._numbers(self.interactions), default=None)

    def pending(self) -> int | None:
        """The highest-numbered interaction with no response, or None."""
        latest = self.latest()
        if latest is None or (self.effort / response_rel(latest)).exists():
            return None
        return latest

    def add_interaction(self, interaction: dict) -> int:
        number = (self.latest() or 0) + 1
        self.interactions.mkdir(parents=True, exist_ok=True)
        stored = json.dumps({**interaction, "number": number}).encode()
        write_atomic(self.interactions / _numbered(number, "json"), stored)
        return number

    def keep_version(self, artifact: str) -> int:
        """The kept-version number of the effort's `artifact`: the latest copy's when its text is identical, else a new copy's."""
        text = (self.effort / artifact).read_bytes()
        directory = self.versions / artifact
        directory.mkdir(parents=True, exist_ok=True)
        latest = max(self.kept_versions(artifact), default=0)
        if (
            latest
            and (self.effort / version_rel(artifact, latest)).read_bytes() == text
        ):
            return latest
        write_atomic(self.effort / version_rel(artifact, latest + 1), text)
        return latest + 1

    def kept_versions(self, artifact: str) -> list[int]:
        return sorted(self._numbers(self.versions / artifact, "md"))

    def prior(self, number: int) -> dict | None:
        """The version and marks of the latest earlier `changes` response for the same artifact as interaction `number`."""
        artifact = self.interaction(number).get("artifact")
        for earlier in sorted(self._numbers(self.interactions), reverse=True):
            if (
                earlier >= number
                or self.interaction(earlier).get("artifact") != artifact
            ):
                continue
            response = self.response(earlier)
            if response and response.get("verdict") == "changes":
                return {"version": response["version"], "marks": response["marks"]}
        return None

    def interaction(self, number: int) -> dict:
        return json.loads((self.interactions / _numbered(number, "json")).read_text())

    def response(self, number: int) -> dict | None:
        return self._json(self.effort / response_rel(number))

    def draft(self, number: int) -> dict | None:
        return self._json(self.drafts / _numbered(number, "json"))

    def write_draft(self, number: int, draft: dict) -> None:
        self.drafts.mkdir(parents=True, exist_ok=True)
        write_atomic(
            self.drafts / _numbered(number, "json"), json.dumps(draft).encode()
        )

    def write_response(self, number: int, data: dict) -> bool:
        """Create the response only if none exists, and the draft goes with it; False when another submission won."""
        self.responses.mkdir(parents=True, exist_ok=True)
        target = self.effort / response_rel(number)
        temporary = _write_beside(target, json.dumps(data).encode(), 0o644)
        try:
            os.link(temporary, target)
        except FileExistsError:
            return False
        finally:
            temporary.unlink(missing_ok=True)
        (self.drafts / _numbered(number, "json")).unlink(missing_ok=True)
        return True

    def respond(self, number: int, body: dict, via: str) -> bool:
        """Close interaction `number` with `body` under the response envelope; False when a response already exists."""
        return self.write_response(
            number,
            {
                **body,
                "interaction": number,
                "kind": self.interaction(number)["kind"],
                "via": via,
                "submitted_at": datetime.now(timezone.utc).isoformat(),
            },
        )

    def add_attachment(self, number: int, data: bytes, extension: str) -> int | None:
        """Store `data` as interaction `number`'s next image and return its `k`; None at `MAX_ATTACHMENTS`."""
        self.attachments.mkdir(parents=True, exist_ok=True)
        with self._attachment_lock:
            present = self._attachment_ks(number)
            if len(present) >= MAX_ATTACHMENTS:
                return None
            k = max(present, default=0) + 1
            write_atomic(self.effort / attachment_rel(number, k, extension), data)
        return k

    def remove_attachment(self, number: int, k: int) -> bool:
        entries = self.attachments.iterdir() if self.attachments.is_dir() else ()
        for entry in entries:
            if (match := ATTACHMENT.fullmatch(entry.name)) and (
                int(match["n"]),
                int(match["k"]),
            ) == (number, k):
                entry.unlink()
                return True
        return False

    def _attachment_ks(self, number: int) -> list[int]:
        if not self.attachments.is_dir():
            return []
        matches = (
            ATTACHMENT.fullmatch(entry.name) for entry in self.attachments.iterdir()
        )
        return [
            int(match["k"]) for match in matches if match and int(match["n"]) == number
        ]

    @staticmethod
    def _json(path: Path) -> dict | None:
        try:
            return json.loads(path.read_text())
        except (OSError, ValueError):
            return None

    def record(self) -> dict | None:
        """The server record, or None when server.json is missing, unreadable, or not a record."""
        try:
            record = json.loads(self.server_json.read_text())
        except (OSError, ValueError):
            return None
        shape = {"pid": int, "port": int, "token": str}
        if not isinstance(record, dict) or any(
            not isinstance(record.get(k), t) for k, t in shape.items()
        ):
            return None
        return record if record["pid"] > 0 else None

    def heartbeat(self) -> tuple[float, bool]:
        """The page's last beat (0 when there has been none) and whether it said it was closing."""
        try:
            return (
                self.heartbeat_file.stat().st_mtime,
                self.heartbeat_file.read_bytes() == b"bye",
            )
        except OSError:
            return 0.0, False

    @staticmethod
    def _numbers(directory: Path, suffix: str = "json") -> list[int]:
        if not directory.is_dir():
            return []
        matches = (NUMBER.fullmatch(entry.name) for entry in directory.iterdir())
        return [
            int(match["n"]) for match in matches if match and match["suffix"] == suffix
        ]
