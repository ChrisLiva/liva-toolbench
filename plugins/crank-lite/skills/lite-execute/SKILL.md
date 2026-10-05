---
name: lite-execute
description: "Execute an implementation plan task by task: implement, verify, review, and commit the work."
argument-hint: "[path to plan.md, or a .crank/ plan slug]"
disable-model-invocation: true
---

You are the orchestrator of one plan's execution. Every effort's artifacts live in one directory, `.crank/<slug>/`, per [ARTIFACT-HOME.md](ARTIFACT-HOME.md); read it before resolving or writing any artifact.

## Steps

1. Resolve the plan.
2. Read its Progress block and confirm each done task (Plan state).
3. Resolve the subagent tiers.
4. Set the Bound and pick the shape (Shape).
5. Write the Pre-flight lines into the plan's Progress block (Pre-flight).
6. Run the task loop through the Bound (Implement).
7. A run that ends with boxes unchecked ends as a short run. A run that ends with every box checked goes on to Review, Close the loop, and Retro; when `.crank/<slug>/retro.md` already exists, report the plan done and stop.

## Resolve the plan

Take the first case that matches:

1. **Explicit path**: read it as-is; the slug is the plan's parent directory name. A file with no task list, such as a spec, PRD, or brainstorm, is not a plan: say so, recommend the plan phase (`/crank-lite plan …`), and stop.
2. **Bare slug**: resolves to `.crank/<slug>/plan.md`.
3. **No argument, plan in the conversation**: derive a slug from the plan's title, write the plan to `.crank/<slug>/plan.md`, and use that file.
4. **No argument, exactly one plan on disk**: use it without asking.
5. **No argument, several plans**: ask via a structured question listing each plan with its status (see Plan state). An effort directory without a `plan.md` (a spec-only effort, say) shows as "no plan yet" and is not executable.
6. **No argument, no plans anywhere**: say so and recommend the plan phase (`/crank-lite plan …`).

## Plan state

Durable progress lives in a `## Progress` block directly under the plan's title. It opens with the current run's Pre-flight lines (see Pre-flight). `Base` is HEAD before the first task, and each task has one line carrying its subject. When a task's **check** has passed and its commit lands, flip its box and put the commit SHA right after the subject, ahead of any `— open:` or `— note:`:

```
## Progress

Base: 9f8e7d6
- [x] Task 1: Add the parser — a1b2c3d
- [ ] Task 2: Wire the CLI flag
```

On invocation, read this block first. An `[x]` line is done: confirm it in `git log` by its SHA, or after a squash or rebase merge by its commit subject (`git log --grep`), and never redo it. A done task that neither search finds stops the run; tell the user. A plan's status reads off this block: *not started* (no block), *in progress* (unchecked boxes remain), *done* (all `[x]`).

The plan's **grounding** is the file its `Grounding:` header names, or else its `## Grounding` section, one `- <claim> | <evidence> | <phase>, <date>` line per fact ([ARTIFACT-HOME.md](ARTIFACT-HOME.md) → Grounding). Confirm an entry at its evidence before you build on it.

In a plan with a Stages table, every task number in a message to the user carries its stage, as in `Task 14 (stage 2 of 3)`. The task that closes a stage also names its gate and that stage row's exit state, as in `Task 18 (stage 2 of 3, gate): <exit state>`. Progress lines, commit messages, and the Pre-flight lines keep the bare task number.

A task's **check** is the first of these that exists:

1. the check the plan names for that task;
2. a gate command the plan names: in its verification checks, its `Gates:` header, or its grounding;
3. the repo's typecheck plus the test file covering the touched behavior. A task with no such test gets one at the seam it changes; a task with no testable behavior, such as docs, gets the repo's typecheck or lint.

Read the check's output in the same turn it runs. When a change has no test seam, validate it with a **probe** and treat its passing output as the check.

## Subagent tiers

Resolve the tiers once per run, before the Pre-flight lines, and reuse the mapping at every dispatch. The source of truth is a subagent model preference stated in the user instructions already loaded this session (user- and project-level `CLAUDE.md` / `AGENTS.md`); it is binding: map the tiers onto it, even when it names a weaker model than a fallback below, and a preference that covers all subagent work covers implementers too. The block below is a fallback only, for a session whose loaded instruction files state no such preference:

