# JS/TS analyzers

Run from the repo root unless a row says otherwise. Ephemeral form is `npx --yes <pkg>@latest`; when the binary name differs from the package: `npx --yes --package <pkg>@latest -- <bin>`. A repo-owned tool runs as `<nearest node_modules/.bin>/<bin>` with the repo's config. Record the version each tool prints.

Three file lists, each the project's tracked files of those extensions from the inventory, batched at ~200 per invocation:

- `<files>` is `.ts .tsx .mts .cts .js .jsx .mjs .cjs`. Every row takes it but the two named below.
- `<format-files>` is `<files>` plus `.css .scss .less .json .jsonc .graphql .gql .md .mdx .yaml .yml .html .vue`, minus lockfiles, minus what the repo's own `.prettierignore` or Biome `files.includes` `!`-entries exclude: a file its formatter is configured to skip belongs in neither half of the ratio. The two format rows take it, and the format letter is a ratio over files rather than over KLOC, so widening it moves no density band.
- `<lint-files>` is `<files>` plus `.css .graphql .gql`, and only the `biome lint` row takes it. Biome lints `.json` as well, but the largest JSON in a repo is usually its lockfile and generated data earns no lint task, so JSON stays out of the list and out of the count.

| category | default | repo-owned only (never imposed) |
| --- | --- | --- |
| lint | oxlint | eslint, biome lint, react-doctor (when `react` is a dependency) |
| format | prettier | biome format |
| types | tsc (needs a `tsconfig.json` in the project itself) | |
| dead code | knip | fallow dead-code |
| complexity | fallow health | |
| test quality (deep) | | stryker |

Ownership = a config file in the project or an ancestor, or the package name in any of `dependencies`, `devDependencies`, `optionalDependencies`, `peerDependencies`. A `scripts` entry never decides.

## Commands

**oxlint** (lint). Exit 1 = findings. Empty stdout with exit 1 = it crashed.
```sh
oxlint --format sarif --no-error-on-unmatched-pattern <files>
# no repo config: add
--config <scratch>/oxlintrc.json --disable-nested-config
```
Default config to write: `{"plugins":["typescript","unicorn","oxc"],"categories":{"correctness":"error","suspicious":"warn","perf":"warn"}}`. On the default config only `correctness` rules grade; the rest are advisory.

**eslint** (lint, owned only). Exit 1 = findings, exit 2 = could not run (no JSON). A repo with only a legacy `.eslintrc*` and no install: not available, "ESLint 9+ no longer reads it". Never `--fix` or `--cache` during the scan.
```sh
eslint --format json --no-color --no-warn-ignored <files>
```

**biome** (lint and format, owned only). cwd must be the directory of the highest `biome.json[c]` in the ancestry: Biome refuses a config below its cwd as "nested". JSON is on stdout after other lines: take the first line starting with `{` that parses and has `diagnostics`. Never `--write`, `--fix`, `--suppress`.
```sh
biome lint   --reporter=json --max-diagnostics=none --colors=off --no-errors-on-unmatched --vcs-enabled=true --vcs-client-kind=git --vcs-use-ignore-file=true --vcs-root=<repo> <lint-files>
biome format --reporter=json --max-diagnostics=none --colors=off --no-errors-on-unmatched --vcs-enabled=true --vcs-client-kind=git --vcs-use-ignore-file=true --vcs-root=<repo> <format-files>
```
Exit 1 = findings, 0 = clean. `summary.changed` counts files written, so a check run always reports 0: the format metric is the count of distinct `location.path` among the `diagnostics` rows whose `category` is `format`. `summary.errors` is not that count, because a `parse` row lands in it too, and a `parse` row is a tool error on that file rather than a format failure. Diagnostic paths are relative to cwd, so the cwd rule above also decides how findings anchor. The denominator is `summary.unchanged`, the files Biome parsed, never the length of the list you handed it: it formats `.css`, `.json[c]` and `.graphql` but drops `.scss`, `.less`, `.md`, `.yaml` and `.html` without counting them in `skipped` either, and in `.vue` and `.svelte` it reads the `<script>` block alone.

Biome's recommended set lints `.css` and `.graphql` on their own rules (`noUnknownProperty`, `noUnknownUnit`, `noEmptyBlock`, `noDuplicateFields`), so its lint denominator is the js-ts KLOC plus the `css` and `graphql` line counts `inventory.md` records on the project's `lint assets` row. When oxlint graded lint instead, because biome errored, the denominator drops back to js-ts KLOC alone: oxlint never read those files.

