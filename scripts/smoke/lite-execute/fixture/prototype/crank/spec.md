# Ledger HTML report

## Problem

The ledger reads into `Entry` values, but there is no way to look at it. Users want one HTML page they can open from disk that shows where the money went.

## Proposed solution

A `ledger.report` module renders one self-contained HTML page from the entries, and `python3 -m ledger.report <csv> <out.html>` writes it.

## Acceptance criteria

1. `python3 -m ledger.report data/ledger.csv out.html` writes one self-contained HTML file: inline CSS and JS, no external requests.
2. The page shows each account's total.
3. The page lists the entries grouped by month, newest month first.
4. A memo filter input narrows the visible entry rows, case-insensitively, without a reload.

## Key technical decisions

- Rendering uses the standard library only (f-strings and `html.escape`), no template engine.
- Totals and month grouping are pure functions over `Entry` lists, tested on their own.
- Prototype: B (Sidebar summary) wins; took A's sticky month headers; left out B's per-account sparklines; .crank/ledger-report/prototype/variant-b.html; the report page.

## Testing and validation

One journey test renders the fixture ledger and asserts the totals, the month order, and the filter input. The CLI gets one test that writes to a temp file.

## Out of scope

- Charts of any kind.
- Editing entries from the page.
