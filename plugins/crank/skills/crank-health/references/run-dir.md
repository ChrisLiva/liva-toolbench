# The run dir

`scripts/health.py scan` writes everything here, and every later command reads it back. Read
this when you open a run dir, rule on findings, or need a tool run again.

## What the scan writes

| file | holds |
| --- | --- |
| `inventory.md` | scope, projects, lines per language, owned tools, what is on PATH ([inventory.md](inventory.md)) |
| `tools.md` | one row per (project × tool) with version, provenance and state; then every command as it ran |
| `grades.md` | eight letters per project and for the rollup, each with its arithmetic |
| `summary/<language>--<project>.md`, `summary/repo-wide.md` | per tool: state, graded and advisory counts, metric, top rules, notes |
| `findings/<project>/<tool>.tsv` | one row per finding, in the schema below |
| `raw/<project>/` | each tool's output, with source excerpts and secret fields removed |
| `config/`, `lists/` | the skill's default configs and the file lists the recorded commands read |
| `scope.txt`, `footprint.txt` | the in-scope files; the repo's dirty state before any tool ran |
| `results.json` | the machine copy of all of it, with the pinned versions |
| `pr.md`, `new-findings.tsv`, `resolved-findings.tsv`, `base/` | PR mode only: the delta, and the merge-base's own run dir |
| `scratch/` | tool caches; `finish` deletes it |

`<project>` in a path is the project directory with `/` as `-`, `root` for `.`, and `repo` for
the repo-wide tools.

## tools.md

Provenance is one of: `repo config (<file>), repo binary` · `repo config (<file>), ephemeral` ·
`default config, ephemeral` · `default config, ephemeral, standby behind <owner>` ·
`skill config, ephemeral` · `…, system binary` · `skipped: <reason>` · `not available: <hint>`.
An argument you added through `overrides.json` shows as `+ <argument>`.

A tool the repo owns runs its binary against its config; owned but not installed runs the
version the manifest declares, ephemerally, against the repo's config; not owned runs the
default at the latest version, which the scan resolves once and pins for the run.

eslint, biome, oxfmt, mypy, golangci-lint, clang-format, fallow dead-code, stryker, cosmic-ray,
gremlins, Stryker.NET and Mull are **never imposed**: unowned, they read
`skipped: not owned (never imposed)`.

The default lint, format, types and dead-code tool still runs behind an owner as a **standby**.
Once the owner graded the category the standby's findings are gone and its row says
`stood down`. An owner that errored leaves the standby's findings in the grade, and its Notes
line says so: carry that sentence into the plan. An owner whose config excludes every file of
the project stands the standby down too, and the category reads `not assessed`: the repo
chose not to lint or format those files.

State is one of `ok`; `error`, carrying stderr's first line; `not-available`, carrying why and
the install hint; `skipped`, carrying `never imposed`, `nothing to scan`, `needs --deep` or
`deep tool`; `timeout`, for a tool its budget killed. A state other than `ok` has no findings
file.

A Notes line that starts `check:` names a run that finished `ok` and measured less than it
looks: cppcheck aborting on an unknown macro, knip finding no entry point. Resolve each one or
say in the plan what it left unmeasured.

## Findings

One row per finding, tab-separated, no header:

```
file  line  category  tool/rule  severity  verdict  message  flags
```

- `file` is repo-relative. `line` is empty when the finding is about the whole file.
- `category` is one of the eight. `tool/rule` is stable across runs: `oxlint/eslint/no-shadow`,
  `ruff-check/F401`, `knip/unused-export`, `osv-scanner/vulnerable-dependency`.
- `severity` is `critical`, `error`, `warning` or `info`, mapped by [grading.md](grading.md).
- `verdict` is `graded`, `advisory: <reason>` or `dropped: <reason>`. The scan writes the first
  two from the lookups in grading.md. `dropped` is yours: it takes a row out of every count.
- `flags` is what you sort on first: `test`, `snapshot` and `generated` for the path's class,
  `touched` in PR mode, and the numbers behind a message (`score=24`, `confidence=60`,
  `ids=GHSA-…`, `hits=512`).

Messages are one line and never quote a secret. Source excerpts are not copied.

## Ruling on findings

```sh
health.py verdict <run-dir> --dropped "<reason>"  <filters>   # a false positive, a fixture, generated code
health.py verdict <run-dir> --advisory "<reason>" <filters>   # real, and not this repo's to count
health.py verdict <run-dir> --graded              <filters>   # promote: a devDependency that ships
```

Filters, combined with AND, at least one: `--tool`, `--project`, `--category`, `--rule <glob>`,
`--path <glob>`, `--flag`, `--line`, `--message <text>`. It prints how many rows changed and the
new grade line, and rewrites the summaries and `grades.md`. Editing the verdict column of a
findings file by hand works too; run `health.py grade <run-dir>` afterwards.

## Running a tool again

`health.py rerun <run-dir> [--tool <name>]… [--project <dir>]…` runs those rows again at the
run's pinned versions, keeps the verdict of every finding that is still there, and re-grades.
Use it after a fix, after a `timeout` (add `--budget-scale 3`), and after an override.

`<run-dir>/overrides.json` adds arguments to one tool, `{"<tool>": ["<arg>", …]}`, or to one
tool in one project with the key `<tool>@<project dir>`. `<run-dir>` inside an argument expands.
The two that come up:

```json
{"knip": ["--config", "<run-dir>/knip.json"], "cppcheck@src/core": ["--library=boost"]}
```

## Closing the run

`health.py finish <run-dir>` deletes `scratch/`, greps the run dir for secret patterns, lists
every path `git status` shows now and did not before the scan, and lists every file written
since the scan started, ignored paths included. The first two lists must be empty; exit code 1
says one is not. A path in the last list is a cache a tool left (remove it) or an edit made
while the scan ran (yours or another session's: say which in the report).
