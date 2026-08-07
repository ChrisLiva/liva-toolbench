# Phase: Plan

Interview the user relentlessly at an implementation level about every aspect of their idea, spec, or PRD until you reach a shared understanding of the build strategy, code boundaries, risks, and verification approach. Interview and readback follow the shared discipline in [INTERVIEW.md](INTERVIEW.md) — read it before your first question.

## Interview

Resolve every implementation decision, and keep the planned code minimal.

A risk no check can retire is a decision: put it to the user during the interview, not into the artifact. The interview resolves open questions; the plan ships without any.

Probe, don't recall: any build-tool, CLI-flag, or pinned-dependency behavior the plan leans on gets run once during the interview's fact lookups — never asserted from memory. And when the work keys, transforms, or migrates data that already exists, run the proposed invariant over the full real dataset and record the count checked; canned fixtures can't stand in for it.

## Plan

When every readback section stands approved, record the concise implementation plan to a new temp file (e.g. `${TMPDIR:-/tmp}/lite-plan-<slug>.md`) and stop.

Keep the artifact light: include the goal, assumptions, ordered tasks, verification checks, and risks — each risk paired with the check that retires it during execution — when those sections earn their place. Prefer checks a machine can judge: the repo's exact gate commands (typecheck, lint, test, build), or — where no committed test fits — a throwaway probe script that asserts exact outputs and exits non-zero on failure, deleted before commit; the check that retires a risk names one of these instruments.

Tell the user the temp file path and recommend `/lite-execute` next when the plan is ready to build.
