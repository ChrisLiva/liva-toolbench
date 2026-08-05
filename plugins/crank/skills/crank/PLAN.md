# Phase: Plan

## Goal

Turn the spec into something a coding agent can execute task-by-task with no further design conversation. The plan resolves every implementation *decision* — boundaries, contracts, checks — and leaves construction to the executor. **Bite-sized tasks. Exact contracts. Oracles, not placeholders. Code only where surveyed.**

## Hard Rules

- If triage handed you a spec path (from the skill's arguments or an earlier phase), read the spec from there; otherwise use the spec already in the conversation.
- **Write the plan to a new temp file** (e.g. `${TMPDIR:-/tmp}/crank-plan-<slug>.md`). Do not write into the working directory unless the user explicitly asks. Tell the user the path once.
- **Oracles, not placeholders.** A step may omit code; it never omits proof: each behavior names its oracle (or the exact check that proves it) and each verify its exact command and success reading. `TODO`, `TBD`, `implement later`, "add appropriate error handling", "similar to Task N", and references to symbols no task defines have no place — prose is welcome, unverifiable prose is not.
- **Tasks must be readable out of order.** Repeat structure across tasks rather than back-referencing.

## Guidelines

### Test-first or lightest-check

<tradeoff>
**Test-first** pins the intended behavior before code exists and leaves a regression net behind — at the cost of upfront time, and of awkward contortions where no real seam exists. **Lightest-check** (typecheck, build, curl, render) is fast and honest for work with no behavioral seam (config, docs, CSS, refactor-only) — at the cost of leaving no net. Between them sits the **probe** (VOCABULARY.md): behavior that deserves a deterministic check but has no seam worth a committed test — a migration's row counts, a one-shot transform, a regex over a corpus — gets a probe step: name its oracle and exact expected output, and end the step with its deletion; its code is embedded only when grounding already ran it (see Prose, pseudo-code, or embedded code). Choose per task by whether a real seam exists; where none does but the logic still has an oracle, plan a probe rather than manufacture a fake test — a test against a manufactured seam costs maintenance and protects nothing (see Dead seam).
</tradeoff>

### Prose, pseudo-code, or embedded code

Three rungs, climbed only as far as the decision demands (per project decision: the executor constructs code from a pinned contract — the plan stopped scripting keystrokes):

<tradeoff>
**Prose-with-contract** — behavior, oracle, exact signatures — is the default: short and drift-tolerant, trusting construction to the executor. **Pseudo-code** pins an algorithm's shape — the tricky loop, ordering, or state machine that is itself a design decision — without forging unverified code; a sketch the readback approved carries in verbatim. **Embedded code** fixes exact text — at the cost of length, and of shipping the planner's unverified first draft: stale embedded code is where execute's detours start. Embed only the **surveyed** — verified during grounding (a regex probed against a corpus, migration SQL run and checked, a signature read from the live file) — and text that *is* the requirement (a public API signature, user-facing copy, config values); embedded code names its evidence in the step ("probed, output below", "read from `foo.ts:12`"). A purely mechanical change needs none of the three: a directive line (`change < to <= at foo.ts:18`) is enough.
</tradeoff>

Tests follow the same ladder: state the test *cases* — the oracle's exact inputs → expected outputs and the seam the test drives — and let the executor write the test to the repo's conventions; embed test code only when the harness shape itself was surveyed (a subtle async fixture, a mock grounding worked out).

## References

### Subagents

If exploring the codebase could answer a question — an exact signature, prior art for a pattern, whether a spec claim still holds — dispatch a standard subagent to find out rather than digging in your own context. Two tiers: **standard** = codebase grounding and exploration; **heavy** = the adversarial plan review. Resolve each tier to your harness (Claude Code / Codex / Cursor), and the dispatch-or-main-thread call, per [SUBAGENT-TIERS.md](SUBAGENT-TIERS.md).

### Vocabulary

Shared design language across the crank pipeline, defined once in [VOCABULARY.md](VOCABULARY.md). This skill leans on the **oracle**, the **deletion test**, **seam**, **dead seam**, the **probe**, **spaghetti growth**, the **tracer bullet** (**vertical slice**), and the **implementation-detail test** — read their meanings there.

## Deliverables

A single self-contained implementation plan written to the temp file (see Hard Rules). Include whichever sections apply, scaled to the change (a small fix is 2–4 tasks; a subsystem is denser):

- **Header** — title, `Spec:` (absolute path to the spec, when one exists — execute's final review needs it), `Goal:` (one sentence), `Architecture:` (2–3 sentences), `Tech stack:` (pinned versions), `Gates:` (the repo's test / lint / typecheck / build commands, each proven to run during grounding — execute's final walk and every implementer inherit them from here).
- **Global Constraints** — project-wide rules every task must honor: version floors, dependency limits, naming and copy rules, platform requirements — one line each, with the exact values copied verbatim from the spec. Every task's requirements implicitly include this section, and execute's per-task and final reviews run against it as a standing lens. Omit only if the spec names no such rule.
- **Updates since spec** — drift you found while grounding. Omit if none.
- **Refactor scope** — copy from the spec if present; the explicit allowlist of existing modules open to reshaping. Omit if the spec had none.
- **File structure** — the table from Map the files.
- **Tasks** — each with a `Files:` block; an **Interfaces** block (`Consumes:` / `Produces:` — the exact signatures this task depends on and the ones it exposes, so an implementer who sees only this task's brief learns its neighbors' contracts; drop a side that's empty); a `Check:` line naming the per-task call (test-first / lightest-check / probe); then one checkbox per behavior — each carrying its oracle and, where a test drives it, its seam — ending on the task's `Verify:` step.
- **Coverage** — a table with one row per acceptance criterion in the spec (if the spec lacks a numbered list, enumerate the behaviors it describes yourself): `criterion | task # | verify step that proves it`. Every criterion gets a row; a row whose verify cell is empty must say why (e.g. human-only smoke check) — silence is a gap, not a pass. Execute walks this table before claiming completion.
- **Smoke tests for the user** — anything the spec flagged as needing real-human verification. Omit if none.
- **Out of scope** — copy from the spec.

## Flow

Create a task for each step below and mark each complete as you finish it, live, so the user can watch progress.

### 1. Ground first

Before writing tasks, learn what you'll touch: read the files the spec names; grep for the symbols, types, and patterns you'll have to match; capture exact signatures, import paths, and any drift since the spec was written. Capture the repo's gate commands — test, lint, typecheck, build — exactly as this project runs them, and run each once so the plan's `Gates:` header line never names a gate that doesn't work. Grounding is also where anything the plan will embed gets **surveyed**: run it (a probe), or read it from the live tree, and keep the evidence for the step. **Bias toward delegating** wide reads (see References → Subagents) so the subagent's context — not yours — holds the source.

Completion criterion: every file and symbol the spec names has been read (or its read delegated and returned) with exact signatures and import paths in hand, any drift since the spec noted for **Updates since spec**, every `Gates:` command captured and proven to run, and every artifact the plan will embed surveyed with its evidence in hand.

### 2. Map the files

For every file the plan touches, record **path / action (`create` / `modify` / `delete`) / responsibility (one line)**. One clear responsibility per file. Follow established patterns; don't unilaterally restructure unless a file you're already modifying has grown unwieldy (a task that would push it past ~1,000 lines is the canonical trigger — plan the decomposition, don't defer it) or the spec's **Refactor scope** names it for reshaping.

If you can't state a `create`'d file's responsibility without "passes X to Y" or "wraps Z", it fails the deletion test — fold it into its caller rather than adding a pass-through module. (This applies to new files and to files named in the spec's **Refactor scope**, which are deliberately open to reshaping; files outside that scope keep their established boundaries.)

Every `modify` should trace to a surface the spec named. A change that threads a new boolean, mode, or special-case branch through a file the spec never mentions is spaghetti growth — route the behavior behind the module that owns the concept, or record the spec gap in **Updates since spec**; don't tangle the shared path.

Completion criterion: every file the plan touches has a path / action / responsibility row, every `create` passes the deletion test, and every `modify` traces to a spec-named surface.

### 3. Decompose

A **task** is independently committable (green tree at end), implements one cohesive thing. Execute supplies the working rhythm — failing test → minimal impl → verify → commit — so size tasks to that cycle rather than scripting it. When a task covers more than one behavior, its steps slice **vertically** — one **tracer bullet** at a time, never a **horizontal slice** (both defined in VOCABULARY.md). Order tasks so each builds on the prior green tree. Right-size it: a task is the smallest unit that ends on a green tree and carries its own test cycle. **Split trigger** — if a task would yield two changes that each leave a green tree and each prove a distinct spec behavior (two unrelated acceptance criteria, or a refactor plus the feature that rides on it), make them two tasks; fold setup, config, and doc edits into the task that needs them rather than giving them their own.

When the spec's **Refactor scope** reshapes a module, **replace tests, don't layer them**: the task that adds tests at the deepened interface must also *delete* the superseded tests on the old shallow interface — write the literal step (`delete the N tests in foo.test.ts`), don't just describe the new ones. Old shallow-module tests left layered under new ones are maintenance cost protecting nothing.

**Wide refactors are the exception to the one-task green tree.** A **wide refactor** is one mechanical change — rename a shared symbol, retype a column — whose blast radius fans across the codebase, so a single edit breaks call sites everywhere at once and no one task can land it green. Don't force it into one tracer bullet; sequence it as **expand–contract**: an *expand* task adds the new form beside the old so nothing breaks, *migrate* tasks move call sites over in batches sized by blast radius (per package, per directory) — each batch still ends on a green tree because the old form stands — and one *contract* task deletes the old form once no caller remains. If even the batches can't stay green alone, keep the sequence but say so in the plan: green is promised only at a final integrate-and-verify task.

Whether a given task is **test-first** or a **lightest-check** is a per-task call — see Guidelines → Test-first or lightest-check.

Completion criterion: every task is independently committable, right-sized per the split trigger, and ordered so each builds on the prior green tree — no task bundles two green-tree outcomes.

### 4. Read back the shape

Decomposition settled the shape; before writing the tasks in full, read it back per [READBACK.md](READBACK.md) (read it here). Open with what the plan commits to build, what's explicitly out of scope, and anything still unsettled — those are what the user vetoes. Then group the plan-to-be into logical sections and walk them: the file map first (the actual path / action / responsibility rows), then each section — showing what it builds and the consequential decisions behind it (a test-first vs. lightest-check call where that's a real judgment call).

Completion criterion: the file map and every section's content and decisions have been read back and user-approved section by section; objections resolved now, none carried into the written steps.

### 5. Write the tasks

Read [PLAN-TEMPLATE.md](PLAN-TEMPLATE.md), then write the plan into that shape, carrying the material the readback approved in as vetted (READBACK.md → Carry what was approved). Each task: the `Files:` block, the Interfaces block, the `Check:` call from Decompose (test-first, lightest-check, or probe), then one checkbox per behavior in **tracer-bullet** order, ending on the task's `Verify:` step. A behavior line states what the code must do, its oracle, and — where a test drives it — the seam; how far to climb from prose toward embedded code is a per-behavior call (see Guidelines → Prose, pseudo-code, or embedded code). Execute owns the keystroke rhythm; the plan states what each behavior must do and how to prove it.

Every `Verify:` step names exact success (`1 passed`, exit 0, status 200) and a deterministic instrument — the task's test, a `Gates:` command, or a **probe** (its oracle and exact expected output pinned here, ending in its deletion) — "tests pass" is not enough. A test must drive the production seam the spec named — the real DOM node, endpoint, or entry point a user reaches — never a dead seam. Name the seam in the behavior line so the specified test and the production wiring point at the same place; a test case specified in prose can still be an **implementation-detail test** — an oracle read through a back channel instead of the seam is one.

Route reuse by name: if grounding (or the spec) surfaced an existing utility, the task names it and the contract goes through it — a bespoke near-duplicate is architectural drift. When no in-repo helper fits, reach in order — the stdlib, then a native platform feature (a DB constraint over app code, `<input type="date">` over a date-picker lib), then a dependency already in the manifest — before adding a new one; never add a dependency for what a few lines do, and a new dependency the spec's **Tech stack** didn't pin is an **Updates since spec** item to resolve, not a quiet import. And a contract that only types with a cast, `any`, or a new optional parameter is unclear: an **Updates since spec** item to resolve, not something to paper over inline.

**Completion criterion.** Every behavior the spec lists must land in a task's behavior line or verify — and the proof is the **Coverage table** (see Deliverables): walking the spec to build it *is* how you check yourself. A spec that names five keys and a plan that tests two is an incomplete plan, not a smaller one. And "smaller" never means thinner safety: trust-boundary validation, data-loss and error handling, security, and accessibility are behavior, not surface — keep each in a task and a Coverage row even where trimming would shorten the plan; where the spec only implies one, surface it in **Updates since spec** rather than dropping it.

### 6. Adversarially review

Read [PLAN-REVIEW-BRIEF.md](PLAN-REVIEW-BRIEF.md). Spawn one heavy subagent resolved per [SUBAGENT-TIERS.md](SUBAGENT-TIERS.md) and pass it the plan's absolute path plus the spec's path. If the spec exists only in the conversation (no file), drop the spec-path sentence from the brief and paste the spec's behavior list (or acceptance criteria) into the brief instead. Pass the resulting brief verbatim.

Quote the reviewer's summary line back to the user.

Completion criterion: the reviewer's edits are in the plan file and its one-line summary is quoted back to the user.

### 7. Hand back

The plan is the bottom of this skill's pipeline; recommend the user run `/crank-execute` when the plan is ready to build. In chat prose, offer:

- **Keep the temp file** (default) — the path is known; user can hand it to `/crank-execute`, feed it elsewhere, or move it later.
- **Copy into the repo** — copy to a user-named path under the working directory.
- **Print inline and delete** — paste the final contents into the chat and remove the temp file.

Then stop — executing is a deliberate act the user starts explicitly.

Completion criterion: the user picked from the file menu and you did exactly what they picked — nothing invoked they didn't opt into.
