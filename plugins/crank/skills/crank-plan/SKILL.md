---
name: crank-plan
description: Turn a spec — written by the spec skill or already in the conversation — into a bite-sized, TDD-flavored implementation plan, then adversarially review it in place. Use when the user asks to break a spec into ordered tasks.
argument-hint: "[optional path to spec.md]"
---

# Plan

Turn the spec into something a coding agent can execute task-by-task with no further design conversation. **Bite-sized tasks. TDD rhythm. Frequent commits. No placeholders.**

<subagent-tiers>
This skill delegates work to subagents at two capability tiers. Where the body says to spawn a **standard** or **heavy** subagent, resolve the tier for the harness you are running in:

- **Claude Code** — spawn via the `Agent` tool and set `model` per tier: standard → `model: sonnet`, heavy → `model: opus`. Set per spawn; nothing else to configure.
- **Codex** — spawn a subagent and set its reasoning effort per tier on `gpt-5.5`: standard → `medium`, heavy → `high`. Set per spawn; nothing else to configure.
- **Cursor** — spawn a subagent and set its `model` per tier: standard → `cursor-composer-2-5`, heavy → `gpt-5.5-high`. Set per spawn; nothing else to configure.

Tier intent (harness-independent): **standard** = bulk work — codebase grounding, exploration, per-task review. **heavy** = work that rewards the strongest reasoning — spec drafting, adversarial review, final cross-task review.
</subagent-tiers>

<rules>
- If `$ARGUMENTS` is a path, read the spec from there; otherwise use the spec already in the conversation.
- **Write the plan to a fresh OS temp file:** `$(mktemp -t crank-plan).md`. Do not write into the working directory unless the user explicitly asks. Tell the user the path once.
- **Every subagent this skill spawns runs at the standard tier** (see <subagent-tiers>) unless otherwise specified.
- **No placeholders.** No `TODO`, `TBD`, `implement later`, "add appropriate error handling", "similar to Task N", or references to symbols no task defines. Show code in every code step.
- **Tasks must be readable out of order.** Repeat structure across tasks rather than back-referencing.
</rules>

## Subagents

If exploring the codebase could answer a question — an exact signature, prior art for a pattern, whether a spec claim still holds — dispatch a standard subagent to find out rather than digging in your own context.

<tradeoff>
**Dispatching** keeps your context free to hold the plan's structure, and the subagent's window — not yours — absorbs the source it reads. It costs dispatch latency and requires writing a self-contained brief. **Main-thread reading** is faster for a single lookup and keeps full conversational nuance — at the cost of crowding the window you need for plan-writing. Default: a one-symbol lookup in a known file, do yourself; wide reads, dispatch.
</tradeoff>

## Vocabulary

Shared design language across the crank skills (the spec skill defines the full set). The terms this skill leans on:

- **Deletion test** — imagine the module gone. If its complexity simply vanishes, it was a pass-through; if that complexity reappears across many callers, the boundary earned its place.
- **Seam** — a place where behavior can be swapped without editing in that place; the location of an interface, and the surface tests drive (the production node/endpoint/entry point a real user reaches, never a synthetic stand-in).
- **Dead seam** — a verify step that drives a node, handler, or endpoint the production code never wires up. It passes even if the feature is absent — worse than no check, because it hides the gap.
- **Spaghetti growth** — a one-off conditional, flag, or special case bolted onto a flow the spec never named. A design problem, not a style nit: route the behavior behind the module that owns the concept, or surface the spec gap.

## Workflow

Create a task for each step below and mark each one complete as you finish it — update them live as you go, not in a batch at the end — so the user can watch progress:

- Ground: spec-named files read, signatures captured (delegate wide reads); Global Constraints lifted from the spec
- File map: every touched file has path / action / responsibility
- Tasks decomposed and ordered (each independently committable), each naming its Consumes / Produces interfaces
- Steps written: code embedded where shape matters, exact verify lines
- Coverage table: every spec criterion has a row
- Adversarially reviewed (subagent edits the file in place)
- Hand back

## Ground first

Before writing tasks, learn what you'll touch: read the files the spec names; grep for the symbols, types, and patterns you'll have to match; capture exact signatures, import paths, and any drift since the spec was written. **Bias toward delegating** wide reads (see Subagents) so the subagent's context — not yours — holds the source.

