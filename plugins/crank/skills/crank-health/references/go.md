# Go analyzers

cwd = the module directory (the one holding `go.mod`); run once per module. Env for every command: `GOFLAGS=-mod=readonly GOMODCACHE=$HOME/go/pkg/mod`. Ephemeral form is `go run <import-path>@latest`, which builds into the module and build caches, never the repo. Gate every tool on `go version` run from the same directory (a `go.work` or `toolchain` directive changes the answer per directory); no `go`, or below 1.25: every Go category is not assessed with one sentence naming https://go.dev/dl. Strip `go: downloading …`, `go: extracting …`, `go: finding …` lines from stderr before reading it. Record the version each tool prints; gocognit has no `-version` and a `go run @latest` gosec prints `dev`, so resolve those with `cd <scratch> && GOFLAGS= go list -m -f '{{.Version}}' <module>@latest`.

| category | tool |
| --- | --- |
| lint | staticcheck (S/SA/ST), `go vet`, golangci-lint (owned only) |
| format | gofmt |
| types | staticcheck compile diagnostics |
| dead code | staticcheck U1000 |
| complexity | gocognit |
| security | gosec; govulncheck (repo-wide, see common.md) |
| test quality (deep) | gremlins (owned only); `go test -cover` as context |

## Commands

**staticcheck** (types, dead code, lint from one run). Exit 1 = findings; failure = non-zero and nothing parsed. `compile` records saying `cannot find module providing package`, `no required module provides` or `import lookup disabled` mean the module graph is broken: refuse the whole run as error rather than grade a partial graph. Route: `U\d+` to dead code, `compile` to types as error, the rest to lint as warning.
```sh
go run honnef.co/go/tools/cmd/staticcheck@latest -f json ./...
```

**go vet** (lint). Exit 0 even with diagnostics; non-zero = package load failure, stderr's first line names the package. Output is several pretty-printed JSON documents concatenated (`{}` per silent package): split by brace counting outside strings.
```sh
go vet -json ./...
```

**golangci-lint** (lint, owned only: `.golangci.yml|yaml|toml|json`). Stdout is one JSON line followed by prose: take the line carrying `Issues`. Rule = `FromLinter`.
```sh
go run github.com/golangci/golangci-lint/v2/cmd/golangci-lint@latest run --output.json.path stdout
```

**gofmt** (format). Pass files, never a directory (a directory walks vendor and generated code). Exit 0 always; non-zero = unparseable file. Never `-w`, never `go fmt`.
```sh
gofmt -l <module-relative files>
```

**gocognit** (complexity). `-over -1` is load-bearing: the default omits zero-scored functions and shrinks the denominator. `./...` is rejected; pass `.` and filter to the inventory.
```sh
go run github.com/uudashr/gocognit/cmd/gocognit@latest -json -over -1 .
```

**gosec** (security). No `-quiet` (under it a load failure prints nothing and exits 0). Exit 1 for findings and for load errors alike, so read the envelope: empty `Issues` with non-empty `Golang errors` is a refusal. `line` and `column` arrive as strings. Drop the `code` window from findings and from the saved JSON before it leaves scratch (G101's window is the credential): `jq 'del(.Issues[].code)'`.
```sh
go run github.com/securego/gosec/v2/cmd/gosec@latest -fmt=json ./...
```

**go test** (deep, context only). Total is the `total: (statements) N%` line. This is statement coverage, say so.
```sh
go test -coverprofile=<scratch>/coverage.out ./... && go tool cover -func=<scratch>/coverage.out
```

**gremlins** (deep, owned only: `.gremlins.yaml|yml`). The report outranks the exit code (`--threshold-efficacy` makes a complete run exit non-zero). Zero mutants = error, never 0%.
```sh
go run github.com/go-gremlins/gremlins/cmd/gremlins@latest unleash --output <scratch>/gremlins.json
```

## Gotchas

- Timeouts: 300 s for staticcheck, vet, gosec and govulncheck; a cold module cache compiles the world.
- `vendor/` is out of the inventory; the tools' `./...` respects `-mod=readonly`.
- A nested `go.mod` is its own module and its own project.
