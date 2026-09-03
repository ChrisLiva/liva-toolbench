# Grading

Read this when turning tool findings into letters. Eight categories, fixed order (also the
remediation order): security, types, dead code, complexity, duplication, lint, format, test quality.
A category no tool measured is `not assessed (reason)`, never A. All eight appear in every report.

## Graded vs advisory

Only graded findings count toward a letter. A finding is advisory when:

- the tool ran on the skill's default config and the rule is style or pedantic (correctness-class
  rules grade; `S`, `B`, `E`, `F`, `security`, `correctness`, `suspicious` groups grade, `style`,
  `pedantic`, `nursery` do not);
- it is a type diagnostic in a JS/TS project with no `node_modules` (a missing `@types/*` is an
  install that never ran, not a code defect);
- it is dead code reported by knip/fallow in a package no entry point reaches, or an unused *export*
  in a library (its consumers are outside the repo);
- vulture confidence < 90%;
- bandit severity < HIGH and confidence < HIGH under the default config;
- a vulnerable dependency has no fixed version, is reachable only from devDependencies, or
  govulncheck says the vulnerable symbol is never called;
- a formatter disagreement comes from a repo that formats in CI with an older formatter version.

A repo that owns a tool's config grades every finding that config selected, and a finding that
config waived (a gitleaks allowlist, a zizmor or osv-scanner ignore, a `# noqa`) is the repo's
decision: it is not graded, and the security row prints `n waived by <file>` so the reader can see
the allowlist working. Read the allowlist: an entry naming fixtures or tests is fine; one naming a
source path is a task ("remove the waiver on `src/x` or the finding it hides").

## Severity map

Tool severities land on four levels: critical 5, error 5, warning 1, info 0.2.

- secrets (gitleaks, gosec G101, bandit B105 to B107 at high confidence): critical
- type checker errors (tsc, ty, pyright, mypy, staticcheck `compile`, CS diagnostics): error;
  their warnings and notes: info
- lint: the tool's own error/warning where it has one (eslint 2/1, biome, oxlint correctness =
  error, suspicious and perf = warning); ruff `E9` and syntax = error, every other ruff rule =
  warning; staticcheck non-compile, go vet, golangci-lint, CA rules = warning; aislop = warning
- dead code: warning (knip unused dependencies and vulture below 90%: info)
- security: bandit and gosec HIGH = error, MEDIUM = warning, LOW = info; zizmor High = error except
  `unpinned-uses` and `unpinned-images` = warning, Medium = warning, Low = info; osv-scanner
  advisory severity HIGH or CRITICAL = error, else warning
- format and complexity and duplication are ratios, not weighted

## One defect, one finding

Two tools naming the same place in the same category is one defect: keep the row from the default
tool for that category (the first in the reference's table), mark the others
`advisory: duplicate of <tool>/<rule>`. gitleaks outranks gosec G101 and aislop on a secret;
staticcheck outranks go vet; ruff F401 and vulture on one import is one dead-code finding.
Across categories the rows stay separate and link to each other, so one place can be one task.

## Shapes and bands

Severity weights: critical 5, error 5, warning 1, info 0.2.

| category     | shape                              | A     | B    | C    | D    | else |
| ------------ | ---------------------------------- | ----- | ---- | ---- | ---- | ---- |
| lint         | weighted findings / KLOC           | ≤ 1   | ≤ 5  | ≤ 15 | ≤ 40 | F    |
| types        | weighted **errors** / KLOC         | 0     | ≤ 1  | ≤ 5  | ≤ 15 | F    |
| dead code    | weighted findings / KLOC, one per symbol | ≤ 0.5 | ≤ 2 | ≤ 5 | ≤ 10 | F |
| complexity   | % functions with cognitive complexity > 15 | ≤ 2 | ≤ 5 | ≤ 10 | ≤ 20 | F |
| duplication  | jscpd duplicated-token %           | ≤ 3   | ≤ 5  | ≤ 10 | ≤ 20 | F    |
| format       | % files failing the formatter      | ≤ 1   | ≤ 10 | ≤ 30 | ≤ 60 | F    |
| test quality | mutation score % (higher better)   | ≥ 80  | ≥ 65 | ≥ 50 | ≥ 35 | F    |
| security     | absolute counts, never normalized  | zero findings of any kind | ≤ 2 warning and ≤ 10 info | more | any error (high) | any critical → F |

KLOC is the assessed lines of that language in that project (`scripts/detect.sh` prints it).
Lint is the one density whose denominator follows the tool rather than the language: it is the
KLOC the tool that graded lint actually read. Only biome reads past the language's own files,
adding the `css` and `graphql` lines `detect.sh` prints on the project's `lint assets` row; every
other lint tool reads the language files alone, so its denominator is the language KLOC unchanged.
Types, dead code and complexity always divide by the language KLOC, so an asset line never
flatters them.
A density category with findings and zero KLOC is F; with no graded findings it is A.
A secret is always critical and never advisory: one leaked credential is F in a million-line repo.
Security A is reserved for nothing found at all; advisory-only lands at B.

Print the arithmetic beside every letter so the reader can redo it:
`lint C (34.5 weighted / 2.3 KLOC = 15.0)`.

## Calibration you should expect

Measured on zustand, requests, datasette and crank-health with these exact bands:

- A repo that lints in CI sits near 0 (A). One that does not lands at 5 to 8 (C). F is eight
  errors per KLOC, which nothing well-kept reaches.
- Untyped Python under ty or pyright measures 25 to 75 errors/KLOC (F). That is the honest reading;
  say "no type safety" rather than bending the band.
- knip and fallow on a library with no configured entry points report the public modules, tests and
  examples as unused. Read the package's `exports`/`main`/`bin` and the test globs before grading
  dead code; findings there are advisory.
- Format is bimodal: 0 to 2% (formats in CI) or 30%+ (does not, or an older formatter).
- Complexity discriminates cleanly: well-kept repos measure 0.1% to 4%.
- Duplication: a test-heavy repo can read F on its test suite alone. Report where the clones sit.
- Security D on every real repo came from one of: zizmor `unpinned-uses` on workflows that do not
  hash-pin actions (that one is a warning, not high), bandit B324 weak hash and B602 `shell=True`
  at high confidence, or one zizmor `cache-poisoning` at low confidence. Name the finding that
  holds the letter.
