# Phase: Spec

## Goal

Turn what you and the user have been discussing, or the user's idea, into a single self-contained spec — part PRD (user-facing intent), part technical spec (decisions already settled).

## Hard Rules

- **Grill the open technical decisions before drafting** (Flow → Grill the technical decisions). Outside those, if a gap blocks the writeup, resolve it and note the assumption rather than reopening the interview.
- **Placeholder language.** No `TODO`, `TBD`, `for later`, `v2`, "we'll figure out later", or equivalent. If a decision is open: resolve it now (one targeted question or spawn a subagent to investigate), or move it to **Out of scope** with a sentence on why.
- **Write the draft to `.crank/<slug>/spec.md`** per [ARTIFACT-HOME.md](ARTIFACT-HOME.md) — read it before writing the file.
- **Reference real files as `path:line`** wherever you have them.

## Guidelines

### Simplify first

Before locking Technical decisions, hunt for the re-framing that makes the change smaller — not the design that best organizes its complexity. The strongest version of a feature is often a natural extension of a module that already exists.

Treat each of these as a design problem to resolve in the spec, never a detail to leave for the implementer:

- **Spaghetti growth the spec would introduce** — a one-off boolean, nullable mode, or special-case branch threaded through an existing flow. Re-frame the state model so the branch disappears, or route the behavior behind the module that owns the concept.
- **Feature-specific logic landing in a shared path.** Move the ownership boundary so the feature becomes part of the module that owns the concept, instead of a check scattered through code that shouldn't know about it.
- **A near-duplicate of something the codebase already has.** Reuse the canonical helper the grounding subagents reported; a bespoke twin is architectural drift.
- **Make impossible states unrepresentable.** An interface that leans on optionality, casts, or silent fallbacks hides an invariant; make it explicit instead — if a field is sometimes absent, the spec says when and why.

Working code that makes the surrounding code harder to reason about is a spec bug, not an implementation detail.

## References

### Subagents

This phase dispatches **standard** subagents for what the codebase can answer — does this surface exist, what's the exact signature, is a claim you're about to write into the spec actually true. The adversarial review is its only **heavy** dispatch. Resolve each tier to your harness, and the dispatch-or-main-thread call, per [SUBAGENT-TIERS.md](SUBAGENT-TIERS.md) → Dispatch or main thread.

### Vocabulary

[VOCABULARY.md](VOCABULARY.md) — read it before you draft. This phase leans on **module**, **interface**, **depth** (**leverage** / **locality**), the **deletion test**, **seam**, **dead seam**, **port** / **adapter**, **spaghetti growth**, the **probe**, the **implementation-detail test**, the **rewrite test**, and the **journey test**.

## Deliverables

A single self-contained spec written to the `.crank/` file (see Hard Rules). Include whichever sections apply, scaled to the topic (a bug fix is 20 lines; a new subsystem is denser):

