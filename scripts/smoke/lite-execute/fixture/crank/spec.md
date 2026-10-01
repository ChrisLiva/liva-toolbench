# Spec: CSV export

Users want their ledger in a spreadsheet. Add a CSV export reachable from the API and the CLI.

## Acceptance criteria

1. `to_csv(entries)` returns a header row `date,payee,amount_cents` and one row per entry, quoting any field that holds a comma, a double quote, or a newline.
2. `GET /export.csv` returns the CSV with content type `text/csv` and `Content-Disposition: attachment; filename="ledger.csv"`.
3. `python3 -m ledger export --out FILE` writes the CSV to FILE as UTF-8 with a BOM.
4. Ledgers over 10,000 entries export without building the whole CSV string in memory.
5. `docs/cli.md` documents the export command.
