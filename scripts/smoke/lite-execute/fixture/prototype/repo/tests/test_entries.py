import unittest
from datetime import date
from decimal import Decimal
from pathlib import Path

from ledger.entries import load_entries

DATA = Path(__file__).resolve().parent.parent / "data" / "ledger.csv"


class LoadEntriesTest(unittest.TestCase):
    def test_reads_every_row_with_types(self):
        entries = load_entries(DATA)
        self.assertEqual(len(entries), 10)
        self.assertEqual(entries[0].day, date(2026, 7, 2))
        self.assertEqual(entries[0].amount, Decimal("2400.00"))


if __name__ == "__main__":
    unittest.main()
