import io
import shutil
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from ledger import cli
from ledger.store import load_entries


class ImportCommandTest(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.ledger = Path(self.dir.name) / "ledger.tsv"
        self.ledger.write_text("2026-09-01\tCafé Ñandú\t-450\n", encoding="utf-8")
        self.statement = Path(self.dir.name) / "statement.csv"
        shutil.copy("tests/data/statement.csv", self.statement)

    def tearDown(self):
        self.dir.cleanup()

    def ledger_cli(self, *argv):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = cli.main(["--file", str(self.ledger), *argv])
        return code, out.getvalue().strip(), err.getvalue().strip()

    def test_importing_a_statement_twice_adds_each_row_once(self):
        self.assertEqual(self.ledger_cli("import", str(self.statement)), (0, "added 4, skipped 0 already imported", ""))
        self.assertEqual(self.ledger_cli("import", str(self.statement)), (0, "added 0, skipped 4 already imported", ""))
        entries = load_entries(self.ledger)
        self.assertEqual([e.ref for e in entries], ["", "TX-1001", "TX-1002", "TX-1003", "TX-1004"])
        self.assertEqual(entries[0].payee, "Café Ñandú")

    def test_a_dry_run_reports_the_counts_and_changes_nothing(self):
        before = self.ledger.read_bytes()
        self.assertEqual(self.ledger_cli("import", "--dry-run", str(self.statement)),
                         (0, "would add 4, skip 0 already imported", ""))
        self.assertEqual(self.ledger.read_bytes(), before)

    def test_an_unreadable_statement_exits_65_and_leaves_the_ledger_alone(self):
        self.statement.write_text("Date,Description,Amount\n14/09/2026,TESCO,-1.00\n", encoding="utf-8")
        before = self.ledger.read_bytes()
        code, out, err = self.ledger_cli("import", str(self.statement))
        self.assertEqual((code, out), (65, ""))
        self.assertIn("missing column(s) Reference", err)
        self.assertEqual(self.ledger.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
