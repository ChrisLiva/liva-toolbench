# Inventory and detection

The scan writes `<run-dir>/inventory.md`: what code is in scope, how it splits into projects, how
many lines of each language each project holds, and which analyzers each project already owns.
These are the rules it applies, so you can tell when one of them misreads this repo.

## What is in scope

Tracked files plus untracked-unignored ones, minus `node_modules/`, `vendor/`, `dist/`,
`build/`, `bin/`, `obj/`, `.venv/`, `venv/`, `__pycache__/`, `coverage/` and every hidden
directory. `.github/`, `.gitea/` and `.forgejo/` come back in: their workflows are scanned. The
list is `<run-dir>/scope.txt`, and a finding outside it is dropped with a count.

The rule drops `vendor/` by name only. A repo that vendors under another name (`deps_src/`,
`third_party/`) has that code in scope: scope the run with `--project` and say so in the plan.

## Projects

A project is a directory holding `package.json`, `pyproject.toml`, `go.mod`, `*.csproj`, `*.sln`,
`*.vcxproj`, `configure.ac`, `BUILD.bazel` or `BUILD`, or a `CMakeLists.txt` or `meson.build` that
calls `project(`: a subdirectory's list file without that call belongs to the enclosing project. A
bare `Makefile` counts only with C or C++ sources beside it. Each in-scope file belongs to the
project whose directory is the longest prefix of its path, and the repo root takes what no other
project holds. A candidate that ends up holding no source of its own is a workspace shell: nothing
is scanned there. A monorepo is N projects plus the rollup.

## Lines

Per project, each language's in-scope files counted as `wc -l` counts them, blank and comment
lines included: js-ts (`.ts .tsx .mts .cts .js .jsx .mjs .cjs`), python (`.py .pyi`), csharp
(`.cs`), go (`.go`), c-cpp (`.c .h .cpp .cc .cxx .c++ .hpp .hh .hxx .h++`).
KLOC is that count over 1000. It is the denominator for types, dead code and complexity, so the
file count and the line count print beside it.

`.css` and `.graphql`/`.gql` count on a separate `lint assets` line. They are not a language: they
never enter a language KLOC. Only `biome lint` reads them, and only lint's denominator grows by
them ([grading.md](grading.md)).

A language whose every file in a project sits under a snapshot directory prints
`likely fixtures`, and gets no scan while the project holds another language: one sample file
per language under `tests/fixtures/` is not a codebase.

## Owned tools

`owned:` names each tool the project owns and the evidence, by the ownership rule in the reference
for that language: [jsts.md](jsts.md), [python.md](python.md), [go.md](go.md),
[csharp.md](csharp.md), [cpp.md](cpp.md). Every rule covers ancestors, so a config above the
project still owns. A manifest is parsed, never grepped: `"eslint"` sits in `scripts` far more
often than in any dependency block, and a `scripts` entry never decides ownership.

Ownership the rules cannot see is yours to name in the plan: a linter config under a non-standard
filename that the repo's own script passes with `--config`, a formatter that runs only in CI.

`on PATH` and `missing` list `uv`, `node`, `go` (1.25+), `dotnet` (10+), `cmake` and `meson`
(C/C++ under `--deep`), `gitleaks`, `opengrep` and `osv-scanner`. A missing toolchain is what a
whole language's `not assessed (reason)` cites.

## The footprint

Before any tool runs, the scan saves `git status --porcelain --untracked-files=all` as
`<run-dir>/footprint.txt`. `health.py finish` compares a second listing against it, and also
lists every file written since the scan started, because a cache a tool leaves under an ignored
directory (`node_modules/.cache`, `__pycache__`) never shows in `git status`.

## The shape it writes

```
repo: <abs path> · head: <short sha> · dirty: <n> paths

## project <dir>
  manifests: package.json
  js-ts         42 files     6210 lines (6.2 KLOC)
  lint assets  css 6 files 900 lines (0.9 KLOC); graphql 2 files 40 lines (0.0 KLOC)
  owned: biome (biome.json), prettier (package.json devDependencies), tsc (tsconfig.json)
  unowned: eslint, fallow, knip, oxfmt, oxlint, stryker
  node_modules: present

## project <dir>
  manifests: package.json
  workspace shell: no source of its own

## repo-wide
  on PATH: git 2.50.0, uv 0.13.6, node 26.13.0, gitleaks 8.30.1, osv-scanner 2.7.0
  missing: meson, opengrep
  workflows: 3 files (.github/workflows/ci.yml, …)
  snapshots: testdata/, tests/__snapshots__/
  generated: 4 files by name or header (src/routeTree.gen.ts, …)
  lockfiles: package-lock.json, uv.lock
  unassessed: md:84 yaml:14 sh:2
  file list: scope.txt (312 files)
```

`snapshots` and `generated` are the two lines triage leans on: a fixture, a captured snapshot or
generated code under scan is graded differently from hand-written code. `snapshots` lists every
directory named `captured`, `golden`, `__snapshots__`, `fixtures`, `testdata` or `snapshots`;
`generated` lists files under `gen/` or `generated/`, files named `*.gen.*`, `*.pb.*`, `*_gen.go`,
`*_pb2.py` or `*.min.js`, and files whose first lines say `Code generated … DO NOT EDIT` or `@generated`.
Both lists are by name: a snapshot or a generated file the names do not give away is yours to
find.
