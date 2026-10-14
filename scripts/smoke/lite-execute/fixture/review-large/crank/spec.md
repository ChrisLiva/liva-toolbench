# Spec: Bank import and budgets

Users download statements from their bank as CSV files and want each month's spending against a budget per category. Add statement import, payee rules that assign categories, and a monthly budget report, reachable from the CLI and the API.

## Acceptance criteria

1. `parse_amount` reads every amount shape the bank's statements use, as exact integer cents: a leading minus or parentheses for money out, a currency sign, thousands separators, and one or two decimal places.
2. A save that fails partway leaves the previous ledger file intact at its path, and a reader never sees a partly written ledger.
3. While one command writes a ledger, a second command that writes the same ledger exits at once with status 75 and `ledger is locked` on stderr, and the ledger holds what the first command wrote.
4. `ledger import STATEMENT` adds each statement row to the ledger once: importing the same statement again adds nothing, including after other commands have rewritten the ledger.
5. The bank writes statement dates as `DD/MM/YYYY`, and they land in the ledger as ISO dates.
6. `ledger list` shows each entry's category, and `ledger list --uncategorized` shows only the entries with none.
7. `ledger categorize` gives each uncategorized entry the category of the first rule in `rules.tsv`, in file order, whose pattern appears in its payee, ignoring case. An entry that already has a category keeps it.
8. `ledger report --month YYYY-MM` prints, for each category in `budgets.tsv`, the month's spending in it against its limit, and marks each category whose spending exceeds its limit with `OVER`. A refund in a category reduces its spending.
9. `GET /report?month=YYYY-MM` returns the same report as JSON, amounts in integer cents.
10. `docs/import.md` and `docs/budgets.md` document the commands and the statement, rules, and budgets file formats.
