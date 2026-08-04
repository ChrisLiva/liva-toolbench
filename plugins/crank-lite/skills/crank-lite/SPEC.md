# Phase: Spec

Interview the user relentlessly at a PRD/Spec level about every aspect of their idea until you reach a shared understanding of the user-facing behavior, acceptance criteria, key technical decisions, and validation strategy. Interview and readback follow the shared discipline in [INTERVIEW.md](INTERVIEW.md) — read it before your first question.

## Interview

Resolve the key technical decisions: data structures, interfaces/seams, test methodology, validation strategies, and the general shape an implementation might take. When speccing existing codebases, proactively suggest refactors, simplifications, or new codebase designs that would improve the codebase as a whole and also accomplish the user's idea.

Walk down each branch of the decision tree for their idea, resolving dependencies between decisions one-by-one.

## Spec

When every readback section stands approved, record the concise spec to a new temp file (e.g. `${TMPDIR:-/tmp}/lite-spec-<slug>.md`) and stop.

Keep the artifact light: include the problem, proposed solution, acceptance criteria, key technical decisions, testing/validation, out of scope, and open questions when those sections earn their place. Carry any pseudo-code or diagram the user approved during readback into the spec — downstream planning inherits the exact shape that was vetted, not a prose paraphrase of it.

Tell the user the temp file path and offer to continue to the plan phase ([PLAN.md](PLAN.md)) when implementation planning is the natural next step. Load the next phase file only on an explicit "continue"; never auto-advance.
