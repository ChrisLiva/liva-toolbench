# Brainstorm: monthly spending report page

## The idea

`python3 -m ledger report` writes one self-contained HTML file for one month of the ledger and opens it in the browser. The page shows where that month's money went, grouped by payee.

Done means the user runs one command, sees each payee's share of the month's spending with income and net beside it, and needs nothing beyond the ledger file and the Python standard library.

## Goals and constraints

- Standard library only (`README.md:3`). The page draws its bars with CSS widths, loads no CDN, no web font, and no script, and works offline.
- The page reads entries through the existing `load_entries()`. The ledger file format does not change.
- Every payee is HTML-escaped. The sample payees already carry `&` and `"`.
- One month per run. No month picker, no previous-month comparison, no filters.
- The breakdown covers outflows only. Positive entries are income and appear only in the header.

## Chosen shape

A new `ledger/report.py` holds a pure summary function over `load_entries()` output and a separate HTML renderer. `ledger/cli.py` gets a `report` subcommand beside `list`, and `ledger/api.py` stays untouched.

```
python3 -m ledger [--file data/sample.tsv] report [--month YYYY-MM] [--out PATH] [--no-open]

load_entries(file)
  -> filter entries where date[:7] == month   (default: latest month in the file)
  -> income = sum of positive amounts; spent = sum of negative amounts, negated; net = income - spent
  -> group outflows by payee, sort by spend descending
  -> top 8 payees keep their own row; the rest roll into "Other (N payees)" when more than 8 exist
  -> render the page: header, then one bar row per payee (variant A with C's header)
  -> write report-YYYY-MM.html (or --out), print the path, open it with webbrowser unless --no-open
```

The page follows mock variant A. Under a slim `Ledger` header and the month label (`September 2026`), the header reads as C's equation, Income − Spent = Net. Below it, one row per payee shows the name on the left, a bar scaled to the largest payee, and the amount with its percent of spent on the right. The gray "Other" row sits under a hairline.

## Key decisions

Each decision names the option it beat.

1. **Delivery:** a `report` command writes a static HTML file. It beat a `serve` command on `http.server`, because the route table in `ledger/api.py` has no server behind it and a server adds a port and new code for no gain here.
2. **Grouping:** by payee. It beat a `data/categories.tsv` mapping and a fourth ledger column, because payee needs no data change and the fourth column breaks the three-field unpack at `ledger/store.py:21`. The user owns the question of whether the real ledger's payee count outgrows this, and the first revisit is the mapping file.
3. **Month scope:** one month per run, `--month YYYY-MM`, defaulting to the latest month in the file. It beat one file with a dropdown for every month, which needs JavaScript.
4. **Income and refunds:** positive entries all count as income, and the breakdown covers outflows only. It beat netting a positive entry against the same payee's spending, because sign-only data cannot tell a refund from a salary.
5. **Output:** writes `report-YYYY-MM.html` in the current directory, `--out PATH` overrides, and `webbrowser.open` opens it unless `--no-open` is passed. `report-*.html` goes into `.gitignore`. It beat a temp file and stdout.
6. **Payee cutoff:** a constant of 8, with "Other (N payees)" shown only when more than 8 payees exist. It beat a `--top N` flag, which adds a knob nobody asked for.
7. **Empty month:** the command exits with code 2 and a stderr line such as `no entries for 2026-10 (months in file: 2026-09)`, and writes no file. It beat an empty page. A month with entries but no outflows still renders the header and a "No spending" line.
8. **Defaults taken without a fork:** a month is `date[:7]`; percents show one decimal; ties in spend sort by payee name ascending; a malformed row still raises `ValueError` from `store.py:21`, as `list` does today; the existing top-level `--file` option (`cli.py:12`) selects the ledger file; tests cover the summary (totals, top 8 rollup, month filter, default month) and the escaping of `&` and `"`.
9. **Look:** Prototype: variant A (bar list) wins; the user took C's equation header (Income − Spent = Net) in place of A's plain three-figure row and left nothing out of A | `.crank/monthly-spending-report/prototype/variant-a.html` | stood in for the report page, with no host page. The other variants (`variant-b.html` donut, `variant-c.html` stacked bar, `variant-d.html` table) stay on disk. B lost mainly because 9 slices exceed the 6 a donut carries legibly.

## Open questions

None. Every decision the interview surfaced has one settled answer.

## Grounding

- Nothing in the repo reads `ROUTES` or starts an HTTP server | searched `ledger`, `tests`, `README.md`, `docs` for `ledger.api|http.server|ROUTES|serve`, none found beyond `ledger/api.py:8`, `ledger/api.py:28`, and the docstring at `ledger/__init__.py:1` | brainstorm, 2026-10-05
- `Entry` has exactly three fields: `date`, `payee`, `amount_cents` | `ledger/store.py:8-12` | brainstorm, 2026-10-05
- `load_entries` unpacks exactly three tab-separated fields per line | `ledger/store.py:21` | brainstorm, 2026-10-05
- The only subcommand is `list`, and `--file` is a top-level option defaulting to `data/sample.tsv` | `ledger/cli.py:12-14` | brainstorm, 2026-10-05
- `list` formats amounts as cents divided by 100 with two decimals | `ledger/cli.py:19` | brainstorm, 2026-10-05
- The sample has four rows, all dated 2026-09, with one positive amount (Salary, 350000) | `data/sample.tsv:2-5` | brainstorm, 2026-10-05
- The sample payees include `&` and `"` | `data/sample.tsv:3-4` | brainstorm, 2026-10-05
- The project is standard library only | `README.md:3` | brainstorm, 2026-10-05
- `.gitignore` lists `.crank/` and `__pycache__/` but no report output | `.gitignore:1-2` | brainstorm, 2026-10-05
- The mock fixture's September totals are Income $3,500.00, Spent $2,471.42, Net $1,028.58, over 12 payees | `.crank/monthly-spending-report/prototype/variant-a.html:148-155` | brainstorm, 2026-10-05

## Suggested next step

Continue to the spec phase in this session, or in a fresh one: `/crank-lite spec .crank/monthly-spending-report/brainstorm.md`. The spec turns decisions 1 to 9 into numbered acceptance criteria, and variant A's behaviors become criteria through the `Prototype:` line in decision 9.
