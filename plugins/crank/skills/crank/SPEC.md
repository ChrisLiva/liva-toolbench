# Phase: Spec

## Goal

Turn the conversation so far, or the user's idea, into a single self-contained spec — part PRD (user-facing intent), part technical spec (settled decisions).

## Hard Rules

- **Grill the open technical decisions before drafting** (Flow → Grill the technical decisions). Outside those, resolve a gap that blocks the writeup and note the assumption rather than reopening the interview.
- **Placeholder language.** No `TODO`, `TBD`, `for later`, `v2`, "we'll figure out later", or equivalent. Resolve an open decision now (one targeted question or a subagent), or move it to **Out of scope** with a sentence on why.
- **Write the draft to `.crank/<slug>/spec.md`** per [ARTIFACT-HOME.md](ARTIFACT-HOME.md) — read it first.
- **Cite what you assert.** Every claim about code as it stands — a path, a signature, a type, a fixture, a digest, a protocol's behavior, a value pinned as an oracle — is **confirmed**: opened or run this phase, inside this repo or outside it, and carries its `path:line` or the command and what it printed. An oracle names what produced it and whether that matches the construction the spec mandates. A claim you cannot confirm this phase moves to **Out of scope** with the check that would settle it.

## Guidelines

### Simplify first

Hunt for the re-framing that makes the change smaller — not the design that best organizes its complexity. The strongest version of a feature is often a natural extension of an existing module.

Treat each of these as a design problem the spec resolves, never one left to the implementer; working code that makes the surrounding code harder to reason about is a spec bug:

- **Spaghetti growth the spec would introduce.** Re-frame the state model so the branch disappears, or route the behavior behind the module that owns the concept.
- **Feature-specific logic landing in a shared path.** Move the ownership boundary so the feature lives in the module that owns the concept, not in checks scattered through code that shouldn't know about it.
- **A near-duplicate of something the codebase already has.** Reuse the canonical helper the grounding subagents reported; a bespoke twin is architectural drift.
- **Make impossible states unrepresentable.** An interface that leans on optionality, casts, or silent fallbacks hides an invariant; make it explicit — if a field is sometimes absent, the spec says when and why.

## References

Read [SUBAGENT-TIERS.md](SUBAGENT-TIERS.md) and [VOCABULARY.md](VOCABULARY.md) together in one turn, before step 1.

### Subagents

This phase dispatches **standard** subagents for what the codebase can answer: whether a surface exists, its exact signature, whether a claim you're about to write is true. The adversarial review is its only **heavy** dispatch. Resolve each tier, and the dispatch-or-main-thread call, per [SUBAGENT-TIERS.md](SUBAGENT-TIERS.md) → Dispatch or main thread: a loaded instruction file's preference first, its harness models only as the fallback.

### Vocabulary

[VOCABULARY.md](VOCABULARY.md) — both sections; this phase uses its terms bare.

## Deliverables

The spec file named in Hard Rules, with whichever sections apply, scaled to the topic (a bug fix stays terse; a new subsystem is denser):

