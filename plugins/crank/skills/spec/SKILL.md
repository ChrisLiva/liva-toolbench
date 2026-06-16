---
name: spec
description: Synthesize the current conversation — grilling, brainstorming, prototyping — into one document that is part PRD, part technical spec, then adversarially review it in place. Use when the user asks to write up what you've been discussing.
argument-hint: "[optional topic hint]"
---

# Spec

Turn what you and the user have been discussing into a single self-contained spec — part PRD (user-facing intent), part technical spec (decisions already settled).

<subagent-tiers>
This skill delegates work to subagents at two capability tiers. Where the body says to spawn a **standard** or **heavy** subagent, resolve the tier for the harness you are running in:

- **Claude Code** — spawn via the `Agent` tool and set `model` per tier: standard → `model: sonnet`, heavy → `model: opus`. Set per spawn; nothing else to configure.
- **Codex** — spawn a subagent and set its reasoning effort per tier on `gpt-5.5`: standard → `medium`, heavy → `high`. Set per spawn; nothing else to configure.

Tier intent (harness-independent): **standard** = bulk work — codebase grounding, exploration, per-task review. **heavy** = work that rewards the strongest reasoning — spec drafting, adversarial review, final cross-task review.
</subagent-tiers>

<rules>
- **Synthesize from the conversation; do not restart the interview.** If a real gap blocks the writeup, ask one targeted question; otherwise resolve it and note the assumption in the doc.
- **No placeholder language.** No `TODO`, `TBD`, `for later`, `v2`, "we'll figure out later", or equivalent. If a decision is open: resolve it now (one targeted question), or move it to **Out of scope** with a sentence on why.
- **Every subagent this skill spawns runs at the standard tier** (see <subagent-tiers>) unless otherwise specified.
- **Write the draft to a fresh OS temp file:** `$(mktemp -t crank-spec).md`. Do not write into the working directory unless the user explicitly asks. Tell the user the path once.
- **Reference real files as `path:line`** wherever you have them.
</rules>

## Subagents

If exploring the codebase could answer a question — does this surface exist, what's the exact signature, is a claim you're about to write into the spec actually true — dispatch a standard subagent to find out rather than digging in your own context.

<tradeoff>
**Dispatching** keeps your context clean for synthesis and lets explorations run in parallel — at the cost of dispatch latency and a subagent that lacks the conversation's nuance. **Main-thread reading** keeps that nuance and is faster for a single lookup — at the cost of filling your window with source you'll never need again. Default: a one-symbol lookup in a known file, do yourself; anything wider, dispatch.
</tradeoff>

## Vocabulary

Shared design language across the crank skills (spec → plan → execute). Use these terms with these meanings:

- **Module** — anything with an interface and an implementation: a function, class, file, or larger slice.
- **Interface** — the full contract a caller must understand: signatures, invariants, ordering, errors, config.
- **Depth** — how much an interface hides. A **deep** module exposes a small interface over substantial behavior; a **shallow** one exposes nearly as much as it hides. Depth lives in the interface, not the implementation — a deep module may be built of many small internal parts, so long as they don't show through.
- **Leverage / locality** — the two payoffs of depth. Callers get **leverage**: more behavior per unit of interface they must learn. Maintainers get **locality**: change, bugs, and knowledge concentrate in one place instead of spreading across callers. Use these words when recording why a chosen design beat its alternative.
- **Deletion test** — imagine the module gone. If its complexity simply vanishes, it was a pass-through; if that complexity reappears across many callers, the boundary earned its place.
- **Seam** — a place where behavior can be swapped without editing in that place; the location of an interface, and the surface tests drive (the production node/endpoint/entry point a real user reaches, never a synthetic stand-in).
- **Port / adapter** — a seam that crosses a dependency: the **port** is the interface, an **adapter** is a concrete fill (production HTTP/db vs. in-memory test double). Two adapters justify a port; one is just indirection.

## Workflow

Create a task for each step below and mark each one complete as you finish it — update them live as you go, not in a batch at the end — so the user can watch progress:

- Ground in the codebase first (parallel standard subagents, one per layer)
- Draft (sections scaled to topic, design lens on in-scope modules)
- Adversarially review (subagent edits the file in place)
- Hand back

## Ground in the codebase first

Before drafting Technical decisions, dispatch standard subagents in parallel — one per layer the change touches (database, api, frontend, tests, etc.) — to find the existing surface in the codebase. Pass each one this brief verbatim:

