---
name: plan
description: Turn a spec — written by the spec skill or already in the conversation — into a bite-sized, TDD-flavored implementation plan, then adversarially review it in place. Use when the user types /plan or asks to break a spec into ordered tasks.
argument-hint: "[optional path to spec.md]"
---

# Plan

Turn the spec into something a coding agent can execute task-by-task with no further design conversation. **Bite-sized tasks. TDD rhythm. Frequent commits. No placeholders.**

Write the plan to a fresh OS temp file: `$(mktemp -t crank-plan).md`. Do not write into the working directory unless the user explicitly asks. If `$ARGUMENTS` is a path, read the spec from there; otherwise use the spec already in the conversation. Tell the user the path once.

## Ground first

Before writing tasks, learn what you'll touch: read the files the spec names; grep for the symbols, types, and patterns you'll have to match; capture exact signatures, import paths, and any drift since the spec was written. **Bias toward delegating** wide reads to a subagent (`Agent` tool) so its context — not yours — holds the source.

## Map the files

For every file the plan touches, record **path / action (`create` / `modify` / `delete`) / responsibility (one line)**. One clear responsibility per file. Follow established patterns; don't unilaterally restructure unless a file you're already modifying has grown unwieldy.

## Decompose

A **task** is independently committable (green tree at end), implements one cohesive thing. Default rhythm per task: **failing test → minimal impl → verify → commit**. Skip honestly when no test seam exists (config, docs, CSS, refactor-only) — substitute the lightest agent-verifiable check (typecheck, build, curl). Don't manufacture fake tests. Order tasks so each builds on the prior green tree.

## Write the steps

Each step is one bite-sized action, checkbox syntax (`- [ ] Step N: <what>`). Embed code when the shape matters (tests, non-obvious signatures, regexes, migrations, structural templates); use prose-with-signature when mechanical (`change < to <= at foo.ts:18`). Every `verify` step names exact success (`1 passed`, exit 0, status 200) — "tests pass" is not enough.

**Bar.** No `TODO`, `TBD`, `implement later`, "add appropriate error handling", "similar to Task N", or references to symbols no task defines. Show code in every code step. Repeat structure across tasks rather than back-referencing — tasks must be readable out of order.

## Document shape

Include whichever sections apply, scaled to the change (a small fix is 2–4 tasks; a subsystem is denser):

- **Header** — title, link to the spec, `Goal:` (one sentence), `Architecture:` (2–3 sentences), `Tech stack:` (pinned versions).
- **Updates since spec** — drift you found while grounding. Omit if none.
- **File structure** — the table from above.
- **Tasks** — each with a `Files:` block followed by the checkbox steps.
- **Smoke tests for the user** — anything the spec flagged as needing real-human verification. Omit if none.
- **Out of scope** — copy from the spec.

## Adversarially review

Spawn one subagent via the `Agent` tool (`description: "Adversarial plan review"`) and pass it the plan's absolute path plus the spec's path. Brief verbatim:

> Read the plan at `<plan-path>` and the spec at `<spec-path>`. You will execute this plan tomorrow with no further design conversation. Flag every instance of: **non-runnable steps** (path / command / expected / instruction not concrete enough to type code from), **missing spec coverage** (a goal, interface, or validation in the spec that no task implements), **name / type / path inconsistencies** across tasks or against the codebase, **placeholder language** (`TODO` / `TBD` / `similar to Task N` / "add appropriate handling" / vague instructional prose / undefined symbols), and **order problems** (a task imports what no earlier task built). Don't re-open spec-level decisions. Then edit the file in place to fix every item you flagged. End your reply with a one-line summary of what changed.

Quote the reviewer's summary line back to the user.

## Hand back

In chat prose, offer:

- **Keep the temp file** (default) — the path is known; user can execute it, feed it elsewhere, or move it later.
- **Copy into the repo** — copy to a user-named path under the working directory.
- **Print inline and delete** — paste the final contents into the chat and remove the temp file.

Then stop. Do not auto-invoke other skills or continue past the handback.
