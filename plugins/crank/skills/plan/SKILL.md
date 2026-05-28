---
name: plan
description: Turn a spec — written by the spec skill or already in the conversation — into a bite-sized, TDD-flavored implementation plan, then adversarially review it in place. Use when the user types /plan or asks to break a spec into ordered tasks.
argument-hint: "[optional path to spec.md]"
---

# Plan

Turn the spec into something a coding agent can execute task-by-task with no further design conversation. **Bite-sized tasks. TDD rhythm. Frequent commits. No placeholders.**

Write the plan to a fresh OS temp file: `$(mktemp -t crank-plan).md`. Do not write into the working directory unless the user explicitly asks. If `$ARGUMENTS` is a path, read the spec from there; otherwise use the spec already in the conversation. Tell the user the path once.

## Vocabulary

Shared design language across the crank skills (spec → plan → execute). Use these terms with these meanings:

- **Module** — anything with an interface and an implementation: a function, class, file, or larger slice.
- **Interface** — the full contract a caller must understand: signatures, invariants, ordering, errors, config.
- **Depth** — how much an interface hides. A **deep** module exposes a small interface over substantial behavior; a **shallow** one exposes nearly as much as it hides.
- **Deletion test** — imagine the module gone. If its complexity simply vanishes, it was a pass-through; if that complexity reappears across many callers, the boundary earned its place.
- **Seam** — a place where behavior can be swapped without editing in that place; the location of an interface, and the surface tests drive (the production node/endpoint/entry point a real user reaches, never a synthetic stand-in).
- **Port / adapter** — a seam that crosses a dependency: the **port** is the interface, an **adapter** is a concrete fill (production HTTP/db vs. in-memory test double). Two adapters justify a port; one is just indirection.

## Ground first

Before writing tasks, learn what you'll touch: read the files the spec names; grep for the symbols, types, and patterns you'll have to match; capture exact signatures, import paths, and any drift since the spec was written. **Bias toward delegating** wide reads to a subagent (`Agent` tool) so its context — not yours — holds the source.

## Map the files

For every file the plan touches, record **path / action (`create` / `modify` / `delete`) / responsibility (one line)**. One clear responsibility per file. Follow established patterns; don't unilaterally restructure unless a file you're already modifying has grown unwieldy or the spec's **Refactor scope** names it for reshaping.

If you can't state a `create`'d file's responsibility without "passes X to Y" or "wraps Z", it fails the deletion test — fold it into its caller rather than adding a pass-through module. (This applies to new files and to files named in the spec's **Refactor scope**, which are deliberately open to reshaping; files outside that scope keep their established boundaries.)

## Decompose

A **task** is independently committable (green tree at end), implements one cohesive thing. Default rhythm per task: **failing test → minimal impl → verify → commit**. Skip honestly when no test seam exists (config, docs, CSS, refactor-only) — substitute the lightest agent-verifiable check (typecheck, build, curl). Don't manufacture fake tests. Order tasks so each builds on the prior green tree.

## Write the steps

Each step is one bite-sized action, checkbox syntax (`- [ ] Step N: <what>`). Embed code when the shape matters (tests, non-obvious signatures, regexes, migrations, structural templates); use prose-with-signature when mechanical (`change < to <= at foo.ts:18`). Every `verify` step names exact success (`1 passed`, exit 0, status 200) — "tests pass" is not enough. The check must drive the production seam the spec named — the real DOM node, endpoint, or entry point a user reaches — not a synthetic stand-in. A test that fires events at a container the listener never attaches to, or calls a handler the UI never wires up, passes against a dead seam: worse than no check, because it hides the gap. Name the seam in the verify step so the test and the production wiring point at the same place.

**Bar.** Every behavior the spec lists — each interaction, keybinding, alias, edge case, state transition, and validation — must land in a task step or a verify line. Walk the spec and account for each one before you call the plan done; a spec that names five keys and a plan that tests two is an incomplete plan, not a smaller one. No `TODO`, `TBD`, `implement later`, "add appropriate error handling", "similar to Task N", or references to symbols no task defines. Show code in every code step. Repeat structure across tasks rather than back-referencing — tasks must be readable out of order.

## Document shape

Include whichever sections apply, scaled to the change (a small fix is 2–4 tasks; a subsystem is denser):

- **Header** — title, link to the spec, `Goal:` (one sentence), `Architecture:` (2–3 sentences), `Tech stack:` (pinned versions).
- **Updates since spec** — drift you found while grounding. Omit if none.
- **Refactor scope** — copy from the spec if present; the explicit allowlist of existing modules open to reshaping. Omit if the spec had none.
- **File structure** — the table from above.
- **Tasks** — each with a `Files:` block followed by the checkbox steps.
- **Smoke tests for the user** — anything the spec flagged as needing real-human verification. Omit if none.
- **Out of scope** — copy from the spec.

## Adversarially review

Spawn one subagent via the `Agent` tool (`description: "Adversarial plan review"`) and pass it the plan's absolute path plus the spec's path. Brief verbatim:

> Read the plan at `<plan-path>` and the spec at `<spec-path>`. You will execute this plan tomorrow with no further design conversation. Flag every instance of: **non-runnable steps** (path / command / expected / instruction not concrete enough to type code from), **missing spec coverage** (walk every behavior the spec lists — each interaction, keybinding, alias, edge case, state transition, and validation — and flag any that no task step or verify line covers, plus any goal or interface no task implements), **name / type / path inconsistencies** across tasks or against the codebase, **placeholder language** (`TODO` / `TBD` / `similar to Task N` / "add appropriate handling" / vague instructional prose / undefined symbols), **dead-seam verify steps** (a test that drives a node, handler, or endpoint the production code never wires up, so it would pass even if the feature were absent), and **order problems** (a task imports what no earlier task built). Don't re-open spec-level decisions. Then edit the file in place to fix every item you flagged. End your reply with a one-line summary of what changed.

Quote the reviewer's summary line back to the user.

## Hand back

In chat prose, offer:

- **Keep the temp file** (default) — the path is known; user can execute it, feed it elsewhere, or move it later.
- **Copy into the repo** — copy to a user-named path under the working directory.
- **Print inline and delete** — paste the final contents into the chat and remove the temp file.

Then stop. Do not auto-invoke other skills or continue past the handback.