<brief>
Investigate `<layer>` in this codebase. We're about to add `<one-sentence feature summary>`. Find one or two existing features that do something analogous and report: the exact surface they use (database, api, frontend, tests, etc.), the `file:line` of that surface, and one sentence on the convention you observed. Also report any canonical helper or utility an implementer would be expected to reuse for this work (`file:line`), if one exists. Don't propose a design — just surface what already exists. If no analogous surface exists, say so.
</brief>

Synthesize their findings into the Technical decisions section. The spec inherits the surfaces they reported. A spec that says "the handler calls `db.update(...)` directly" when the investigator found every analogous endpoint routes through `repo.X` has already shipped an idiom-break that code review will catch.

## Draft

Include whichever sections apply, scaled to the topic (a bug fix is 20 lines; a new subsystem is denser):

- **Problem** — what the user is trying to solve, in their words.
- **Solution** — the proposed change, in user-facing terms.
- **User stories** — `As an <actor>, I want <feature>, so that <benefit>`. Exhaustive within the scope discussed.
- **Acceptance criteria** — a numbered list of independently checkable statements, one per behavior: every interaction, keybinding, alias, edge case, state transition, and validation. Each criterion must be falsifiable by an agent or a named human smoke check — "works correctly" is not a criterion; "pressing `Esc` closes the dialog without saving" is. This list is the contract the plan's Coverage table and execute's final review key off: a behavior not listed here is invisible to every downstream check.
- **Technical decisions** — every architecturally-meaningful call landed on: modules touched, interfaces, schemas, data flow, dependencies (pinned), failure modes. Name the chosen option and one sentence on why; when a real alternative was on the table, also name what the chosen option gives up — a decision recorded with only its upside reads as unexamined and invites relitigating. For each layer touched (DB, IPC, renderer state, renderer queries), name the existing surface the change goes through and cite the prior-art `file:line` — `repository function: …`, `IPC endpoint: …`, `renderer hook: …`, `query key: …`. If the grounding subagents reported no analogous surface, say so explicitly. Inline prototype snippets when they pin a decision more precisely than prose (type shape, reducer, schema, query) — the decisive slice, not a demo.
- **Testing approach** — what makes a good test for this work (external behavior, not internals), which seams to test, prior art in the codebase. Name the same code path real users hit: if the listener attaches to `window`, dispatch on `window`; if a click traverses a button with `role`/`tabindex`, click that element. A test that fires synthetic events past the production seam is a dead feature in disguise.
- **Refactor scope** (architecture-improvement specs only) — when the spec's goal *is* to change existing structure (deepen a module, consolidate, extract, re-seam), name the existing modules / files / boundaries that are intentionally in play, each with the `path` and one line on the reshape intended. This is the explicit allowlist that opens those modules to redesign downstream; anything not listed keeps its current boundary. Tests move with the seam: name the existing tests the reshape supersedes — the plan deletes them and writes new ones at the deepened interface, rather than layering new over old. Omit this section entirely for ordinary feature/fix specs.
- **Out of scope** — what was discussed and explicitly punted.

### Simplify first

Before locking Technical decisions, hunt for the reframing that makes the change smaller — not the design that best organizes its complexity. The strongest version of a feature is often a natural extension of a module that already exists, where branches, modes, and layers disappear instead of accumulating. Prefer the design that deletes complexity over the one that rearranges it.

Treat each of these as a design problem to resolve in the spec, never a detail to leave for the implementer:

- **A one-off boolean, nullable mode, or special-case branch threaded through an existing flow.** Reframe the state model so the branch disappears, or route the behavior behind the module that owns the concept.
- **Feature-specific logic landing in a shared path.** Move the ownership boundary so the feature becomes part of the module that owns the concept, instead of a check scattered through code that shouldn't know about it.
- **A near-duplicate of something the codebase already has.** Reuse the canonical helper the grounding subagents reported; a bespoke twin is architectural drift.
- **An interface that leans on optionality, casts, or silent fallbacks.** Make the invariant explicit instead — if a field is sometimes absent, the spec says when and why.

Working code that makes the surrounding code harder to reason about is a spec bug, not an implementation detail.

### Design lens

Apply to any module that is **new** (the grounding subagents reported no analogous surface) **or named in the Refactor scope** (an existing module the spec intends to reshape). For a module that merely extends existing prior art and isn't in the Refactor scope, follow the established pattern and skip this lens. For an in-scope module, before you name the chosen design:

