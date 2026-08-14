# Phase: Spec

Interview the user relentlessly at a PRD/Spec level about every aspect of their idea until you reach a shared understanding of the user-facing behavior, acceptance criteria, key technical decisions, and validation strategy. Interview and readback follow the shared discipline in [INTERVIEW.md](INTERVIEW.md) — read it before your first question.

## Interview

Resolve the key technical decisions: data structures, interfaces/seams, test methodology, validation strategies, and the general shape an implementation might take. When speccing existing codebases, proactively suggest refactors, simplifications, or new codebase designs that would improve the codebase as a whole and also accomplish the user's idea.

Settle the test methodology as a minimalist: every test the spec calls for pins a distinct observable behavior through a seam and would survive a rewrite of the implementation in another language; acceptance criteria that fall along one workflow share one end-to-end journey test that accretes their assertions, rather than a test per criterion.

Before closing the interview, walk the failure catalogue — absence, permission siblings, staleness, destruction, limits — each item settled by a fact lookup, asked as a policy question, or landed as an acceptance criterion.

## Spec

When every readback section stands approved, record the concise spec to `.crank/<slug>/spec.md` at the working root — one directory per effort; if `.crank/<slug>/` already holds a *different* effort (judge by content, not name), use `<slug>-2`, `<slug>-3`, …, never renaming an existing directory — create `.crank/` if missing, with a `.crank/.gitignore` containing `*` so it never enters version control; only outside a git repo, fall back to `${TMPDIR:-/tmp}/lite-<slug>/spec.md` and say so; handed a legacy flat artifact (`.crank/<phase>-<slug>.md`), move it to its per-plan home first and state the new path — and stop.

Keep the artifact light: include the problem, proposed solution, acceptance criteria, key technical decisions, testing/validation, out of scope, and open questions when those sections earn their place.

State the path and the next step — continue to the plan phase ([PLAN.md](PLAN.md)) in this session, or in a fresh one: `/crank-lite plan .crank/<slug>/spec.md`. Close with a single trailing sentence noting the spec can be copied elsewhere, printed inline, or deleted on request — prose, not a numbered question.
