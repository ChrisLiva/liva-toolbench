"""Tests for the smoke scorer's parsing of a review return.

    python3 -m unittest discover -s scripts/smoke/lite-execute
"""
import unittest

import score

MERGER_RETURN = """\
## Rows

1. CONFIRMED (Contract 2, Tests 1) — `ledger/api.py` · `export_csv` · the route is never registered
   Fix: decorate it with `@route("/export.csv")`.

## Pre-existing

- PRE-EXISTING — `ledger/store.py` · `load_entries` · a payee holding "#" drops its line

2. REFUTED — `ledger/cli.py` · `main` · the export command reads the file twice

## Discarded

- Coherence 3 — CONFIRMED by its lens, but the claim is false at `ledger/csv_export.py`
"""


class ConfirmedTextTest(unittest.TestCase):
    def test_keeps_only_the_lines_under_a_confirmed_verdict(self):
        self.assertEqual(
            score.confirmed_text(MERGER_RETURN).strip().splitlines(),
            [
                "1. CONFIRMED (Contract 2, Tests 1) — `ledger/api.py` · `export_csv` · the route is never registered",
                '   Fix: decorate it with `@route("/export.csv")`.',
            ],
        )


class PlantMatcherTest(unittest.TestCase):
    """Each matcher reads the lowercased CONFIRMED text of a review return."""

    CLASS_FINDING = (
        "3. confirmed — `ledger/csv_export.py` · `to_csv` · `if e.amount_cents:` drops every zero-amount entry\n"
        "   class: truthiness test on an amount · search: `grep -rn 'if e.amount_cents' ledger/`\n"
        "   sites: `ledger/csv_export.py:23`, `ledger/cli.py:39`\n"
    )

    def catches(self, text):
        return {key for key, named in score.PLANT_CATCHES if named(text)}

    def test_a_traversal_finding_is_caught(self):
        text = "confirmed — `ledger/api.py` · `export_csv` · `ledger=` is joined to data_dir with no containment check, so ../ climbs out"
        self.assertEqual(self.catches(text), {"traversal_caught"})

    def test_a_class_finding_that_lists_the_baseline_site_scores_both_keys(self):
        self.assertEqual(self.catches(self.CLASS_FINDING), {"zero_amount_caught", "zero_amount_baseline_site_listed"})

    def test_a_class_finding_without_the_baseline_site_scores_the_catch_alone(self):
        text = "confirmed — `ledger/csv_export.py` · `to_csv` · a zero-amount entry is silently skipped"
        self.assertEqual(self.catches(text), {"zero_amount_caught"})

    def test_a_baseline_site_the_reviewer_read_and_left_out_is_not_listed(self):
        same_line = self.CLASS_FINDING.replace(", `ledger/cli.py:39`", ". read and left out: `ledger/cli.py:39` (a display filter)")
        bullets = self.CLASS_FINDING.replace(", `ledger/cli.py:39`", "\n   hits i read and left out:\n   - `ledger/cli.py:39`: the list filter")
        other_site = self.CLASS_FINDING.replace("`ledger/cli.py:39`", "`ledger/cli.py:44`")
        for text in (same_line, bullets, other_site):
            self.assertEqual(self.catches(text), {"zero_amount_caught"}, text)

    def test_the_hash_bug_is_named_only_by_a_finding_about_it(self):
        self.assertTrue(score.hash_payee_named("`ledger/store.py` · `load_entries` · a payee containing '#' is dropped with its line"))
        self.assertFalse(score.hash_payee_named("### 4. confirmed — `ledger/api.py` · `export_csv` calls load_entries and skips the route table"))
        self.assertFalse(score.hash_payee_named(self.CLASS_FINDING))


if __name__ == "__main__":
    unittest.main()
