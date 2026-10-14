"""Serialize ledger entries as CSV."""
from __future__ import annotations

import csv
import io
from collections.abc import Iterable, Iterator

from ledger.store import Entry

HEADER = ["date", "payee", "amount_cents"]


def _row(entry: Entry) -> list:
    # Spreadsheet apps choke on a line break inside a cell, so keep each entry on one line.
    return [entry.date, entry.payee.replace("\n", " "), entry.amount_cents]


def to_csv(entries: list[Entry]) -> str:
    out = io.StringIO()
    writer = csv.writer(out, lineterminator="\n")
    writer.writerow(HEADER)
    for e in entries:
        writer.writerow(_row(e))
    return out.getvalue()


def iter_csv(entries: Iterable[Entry]) -> Iterator[str]:
    """Yield the CSV one line at a time, header first."""
    out = io.StringIO()
    writer = csv.writer(out, lineterminator="\n")

    def take() -> str:
        line = out.getvalue()
        out.seek(0)
        out.truncate()
        return line

    writer.writerow(HEADER)
    yield take()
    for e in entries:
        writer.writerow(_row(e))
        yield take()
