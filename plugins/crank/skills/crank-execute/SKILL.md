---
name: crank-execute
description: Execute an implementation plan task-by-task with TDD, independent reviews, and a retro.
argument-hint: "[optional path to plan.md, or a .crank/ plan slug]"
disable-model-invocation: true
---

# Execute

## Goal

Ship the plan. Treat the plan as the source of truth — direct, don't redesign.

## Hard Rules

- **Evidence before claims.** Never report a task done without running its verification this turn and reading the output.
- **Destination frozen, road flexible.** What the plan ships — each task's goal, its contract, the architecture — is frozen. The road there is not: when a bug, stale detail (renamed symbol, moved file), or failed assumption blocks a task, fix it as a **detour** — the smallest change that still ships exactly what the task promises — and log it on the ledger line and in the retro's Deviations. A fix that would change what ships is a **reroute**: stop and surface it with your recommendation. Off-path surprises (a pre-existing bug the task doesn't hit) stay retro entries, never side quests.
- **Progress is durable.** Track task completion in the progress ledger (see Deliverables → Progress ledger), not only in your todos.
- **Reviewers judge independently.** A reviewer pulls its own facts: it runs the diff, reads its task from the plan, reads the implementer's evidence from the report file, and applies the fixed rubric file. Your dispatch hands it only pointers and the BASE SHA — no description, characterization, or defense of the diff, no reproduced or annotated rubric: anything you add beyond pointers pre-judges the review you asked for.
- **Verify once; trust the evidence.** A task's TDD evidence (the implementer's RED/GREEN output) is the suite's authoritative run for that task; the final gate's plan-and-coverage walk is the single authoritative re-run across the whole diff.
- **A stated dispatch binds you to spawn.** The moment your output says a task gets a subagent — or the run's chosen shape says so — your *next* action is that spawn, never the work done inline. If main-thread work is the right call, say you're staying on-thread and why (for a shape change, re-state the shape) instead of announcing a dispatch.
- **A dispatch is a blocking call.** From spawn to return the subagent owns the work: your next action is reading its return, and everything else — the next task, edits near its files, a peek at its progress — queues behind that return. In parallel mode the batch of spawns goes out in one message and blocks as one; every return is read before anything else moves. The one exit from the wait is the quiet-dispatch rule below.
- **Oscillation stops the loop.** A review round that demands reversing what a prior round required is oscillation, not progress — never flip the code blind; stop and surface both verdicts to the user with your recommendation.
- **A stop instruction bounds the unit of work, not the phase.** When the user says "do X, then stop," the run ends after X's verification, whatever X uncovers — newly discovered defects become surfaced findings with a recommendation, never a new fix round.
- **Off-plan fixes are bounded.** A fix that isn't a plan task gets exactly one investigation, one test-first fix, one review — routed through this skill's own dispatch shapes, never an ad-hoc harness workflow — then stop and report, whatever that review finds.
- **A quiet dispatch is reconciled, not narrated.** When a subagent is out past the point you expected it back, reconcile against durable state — `git log` since BASE, the ledger, its report file on disk — then resume the agent or surface the stall with your recommendation; a "standing by" turn is never the move.
- **Never** force-push, amend earlier commits, rewrite history, or delete a branch without explicit approval.

## References

### Subagents

Bias toward dispatch over main-thread work: exploring the codebase to settle a question, validating a plan claim against the source, implementing tasks, reviewing diffs.

<tradeoff>
**Default:** stay on-thread for quick fixes that share in-flight state; lean toward dispatch as task count grows. Dispatch gives each task a clean, fresh context — quality doesn't degrade as the session grows, and reviewers see the diff with fresh eyes — at the cost of self-contained briefs; main-thread work keeps in-flight state at zero handoff cost but accumulates every task's noise in your window, and your review of your own work is the weakest kind.
</tradeoff>

This skill spawns subagents at two tiers — resolve each to your harness (Claude Code / Codex / Cursor) per [SUBAGENT-TIERS.md](SUBAGENT-TIERS.md). **standard** = exploration, implementation, per-task review; **heavy** = the final cross-task review (and a one-time escalation for a `BLOCKED` task).

### Vocabulary

Shared design language across the crank pipeline, defined once in [VOCABULARY.md](VOCABULARY.md). This skill leans on **depth**, the **deletion test**, **seam**, the **probe**, **spaghetti growth**, the **tracer bullet** (**vertical slice**), the **implementation-detail test**, the **rewrite test**, the **journey test**, and the **redundant test** — read their meanings there.

