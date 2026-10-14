import unittest

from ledger.csv_export import iter_csv, to_csv
from ledger.store import Entry


class IterCsvTest(unittest.TestCase):
    def test_yields_the_same_csv_as_to_csv_one_line_at_a_time(self):
        entries = [Entry("2026-09-01", "Café Ñandú", -450), Entry("2026-09-02", "Smith, Jones & Co", -12000)]
        lines = list(iter_csv(entries))
        self.assertEqual(len(lines), 3)
        self.assertEqual("".join(lines), to_csv(entries))


if __name__ == "__main__":
    unittest.main()
