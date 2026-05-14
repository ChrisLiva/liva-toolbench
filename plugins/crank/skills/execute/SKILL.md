---
name: execute
description: Executes a Crank plan.md — auto-triages between solo, sequential-subagent, or parallel-subagent execution, runs TDD per task, gates on verification evidence, and writes retro.md. Use whenever a plan.md exists and the user types /execute, says "implement the plan", "ship this", "build it", "run the plan", or otherwise asks to execute the work captured in a plan.
argument-hint: "[optional path to plan.md or its directory]"
---

# Execute

Ship the plan. Take the ordered tasks in `plan.md`, decide *how* to execute them, do the work (or delegate it), gate every "done" claim on real verification evidence, and finish with `retro.md`. The plan is the source of truth — direct, don't redesign. Surprises become entries in `retro.md`, not silent reroutes.

## Hard rules

- **Evidence before claims.** Never report a task done without running its verification in this turn and reading the output. "Tests should pass" is a lie if you didn't run them.
- **TDD by default.** Failing test → watch it fail → implement. Plan-specified exceptions (config flips, doc edits, generated code) skip TDD.
- **No scope creep.** Stick to the plan's task list. Deviations get logged to `retro.md` and surfaced; they do not silently expand the change.
- **Plan is frozen.** Don't edit `plan.md` mid-execution.
- **Don't start on `main`/`master`** without explicit consent — see Workspace setup.

## Workspace setup

Check `git rev-parse --abbrev-ref HEAD`, `git status --short`, `git worktree list`. If already on a `crank/<slug>` branch or worktree (spec/plan set it up), confirm in one line and proceed. If on `main`/`master`/`trunk`, **stop and offer in chat prose** (not `AskUserQuestion`): **A.** new branch `git checkout -b crank/<slug>` (cheapest, reuses tree), **B.** new worktree via the `EnterWorktree` tool with `name: "crank/<slug>"` (recommended if tree is dirty, plan is L/XL, or user wants throw-away isolation — lands under `.claude/worktrees/` and switches the session into it), **C.** stay put (only if user says so). Wait for confirmation before acting. Never `git worktree add` to a sibling path; always use `EnterWorktree`. Record the branch and worktree path — you'll cite them in retro and cleanup.

## Locate the plan

Use `$ARGUMENTS` if it points to `plan.md`, a phase file, or its directory. Otherwise auto-detect via `ls -1t docs/crank/*/plan.md | head -5` — use it if exactly one, ask if multiple, offer `crank:plan` if none. Read `plan.md` in full plus any phase files it indexes. Skim `spec.md` for context if the plan references decisions not restated. Do not re-derive the plan.

## Phase 1: Triage

Track the rest of the work with TaskCreate. Decide execution mode by reading the task list:

| Signal | Mode |
|---|---|
| ≤ ~3 tasks **and** later tasks edit code from earlier tasks or share in-flight state | **Solo** — execute in this session |
| Sequential ordering (later builds on earlier), each task self-contained once its predecessor lands | **Sequential subagents** — one Haiku implementer per task, you coordinate |
| Tasks touch disjoint files, no shared state, order doesn't matter | **Parallel subagents** — dispatch a batch of Haiku implementers concurrently |

Default to **sequential subagents** for plans larger than ~3 tasks — fresh context per task beats a crowded session. State the choice in one sentence ("Triaging as parallel: tasks 2/3/5 touch disjoint files; tasks 1, 4, 6 sequential."). Mixed plans are normal — run the parallel-safe slice in parallel, then resume sequential.

## Phase 2: Execute

### Solo mode

For each task in order: mark in-progress, open the files block, write the failing test, run it, confirm it fails for the right reason, implement, run the task's verification, commit with a message that names the task, mark complete. Stop on the first blocker (failing verification, ambiguous instruction, missing dependency) and surface it with the actual error — don't push through.

### Subagent modes (sequential or parallel)

You are the controller. Subagents never read `plan.md`; you extract the full task text and required context and pass it in.

