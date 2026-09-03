# Inventory and detection

Step 1 writes `<run-dir>/inventory.md`: what code is in scope, how it splits into projects, how
many lines of each language each project holds, and which analyzers each project already owns.
Every later step reads it.

## What is in scope

Tracked files plus untracked-unignored ones:

```sh
git -C <repo> ls-files -z --cached --others --exclude-standard | tr '\0' '\n'
```

Drop `node_modules/`, `vendor/`, `dist/`, `build/`, `bin/`, `obj/`, `.venv/`, `venv/`,
`__pycache__/`, `coverage/` and every hidden directory, then add `.github/` back: its workflows
are scanned. Hold the result in a file under the run dir and pass it to tools as a shell array.
An unquoted variable hands ruff one joined filename, which it reports as an `io-error` with
exit 0, and zsh does not word-split an unquoted variable at all.

## Projects

A project is a directory holding `package.json`, `pyproject.toml`, `go.mod`, `*.csproj` or
`*.sln`. Each in-scope file belongs to the project whose directory is the longest prefix of its
path. A candidate that ends up holding no source of its own is a workspace shell: say so and scan
nothing there. A monorepo is N projects plus the rollup.

## Lines

Per project, count each language's in-scope files with `wc -l`, blank and comment lines included:
js-ts (`.ts .tsx .mts .cts .js .jsx .mjs .cjs`), python (`.py .pyi`), csharp (`.cs`), go (`.go`).
KLOC is that count over 1000. It is the denominator for types, dead code and complexity, so print
the file count and the line count beside it and let the reader redo the division.

Count `.css` and `.graphql`/`.gql` on a separate `lint assets` line. They are not a language: they
dispatch no scan subagent and never enter a language KLOC. Only `biome lint` reads them, and only
lint's denominator grows by them ([grading.md](grading.md)).

## Owned tools

Read each project's manifests and configs and record what it owns, by the ownership rule in the
reference for that language: [jsts.md](jsts.md), [python.md](python.md), [go.md](go.md),
[csharp.md](csharp.md). Each of those four states its own rule and is the only place that does.
Each rule covers ancestors, so a config above the project still owns.

Read a manifest, never grep it. `"eslint"` sits in `scripts` far more often than in any dependency
block, and a `scripts` entry never decides ownership; a grep that cannot tell the two apart
imposes a tool the repo never chose.

Record what is on PATH too, with the install hint for each one missing: `uv`, `go` (1.25+),
`dotnet` (10+), `gitleaks`, `opengrep`, `osv-scanner`. A missing toolchain is what a whole
language's `not assessed (reason)` will cite, so the reason has to be readable here.

## Snapshot the footprint

Before any tool runs, record the repo's dirty state:

```sh
git -C <repo> status --porcelain --untracked-files=all --ignored=no | sort > <run-dir>/footprint.txt
```

Step 7 runs that command again and compares. A path in the second listing and not the first is
something the scan left behind: remove it, or gitignore it when the repo's own tool wrote it,
before you report.

## The shape to write

```
repo: <abs path> · head: <short sha> · dirty: <n> paths

## project <dir>
  manifests: package.json
  js-ts      42 files   6210 lines (6.2 KLOC)
  lint assets  css 6 files 900 lines (0.9 KLOC); graphql 2 files 40 lines (0.0 KLOC)
  owned: tsc (tsconfig.json), biome (biome.json), prettier (devDependencies)
  unowned: eslint, oxlint, knip, fallow, stryker
  node_modules: present

## project <dir>
  workspace shell: no source of its own

## repo-wide
  on PATH: gitleaks 8.30.1, osv-scanner 2.5.1
  missing: opengrep (brew install opengrep)
  workflows: 3 files
  configs: .gitleaks.toml, zizmor.yml
  snapshots: testdata/, __snapshots__/
  lockfiles: package-lock.json, uv.lock
  unassessed: md:84 yaml:14 sh:2
```

`snapshots` is the one step 3 leans on: a fixture or a captured snapshot under scan is graded
differently from hand-written code, so list every directory whose name says so (`captured`,
`golden`, `__snapshots__`, `fixtures`, `testdata`, `snapshots`).