## Deliverables

The primary deliverable is **shipped code** — the task-by-task commits, recorded in the progress ledger. The **retro** is a secondary doc.

### Progress ledger

The ledger is your durable record of what has shipped — it survives compaction, where your todos and conversation memory do not. Its home is a **probe, not a prescription** — try the git directory first, and on refusal fall back to the ignored `.crank/` directory, never the session scratchpad (which dies with the session):

1. Print the git-directory path, then create it — two plain commands, not a compound one-liner (sandboxes that guard the worktree reject compound shells):

   ```
   git rev-parse --git-path crank
   mkdir -p <the path it printed>
   ```

   The ledger is `<that dir>/progress-<slug>.md` — slug-keyed, so several plans' ledgers coexist; the slug is the plan's parent directory name.
2. If the harness refuses writes there — worktree isolation guards the shared `.git` path — use `.crank/<slug>/progress.md` at the worktree root instead: create `.crank/` with a `.crank/.gitignore` containing `*`, and note the fallback once.

One ledger per plan per worktree. It opens with the run's anchor, then one line per plan task:

```
# Crank execute — <branch>
Plan: <plan path, normally .crank/<slug>/plan.md>
Base: <the HEAD SHA when the run started>

- [ ] Task 1: <subject>
- [ ] Task 2: <subject>
```

Flip a task's box to `[x]` the moment it lands and append its commit SHA(s) and review verdict — `- [x] Task 1: <subject> — <sha> — APPROVED`. A task that took a detour appends it too — `— detour: <one line>` — so the retro's Deviations survive compaction. On resume, an `[x]` line means done: confirm it against `git log` and skip it; never re-dispatch it. The ledger applies in every execution shape, solo included — compaction can strike a solo run too.

### Retro

Written to the effort's `.crank/<slug>/` directory (see Flow → Retro). Sections:

- **Summary** — what shipped, commits `<first>..<last>` on `<branch>`.
- **Deviations** — every detour taken (what blocked, the fix), plus anywhere else the diff meaningfully differs from the plan and why. "None" if none.
- **Final review** — verdict, findings fixed (with commit SHAs), findings dismissed as false positives (each with the wider-context reasoning that disproved it), findings deferred (including any non-blocking Notes).
- **Open items** — only what survived Flow → Close the loop: each entry is a decision the user must make or an action only a human can perform, stated as that decision with your recommendation. Deferred findings and dismissals stay in the Final review section above — this section holds nothing you could have settled yourself.
- **Validation evidence** — commands run, outcomes.

## Flow

Track progress with live tasks the user can watch — but every task update costs a full-context turn, so keep the list lean. Create **one tracked task per plan task** (the work that visibly advances), not one per Flow step below; the steps are your own orientation. Flip each plan task to complete the instant it lands — one update per transition, not a done-this-then-start-next pair — live, never batched at the end. Your durable record is the progress ledger (see Deliverables → Progress ledger).

### 1. Load and critically review

Resolve the plan first — every effort's artifacts live in one directory, `.crank/<slug>/` at the working root:

1. **Explicit path** — read it as-is; the slug is the plan's parent directory name, and the ledger and `exec/` dir resolve deterministically from it.
2. **Bare slug** — resolves to `.crank/<slug>/plan.md`.
3. **No argument, plan in the conversation** — use it; derive a slug from the plan's title — its artifacts live in `.crank/<slug>/`.
4. **No argument, exactly one plan on disk** — use it without asking.
5. **No argument, several plans** — ask via a structured question listing each plan with its derived status: *not started* (no ledger in either home), *in progress* (unchecked boxes remain), *done* (all `[x]`). An effort directory without a `plan.md` (e.g. spec-only) shows as "no plan yet" and is not executable.
6. **No argument, no plans anywhere** — say so and recommend the plan phase (`/crank plan …`).

**Adopt legacy artifacts on encounter.** Resolving an artifact checks the per-plan path first, then the legacy flat path (`.crank/plan-<slug>.md`, `.crank/exec-<slug>/`, a fixed-name ledger — `<git-dir>/crank/progress.md` or worktree-root `.crank/progress.md`). On a legacy hit, move the file(s) into `.crank/<slug>/…`, rewrite the ledger's `Plan:` header to the new plan path, rename a fixed-name git-dir `progress.md` to `progress-<slug>.md` (slug taken from its `Plan:` header) — a legacy worktree-root `.crank/progress.md` moves to `.crank/<slug>/progress.md` the same way — and announce every new path so a user's saved link is updated once. Never clobber: if both the legacy and per-plan copies of an artifact exist, stop and ask instead of overwriting either. A git-dir ledger whose slug matches no `.crank/<slug>/` directory (plan deleted) is stale — surface it and offer deletion, never silently resume it.

