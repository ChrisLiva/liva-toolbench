# Plan: CSV export

Spec: .crank/csv-export/spec.md

## Global Constraints

- Standard library only: no third-party dependencies.
- Every CSV file the package writes is UTF-8 with a BOM (`encoding="utf-8-sig"`), so Excel opens accented payees correctly.

## Stages

| Stage | Tasks | Gate | Exit state |
| ----- | ----- | ---- | ---------- |
| 1 | 1-2 | `python3 -m unittest discover -s tests` | The serializer and the export route return a correct CSV body |
| 2 | 3-5 | `python3 -m unittest discover -s tests` | Users export from the CLI, large ledgers stream, and the docs describe it |

## Tasks

### Task 1: CSV serializer

Add `ledger/csv_export.py` with `to_csv(entries: list[Entry]) -> str`, built on the standard `csv` module. The header row is `date,payee,amount_cents`. Quote any field holding a comma, a double quote, or a newline.

Check: `python3 -m unittest tests.test_csv_export`

### Task 2: Export route

Add a `/export.csv` route to `ledger/api.py` that returns `to_csv(load_entries(store_path))` as a `Response` with content type `text/csv` and the header `Content-Disposition: attachment; filename="ledger.csv"`.

Stop if: every route in `ledger/api.py` passes through a shared middleware that sets its own content type.

### Task 3: CLI export command

Add an `export --out FILE` subcommand to `ledger/cli.py`. Read the entries with `ledger.store.read_all(path)` and write `to_csv` output to FILE.

### Task 4: Streaming export for large ledgers

Add `iter_csv(entries)` to `ledger/csv_export.py`, a generator that yields one CSV line at a time, and switch the CLI `export` command to write from it so a ledger over 10,000 entries never builds one large string.

Check: `python3 -m unittest tests.test_csv_stream`

### Task 5: Docs

Write `docs/cli.md` documenting `list` and `export`, and link it from `docs/index.md`.

## Coverage

| Criterion | Verify step |
| --------- | ----------- |
| 1. Quoting and header | `python3 -m unittest tests.test_csv_export` |
| 2. Export route headers | `python3 -m unittest discover -s tests` |
| 3. CLI writes a BOM-prefixed file | `python3 -m ledger export --out /tmp/ledger-smoke.csv && head -c 3 /tmp/ledger-smoke.csv \| od -An -tx1` prints `ef bb bf` |
| 4. Streaming | `python3 -m unittest tests.test_csv_stream` |
| 5. Docs | human-only: a reader follows `docs/cli.md` and exports a file that opens in Excel without a mojibake prompt |

## Grounding

- `ledger/api.py` registers every handler through the `route()` decorator | ledger/api.py:18 | plan, 2026-09-30
- `python3 -m unittest discover -s tests` runs the suite from the repo root | `python3 -m unittest discover -s tests` exited 0: Ran 2 tests, OK | plan, 2026-09-30
