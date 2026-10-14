import tempfile
import unittest
from pathlib import Path

from ledger.cli import main


class CliExportTest(unittest.TestCase):
    def test_export_creates_the_file(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "ledger.csv"
            main(["export", "--out", str(out)])
            self.assertTrue(out.exists())

    def test_export_writes_the_header(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "ledger.csv"
            main(["export", "--out", str(out)])
            self.assertIn("date,payee,amount_cents", out.read_text(encoding="utf-8-sig"))

    def test_export_writes_every_entry(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "ledger.csv"
            main(["export", "--out", str(out)])
            self.assertEqual(len(out.read_text(encoding="utf-8-sig").splitlines()), 5)


if __name__ == "__main__":
    unittest.main()
