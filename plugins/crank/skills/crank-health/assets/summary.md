# Scan summary: <js-ts|python|go|csharp|repo-wide> · <project path>

Saved by the caller as `<run-dir>/summary/<language>--<project path with / as ->.md` (`repo-wide.md` for the repo-wide scan).

Inventory: <n> files, <n> lines (<KLOC>)

## Tools

| tool | version | provenance | state | graded | advisory | metric |
| --- | --- | --- | --- | --- | --- | --- |
| oxlint | 1.81.0 | default config (standby, stood down: eslint graded lint) | ok | 0 | 0 | |
| eslint | 9.30.0 | repo config, repo binary | ok | 12 error, 40 warning | 3 | |
| prettier | 3.6.2 | repo config, ephemeral | ok | 4 files | | 4 / 210 files |
| fallow health | 3.22.0 | default | ok | 9 | | 9 / 412 functions over 15 |
| tsc | 5.9.2 | repo tsconfig | error | | | exit 2, no diagnostics: <first stderr line> |
| knip | 6.34.0 | default | not-available | | | no package.json in ancestry |

State is one of ok; error, carrying stderr's first line; not-available, carrying why and the install hint; skipped, carrying `never imposed` or `nothing to scan`; timeout, for a tool the budget killed. One tool per row, and a state other than ok is what stands in for its findings file.
Metric is `<numerator> / <denominator> <unit> (<percent>)`: `4 / 210 files (1.9%)`, `9 / 412 functions over 15 (2.2%)`, `8240 / 268415 tokens (3.07%)`. Graded and advisory columns follow the rules in `references/grading.md`.

## Findings

Written to `<run-dir>/findings/<project>/<tool>.tsv`, one row per finding:
`file	line	category	tool/rule	severity	graded|advisory	message`
Messages are one line and never quote a secret. Source excerpts are not copied.

## Top rules (graded)

| category | tool/rule | count | files | sample |
| --- | --- | --- | --- | --- |
| lint | eslint/no-unused-vars | 22 | 9 | src/a.ts:12 |

## Notes

Every count in this section must match the TSV it describes; recount before returning.

- <anything the grader must know: a standby stood down, findings dropped as generated, an owner that errored, a tool that refused a partial module graph>