Read the plan in full. If the plan's header names a spec (`Spec:` line), read that too — it is the contract the final review runs against; the plan is only its decomposition. If the plan has a **Global Constraints** section, treat its values as binding on every task — they are the attention lens the per-task and final reviews run against.

Before starting, scan the plan once for two kinds of problem and raise whatever you find as a **single batched question**, not one interrupt per discovery:

- **Blockers** — missing context, ambiguous step, undefined symbol, contradiction with the codebase.
- **Plan-mandated defects** — places the plan instructs you to write something the review rubric would reject: a test that asserts nothing, verbatim duplication of a helper the codebase already provides, a cast or `any` papering over a contract. Overriding what the plan explicitly instructs is a reroute, never a detour — surface them and let the user say which governs.

If you find either, surface them together and stop — don't push through. Then check `git status --short` and the current branch; if you're on `main`/`master` with a non-trivial change, ask once before committing.

Open the progress ledger (see Deliverables → Progress ledger); if one already exists for this plan in this worktree from an interrupted run, resume from it per that section, otherwise start fresh.

### 2. Pick the execution shape

You decide based on the plan — there is no required mode. State the choice in one sentence and proceed.

- **Solo (in this session)** — *Gains:* zero dispatch overhead; full in-flight state carries between tasks; no per-task review, since reviewing your own just-written code is the weakest review — solo's one review is the fresh-eyes final gate. *Costs:* every task's source and noise stays in your window, degrading later tasks; a defect can ride forward into later tasks until that final gate catches it. *Fits:* small plans (~3 tasks or fewer), tasks that share in-flight state, quick fixes.
- **Sequential subagents** — *Gains:* fresh context per task; an independent reviewer per diff. *Costs:* each dispatch pays re-orientation; you must brief completely or the implementer guesses. *Fits:* the default for >3 tasks.
- **Parallel subagents** — *Gains:* wall-clock speed. *Costs:* no shared state between implementers; overlapping edits conflict. *Fits:* only when tasks touch disjoint files with no shared state.

Once stated, the shape binds the run (Hard Rules → A stated dispatch binds you to spawn): in a subagent mode, each task's first action is the implementer dispatch and each task's review a dispatched reviewer — never work silently absorbed onto the main thread.

If you chose a subagent mode, create this run's **brief directory** — where briefs and reports go — at `.crank/<slug>/exec/` under the working root (create `.crank/` with a `.crank/.gitignore` containing `*` if missing; outside a git repo, fall back to a temp directory like `${TMPDIR:-/tmp}/crank-<slug>/exec/`) and state the path once. Hold the path for the run. Solo mode dispatches nothing, so it needs no brief directory. This choice does not touch the progress ledger — that resolves its own home (see Deliverables → Progress ledger).

Once the directory is set, read [IMPLEMENTER-BRIEF.md](IMPLEMENTER-BRIEF.md) and write its `orientation.md` template there — a compact repo map every brief points to so implementers and reviewers don't each re-discover the codebase from scratch. Spend a few reads on it now; it pays back on every dispatch. In the same step, place the three review rubrics in the brief dir as fixed reference files: copy [PER-TASK-REVIEW-BRIEF.md](PER-TASK-REVIEW-BRIEF.md) to `review-rubric.md`, [FINAL-REVIEW-BRIEF.md](FINAL-REVIEW-BRIEF.md) to `final-review-rubric.md`, and [RE-REVIEW-BRIEF.md](RE-REVIEW-BRIEF.md) to `re-review-rubric.md`, **verbatim** — a byte-for-byte copy, never a retype or a "fill it in." Do this now, before any task is implemented: with no diff yet in view there is nothing to pre-judge, so the rubrics freeze clean.

### 3. Per task