**Implementer** (default Haiku; escalate to Sonnet for multi-file integration or judgment-heavy tasks). The `model` field on `Agent()` overrides the agent definition's default, so passing `"haiku"` is sufficient with `general-purpose`:

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
  Constraints: do NOT push, do NOT amend earlier commits, do NOT touch files outside the files block.
  Return: status (DONE / DONE_WITH_CONCERNS / NEEDS_CONTEXT / BLOCKED), commit SHA, verification output, concerns."
})
```

**Parallel dispatch.** Send multiple Agent calls in a single message when tasks are independent and touch disjoint files. Never dispatch two implementers that could touch the same file in parallel.

**Combined reviewer** (Sonnet) — once per task after implementer reports `DONE`:

```
Agent({
  description: "Review task <N>",
  subagent_type: "general-purpose",
  model: "sonnet",
  prompt: "Review commit <SHA> against this task spec:

  <full task text>

  Check: (1) spec compliance — does the diff implement exactly what the task asks, no more, no less? (2) code quality — naming, duplication, error handling, test quality, obvious bugs.

  Return: APPROVED or CHANGES_REQUESTED with a specific list. Cite file:line."
})
```

On `CHANGES_REQUESTED`, re-dispatch the implementer (same model) with the reviewer's feedback and re-review. Loop until `APPROVED`. Don't move to the next task with open review issues.

**Implementer status:** `DONE` → review. `DONE_WITH_CONCERNS` → read concerns, address before review if they affect correctness, otherwise note and proceed. `NEEDS_CONTEXT` → provide it, re-dispatch. `BLOCKED` → context-shaped: more context + re-dispatch; reasoning-shaped: escalate to Sonnet; plan-shaped: escalate to user.

## Phase 3: Verification gate

Before claiming completion: re-read `plan.md`'s task list and tick each one against an actual commit and verification output you ran this session. Then run the plan's overall validation commands (test suite, linter, typecheck, build) fresh, in this turn. Read exit codes and full output. Fix or surface any failure — do not claim completion otherwise.

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

Keep it short. `git log` already records what shipped — the durable signal here is **deviations** and **open items** that the diff alone won't tell the next reader. Then go to Phase 5; do not hand back yet.

## Phase 5: Finish — offer cleanup and merge

Required step. Ask in plain chat prose (not `AskUserQuestion`). Detect state with `git rev-parse --abbrev-ref HEAD`, `git log --oneline <base>..HEAD`, `git worktree list` (`<base>` = the user's default branch). Tailor the options to what's actually true — skip worktree-removal if not in a worktree, skip merge if no new commits.

> "Execution complete. Commits `<first>..<last>` shipped on `<branch>`<` in worktree <path>` if applicable>. How do you want to finish up?
>
> - **Merge into `<base>` and clean up** — fast-forward (or `--no-ff` if the user prefers) into `<base>`, delete the branch, and (if the worktree was created via `EnterWorktree`) call `ExitWorktree` with `action: "remove"`. For worktrees created manually with `git worktree add`, run `git worktree remove <path>` from outside the worktree. Recommended when reviewed-or-self-reviewed and ready to land.
> - **Open a PR instead** — push `<branch>` to origin and create a draft PR via `gh pr create`. Recommended when human review is needed first.
> - **Leave it as-is** — branch and worktree stay where they are.
> - **Throw it away** — only on explicit request: `git branch -D <branch>` and either `ExitWorktree` with `action: "remove", discard_changes: true` (if entered via `EnterWorktree`) or `git worktree remove --force <path>` (manual worktrees). **Confirm twice** — destructive."

Recommend the option that fits context (PR for shared/production code, direct merge for solo or experimental work) but let the user decide. Execute the picked option and report what happened in one line. Never force-push, amend, rewrite history, or delete a branch/worktree the user didn't approve. Hand back with a one-line summary, the `retro.md` path, and final state (`branch merged and deleted` / `PR #123 open` / `branch and worktree left at <path>`).

## Red flags — stop

Catch yourself when:

- You reach for "should" or "probably" to describe test/build state.
- An implementer reported `BLOCKED` and you're about to retry with the same model and same context.
- You're about to dispatch parallel subagents whose files-blocks overlap.
- An implementer's self-review is standing in for the Sonnet review.
- You're tempted to "just nudge" `plan.md` rather than write a deviation note.

## Integration

Runs after `crank:plan`. Won't fabricate a plan — bounces back if none exists. Reads `spec.md` only as context. Writes only `retro.md` and the implementation diffs. Plan and spec stay frozen.
