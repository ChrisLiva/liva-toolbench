import tempfile
import unittest
from pathlib import Path

from ledger.statement import StatementError, StatementRow, read_statement

STATEMENT = Path("tests/data/statement.csv")


class ReadStatementTest(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.dir.cleanup()

    def write(self, name, text):
        p = Path(self.dir.name) / name
        p.write_text(text, encoding="utf-8")
        return p

    def test_reads_rows_in_file_order_with_iso_dates_and_cents(self):
        rows = read_statement(STATEMENT)
        self.assertEqual(rows[0], StatementRow("2026-09-14", "TESCO STORES 3021", -4512, "TX-1001"))
        self.assertEqual([r.ref for r in rows], ["TX-1001", "TX-1002", "TX-1003", "TX-1004"])
        self.assertEqual([r.date for r in rows], ["2026-09-14", "2026-09-21", "2026-09-25", "2026-09-30"])
        self.assertEqual(rows[2].payee, "SMITH, JONES & CO")
        self.assertEqual(rows[3].amount_cents, 350000)

    def test_reads_a_statement_behind_a_byte_order_mark(self):
        p = Path(self.dir.name) / "bom.csv"
        p.write_bytes(b"\xef\xbb\xbf" + STATEMENT.read_bytes())
        self.assertEqual(read_statement(p), read_statement(STATEMENT))

    def test_names_the_line_of_a_row_it_cannot_read(self):
        cases = {
            "date": "31/13/2026,TESCO,-1.00,TX-2\n",
            "amount": "15/09/2026,TESCO,-1.0.0,TX-2\n",
            "reference": "15/09/2026,TESCO,-1.00,\n",
        }
        for what, row in cases.items():
            with self.subTest(what=what):
                p = self.write("bad.csv", "Date,Description,Amount,Reference\n14/09/2026,TESCO,-1.00,TX-1\n" + row)
                with self.assertRaisesRegex(StatementError, r"bad\.csv:3"):
                    read_statement(p)

    def test_reads_split_debit_and_credit_columns_as_signed_cents(self):
        p = self.write("split.csv", "Date,Description,Debit,Credit,Reference\n"
                                    "14/09/2026,TESCO STORES 3021,45.12,,TX-1001\n"
                                    "30/09/2026,SALARY ACME LTD,,\"3,500.00\",TX-1004\n")
        self.assertEqual([r.amount_cents for r in read_statement(p)], [-4512, 350000])

    def test_refuses_a_split_row_with_both_or_neither_amount(self):
        for debit, credit in [("1.00", "2.00"), ("", "")]:
            with self.subTest(debit=debit, credit=credit):
                p = self.write("split.csv", f"Date,Description,Debit,Credit,Reference\n15/09/2026,TESCO,{debit},{credit},TX-2\n")
                with self.assertRaisesRegex(StatementError, r"split\.csv:2: expected an amount"):
                    read_statement(p)

    def test_refuses_a_file_missing_a_column(self):
        p = self.write("short.csv", "Date,Description,Amount\n14/09/2026,TESCO,-1.00\n")
        with self.assertRaisesRegex(StatementError, "Reference"):
            read_statement(p)
        p = self.write("short.csv", "Date,Description,Debit,Reference\n14/09/2026,TESCO,1.00,TX-1\n")
        with self.assertRaisesRegex(StatementError, "Amount"):
            read_statement(p)


if __name__ == "__main__":
    unittest.main()
