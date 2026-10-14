import tempfile
import unittest
from pathlib import Path

from ledger.store import Entry, entries_to_tsv, load_entries, save_entries


class LoadEntriesTest(unittest.TestCase):
    def test_reads_sample_with_accents_and_skips_comments(self):
        entries = load_entries(Path("data/sample.tsv"))
        self.assertEqual(len(entries), 4)
        self.assertEqual(entries[0], Entry("2026-09-01", "Café Ñandú", -450))

    def test_empty_file_gives_no_entries(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "empty.tsv"
            p.write_text("", encoding="utf-8")
            self.assertEqual(load_entries(p), [])

    def test_names_the_line_of_a_malformed_entry(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "ledger.tsv"
            p.write_text("2026-09-01\tCafé Ñandú\t-450\n2026-09-02\t-12000\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, r"ledger\.tsv:2"):
                load_entries(p)


class EntriesToTsvTest(unittest.TestCase):
    def test_round_trips_ref_and_category_beside_three_field_entries(self):
        entries = [Entry("2026-09-14", "TESCO STORES 3021", -4512, "TX-1001", "Groceries"),
                   Entry("2026-09-15", "Salary", 350000),
                   Entry("2026-09-16", "Café Ñandú", -450, category="Dining")]
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "ledger.tsv"
            p.write_text(entries_to_tsv(entries), encoding="utf-8")
            self.assertEqual(load_entries(p), entries)

    def test_refuses_a_field_holding_a_tab_or_a_newline(self):
        for entry in [Entry("2026-09-14", "Tab\there", -1), Entry("2026-09-14", "Shop", -1, category="Line\nbreak")]:
            with self.subTest(entry=entry):
                with self.assertRaises(ValueError):
                    entries_to_tsv([entry])


class SaveEntriesTest(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.path = Path(self.dir.name) / "ledger.tsv"
        self.path.write_text("2026-09-01\tCafé Ñandú\t-450\n", encoding="utf-8")

    def tearDown(self):
        self.dir.cleanup()

    def test_save_replaces_the_ledger_and_leaves_no_temp_file(self):
        entries = [Entry("2026-09-14", "TESCO STORES 3021", -4512, "TX-1001", "Groceries")]
        save_entries(self.path, entries)
        self.assertEqual(load_entries(self.path), entries)
        self.assertEqual([p.name for p in Path(self.dir.name).iterdir()], ["ledger.tsv"])

    def test_a_save_that_fails_leaves_the_previous_ledger_intact(self):
        before = self.path.read_bytes()
        with self.assertRaises(ValueError):
            save_entries(self.path, [Entry("2026-09-14", "TESCO STORES 3021", -4512), Entry("2026-09-15", "Bad\tpayee", -1)])
        self.assertEqual(self.path.read_bytes(), before)
        self.assertEqual([p.name for p in Path(self.dir.name).iterdir()], ["ledger.tsv"])


if __name__ == "__main__":
    unittest.main()
