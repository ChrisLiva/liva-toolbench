# Legacy artifact adoption

Earlier crank versions stored artifacts at flat paths. On a legacy hit, adopt the artifact into the per-plan layout once, at the moment of encounter:

- The legacy paths: `.crank/plan-<slug>.md`, `.crank/exec-<slug>/`, and the fixed-name ledgers — `<git-dir>/crank/progress.md` or worktree-root `.crank/progress.md`.
- **Plan and exec dir** — move `.crank/plan-<slug>.md` to `.crank/<slug>/plan.md` and `.crank/exec-<slug>/` to `.crank/<slug>/exec/`.
- **The ledger** — rename a fixed-name git-dir `progress.md` to `progress-<slug>.md` (slug from its `Plan:` header), or move a worktree-root `.crank/progress.md` to `.crank/<slug>/progress.md`; either way rewrite its `Plan:` header to the new plan path. A ledger whose slug matches no `.crank/<slug>/` directory (plan deleted) is stale — surface it and offer deletion, never silently resume it.
- Announce every new path so a user's saved link is updated once.
- Never clobber: if both the legacy and per-plan copies of an artifact exist, stop and ask instead of overwriting either.

Completion criterion: re-resolve every artifact for this slug — plan, exec dir, ledger — and none resolves to a legacy path, and the ledger's `Plan:` line names the file that now exists at `.crank/<slug>/plan.md`.
