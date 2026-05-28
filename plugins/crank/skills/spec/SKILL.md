---
name: spec
description: Synthesize the current conversation — grilling, brainstorming, prototyping — into one document that is part PRD, part technical spec, then adversarially review it in place. Use when the user types /spec or asks to write up what you've been discussing.
argument-hint: "[optional topic hint]"
---

# Spec

Turn what you and the user have been discussing into a single self-contained spec — part PRD (user-facing intent), part technical spec (decisions already settled). **Synthesize from the conversation; do not restart the interview.** If a real gap blocks the writeup, ask one targeted question; otherwise resolve it and note the assumption in the doc.

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
- **Out of scope** — what was discussed and explicitly punted.

**Bar.** No `TODO`, `TBD`, `for later`, `v2`, "we'll figure out later", or equivalent placeholder language. If a decision is open: either resolve it now (one targeted question), or move it to **Out of scope** with a sentence on why. Reference real files as `path:line` where you have them.

## Adversarially review

Spawn one subagent via the `Agent` tool (`description: "Adversarial spec review"`) and pass it the spec's absolute path. Brief verbatim:

> Read the spec at `<path>`. Flag every instance of: **ambiguity** (two engineers could implement it meaningfully differently), **inaccuracy** (a claim that contradicts the codebase — verify against the repo), **off-pattern** (a layer is touched without naming the existing surface for that layer — repository function, renderer hook, query key, IPC shape — that analogous features in the codebase use; grep one or two analogous files to confirm), **placeholder language** (`TODO` / `TBD` / `for later` / `v2` / anything punting a decision the spec should have resolved), and **missing technical detail** that would block an implementer. Don't re-open settled decisions. Then edit the file in place to fix what you flagged: tighten ambiguous language, correct inaccuracies, name the surface and `file:line` for any off-pattern flag, resolve placeholders or move them to **Out of scope**, fill in missing detail. End your reply with a one-line summary of what changed.

Quote the reviewer's summary line back to the user.

## Hand back

In chat prose, offer:

- **Keep the temp file** (default) — the path is already known; user can hand it to the plan skill, feed it elsewhere, or move it later.
- **Copy into the repo** — copy to a user-named path under the working directory.
- **Print inline and delete** — paste the final contents into the chat and remove the temp file.

Then stop. Do not auto-invoke other skills or continue past the handback.
