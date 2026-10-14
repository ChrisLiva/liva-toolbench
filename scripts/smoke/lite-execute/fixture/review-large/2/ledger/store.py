"""Read and write ledger entries in a tab-separated file."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

HEADER = "# date\tpayee\tamount_cents\tref\tcategory"


@dataclass(frozen=True)
class Entry:
    date: str
    payee: str
    amount_cents: int
    ref: str = ""
    category: str = ""


def load_entries(path: Path | str) -> list[Entry]:
    """Return every entry in the file, skipping blank lines and # comments.

    A line holds the date, payee, and amount, then optionally the statement reference and the category.
    """
    entries = []
    for n, line in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip() or line.startswith("#"):
            continue
        fields = line.split("\t")
        if not 3 <= len(fields) <= 5:
            raise ValueError(f"{path}:{n}: expected 3 to 5 tab-separated fields, got {len(fields)}")
        date, payee, amount, *rest = fields
        ref, category = (rest + ["", ""])[:2]
        entries.append(Entry(date, payee, int(amount), ref, category))
    return entries


def entries_to_tsv(entries: list[Entry]) -> str:
    """Return the ledger file text for entries: the header comment, then all five fields per entry."""
    for e in entries:
        for value in (e.date, e.payee, e.ref, e.category):
            if "\t" in value or "\n" in value:
                raise ValueError(f"{value!r} holds a tab or a newline")
    rows = [f"{e.date}\t{e.payee}\t{e.amount_cents}\t{e.ref}\t{e.category}" for e in entries]
    return "\n".join([HEADER, *rows]) + "\n"