- **Problem** — what the user is trying to solve, in their words.
- **Solution** — the proposed change, in user-facing terms.
- **User stories** — `As an <actor>, I want <feature>, so that <benefit>`, when distinct actors or user goals clarify the scope. Omit for small bugs, internal refactors, or technical changes where the real contract is the acceptance criteria plus Technical decisions.
- **Acceptance criteria** — a numbered list of independently checkable statements, one per behavior: every interaction, keybinding, alias, edge case, state transition, and validation. Each criterion must be falsifiable by an agent or a named human smoke check — "works correctly" is not a criterion; "pressing `Esc` closes the dialog without saving" is. This list is the contract the plan's Coverage table and execute's final review key off: a behavior not listed here is invisible to every downstream check.
- **Technical decisions** — every architecturally-meaningful call landed on: modules touched, interfaces, schemas, data flow, dependencies (pinned), failure modes. Name the chosen option and one sentence on why; when a real alternative was on the table, also name what the chosen option gives up — a decision recorded with only its upside reads as unexamined and invites re-litigating. For each layer touched (DB, IPC, renderer state, renderer queries), name the existing surface the change goes through and cite the prior-art `file:line` — `repository function: …`, `IPC endpoint: …`, `renderer hook: …`, `query key: …`. If the grounding subagents reported no analogous surface, say so explicitly. Inline prototype snippets when they pin a decision more precisely than prose (type shape, reducer, schema, query) — the decisive slice, not a demo.
- **Testing approach** — what makes a good test for this work (external behavior, not internals), which seams to test, prior art in the codebase. Name the same code path real users hit: if the listener attaches to `window`, dispatch on `window`; if a click traverses a button with `role`/`tabindex`, click that element. A test that fires synthetic events past the production seam is a **dead seam**. Steer the plan and implementer away from an **implementation-detail test** toward a behavior test driven through the seam. Where the work builds checkable logic — a transform, migration, parser, calculation — name the oracle (known-good examples, a naive reference implementation, a round-trip inverse, an invariant that must hold) so the plan can turn it into tests or **probes**. Size the suite here too: name the criteria that ride one **journey test** together, so the plan doesn't spec a sibling test per criterion, and every test this section calls for must pass the **rewrite test**. The plan slices the acceptance criteria into separate test-then-code cycles, so this section sets the bar each cycle's test must clear — it doesn't restate the criteria.
- **Refactor scope** (architecture-improvement specs only) — when the spec's goal *is* to change existing structure (deepen a module, consolidate, extract, re-seam), name the existing modules / files / boundaries that are intentionally in play, each with the `path` and one line on the reshape intended. This is the explicit allowlist that opens those modules to redesign downstream; anything not listed keeps its current boundary. Tests move with the seam: name the existing tests the reshape supersedes — the plan deletes them and writes new ones at the deepened interface, rather than layering new over old. Omit this section entirely for ordinary feature/fix specs.
- **Out of scope** — what was discussed and explicitly punted.

## Flow

### 1. Ground in the codebase

Read the repo's intent docs where they exist: `CONTEXT.md` (domain vocabulary the spec uses by name), ADRs (commonly `docs/adr/`, `docs/decisions/`), `DESIGN.md`, and the conventions section of `CLAUDE.md`/`AGENTS.md`. A tradeoff an ADR records is settled: Simplify first and the reviewer leave it alone. Code that has drifted from what an ADR says is an **Updates since spec** entry for the plan, since either the doc or the code is wrong — bank it as a grounding entry now; the spec has no section to hold it.

Read `.crank/<slug>/grounding.md` too, where it exists ([ARTIFACT-HOME.md](ARTIFACT-HOME.md) → Grounding), and verify-then-trust its entries: for a layer the file covers, prepend the covered entries to that layer's brief as previously-established facts to confirm at their citations, so its dispatch gap-fills and drift-checks instead of re-deriving — every layer still gets a dispatch, and a survey entry (canonical helper, convention winner, any absence) only narrows the re-search to its recorded scope.

Before drafting Technical decisions, dispatch standard subagents in parallel — one per layer the change touches (database, api, frontend, tests, etc.) — to find the existing surface in the codebase. Pass each one this brief verbatim:

<brief>
Investigate `<layer>` in this codebase. We're about to add `<one-sentence feature summary>`.

Find one or two existing features that do something analogous and report:

- the exact surface they use (database, api, frontend, tests, etc.);
- the `file:line` of that surface;
- one sentence on the convention you observed;
- any canonical helper or utility an implementer would be expected to reuse for this work (`file:line`), if one exists.

Don't propose a design — just surface what already exists. If no analogous surface exists, say so. When the analogous features disagree on convention, report both and name the winner: the one the repo converged on most recently, per `git log` on those files.
</brief>

Synthesize their findings into the Technical decisions section. The spec inherits the surfaces they reported. A spec that says "the handler calls `db.update(...)` directly" when the investigator found every analogous endpoint routes through `repo.X` has already shipped an idiom-break that code review will catch. Close the step by banking the per-layer findings — surfaces, conventions, canonical helpers, drift — to the grounding file.

Completion criterion: the intent docs are read or confirmed absent, and every layer the change touches has either a reported surface (`file:line`) or an explicit "no analogous surface" from its grounding subagent — fresh, or confirmed against the grounding file by that subagent — no layer unreported, and the step's findings banked to the grounding file.

### 2. Grill the technical decisions

