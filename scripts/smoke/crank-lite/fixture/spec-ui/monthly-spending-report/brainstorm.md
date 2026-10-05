# Monthly spending report

## Idea

Add a monthly spending report to the household ledger that opens in a browser and makes it clear where the money went.

## Goals and constraints

- Let the user open the selected ledger file as a monthly report in a local browser.
- Show how much money went out and which payees received it.
- Use the existing tab-separated ledger entries, which store a date, payee, and amount in cents.
- Keep the report within the project's Python standard library dependency constraint.

## Chosen shape

Add a `python3 -m ledger report` command that starts the local report and opens it in the browser. The report defaults to the latest calendar month with entries. Previous and next month controls move by calendar month, including months with no entries. The report shows total spending from negative entries, an ordered list of spending totals by payee, incoming positive amounts as a separate total, and all monthly entries. The report uses an ordered list rather than a chart and does not require adding categories to ledger data.

The static UI mock at `.crank/monthly-spending-report/report-mock.html` uses the repository's sample entries to show this shape.

## Key decisions

- Group spending by payee using the existing fields; this avoids adding category data.
- Open the browser from a ledger command; this lets the report read the selected ledger file when launched.
- Default to the latest month with entries and navigate by calendar month; this opens a useful report even when the current month has no entries.
- Count negative amounts as spending and show positive amounts separately as money in; a salary entry should not reduce the spending total.
- Keep the payee breakdown as an ordered list; the list shows exact totals without a chart.

## Open questions

- Which local HTTP server, browser-launch behavior, and port-selection rules should the spec require for `python3 -m ledger report`?
- Which currency should the report use to format the ledger's integer-cent amounts?

## Grounding

- The project uses only Python's standard library | `README.md:3` | brainstorm, 2026-10-05
- The CLI currently accepts a ledger file path and exposes only the `list` command | `ledger/cli.py:10-20` | brainstorm, 2026-10-05
- Each ledger entry stores a date, payee, and integer amount in cents, and the loader reads those three tab-separated fields | `ledger/store.py:8-23` | brainstorm, 2026-10-05
- The sample ledger has four September 2026 entries, three negative amounts, and one positive salary amount | `data/sample.tsv:1-5` | brainstorm, 2026-10-05
- The API module registers an `/entries` route but does not define an HTTP server | `ledger/api.py:8-36` | brainstorm, 2026-10-05
- No browser server or page files appear in the ledger, data, or tests directories | searched `ledger/`, `data/`, and `tests/`, none found | brainstorm, 2026-10-05

## Suggested next step

Continue to the spec phase to define acceptance criteria, local server behavior, browser launch and port rules, and currency formatting.
