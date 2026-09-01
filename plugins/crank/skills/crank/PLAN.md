# Phase: Plan

## Goal

Turn the spec into tasks the **executor** can build with no further design conversation. The executor is a standard-tier subagent ([SUBAGENT-TIERS.md](SUBAGENT-TIERS.md)) that receives one task's block plus a repo orientation, never the spec, this conversation, or the other tasks. It follows explicit instructions well and fills gaps badly: an unnamed oracle becomes a guess, a back-reference to Task N becomes a missing file, an unstated assumption becomes an improvisation. Write every task for the weakest plausible executor, repeating structure across tasks rather than back-referencing. The plan resolves every implementation *decision* — boundaries, contracts, checks — and leaves construction to the executor. **Bite-sized tasks. Exact contracts. Oracles, not placeholders. Code only where surveyed.**

## Hard Rules

- If triage handed you a spec path (from the skill's arguments or an earlier phase), read the spec from there; otherwise use the spec already in the conversation. With no spec at all — a settled change routed straight to plan — write the acceptance criteria yourself from the user's ask before grounding, read them back at step 4, and treat that list as the spec everywhere below (Coverage, the review brief, Updates since spec).
- **Write the plan to `.crank/<slug>/plan.md`** per [ARTIFACT-HOME.md](ARTIFACT-HOME.md) — read it before writing the file.
- **Oracles, not placeholders.** A step may omit code; it never omits proof: each behavior names its oracle (or the exact check that proves it) and each verify its exact command and success reading. `TODO`, `TBD`, `implement later`, "add appropriate error handling", "similar to Task N", and references to symbols no task defines have no place — prose is welcome, unverifiable prose is not.
- **Cite what you assert.** Every claim the plan states about the code as it stands now carries its evidence in the step that states it: `path:line`, the command and the exact output it printed, or `searched <scope>, none found`. The rule reaches the claims that ride in prose and so escape the embedded-code evidence check: a count, a sole caller or sole use, a uniqueness, a snippet quoted from a file, the output a gate is expected to print, and a third-party tool's exact output, exit code, or API contract. Grounding proves them (Flow → Ground first). A claim grounding could not settle becomes a `Stop if:` line on the task that rests on it, never an assertion. Execute's plan walk confirms a cited claim at its citation with one read; an uncited claim is what sends it grepping, and a wrong one is what turns into a detour mid-task.

## Guidelines

### Test-first or lightest-check

<tradeoff>
**Test-first** pins the intended behavior before code exists and leaves a regression net behind — at the cost of upfront time, and of awkward contortions where no real seam exists. **Lightest-check** (typecheck, build, curl, render) is fast and honest for work with no behavioral seam (config, docs, CSS, refactor-only) — at the cost of leaving no net. Between them sits the **probe**: behavior that deserves a deterministic check but has no seam worth a committed test — a migration's row counts, a one-shot transform, a regex over a corpus — gets a probe step: name its oracle and exact expected output, and end the step with its deletion; its code is embedded only when grounding already ran it (see Prose, pseudo-code, or embedded code). Choose per task by whether a real seam exists; where none does but the logic still has an oracle, plan a probe rather than manufacture a fake test — a test against a manufactured seam costs maintenance and protects nothing: it is a **dead seam**.
</tradeoff>

Test-first sets the rhythm, not the count: behaviors along one workflow ride one **journey test**, a new test earns its own file only at a new seam, and a planned test that wouldn't survive the **rewrite test** isn't worth writing.

### Prose, pseudo-code, or embedded code

Three rungs, climbed only as far as the decision demands (per project decision: the executor constructs code from a pinned contract — the plan stopped scripting keystrokes):

<tradeoff>
**Prose-with-contract** — behavior, oracle, exact signatures — is the default: short and drift-tolerant, trusting construction to the executor. **Pseudo-code** pins an algorithm's shape — the tricky loop, ordering, or state machine that is itself a design decision — without forging unverified code; a sketch the readback approved carries in verbatim. **Embedded code** fixes exact text — at the cost of length, and of shipping the planner's unverified first draft: stale embedded code is where execute's detours start. Embed only the **surveyed** — verified during grounding (a regex probed against a corpus, migration SQL run and checked, a signature read from the live file) — and text that *is* the requirement (a public API signature, user-facing copy, config values); embedded code names its evidence in the step ("probed, output below", "read from `foo.ts:12`"). A purely mechanical change needs none of the three: a directive line (`change < to <= at foo.ts:18`) is enough.
</tradeoff>

Tests follow the same ladder: state the test *cases* — the oracle's exact inputs → expected outputs and the seam the test drives — and let the executor write the test to the conventions of the exemplar test the `Check:` line names; embed test code only when the harness shape itself was surveyed (a subtle async fixture, a mock grounding worked out).

## References

Read both files this section names — [SUBAGENT-TIERS.md](SUBAGENT-TIERS.md) and [VOCABULARY.md](VOCABULARY.md) — together in one turn, before step 1.

### Subagents

This phase dispatches **standard** subagents for what the codebase can answer — an exact signature, prior art for a pattern, whether a spec claim still holds. The adversarial review is its only **heavy** dispatch. Resolve each tier to your harness, and the dispatch-or-main-thread call, per [SUBAGENT-TIERS.md](SUBAGENT-TIERS.md) → Dispatch or main thread.

Dispatch each grounding read with this brief, filled in:

<brief>
Investigate `<files, symbols, or gate commands>` in this codebase. We're planning `<one-sentence change summary>`. Read-only: change nothing in the codebase or on the machine, beyond running the gate commands named below.

Report:

- the exact signature and import path of each named symbol, as `file:line`;
- the exemplar test at each seam the change will drive (`file:line`), and one sentence on the convention it follows;
- any drift from what the spec claims about these files — what the spec says, what the code says;
- the exact output of each gate command you were asked to run, verbatim, and whether it exited 0.

Keep each item you report — one symbol, one exemplar, one drift note — under ~150 words. Cite `file:line` instead of pasting the code around it, and quote source only where the exact text is the answer. Exact signatures and gate output are the answer: reproduce those in full, however long.

Don't propose a design or write tasks. If something named doesn't exist, say so plainly rather than naming the nearest match as if it were the thing.
</brief>

### Vocabulary

[VOCABULARY.md](VOCABULARY.md) — both **Design language** and **Verification language**. This phase leans on the **oracle**, the **deletion test**, **seam**, **dead seam**, the **probe**, **spaghetti growth**, the **tracer bullet** (**vertical slice**), the **implementation-detail test**, the **rewrite test**, the **journey test**, and the **redundant test**.

## Deliverables

A single self-contained implementation plan written to the `.crank/` file (see Hard Rules). Include whichever sections apply, scaled to the change (a small fix is 2–4 tasks; a subsystem is denser):

- **Header** — title, `Spec:` (absolute path to the spec, when one exists — execute's final review needs it), `Goal:` (one sentence), `Architecture:` (2–3 sentences), `Tech stack:` (pinned versions), `Gates:` (the repo's test / lint / typecheck / build commands, each proven to run during grounding — execute's final walk and every implementer inherit them from here).
- **Global Constraints** — project-wide rules every task must honor: version floors, dependency limits, naming and copy rules, platform requirements — one line each, with the exact values copied verbatim from the spec. Every task's requirements implicitly include this section, and execute's per-task and final reviews run against it as a standing lens. Omit only if the spec names no such rule.
- **Updates since spec** — drift you found while grounding. Omit if none.
- **Refactor scope** — copy from the spec if present; the explicit allowlist of existing modules open to reshaping. Omit if the spec had none.
- **File structure** — the table from Map the files.
- **Tasks** — each with a `Files:` block; an **Interfaces** block (`Consumes:` / `Produces:` — the exact signatures this task depends on and the ones it exposes, so an implementer who sees only this task's brief learns its neighbors' contracts; drop a side that's empty); a `Check:` line naming the per-task call (test-first / lightest-check / probe) and the exemplar to model after; a `Stop if:` line naming the assumption this task rests on that grounding could not prove, so the executor returns `BLOCKED` instead of improvising (omit when grounding proved every assumption); then one checkbox per behavior — each carrying its oracle and, where a test drives it, its seam (naming the existing journey test to extend when that seam is already walked) — ending on the task's `Verify:` step.
- **Coverage** — a table with one row per acceptance criterion in the spec (if the spec lacks a numbered list, enumerate the behaviors it describes yourself): `criterion | task # | verify step that proves it`. Every criterion gets a row; several rows proved along one workflow share that journey test's verify step — a shared cell is the minimal-suite shape, not a gap; a row whose verify cell is empty must say why (e.g. human-only smoke check) — silence is a gap, not a pass. Execute walks this table before claiming completion.
- **Smoke tests for the user** — anything the spec flagged as needing real-human verification. Omit if none.
- **Out of scope** — copy from the spec.

## Flow

### 1. Ground first

Read `.crank/<slug>/grounding.md` first, where it exists ([ARTIFACT-HOME.md](ARTIFACT-HOME.md) → Grounding), and verify-then-trust its entries: a covered point fact (a signature, a proven command) downgrades its re-derivation to one confirm at the citation or one re-run; a survey entry narrows the re-search to its recorded scope; an entry that has drifted is rewritten in place and joins **Updates since spec** with the rest of the drift below.

Before writing tasks, learn what you'll touch: read the files the spec names; grep for the symbols, types, and patterns you'll have to match; capture exact signatures, import paths, and any drift since the spec was written. Capture the repo's gate commands — test, lint, typecheck, build — exactly as this project runs them, and run each once so the plan's `Gates:` header line never names a gate that doesn't work. If no gate runs, the first task establishes one (a typecheck script, or a characterization test at the seam the work touches) before any task that changes behavior. Grounding is also where anything the plan will embed gets **surveyed** (Guidelines → Prose, pseudo-code, or embedded code), with the evidence kept for the step. Toolchain behavior the plan leans on — a build tool, bundler, CLI flag, or pinned dependency — gets surveyed the same way: run it once during grounding, never asserted from memory; a behavior you can't probe becomes a `Stop if:` line on the task that leans on it, naming the check that would settle it. Every claim the plan will state about the current code gets the same treatment (Hard Rules → Cite what you assert): run the count, the grep, or the command once, and keep its output as the step's citation. A change that tightens a shared contract — a field made required, a shared symbol renamed, a validator narrowed — has a mechanical **blast radius**: grep every call site once here, and let that list, not where the change conceptually belongs, decide which files the tasks name. A claim about a population — the only caller, no other use, the canonical helper, an absence — records the scope searched, per [ARTIFACT-HOME.md](ARTIFACT-HOME.md) → Grounding, which is also where a claim with no home in a step banks. And when the work keys, transforms, or migrates data that already exists (a DB, corpus, file tree), run the proposed invariant over the full real dataset — round-trip every existing name, sweep every row — and record the count checked; canned fixtures can't stand in for the data the work will actually meet. Dispatch the wide reads per [SUBAGENT-TIERS.md](SUBAGENT-TIERS.md) → Dispatch or main thread — the file and symbol reads, the drift check, and the gate commands go out on the brief at References → Subagents; the embed survey, the toolchain probes, and the full-dataset sweep stay where you can read their output.

Close grounding by banking what this step proved to the grounding file: the proven `Gates:` commands, the single-test invocation pattern, toolchain probe outputs, and convention exemplars.

Completion criterion, all of:

- every spec-named file and symbol read (or its read delegated and returned), with exact signatures and import paths in hand;
- drift since the spec noted for **Updates since spec**;
- every `Gates:` command captured and proven to run;
- every artifact the plan will embed surveyed, its evidence in hand;
- every toolchain behavior the plan depends on probed or named as a plan risk;
- every claim the plan will state about the current code checked at its source, its citation in hand;
- any full-dataset invariant swept, its count recorded;
- the step's proven facts banked to the grounding file.

### 2. Map the files

For every file the plan touches, record **path / action (`create` / `modify` / `delete`) / responsibility (one line)**. One clear responsibility per file. Follow established patterns; don't unilaterally restructure unless a file you're already modifying has grown unwieldy (a task that would push it past ~1,000 lines is the canonical trigger — plan the decomposition, don't defer it) or the spec's **Refactor scope** names it for reshaping.

If you can't state a `create`'d file's responsibility without "passes X to Y" or "wraps Z", it fails the deletion test — fold it into its caller rather than adding a pass-through module. (This applies to new files and to files named in the spec's **Refactor scope**, which are deliberately open to reshaping; files outside that scope keep their established boundaries.)

Every `modify` should trace to a surface the spec named. A change that threads a new boolean, mode, or special-case branch through a file the spec never mentions is **spaghetti growth** — record the spec gap in **Updates since spec** rather than tangling the shared path.

When one concept forces `modify` rows across several files in lockstep, that is a missing seam, not a wide change: record it in **Updates since spec** as a Refactor scope candidate naming the module that should own the concept, rather than planning N synchronized edits.

Completion criterion: every file the plan touches has a path / action / responsibility row, every `create` passes the deletion test, and every `modify` traces to a spec-named surface.

### 3. Decompose

A **task** is independently committable (green tree at end), implements one cohesive thing. Execute supplies the working rhythm — failing test → minimal impl → verify → commit — so size tasks to that cycle rather than scripting it. When a task covers more than one behavior, its steps slice **vertically** — one **tracer bullet** at a time, never a **horizontal slice** (both defined in VOCABULARY.md). Order tasks so each builds on the prior green tree. **Split trigger** — if a task would yield two changes that each leave a green tree and each prove a distinct spec behavior (two unrelated acceptance criteria, or a refactor plus the feature that rides on it), make them two tasks; fold setup, config, and doc edits into the task that needs them rather than giving them their own.

When the spec's **Refactor scope** reshapes a module, **replace tests, don't layer them**: the task that adds tests at the deepened interface must also *delete* the superseded tests on the old shallow interface — write the literal step (`delete the N tests in foo.test.ts`), don't just describe the new ones. Old shallow-module tests left layered under new ones are maintenance cost protecting nothing.

A Refactor scope module with no test at its seam gets a **characterization** task first: pin its current behavior through the seam, watch it pass, then reshape. The reshape task's RED is a failing assertion extended onto that test.

**Wide refactors are the exception to the one-task green tree.** A **wide refactor** is one mechanical change — rename a shared symbol, retype a column — whose blast radius fans across the codebase, so a single edit breaks call sites everywhere at once and no one task can land it green. Don't force it into one tracer bullet; sequence it as **expand–contract**: an *expand* task adds the new form beside the old so nothing breaks, *migrate* tasks move call sites over in batches sized by blast radius (per package, per directory) — each batch still ends on a green tree because the old form stands — and one *contract* task deletes the old form once no caller remains. If even the batches can't stay green alone, keep the sequence but say so in the plan: green is promised only at a final integrate-and-verify task.

Whether a given task is **test-first** or a **lightest-check** is a per-task call — see Guidelines → Test-first or lightest-check.

Completion criterion: every task is independently committable, right-sized per the split trigger, and ordered so each builds on the prior green tree — no task bundles two green-tree outcomes.

### 4. Read back the shape

Decomposition settled the shape; before writing the tasks in full, read it back per [SKILL.md](SKILL.md) → Phase gates, reading [READBACK.md](READBACK.md) here. The material to walk: the file map first (the actual path / action / responsibility rows), then the task sections — each showing what it builds and the judgment calls behind it, such as a test-first vs. lightest-check call where that's a real call.

### 5. Write the tasks

Read [PLAN-TEMPLATE.md](PLAN-TEMPLATE.md), then write the plan into that shape, carrying the material the readback approved in as vetted (READBACK.md → Carry what was approved). Give each task the blocks listed at Deliverables → **Tasks**. Two calls are step 5's: which exemplar the `Check:` line names — the existing test grounding read at that seam, or for a lightest-check task the file that shows the code pattern — and how far each behavior climbs from prose toward embedded code (see Guidelines → Prose, pseudo-code, or embedded code).

Every `Verify:` step names exact success (`1 passed`, exit 0, status 200) and a deterministic instrument — the task's test, a `Gates:` command, or a **probe** (its oracle and exact expected output pinned here, ending in its deletion) — "tests pass" is not enough. A test must drive the production seam the spec named, never a **dead seam**. Name the seam in the behavior line so the specified test and the production wiring point at the same place; a test case specified in prose can still be an **implementation-detail test** — an oracle read through a back channel instead of the seam is one. And it must pin a behavior no earlier line's test already pins: where the Coverage table shows the workflow already walked, the behavior line extends that journey test with its assertion — a **redundant test** is a plan defect, not extra safety.

Route reuse by name: if grounding (or the spec) surfaced an existing utility, the task names it and the contract goes through it — a bespoke near-duplicate is architectural drift. When no in-repo helper fits, reach in order — the stdlib, then a native platform feature (a DB constraint over app code, `<input type="date">` over a date-picker lib), then a dependency already in the manifest — before adding a new one; never add a dependency for what a few lines do, and a new dependency the spec's **Tech stack** didn't pin is an **Updates since spec** item to resolve, not a quiet import. And a contract that only types with a cast, `any`, or a new optional parameter is unclear: an **Updates since spec** item to resolve, not something to paper over inline.

**Completion criterion**, all of:

- every behavior the spec lists lands in a task's behavior line or verify, proved by walking the spec to build the **Coverage table** — that walk *is* how you check yourself;
- every `Verify:` names an exact command and its exact success reading;
- every test-driven behavior names the production seam it drives;
- every reuse the grounding surfaced is named in the task that needs it;
- every claim about the current code carries its citation, and no uncited assertion survives in a step;
- the finished file's counts read back clean — `tasks: <N> / coverage rows: <N> / placeholders: <N> / criteria <first>..<last>` — one Coverage row per acceptance criterion and zero placeholders. Count them with a command over the file and state the line; counting by eye is what lets a criterion go missing.

A spec that names five keys and a plan that tests two is an incomplete plan, not a smaller one. And "smaller" never means thinner safety: trust-boundary validation, data-loss and error handling, security, and accessibility are behavior, not surface — keep each in a task and a Coverage row even where trimming would shorten the plan; where the spec only implies one, surface it in **Updates since spec** rather than dropping it.

### 6. Adversarially review

Read [PLAN-REVIEW-BRIEF.md](PLAN-REVIEW-BRIEF.md) and dispatch it per [SKILL.md](SKILL.md) → Phase gates, substituting the plan's absolute path and the spec's path into it. If the spec exists only in the conversation (no file), drop the spec-path sentence from the brief and paste the spec's behavior list (or acceptance criteria) into the brief instead.

### 7. Hand back

The plan is the bottom of this skill's pipeline. Hand off per [SKILL.md](SKILL.md) → Phase gates, and stop there: executing is a deliberate act the user starts explicitly.

- **Next:** `/crank-execute .crank/<slug>/plan.md` — in this session or a fresh one; the plan is self-contained.

Completion criterion: the path and the `/crank-execute` command are stated and you've stopped — nothing invoked the user didn't opt into.