<subagent-tiers>
- **standard** fallback (implementers): Claude Code `model: sonnet` · Codex Luna at high effort · Cursor Composer
- **heavy** fallback (adversarial review): Claude Code `model: opus` · Codex Sol at high effort · Cursor Sol at high effort
</subagent-tiers>

## Shape

The run's tasks are its unchecked Progress lines up to and including the **Bound**, the task the run ends after: the plan's last task, or an earlier one the user named. Take the first shape that matches the run's tasks:

1. **Solo**: the run has three tasks or fewer. Implement them inline on this thread. Count only the run's tasks: a twelve-task plan resumed at Task 10, or bounded at Task 2 with Task 1 done, is solo.
2. **Parallel**: the tasks touch disjoint file sets and their checks can run concurrently. Standard-tier subagents implement them, dispatched per [DISPATCH.md](DISPATCH.md).
3. **Sequential**: every other run, including tasks that share files, build on an earlier task's output, or serialize on one build directory. One standard-tier subagent per task, dispatched per [DISPATCH.md](DISPATCH.md), in plan order.

The shape you state binds the run: in a sequential or parallel run, the first action on each task is a dispatch, not an inline edit.

Every dispatch, implementer or reviewer, is a **blocking call**. When the harness offers a blocking wait on a subagent, wait on it. When the harness instead resumes you with a completion notification, end your turn at the spawn and let the notification resume you. When the result comes back in the same call, read it there. Ending your turn while a dispatch is out is safe only under that notification; under any other harness it ends the run. A wait that comes back before the subagent does, such as a timeout, is not a return, so wait again. Either way, read the return before anything else moves, and leave the dispatched work to the dispatch: no sleeping, polling, or doing its task yourself while it is out. A dispatch is **stalled** when a user message, or a notice that the subagent ended without returning, resumes you while it is still out. Run `git status` and `git diff` on its task's files once, then resume it when the harness can still reach that subagent, and otherwise dispatch the task again with the files it already changed on its `Settled:` line. A second stall on the same task is a decision under Detours and stops.

## Pre-flight

Every invocation, resumed runs included, write these lines with every line filled at the top of the plan's `## Progress` block, between the heading and `Base:`, replacing the lines an earlier run left there. When the plan has no Progress block yet, this same edit adds it, with `Base:` and one unchecked line per task. This edit is the run's first file change, ahead of every other edit, commit, and dispatch, and its diff is the user's one look at the models, shape, and bound before a long run. Then continue in the same turn.

```
## Progress

Pre-flight: branch <current branch>
Shape: <sequential | parallel | solo>
Subagents: standard = <model> (implementers) · heavy = <model> (adversarial review) · resolved from <user CLAUDE.md | project CLAUDE.md/AGENTS.md | harness fallback>
Tasks: <N> (<M> remaining, <R> this run)
Bound: <Task <N>, the plan's last | Task <N>, the user's stop | Task <N>, the stage <S> gate the user named>
Base: <HEAD before the first task>
```

Fill rules, line by line:

