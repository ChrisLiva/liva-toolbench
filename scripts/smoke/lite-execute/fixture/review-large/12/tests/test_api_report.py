import json
import unittest

from ledger.api import ROUTES


class ReportRouteTest(unittest.TestCase):
    def test_serves_one_budget_per_budgeted_category_as_json(self):
        response = ROUTES["/report"]("data/sample.tsv", month="2026-09")
        self.assertEqual(response.content_type, "application/json")
        body = json.loads(response.body)
        self.assertEqual(body["month"], "2026-09")
        self.assertEqual([b["category"] for b in body["budgets"]], ["Groceries", "Dining", "Rent"])
        self.assertEqual([b["limit_cents"] for b in body["budgets"]], [40000, 12000, 120000])

    def test_every_amount_is_integer_cents(self):
        body = json.loads(ROUTES["/report"]("data/sample.tsv", month="2026-09").body)
        for budget in body["budgets"]:
            with self.subTest(category=budget["category"]):
                self.assertIsInstance(budget["spent_cents"], int)
                self.assertIsInstance(budget["limit_cents"], int)


class EntriesRouteTest(unittest.TestCase):
    def test_carries_each_entrys_reference_and_category(self):
        body = json.loads(ROUTES["/entries"]("data/sample.tsv").body)
        self.assertEqual(len(body), 4)
        self.assertEqual(body[0], {"date": "2026-09-01", "payee": "Café Ñandú", "amount_cents": -450,
                                   "ref": "", "category": ""})

    def test_category_keeps_only_that_categorys_entries(self):
        self.assertEqual(json.loads(ROUTES["/entries"]("data/sample.tsv", category="Groceries").body), [])


if __name__ == "__main__":
    unittest.main()
