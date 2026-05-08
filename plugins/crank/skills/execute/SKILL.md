---
name: execute
description: Executes a Crank plan.md — auto-triages between solo, sequential-subagent, or parallel-subagent execution, runs TDD per task, gates on verification evidence, and writes retro.md. Use whenever a plan.md exists and the user types /execute, says "implement the plan", "ship this", "build it", "run the plan", or otherwise asks to execute the work captured in a plan.
argument-hint: "[optional path to plan.md or its directory]"
---

# Execute

You are a senior engineer shipping the plan. Your job is to take the ordered tasks captured in `plan.md`, decide *how* to execute them, do the work (or delegate it), gate every "done" claim on real verification evidence, and finish by writing `retro.md`.

The implementer (you, or a subagent you dispatch) is capable. The plan is the source of truth — direct, don't redesign. Surprises become open items in `retro.md`, not silent reroutes.

## Hard rules (invariants)

- **Evidence before claims.** Never report a task done without running its verification command in this turn and reading the output. "Tests should pass" is a lie if you didn't run them.
- **TDD by default.** For each behavioral change, write the failing test first, watch it fail, then implement. Plan-specified exceptions (config flips, doc edits, generated code) skip TDD.
- **No scope creep.** Stick to the plan's task list. Discoveries that warrant deviation get logged to `retro.md` and surfaced — they do not silently expand the change.
- **Don't start on `main`/`master`** without explicit consent — branch first.
- **Plan is frozen.** Don't edit `plan.md` mid-execution. Deviations go in `retro.md`.

## Input contract

Locate `plan.md`:

1. **Explicit argument** — `$ARGUMENTS` may be a path to `plan.md`, a phase file, or its directory. Use it if present.
2. **Auto-detect** — otherwise:

   ```!
   ls -1t docs/crank/*/plan.md 2>/dev/null | head -5
   ```

   If exactly one exists, use it. If multiple, list them with mtime and ask the user — don't guess.
3. **None found** — say so and offer to invoke `crank:plan` first.

Read `plan.md` in full (and any phase files it indexes). Skim `spec.md` for context if the plan references decisions not restated. Do **not** re-derive the plan.

## Phase 1: Triage

Use TaskCreate to track the rest of the work so the user sees progress.

**Default to sequential subagents** for plans larger than ~3 tasks. Fresh context per task beats a crowded session — the only reason to stay solo is when tasks share state so heavily that the controller-overhead isn't worth it.

Decide execution mode by reading the plan's task list:

| Signal | Mode |
|---|---|
| ≤ ~3 tasks, *and* later tasks edit code from earlier tasks or share in-flight state | **Solo** — execute in this session |
| Multiple tasks with sequential ordering (later builds on earlier), but each task is self-contained once its predecessor lands | **Sequential subagents** — one Haiku implementer per task, you coordinate |
| Tasks touching disjoint files, no shared state, order doesn't matter | **Parallel subagents** — dispatch a batch of Haiku implementers concurrently |

State the choice in one sentence ("Triaging as parallel: tasks 2/3/5 touch disjoint files; tasks 1, 4, 6 sequential."). Mixed plans are normal — execute the parallel-safe slice in parallel, then resume sequential.

## Phase 2: Execute

### Solo mode

For each task in order:

1. Mark in-progress in TaskCreate.
2. Read the task's files block; open the files.
3. **TDD** — write the failing test, run it, confirm it fails for the right reason, then implement.
4. Run the task's verification commands. Read the output.
5. Commit with a message that names the task. Mark complete.

Stop on the first blocker (failing verification, ambiguous instruction, missing dependency). Don't push through — surface the blocker to the user with the actual error.

### Subagent modes (sequential or parallel)

You are the controller. Subagents never read `plan.md` themselves — you extract the full task text and required context and pass it in.

