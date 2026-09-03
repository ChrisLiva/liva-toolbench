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
