# Legacy artifact adoption

Earlier crank versions stored artifacts at flat paths. On a legacy hit, adopt the artifact into the per-plan layout once, at the moment of encounter:

- The legacy paths: `.crank/plan-<slug>.md`, `.crank/exec-<slug>/`, and the fixed-name ledgers — `<git-dir>/crank/progress.md` or worktree-root `.crank/progress.md`.
- Move the file(s) into `.crank/<slug>/…` and rewrite the ledger's `Plan:` header to the new plan path.
- Rename a fixed-name git-dir `progress.md` to `progress-<slug>.md`, slug taken from its `Plan:` header; a legacy worktree-root `.crank/progress.md` moves to `.crank/<slug>/progress.md` the same way.
- Announce every new path so a user's saved link is updated once.
- Never clobber: if both the legacy and per-plan copies of an artifact exist, stop and ask instead of overwriting either.
- A git-dir ledger whose slug matches no `.crank/<slug>/` directory (plan deleted) is stale — surface it and offer deletion, never silently resume it.
