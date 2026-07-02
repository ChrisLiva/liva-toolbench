---
name: crank-execute
description: Execute an implementation plan task-by-task — TDD where a seam exists, verification evidence before every "done" claim — then write a retro. Use when the user types /crank-execute or hands you a plan to ship.
argument-hint: "[optional path to plan.md]"
---

# Execute

## Goal

Ship the plan. Treat the plan as the source of truth — direct, don't redesign.

## Hard Rules

- **Evidence before claims.** Never report a task done without running its verification this turn and reading the output.
- **Plan is frozen** during execution — surprises become retro entries, not silent reroutes.
- **Progress is durable.** Track task completion in the progress ledger (see Deliverables → Progress ledger), not only in your todos — conversation memory does not survive compaction. On resume, trust the ledger and `git log`; never re-dispatch a task the ledger already marks complete.
- **Reviewers judge independently.** A reviewer pulls its own facts: it runs the diff, reads its task from the plan, reads the implementer's evidence from the report file, and applies the fixed rubric file. Your dispatch hands it only pointers and the BASE SHA — never a description, characterization, or defense of the diff, never a reproduced or annotated rubric, never a sentence of your own about the task or the implementation. The dispatch is **assembled from pointers, not authored**: there is no free-text "context" or "notes" slot for you to fill, because the moment you write one — a "Note: … not a finding", a "this is the natural shape, NOT a horizontal slice", a "do not flag", an "at most Minor", a "the plan chose X so" — you've pre-judged the review you asked for. Your read of the diff belongs at the resolution step, after the verdict returns — never in the dispatch.
- **Verify once; trust the evidence.** A task's TDD evidence (the implementer's RED/GREEN output) is the suite's authoritative run for that task — per-task reviewers trust it and do not re-run the suite, re-running a command only when the evidence is missing or self-contradictory. The final gate's plan-and-coverage walk is the single authoritative re-run across the whole diff. Re-running a green suite a second and third time buys nothing and pays a fresh context each time.
- **Every subagent this skill spawns runs at the standard tier** (see References → Subagents) unless otherwise specified. Set the tier explicitly on every spawn — never leave it to default.
- **A stated dispatch binds you to spawn.** The moment your output says you'll spawn, dispatch, delegate, or hand a task to a subagent, your *next* action is that spawn — per References → Subagents, an `Agent` call in Claude Code or a subagent spawn in Codex — not the work done inline. Announcing a subagent and then implementing or reviewing it yourself on the main thread is a defect, not a shortcut. If main-thread work is the right call, don't announce a dispatch in the first place; say you're staying on-thread and why.
- **Never** force-push, amend earlier commits, rewrite history, or delete a branch without explicit approval.

## References

### Subagents

Bias toward dispatch over main-thread work: exploring the codebase to settle a question, validating a plan claim against the source, implementing tasks, reviewing diffs.

<tradeoff>
**Default:** stay on-thread for quick fixes that share in-flight state; lean toward dispatch as task count grows. Dispatch gives each task a clean, fresh context — quality doesn't degrade as the session grows, and reviewers see the diff with fresh eyes — at the cost of self-contained briefs; main-thread work keeps in-flight state at zero handoff cost but accumulates every task's noise in your window, and your review of your own work is the weakest kind.
</tradeoff>

This skill spawns subagents at two tiers — resolve each to your harness (Claude Code / Codex / Cursor) per [SUBAGENT-TIERS.md](SUBAGENT-TIERS.md). **standard** = exploration, implementation, per-task review; **heavy** = the final cross-task review (and a one-time escalation for a `BLOCKED` task).

### Vocabulary

Shared design language across the crank pipeline, defined once in [VOCABULARY.md](VOCABULARY.md). This skill leans on **depth**, the **deletion test**, **seam**, **spaghetti growth**, the **tracer bullet** (**vertical slice**), and the **implementation-detail test** — read their meanings there.

### Implementer artifacts

The orientation note, task brief, task report, and thin implementer return templates live in [IMPLEMENTER-BRIEF.md](IMPLEMENTER-BRIEF.md); Flow → Pick the execution shape tells you when to read it before writing any subagent brief.

### Per-task review rubric

The fixed per-task review rubric lives in [PER-TASK-REVIEW-BRIEF.md](PER-TASK-REVIEW-BRIEF.md). Flow → Pick the execution shape copies it into the brief dir verbatim; Flow → Per task points each reviewer at that copy. The reviewer then **pulls its own facts** — runs the diff, reads its task from the plan, reads the implementer's report — so the orchestrator supplies pointers only and reproduces neither the rubric nor the diff.