- **Deletion test.** Imagine the new module gone. If its complexity simply vanishes, it's a pass-through — fold it into its caller and don't spec it as a module. It earns a boundary only if deleting it would scatter that complexity across many callers.
- **Design it twice.** Sketch one *radically different* interface for the module (fewer entry points vs. more flexibility; data-in/data-out vs. injected behavior) and pick the deeper one — more capability behind a smaller interface. Record the chosen shape, one sentence on why it beat the alternative, and one sentence on what it gives up (the alternative's strongest property).
- **Seam & dependencies.** Classify each dependency the module crosses: **in-process** (no seam — test through the interface directly), **local-substitutable** (test stand-in like PGLite/in-memory FS — internal seam), **remote-but-owned** or **true-external** (define a port at the seam; production adapter + test adapter).

<tradeoff>
**A port** buys swappability and a clean test seam — at the cost of an extra layer every reader must traverse. **Direct use** keeps the call path flat and obvious — at the cost of coupling tests to the real dependency. Only introduce a port when two adapters are actually justified (typically production + test); a single-adapter seam pays the indirection cost and buys nothing.
</tradeoff>

Keep the interface as the test surface (see Testing approach): the seam you name here is the one the tests drive.

## Adversarially review

Spawn one heavy subagent via the `Agent` tool (`description: "Adversarial spec review"`) and pass it the spec's absolute path. Pass this brief verbatim:

<brief>
Read the spec at `<path>`. Flag every instance of: **ambiguity** (two engineers could implement it meaningfully differently), **inaccuracy** (a claim that contradicts the codebase — verify against the repo), **criteria gaps** (a behavior the spec body describes — interaction, keybinding, edge case, state transition, validation — with no matching numbered acceptance criterion, or a criterion too vague to falsify), **off-pattern** (a layer is touched without naming the existing surface for that layer — repository function, renderer hook, query key, IPC shape — that analogous features in the codebase use; grep one or two analogous files to confirm), **shallow module** (a module that is *new* or named in the spec's **Refactor scope**, whose interface is nearly as complex as its implementation, or that fails the deletion test: removing it would not scatter complexity, so it's a pass-through that should fold into its caller — don't flag existing modules outside the Refactor scope, their boundaries are settled), **missed simplification** (complexity the spec itself introduces — a new mode, flag, wrapper, or special-case branch in an existing flow — where a reframing would let an existing module absorb the behavior; flag only when you can name the simpler shape, and don't flag a decision the spec records with its tradeoff), **bespoke duplication** (the spec designs a helper or utility the codebase already provides — grep to confirm, and name the canonical one), **boundary smells** (a specified interface relies on optionality, casts, `any`, or silent fallbacks where the invariant could be explicit), **placeholder language** (`TODO` / `TBD` / `for later` / `v2` / anything punting a decision the spec should have resolved), and **missing technical detail** that would block an implementer. Don't re-open settled decisions. Then edit the file in place to fix what you flagged: tighten ambiguous language, correct inaccuracies, add or sharpen acceptance criteria for any criteria gap, name the surface and `file:line` for any off-pattern flag, rewrite a missed simplification to the simpler shape you named, replace bespoke duplications with the canonical helper, make the invariant explicit for any boundary smell, resolve placeholders or move them to **Out of scope**, fill in missing detail. End your reply with a one-line summary of what changed.
</brief>

Quote the reviewer's summary line back to the user.

## Hand back

First render an interactive HTML review of the final spec and open it in the user's browser; then offer the file menu.

**Open the review.** Read the rendering guide in this skill's directory — [HTML-REVIEW.md](HTML-REVIEW.md) — then follow it to render the spec as the `.html` sibling of the temp file and open it — give each acceptance criterion its own comment box. Tell the user the HTML path and that they can comment per section, tick any out-of-scope cut that should be in, hit **Export comments →**, and paste the block back — you'll apply it to the spec and re-render. (Under `/crank`/headless the whole Hand back step is skipped, so the browser never opens mid-pipeline.)

In chat prose, offer:

- **Keep the temp file** (default) — the path is already known; user can hand it to the plan skill, feed it elsewhere, or move it later.
- **Copy into the repo** — copy to a user-named path under the working directory.
- **Print inline and delete** — paste the final contents into the chat and remove the temp file (and its `.html` sibling).

When the user pastes a block beginning `> Source: <path>`, apply each `## <heading>` comment to that markdown and resolve every `Out of scope → requested IN scope` item (fold it into the spec as a real acceptance criterion / decision, or push back with a reason — never drop it silently), then re-render the HTML and reopen it. See HTML-REVIEW.md's "Applying a pasted review."

Then stop. Do not auto-invoke other skills or continue past the handback.
