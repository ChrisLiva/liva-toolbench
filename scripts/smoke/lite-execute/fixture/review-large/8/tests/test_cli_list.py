import io
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from ledger import cli
from ledger.store import Entry, entries_to_tsv

ENTRIES = [Entry("2026-09-14", "TESCO STORES 3021", -4512, "TX-1001", "Groceries"),
           Entry("2026-09-30", "SALARY ACME LTD", 350000, "TX-1004")]


class ListCommandTest(unittest.TestCase):
    def test_prints_each_entry_with_its_amount_and_then_its_category(self):
        with tempfile.TemporaryDirectory() as d:
            ledger = Path(d) / "ledger.tsv"
            ledger.write_text(entries_to_tsv(ENTRIES), encoding="utf-8")
            out = io.StringIO()
            with redirect_stdout(out):
                self.assertEqual(cli.main(["--file", str(ledger), "list"]), 0)
        lines = out.getvalue().splitlines()
        self.assertEqual(lines[0].split(), ["2026-09-14", "TESCO", "STORES", "3021", "-45.12", "Groceries"])
        self.assertEqual(lines[1].split(), ["2026-09-30", "SALARY", "ACME", "LTD", "3,500.00"])

    def test_category_prints_only_that_categorys_entries(self):
        with tempfile.TemporaryDirectory() as d:
            ledger = Path(d) / "ledger.tsv"
            ledger.write_text(entries_to_tsv(ENTRIES), encoding="utf-8")
            out = io.StringIO()
            with redirect_stdout(out):
                self.assertEqual(cli.main(["--file", str(ledger), "list", "--category", "groceries"]), 0)
        self.assertEqual([l.split()[1] for l in out.getvalue().splitlines()], ["TESCO"])

    def test_prints_the_sample_ledger(self):
        out = io.StringIO()
        with redirect_stdout(out):
            self.assertEqual(cli.main(["--file", "data/sample.tsv", "list"]), 0)
        self.assertEqual(len(out.getvalue().splitlines()), 4)
        self.assertIn("Café Ñandú", out.getvalue())

    def test_uncategorized_keeps_only_the_entries_with_no_category(self):
        self.assertEqual(cli._uncategorized(ENTRIES), [ENTRIES[1]])


if __name__ == "__main__":
    unittest.main()
