# Phase: Brainstorm

Interview the user at a high level about every aspect of their idea until you reach a shared understanding of the problem, desired experience, important constraints, and the concept's overall shape. Interview and readback follow the shared discipline in [INTERVIEW.md](INTERVIEW.md) — read it before your first question.

## Interview

Settle the destination first: one or two lines on the problem and what "done" looks like, confirmed by the user. Every later question, approach, and cut orients to it.

For greenfield, ask about user experience, design, workflows. For existing projects, ask how their idea fits into the current project, and if the current project needs to change significantly to incorporate their idea.

Survey before you drill: share a short agenda of the consequential decisions you can already name, then walk it in rounds per [INTERVIEW.md](INTERVIEW.md), keeping questions and decisions at a high level. Keep the agenda live — add decisions as answers surface them, strike ones they moot. If the survey turns up nothing genuinely open, say so and recommend jumping straight to the spec phase.

When a question is experiential — how something should look, behave, or read — offer a cheap throwaway artifact to react to instead of another prose question: a sketch, a sample output, or for interactive behavior a single self-contained HTML file the user double-clicks. If it settles a key decision, offer to commit it to a throwaway `prototype/<slug>` branch and note the branch beside the decision in the brief.

## Brief

When every readback section stands approved, record the concise brainstorm brief to `.crank/<slug>/brainstorm.md` at the working root — one directory per effort; if `.crank/<slug>/` already holds a *different* effort (judge by content, not name), use `<slug>-2`, `<slug>-3`, …, never renaming an existing directory — create `.crank/` if missing, with a `.crank/.gitignore` containing `*` so it never enters version control; only outside a git repo, fall back to `${TMPDIR:-/tmp}/lite-<slug>/brainstorm.md` and say so; handed a legacy flat artifact (`.crank/<phase>-<slug>.md`), move it to its per-plan home first and state the new path — and stop.

Keep the artifact light: include the idea, goals/constraints, chosen shape, key decisions, open questions, and suggested next step when those sections earn their place. An open question earns its place only when it's stated sharply enough for the spec to answer it — anything you can't phrase that precisely yet is a design hole to resolve here first.

State the path and the next step — continue to the spec phase ([SPEC.md](SPEC.md)) in this session, or in a fresh one: `/crank-lite spec .crank/<slug>/brainstorm.md` (route to the plan phase instead if the idea is already implementation-ready). Close with a single trailing sentence noting the brief can be copied elsewhere, printed inline, or deleted on request — prose, not a numbered question.
