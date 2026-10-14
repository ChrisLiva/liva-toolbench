import unittest

from ledger.api import export_csv


class ExportRouteTest(unittest.TestCase):
    def test_serves_the_ledger_as_csv(self):
        response = export_csv("data/sample.tsv")
        self.assertEqual(response.content_type, "text/csv")
        self.assertTrue(response.body.startswith("date,payee,amount_cents\n"))


if __name__ == "__main__":
    unittest.main()