### Final review rubric

The fixed final cross-task review rubric lives in [FINAL-REVIEW-BRIEF.md](FINAL-REVIEW-BRIEF.md). Flow → Pick the execution shape copies it into the brief dir verbatim; Flow → Verify the whole points the final reviewer at that copy. The final reviewer then **pulls its own facts** — reads the spec and plan, runs the whole-diff range — so the orchestrator supplies pointers only.

## Deliverables

The primary deliverable is **shipped code** — the task-by-task commits, recorded in the progress ledger. The **retro** is a secondary doc.

### Progress ledger

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

### Retro

Written to a fresh OS temp file (see Flow → Retro). Sections:

- **Summary** — what shipped, commits `<first>..<last>` on `<branch>`.
- **Deviations** — anywhere the diff meaningfully differs from the plan and why. "None" if none.
- **Final review** — verdict, findings fixed (with commit SHAs), findings dismissed as false positives (each with the wider-context reasoning that disproved it), findings deferred (including any non-blocking Notes).
- **Open items** — follow-ups, human-only smoke checks, surprises future related work should know about.
- **Validation evidence** — commands run, outcomes.

## Flow

Track progress with live tasks the user can watch — but every task update costs a full-context turn, so keep the list lean. Create **one tracked task per plan task** (the work that visibly advances), not one per Flow step below; the steps are your own orientation. Flip each plan task to complete the instant it lands — one update per transition, not a done-this-then-start-next pair — live, never batched at the end. Your durable record is the progress ledger (see Deliverables → Progress ledger), which survives compaction where the task list does not.

### 1. Load and critically review

If `$ARGUMENTS` is a path, read it; otherwise use the plan already in the conversation. Read it in full. If the plan's header names a spec (`Spec:` line), read that too — it is the contract the final review runs against; the plan is only its decomposition. If the plan has a **Global Constraints** section, treat its values as binding on every task — they are the attention lens the per-task and final reviews run against.

Before starting, scan the plan once for two kinds of problem and raise whatever you find as a **single batched question**, not one interrupt per discovery:

- **Blockers** — missing context, ambiguous step, undefined symbol, contradiction with the codebase.
- **Plan-mandated defects** — places the plan instructs you to write something the review rubric would reject: a test that asserts nothing, verbatim duplication of a helper the codebase already provides, a cast or `any` papering over a contract. The plan is frozen, so you can't quietly "fix" these mid-run — surface them and let the user say which governs.

If you find either, surface them together and stop — don't push through. Then check `git status --short` and the current branch; if you're on `main`/`master` with a non-trivial change, ask once before committing.

Open the progress ledger (see Deliverables → Progress ledger). If one already exists for this worktree from an interrupted run, read it: tasks it marks complete are done — confirm each against `git log` and do not re-dispatch them. Otherwise start a fresh ledger.

### 2. Pick the execution shape

You decide based on the plan — there is no required mode. State the choice in one sentence and proceed.

- **Solo (in this session)** — *Gains:* zero dispatch overhead; full in-flight state carries between tasks; no per-task review, since reviewing your own just-written code is the weakest review — solo's one review is the fresh-eyes final gate. *Costs:* every task's source and noise stays in your window, degrading later tasks; a defect can ride forward into later tasks until that final gate catches it. *Fits:* small plans (~3 tasks or fewer), tasks that share in-flight state, quick fixes.
- **Sequential subagents** — *Gains:* fresh context per task; an independent reviewer per diff. *Costs:* each dispatch pays re-orientation; you must brief completely or the implementer guesses. *Fits:* the default for >3 tasks.
- **Parallel subagents** — *Gains:* wall-clock speed. *Costs:* no shared state between implementers; overlapping edits conflict. *Fits:* only when tasks touch disjoint files with no shared state.

Once stated, the shape binds the run. If you chose Sequential or Parallel subagents, the first action on each task is the implementer dispatch — not an Edit or Write on the main thread — and each task's review is a dispatched reviewer, not self-review. Sliding back to solo mid-run because dispatch feels heavier is a deviation: if one task genuinely needs shared in-flight state, name it and re-state the shape before you proceed — don't silently absorb the work onto the main thread.