**prettier** (format). Prints one path per line for each file that would change. Exit 1 = some would change, 2 = failure. `--check` and `--list-different` are mutually exclusive.
```sh
prettier --list-different --ignore-unknown <format-files>
# no repo config: add
--no-config --no-editorconfig
```
Format grades even on the default config (the measure is "formatted at all"). Prettier parses every extension in `<format-files>` but `.svelte`, which needs a plugin it does not ship; `--ignore-unknown` drops that one without a word, so leave it out of the denominator.

**tsc** (types). Always name the project explicitly, or a monorepo grabs another package's tsconfig. `--incremental false` stops `.tsbuildinfo` being written.
```sh
tsc --noEmit --pretty false --incremental false --project <project-dir>
```
No `tsconfig.json` in the project: write `<scratch>/tsconfig.json` with `{"compilerOptions":{"strict":true,"noEmit":true,"skipLibCheck":true,"module":"esnext","moduleResolution":"bundler","target":"es2022","jsx":"preserve"},"files":[<absolute paths>]}` and point `--project` at it. Advisory, not graded, when the project has no `node_modules`: TS2307, TS2503, TS2580, TS2591, TS2593, TS2688, TS2792, TS7016, and any message saying `npm i --save-dev @types/…`. Exit non-zero with zero diagnostics parsed = error.

**knip** (dead code). No file list: knip's cwd is the analysis unit. cwd = the highest ancestor with `workspaces` in `package.json` or a `pnpm-workspace.yaml` or a knip config; else the project's `package.json` dir. Unused dependencies are info and never grade.
```sh
knip --reporter json --no-config-hints --no-progress --no-exit-code
```
Before grading `unused-file` or unused-export rows, read `exports`, `main`, `bin`, the test globs and the examples dir: a library's public modules, its tests and its examples are the usual false positives, and they are advisory. A project knip found no entry point for gets its rows advisory with the note `no entry point reaches this project`.

**fallow** (dead code when owned; complexity by default). cwd = repo root (its config resolves above `--root`). Exit 1 = findings; only empty stdout is failure. `--no-cache` is the zero-footprint flag; never `fix`, `--save-snapshot`, `--save-baseline`.
```sh
fallow dead-code --format json --no-cache -q
fallow health    --format json --no-cache -q --root <project-dir> --complexity --file-scores --max-cognitive 15
```
Complexity metric = functions whose *cognitive* complexity row is over 15 / functions counted, both filtered to the project's inventory (fallow walks from `--root`, which is the whole repo for a root project). CRAP, cyclomatic and unit-size rows are advisory. Leave out `--hotspots`, `--churn` and `--ownership`: they read git with a relative time window.

**react-doctor** (lint, complementary, advisory). cwd = scratch. Only when `react` is a declared dependency.
```sh
react-doctor <abs project-dir> --json --no-telemetry --no-supply-chain --no-dead-code --blocking none --output-dir <scratch>/react-doctor
```

**stryker** (test quality, `--deep`, owned and installed only). Write `<scratch>/stryker.config.mjs` that imports the repo's config and overrides `reporters: ['json']`, `jsonReporter: { fileName: '<scratch>/mutation.json' }`, `tempDirName: '<scratch>/stryker-tmp'`, `cleanTempDir: 'always'`, `incremental: false`, `allowConsoleColors: false`, `allowEmpty: true`, `fileLogLevel: 'off'`; in PR mode set `mutate` to the changed files. Then `<node_modules/.bin>/stryker run <scratch>/stryker.config.mjs` from the repo root. Budget 15 minutes. Score = killed / (killed + survived + no-coverage + timeout).

## Gotchas

- A `tsconfig.json` is project-local. Every other config inherits from ancestors.
- oxlint stands in as a standby behind an owned eslint or biome: run both, and drop oxlint's findings when the owner graded lint. Keep them, and say so, when the owner errored (an ephemeral eslint crashes on plugins only a real install provides).
- knip and fallow both name the same export: one symbol is one dead-code finding.
- `dist/`, `build/`, `coverage/`, `*.gen.*`, `gen/` and any glob the repo's Biome `files.includes` `!`-entries or fallow `ignorePatterns` exclude are generated: never a task, even when a tool reports them.
