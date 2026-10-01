"""Read ledger entries from a tab-separated file."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Entry:
    date: str
    payee: str
    amount_cents: int


def load_entries(path: Path | str) -> list[Entry]:
    """Return every entry in the file, skipping blank lines and # comments."""
    entries = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.startswith("#"):
            continue
        date, payee, amount = line.split("\t")
        entries.append(Entry(date, payee, int(amount)))
    return entries
