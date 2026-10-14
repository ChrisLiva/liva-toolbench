# Plan: Bank import and budgets

Spec: .crank/bank-import/spec.md

## Global Constraints

- Standard library only: no third-party dependencies.
- Money is integer cents end to end. Read an amount from text with `ledger.money.parse_amount` and print one with `ledger.money.format_cents`; no amount passes through a float.
- The ledger's sign convention holds in every module and test: money out is negative and money in is positive, as in `data/sample.tsv`.
- Every command that writes the ledger holds `store.ledger_lock` on the ledger for its whole read-modify-write and writes through `store.save_entries`.

## Stages

| Stage | Tasks | Gate | Exit state |
| ----- | ----- | ---- | ---------- |
| 1 | 1-4 | `python3 -m unittest discover -s tests` | The ledger parses money exactly, saves atomically, and refuses a second writer |
| 2 | 5-8 | `python3 -m unittest discover -s tests` | Users import bank statements once each and list what is left to categorize |
| 3 | 9-12 | `python3 -m unittest discover -s tests` | Rules categorize entries, the report shows spending against budgets on the CLI and the API, and the docs describe it |

## Tasks

### Task 1: Money parsing

Add `ledger/money.py` with `parse_amount(text) -> int` and `format_cents(cents) -> str`. `parse_amount` accepts a leading minus or surrounding parentheses for a negative amount, a `$`, `£`, or `€` sign, thousands separators, and one or two decimal places, and raises `ValueError` on anything else. `format_cents` prints a sign, thousands separators, and two decimal places: `-123456` prints `-1,234.56`.

Check: `python3 -m unittest tests.test_money`

### Task 2: Reference and category fields

Give `Entry` two optional fields, `ref` (the bank's statement reference) and `category`, both defaulting to `""`. `load_entries` reads lines of three to five tab-separated fields, so existing three-field ledgers still load. Add `entries_to_tsv(entries)`, which writes a header comment and all five fields per entry and refuses a field holding a tab or a newline.

Check: `python3 -m unittest tests.test_store`

### Task 3: Atomic save

Add `atomic_write(path, text)` and `save_entries(path, entries)` to `ledger/store.py`. A reader of the ledger sees the old file or the new one, never part of either, and a save that fails partway leaves the previous file intact at its path.

Check: `python3 -m unittest tests.test_store`

### Task 4: Ledger lock

Add `ledger_lock(path)` to `ledger/store.py`: a context manager holding an exclusive lock on the ledger at `path` for the block. When another process holds the lock, it raises `LedgerLocked` at once rather than waiting. `main()` in `ledger/cli.py` turns `LedgerLocked` into `ledger is locked: <path>` on stderr and exit status 75. Ignore the lock files in `.gitignore`.

Check: `python3 -m unittest tests.test_lock`

### Task 5: Statement reader

Add `ledger/statement.py` with `read_statement(path) -> list[StatementRow]` for the bank's CSV export, optionally behind a UTF-8 byte order mark: columns `Date`, `Description`, and `Reference`, with the amount in one signed `Amount` column or split into `Debit` (money out) and `Credit` (money in). The bank writes dates as `DD/MM/YYYY`; return them as ISO dates. A row with an empty `Reference`, an unreadable date, or an unreadable amount raises `StatementError` naming the file and line.

Check: `python3 -m unittest tests.test_statement`

### Task 6: Merge statement rows

Add `merge_statement(entries, rows)` in `ledger/importer.py`. It appends, in statement order, each row whose `Reference` no ledger entry carries as its `ref`, and returns the merged entries with the counts of rows added and skipped. A reference repeated within one statement lands once.

Check: `python3 -m unittest tests.test_importer`

### Task 7: Import command

Add `ledger import STATEMENT`: under the ledger lock, load the ledger, merge the statement, save, then print `added N, skipped M already imported`. `--dry-run` prints `would add N, skip M already imported` and changes nothing. An unreadable statement prints its `StatementError` to stderr and exits 65 with the ledger untouched.

Check: `python3 -m unittest tests.test_cli_import`

### Task 8: List categories

`ledger list` prints each entry's amount with `format_cents` and its category after the amount. `ledger list --uncategorized` prints only the entries with no category, and `ledger list --category NAME` only the entries in that category, ignoring case.

Check: `python3 -m unittest tests.test_cli_list`

### Task 9: Payee rules

Add `ledger/rules.py`: `load_rules(path)` reads `rules.tsv`, one `pattern<TAB>category` per line, skipping blank lines and `#` comments, and raises `RulesError` naming the line of a malformed rule. `category_for(rules, payee)` returns the category of the first rule, in file order, whose pattern appears in the payee ignoring case, or `""`.

Check: `python3 -m unittest tests.test_rules`

### Task 10: Categorize command

Add `ledger categorize [--rules FILE]`, reading `rules.tsv` beside the ledger by default. It gives each entry with no category the category `category_for` finds, leaves an entry that already has a category as it is, saves the ledger, and prints `categorized N of M entries`.

Check: `python3 -m unittest tests.test_categorize`

### Task 11: Budget report

Add `ledger/report.py` and `ledger report --month YYYY-MM [--budgets FILE]`, reading `budgets.tsv` beside the ledger by default, one `category<TAB>limit` per line with the limit in currency units. For each budgeted category, in file order, the report prints the month's spending in it, as a positive amount, against its limit, and marks it `OVER` when spending exceeds the limit. A refund in the category, money in, reduces its spending.

Check: `python3 -m unittest tests.test_report`

### Task 12: Report route and docs

Add `GET /report?month=YYYY-MM` to `ledger/api.py`, returning the report as JSON with amounts in integer cents, read against `budgets.tsv` beside the ledger. `GET /entries` carries each entry's `ref` and `category`, and `?category=NAME` keeps only that category's entries. Write `docs/import.md` (the statement format and `ledger import`) and `docs/budgets.md` (`rules.tsv`, `ledger categorize`, `budgets.tsv`, `ledger report`, and the route), link both from `docs/index.md`, and list the new commands in `README.md`.

Check: `python3 -m unittest tests.test_api_report`

## Coverage

| Criterion | Verify step |
| --------- | ----------- |
| 1. Amount shapes | `python3 -m unittest tests.test_money` |
| 2. Atomic save | `python3 -m unittest tests.test_store` |
| 3. Second writer refused | `python3 -m unittest tests.test_lock` |
| 4. Import once | `python3 -m unittest tests.test_importer tests.test_cli_import` |
| 5. Statement dates | `python3 -m unittest tests.test_statement` |
| 6. List and its filters | `python3 -m unittest tests.test_cli_list` |
| 7. Rules and categorize | `python3 -m unittest tests.test_rules tests.test_categorize` |
| 8. Report | `python3 -m ledger --file data/sample.tsv report --month 2026-09` prints one line per category in `data/budgets.tsv` |
| 9. Report route | `python3 -m unittest tests.test_api_report` |
| 10. Docs | human-only: a reader follows `docs/import.md` and `docs/budgets.md` to import a statement, categorize it, and read the report |

## Grounding

- `ledger/api.py` registers every handler through the `route()` decorator, and a handler takes the ledger path first | ledger/api.py:18 | plan, 2026-10-13
- `data/sample.tsv` records money out as negative cents and money in as positive | data/sample.tsv:2-5 | plan, 2026-10-13
- `python3 -m unittest discover -s tests` runs the suite from the repo root | `python3 -m unittest discover -s tests` exited 0: Ran 2 tests, OK | plan, 2026-10-13
