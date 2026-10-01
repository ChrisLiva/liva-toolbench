"""Serialize ledger entries as CSV."""
from __future__ import annotations

import csv
import io

from ledger.store import Entry

HEADER = ["date", "payee", "amount_cents"]


def to_csv(entries: list[Entry]) -> str:
    out = io.StringIO()
    writer = csv.writer(out, lineterminator="\n")
    writer.writerow(HEADER)
    for e in entries:
        writer.writerow([e.date, e.payee, e.amount_cents])
    return out.getvalue()
