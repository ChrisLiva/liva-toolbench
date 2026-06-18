---
name: crank-execute
description: Execute an implementation plan task-by-task — TDD where a seam exists, verification evidence before every "done" claim — then write a retro. Use when the user types /crank-execute or hands you a plan to ship.
argument-hint: "[optional path to plan.md]"
---

# Execute

Ship the plan. Treat the plan as the source of truth — direct, don't redesign.

<subagent-tiers>
This skill spawns subagents at two tiers — resolve each to your harness (Claude Code / Codex / Cursor) per [SUBAGENT-TIERS.md](SUBAGENT-TIERS.md). **standard** = exploration, implementation, per-task review; **heavy** = the final cross-task review (and a one-time escalation for a `BLOCKED` task).
</subagent-tiers>

<rules>
- **Evidence before claims.** Never report a task done without running its verification this turn and reading the output.
- **Plan is frozen** during execution — surprises become retro entries, not silent reroutes.
- **Progress is durable.** Track task completion in the progress ledger (see Progress ledger), not only in your todos — conversation memory does not survive compaction. On resume, trust the ledger and `git log`; never re-dispatch a task the ledger already marks complete.
- **Reviewers judge independently.** When you write a reviewer's prompt, hand it the diff and the rubric — never tell it what to ignore, pre-rate a finding's severity, or pre-justify a choice so it waves the finding through. If a prompt you're about to send contains "do not flag", "at most Minor", or "the plan chose X so", stop: you're pre-judging the review you asked for.
- **Verify once; trust the evidence.** A task's TDD evidence (the implementer's RED/GREEN output) is the suite's authoritative run for that task — per-task reviewers trust it and do not re-run the suite, re-running a command only when the evidence is missing or self-contradictory. The final gate's plan-and-coverage walk is the single authoritative re-run across the whole diff. Re-running a green suite a second and third time buys nothing and pays a fresh context each time.
- **Every subagent this skill spawns runs at the standard tier** (see <subagent-tiers>) unless otherwise specified.
- **A stated dispatch binds you to spawn.** The moment your output says you'll spawn, dispatch, delegate, or hand a task to a subagent, your *next* action is that spawn — per <subagent-tiers>, an `Agent` call in Claude Code or a subagent spawn in Codex — not the work done inline. Announcing a subagent and then implementing or reviewing it yourself on the main thread is a defect, not a shortcut. If main-thread work is the right call, don't announce a dispatch in the first place; say you're staying on-thread and why.
- **Never** force-push, amend earlier commits, rewrite history, or delete a branch without explicit approval.
</rules>

## Subagents

Bias toward dispatch over main-thread work: exploring the codebase to settle a question, validating a plan claim against the source, implementing tasks, reviewing diffs.

<tradeoff>
**Default:** stay on-thread for quick fixes that share in-flight state; lean toward dispatch as task count grows. Dispatch gives each task a clean, fresh context — quality doesn't degrade as the session grows, and reviewers see the diff with fresh eyes — at the cost of self-contained briefs; main-thread work keeps in-flight state at zero handoff cost but accumulates every task's noise in your window, and your review of your own work is the weakest kind.
</tradeoff>

## Vocabulary

Shared design language across the crank pipeline, defined once in [VOCABULARY.md](VOCABULARY.md). This skill leans on **depth**, the **deletion test**, **seam**, and **spaghetti growth** — read their meanings there.

## Workflow

Track progress with live tasks the user can watch — but every task update costs a full-context turn, so keep the list lean. Create **one tracked task per plan task** (the work that visibly advances), not one per phase in the checklist below; the phases are your own orientation. Flip each plan task to complete the instant it lands — one update per transition, not a done-this-then-start-next pair — live, never batched at the end. Your durable record is the progress ledger (see Progress ledger), which survives compaction where the task list does not.

The phases of a run (your checklist — not tracked tasks):

