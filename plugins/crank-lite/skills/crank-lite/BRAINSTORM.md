# Phase: Brainstorm

Interview the user at a high level about every aspect of their idea — every section the brief holds, listed below — until the agenda and the frontier are both empty. Interview and readback follow the shared discipline in [INTERVIEW.md](INTERVIEW.md) — read it before your first question.

## Interview

Settle the destination first: one or two lines on the problem and what "done" looks like, confirmed by the user. Every later question, approach, and cut orients to it.

Survey before you drill: share a short agenda of the consequential decisions you can already name — for greenfield, user experience, design, and workflows; for an existing project, how the idea fits the current code and how much that code has to change to take it — then walk it in rounds, keeping questions and decisions at a high level. Keep the agenda live — add decisions as answers surface them, strike ones they moot. If the agenda comes out empty — every decision you can name has one defensible answer — say so, list what you considered and why each is settled, and recommend jumping straight to the spec phase.

When a question is experiential — how something should look, behave, or read — offer a cheap throwaway artifact to react to instead of another prose question: a sketch, a sample output, or for interactive behavior a single self-contained HTML file the user double-clicks. If it settles a key decision, offer to commit it to a throwaway `prototype/<slug>` branch and note the branch beside the decision in the brief.

## Brief

The brief's file is `brainstorm.md`, in the effort's directory (see [ARTIFACT-HOME.md](ARTIFACT-HOME.md)). Its sections: the idea, goals/constraints, chosen shape, key decisions, open questions, a Grounding section holding the interview's banked entries (ARTIFACT-HOME.md → Grounding), and suggested next step. An open question earns its place only when it's stated sharply enough for the spec to answer it — anything you can't phrase that precisely yet is a design hole to resolve here first. In the readback each open question comes back as the sharp question it hands the spec, not as a decision to re-open.

Next step: continue to the spec phase ([SPEC.md](SPEC.md)) in this session, or in a fresh one: `/crank-lite spec .crank/<slug>/brainstorm.md` (route to the plan phase instead if the idea is already implementation-ready).
