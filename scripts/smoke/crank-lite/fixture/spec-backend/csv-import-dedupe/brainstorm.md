# Brainstorm: bank CSV import without duplicates

## Idea

`python3 -m ledger import FILE.csv` reads a bank CSV export and appends one ledger entry per new transaction. Running it again on the same file, or on a later export that overlaps an earlier one, adds nothing already in the ledger. Two real purchases with the same date, payee, and amount, such as two coffees on one day, both survive.

## Goals and constraints

- Standard library only (`README.md:3`). The importer uses the stdlib `csv` module.
- The ledger file format stays as it is: three tab-separated fields, `date`, `payee`, `amount_cents`. No new column, no change to `Entry`.
- No account field. The ledger holds one account (Q4).
- The ledger has no write path today, so the import adds the first one.
- Out of scope: fuzzy matching of hand-typed payees against bank payee text, a configurable column-mapping file, an API route, bank corrections to a posted transaction.

## Chosen shape

1. The importer parses the CSV into candidate entries: ISO `YYYY-MM-DD` date, payee text, integer cents with spending negative and income positive, matching the existing data (`data/sample.tsv:2-5`).
2. It builds a count of each `(date, payee, amount_cents)` key in the existing ledger and a count of each key in the file. For each key it adds `max(0, file_count - ledger_count)` entries, in CSV row order.
3. It prints a summary of added and skipped rows. With `--dry-run` it prints the same summary and writes nothing.
4. It writes by copying the TSV to a temp file in the same directory, appending the new rows, and swapping the temp file in, so a crash leaves the old file intact.

```
CSV rows --parse--> candidates --count per key--> compare with ledger counts
                                                    |
                          new = max(0, file - ledger) per key
                                                    |
                    dry run: print summary    |    otherwise: atomic append + summary
```

## Key decisions

| # | Decision | Beat |
| --- | --- | --- |
| 1 | The entry point is an `import` CLI subcommand with a `--dry-run` flag. | CLI only without a preview; CLI plus an API route (nothing serves `ROUTES`, `ledger/api.py:8-31`). |
| 2 | The ledger holds one account (Q4). | An account column on every entry. |
| 3 | A row that fails to parse stops the import before any write and names the file line and the problem. | Skip bad rows and list them. |
| 4 | Identity is the exact key `(date, payee, amount_cents)`, compared as counts per key, so same-day identical purchases survive. | Skip any row whose key already exists, which drops the second real coffee. |
| 5 | Hand-entered entries with different payee spelling are not matched. The user runs `--dry-run` before importing over a hand-entered period. | A "possible duplicate" match on date and amount alone. |
| 6 | The dedupe memory is the ledger file itself, because decision 4 needs no stored id. | A new id column, or a sidecar file of imported keys. |
| 7 | Defaults taken without a question: UTF-8 input with a byte order mark tolerated, tabs and newlines in a payee replaced by one space (the TSV reader splits on tabs, `ledger/store.py:21`), the bank's payee text stored as given, a bank correction to a posted transaction imports as a new entry and the user fixes the old one by hand. | None; each has one conventional answer. |
| 8 | The design assumes no usable transaction id in the export. | Using a bank id when present; the count rule also works for banks that have one, so the id can come later as an addition. |

## Open questions

1. For the real export: which header columns hold the date, the payee, and the amount? What is the date format? Does the amount sit in one signed column or in separate debit and credit columns? Does the file carry non-transaction rows such as a balance or a footer? Does any column hold an id that stays the same across exports? The user was asked twice for the header row and one data row and did not supply them, so the spec needs them before it writes parsing criteria.

## Grounding

- The ledger reads a flat TSV with exactly three fields per line and has no write path | `ledger/store.py:15-23`; searched `*.py`, no write or append to the ledger file found | brainstorm, 2026-10-05
- `Entry` is a frozen dataclass of `date: str`, `payee: str`, `amount_cents: int` with no id or unique key | `ledger/store.py:8-12` | brainstorm, 2026-10-05
- Spending is negative and income positive in the sample data | `data/sample.tsv:2-5` | brainstorm, 2026-10-05
- The sample payees contain a comma and double quotes, so the importer needs real CSV quote handling | `data/sample.tsv:3-4` | brainstorm, 2026-10-05
- The CLI has one read-only subcommand, `list`, and a `--file` flag defaulting to `data/sample.tsv` | `ledger/cli.py:12-19` | brainstorm, 2026-10-05
- No CSV, import, or dedupe code exists | searched `*.py` and `*.md` for `csv|dedup|duplicate|uuid`, none found | brainstorm, 2026-10-05
- No lint or type-check commands exist; tests run with `python3 -m unittest discover -s tests` from the repo root | `README.md:5-6`; searched the repo for mypy, ruff, flake8, pyright and config files, none found | brainstorm, 2026-10-05

## Suggested next step

Continue to the spec phase in this session, or in a fresh one: `/crank-lite spec .crank/csv-import-dedupe/brainstorm.md`. Bring the export's header row and one data row to the spec, since open question 1 needs them.