## Map the files

For every file the plan touches, record **path / action (`create` / `modify` / `delete`) / responsibility (one line)**. One clear responsibility per file. Follow established patterns; don't unilaterally restructure unless a file you're already modifying has grown unwieldy (a task that would push it past ~1,000 lines is the canonical trigger — plan the decomposition, don't defer it) or the spec's **Refactor scope** names it for reshaping.

If you can't state a `create`'d file's responsibility without "passes X to Y" or "wraps Z", it fails the deletion test — fold it into its caller rather than adding a pass-through module. (This applies to new files and to files named in the spec's **Refactor scope**, which are deliberately open to reshaping; files outside that scope keep their established boundaries.)

Every `modify` should trace to a surface the spec named. A change that threads a new boolean, mode, or special-case branch through a file the spec never mentions is spaghetti growth — route the behavior behind the module that owns the concept, or record the spec gap in **Updates since spec**; don't tangle the shared path.

## Decompose

A **task** is independently committable (green tree at end), implements one cohesive thing. Default rhythm per task: **failing test → minimal impl → verify → commit**. Order tasks so each builds on the prior green tree. Right-size it: a task is the smallest unit that carries its own test cycle and is worth a fresh reviewer's gate — fold setup, config, and doc edits into the task that needs them, and split only where a reviewer could reasonably reject one piece while approving its neighbor.

When the spec's **Refactor scope** reshapes a module, plan test replacement, not accretion: the task that adds tests at the deepened interface also deletes the superseded tests the spec named — old shallow-module tests left layered under new ones are maintenance cost protecting nothing.

<tradeoff>
**Test-first** pins the intended behavior before code exists and leaves a regression net behind — at the cost of upfront time, and of awkward contortions where no real seam exists. **Lightest-check** (typecheck, build, curl, render) is fast and honest for work with no behavioral seam (config, docs, CSS, refactor-only) — at the cost of leaving no net. Choose per task by whether a real seam exists; don't manufacture fake tests, because a test against a manufactured seam costs maintenance and protects nothing (see Dead seam).
</tradeoff>

## Write the steps

Each step is one bite-sized action, checkbox syntax (`- [ ] Step N: <what>`).

<tradeoff>
**Embedded code** removes ambiguity — the executor types what the plan shows — at the cost of plan length and of going stale if the codebase moves before execution. **Prose-with-signature** stays short and drift-tolerant — at the cost of delegating construction to the executor. Embed when the shape matters (tests, non-obvious signatures, regexes, migrations, structural templates); use prose when the change is mechanical (`change < to <= at foo.ts:18`).
</tradeoff>

Every `verify` step names exact success (`1 passed`, exit 0, status 200) — "tests pass" is not enough. The check must drive the production seam the spec named — the real DOM node, endpoint, or entry point a user reaches — never a dead seam. Name the seam in the verify step so the test and the production wiring point at the same place.

Reuse the canonical helper for the job: if grounding (or the spec) surfaced an existing utility, embedded code calls it rather than re-implementing it — a bespoke near-duplicate is architectural drift. And embedded code never reaches for a cast, `any`, or a new optional parameter to make types fit: an unclear contract is an **Updates since spec** item to resolve, not something to paper over inline.

**Bar.** Every behavior the spec lists must land in a task step or a verify line — and the proof is the **Coverage table** (see Document shape): walking the spec to build it *is* how you check yourself. A spec that names five keys and a plan that tests two is an incomplete plan, not a smaller one.

## Document shape

Include whichever sections apply, scaled to the change (a small fix is 2–4 tasks; a subsystem is denser):