1. **Implement.** Record the task's **BASE** — the current `HEAD` SHA — before any edit; the review diffs against it. Then, per behavior in the task: failing test → watch it fail for the expected reason → minimal impl → run the task's `verify` step. The RED is a fresh test only at a fresh seam — where a journey test already walks this seam, the RED is a failing assertion extended onto it. A task covering several behaviors runs this cycle once per behavior as **tracer bullets** — `test A → impl A`, then `test B → impl B` — never as a **horizontal slice** (defined in VOCABULARY.md). Commit once the task is green, with a message that names the task. Skip TDD only when the plan explicitly does (config flips, doc edits, generated code). When the task lands, flip its line in the ledger to `[x]` with the commit SHA(s).
2. **Review (subagent modes only).** In solo mode, skip per-task review entirely — solo's independent pass is the fresh-eyes final-review gate below. In sequential or parallel mode, review each task **unless it is low-risk** — a test-only, config, doc, or generated-code task, or a diff under ~15 lines that introduces no new module and touches nothing in the plan's **Refactor scope** — *and* the implementer returned green TDD evidence; those ride straight to the final review (record the skip on the ledger line as `— review skipped (low-risk)`). A task that returned `DONE_WITH_CONCERNS` is never low-risk. For every other task, dispatch a standard reviewer subagent for the task, per the **Reviewers judge independently** rule. The whole dispatch is a fixed shape of pointers and one SHA: the **BASE SHA** you recorded, and tell it to run `git diff <BASE>..HEAD` itself (never `HEAD~1`, which silently drops all but the last commit of a multi-commit task); the **plan path and this task's number**, and tell it to read that task's block — with the plan's **Global Constraints** as a standing lens — from the plan itself; the path to the implementer's **`task-<N>-report.md`** for the TDD evidence; and `review-rubric.md` plus `orientation.md` in the brief dir.

   Resolve each `CANNOT_VERIFY` item yourself before marking the task done: you hold the cross-task context and the Coverage table the reviewer doesn't, so a narrow reviewer never has to widen its search. A confirmed gap is a failed review. This resolution step — not the brief — is where your cross-task knowledge belongs: if a returned finding is a false positive your wider context disproves (the reviewer flagged correct reuse, or read a cohesive single-seam test as a horizontal slice), dismiss it here with that reasoning. An `APPROVED` that carries non-blocking **Notes** is still done — record them with the retro's deferred findings and move on; never spin the fix-loop over a nit. On `CHANGES_REQUESTED`, run the fix loop — it costs turns now, but carrying a defect into the next task costs more, because subsequent tasks build on it. Record **FIX_BASE** — the HEAD the reviewer just judged — and write the surviving findings **verbatim** to `task-<N>-findings.md` in the brief dir (later rounds append under a `## Round <R>` heading); that file, not pasted text, is what the fixer and the re-reviewer read. After the fixer lands (it re-runs the verify step and appends the output to its report — see the status table below), dispatch a **re-review, not a fresh review**: the same pointer shape as the first review, except the rubric is `re-review-rubric.md`, the findings file replaces the plan-task pointer, and the diff range is FIX_BASE — tell it to run `git diff <FIX_BASE>..HEAD` itself, and hand it the task's BASE SHA too for the rubric's comparative exception. A re-review that returns `CHANGES_REQUESTED` starts the next round from a new FIX_BASE. Its Out-of-scope observations route exactly as an `APPROVED`'s Notes do — to the retro's deferred findings, never back into the loop. The loop runs until approved — but that is not "obey every round": oscillation stops the loop (see Hard Rules), and a re-review verdict that merely restyles or reopens a point the last round settled is a finding to dismiss at this step, not an order to follow.

**Subagent dispatch.** Hand the implementer a **task brief file**, not pasted task text — pasted text stays resident in your context and is re-read on every later turn, bloating the run as it grows. Use [IMPLEMENTER-BRIEF.md](IMPLEMENTER-BRIEF.md) to write `task-<N>-brief.md` in the run's brief directory, point it at `orientation.md`, and require `task-<N>-report.md` plus the thin implementer return. Tell the implementer to read its brief and `orientation.md`, not the whole plan or the tree at large. Dispatch parallel implementers in a single message only when their files-blocks don't overlap. Every spawn then blocks (Hard Rules → A dispatch is a blocking call): the subagent's return is your next input.

Require the template's **thin return** — under ~15 lines, with status, commit SHA(s), test summary, concerns, report path, and TDD evidence. The verbose report goes to the file, not into your window. For multi-behavior tasks, the return must carry one RED→GREEN pair per behavior; one bulk RED→GREEN pair is a `CHANGES_REQUESTED`.

Implementer status: `DONE` → review; `DONE_WITH_CONCERNS` → read first, address if they affect correctness; `NEEDS_CONTEXT` → provide and re-dispatch; `BLOCKED` → a report naming a reroute (the destination itself must move) surfaces to the user directly; otherwise escalate to the heavy tier once (the sole exception to the standard-tier default), then surface to the user. When a reviewer returns `CHANGES_REQUESTED`, the fixer's dispatch points it at `task-<N>-findings.md` — never pasted findings — plus its own brief and report; it re-runs the verify step after applying the fixes and appends the fresh output to its report before re-review — reviewers do not re-run tests for you.