**Implementer subagent (default: Haiku, escalate to Sonnet for multi-file integration or judgment-heavy tasks).** The `model` field on `Agent()` overrides the agent definition's default model, so passing `"haiku"` is sufficient even with `general-purpose`:

```
Agent({
  description: "Implement task <N>: <slug>",
  subagent_type: "general-purpose",
  model: "haiku",
  prompt: "<full task text from plan.md>

  Context:
  - Branch: <name>, working dir: <repo root>
  - Files this task touches: <list>
  - Verification command(s): <list>
  - TDD: write failing test first unless plan says otherwise.

  Do the work, run verification, commit with message 'feat(<area>): <task summary>'.
  Constraints: do NOT push, do NOT amend earlier commits, do NOT touch files outside the files block above.
  Return: status (DONE / DONE_WITH_CONCERNS / NEEDS_CONTEXT / BLOCKED), commit SHA, verification output, and any concerns."
})
```

**Parallel dispatch:** when tasks are independent and touch disjoint files, send multiple Agent calls in a single message. Never dispatch two implementers that could touch the same file in parallel.

**Combined review subagent (Sonnet) — once per task after implementer reports DONE:**

```
Agent({
  description: "Review task <N>",
  subagent_type: "general-purpose",
  model: "sonnet",
  prompt: "Review commit <SHA> against this task spec:

  <full task text>

  Check both:
  1. Spec compliance — does the diff implement exactly what the task asks, no more, no less?
  2. Code quality — naming, duplication, error handling, test quality, obvious bugs.

  Return: APPROVED or CHANGES_REQUESTED with a specific list. Be concrete; cite file:line."
})
```

If `CHANGES_REQUESTED`, dispatch the same implementer subagent (same model) with the reviewer's feedback and re-review. Loop until `APPROVED`. Don't move to the next task with open review issues.

**Handling implementer status:**

- `DONE` → review.
- `DONE_WITH_CONCERNS` → read the concerns; address before review if they affect correctness, otherwise note and proceed.
- `NEEDS_CONTEXT` → provide the missing context, re-dispatch.
- `BLOCKED` → if context-shaped, more context + re-dispatch; if reasoning-shaped, escalate to Sonnet; if plan-shaped, escalate to user.

## Phase 3: Verification gate

Before claiming the plan is done:

1. Re-read `plan.md`'s task list. Tick each one against an actual commit / verification output you ran in this session.
2. Run the plan's overall validation commands (test suite, linter, typecheck, build) — fresh, in this turn. Read exit codes and full output.
3. If anything fails or any task is unverified, fix or surface — do not claim completion.

## Phase 4: Retro

Write `<plan-dir>/retro.md` (sibling to `plan.md`):

```markdown
# Retro: <plan title>

## Summary
- Tasks 1–N shipped, commits <first-SHA>..<last-SHA> on branch `<branch>`.

## Deviations from plan
- <task / what changed / why> (or "none")

## Open items
- <anything punted, follow-up work, surprises that future related work should know>

## Validation evidence
- <commands run + outcome>
```

Keep it short. `git log` already records *what shipped* — the durable signal here is **deviations** and **open items** that the diff alone won't tell the next reader.

Then hand back to the user with a one-line summary and the `retro.md` path. Do not auto-commit/PR — the user runs their own finish flow.

## Red flags — stop

These are the *moments* where you'd be tempted to break a hard rule. Catch yourself:

- Reaching for the word "should" or "probably" when describing test/build state.
- Implementer reported `BLOCKED` and you're about to retry with the same model and same context.
- About to dispatch parallel subagents whose files-blocks overlap.
- Letting an implementer's self-review stand in for the combined Sonnet review.
- Tempted to "just nudge" `plan.md` rather than write a deviation note.

## Integration

- Runs **after** `crank:plan`. Won't fabricate a plan — bounces back if none exists.
- Reads `spec.md` only as context; does not modify it.
- Writes only `retro.md` and the implementation diffs. Plan and spec stay frozen.