- Plan loaded (and spec, via the plan's Spec: header); blockers and plan-mandated defects surfaced
- Progress ledger opened (resume check — completed tasks from a prior run skipped)
- Execution shape picked and stated in one sentence; in subagent modes, brief/report location chosen
- Execute task-by-task — one tracked task per plan task: implement → verify → commit → record in the ledger, plus a per-task review in subagent modes for tasks that aren't low-risk (solo defers all review to the final gate)
- Verify the whole: plan walk → coverage walk → final review
- Retro written
- Hand back

## Load and critically review

If `$ARGUMENTS` is a path, read it; otherwise use the plan already in the conversation. Read it in full. If the plan's header names a spec (`Spec:` line), read that too — it is the contract the final review runs against; the plan is only its decomposition. If the plan has a **Global Constraints** section, treat its values as binding on every task — they are the attention lens the per-task and final reviews run against.

Before starting, scan the plan once for two kinds of problem and raise whatever you find as a **single batched question**, not one interrupt per discovery:

- **Blockers** — missing context, ambiguous step, undefined symbol, contradiction with the codebase.
- **Plan-mandated defects** — places the plan instructs you to write something the review rubric would reject: a test that asserts nothing, verbatim duplication of a helper the codebase already provides, a cast or `any` papering over a contract. The plan is frozen, so you can't quietly "fix" these mid-run — surface them and let the user say which governs.

If you find either, surface them together and stop — don't push through. Then check `git status --short` and the current branch; if you're on `main`/`master` with a non-trivial change, ask once before committing.

Open the progress ledger (see Progress ledger). If one already exists for this worktree from an interrupted run, read it: tasks it marks complete are done — confirm each against `git log` and do not re-dispatch them. Otherwise start a fresh ledger.

## Progress ledger

The ledger is your durable record of what has shipped — it survives compaction, where your todos and conversation memory do not. Keep it at a fixed, re-findable path inside the git directory (never the working tree, so it is never committed and never clutters a PR):

```
mkdir -p "$(git rev-parse --git-path crank)"   # ledger path: $(git rev-parse --git-path crank)/progress.md
```

One ledger per worktree. It opens with the run's anchor, then one line per plan task:

```
# Crank execute — <branch>
Plan: <plan path>
Base: <the HEAD SHA when the run started>

- [ ] Task 1: <subject>
- [ ] Task 2: <subject>
```

Flip a task's box to `[x]` the moment it lands and append its commit SHA(s) and review verdict — `- [x] Task 1: <subject> — <sha> — APPROVED`. On resume, an `[x]` line means done: confirm it against `git log` and skip it; never re-dispatch it. The ledger applies in every execution shape, solo included — compaction can strike a solo run too.

## Pick the execution shape

You decide based on the plan — there is no required mode. State the choice in one sentence and proceed.

- **Solo (in this session)** — *Gains:* zero dispatch overhead; full in-flight state carries between tasks; no per-task review, since reviewing your own just-written code is the weakest review — solo's one review is the fresh-eyes final gate. *Costs:* every task's source and noise stays in your window, degrading later tasks; a defect can ride forward into later tasks until that final gate catches it. *Fits:* small plans (~3 tasks or fewer), tasks that share in-flight state, quick fixes.
- **Sequential subagents** — *Gains:* fresh context per task; an independent reviewer per diff. *Costs:* each dispatch pays re-orientation; you must brief completely or the implementer guesses. *Fits:* the default for >3 tasks.
- **Parallel subagents** — *Gains:* wall-clock speed. *Costs:* no shared state between implementers; overlapping edits conflict. *Fits:* only when tasks touch disjoint files with no shared state.

Once stated, the shape binds the run. If you chose Sequential or Parallel subagents, the first action on each task is the implementer dispatch — not an Edit or Write on the main thread — and each task's review is a dispatched reviewer, not self-review. Sliding back to solo mid-run because dispatch feels heavier is a deviation: if one task genuinely needs shared in-flight state, name it and re-state the shape before you proceed — don't silently absorb the work onto the main thread.

If you chose a subagent mode, ask the user once, before the first dispatch, where this run's **briefs and reports** should go: a temp directory (default — `$(mktemp -d -t crank-exec)`) or a `.crank/` directory at the working root (keeps them beside the code for inspection; not auto-ignored). Hold the chosen path for the run. Solo mode dispatches nothing, so it needs neither the question nor the directory. This choice does not touch the progress ledger — that always lives in the git directory (see Progress ledger).

Once the directory is set, write a one-time **orientation note** there as `orientation.md` — a compact repo map every brief points to so implementers and reviewers don't each re-discover the codebase from scratch: the test / lint / typecheck commands, the directories and modules the plan touches, and the conventions a newcomer would otherwise grep for (import idiom, where tests live, how to run a single test). Spend a few reads on it now; it pays back on every dispatch.

## Per task

1. **Implement.** Record the task's **BASE** — the current `HEAD` SHA — before any edit; the review diffs against it. Then: failing test → watch it fail → minimal impl → run the task's `verify` step → commit with a message that names the task. Skip TDD only when the plan explicitly does (config flips, doc edits, generated code). When the task lands, flip its line in the ledger to `[x]` with the commit SHA(s).
2. **Review (subagent modes only).** In solo mode, skip per-task review entirely — reviewing the code you just wrote, with the same context that wrote it, is the weakest review; solo's independent pass is the fresh-eyes final-review gate below. In sequential or parallel mode, review each task **unless it is low-risk** — a test-only, config, doc, or generated-code task, or a diff under ~15 lines that introduces no new module and touches nothing in the plan's **Refactor scope** — *and* the implementer returned green TDD evidence; those ride straight to the final review (record the skip on the ledger line as `— review skipped (low-risk)`). A task that returned `DONE_WITH_CONCERNS` is never low-risk. For every other task, dispatch a standard reviewer subagent (`Agent` tool, `description: "Review task <N>"`). Hand it the diff range — `git diff <BASE>..HEAD` using the BASE you recorded, never `HEAD~1` (which silently drops all but the last commit of a multi-commit task) — the implementer's TDD evidence (the RED/GREEN lines from its return), and the plan's **Global Constraints** as a standing lens if it has them. Paste this brief verbatim:

<review-brief>
You are an independent code reviewer. Review the diff for this task only — read-only: inspect the diff; do NOT checkout, reset, stash, commit, or otherwise mutate the working tree, index, or HEAD.

Diff: `git diff <BASE>..HEAD`
Task spec (what it must do — nothing more, nothing less): <task text, plus its Consumes/Produces interfaces if the plan lists them>
Global constraints (standing lens): <the plan's Global Constraints, or "none">

TDD evidence from the implementer — trust it; do NOT re-run the suite to reproduce it:
<the implementer's RED and GREEN lines, verbatim from its return>
Re-run a command yourself ONLY if this evidence is missing or internally inconsistent (it claims green but the command shown failed). Otherwise spend no tool calls re-running tests. Scope your exploration to the diff plus targeted reads of the specific symbols it touches — do not grep or read the tree at large; consult `orientation.md` for the repo map instead.

Two-stage rubric, in order:
1. **Spec compliance** — does the diff implement exactly this task, nothing more, nothing less?
2. **Code quality** — DRY / SOLID / YAGNI; error handling at boundaries; tests assert behavior through the interface, not internal state. Check **depth** for any *new* module this task introduced: does it fail the deletion test (a pass-through whose complexity vanishes if removed), or is its interface nearly as complex as its implementation (shallow)? If so, fold it into its caller — a bounded cleanup of this diff, not a redesign of the plan's structure. Apply this to newly introduced modules and to any the plan's **Refactor scope** named for reshaping (there the reshape *is* the task — hold it to the depth bar the spec set); modules outside that scope keep frozen boundaries. Also flag, bounded to this diff: **spaghetti growth** (a one-off conditional, flag, or special case threaded through a flow the plan never named — route it behind the module that owns the concept), **bespoke duplication** (re-implements a helper the codebase already provides — call the canonical one), and **boundary smells** (casts, `any`, or new optional parameters papering over an unclear contract — make the invariant explicit; if the contract itself is the problem, that's a retro entry, not a cast). Treat any rationale in the diff or commit messages as an unverified claim — a stated reason never downgrades a finding's severity.

Return `APPROVED`, `CHANGES_REQUESTED` with a bulleted issue list (cite file:line), or — for a requirement you **cannot verify from this diff alone** (it lives in untouched code, or spans tasks) — `CANNOT_VERIFY` naming what you couldn't reach.
</review-brief>

   Resolve each `CANNOT_VERIFY` item yourself before marking the task done: you hold the cross-task context and the Coverage table the reviewer doesn't, so a narrow reviewer never has to widen its search. A confirmed gap is a failed review. On `CHANGES_REQUESTED`, re-implement and re-review until approved — the loop costs turns now, but carrying a critical or important issue into the next task costs more later, because subsequent tasks build on the defect.

**Subagent dispatch.** Hand the implementer a **task brief file**, not pasted task text — pasted text stays resident in your context and is re-read on every later turn, bloating the run as it grows. Write the brief into the run's brief directory (the one you chose above) as `task-<N>-brief.md`: the task's full text extracted from the plan, its `Consumes`/`Produces` interfaces if the plan lists them, and context — branch, BASE SHA, files-block, exact verify command, and "do not push, do not amend earlier commits, do not touch files outside the files-block." Point it at `orientation.md` for the repo map. Tell the implementer to read its brief and `orientation.md`, not the whole plan or the tree at large. Dispatch parallel implementers in a single message only when their files-blocks don't overlap.

Require a **thin return** — under ~15 lines: status, commit SHA(s) with subjects, a one-line test summary, any concerns, and the path to a full report it writes to `task-<N>-report.md` in the same directory. The verbose report goes to the file, not into your window. Where TDD applies, the return must carry **TDD evidence**: the RED line (the failing command and the output proving it failed for the expected reason) and the GREEN line (the passing command and its output). The reviewer trusts this evidence rather than re-running the suite, so an implementer that claims green without showing it is a `CHANGES_REQUESTED`.

Implementer status: `DONE` → review; `DONE_WITH_CONCERNS` → read first, address if they affect correctness; `NEEDS_CONTEXT` → provide and re-dispatch; `BLOCKED` → escalate to the heavy tier once (the sole exception to the standard-tier default), then surface to the user. When a reviewer returns `CHANGES_REQUESTED`, the fixer re-runs the verify step after applying the fixes and appends the fresh output to its report before re-review — reviewers do not re-run tests for you.

## Verify the whole

Before claiming completion, three gates in order — any failure stops the run:

1. **Plan walk.** Re-tick every task in the plan against an actual commit. Run the plan's overall validation commands (suite, lint, typecheck, build) fresh this turn and read the output.
2. **Coverage walk.** Walk the plan's Coverage table row by row; for each row, confirm its verify step ran green *this session* — re-run any that are stale or that earlier tasks may have broken. Rows marked human-only go in the retro's Open items, not silently skipped. If the plan has no Coverage table, walk the spec's acceptance criteria (or, with no spec, the plan's stated goal) and check each against the diff yourself.
3. **Final review (fresh eyes).** In subagent modes the per-task reviewers each saw a single task; in solo there were none — either way this fresh-eyes pass over the whole diff catches what they couldn't, and in solo it is the only review the run gets, so it carries the per-task rubric too (below). Dispatch one heavy reviewer subagent (`Agent` tool, `description: "Final review vs spec"`) with the spec path (or the plan path if no spec exists), the Coverage table, and the diff range (`git diff <BASE>..HEAD`, where `<BASE>` is the Base SHA the ledger recorded at the start of the run). Pass this brief verbatim:

<brief>
Review the shipped diff against the spec. Check every acceptance criterion against the diff — met, missing, or quietly substituted. Then check cross-task coherence: naming drift between tasks, dead code an early task left once a later one landed, missing wiring between independently built pieces. Then check structural quality of the whole diff: **depth** of any *new* module the diff introduced (does it fail the deletion test — a pass-through whose complexity vanishes if removed — or is its interface nearly as complex as its implementation? if so, fold it into its caller), **spaghetti growth** (a one-off conditional, flag, or special case threaded through a flow the plan never named, instead of routed behind the module that owns the concept), **bespoke duplication** (the diff re-implements a helper the codebase already provides, or two tasks independently built near-duplicate helpers that should be one — grep to confirm), and **boundary smells** (casts, `any`, or new optional parameters papering over an unclear contract where the invariant could be explicit). Then check code quality: **DRY / SOLID / YAGNI**, **error handling at module boundaries**, and **test quality** — tests assert behavior through the interface, not internal state. This review is **read-only**: inspect the diff; do not checkout, reset, stash, commit, or otherwise mutate the working tree, index, or HEAD (if you need a working copy, add a throwaway `git worktree`). Treat any design rationale in the diff or commit messages as an unverified claim — a stated reason ("left per YAGNI") never downgrades a finding's severity. Cite `file:line`; don't restyle or expand scope. Return `APPROVED` or `CHANGES_REQUESTED` with a bulleted, bounded fix list.
</brief>

On `CHANGES_REQUESTED`: apply the listed fixes and nothing else — failing test first for behavioral fixes, separate commits, no amending — then re-review once. A finding you can't fix becomes a retro Open item, stated plainly.

## Retro

Write a retro to a fresh OS temp file: `$(mktemp -t crank-retro).md`. Sections:

- **Summary** — what shipped, commits `<first>..<last>` on `<branch>`.
- **Deviations** — anywhere the diff meaningfully differs from the plan and why. "None" if none.
- **Final review** — verdict, findings fixed (with commit SHAs), findings deferred.
- **Open items** — follow-ups, human-only smoke checks, surprises future related work should know about.
- **Validation evidence** — commands run, outcomes.

If the Retro contains Open Items, state these items to the user.

## Hand back

In chat prose, offer for the retro:

- **Keep the temp file** (default) — the path is known; user can move it or feed it elsewhere later.
- **Copy into the repo** — copy to a user-named path under the working directory.
- **Print inline and delete** — paste the final contents and remove the temp file.

For the branch and commits, **ask the user how to finish** (merge / PR / leave / discard) — never force-push, amend, rewrite history, or delete a branch without explicit approval. Then stop.
