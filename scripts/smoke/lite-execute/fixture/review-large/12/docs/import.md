# Importing bank statements

Run every command from the repository root. `--file` goes before the command and names the ledger; it defaults to `data/sample.tsv`.

## The statement file

Download the statement from the bank as CSV. The import reads four columns by name, in any order, and ignores the rest:

| Column | Holds |
| --- | --- |
| `Date` | the day the money moved, as the bank writes it: `DD/MM/YYYY` |
| `Description` | the payee |
| `Amount` | money out with a leading minus or in parentheses, money in without: `-45.12`, `(45.12)`, `3,500.00` |
| `Debit` and `Credit` | in place of `Amount`, for a bank that splits it: money out in `Debit`, money in in `Credit`, one of the two per row |
| `Reference` | the bank's reference for the transaction, unique per transaction |

A file saved with a UTF-8 byte order mark imports the same as one without.

## ledger import

    python3 -m ledger --file ledger.tsv import ~/Downloads/statement.csv

Adds each statement row whose reference the ledger does not hold yet, then prints what it did:

    added 4, skipped 0 already imported

`--dry-run` prints the same counts as `would add 4, skip 0 already imported` and leaves the ledger alone.

Import a statement as often as you like: a row that is already in the ledger is skipped, so overlapping statements never double-count.

A statement the import cannot read, such as one missing a column or holding a date it cannot parse, prints the file and line at fault and exits with status 65, leaving the ledger as it was.

## Two commands at once

A command that writes the ledger holds a lock on it while it works. A second command that writes the same ledger meanwhile exits at once with status 75 and `ledger is locked`; run it again once the first finishes.