- `Subagents`: the resolved model names, never bare tier labels. `resolved from` names the instruction file whose subagent preference you mapped the tiers onto, or `harness fallback` when no loaded instruction file states one. A solo run's line reads `Subagents: heavy = <model> (adversarial review) — implementation inline · resolved from <source>`.
- `Tasks`: `<M>` is the Progress block's unchecked boxes, or `<N>` before the block exists. `<R>` is the run's tasks, the unchecked ones up to and including the Bound; Shape counts `<R>`.
- `Bound`: the plan's last task, or an earlier one the user's ask named (`stop after Task 4`; `stop at the stage 1 gate` means the last task of stage 1 in the plan's Stages table). A Stages table on its own leaves the bound at the last task.

Completion criterion: the plan's Progress block opens with this run's filled Pre-flight lines, written before any other edit, commit, or dispatch. Your reply need not repeat them.

## Implement

Before the first task:

- Read the `## Verification language` section of [VOCABULARY.md](VOCABULARY.md), plus the **seam** entry above it, and the plan's **Global Constraints** section when it has one. Global Constraints bind every task alongside the task's own lines.
- Read the `While implementing` and `Detours and stops` sections of [IMPLEMENTER-BRIEF.md](IMPLEMENTER-BRIEF.md). In a solo run, hold your inline work to them, and handle each finding they tell an implementer to return under Detours and stops below; in every run, hold your own fixes to them.
- Find each `Prototype:` line that names a winner, in the plan and in the spec its `Spec:` header names, and read the winning variant at the path it names, or the block copied beneath it. Each task that builds or reshapes a line's surface gets that line on its dispatch's `Prototype:` slot; in a solo run, build that surface from the variant yourself.
- Run `git status --porcelain` and keep its file list: those files hold the user's uncommitted work.
- If the plan has no Progress block, add it.

Then run this loop for each of the run's tasks, in plan order. A sequential run sends the next task's dispatch only after the previous task's check passed and its commit landed. A parallel run sends its dispatches in one message and waits on them as blocking calls, reading each return as it arrives; once every dispatch has returned, it runs steps 2 to 5 for each task in plan order.

1. **Implement.** Sequential and parallel: dispatch the task per [DISPATCH.md](DISPATCH.md). Solo: implement it inline.
2. **Check.** Run the task's check yourself and read its output. A failing check goes back to the implementer with its output, or in a solo run, to your own fix, at most twice. A check that still fails, or a return that reports a reroute or an observed `Stop if:`, goes to Detours and stops below.
3. **Commit.** Run `git status`. Stage only the files this task changed, by path, and commit only those paths (`git commit -- <paths>`). A file this task changed that was on the pre-run list holds user edits: ask the user before committing it.
4. **Record.** Flip the task's Progress line to `[x]` with the commit SHA. When the task took a detour, add its corrected fact to the plan's grounding in the same step.
5. **Stage gate.** When this task closes a stage in the plan's Stages table, run every gate command the plan names. A red gate is fixed before the next task, unless the same command also fails at `Base` (Review step 1); that failure is a retro note.

The loop hands the turn back to the user in two cases: step 3's question about a pre-run file, after which the loop carries on from step 3 with the user's answer, and a **decision** from Detours and stops, which ends the run. Everything else leads straight to the next step in the same turn: a subagent's return, a check's output, a commit, a stage gate, a detour. A progress report between tasks is not a stopping point. Completion criterion: every task through the Bound is checked, or a decision the user must make ended the run.

## Detours and stops

The plan's destination is frozen; the road is not. Settle every surprise that leaves what ships unchanged, and classify each surprise by what it does to what ships:

| You find | It is | Then |
| --- | --- | --- |
| A bug, a stale detail (renamed symbol, moved file), or a failed assumption blocks the task, and the smallest fix still ships exactly what the plan promises | a **detour** | Fix it and note it for the retro's deviations. Beside the task's Progress flip, append the corrected fact as one line to the plan's grounding, or rewrite in place the entry it contradicts, so a resumed run stops re-hitting the same stale detail. |
| A `Stop if:` condition the plan wrote on the task, observed | a **stop** | Settle it before you stop anything. Read the code the condition names and look for a route that code already offers, such as an existing parameter, helper, or pattern used the way its other callers use it, that ships exactly what the task promises and edits no code outside the task's own additions. Such a route makes the stop a detour. Take it inline in a solo run, or dispatch the task again with the route on its `Settled:` line ([DISPATCH.md](DISPATCH.md)). A stop with no such route is a decision. |
| A check that still fails after two fixes | a **stuck check** | Diagnose it yourself. Read its output and the code it names, and run a **probe** when the output leaves the cause open. The diagnosis is done when you can name the cause and quote the output line or probe reading that shows it; when your probes leave the cause open, the stuck check is a decision. When the fix for that cause still ships what the plan promises, make one more fix that carries the diagnosis, inline in a solo run or by dispatching the task again with the diagnosis on its `Settled:` line. A check that fails after that fix is a decision. |
| A **reroute**, meaning a fix that would change what ships; a stop with no route the code offers; a stuck check with no diagnosed cause or that failed its diagnosed fix; or a second stall on the same task | a **decision** | Stop the run, and put the decision to the user in the short-run report. |
| A pre-existing bug off the plan's path | a retro note | Record it for the retro and leave it unfixed. |

A settled stop and a diagnosed stuck check send the task back to step 2 of the loop. A decision leaves the task unchecked and its edits uncommitted; name those files in your report. In a parallel run, first finish steps 2 to 5 for every other task that returned. Then finish as a short run.

## Short run

A run that ends with boxes still unchecked in the `## Progress` block is a **short run**: its Bound fell short of the last task, or a decision ended it. The review, the loop-close, and the retro below belong to the run that ends with every box checked, since the reviewer reads the whole diff against the whole plan. Leave the plan able to brief whoever picks it up instead:

- Read each unchecked task's text against this run's diff. On its line, append `— open: <a question this run raised about it>` or `— note: <an interface, path, or contract its task text no longer matches>`, as many as apply. A task this run did not affect gets `— note: unaffected`, unless its line already carries one.
- On each task that landed this run, append `— note: <one line>` per observation the retro would otherwise have carried.
- Add each corrected repo fact, detour or not, with its evidence to the plan's grounding as under Detours and stops.
- Under the Progress block's `Base:` line, write `Stopped: <why> — resume at Task <N>`; the run that resumes overwrites it.

```
Base: 9f8e7d6
Stopped: Task 2's Stop if observed, every route sets JSON — resume at Task 2
- [x] Task 1: Add the parser — a1b2c3d
- [ ] Task 2: Wire the CLI flag — open: may the export route bypass the middleware?
- [ ] Task 3: Document the flag — note: unaffected
```

Then report the tasks that landed this run with their commit SHAs (or that none did), the tasks that remain, and `/lite-execute <plan path>` to resume. When a decision ended the run, also put that decision to the user in the report: what you found, the check's output where there is one, and numbered options with your recommendation marked. Completion criterion: every unchecked task was read against this run's diff and its line carries an `— open:` or `— note:`, the `Stopped:` line names the resume point, and a run that a decision ended gives that decision's numbered options in its report.

## Review

Once every box is checked:

1. Run the full suite once. Fix what this run broke and commit each fix, staged as in the task loop, so the reviewer's diff holds it. A failure counts as pre-existing only when the same test fails the same way at `Base`: check it in a temporary `git worktree` at `Base` with the repo's dependencies installed, then remove the worktree. A pre-existing failure is a retro note.
2. Walk the plan's **Coverage** table, when it carries one, row by row. Re-run a row's verify step unless it ran green this session after the last commit that touched a file it exercises. A row marked human-only goes to Close the loop as an action only a human can perform.
3. Dispatch one heavy-tier reviewer with this message, filled, and nothing else; the reviewer gathers its own facts:

   ```
   Read <absolute path to this skill's REVIEW-BRIEF.md> and follow it.
   Plan: <plan path>
   Spec: <the path the plan's Spec: header names, or none>
   Base: <the Progress block's Base SHA>
   Diff: git diff <Base>..HEAD
   Vocabulary: <absolute path to this skill's VOCABULARY.md>
   ```

   It returns each finding as `CONFIRMED` or `REFUTED` with the code evidence.
4. Fix every `CONFIRMED` finding and re-run the check that covers it, or record it in the retro's deviations with the reason it stands. Commit the fixes, staged as in the task loop.

Completion criterion: every `CONFIRMED` finding is fixed and re-verified by the same check, or recorded in the retro's deviations with the reason it stands.

## Close the loop

Before the retro, settle every loose end with a command, read, or test this session: what earlier short runs left on the Progress lines, reviewer findings, plan risks, and your own "worth noting" observations. A loose end survives only as a decision the user must make or an action only a human can perform, written with your recommendation. A fact that cost this run a detour and would cost the next run the same, such as a fixture that breaks tests in a way the code does not show, a known flaky test, or a flag a toolchain command needs, outlives the effort: append one line carrying its evidence to the repo's `AGENTS.md`, `CLAUDE.md`, `CONTEXT.md`, or an ADR, whichever the repo already has, commit it, and name where it landed in the retro; with no such file it survives as a decision naming the line and its target.

## Retro

Record the retro to `.crank/<slug>/retro.md` and stop. Include, when each earns its place: what changed, verification run, review outcome, deviations from the plan, where any promoted fact landed, and any surviving decisions. Tell the user the commit SHAs this run landed and the retro path; when nothing survived the loop-close, say the work is complete.