If you chose a subagent mode, ask the user once, before the first dispatch, where this run's **briefs and reports** should go: a temp directory (default — `$(mktemp -d -t crank-exec)`) or a `.crank/` directory at the working root (keeps them beside the code for inspection; not auto-ignored). Hold the chosen path for the run. Solo mode dispatches nothing, so it needs neither the question nor the directory. This choice does not touch the progress ledger — that always lives in the git directory (see Deliverables → Progress ledger).

Once the directory is set, read [IMPLEMENTER-BRIEF.md](IMPLEMENTER-BRIEF.md) and write its `orientation.md` template there — a compact repo map every brief points to so implementers and reviewers don't each re-discover the codebase from scratch. Spend a few reads on it now; it pays back on every dispatch. In the same step, place the two review rubrics in the brief dir as fixed reference files: copy [PER-TASK-REVIEW-BRIEF.md](PER-TASK-REVIEW-BRIEF.md) to `review-rubric.md` and [FINAL-REVIEW-BRIEF.md](FINAL-REVIEW-BRIEF.md) to `final-review-rubric.md`, **verbatim** — a byte-for-byte copy, never a retype or a "fill it in." Do this now, before any task is implemented: with no diff yet in view there is nothing to pre-judge, so the rubrics freeze clean. Later you hand reviewers these files by reference and never reproduce a rubric in a dispatch yourself.

### 3. Per task

1. **Implement.** Record the task's **BASE** — the current `HEAD` SHA — before any edit; the review diffs against it. Then, per behavior in the task: failing test → watch it fail for the expected reason (not merely see red — a test that errors on a typo or missing import is red without proving anything) → minimal impl → run the task's `verify` step. A task covering several behaviors runs this cycle once per behavior as **tracer bullets** — `test A → impl A`, then `test B → impl B` — never as a **horizontal slice** (defined in VOCABULARY.md). Commit once the task is green, with a message that names the task. Skip TDD only when the plan explicitly does (config flips, doc edits, generated code). When the task lands, flip its line in the ledger to `[x]` with the commit SHA(s).
2. **Review (subagent modes only).** In solo mode, skip per-task review entirely — solo's independent pass is the fresh-eyes final-review gate below. In sequential or parallel mode, review each task **unless it is low-risk** — a test-only, config, doc, or generated-code task, or a diff under ~15 lines that introduces no new module and touches nothing in the plan's **Refactor scope** — *and* the implementer returned green TDD evidence; those ride straight to the final review (record the skip on the ledger line as `— review skipped (low-risk)`). A task that returned `DONE_WITH_CONCERNS` is never low-risk. For every other task, dispatch a standard reviewer subagent for the task. **The reviewer pulls its own facts; your dispatch is pointers only, never a description of the diff.** Give it: the **BASE SHA** you recorded, and tell it to run `git diff <BASE>..HEAD` itself (never `HEAD~1`, which silently drops all but the last commit of a multi-commit task); the **plan path and this task's number**, and tell it to read that task's block — with the plan's **Global Constraints** as a standing lens — from the plan itself; the path to the implementer's **`task-<N>-report.md`** for the TDD evidence; and `review-rubric.md` plus `orientation.md` in the brief dir. That is the whole dispatch — a fixed shape of pointers and one SHA. Write no "context", no "note", no sentence describing or defending the task or the diff: there is no slot for it, and your read of the just-written diff stays out of the review entirely. It belongs at the resolution step below.

   Resolve each `CANNOT_VERIFY` item yourself before marking the task done: you hold the cross-task context and the Coverage table the reviewer doesn't, so a narrow reviewer never has to widen its search. A confirmed gap is a failed review. This resolution step — not the brief — is where your cross-task knowledge belongs: if a returned finding is a false positive your wider context disproves (the reviewer flagged correct reuse, or read a cohesive single-seam test as a horizontal slice), dismiss it here with that reasoning. Pre-empting it in the brief would have pre-judged the review. An `APPROVED` that carries non-blocking **Notes** is still done — record them in the retro's Open items and move on; never spin the fix-loop over a nit. On `CHANGES_REQUESTED`, re-implement and re-review until approved — the loop costs turns now, but carrying a critical or important issue into the next task costs more later, because subsequent tasks build on the defect. But "until approved" is not "obey every round": if a re-review demands reversing a fix the previous round required — oscillation, not progress — stop and surface both verdicts to the user with your recommendation rather than ping-pong the code, and treat a re-review that merely restyles or reopens a point the last round settled as a finding to dismiss at this step, not an order to follow.

