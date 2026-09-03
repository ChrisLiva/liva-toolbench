# Tools of record

Run dir `<run-dir>` · `<repo>` @ `<sha>` · <quick|deep> · scope: <all projects | --project …> · categories: <all | --only …>

| project | category | tool | version | provenance | scope |
| --- | --- | --- | --- | --- | --- |
| . | lint | eslint | 9.30.0 | repo config (eslint.config.js), repo binary | project |
| . | lint | oxlint | latest | default config, ephemeral, standby behind eslint | project |
| . | types | tsc | 7.0.2 | repo config (tsconfig.json), repo binary | project |
| . | dead code | knip | latest | default config, ephemeral | project |
| . | complexity | fallow health | latest | default config, ephemeral | project |
| . | format | prettier | 3.9.6 | repo config (.prettierrc.json), repo binary | project |
| . | test quality | stryker | | skipped: not owned (never imposed) | |
| repo | security | gitleaks | 8.30.1 | repo config (.gitleaks.toml), system binary | repo |
| repo | security | osv-scanner | 2.5.1 | default, system binary | repo |
| repo | security | zizmor | latest | repo config (zizmor.yml), ephemeral | repo |
| repo | security | opengrep | | not available: brew install opengrep | |
| repo | duplication | jscpd | latest | skill config, ephemeral | selected project dirs |
| repo | lint | aislop | latest | default config, ephemeral | selected project dirs |

Provenance vocabulary, exactly: `repo config (<file>), repo binary` · `repo config (<file>), ephemeral` · `default config, ephemeral` · `default config, ephemeral, standby behind <owner>` · `skill config, ephemeral` · `system binary` · `skipped: <reason>` · `not available: <hint>`.
Version is `latest` until the tool prints one; the scan subagent replaces it.

## Resolving a row

A tool the repo owns runs its binary against its config; owned but not installed runs ephemeral
against the repo's config; not owned runs the default at the latest version. Ownership itself was
settled in step 1, by the ownership rule in that language's reference.

eslint, biome, mypy, golangci-lint, stryker, cosmic-ray, gremlins and Stryker.NET are **never
imposed**: unowned, they get a `skipped: not owned (never imposed)` row and no run.

The default lint, format and types tool still runs behind an owner as a **standby**, and its
findings are dropped once the owner graded the category. An owner that errored leaves the standby's
findings in the grade, and the plan says so.
