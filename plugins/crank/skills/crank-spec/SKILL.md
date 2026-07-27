---
name: crank-spec
description: Write up the conversation as a spec — part PRD, part technical spec — then adversarially review it in place. Use when the user asks to spec out or write up what you've been discussing.
argument-hint: "[optional topic hint]"
---

# Spec

## Goal

Turn what you and the user have been discussing, or the user's idea, into a single self-contained spec — part PRD (user-facing intent), part technical spec (decisions already settled).

## Hard Rules

- **Before drafting, grill the user on the open *technical* decisions** (see Flow → Grill the technical decisions) — material choices the conversation left unresolved that the codebase can't settle. Outside those, if a gap blocks the writeup, resolve it and note the assumption rather than reopening the interview.
- **Placeholder language.** No `TODO`, `TBD`, `for later`, `v2`, "we'll figure out later", or equivalent. If a decision is open: resolve it now (one targeted question or spawn a subagent to investigate), or move it to **Out of scope** with a sentence on why.
- **Every subagent this skill spawns runs at the standard tier** (see References → Subagents) unless otherwise specified.
- **Write the draft to a fresh OS temp file:** `$(mktemp -t crank-spec).md`. Do not write into the working directory unless the user explicitly asks. Tell the user the path once.
- **Reference real files as `path:line`** wherever you have them.

## Guidelines

- **Synthesize from the conversation; don't re-litigate what's settled.**

### Simplify first

Before locking Technical decisions, hunt for the re-framing that makes the change smaller — not the design that best organizes its complexity. The strongest version of a feature is often a natural extension of a module that already exists; prefer the design that deletes complexity over the one that rearranges it.

Treat each of these as a design problem to resolve in the spec, never a detail to leave for the implementer:

- **A one-off boolean, nullable mode, or special-case branch threaded through an existing flow.** Re-frame the state model so the branch disappears, or route the behavior behind the module that owns the concept.
- **Feature-specific logic landing in a shared path.** Move the ownership boundary so the feature becomes part of the module that owns the concept, instead of a check scattered through code that shouldn't know about it.
- **A near-duplicate of something the codebase already has.** Reuse the canonical helper the grounding subagents reported; a bespoke twin is architectural drift.
- **An interface that leans on optionality, casts, or silent fallbacks.** Make the invariant explicit instead — if a field is sometimes absent, the spec says when and why.

Working code that makes the surrounding code harder to reason about is a spec bug, not an implementation detail.

### Design lens

Apply to any module that is **new** (the grounding subagents reported no analogous surface) **or named in the Refactor scope** (an existing module the spec intends to reshape). For a module that merely extends existing prior art and isn't in the Refactor scope, follow the established pattern and skip this lens. For an in-scope module, before you name the chosen design:

