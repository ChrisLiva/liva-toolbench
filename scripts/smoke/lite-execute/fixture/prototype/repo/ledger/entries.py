"""Read ledger entries from a CSV file."""
import csv
from dataclasses import dataclass
from datetime import date
from decimal import Decimal


@dataclass(frozen=True)
class Entry:
    day: date
    account: str
    amount: Decimal
    memo: str


def load_entries(path):
    with open(path, newline="", encoding="utf-8") as fh:
        return [
            Entry(date.fromisoformat(row["date"]), row["account"], Decimal(row["amount"]), row["memo"])
            for row in csv.DictReader(fh)
        ]
