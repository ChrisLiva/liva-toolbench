# Phase: Brainstorm

Interview the user at a high level about every aspect of their idea until you reach a shared understanding of the problem, desired experience, important constraints, and the concept's overall shape. Interview and readback follow the shared discipline in [INTERVIEW.md](INTERVIEW.md) — read it before your first question.

## Interview

Settle the destination first: one or two lines on the problem and what "done" looks like, confirmed by the user. Every later question, approach, and cut orients to it.

For greenfield, ask about user experience, design, workflows. For existing projects, ask how their idea fits into the current project, and if the current project needs to change significantly to incorporate their idea.

Survey before you drill: share a short agenda of the consequential decisions you can already name, then walk it one decision at a time, keeping questions and decisions at a high level and resolving dependencies between them one-by-one. Keep the agenda live — add decisions as answers surface them, strike ones they moot. If the survey turns up nothing genuinely open, say so and recommend jumping straight to the spec phase.

When a question is experiential — how something should look, behave, or read — offer a cheap throwaway artifact (a sketch, stub, or sample output) to react to instead of another prose question.

## Brief

When every readback section stands approved, record the concise brainstorm brief to a new temp file (e.g. `${TMPDIR:-/tmp}/lite-brainstorm-<slug>.md`) and stop.

Keep the artifact light: include the idea, goals/constraints, chosen shape, key decisions, open questions, and suggested next step when those sections earn their place. Carry any sketch or diagram the user approved during readback into the brief. An open question earns its place only when it's stated sharply enough for the spec to answer it — anything you can't phrase that precisely yet is a design hole to resolve here first.

Tell the user the temp file path and offer to continue to the spec phase ([SPEC.md](SPEC.md)) — or the plan phase ([PLAN.md](PLAN.md)) if the idea is already implementation-ready. Load the next phase file only on an explicit "continue"; never auto-advance.