- **Header** — title, `Spec:` (absolute path to the spec, when one exists — execute's final review needs it), `Goal:` (one sentence), `Architecture:` (2–3 sentences), `Tech stack:` (pinned versions).
- **Global Constraints** — project-wide rules every task must honor: version floors, dependency limits, naming and copy rules, platform requirements — one line each, with the exact values copied verbatim from the spec. Every task's requirements implicitly include this section, and execute's per-task and final reviews run against it as a standing lens. Omit only if the spec names no such rule.
- **Updates since spec** — drift you found while grounding. Omit if none.
- **Refactor scope** — copy from the spec if present; the explicit allowlist of existing modules open to reshaping. Omit if the spec had none.
- **File structure** — the table from Map the files.
- **Tasks** — each with a `Files:` block, then an **Interfaces** block (`Consumes:` / `Produces:` — the exact signatures this task depends on and the ones it exposes, so an implementer who sees only this task's brief learns its neighbors' contracts; drop a side that's empty), then the checkbox steps.
- **Coverage** — a table with one row per acceptance criterion in the spec (if the spec lacks a numbered list, enumerate the behaviors it describes yourself): `criterion | task # | verify step that proves it`. Every criterion gets a row; a row whose verify cell is empty must say why (e.g. human-only smoke check) — silence is a gap, not a pass. Execute walks this table before claiming completion.
- **Smoke tests for the user** — anything the spec flagged as needing real-human verification. Omit if none.
- **Out of scope** — copy from the spec.

## Adversarially review

Spawn one heavy subagent via the `Agent` tool (`description: "Adversarial plan review"`) and pass it the plan's absolute path plus the spec's path. If the spec exists only in the conversation (no file), drop the spec-path sentence from the brief and paste the spec's behavior list (or acceptance criteria) into the brief instead. Pass this brief verbatim:

<brief>
Read the plan at `<plan-path>` and the spec at `<spec-path>`. You will execute this plan tomorrow with no further design conversation. Flag every instance of: **non-runnable steps** (path / command / expected / instruction not concrete enough to type code from), **coverage holes** (walk the spec yourself — every acceptance criterion and every behavior the body describes: interaction, keybinding, alias, edge case, state transition, validation — and check the plan's Coverage table against your walk; flag criteria missing from the table, rows whose verify step doesn't actually exercise the behavior, and empty verify cells with no stated reason), **name / type / path inconsistencies** across tasks or against the codebase, **placeholder language** (`TODO` / `TBD` / `similar to Task N` / "add appropriate handling" / vague instructional prose / undefined symbols), **dead-seam verify steps** (a test that drives a node, handler, or endpoint the production code never wires up, so it would pass even if the feature were absent), **spaghetti growth** (a step threads a one-off conditional, flag, or special case through a file or flow the spec never named, instead of routing it behind the module that owns the concept), **bespoke duplication** (embedded code re-implements a helper the codebase already provides — grep to confirm, and rewrite the step to call the canonical one), **boundary smells** (embedded code uses casts, `any`, or new optional parameters to paper over an unclear contract), **interface drift** (a task's `Consumes` names a signature no earlier task `Produces` or that contradicts the codebase, or a `Produces` no later task and no acceptance criterion ever uses), **Global Constraints violations** (a task contradicts a rule in the plan's Global Constraints, or a Global Constraints value isn't copied verbatim from the spec), and **order problems** (a task imports what no earlier task built). Don't re-open spec-level decisions. Then edit the file in place to fix every item you flagged. End your reply with a one-line summary of what changed.
</brief>

Quote the reviewer's summary line back to the user.

## Hand back

First render an interactive HTML review of the final plan and open it in the user's browser; then offer the file menu.

**Open the review.** Read the rendering guide in this skill's directory — [HTML-REVIEW.md](HTML-REVIEW.md) — then follow it to render the plan as the `.html` sibling of the temp file and open it. Tell the user the HTML path and that they can comment per task, tick any out-of-scope cut that should be in, hit **Export comments →**, and paste the block back — you'll apply it to the plan and re-render. (Under `/crank`/headless the whole Hand back step is skipped, so the browser never opens mid-pipeline.)

In chat prose, offer:

- **Keep the temp file** (default) — the path is known; user can execute it, feed it elsewhere, or move it later.
- **Copy into the repo** — copy to a user-named path under the working directory.
- **Print inline and delete** — paste the final contents into the chat and remove the temp file (and its `.html` sibling).

When the user pastes a block beginning `> Source: <path>`, apply each `## <heading>` comment to that markdown and resolve every `Out of scope → requested IN scope` item (fold it into the plan as a real task/step, or push back with a reason — never drop it silently), then re-render the HTML and reopen it. See HTML-REVIEW.md's "Applying a pasted review."

Then stop. Do not auto-invoke other skills or continue past the handback.
