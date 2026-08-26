# Phase: Spec

Interview the user relentlessly at a PRD/Spec level about every aspect of their idea until you reach a shared understanding of the user-facing behavior, acceptance criteria, key technical decisions, and validation strategy. Interview and readback follow the shared discipline in [INTERVIEW.md](INTERVIEW.md) — read it before your first question.

## Interview

Resolve the key technical decisions: data structures, interfaces/seams, test methodology, validation strategies, and the general shape an implementation might take.

Before the first question, read `CONTEXT.md`, any ADRs, and the conventions in `CLAUDE.md`/`AGENTS.md` where they exist; a tradeoff an ADR records is settled. For each new or reshaped module: imagine it deleted, and if its complexity just vanishes, fold it into its caller. Sketch it two ways under different constraints (smallest interface vs. most flexible), pick the one that hides more behind less, and when they tie, the one a test at its seam proves with fewer stand-ins. Where the analogous features disagree on convention, follow the one the repo converged on most recently. A one-off flag or special case threaded through a shared flow is a spec bug to reframe, not a detail for the plan. When the user rejects a load-bearing recommendation for a reason a future spec would need, offer to record it as an ADR in the repo.

Settle the test methodology as a minimalist: every test the spec calls for pins a distinct observable behavior through a seam and would survive a rewrite of the implementation in another language; acceptance criteria that fall along one workflow share one end-to-end journey test that accretes their assertions, rather than a test per criterion.

Before closing the interview, walk the failure catalogue — absence, permission siblings, staleness, destruction, limits, interruption (concurrent callers, retry after partial failure, crash midway), trust boundary (who may call, what is validated, which access checks ownership) — each item settled by a fact lookup, asked as a policy question, or landed as an acceptance criterion.

## Spec

When every readback section stands approved, record the concise spec to `.crank/<slug>/spec.md` per [ARTIFACT-HOME.md](ARTIFACT-HOME.md) — read it before writing the file — and stop.

Keep the artifact light: include the problem, proposed solution, acceptance criteria, key technical decisions, testing/validation, out of scope, and open questions when those sections earn their place.

State the path and the next step — continue to the plan phase ([PLAN.md](PLAN.md)) in this session, or in a fresh one: `/crank-lite plan .crank/<slug>/spec.md`. Close with a single trailing sentence noting the spec can be copied elsewhere, printed inline, or deleted on request — prose, not a numbered question.
