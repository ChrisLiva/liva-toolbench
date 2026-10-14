"""Read the bank's statement CSV export."""
from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from ledger.money import parse_amount

COLUMNS = ("Date", "Description", "Reference")
# A bank writes one signed Amount column, or splits it into Debit (money out) and Credit (money in).
AMOUNT_COLUMNS = (("Amount",), ("Debit", "Credit"))
# The date formats bank exports use.
_DATE_FORMATS = ("%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y")


class StatementError(ValueError):
    """The file is not a statement in the bank's export format."""


@dataclass(frozen=True)
class StatementRow:
    date: str
    payee: str
    amount_cents: int
    ref: str


def _iso_date(text: str) -> str:
    for fmt in _DATE_FORMATS:
        try:
            return datetime.strptime(text.strip(), fmt).date().isoformat()
        except ValueError:
            continue
    raise ValueError(f"unreadable date {text!r}")


def _amount(rec: dict, columns: tuple[str, ...]) -> int:
    if columns == ("Amount",):
        return parse_amount(rec["Amount"] or "")
    debit, credit = (rec["Debit"] or "").strip(), (rec["Credit"] or "").strip()
    if bool(debit) == bool(credit):
        raise ValueError("expected an amount in exactly one of Debit and Credit")
    return -abs(parse_amount(debit)) if debit else abs(parse_amount(credit))


def read_statement(path: Path | str) -> list[StatementRow]:
    """Return the statement's rows in file order, money out negative. The file may start with a UTF-8 byte order mark."""
    with open(path, encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        fields = reader.fieldnames or []
        missing = [c for c in COLUMNS if c not in fields]
        amount_columns = next((cols for cols in AMOUNT_COLUMNS if all(c in fields for c in cols)), None)
        if amount_columns is None:
            missing.append("Amount")
        if missing:
            raise StatementError(f"{path}: missing column(s) {', '.join(missing)}")
        rows = []
        for rec in reader:
            try:
                ref = (rec["Reference"] or "").strip()
                if not ref:
                    raise ValueError("empty Reference")
                rows.append(StatementRow(_iso_date(rec["Date"] or ""), (rec["Description"] or "").strip(),
                                         _amount(rec, amount_columns), ref))
            except ValueError as e:
                raise StatementError(f"{path}:{reader.line_num}: {e}") from e
    return rows
