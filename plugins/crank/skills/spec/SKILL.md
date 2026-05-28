---
name: spec
description: Synthesize the current conversation — grilling, brainstorming, prototyping — into one document that is part PRD, part technical spec, then adversarially review it in place. Use when the user types /spec or asks to write up what you've been discussing.
argument-hint: "[optional topic hint]"
---

# Spec

Turn what you and the user have been discussing into a single self-contained spec — part PRD (user-facing intent), part technical spec (decisions already settled). **Synthesize from the conversation; do not restart the interview.** If a real gap blocks the writeup, ask one targeted question; otherwise resolve it and note the assumption in the doc.

## Vocabulary

Shared design language across the crank skills (spec → plan → execute). Use these terms with these meanings:

- **Module** — anything with an interface and an implementation: a function, class, file, or larger slice.
- **Interface** — the full contract a caller must understand: signatures, invariants, ordering, errors, config.
- **Depth** — how much an interface hides. A **deep** module exposes a small interface over substantial behavior; a **shallow** one exposes nearly as much as it hides.
- **Deletion test** — imagine the module gone. If its complexity simply vanishes, it was a pass-through; if that complexity reappears across many callers, the boundary earned its place.
- **Seam** — a place where behavior can be swapped without editing in that place; the location of an interface, and the surface tests drive (the production node/endpoint/entry point a real user reaches, never a synthetic stand-in).
- **Port / adapter** — a seam that crosses a dependency: the **port** is the interface, an **adapter** is a concrete fill (production HTTP/db vs. in-memory test double). Two adapters justify a port; one is just indirection.

## Ground in the codebase first

Before drafting Technical decisions, dispatch subagents in parallel — one per layer the change touches (database, api, frontend, tests, etc.) — to find the existing surface in the codebase. Brief each subagent verbatim:

> Investigate `<layer>` in this codebase. We're about to add `<one-sentence feature summary>`. Find one or two existing features that do something analogous and report: the exact surface they use (database, api, frontend, tests, etc.), the `file:line` of that surface, and one sentence on the convention you observed. Don't propose a design — just surface what already exists. If no analogous surface exists, say so.

Synthesize their findings into the Technical decisions section. The spec inherits the surfaces they reported. A spec that says "the handler calls `db.update(...)` directly" when the investigator found every analogous endpoint routes through `repo.X` has already shipped an idiom-break that code review will catch.

## Draft

Write the draft to a fresh OS temp file: `$(mktemp -t crank-spec).md`. Do not write into the working directory unless the user explicitly asks. Tell the user the path once.

Suggested sections — include whichever apply, scaled to the topic (a bug fix is 20 lines; a new subsystem is denser):

- **Problem** — what the user is trying to solve, in their words.
- **Solution** — the proposed change, in user-facing terms.
- **User stories** — `As an <actor>, I want <feature>, so that <benefit>`. Exhaustive within the scope discussed.
- **Technical decisions** — every architecturally-meaningful call landed on: modules touched, interfaces, schemas, data flow, dependencies (pinned), failure modes. Name the chosen option and one sentence on why. For each layer touched (DB, IPC, renderer state, renderer queries), name the existing surface the change goes through and cite the prior-art `file:line` — `repository function: …`, `IPC endpoint: …`, `renderer hook: …`, `query key: …`. If the grounding subagents reported no analogous surface, say so explicitly. Inline prototype snippets when they pin a decision more precisely than prose (type shape, reducer, schema, query) — the decisive slice, not a demo.
- **Testing approach** — what makes a good test for this work (external behavior, not internals), which seams to test, prior art in the codebase. Name the same code path real users hit: if the listener attaches to `window`, dispatch on `window`; if a click traverses a button with `role`/`tabindex`, click that element. A test that fires synthetic events past the production seam is a dead feature in disguise.
- **Refactor scope** (architecture-improvement specs only) — when the spec's goal *is* to change existing structure (deepen a module, consolidate, extract, re-seam), name the existing modules / files / boundaries that are intentionally in play, each with the `path` and one line on the reshape intended. This is the explicit allowlist that opens those modules to redesign downstream; anything not listed keeps its current boundary. Omit this section entirely for ordinary feature/fix specs.
- **Out of scope** — what was discussed and explicitly punted.

### Design lens

Apply to any module that is **new** (the grounding subagents reported no analogous surface) **or named in the Refactor scope** (an existing module the spec intends to reshape). For a module that merely extends existing prior art and isn't in the Refactor scope, follow the established pattern and skip this lens. For an in-scope module, before you name the chosen design:

- **Deletion test.** Imagine the new module gone. If its complexity simply vanishes, it's a pass-through — fold it into its caller and don't spec it as a module. It earns a boundary only if deleting it would scatter that complexity across many callers.
- **Design it twice.** Sketch one *radically different* interface for the module (fewer entry points vs. more flexibility; data-in/data-out vs. injected behavior) and pick the deeper one — more capability behind a smaller interface. Record the chosen shape and one sentence on why it beat the alternative.
- **Seam & dependencies.** Classify each dependency the module crosses: **in-process** (no seam — test through the interface directly), **local-substitutable** (test stand-in like PGLite/in-memory FS — internal seam), **remote-but-owned** or **true-external** (define a port at the seam; production adapter + test adapter). Only introduce a port when two adapters are actually justified (typically production + test) — a single-adapter seam is just indirection.

Keep the interface as the test surface (see Testing approach): the seam you name here is the one the tests drive.

**Bar.** No `TODO`, `TBD`, `for later`, `v2`, "we'll figure out later", or equivalent placeholder language. If a decision is open: either resolve it now (one targeted question), or move it to **Out of scope** with a sentence on why. Reference real files as `path:line` where you have them.

## Adversarially review

Spawn one subagent via the `Agent` tool (`description: "Adversarial spec review"`) and pass it the spec's absolute path. Brief verbatim:

> Read the spec at `<path>`. Flag every instance of: **ambiguity** (two engineers could implement it meaningfully differently), **inaccuracy** (a claim that contradicts the codebase — verify against the repo), **off-pattern** (a layer is touched without naming the existing surface for that layer — repository function, renderer hook, query key, IPC shape — that analogous features in the codebase use; grep one or two analogous files to confirm), **shallow module** (a module that is *new* or named in the spec's **Refactor scope**, whose interface is nearly as complex as its implementation, or that fails the deletion test: removing it would not scatter complexity, so it's a pass-through that should fold into its caller — don't flag existing modules outside the Refactor scope, their boundaries are settled), **placeholder language** (`TODO` / `TBD` / `for later` / `v2` / anything punting a decision the spec should have resolved), and **missing technical detail** that would block an implementer. Don't re-open settled decisions. Then edit the file in place to fix what you flagged: tighten ambiguous language, correct inaccuracies, name the surface and `file:line` for any off-pattern flag, resolve placeholders or move them to **Out of scope**, fill in missing detail. End your reply with a one-line summary of what changed.

Quote the reviewer's summary line back to the user.

## Hand back

In chat prose, offer:

- **Keep the temp file** (default) — the path is already known; user can hand it to the plan skill, feed it elsewhere, or move it later.
- **Copy into the repo** — copy to a user-named path under the working directory.
- **Print inline and delete** — paste the final contents into the chat and remove the temp file.

Then stop. Do not auto-invoke other skills or continue past the handback.
