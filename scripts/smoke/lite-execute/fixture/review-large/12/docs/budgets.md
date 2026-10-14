# Categories and budgets

Run every command from the repository root. `--file` goes before the command and names the ledger; it defaults to `data/sample.tsv`.

## Rules

`ledger categorize` assigns categories with the rules in `rules.tsv` beside the ledger. Each line holds a payee pattern, then whitespace, then the category it assigns:

    tesco          Groceries
    amazon         Shopping
    smith, jones   Rent

A pattern matches any payee that contains it, ignoring case, so `tesco` matches `TESCO STORES 3021`. Lines starting with `#` are comments.

## ledger categorize

    python3 -m ledger --file ledger.tsv categorize
    python3 -m ledger --file ledger.tsv categorize --rules ~/rules.tsv

Gives each entry with no category the category of the first rule whose pattern its payee contains, saves the ledger, and prints how many entries it categorized. An entry that already has a category keeps it, so a category you set by hand survives the next run.

`ledger list --uncategorized` prints the entries no rule matched yet.

## Budgets

`budgets.tsv` beside the ledger holds one monthly limit per category: the category, a tab, then the limit in currency units.

    Groceries	400.00
    Dining	120.00
    Rent	1200

## ledger report

    python3 -m ledger --file ledger.tsv report --month 2026-09

Prints each budgeted category's spending that month against its limit, and marks a category past its limit with `OVER`:

    Groceries        412.30 of       400.00  OVER
    Dining            84.50 of       120.00
    Rent           1,200.00 of     1,200.00

A refund in a category reduces its spending. `--budgets FILE` reads another budgets file.

## The report route

`GET /report?month=2026-09` returns the same report as JSON, amounts in integer cents:

    {"month": "2026-09", "budgets": [{"category": "Groceries", "spent_cents": 41230, "limit_cents": 40000, "over": true}]}
