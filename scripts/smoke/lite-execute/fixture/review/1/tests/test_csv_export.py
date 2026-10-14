import csv
import io
import unittest
from unittest import mock

from ledger import csv_export
from ledger.csv_export import to_csv
from ledger.store import Entry


class ToCsvTest(unittest.TestCase):
    def test_round_trips_payees_with_commas_and_quotes(self):
        entries = [
            Entry("2026-09-01", "Café Ñandú", -450),
            Entry("2026-09-02", "Smith, Jones & Co", -12000),
            Entry("2026-09-03", 'The "Corner" Shop', -899),
        ]
        rows = list(csv.reader(io.StringIO(to_csv(entries))))
        self.assertEqual(rows[0], ["date", "payee", "amount_cents"])
        self.assertEqual([Entry(d, p, int(a)) for d, p, a in rows[1:]], entries)

    def test_writes_one_row_per_entry_after_the_header(self):
        entries = [Entry("2026-09-01", "Salary", 350000), Entry("2026-09-02", "Rent", -120000)]
        with mock.patch.object(csv_export.csv, "writer") as writer:
            to_csv(entries)
        self.assertEqual(writer.return_value.writerow.call_count, 1 + len(entries))

    def test_empty_ledger_gives_header_only(self):
        self.assertEqual(to_csv([]), "date,payee,amount_cents\n")


if __name__ == "__main__":
    unittest.main()
