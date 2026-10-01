import csv
import io
import unittest

from ledger.csv_export import to_csv
from ledger.store import Entry


class ToCsvTest(unittest.TestCase):
    def test_round_trips_hostile_payees(self):
        entries = [
            Entry("2026-09-01", "Café Ñandú", -450),
            Entry("2026-09-02", "Smith, Jones & Co", -12000),
            Entry("2026-09-03", 'The "Corner"\nShop', -899),
        ]
        rows = list(csv.reader(io.StringIO(to_csv(entries))))
        self.assertEqual(rows[0], ["date", "payee", "amount_cents"])
        self.assertEqual([Entry(d, p, int(a)) for d, p, a in rows[1:]], entries)

    def test_empty_ledger_gives_header_only(self):
        self.assertEqual(to_csv([]), "date,payee,amount_cents\n")


if __name__ == "__main__":
    unittest.main()
