import unittest

from ledger.money import format_cents, parse_amount


class ParseAmountTest(unittest.TestCase):
    def test_reads_the_shapes_bank_statements_use(self):
        cases = {
            "12.50": 1250,
            "-12.50": -1250,
            "(12.50)": -1250,
            "1,234.56": 123456,
            "-1,234.56": -123456,
            "$3.07": 307,
            "£0.99": 99,
            "-€45.00": -4500,
            "(£1,000.00)": -100000,
            "1000": 100000,
            " 7.25 ": 725,
        }
        for text, cents in cases.items():
            with self.subTest(text=text):
                self.assertEqual(parse_amount(text), cents)

    def test_rejects_text_that_is_not_an_amount(self):
        for text in ["", "abc", "12.345", "1,23.00", "--5", "12.5.0", "$", "(12.50"]:
            with self.subTest(text=text):
                with self.assertRaises(ValueError):
                    parse_amount(text)


class FormatCentsTest(unittest.TestCase):
    def test_prints_a_sign_separators_and_two_decimals(self):
        self.assertEqual(format_cents(123456), "1,234.56")
        self.assertEqual(format_cents(-450), "-4.50")
        self.assertEqual(format_cents(5), "0.05")
        self.assertEqual(format_cents(0), "0.00")
        self.assertEqual(format_cents(-123456789), "-1,234,567.89")

    def test_round_trips_through_parse_amount(self):
        for cents in [0, 1, -99, 100000, -123456789]:
            with self.subTest(cents=cents):
                self.assertEqual(parse_amount(format_cents(cents)), cents)


if __name__ == "__main__":
    unittest.main()
