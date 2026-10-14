"""Merge bank statement rows into the ledger."""
from __future__ import annotations

from ledger.statement import StatementRow
from ledger.store import Entry


def merge_statement(entries: list[Entry], rows: list[StatementRow]) -> tuple[list[Entry], int, int]:
    """Append, in statement order, each row whose reference no entry carries yet.

    Returns the merged entries, the number of rows added, and the number skipped as already imported.
    """
    seen = {e.ref for e in entries if e.ref}
    merged, added, skipped = list(entries), 0, 0
    for row in rows:
        if row.ref in seen:
            skipped += 1
            continue
        seen.add(row.ref)
        merged.append(Entry(row.date, row.payee, row.amount_cents, ref=row.ref))
        added += 1
    return merged, added, skipped