**Subagent dispatch.** Hand the implementer a **task brief file**, not pasted task text — pasted text stays resident in your context and is re-read on every later turn, bloating the run as it grows. Use [IMPLEMENTER-BRIEF.md](IMPLEMENTER-BRIEF.md) to write `task-<N>-brief.md` in the run's brief directory, point it at `orientation.md`, and require `task-<N>-report.md` plus the thin implementer return. Tell the implementer to read its brief and `orientation.md`, not the whole plan or the tree at large. Dispatch parallel implementers in a single message only when their files-blocks don't overlap.

Require the template's **thin return** — under ~15 lines, with status, commit SHA(s), test summary, concerns, report path, and TDD evidence. The verbose report goes to the file, not into your window. For multi-behavior tasks, the return must carry one RED→GREEN pair per behavior; one bulk RED→GREEN pair is a `CHANGES_REQUESTED`.

Implementer status: `DONE` → review; `DONE_WITH_CONCERNS` → read first, address if they affect correctness; `NEEDS_CONTEXT` → provide and re-dispatch; `BLOCKED` → escalate to the heavy tier once (the sole exception to the standard-tier default), then surface to the user. When a reviewer returns `CHANGES_REQUESTED`, the fixer re-runs the verify step after applying the fixes and appends the fresh output to its report before re-review — reviewers do not re-run tests for you.

### 4. Verify the whole

Before claiming completion, three gates in order — any failure stops the run:

1. **Plan walk.** Re-tick every task in the plan against an actual commit. Run the plan's overall validation commands (suite, lint, typecheck, build) fresh this turn and read the output.
2. **Coverage walk.** Walk the plan's Coverage table row by row; for each row, confirm its verify step ran green *this session* — re-run any that are stale or that earlier tasks may have broken. Rows marked human-only go in the retro's Open items, not silently skipped. If the plan has no Coverage table, walk the spec's acceptance criteria (or, with no spec, the plan's stated goal) and check each against the diff yourself.
3. **Final review (fresh eyes).** In subagent modes the per-task reviewers each saw a single task; in solo there were none — either way this fresh-eyes pass over the whole diff catches what they couldn't, and in solo it is the only review the run gets, so it carries the per-task rubric too — the final brief folds it in. Dispatch one heavy reviewer subagent for the final review. **It pulls its own facts; your dispatch is pointers only.** Give it: the **spec path** (or the plan path if no spec exists) and the **plan path**, and tell it to read them itself — including the plan's Coverage table; the **BASE SHA** the ledger recorded at the start of the run, and tell it to run `git diff <BASE>..HEAD` itself; and `final-review-rubric.md` in the brief dir for its review axes and return format. Write no sentence describing or defending the diff — there is no slot for it.

On `CHANGES_REQUESTED`, vet each finding before you touch code — the final review's resolution step, counterpart to the per-task one above. The final reviewer is fresh-eyes but context-starved by design (pointers only, no cross-task memory), so a finding can be a false positive your spec-and-plan context disproves: it read correct reuse as duplication, or called an acceptance criterion missing that a file outside its narrow read already satisfies. Dismiss those here with stated reasoning, recorded in the retro's Final review section so the dismissal is auditable, not a silent exit from the gate — and dismiss only what you can actually disprove, never what you'd rather not fix; a confirmed gap is still a failed review. Apply the surviving fixes and nothing else — failing test first for behavioral fixes, separate commits, no amending — then re-review once. A finding you can't fix becomes a retro Open item, stated plainly. An `APPROVED` that arrives with non-blocking **Notes** routes them to the retro's deferred findings, never the fix-loop. If a surviving finding would reverse a change an earlier per-task review required — oscillation, not progress — don't flip it blind: stop and surface both verdicts to the user with your recommendation.

### 5. Retro

Write a retro to a fresh OS temp file: `$(mktemp -t crank-retro).md`, with the sections listed in **Deliverables → Retro**.

If the Retro contains Open Items, state these items to the user.

### 6. Hand back

In chat prose, offer for the retro:

- **Keep the temp file** (default) — the path is known; user can move it or feed it elsewhere later.
- **Copy into the repo** — copy to a user-named path under the working directory.
- **Print inline and delete** — paste the final contents and remove the temp file.

For the branch and commits, **ask the user how to finish** (merge / PR / leave / discard) — never force-push, amend, rewrite history, or delete a branch without explicit approval. Then stop.
