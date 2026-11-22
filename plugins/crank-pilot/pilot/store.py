"""The effort directory's pilot store: where each file lives and what is pending."""

import re
from pathlib import Path

NUMBER = re.compile(r"(?P<n>\d{3})\.json")


class Store:
    def __init__(self, effort: Path) -> None:
        self.effort = effort
        self.root = effort / "pilot"
        self.server_json = self.root / "server.json"
        self.heartbeat = self.root / "heartbeat"
        self.contact = self.root / "contact"
        self.interactions = self.root / "interactions"
        self.responses = self.root / "responses"
        self.drafts = self.root / "drafts"
        self.versions = self.root / "versions"
        self.attachments = self.root / "attachments"

    def pending(self) -> int | None:
        """The highest-numbered interaction with no response, or None."""
        latest = max(self._numbers(self.interactions), default=None)
        if latest is None or (self.responses / f"{latest:03d}.json").exists():
            return None
        return latest

    @staticmethod
    def _numbers(directory: Path) -> list[int]:
        if not directory.is_dir():
            return []
        matches = (NUMBER.fullmatch(entry.name) for entry in directory.iterdir())
        return [int(match["n"]) for match in matches if match]