- **Deletion test** (VOCABULARY.md). Run it on the module: if deleting it wouldn't scatter complexity across its callers, it's a pass-through — fold it into the caller and don't spec it as a module.
- **Design it twice.** Sketch the module two ways under *different binding constraints* so they genuinely diverge — e.g. one *minimize the interface*: 1–3 entry points, max capability each; the other *maximize flexibility*: let the caller compose the behavior. Pick the **deeper** one. Record the chosen shape, one sentence on why it beat the alternative, and one sentence on what it gives up (the alternative's strongest property). A second sketch that's a near-twin of the first means the constraint wasn't binding — re-sketch it.
- **Seam & dependencies.** Classify each dependency the module crosses: **in-process** (no seam — test through the interface directly), **local-substitutable** (test stand-in like PGLite/in-memory FS — internal seam), **remote-but-owned** or **true-external** (define a port at the seam; production adapter + test adapter).

<tradeoff>
**A port** buys swappability and a clean test seam — at the cost of an extra layer every reader must traverse. **Direct use** keeps the call path flat and obvious — at the cost of coupling tests to the real dependency. That second adapter is exactly what the **remote-but-owned** / **true-external** rows above buy you — outside them a single-adapter seam pays the indirection cost and buys nothing.
</tradeoff>

Keep the interface as the test surface (see Deliverables → Testing approach): the seam you name here is the one the tests drive.

## References

### Subagents

If exploring the codebase could answer a question — does this surface exist, what's the exact signature, is a claim you're about to write into the spec actually true — dispatch a standard subagent to find out rather than digging in your own context. Whether to dispatch or read on the main thread follows the shared default in [SUBAGENT-TIERS.md](SUBAGENT-TIERS.md) → Dispatch or main thread.

This skill spawns subagents at two tiers — resolve each to your harness (Claude Code / Codex / Cursor) per [SUBAGENT-TIERS.md](SUBAGENT-TIERS.md). **standard** = codebase grounding and exploration; **heavy** = the adversarial spec review. Set the tier explicitly on every spawn — never leave it to default.

### Vocabulary

Shared design language across the crank pipeline, defined once in [VOCABULARY.md](VOCABULARY.md). This skill leans on **module**, **interface**, **depth** (**leverage** / **locality**), the **deletion test**, **seam**, **port** / **adapter**, and the **implementation-detail test** — read their meanings there.

### Spec skeleton

The compact markdown skeleton lives in [SPEC-TEMPLATE.md](SPEC-TEMPLATE.md); Flow → Draft uses it as the starting shape, then scales or omits sections per Deliverables.

### Adversarial review brief

The heavy review prompt lives in [SPEC-REVIEW-BRIEF.md](SPEC-REVIEW-BRIEF.md); Flow → Adversarially review loads it only at that step.

## Deliverables

A single self-contained spec written to the temp file (see Hard Rules). Include whichever sections apply, scaled to the topic (a bug fix is 20 lines; a new subsystem is denser):

- **Problem** — what the user is trying to solve, in their words.
- **Solution** — the proposed change, in user-facing terms.
- **User stories** — `As an <actor>, I want <feature>, so that <benefit>`, when distinct actors or user goals clarify the scope. Omit for small bugs, internal refactors, or technical changes where the real contract is the acceptance criteria plus Technical decisions.
- **Acceptance criteria** — a numbered list of independently checkable statements, one per behavior: every interaction, keybinding, alias, edge case, state transition, and validation. Each criterion must be falsifiable by an agent or a named human smoke check — "works correctly" is not a criterion; "pressing `Esc` closes the dialog without saving" is. This list is the contract the plan's Coverage table and execute's final review key off: a behavior not listed here is invisible to every downstream check.
- **Technical decisions** — every architecturally-meaningful call landed on: modules touched, interfaces, schemas, data flow, dependencies (pinned), failure modes. Name the chosen option and one sentence on why; when a real alternative was on the table, also name what the chosen option gives up — a decision recorded with only its upside reads as unexamined and invites re-litigating. For each layer touched (DB, IPC, renderer state, renderer queries), name the existing surface the change goes through and cite the prior-art `file:line` — `repository function: …`, `IPC endpoint: …`, `renderer hook: …`, `query key: …`. If the grounding subagents reported no analogous surface, say so explicitly. Inline prototype snippets when they pin a decision more precisely than prose (type shape, reducer, schema, query) — the decisive slice, not a demo.
- **Testing approach** — what makes a good test for this work (external behavior, not internals), which seams to test, prior art in the codebase. Name the same code path real users hit: if the listener attaches to `window`, dispatch on `window`; if a click traverses a button with `role`/`tabindex`, click that element. A test that fires synthetic events past the production seam is a dead feature in disguise. Steer the plan and implementer away from an **implementation-detail test** (defined in VOCABULARY.md) toward a behavior test driven through the seam. The plan slices the acceptance criteria into separate test-then-code cycles, so this section sets the bar each cycle's test must clear — it doesn't restate the criteria.
- **Refactor scope** (architecture-improvement specs only) — when the spec's goal *is* to change existing structure (deepen a module, consolidate, extract, re-seam), name the existing modules / files / boundaries that are intentionally in play, each with the `path` and one line on the reshape intended. This is the explicit allowlist that opens those modules to redesign downstream; anything not listed keeps its current boundary. Tests move with the seam: name the existing tests the reshape supersedes — the plan deletes them and writes new ones at the deepened interface, rather than layering new over old. Omit this section entirely for ordinary feature/fix specs.
- **Out of scope** — what was discussed and explicitly punted.

## Flow

Create a task for each step below and mark each one complete as you finish it — update them live as you go, not in a batch at the end — so the user can watch progress.

### 1. Ground in the codebase

Before drafting Technical decisions, dispatch standard subagents in parallel — one per layer the change touches (database, api, frontend, tests, etc.) — to find the existing surface in the codebase. Pass each one this brief verbatim:

<brief>
Investigate `<layer>` in this codebase. We're about to add `<one-sentence feature summary>`.

Find one or two existing features that do something analogous and report:

- the exact surface they use (database, api, frontend, tests, etc.);
- the `file:line` of that surface;
- one sentence on the convention you observed;
- any canonical helper or utility an implementer would be expected to reuse for this work (`file:line`), if one exists.

Don't propose a design — just surface what already exists. If no analogous surface exists, say so.
</brief>

Synthesize their findings into the Technical decisions section. The spec inherits the surfaces they reported. A spec that says "the handler calls `db.update(...)` directly" when the investigator found every analogous endpoint routes through `repo.X` has already shipped an idiom-break that code review will catch.

Completion criterion: every layer the change touches has either a reported surface (`file:line`) or an explicit "no analogous surface" from its grounding subagent — no layer unreported.

### 2. Grill the technical decisions

Grounding tells you what already exists; grilling settles what's still open. After grounding, before you draft Technical decisions, list the technical decisions that are both **material** (they change the shape of the implementation) and **unsettled** (the conversation didn't land them and the grounding subagents didn't answer them).

Interview the user on each, one question at a time — exactly one question mark per message; a sub-question, clarifier, or "and also…" rider is the *next* message, sent after this answer lands. Ask in plain chat text — not the structured-question UI, so you have room to show your reasoning. Lead with your recommended answer and the trade-off it accepts, and wait for the response before the next question. Offer discrete options to frame a genuine choice, never as a neutral menu — your pick still leads.

This is targeted, not a fresh interview — only the open technical decisions, and only the ones the codebase can't answer for you. Explore first: if a subagent can settle a question, dispatch one (see References → Subagents) rather than spending the user's attention on it. If the conversation came through `crank:crank-brainstorm`, the brief's **Open questions** list is your agenda — walk it. Resolve every material item before drafting: a decision you grill into the open now is one the adversarial reviewer and the plan don't have to re-litigate, and one less `Assumption:` line standing in for a real choice.

Don't re-open decisions the conversation already settled, and don't grill on detail the chosen idiom dictates — if grounding found the surface, follow it. Grill where the call is genuinely the user's: a trade-off between viable options, a constraint only they know, a priority that tips the design.

Completion criterion: every material, unsettled decision on your list has a user answer or a subagent-settled fact recorded — none carried into the draft as an implicit choice.

### 3. Read back the sections

Grilling settled the decisions; before any of them hardens into a draft, read them back — the content itself, not a table of contents. Open with what the spec commits to, what's explicitly out of scope, and which questions remain open — those are what the user vetoes. Then walk the spec-to-be one Deliverables section per message, pausing after each so the user can question, refute, or change it, and fold each change in before the next.

- Show each section's actual content — the acceptance criteria as a numbered list, each technical decision with its one-line why, the scope cuts by name — material the user can strike or amend line by line, not finished prose.
- Where an interface, data flow, or piece of logic is easier to veto in picture form, show it as pseudo-code, a call graph, or a small plain-text diagram (ASCII; chat renders mermaid as raw text).
- The test for each message: could the user veto a specific item from it? If all they can say is "sounds good", you've sent a summary, not a readback.

A change caught in the readback costs a sentence; the same change after drafting re-litigates the draft and the review.

Completion criterion: every section the draft will contain has had its actual content read back — one section per message — and user-approved section by section; objections resolved now, none carried into the draft.

### 4. Draft

Read [SPEC-TEMPLATE.md](SPEC-TEMPLATE.md), then write the spec to the temp file, section by section per **Deliverables**, scaled to the topic. Carry any pseudo-code, call graph, or diagram the user approved during readback into the spec — the plan inherits the exact shape that was vetted, not a prose paraphrase of it. Before locking **Technical decisions**, apply the **Simplify first** and **Design lens** guidelines (see Guidelines) to every in-scope module.

Completion criterion: every Deliverables section that applies is written to the temp file, no template placeholder survives, and every in-scope module has been through both guidelines.

### 5. Adversarially review

Read [SPEC-REVIEW-BRIEF.md](SPEC-REVIEW-BRIEF.md). Spawn one heavy subagent resolved per [SUBAGENT-TIERS.md](SUBAGENT-TIERS.md) and pass it the spec's absolute path plus the brief verbatim.

Quote the reviewer's summary line back to the user.

Completion criterion: the reviewer's edits are in the spec file and its one-line summary is quoted back to the user.

### 6. Hand back

In chat prose, offer:

- **Keep the temp file** (default) — the path is already known; user can hand it to the plan skill, feed it elsewhere, or move it later.
- **Copy into the repo** — copy to a user-named path under the working directory.
- **Print inline and delete** — paste the final contents into the chat and remove the temp file.

Then stop. Do not auto-invoke other skills or continue past the handback.

Completion criterion: the user picked from the file menu and you did exactly what they picked — nothing invoked they didn't opt into.
