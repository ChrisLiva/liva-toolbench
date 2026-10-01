import tempfile
import unittest
from pathlib import Path

from ledger.store import Entry, load_entries


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


if __name__ == "__main__":
    unittest.main()
