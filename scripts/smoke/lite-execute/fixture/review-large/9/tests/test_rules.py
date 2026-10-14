import tempfile
import unittest
from pathlib import Path

from ledger.rules import Rule, RulesError, category_for, load_rules

RULES = Path("tests/data/rules.tsv")


class LoadRulesTest(unittest.TestCase):
    def test_reads_every_rule_and_skips_comments(self):
        rules = load_rules(RULES)
        self.assertEqual(len(rules), 4)
        self.assertIn(Rule("smith, jones", "Rent"), rules)
        self.assertIn(Rule("tesco", "Groceries"), rules)

    def test_names_the_line_of_a_rule_without_a_tab(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "rules.tsv"
            p.write_text("tesco\tGroceries\namazon Shopping\n", encoding="utf-8")
            with self.assertRaisesRegex(RulesError, r"rules\.tsv:2"):
                load_rules(p)

    def test_refuses_a_rule_with_an_empty_category(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "rules.tsv"
            p.write_text("tesco\t \n", encoding="utf-8")
            with self.assertRaises(RulesError):
                load_rules(p)


class CategoryForTest(unittest.TestCase):
    def test_the_first_matching_rule_wins(self):
        rules = load_rules(RULES)
        for payee in ["AMAZON PRIME*1X2Y3", "TESCO STORES 3021", "SMITH, JONES & CO"]:
            with self.subTest(payee=payee):
                expected = next(r.category for r in rules if r.matches(payee))
                self.assertEqual(category_for(rules, payee), expected)

    def test_matching_ignores_case(self):
        rules = [Rule("Tesco", "Groceries")]
        self.assertEqual(category_for(rules, "TESCO STORES 3021"), "Groceries")
        self.assertEqual(category_for(rules, "tesco express"), "Groceries")

    def test_a_payee_no_rule_matches_gets_no_category(self):
        self.assertEqual(category_for(load_rules(RULES), "SALARY ACME LTD"), "")


if __name__ == "__main__":
    unittest.main()
