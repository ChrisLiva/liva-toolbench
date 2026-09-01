# Phase: Spec

Interview the user relentlessly at a PRD/Spec level about every aspect of their idea — the user-facing behavior, acceptance criteria, key technical decisions, and validation strategy — until the frontier is empty and the failure catalogue is walked. Interview and readback follow the shared discipline in [INTERVIEW.md](INTERVIEW.md) — read it before your first question.

## Vocabulary

Before the design and test-methodology questions, read [VOCABULARY.md](VOCABULARY.md): this phase leans on **depth**, **leverage / locality**, the **deletion test**, the **seam**, the **rewrite test**, the **journey test**, and **spaghetti growth**.

## Interview

Resolve the key technical decisions: data structures, interfaces/seams, test methodology, validation strategies, and the general shape an implementation might take.

Before the first question, read `CONTEXT.md`, any ADRs, the conventions in `CLAUDE.md`/`AGENTS.md` where they exist, and the incoming artifact's Grounding section (or the `grounding.md` its `Grounding:` header names, when the full crank pipeline wrote it) — a covered lookup becomes a confirm at its cited evidence, and an absence entry re-runs its recorded search; a tradeoff an ADR records is settled. For each new or reshaped module, apply the **deletion test**: a module whose complexity just vanishes folds into its caller. Sketch it two ways under different constraints (smallest interface vs. most flexible), take the **deeper** shape, and when they tie, the one a test at its seam proves with fewer stand-ins. Where the analogous features disagree on convention, follow the one the repo converged on most recently. A one-off flag or special case threaded through a shared flow is **spaghetti growth** — a spec bug to reframe, not a detail for the plan. When the user rejects a load-bearing recommendation for a reason a future spec would need, offer to record it as an ADR in the repo.

Settle the test methodology as a minimalist: every test the spec calls for pins a distinct observable behavior through a **seam** and passes the **rewrite test**; acceptance criteria that fall along one workflow share one **journey test** rather than a test per criterion.

Before closing the interview, walk the failure catalogue — absence, permission family (which sibling failures get the same treatment — EPERM beside EACCES), staleness, destruction, limits, interruption (concurrent callers, retry after partial failure, crash midway), trust boundary (who may call, what is validated, which access checks ownership) — each item settled by a fact lookup, asked as a policy question, or landed as an acceptance criterion.

## Spec

The spec's file is `spec.md`, in the effort's directory (see [ARTIFACT-HOME.md](ARTIFACT-HOME.md)). Its sections: the problem, proposed solution, acceptance criteria, key technical decisions, testing/validation, a Grounding section holding the interview's banked entries (ARTIFACT-HOME.md → Grounding), and out of scope. Every decision in it carries its answer: one the interview left unanswered is settled now by a targeted question or a lookup, or moves to out of scope with a sentence on why.

Next step: continue to the plan phase ([PLAN.md](PLAN.md)) in this session, or in a fresh one: `/crank-lite plan .crank/<slug>/spec.md`.
