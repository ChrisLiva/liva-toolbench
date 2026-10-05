# Phase: Brainstorm

Interview the user at a high level about every aspect of their idea — every section the brief holds, listed below — until the agenda and the frontier are both empty.

## Interview

1. **Settle the destination first**: one or two lines on the problem and what "done" looks like, confirmed by the user. Every later question, approach, and cut orients to it.
2. **Survey before you drill**: share a short agenda of the consequential decisions you can already name:
   - for greenfield, user experience, design, and workflows;
   - for an existing project, how the idea fits the current code and how much that code has to change to take it.

   If the agenda comes out empty, meaning every decision you can name has one defensible answer, say so, list what you considered and why each is settled, and recommend jumping straight to the spec phase.
3. **Walk the agenda in rounds** until it and the frontier are both empty, keeping questions and decisions at a high level. Keep the agenda live: add decisions as answers surface them, strike ones they moot.

When a question is experiential, about how something should look, behave, or read, offer a mock to react to instead of another prose question: a sketch, a sample output, a single self-contained HTML file the user double-clicks when the behavior is the question, or 3 to 5 variants behind one switcher when the look is the question. On a yes to variants, read [PROTOTYPE.md](PROTOTYPE.md) and follow it. Write any mock file under `.crank/<slug>/` per [ARTIFACT-HOME.md](ARTIFACT-HOME.md), and keep it on disk until the plan's execution finishes.

## Brief

The brief's file is `brainstorm.md`, in the effort's directory (see [ARTIFACT-HOME.md](ARTIFACT-HOME.md)). Its sections:

- the idea;
- goals/constraints;
- chosen shape;
- key decisions, each mock's path beside the decision it settled;
- open questions, each listed only when it's stated sharply enough for the spec to answer it. Anything you can't phrase that precisely yet is a design hole to resolve here first. In the readback each open question comes back as the sharp question it hands the spec, not as a decision to re-open;
- a Grounding section holding the interview's banked entries (ARTIFACT-HOME.md → Grounding);
- suggested next step.

Next step: continue to the spec phase ([SPEC.md](SPEC.md)) in this session, or in a fresh one: `/crank-lite spec .crank/<slug>/brainstorm.md` (route to the plan phase instead if the idea is already implementation-ready).