- **Header** — title, then `Grounding:` per [ARTIFACT-HOME.md](ARTIFACT-HOME.md) → Grounding.
- **Problem** — what the user is trying to solve, in their words.
- **Solution** — the proposed change, in user-facing terms.
- **User stories** — `As an <actor>, I want <feature>, so that <benefit>`, when distinct actors or user goals clarify the scope. Omit for small bugs, internal refactors, or technical changes, where the acceptance criteria plus Technical decisions are the contract.
- **Acceptance criteria** — a numbered list of independently checkable statements, one per behavior: every interaction, keybinding, alias, edge case, state transition, and validation. Each must be falsifiable by an agent or a named human smoke check — "works correctly" is not a criterion; "pressing `Esc` closes the dialog without saving" is. The plan's Coverage table and execute's final review key off this list: a behavior missing here is invisible to every downstream check.
- **Technical decisions** — every architecturally-meaningful call: modules touched, interfaces, schemas, data flow, dependencies (pinned), failure modes. Name the chosen option and one sentence on why; when a real alternative was on the table, also name what the choice gives up, or the decision reads as unexamined and invites re-litigating. For each layer touched (DB, IPC, renderer state, renderer queries), name the existing surface the change goes through with its prior-art `file:line` — `repository function: …`, `IPC endpoint: …`, `renderer hook: …`, `query key: …`. Where grounding found none, say so explicitly. Inline prototype snippets when they pin a decision more precisely than prose (type shape, reducer, schema, query) — the decisive slice, not a demo.
- **Testing approach** — what makes a good test for this work (external behavior, not internals), which **seams** to test, prior art in the codebase. Name the same code path real users hit: if the listener attaches to `window`, dispatch on `window`; if a click traverses a button with `role`/`tabindex`, click that element. A test that fires past the production seam is a **dead seam**; one coupled to internals is an **implementation-detail test**. Where the work builds checkable logic — a transform, migration, parser, calculation — name the **oracle** so the plan can turn it into tests or **probes**. Size the suite: name the criteria that ride one **journey test** together; every test this section calls for must pass the **rewrite test**. This section sets the bar each test-then-code cycle's test must clear; it doesn't restate the criteria, which the plan slices into those cycles.
- **Refactor scope** (only when the spec's goal *is* to change existing structure: deepen a module, consolidate, extract, re-seam) — name each module, file, or boundary in play, with its `path` and one line on the intended reshape. This is the explicit allowlist that opens those modules to redesign downstream; anything not listed keeps its current boundary. Tests move with the seam: name the existing tests the reshape supersedes, which the plan deletes and replaces at the deepened interface rather than layering new over old. Omit this section otherwise.
- **Out of scope** — what was discussed and explicitly punted.

## Flow

### 1. Ground in the codebase

Read the repo's intent docs where they exist: `CONTEXT.md` (domain vocabulary the spec uses by name), ADRs (commonly `docs/adr/`, `docs/decisions/`), `DESIGN.md`, and the conventions section of `CLAUDE.md`/`AGENTS.md`. Code that has drifted from an ADR is an **Updates since spec** entry for the plan, since either the doc or the code is wrong. Bank it as a grounding entry now; the spec has no section to hold it.

Read `.crank/<slug>/grounding.md` too, where it exists, and verify-then-trust its entries ([ARTIFACT-HOME.md](ARTIFACT-HOME.md) → Grounding): prepend the entries that cover a layer to that layer's brief as facts to confirm at their citations, so its dispatch gap-fills and drift-checks instead of re-deriving — every layer still gets a dispatch.

Dispatch standard subagents in parallel, one per layer the change touches (database, api, frontend, tests, etc.), to find the existing surface. Pass each one this brief verbatim:

<brief>
Investigate `<layer>` in this codebase. We're about to add `<one-sentence feature summary>`.

Work your lookups in **rounds**: a round's **frontier** is every read or grep whose answer you do not need before issuing the next one; send the whole frontier as one batch in a single turn, read every return, then compose the next round from what came back.

Find one or two existing features that do something analogous and report:

- the exact surface they use;
- the `file:line` of that surface;
- one sentence on the convention you observed;
- any canonical helper an implementer should reuse for this work (`file:line`), if one exists.

Report each item — one surface, one convention note, one helper — in a few sentences. Cite `file:line` instead of pasting the code around it, and quote source only where the exact text is the answer. An exact signature is the answer: reproduce it in full, however long. An item that outgrows a few sentences goes to a file in the OS temp dir, returned as its path plus a one-line summary.

Don't propose a design; just surface what already exists. If no analogous surface exists, say so. When the analogous features disagree on convention, report both and name the winner: the one the repo converged on most recently, per `git log` on those files.
</brief>

Synthesize their findings into Technical decisions; the spec inherits the surfaces they reported. A spec that has the handler call `db.update(...)` directly when every analogous endpoint routes through `repo.X` has shipped an idiom-break.

Completion criterion: the intent docs are read or confirmed absent, each ADR banked to grounding with its path as governing, superseded, or irrelevant to this spec; every layer the change touches has a reported surface (`file:line`) or an explicit "no analogous surface" from its grounding subagent, fresh or confirmed by that subagent; and the step's findings are banked to the grounding file, including each layer's surfaces, conventions, canonical helpers, and drift.

### 2. Grill the technical decisions

List the technical decisions that are both **material** (they change the shape of the implementation) and **unsettled** (neither the conversation nor the grounding subagents landed them).

**Offer a prototype before the prose questions.** When a round would ask a layout, hierarchy, or interaction question with more than one defensible answer, about a page, screen, component, CLI output, flags, help text, or TUI the change adds or reshapes, lead that round with a prototype offer, 3 to 5 variants behind one switcher, in place of the question, once per effort. When `.crank/<slug>/prototype/` already holds files, offer to reopen them in place of a build. On a yes, read [PROTOTYPE.md](PROTOTYPE.md) and follow it, and its verdict replaces those questions. On a no, record `Prototype: declined` in Technical decisions.

Interview the user on each per [GRILLING.md](GRILLING.md) (read it here): a targeted round on only what the codebase can't answer, not a fresh interview. When a brainstorm brief came in, its **Open questions** list is your agenda; walk it. Resolve every material item: one left open becomes an `Assumption:` line downstream re-litigates.

When the user rejects a load-bearing recommendation for a reason a future spec would need to avoid re-proposing it, offer to record it as an ADR in the repo; skip ephemeral reasons ("not now"). The `.crank/` artifacts are gitignored, so only an ADR carries the rejection past the effort.

Before declaring the frontier empty, walk the **failure catalogue**, giving each item a settled answer or a question in the round:

- **absence** — the stored resource is missing, deleted, or empty
- **permission family** — which sibling failures get the same treatment (EPERM beside EACCES)
- **staleness** — what events invalidate this state, and who refreshes it
- **destruction** — what user-owned content the operation touches, and what it must preserve
- **limits** — each threshold's value and check order, including the unbounded collection that needs a page size
- **interruption** — two callers at once, a retry after partial failure, a crash midway: what is idempotent, what is cleaned up, what is left half-written
- **trust boundary** — who may call this entry point, what it validates before acting, and which object access checks ownership

*Which* failures exist is a fact to enumerate (dispatch a subagent); only the policy call goes to the user, and the answer lands as an acceptance criterion so the plan's Coverage table forces a verify step for it.

Completion criterion: the frontier is empty — every material, unsettled decision has a user answer or a subagent-settled fact, and the failure catalogue is walked, each item settled or asked.

### 3. Read back the sections

Grilling settled the decisions. Enumerate the acceptance criteria they imply — one per behavior, each falsifiable per **Deliverables** → Acceptance criteria — then read back per [SKILL.md](SKILL.md) → Phase gates, reading [READBACK.md](READBACK.md) here. The material to walk: the acceptance criteria as a numbered list, the judgment-call technical decisions, the scope cuts by name, and the answer grilling landed for each of the incoming brief's **Open questions**.

Completion criterion: every settled behavior has a numbered criterion, and every criterion, judgment call, and cut has been read back and struck, amended, or approved.

### 4. Draft

Read [SPEC-TEMPLATE.md](SPEC-TEMPLATE.md), then write the spec to its `.crank/` file, section by section per **Deliverables**, scaled to the topic. Carry the material the readback approved into the spec as vetted (READBACK.md → Carry what was approved). Before locking **Technical decisions**, apply **Simplify first** (see Guidelines) and, for every module that is new or named in **Refactor scope**, [DESIGN-LENS.md](DESIGN-LENS.md) (read it here).

Completion criterion: every Deliverables section that applies is written to the spec file, no template placeholder survives, every claim about existing code is confirmed per Hard Rules → Cite what you assert, and every module new or in **Refactor scope** has been through Simplify first and the design lens.

### 5. Adversarially review

Read [SPEC-REVIEW-BRIEF.md](SPEC-REVIEW-BRIEF.md) and dispatch it per [SKILL.md](SKILL.md) → Phase gates, passing the spec's absolute path. Then read back, in one message per [READBACK.md](READBACK.md), every numbered acceptance criterion the review rewrote, since the user approved those at step 3, and in that same message every decision READBACK.md → Carry what was approved names.

### 6. Hand back

Hand off per [SKILL.md](SKILL.md) → Phase gates.

- **Next:** continue to the plan now — say "continue" and you'll read [PLAN.md](PLAN.md) and run its flow on the approved spec — or in a fresh session: `/crank plan .crank/<slug>/spec.md`.
