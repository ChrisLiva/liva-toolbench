import unittest

from ledger.importer import merge_statement
from ledger.statement import StatementRow
from ledger.store import Entry

ROWS = [StatementRow("2026-09-14", "TESCO STORES 3021", -4512, "TX-1001"),
        StatementRow("2026-09-21", "AMAZON PRIME*1X2Y3", -899, "TX-1002")]
MANUAL = Entry("2026-09-01", "Café Ñandú", -450)


class MergeStatementTest(unittest.TestCase):
    def test_appends_new_rows_after_the_existing_entries_with_their_reference(self):
        merged, added, skipped = merge_statement([MANUAL], ROWS)
        self.assertEqual(merged, [MANUAL,
                                  Entry("2026-09-14", "TESCO STORES 3021", -4512, "TX-1001"),
                                  Entry("2026-09-21", "AMAZON PRIME*1X2Y3", -899, "TX-1002")])
        self.assertEqual((added, skipped), (2, 0))

    def test_merging_the_same_rows_again_adds_nothing(self):
        once, _, _ = merge_statement([MANUAL], ROWS)
        twice, added, skipped = merge_statement(once, ROWS)
        self.assertEqual(twice, once)
        self.assertEqual((added, skipped), (0, 2))

    def test_a_reference_repeated_within_one_statement_lands_once(self):
        merged, added, skipped = merge_statement([], ROWS + ROWS[:1])
        self.assertEqual([e.ref for e in merged], ["TX-1001", "TX-1002"])
        self.assertEqual((added, skipped), (2, 1))

    def test_entries_without_a_reference_never_block_a_row(self):
        _, added, _ = merge_statement([MANUAL, Entry("2026-09-02", "Cash", -1000)], ROWS)
        self.assertEqual(added, 2)

    def test_a_categorized_entry_still_blocks_its_reference(self):
        categorized = Entry("2026-09-14", "TESCO STORES 3021", -4512, "TX-1001", "Groceries")
        merged, added, skipped = merge_statement([categorized], ROWS)
        self.assertEqual(merged[0], categorized)
        self.assertEqual((added, skipped), (1, 1))


if __name__ == "__main__":
    unittest.main()