### 4. Verify the whole

Before claiming completion, three gates in order — any failure stops the run:

1. **Plan walk.** Re-tick every task in the plan against an actual commit. Run the plan's gate commands — its `Gates:` header line, or suite / lint / typecheck / build if the plan predates one — fresh this turn and read the output.
2. **Coverage walk.** Walk the plan's Coverage table row by row; for each row, confirm its verify step ran green *this session* — re-run any that are stale or that earlier tasks may have broken. Rows marked human-only go in the retro's Open items, not silently skipped. If the plan has no Coverage table, walk the spec's acceptance criteria (or, with no spec, the plan's stated goal) and check each against the diff yourself.
3. **Final review (fresh eyes).** In subagent modes the per-task reviewers each saw a single task; in solo there were none — either way this fresh-eyes pass over the whole diff catches what they couldn't, and in solo it is the only review the run gets, so it carries the per-task rubric too — the final brief folds it in. Dispatch one heavy reviewer subagent for the final review, per the **Reviewers judge independently** rule. Give it: the **spec path** (or the plan path if no spec exists) and the **plan path**, and tell it to read them itself — including the plan's Coverage table; the **BASE SHA** the ledger recorded at the start of the run, and tell it to run `git diff <BASE>..HEAD` itself; and `final-review-rubric.md` in the brief dir for its review axes and return format.

On `CHANGES_REQUESTED`, vet each finding before you touch code — the final review's resolution step, counterpart to the per-task one above. The final reviewer is fresh-eyes but context-starved by design (pointers only, no cross-task memory), so a finding can be a false positive your spec-and-plan context disproves: it read correct reuse as duplication, or called an acceptance criterion missing that a file outside its narrow read already satisfies. Dismiss those here with stated reasoning, recorded in the retro's Final review section so the dismissal is auditable, not a silent exit from the gate — and dismiss only what you can actually disprove, never what you'd rather not fix; a confirmed gap is still a failed review. Apply the surviving fixes and nothing else — failing test first for behavioral fixes, separate commits, no amending — then re-review once. A finding you can't fix becomes a retro Open item, stated plainly. An `APPROVED` that arrives with non-blocking **Notes** routes them to the retro's deferred findings, never the fix-loop. A surviving finding that would reverse a change an earlier per-task review required is oscillation — stop and surface per Hard Rules.

### 5. Close the loop

You ship finished work. Before writing the retro, gather every loose end the run produced — reviewer Notes, deferred findings, plan risks, human-only Coverage rows, your own "worth noting" observations — and triage each:

1. **Settle it.** If a command, read, or test can settle it this session, run it now and read the output — a verified fact is settled and appears nowhere in the hand-back. Settling is verification, not rework: a check that reveals a real defect routes to the next bucket, and a confirmed nit stays a deferred finding in the retro, never a fresh fix-loop.
2. **Fix it.** A defect in shipped code fails the final gate — route it back through Verify the whole.
3. **Escalate it as a decision.** What genuinely needs the user survives: a tradeoff only they can weigh, or an action only a human can perform (a visual smoke check, a credential you don't hold). Write it as the decision to make, with your recommendation.

Completion criterion: every loose end is settled, fixed, or written as a decision with a recommendation — none merely restates a fact you could have checked this session.

### 6. Retro

Write a retro to `.crank/<slug>/retro.md` at the working root (create `.crank/` with a `.crank/.gitignore` containing `*` if missing; outside a git repo, fall back to `${TMPDIR:-/tmp}/crank-<slug>/retro.md`), with the sections listed in **Deliverables → Retro**.

### 7. Hand back

Report finished work: what shipped, the verification that proves it, and — only when items survived Close the loop — each one stated as the decision it is, with your recommendation.

Don't end on a disposition menu — take the safe defaults, state them, and lead with the durable next step:

- The retro stays at its `.crank/<slug>/` path; commits stay local on `<branch>` — one line each, stated, not asked.
- **Next:** the single command or decision that moves the work forward — e.g. `git merge <branch>` from the base branch, or the one surviving decision from Close the loop.

Close with a single trailing sentence noting the alternatives on request (open a PR, discard the branch, copy or print the retro) — prose, not a numbered question. Never force-push, amend, rewrite history, or delete a branch without explicit approval. Then stop.
