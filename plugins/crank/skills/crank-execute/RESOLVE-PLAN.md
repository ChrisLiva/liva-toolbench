# Resolving the plan

Which plan a run executes, from its argument. Every effort's artifacts live in `.crank/<slug>/` at the repository root ([ARTIFACT-HOME.md](ARTIFACT-HOME.md)); the ledger and `exec/` dir resolve from the slug.

1. **Explicit path** — read it as-is; the slug is the plan's parent directory name.
2. **Bare slug** — resolves to `.crank/<slug>/plan.md`.
3. **No argument, plan in the conversation** — use it; derive a slug from the plan's title, and its artifacts live in `.crank/<slug>/`.
4. **No argument, exactly one plan on disk** — use it without asking.
5. **No argument, several plans** — ask via a structured question listing each plan with its derived status: *not started* (no ledger in either home), *in progress* (unchecked boxes remain), *done* (all `[x]`). An effort directory without a `plan.md` (e.g. spec-only) shows as "no plan yet" and is not executable.
6. **No argument, no plans anywhere** — say so and recommend the plan phase (`/crank plan …`).

Resolving any artifact checks the per-plan path first, then the legacy paths in [LEGACY-ARTIFACTS.md](LEGACY-ARTIFACTS.md); a hit there, or a ledger whose plan directory is gone, is adopted per that file before the run proceeds.
