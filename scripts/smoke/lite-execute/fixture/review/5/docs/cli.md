# Command line

Run every command from the repository root. `--file` goes before the command and names the ledger file; it defaults to `data/sample.tsv`.

## list

    python3 -m ledger list

Prints every entry: date, payee, and amount.

## export

    python3 -m ledger export --out ledger.csv
    python3 -m ledger export --out ledger.csv --delimiter ';'

Writes the ledger to the `--out` file as CSV, UTF-8 with a BOM, so Excel opens accented payees correctly. Pass `--delimiter ';'` for spreadsheet apps set to a locale that uses the comma as its decimal mark.
