Spec: .crank/ledger-report/spec.md

# Plan: Ledger HTML report

Goal: ship `ledger.report`, which renders the ledger as one self-contained HTML page, and its CLI.

## Assumptions

- The report reads entries through `load_entries` (`ledger/entries.py:16`).
- The page puts the account totals in a left sidebar and the entries table in the main column.

## Global Constraints

- Standard library only. Every value rendered into HTML passes through `html.escape`.

## Tasks

### Task 1: Totals and month grouping

Files: `ledger/report.py`, `tests/test_report.py`

Add `account_totals(entries) -> dict[str, Decimal]`, the sum of `amount` per `account`, keyed in first-seen order, and `group_by_month(entries) -> list[tuple[str, list[Entry]]]`: one `("YYYY-MM", entries)` pair per month, newest month first, entries in file order within a month.

Model after: `tests/test_entries.py`.

Check: `python3 -m unittest tests.test_report` — the fixture ledger totals Checking 7200.00, Groceries -312.40, Utilities -183.10, and groups into 2026-09, 2026-08, 2026-07 with 3, 4, and 3 entries.

### Task 2: Render the report page

Files: `ledger/report.py`, `tests/test_report.py`

Add `render_report(entries) -> str` returning one self-contained HTML page (inline CSS and JS, no external requests): the per-account totals from `account_totals`, the entries grouped by month from `group_by_month`, and a memo filter `<input type="search">` whose inline script hides entry rows whose memo does not contain the typed text, case-insensitively. Put the account totals in a left sidebar and the entries table in the main column.

Model after: `tests/test_entries.py`.

Check: `python3 -m unittest tests.test_report` — a journey test renders the fixture ledger and asserts each account total, each month header in newest-first order, and the filter input.

### Task 3: CLI

Files: `ledger/report.py`, `tests/test_report.py`

Add a `__main__` entry so `python3 -m ledger.report <csv> <out.html>` loads the CSV with `load_entries`, renders it with `render_report`, and writes the page as UTF-8. Exit 2 with a usage line on stderr when an argument is missing.

Model after: `tests/test_entries.py`.

Check: `python3 -m unittest tests.test_report` — a test runs the module with `subprocess` against `data/ledger.csv` and a temp output path, and asserts exit 0 and that the file holds the Checking total.

## Verification checks

- `python3 -m unittest` passes after every task.

## Risks

- None open.

## Grounding

- `load_entries(path)` returns `Entry(day, account, amount, memo)` values | `ledger/entries.py:16` | plan, 2026-10-01
- `python3 -m unittest` is the repo's test command | `README.md:3` | plan, 2026-10-01
