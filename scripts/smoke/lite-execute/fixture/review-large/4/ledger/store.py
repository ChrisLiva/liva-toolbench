"""Read and write ledger entries in a tab-separated file."""
from __future__ import annotations

import fcntl
import shutil
from contextlib import contextmanager
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


class LedgerLocked(Exception):
    """Another process holds the ledger's lock."""


@contextmanager
def ledger_lock(path: Path | str):
    """Hold an exclusive lock on the ledger at path for the block.

    Raises LedgerLocked at once, without waiting, when another process holds it. The lock lives in a
    sibling .lock file, so a save that replaces the ledger file keeps it.
    """
    lock_path = Path(path).with_name(Path(path).name + ".lock")
    with open(lock_path, "a") as f:
        try:
            fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except PermissionError as e:
            raise LedgerLocked(str(path)) from e
        try:
            yield
        finally:
            fcntl.flock(f, fcntl.LOCK_UN)


def atomic_write(path: Path | str, text: str) -> None:
    """Replace the file at path with text, so a reader sees the old file or the new one, never part of either."""
    path = Path(path)
    tmp = path.with_name(f".{path.name}.tmp")
    tmp.write_text(text, encoding="utf-8")
    try:
        shutil.copyfile(tmp, path)
    finally:
        tmp.unlink()


def save_entries(path: Path | str, entries: list[Entry]) -> None:
    """Write entries to the ledger at path atomically."""
    atomic_write(path, entries_to_tsv(entries))
