# Phase: Plan

## Goal

Turn the spec into something a coding agent can execute task-by-task with no further design conversation. **Bite-sized tasks. TDD rhythm. Frequent commits. No placeholders.**

## Hard Rules

- If triage handed you a spec path (from the skill's arguments or an earlier phase), read the spec from there; otherwise use the spec already in the conversation.
- **Write the plan to a fresh OS temp file:** `$(mktemp -t crank-plan).md`. Do not write into the working directory unless the user explicitly asks. Tell the user the path once.
- **Every subagent this skill spawns runs at the standard tier** (see References → Subagents) unless otherwise specified.
- **No placeholders.** No `TODO`, `TBD`, `implement later`, "add appropriate error handling", "similar to Task N", or references to symbols no task defines. Show code in every code step.
- **Tasks must be readable out of order.** Repeat structure across tasks rather than back-referencing.

## Guidelines

### Test-first or lightest-check

<tradeoff>
**Test-first** pins the intended behavior before code exists and leaves a regression net behind — at the cost of upfront time, and of awkward contortions where no real seam exists. **Lightest-check** (typecheck, build, curl, render) is fast and honest for work with no behavioral seam (config, docs, CSS, refactor-only) — at the cost of leaving no net. Between them sits the **probe** (VOCABULARY.md): behavior that deserves a deterministic check but has no seam worth a committed test — a migration's row counts, a one-shot transform, a regex over a corpus — gets a probe step: embed its code like any test, name its oracle and exact expected output, and end the step with its deletion. Choose per task by whether a real seam exists; where none does but the logic still has an oracle, plan a probe rather than manufacture a fake test — a test against a manufactured seam costs maintenance and protects nothing (see Dead seam).
</tradeoff>

### Embedded code or prose

<tradeoff>
**Embedded code** removes ambiguity — the executor types what the plan shows — at the cost of plan length and of going stale if the codebase moves before execution. **Prose-with-signature** stays short and drift-tolerant — at the cost of delegating construction to the executor. Embed when the shape matters (tests, non-obvious signatures, regexes, migrations, structural templates); use prose when the change is mechanical (`change < to <= at foo.ts:18`).
</tradeoff>

## References

### Subagents

If exploring the codebase could answer a question — an exact signature, prior art for a pattern, whether a spec claim still holds — dispatch a standard subagent to find out rather than digging in your own context. Whether to dispatch or read on the main thread follows the shared default in [SUBAGENT-TIERS.md](SUBAGENT-TIERS.md) → Dispatch or main thread.

This skill spawns subagents at two tiers — resolve each to your harness (Claude Code / Codex / Cursor) per [SUBAGENT-TIERS.md](SUBAGENT-TIERS.md). **standard** = codebase grounding and exploration; **heavy** = the adversarial plan review.

### Vocabulary

Shared design language across the crank pipeline, defined once in [VOCABULARY.md](VOCABULARY.md). This skill leans on the **deletion test**, **seam**, **dead seam**, the **probe**, **spaghetti growth**, the **tracer bullet** (**vertical slice**), and the **implementation-detail test** — read their meanings there.

### Readback protocol

The shared readback discipline lives in [READBACK.md](READBACK.md); Flow → Read back the shape loads it only at that step.

### Plan skeleton

The compact markdown skeleton lives in [PLAN-TEMPLATE.md](PLAN-TEMPLATE.md); Flow → Write the steps uses it as the starting shape, then scales or omits sections per Deliverables.

### Adversarial review brief

The heavy review prompt lives in [PLAN-REVIEW-BRIEF.md](PLAN-REVIEW-BRIEF.md); Flow → Adversarially review loads it only at that step.

## Deliverables

A single self-contained implementation plan written to the temp file (see Hard Rules). Include whichever sections apply, scaled to the change (a small fix is 2–4 tasks; a subsystem is denser):

- **Header** — title, `Spec:` (absolute path to the spec, when one exists — execute's final review needs it), `Goal:` (one sentence), `Architecture:` (2–3 sentences), `Tech stack:` (pinned versions), `Gates:` (the repo's test / lint / typecheck / build commands, each proven to run during grounding — execute's final walk and every implementer inherit them from here).
- **Global Constraints** — project-wide rules every task must honor: version floors, dependency limits, naming and copy rules, platform requirements — one line each, with the exact values copied verbatim from the spec. Every task's requirements implicitly include this section, and execute's per-task and final reviews run against it as a standing lens. Omit only if the spec names no such rule.
- **Updates since spec** — drift you found while grounding. Omit if none.
- **Refactor scope** — copy from the spec if present; the explicit allowlist of existing modules open to reshaping. Omit if the spec had none.
- **File structure** — the table from Map the files.
- **Tasks** — each with a `Files:` block, then an **Interfaces** block (`Consumes:` / `Produces:` — the exact signatures this task depends on and the ones it exposes, so an implementer who sees only this task's brief learns its neighbors' contracts; drop a side that's empty), then the checkbox steps.
- **Coverage** — a table with one row per acceptance criterion in the spec (if the spec lacks a numbered list, enumerate the behaviors it describes yourself): `criterion | task # | verify step that proves it`. Every criterion gets a row; a row whose verify cell is empty must say why (e.g. human-only smoke check) — silence is a gap, not a pass. Execute walks this table before claiming completion.
- **Smoke tests for the user** — anything the spec flagged as needing real-human verification. Omit if none.
- **Out of scope** — copy from the spec.

## Flow

Create a task for each step below and mark each complete as you finish it, live, so the user can watch progress.

### 1. Ground first

Before writing tasks, learn what you'll touch: read the files the spec names; grep for the symbols, types, and patterns you'll have to match; capture exact signatures, import paths, and any drift since the spec was written. Capture the repo's gate commands — test, lint, typecheck, build — exactly as this project runs them, and run each once so the plan's `Gates:` header line never names a gate that doesn't work. **Bias toward delegating** wide reads (see References → Subagents) so the subagent's context — not yours — holds the source.

Completion criterion: every file and symbol the spec names has been read (or its read delegated and returned) with exact signatures and import paths in hand, any drift since the spec noted for **Updates since spec**, and every `Gates:` command captured and proven to run.

### 2. Map the files

For every file the plan touches, record **path / action (`create` / `modify` / `delete`) / responsibility (one line)**. One clear responsibility per file. Follow established patterns; don't unilaterally restructure unless a file you're already modifying has grown unwieldy (a task that would push it past ~1,000 lines is the canonical trigger — plan the decomposition, don't defer it) or the spec's **Refactor scope** names it for reshaping.

If you can't state a `create`'d file's responsibility without "passes X to Y" or "wraps Z", it fails the deletion test — fold it into its caller rather than adding a pass-through module. (This applies to new files and to files named in the spec's **Refactor scope**, which are deliberately open to reshaping; files outside that scope keep their established boundaries.)

Every `modify` should trace to a surface the spec named. A change that threads a new boolean, mode, or special-case branch through a file the spec never mentions is spaghetti growth — route the behavior behind the module that owns the concept, or record the spec gap in **Updates since spec**; don't tangle the shared path.

Completion criterion: every file the plan touches has a path / action / responsibility row, every `create` passes the deletion test, and every `modify` traces to a spec-named surface.

### 3. Decompose

A **task** is independently committable (green tree at end), implements one cohesive thing. Default rhythm per task: **failing test → minimal impl → verify → commit**. When a task covers more than one behavior, its steps slice **vertically** — `test A → impl A → test B → impl B`, one **tracer bullet** at a time, each test followed immediately by the code that passes it — never every test first then every implementation (a **horizontal slice**, which pins imagined behavior and yields tests that pass when the feature breaks). Order tasks so each builds on the prior green tree. Right-size it: a task is the smallest unit that ends on a green tree and carries its own test cycle. **Split trigger** — if a task would yield two changes that each leave a green tree and each prove a distinct spec behavior (two unrelated acceptance criteria, or a refactor plus the feature that rides on it), make them two tasks; fold setup, config, and doc edits into the task that needs them rather than giving them their own.

When the spec's **Refactor scope** reshapes a module, **replace tests, don't layer them**: the task that adds tests at the deepened interface must also *delete* the superseded tests on the old shallow interface — write the literal step (`delete the N tests in foo.test.ts`), don't just describe the new ones. Old shallow-module tests left layered under new ones are maintenance cost protecting nothing.

**Wide refactors are the exception to the one-task green tree.** A **wide refactor** is one mechanical change — rename a shared symbol, retype a column — whose blast radius fans across the codebase, so a single edit breaks call sites everywhere at once and no one task can land it green. Don't force it into one tracer bullet; sequence it as **expand–contract**: an *expand* task adds the new form beside the old so nothing breaks, *migrate* tasks move call sites over in batches sized by blast radius (per package, per directory) — each batch still ends on a green tree because the old form stands — and one *contract* task deletes the old form once no caller remains. If even the batches can't stay green alone, keep the sequence but say so in the plan: green is promised only at a final integrate-and-verify task.

Whether a given task is **test-first** or a **lightest-check** is a per-task call — see Guidelines → Test-first or lightest-check.

Completion criterion: every task is independently committable, right-sized per the split trigger, and ordered so each builds on the prior green tree — no task bundles two green-tree outcomes.

### 4. Read back the shape

Decomposition settled the shape; before writing full steps, read it back per [READBACK.md](READBACK.md) (read it here). Open with what the plan commits to build, what's explicitly out of scope, and anything still unsettled — those are what the user vetoes. Then group the plan-to-be into logical sections and walk them: the file map first (the actual path / action / responsibility rows), then each section — showing what it builds and the consequential decisions behind it (a test-first vs. lightest-check call where that's a real judgment call).

Completion criterion: the file map and every section's content and decisions have been read back and user-approved section by section; objections resolved now, none carried into the written steps.

### 5. Write the steps

Read [PLAN-TEMPLATE.md](PLAN-TEMPLATE.md), then write the plan into that shape. Each step is one bite-sized action, checkbox syntax (`- [ ] Step N: <what>`). Carry the material the readback approved into the plan as vetted (READBACK.md → Carry what was approved). Whether to **embed** the code or describe it in **prose** is a per-step call — see Guidelines → Embedded code or prose.

Every `verify` step names exact success (`1 passed`, exit 0, status 200) and a deterministic instrument — the task's test, a `Gates:` command, or a **probe** (embed the probe's code like any test, with its oracle, exact expected output, and a final delete) — "tests pass" is not enough. A test-driven check must drive the production seam the spec named — the real DOM node, endpoint, or entry point a user reaches — never a dead seam. Name the seam in the verify step so the test and the production wiring point at the same place.

Keep the step *order* in the **tracer-bullet** rhythm set in Decompose — each test step immediately followed by the implementation step that makes it pass and its verify (`test A → impl A → verify → test B → impl B → verify`), never every test up front. And an embedded test drives the **seam** the spec named, never an **implementation-detail test** (defined in VOCABULARY.md).

Reuse the canonical helper for the job: if grounding (or the spec) surfaced an existing utility, embedded code calls it rather than re-implementing it — a bespoke near-duplicate is architectural drift. When no in-repo helper fits, reach in order — the stdlib, then a native platform feature (a DB constraint over app code, `<input type="date">` over a date-picker lib), then a dependency already in the manifest — before adding a new one; never add a dependency for what a few lines do, and a new dependency the spec's **Tech stack** didn't pin is an **Updates since spec** item to resolve, not a quiet import. And embedded code never reaches for a cast, `any`, or a new optional parameter to make types fit: an unclear contract is an **Updates since spec** item to resolve, not something to paper over inline.

**Completion criterion.** Every behavior the spec lists must land in a task step or a verify line — and the proof is the **Coverage table** (see Deliverables): walking the spec to build it *is* how you check yourself. A spec that names five keys and a plan that tests two is an incomplete plan, not a smaller one. And "smaller" never means thinner safety: trust-boundary validation, data-loss and error handling, security, and accessibility are behavior, not surface — keep each in a task and a Coverage row even where trimming would shorten the plan; where the spec only implies one, surface it in **Updates since spec** rather than dropping it.

### 6. Adversarially review

Read [PLAN-REVIEW-BRIEF.md](PLAN-REVIEW-BRIEF.md). Spawn one heavy subagent resolved per [SUBAGENT-TIERS.md](SUBAGENT-TIERS.md) and pass it the plan's absolute path plus the spec's path. If the spec exists only in the conversation (no file), drop the spec-path sentence from the brief and paste the spec's behavior list (or acceptance criteria) into the brief instead. Pass the resulting brief verbatim.

Quote the reviewer's summary line back to the user.

Completion criterion: the reviewer's edits are in the plan file and its one-line summary is quoted back to the user.

### 7. Hand back

The plan is the bottom of this skill's pipeline; recommend the `crank-execute` skill as the next step when the plan is ready to build. In chat prose, offer:

- **Keep the temp file** (default) — the path is known; user can hand it to `crank-execute`, feed it elsewhere, or move it later.
- **Copy into the repo** — copy to a user-named path under the working directory.
- **Print inline and delete** — paste the final contents into the chat and remove the temp file.

Then stop. Do not auto-invoke other skills or continue past the handback — executing is a deliberate act the user starts explicitly.

Completion criterion: the user picked from the file menu and you did exactly what they picked — nothing invoked they didn't opt into.
