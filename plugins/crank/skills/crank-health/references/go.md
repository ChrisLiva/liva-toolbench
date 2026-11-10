# Go analyzers

What the scan runs for a Go module and how to read each tool's rows. The commands themselves, with
their pinned versions and cwd, are in `<run-dir>/tools.md` → Commands.

Every tool runs once per module, from the directory holding `go.mod`, with
`GOFLAGS=-mod=readonly`, so nothing rewrites `go.mod` or `go.sum`. Ephemeral tools run as
`go run <import path>@<version>`, which builds into the module and build caches, never the repo.
The gate is `go version` run from the module directory (a `go.work` or `toolchain` directive
changes the answer per directory): no `go`, or below 1.25, and every Go category reads
`not assessed`, naming https://go.dev/dl.

| category | tool |
| --- | --- |
| lint | staticcheck (S/SA/ST), `go vet`, golangci-lint (owned only) |
| format | gofmt |
| types | staticcheck compile diagnostics |
| dead code | staticcheck U1000 |
| complexity | gocognit |
| security | gosec; govulncheck (joined to osv-scanner, see [common.md](common.md)) |
| test quality (deep) | gremlins (owned only); `go test -cover` as context |

Ownership: golangci-lint by `.golangci.yml|yaml|toml|json`, gremlins by `.gremlins.yaml|yml`, in
the module or an ancestor. A golangci config under another name that the repo's own script
passes with `--config` is not seen: name it in the plan, and read its waivers before you leave
the findings it waives graded.

## Reading the rows

**staticcheck** (types, dead code, lint from one run). `U…` rules are dead code, `compile` rows
are type errors, the rest is lint at warning. A `compile` row saying the module graph is broken
(`cannot find module providing package`, `no required module provides`, `import lookup disabled`)
turns the whole row into `error`: a partial graph is not graded. With golangci-lint owned,
staticcheck's lint rows stand down and its types and dead-code rows stay.

**go vet** (lint). A non-zero exit is a package that did not load, and the row reads `error`
with the package named.

**golangci-lint** (lint, owned only). The rule is the linter that reported (`FromLinter`).

**gofmt** (format). The metric is files it would rewrite / files passed.

**gocognit** (complexity). Every function counts, zero-scored ones included, so the denominator
is honest; the `score` flag carries each number. Generated files are in both halves: say so when
`inventory.md` lists many.

**gosec** (security). HIGH is error, MEDIUM warning, LOW info, and every row grades on the
default config. `G101` is a secret: critical, its message replaced. `G115` integer-conversion
rows on generated database code are the usual bulk; read the repo's own linter config for a
waiver before you count them.

**govulncheck** (security). One row per advisory with its verdict as the rule:
`symbol-reachable`, `imported-no-call` or `not-imported`. Its verdict decides the osv-scanner row
for the same advisory, and the two never both grade: reachable leaves osv-scanner's row graded
and marks govulncheck's a duplicate; unreachable makes osv-scanner's advisory.

## Deep

**go test** (deep, context only). Total is the `total: (statements) N%` line. This is statement coverage, say so.
```sh
go test -coverprofile=<scratch>/coverage.out ./... && go tool cover -func=<scratch>/coverage.out
```

**gremlins** (deep, owned only: `.gremlins.yaml|yml`). The report outranks the exit code (`--threshold-efficacy` makes a complete run exit non-zero). Zero mutants = error, never 0%.
```sh
go run github.com/go-gremlins/gremlins/cmd/gremlins@latest unleash --output <scratch>/gremlins.json
```

## Gotchas

- Timeouts: every Go tool gets 300 s; a cold module cache compiles the world. A `timeout` row reruns warm, usually inside the budget.
- `vendor/` is out of the inventory; the tools' `./...` respects `-mod=readonly`.
- A nested `go.mod` is its own module and its own project.
