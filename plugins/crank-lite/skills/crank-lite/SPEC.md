# Phase: Spec

Interview the user at a PRD/Spec level about every aspect of their idea — the user-facing behavior, acceptance criteria, key technical decisions, and validation strategy — until the frontier is empty and the failure catalogue is walked.

## Interview

Resolve the key technical decisions: data structures, interfaces/seams, test methodology, validation strategies, and the general shape an implementation might take.

1. **Before the first question, read:**
   - The glossary and any ADRs, each at its home per [DOMAIN-DOCS.md](DOMAIN-DOCS.md) → Homes, and the conventions in `CLAUDE.md`/`AGENTS.md`, where they exist.
   - The incoming artifact's Grounding section, or the `grounding.md` its `Grounding:` header names, verify-then-trusted per [ARTIFACT-HOME.md](ARTIFACT-HOME.md) → Grounding.
2. **Before the design and test-methodology questions, read [VOCABULARY.md](VOCABULARY.md)**: this phase leans on **depth**, **leverage / locality**, **deletion test**, **seam**, **rewrite test**, **journey test**, and **spaghetti growth**.
3. **Walk the frontier in rounds:**
   - Apply the design rules below as each module comes up.
   - Settle the test methodology as a minimalist: every test the spec calls for pins a distinct observable behavior through a **seam** and passes the **rewrite test**; acceptance criteria along one workflow share one **journey test**.
   - When a round would ask a layout, hierarchy, or interaction question with more than one defensible answer about a page, screen, component, CLI output, flags, help text, or TUI the change adds or reshapes, lead that round with a prototype offer, 3 to 5 variants behind one switcher, in place of the question, once per effort. When `.crank/<slug>/prototype/` already holds files, offer to reopen them in place of a build. On a yes, read [PROTOTYPE.md](PROTOTYPE.md) and follow it, and its verdict replaces those questions. On a no, record `Prototype: declined` among the key technical decisions.
   - When the invocation carried `--pilot`, or a loaded instruction file asks for interactive mode, and the invocation carried no `--no-pilot`, put each round on the page per [PILOT.md](PILOT.md).
4. **Before closing the interview, walk the failure catalogue**, settling each item by a fact lookup, a policy question, or an acceptance criterion:
   - absence;
   - permission family (which sibling failures get the same treatment — EPERM beside EACCES);
   - staleness;
   - destruction;
   - limits;
   - interruption (concurrent callers, retry after partial failure, crash midway);
   - trust boundary (who may call, what is validated, which access checks ownership).

## Design rules

- **Deletion test** on every new or reshaped module: one whose complexity vanishes folds into its caller.
- Sketch the module two ways under different constraints (smallest interface vs. most flexible) and take the **deeper** shape; when they tie, the one a test at its seam proves with fewer stand-ins.
- Where the analogous features disagree on convention, follow the one the repo converged on most recently.
- **Spaghetti growth** is a spec bug: reframe it here.

## Spec

The spec's file is `spec.md`, in the effort's directory ([ARTIFACT-HOME.md](ARTIFACT-HOME.md)). Its sections:

- the problem;
- proposed solution;
- user stories, one line per distinct actor and goal: `As an <actor>, I want <feature>, so that <benefit>`;
- acceptance criteria;
- key technical decisions;
- testing/validation;
- a Grounding section holding the interview's banked entries (ARTIFACT-HOME.md → Grounding);
- out of scope.

Every spec carries user stories. A story's actor is whoever meets the change: a role the product or the glossary names, a caller of an API or CLI, or, for an internal change such as a refactor or migration, the maintainer or operator who lives with it. State the feature as what that actor does or sees, with no module, schema, or library named, and the benefit as the outcome the problem says they lack. Take each story from the user's words in the interview or the incoming artifact; an actor or goal they left unnamed takes a targeted question before its story is written. At least one acceptance criterion proves each story.

Every claim about the code as it stands carries its **anchor** ([VOCABULARY.md](VOCABULARY.md) → Verification language), or a command and what it printed.

Copy a `Prototype:` line the brainstorm brief recorded into the key technical decisions as written, and any other mock path the brief recorded beside the decision it settled. Every decision in the spec carries its answer: one the interview left unanswered is settled now by a targeted question or a lookup, or moves to out of scope with a sentence on why.

Next step: continue to the plan phase ([PLAN.md](PLAN.md)) in this session, or in a fresh one: `/crank-lite plan .crank/<slug>/spec.md`.
