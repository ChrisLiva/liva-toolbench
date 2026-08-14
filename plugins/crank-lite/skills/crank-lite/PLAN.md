# Phase: Plan

Interview the user relentlessly at an implementation level about every aspect of their idea, spec, or PRD until you reach a shared understanding of the build strategy, code boundaries, risks, and verification approach. Interview and readback follow the shared discipline in [INTERVIEW.md](INTERVIEW.md) — read it before your first question.

## Interview

Resolve every implementation decision, and keep the planned code minimal.

A risk no check can retire is a decision: put it to the user during the interview, not into the artifact. The interview resolves open questions; the plan ships without any.

Probe, don't recall: any build-tool, CLI-flag, or pinned-dependency behavior the plan leans on gets run once during the interview's fact lookups — never asserted from memory. And when the work keys, transforms, or migrates data that already exists, run the proposed invariant over the full real dataset and record the count checked; canned fixtures can't stand in for it.

## Plan

When every readback section stands approved, record the concise implementation plan to `.crank/<slug>/plan.md` at the working root — one directory per effort; if `.crank/<slug>/` already holds a *different* effort (judge by content, not name), use `<slug>-2`, `<slug>-3`, …, never renaming an existing directory — create `.crank/` if missing, with a `.crank/.gitignore` containing `*` so it never enters version control; only outside a git repo, fall back to `${TMPDIR:-/tmp}/lite-<slug>/plan.md` and say so; handed a legacy flat artifact (`.crank/<phase>-<slug>.md`), move it to its per-plan home first and state the new path — and stop.

Keep the artifact light: include the goal, assumptions, ordered tasks, verification checks, and risks — each risk paired with the check that retires it during execution — when those sections earn their place. Prefer checks a machine can judge: the repo's exact gate commands (typecheck, lint, test, build), or — where no committed test fits — a throwaway probe script that asserts exact outputs and exits non-zero on failure, deleted before commit; the check that retires a risk names one of these instruments. Plan tests as a minimalist: one journey test per workflow, accreting one assertion per behavior — a test that re-pins an already-covered behavior, or that wouldn't survive a rewrite of the implementation, stays out of the plan.

State the path and the next step: `/lite-execute .crank/<slug>/plan.md` — in this session or a fresh one. Close with a single trailing sentence noting the plan can be copied elsewhere, printed inline, or deleted on request — prose, not a numbered question.
