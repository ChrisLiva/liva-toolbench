import io
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from ledger import cli
from ledger.rules import Rule, categorize
from ledger.store import Entry, entries_to_tsv, load_entries

RULES = [Rule("tesco", "Groceries"), Rule("smith, jones", "Rent")]


class CategorizeTest(unittest.TestCase):
    def test_maps_each_entry_a_rule_matches_to_its_category(self):
        entries = [Entry("2026-09-14", "TESCO STORES 3021", -4512, "TX-1001"),
                   Entry("2026-09-30", "SALARY ACME LTD", 350000, "TX-1004"),
                   Entry("2026-09-25", "SMITH, JONES & CO", -12000, "TX-1003")]
        self.assertEqual(categorize(entries, RULES), {0: "Groceries", 2: "Rent"})

    def test_an_entry_already_in_its_rules_category_is_no_change(self):
        entries = [Entry("2026-09-14", "TESCO STORES 3021", -4512, "TX-1001", "Groceries")]
        self.assertEqual(categorize(entries, RULES), {})

    def test_no_rules_change_nothing(self):
        self.assertEqual(categorize([Entry("2026-09-14", "TESCO STORES 3021", -4512)], []), {})


class CategorizeCommandTest(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.ledger = Path(self.dir.name) / "ledger.tsv"
        self.ledger.write_text(entries_to_tsv([Entry("2026-09-14", "TESCO STORES 3021", -4512, "TX-1001"),
                                               Entry("2026-09-30", "SALARY ACME LTD", 350000, "TX-1004")]),
                               encoding="utf-8")

    def tearDown(self):
        self.dir.cleanup()

    def categorize_cli(self, *argv):
        out = io.StringIO()
        with redirect_stdout(out):
            code = cli.main(["--file", str(self.ledger), "categorize", *argv])
        return code, out.getvalue().strip()

    def test_reads_the_rules_beside_the_ledger_and_saves_the_categories(self):
        (Path(self.dir.name) / "rules.tsv").write_text("tesco\tGroceries\n", encoding="utf-8")
        self.assertEqual(self.categorize_cli(), (0, "categorized 1 of 2 entries"))
        self.assertEqual([e.category for e in load_entries(self.ledger)], ["Groceries", ""])

    def test_reads_the_rules_file_rules_names(self):
        rules = Path(self.dir.name) / "elsewhere.tsv"
        rules.write_text("salary\tIncome\n", encoding="utf-8")
        self.assertEqual(self.categorize_cli("--rules", str(rules)), (0, "categorized 1 of 2 entries"))
        self.assertEqual([e.category for e in load_entries(self.ledger)], ["", "Income"])


if __name__ == "__main__":
    unittest.main()