Grounding tells you what already exists; grilling settles what's still open. After grounding, before you draft Technical decisions, list the technical decisions that are both **material** (they change the shape of the implementation) and **unsettled** (the conversation didn't land them and the grounding subagents didn't answer them).

Interview the user on each per [GRILLING.md](GRILLING.md) (read it here). This is targeted, not a fresh interview — only the open technical decisions, and only the ones the codebase can't answer for you. If the conversation came through the brainstorm phase (or the user handed you a brainstorm brief), the brief's **Open questions** list is your agenda — walk it. Resolve every material item before drafting: a decision you grill into the open now is one the adversarial reviewer and the plan don't have to re-litigate, and one less `Assumption:` line standing in for a real choice.

Facts are yours; decisions are the user's — if grounding found the surface, follow it.

When the user rejects a load-bearing recommendation for a reason a future spec would need in order not to re-propose it, offer to record it as an ADR in the repo; skip ephemeral reasons ("not now"). The `.crank/` artifacts are gitignored, so the ADR is the only place the rejection survives the effort.

Before declaring the frontier empty, walk the **failure catalogue** — check each item has a settled answer or a question in the round:

- **absence** — the stored resource is missing, deleted, or empty
- **permission family** — which sibling failures get the same treatment (EPERM beside EACCES)
- **staleness** — what events invalidate this state, and who refreshes it
- **destruction** — what user-owned content the operation touches, and what it must preserve
- **limits** — each threshold's value and check order, including the unbounded collection that needs a page size
- **interruption** — two callers at once, a retry after partial failure, a crash midway: what is idempotent, what is cleaned up, what is left half-written
- **trust boundary** — who may call this entry point, what it validates before acting, and which object access checks ownership

Each item lands as a grounded fact, a policy question in the round, or an acceptance criterion — *which* failures exist is a fact to enumerate (dispatch a subagent); only the policy call goes to the user, and the answer lands as an acceptance criterion so the plan's Coverage table forces a verify step for it.

Completion criterion: the frontier is empty — every material, unsettled decision has a user answer or a subagent-settled fact recorded, none carried into the draft as an implicit choice, and the failure catalogue walked, each item settled or asked.

### 3. Read back the sections

Grilling settled the decisions. Enumerate the acceptance criteria they imply — one per behavior, each falsifiable per **Deliverables** → Acceptance criteria — then read back per [SKILL.md](SKILL.md) → Phase gates, reading [READBACK.md](READBACK.md) here. The material to walk: the acceptance criteria as a numbered list, the judgment-call technical decisions, the scope cuts by name, and the incoming brief's **Open questions** — each read back as the sharp question it hands the spec.

Completion criterion: every settled behavior has a numbered criterion, and every criterion, judgment call, and cut has been read back and struck, amended, or approved.

### 4. Draft

Read [SPEC-TEMPLATE.md](SPEC-TEMPLATE.md), then write the spec to its `.crank/` file, section by section per **Deliverables**, scaled to the topic. Carry the material the readback approved into the spec as vetted (READBACK.md → Carry what was approved). Before locking **Technical decisions**, apply **Simplify first** (see Guidelines) and, for every module that is new or named in **Refactor scope**, [DESIGN-LENS.md](DESIGN-LENS.md) (read it here).

Completion criterion: every Deliverables section that applies is written to the spec file, no template placeholder survives, and every module new or in **Refactor scope** has been through Simplify first and the design lens.

### 5. Adversarially review

Read [SPEC-REVIEW-BRIEF.md](SPEC-REVIEW-BRIEF.md) and dispatch it per [SKILL.md](SKILL.md) → Phase gates, passing the spec's absolute path.

### 6. Hand back

The natural next step is the plan phase, which decomposes this spec into ordered, committable, TDD-flavored tasks. Hand off per [SKILL.md](SKILL.md) → Phase gates.

- **Next:** continue to the plan now — say "continue" and you'll read [PLAN.md](PLAN.md) and run its flow on the approved spec — or in a fresh session: `/crank plan .crank/<slug>/spec.md`.

Completion criterion: the path and resume command are stated and you've stopped — the plan phase loaded only on an explicit "continue".
