# Repo-wide analyzers

Run over the selected directories (the whole repo when unscoped), cwd = scratch, whatever languages they hold. Ephemeral forms: `npx --yes jscpd@latest`, `npx --yes aislop@latest`, `uvx --quiet zizmor`. gitleaks, opengrep and osv-scanner are release binaries with no npm or PyPI package (the npm names are unrelated or empty placeholders), so use the one on PATH and degrade with the install hint when it is missing: `brew install gitleaks`, `brew install opengrep`, `brew install osv-scanner`. Security tools are a union: one owned by the repo never stands the others down. Record the version each tool prints.

**gitleaks** (secrets, critical, never advisory). `--redact=100` is the whole design: the secret value never enters the output, the run dir, or your context. Anchor a finding on the rule id and the file, not the flagged line (the line contains the secret). The repo's own `.gitleaks.toml` is picked up by gitleaks itself.
```sh
gitleaks dir --no-banner --redact=100 --report-format json --report-path <scratch>/gitleaks.json --exit-code 0 <repo>
```
Hits outside the inventory (ignored or vendored paths) are dropped with a count, not a listing.

**osv-scanner** (vulnerable dependencies). `--allow-no-lockfiles` avoids exit 128 on a repo without one. A root `osv-scanner.toml` only reaches nested lockfiles via `--config`. Offline markers on stderr (`no such host`, `dial tcp`, `i/o timeout`, `TLS handshake timeout`): not available, never a clean tree. Never `osv-scanner fix`.
```sh
osv-scanner scan source --recursive --allow-no-lockfiles --format json --output-file <scratch>/osv.json --verbosity error [--config <abs osv-scanner.toml>] <repo>
```
One finding per vulnerable package, not per CVE: `lodash@4.17.15 (npm): 4 advisories; fix: upgrade to ≥4.18.0`. Walk `fixed` out of the affected ranges. Advisory, not graded: no fixed version exists; the package is reached only from `devDependencies` (`package-lock.json` marks `dev: true`; for `pnpm-lock.yaml` walk each importer's `dependencies` and `optionalDependencies`); govulncheck says the symbol is never called. Every uncertainty grades: an unreadable or missing lockfile, `yarn.lock`, a package the lockfile never mentions.

**govulncheck** (Go reachability, once per `go.mod`, cwd = module dir, 300 s). Join to osv-scanner's rows by alias (`GO-…` vs `GHSA-…`). Verdicts: `symbol-reachable` grades, `imported-no-call` and `not-imported` move the advisory out of the grade. No `go` on PATH: every Go advisory grades, reason "reachability unknown".
```sh
go run golang.org/x/vuln/cmd/govulncheck@latest -json ./...
```

**zizmor** (GitHub workflow security). Files = every `.github/workflows/*.yml|yaml` and `action.yml|yaml` in the inventory; none: not available. `--offline` keeps it hermetic. zizmor discovers a `zizmor.yml` at the target repo's root on its own even from scratch: that is repo provenance, record it, and pass `--no-config` only to count what it waives. Demote `unpinned-uses` and `unpinned-images` from high to warning, or every workflow repo caps at D on hygiene alone. Anchor on the document route (`jobs.build.steps.0`).
```sh
uvx --quiet zizmor --format json-v1 --offline --no-exit-codes --no-progress -- <abs workflow files>
```

**opengrep** (SAST, JS/TS and Python, when installed). Only a local ruleset: `--config auto`, `p/…` and URLs pull semgrep-registry rules under semgrep's license. Use the repo's own `.opengrep/` or `.semgrep/` rules dir when it has one; otherwise skip with the note "no local ruleset". Rule id = last dotted segment of `check_id`. Strip `extra.lines` from the saved JSON.
```sh
opengrep scan --config <rules-dir> --json --disable-version-check --quiet <abs files>
```

**jscpd** (duplication, one pass over the whole tree). cwd = scratch, always the skill's own config (a repo's `minTokens` would tune its own grade). Pass the scan directory, never a file list. Ignore globs go in the config file (`--ignore` splits on commas) and each is anchored to the absolute scan root, or a checkout under a dotted directory matches `**/.*/**` and reads a flattering 0%.
```sh
jscpd --reporters json --output <scratch>/jscpd --format javascript,jsx,typescript,tsx,python,csharp,go --config <scratch>/jscpd.json --absolute --no-colors <repo>
```
`<scratch>/jscpd.json`: `{"minTokens":50,"minLines":5,"ignore":["<abs>/**/node_modules/**","<abs>/**/vendor/**","<abs>/**/dist/**","<abs>/**/build/**","<abs>/**/bin/**","<abs>/**/obj/**","<abs>/**/.*/**", <repo's own Biome/fallow excludes>]}`. Grade = `statistics.total.percentageTokens`; its denominator counts only files at or above `minLines`, so print the token counts beside the percent. Clones are listed as evidence, not graded one by one. Say where the clones sit (a test suite alone can read F). One pass per project directory for the project letter, one over the selection for the rollup.

**aislop** (AI-slop lint across all four languages, complementary). Scans a mirror of the inventory under `<scratch>/aislop/repo` so its git calls and config discovery never touch the repo. The mirror must be a git repo with one commit (`git init -q && git add -A && git commit -qm scan`): aislop's file walk is git-backed and an un-committed mirror scans 0 files at exit 0. Copy the repo's `.aislop/` config beside it when there is one. Env `AISLOP_NO_TELEMETRY=1`. Exit 0 or 1. `--json` returns only the summary; `--sarif` carries the per-finding rows, with paths relative to the scan root.
```sh
npx --yes aislop@latest scan --sarif <scratch>/aislop/repo > <raw>/aislop.sarif
```
The mirror holds every secret the repo does: it lives under `scratch/` and is deleted before the report.
