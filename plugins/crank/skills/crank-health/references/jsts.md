# JS/TS analyzers

What the scan runs for a JS/TS project and how to read each tool's rows. The commands themselves,
with their pinned versions and cwd, are in `<run-dir>/tools.md` → Commands.

| category | default | repo-owned only (never imposed) |
| --- | --- | --- |
| lint | oxlint | eslint, biome lint |
| lint (complementary, advisory) | react-doctor, when `react` is a dependency | |
| format | prettier | biome format, oxfmt |
| types | tsc | |
| dead code | knip | fallow dead-code |
| complexity | fallow health | |
| test quality (deep) | | stryker |

Ownership = a config file in the project or an ancestor, or the package name in any of
`dependencies`, `devDependencies`, `optionalDependencies`, `peerDependencies`. A `scripts` entry
never decides. `tsc` alone is project-local: it is owned by a `tsconfig.json` in the project
itself.

Three file lists feed the tools, each the project's in-scope files of those extensions:

- `<files>` is `.ts .tsx .mts .cts .js .jsx .mjs .cjs`.
- `<format-files>` is `<files>` plus `.css .scss .less .json .jsonc .graphql .gql .md .mdx .yaml .yml .html .vue`,
  minus lockfiles. A file the repo's formatter is configured to skip belongs in neither half of
  the ratio, so each format row's denominator is the files its formatter read, not the list's
  length. The format letter is a ratio over files rather than over KLOC, so the wider list moves
  no density band.
- `<lint-files>` is `<files>` plus `.css .graphql .gql`, and only `biome lint` takes it.

## Reading the rows

**oxlint** (lint). On the skill's default config (`correctness` as error, `suspicious` and `perf`
as warn) only `correctness` rules grade; the rest are advisory. A repo that owns an oxlint
config grades everything it selected. Rule ids read `oxlint/<plugin>/<rule>`.

**eslint** (lint, owned only). A repo with only a legacy `.eslintrc*` and no install reads
`not available`: ESLint 9+ no longer reads it. The Notes line gives how many of the project's
files eslint reported on; the rest are files its own config ignores.

**biome** (lint and format, owned only). The format metric is the files carrying a `format`
diagnostic over the files Biome read: its config's `files.includes` decides that set, and it
drops `.scss`, `.less`, `.md`, `.yaml` and `.html` without a word. Biome's recommended set lints
`.css` and `.graphql` on their own rules, so its lint denominator is the js-ts KLOC plus the
`lint assets` lines; when oxlint graded lint instead, the denominator drops back to js-ts KLOC
alone. A project whose every file the Biome config excludes reads
`skipped: nothing to scan`, and lint and format read `not assessed` there: usually generated
code the repo chose not to lint.

**prettier** (format). Format grades even on the default config (the measure is "formatted at
all"). Files a `.prettierignore` excludes leave the denominator, and the Notes line counts them.
A standby prettier behind Biome or oxfmt measures a style the repo never adopted: once the owner
graded format its rows are gone, and when it graded because the owner failed, say in the plan
whose style the number reflects.

**oxfmt** (format, owned only). Its config's `ignorePatterns` and the project's
`.prettierignore` drop files even when they are named, and a file it cannot parse leaves the
denominator and shows in Notes.

**tsc** (types). A project with a `tsconfig.json` is checked against it. A project without one
is checked on a scratch tsconfig (`strict`, `skipLibCheck`, `moduleResolution: bundler`) over its
TypeScript files only; a project of plain JavaScript reads `skipped`, because type-checking code
that never opted in is imposing. Advisory, not graded, when the project has no `node_modules`:
TS2307, TS2503, TS2580, TS2591, TS2593, TS2688, TS2792, TS7016, and any message saying
`npm i --save-dev @types/…`. With no `node_modules` every imported type is unchecked, so a clean
row there is weak evidence: say so beside the letter. Notes names other `tsconfig.*.json` files
the run did not check.

**knip** (dead code). knip's unit is the workspace, so it runs once from the highest ancestor
with `workspaces`, a `pnpm-workspace.yaml` or a knip config, and each project keeps the rows in
its own files. Unused dependencies, unlisted dependencies and unresolved imports are info and
never grade. Before you leave an `unused-file` or `unused-export` row graded, read `exports`,
`main`, `bin`, the test globs and the examples dir: a library's public modules, its tests and
its examples are the usual false positives, and they are advisory. A `check:` line means knip
called a fifth or more of the project's files unused, which is a missing entry point rather
than dead code (a CLI, a bundler plugin's entries, a test setup file): write the entries to
`<run-dir>/knip.json`, point knip at it through `overrides.json`, and rerun
([run-dir.md](run-dir.md)). At half or more, the scan has already marked the rows
`advisory: no entry point reaches this project`.

**fallow** (dead code when owned; complexity by default). Dead code runs once over the repo and
is filtered per project. The complexity metric is functions whose *cognitive* complexity is over
15 / functions counted, both filtered to the project's files. CRAP, cyclomatic and unit-size
rows are advisory.

**react-doctor** (lint, complementary). Runs when `react` is a declared dependency; every row is
advisory.

## Deep

**stryker** (test quality, `--deep`, owned and installed only). Write `<scratch>/stryker.config.mjs` that imports the repo's config and overrides `reporters: ['json']`, `jsonReporter: { fileName: '<scratch>/mutation.json' }`, `tempDirName: '<scratch>/stryker-tmp'`, `cleanTempDir: 'always'`, `incremental: false`, `allowConsoleColors: false`, `allowEmpty: true`, `fileLogLevel: 'off'`; in PR mode set `mutate` to the changed files. Then `<node_modules/.bin>/stryker run <scratch>/stryker.config.mjs` from the repo root. Budget 15 minutes. Score = killed / (killed + survived + no-coverage + timeout).

## Gotchas

- knip and fallow both name the same export: one symbol is one dead-code finding.
- `dist/`, `build/`, `coverage/`, `*.gen.*`, `gen/` and any glob the repo's Biome `files.includes` `!`-entries or fallow `ignorePatterns` exclude are generated: never a task, even when a tool reports them.
- An ephemeral eslint crashes on plugins only a real install provides. Its row reads `error`, the oxlint standby keeps its findings, and the plan says so.
