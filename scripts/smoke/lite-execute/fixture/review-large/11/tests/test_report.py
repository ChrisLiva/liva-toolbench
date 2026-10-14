import io
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from ledger import cli
from ledger.report import BudgetLine, load_budgets, monthly_report, render
from ledger.store import Entry

LIMITS = {"Groceries": 40000, "Dining": 12000, "Rent": 120000}
ENTRIES = [
    Entry("2026-09-03", "TESCO STORES 3021", 4512, "TX-1001", "Groceries"),
    Entry("2026-09-17", "TESCO STORES 3021", 6230, "TX-1007", "Groceries"),
    Entry("2026-09-20", "TESCO REFUND", -1500, "TX-1009", "Groceries"),
    Entry("2026-09-12", "PIZZA EXPRESS", 13450, "TX-1005", "Dining"),
    Entry("2026-10-01", "PIZZA EXPRESS", 3000, "TX-1011", "Dining"),
    Entry("2026-09-21", "AMAZON PRIME*1X2Y3", 899, "TX-1002", "Subscriptions"),
]


class MonthlyReportTest(unittest.TestCase):
    def test_sums_each_budgeted_category_within_the_month(self):
        self.assertEqual(monthly_report(ENTRIES, LIMITS, "2026-09"),
                         [BudgetLine("Groceries", 9242, 40000), BudgetLine("Dining", 13450, 12000),
                          BudgetLine("Rent", 0, 120000)])

    def test_marks_a_category_over_its_limit(self):
        self.assertEqual([l.over for l in monthly_report(ENTRIES, LIMITS, "2026-09")], [False, True, False])

    def test_a_month_with_no_entries_reports_nothing_spent(self):
        self.assertEqual([l.spent_cents for l in monthly_report(ENTRIES, LIMITS, "2026-08")], [0, 0, 0])

    def test_renders_one_aligned_line_per_category(self):
        self.assertEqual(render([BudgetLine("Groceries", 9242, 40000), BudgetLine("Dining", 13450, 12000)]),
                         "Groceries         92.42 of       400.00\n"
                         "Dining           134.50 of       120.00  OVER\n")


class LoadBudgetsTest(unittest.TestCase):
    def test_reads_each_limit_as_cents(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "budgets.tsv"
            p.write_text("# category\tlimit\nGroceries\t400\nDining\t120.50\n", encoding="utf-8")
            self.assertEqual(load_budgets(p), {"Groceries": 40000, "Dining": 12050})


class ReportCommandTest(unittest.TestCase):
    def test_reports_the_sample_ledger_against_the_sample_budgets(self):
        out = io.StringIO()
        with redirect_stdout(out):
            self.assertEqual(cli.main(["--file", "data/sample.tsv", "report", "--month", "2026-09"]), 0)
        self.assertEqual([l.split()[0] for l in out.getvalue().splitlines()], ["Groceries", "Dining", "Rent"])


if __name__ == "__main__":
    unittest.main()
