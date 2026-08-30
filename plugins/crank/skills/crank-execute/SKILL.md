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
- **Every run opens with the pre-flight callout.** Fresh or resumed, the filled block lands as reply text before any other work (Flow step 2).
- **Destination frozen, road flexible.** What the plan ships — each task's goal, its contract, the architecture — is frozen. The road there is not: when a bug, stale detail (renamed symbol, moved file), or failed assumption blocks a task, fix it as a **detour** — the smallest change that still ships exactly what the task promises — and log it on the ledger line. A fix that would change what ships is a **reroute**: stop and surface it with your recommendation. Off-path surprises (a pre-existing bug the task doesn't hit) stay retro entries, never side quests.
- **Progress is durable.** Track task completion in the progress ledger (see Deliverables → Progress ledger), not only in your todos.
- **Reviewers judge independently.** A reviewer pulls its own facts: it runs the diff, reads its task from the plan, reads the implementer's evidence from the report file, and applies the fixed rubric file. Your dispatch hands it only pointers and the BASE SHA — anything more (a description or defense of the diff, a reproduced or annotated rubric) pre-judges the review you asked for.
- **Verify once; trust the evidence.** A task's TDD evidence (the implementer's RED/GREEN output) is the suite's authoritative run for that task; the final gate's plan-and-coverage walk is the single authoritative re-run across the whole diff.
- **A stated dispatch binds you to spawn.** The moment your output says a task gets a subagent — or the run's chosen shape says so — your *next* action is that spawn, never the work done inline (the pre-flight roster is not itself the dispatch). If main-thread work is the right call, say you're staying on-thread and why (for a shape change, re-state the shape) instead of announcing a dispatch.
- **A dispatch is a blocking call.** From spawn to return the subagent owns the work: your next action is reading its return, and everything else — the next task, edits near its files, a peek at its progress — queues behind that return. In parallel mode the batch of spawns goes out in one message and blocks as one; every return is read before anything else moves. The one exit from the wait is the quiet-dispatch rule below.
- **Oscillation stops the loop.** A review round that demands reversing what a prior round required is oscillation, not progress — never flip the code blind; stop and surface both verdicts to the user with your recommendation.
- **A stop instruction bounds the unit of work, not the phase.** When the user says "do X, then stop," the run ends after X's verification, whatever X uncovers — newly discovered defects become surfaced findings with a recommendation, never a new fix round.
- **Off-plan fixes are bounded.** A fix that isn't a plan task gets exactly one investigation, one test-first fix, one review — routed through this skill's own dispatch shapes, never an ad-hoc harness workflow — then stop and report, whatever that review finds.
- **A quiet dispatch is reconciled, not narrated.** When a subagent is out past the point you expected it back, reconcile against durable state — `git log` since BASE, the ledger, its report file on disk — then resume the agent or surface the stall with your recommendation; a "standing by" turn is never the move.
- **Never** force-push, amend earlier commits, rewrite history, or delete a branch without explicit approval.

## References

### Subagents

This skill spawns subagents at two tiers — resolve each to your harness per [SUBAGENT-TIERS.md](SUBAGENT-TIERS.md). **standard** = exploration, implementation, per-task review; **heavy** = the final cross-task review (and a one-time escalation for a `BLOCKED` task). That file's **Dispatch or main thread** default governs off-plan investigation; the execution shape (Flow step 2) governs implementation and review.

### Vocabulary

Read [VOCABULARY.md](VOCABULARY.md) before step 2. Step 3's prose leans on the **seam**, the **journey test**, and the **tracer bullet** against its opposite the **horizontal slice**. Hold the **deletion test**, **depth** (**deep** / **shallow**), **spaghetti growth**, the **implementation-detail test**, and the **redundant test** when you verdict a reviewer's findings at steps 3 and 4 — a finding that misapplies one of these meanings is a dismissal.

### Review verdicts

Both review gates, per task (Flow step 3) and final (Flow step 4), resolve a verdict the same way:

- Dismiss only what you can disprove, never what you'd rather not fix, and record the reasoning that disproved it.
- A confirmed gap is a failed review.
- An `APPROVED` carrying non-blocking **Notes** is still done: record the Notes with the retro's deferred findings and move on, never into a fix round.

## Deliverables

The primary deliverable is **shipped code** — the task-by-task commits, recorded in the progress ledger. The **retro** is a secondary doc.

### Progress ledger

The ledger is your durable record of what has shipped — it survives compaction, where your todos and conversation memory do not. Its home: try the git directory first; on refusal, the worktree fallback below — never the session scratchpad, which dies with the session:

1. Print the git-directory path, then create it — two plain commands, not a compound one-liner (sandboxes that guard the worktree reject compound shells):

   ```
   git rev-parse --git-path crank
   mkdir -p <the path it printed>
   ```

   The ledger is `<that dir>/progress-<slug>.md` — slug-keyed, so several plans' ledgers coexist; the slug is the plan's parent directory name.
2. If the harness refuses writes there — worktree isolation guards the shared `.git` path — use `.crank/<slug>/progress.md` at the worktree root instead, and note the fallback once.

One ledger per plan per worktree. It opens with the run's anchor, then one line per plan task:

```
# Crank execute — <branch>
Plan: <plan path, normally .crank/<slug>/plan.md>
Base: <the HEAD SHA when the run started>

- [ ] Task 1: <subject>
- [ ] Task 2: <subject>
```

Flip a task's box to `[x]` the moment it lands and append its commit SHA(s) and review verdict — `- [x] Task 1: <subject> — <sha> — APPROVED`. A task that took a detour appends it too — `— detour: <one line>` — so the retro's Deviations survive compaction; the corrected fact behind it (the renamed symbol's current name, the moved file's current path) lands as a grounding entry in `.crank/<slug>/grounding.md` ([ARTIFACT-HOME.md](ARTIFACT-HOME.md) → Grounding), so a resumed run or a later dispatch reads the current fact instead of re-hitting the stale one. On resume, an `[x]` line means done: confirm it against `git log` and skip it. The ledger applies in every execution shape, solo included — compaction can strike a solo run too.

### Retro

Written to the effort's `.crank/<slug>/` directory (see Flow → Retro). Sections:

- **Summary** — what shipped, commits `<first>..<last>` on `<branch>`.
- **Deviations** — every detour taken (what blocked, the fix), plus anywhere else the diff meaningfully differs from the plan and why. "None" if none.
- **Final review** — verdict, findings fixed (with commit SHAs), findings dismissed as false positives, findings deferred: each per References → Review verdicts.
- **Open items** — only what survived Flow → Close the loop, each written to that step's completion criterion. Deferred findings and dismissals stay in the Final review section above — this section holds nothing you could have settled yourself.
- **Validation evidence** — commands run, outcomes.

## Flow

Track progress with live tasks the user can watch — but every task update costs a full-context turn, so keep the list lean. Create **one tracked task per plan task** (the work that visibly advances), not one per Flow step below; the steps are your own orientation. Flip each plan task to complete the instant it lands — one update per transition, not a done-this-then-start-next pair.

### 1. Load and critically review

Resolve the plan first — every effort's artifacts live in one directory, `.crank/<slug>/` at the repository root:

1. **Explicit path** — read it as-is; the slug is the plan's parent directory name, and the ledger and `exec/` dir resolve deterministically from it.
2. **Bare slug** — resolves to `.crank/<slug>/plan.md`.
3. **No argument, plan in the conversation** — use it; derive a slug from the plan's title — its artifacts live in `.crank/<slug>/`.
4. **No argument, exactly one plan on disk** — use it without asking.
5. **No argument, several plans** — ask via a structured question listing each plan with its derived status: *not started* (no ledger in either home), *in progress* (unchecked boxes remain), *done* (all `[x]`). An effort directory without a `plan.md` (e.g. spec-only) shows as "no plan yet" and is not executable.
6. **No argument, no plans anywhere** — say so and recommend the plan phase (`/crank plan …`).

Create `.crank/` on first use with a `.crank/.gitignore` containing `*`; outside a git repo, `${TMPDIR:-/tmp}/crank-<slug>/` stands in for `.crank/<slug>/`.

**Legacy artifacts.** Resolving an artifact checks the per-plan path first, then the legacy paths listed in [LEGACY-ARTIFACTS.md](LEGACY-ARTIFACTS.md); a hit there, or a ledger whose plan directory is gone, is adopted per that file before the run proceeds.

Read the plan in full. If the plan's header names a spec (`Spec:` line), read that too — it is the contract the final review runs against; the plan is only its decomposition. If the plan has a **Global Constraints** section, treat its values as binding on every task — they are the attention lens the per-task and final reviews run against.

Before starting, walk the plan task by task for two kinds of problem; for each task, name its blockers and plan-mandated defects or record "none". Raise everything you found in a **single batched question**, not one interrupt per discovery:

- **Blockers** — missing context, ambiguous step, undefined symbol, contradiction with the codebase.
- **Plan-mandated defects** — places the plan instructs you to write something the review rubric would reject: a test that asserts nothing, verbatim duplication of a helper the codebase already provides, a cast or `any` papering over a contract. Overriding what the plan explicitly instructs is a reroute, never a detour — surface them and let the user say which governs.

If you find either, stop until answered. Then check `git status --short` and the current branch; if you're on `main`/`master` with a non-trivial change, ask once before committing.

Open the progress ledger (see Deliverables → Progress ledger); if one already exists for this plan in this worktree from an interrupted run, resume from it per that section, otherwise start fresh. A fixed-name `progress.md` in either home is legacy — adopt it per [LEGACY-ARTIFACTS.md](LEGACY-ARTIFACTS.md) first.

Completion criterion: every task has been judged, every finding raised in one batched question and answered, `git status --short` and the branch checked, and the ledger open with one line per plan task.

### 2. Pre-flight

Pick the execution shape from the plan — there is no required mode — and **call it out**: write the block below into your reply, every line filled, then continue in the same turn. The callout is a statement of record the user reads, so it lands in reply text, ahead of the brief directory, the first edit, and the first dispatch; a tool call, a ledger line, or private reasoning is not a callout. Every invocation calls it out, resumed runs included, so a fresh session re-anchors on the same facts. Callout criterion: the filled block is visible in your reply before any task work starts.

```
**Pre-flight**
- Plan: .crank/<slug>/plan.md (spec: spec.md · brainstorm: brainstorm.md)
- Grounding: <.crank/<slug>/grounding.md — N entries seeded | none>
- Branch: <current branch>
- Shape: <solo | sequential | parallel>
- Subagents: standard = <model> (implement, per-task review) · heavy = <model> (final review)
- Tasks: <N> (<M> remaining)
```

Line rules: the Plan line's parenthetical names only sibling artifacts that actually exist in `.crank/<slug>/`, plus a spec the plan's `Spec:` header names — omit it when there are none. The Grounding line reads `none` when the effort's grounding file is absent or empty; otherwise it names the file and how many of its entries were seeded into `orientation.md` (in solo, which stocks no `orientation.md`, name the file and its entry count). Models are the **resolved** names after [SUBAGENT-TIERS.md](SUBAGENT-TIERS.md) is applied for this harness, never bare tier labels. In solo the Subagents line reads `heavy = <model> (final review) — implementation inline` — solo still dispatches the fresh-eyes final reviewer. `<M> remaining` counts the ledger's unchecked boxes; a fresh run has `M = N`.

- **Solo (in this session)** — *Gains:* zero dispatch overhead, in-flight state carries between tasks. *Costs:* every task's source and noise stays in your window, degrading later tasks; no per-task review, since reviewing your own just-written code is the weakest review, so solo's one review is the fresh-eyes final gate. *Fits:* small plans (~3 tasks or fewer), tasks that share in-flight state, quick fixes.
- **Sequential subagents** — *Gains:* fresh context per task, an independent reviewer per diff. *Costs:* you must brief completely or the implementer guesses. *Fits:* the default for >3 tasks.
- **Parallel subagents** — *Gains:* wall-clock speed. *Costs:* overlapping edits conflict. *Fits:* only when tasks touch disjoint files with no shared state.

Once stated, the shape binds the run (Hard Rules → A stated dispatch binds you to spawn).

Whatever the shape, create this run's **brief directory** — where briefs, reports, and rubrics go — at `.crank/<slug>/exec/` under the repository root and state the path once. The progress ledger keeps its own home (see Deliverables → Progress ledger).

Once the directory is set, stock it. In a subagent mode: read [IMPLEMENTER-BRIEF.md](IMPLEMENTER-BRIEF.md), copy its `implementer-rules.md` block into the brief dir and write its `orientation.md` template there — seeding the template's unfilled slots from `.crank/<slug>/grounding.md` entries banked at plan phase or later ([ARTIFACT-HOME.md](ARTIFACT-HOME.md) → Grounding), where that file exists — then dispatch a standard-tier subagent to fill `orientation.md` from that template (a repo sweep, per [SUBAGENT-TIERS.md](SUBAGENT-TIERS.md)'s **Dispatch or main thread** default) — except the Commands block, which copies the plan's `Gates:` line. The sweep verifies each seeded line at its citation instead of skipping filled slots, so `orientation.md` carries only facts verified this run. Then place the three review rubrics in the brief dir as fixed reference files: copy [PER-TASK-REVIEW-BRIEF.md](PER-TASK-REVIEW-BRIEF.md) to `review-rubric.md`, [FINAL-REVIEW-BRIEF.md](FINAL-REVIEW-BRIEF.md) to `final-review-rubric.md`, and [RE-REVIEW-BRIEF.md](RE-REVIEW-BRIEF.md) to `re-review-rubric.md`. In solo: copy [FINAL-REVIEW-BRIEF.md](FINAL-REVIEW-BRIEF.md) to `final-review-rubric.md` and [PER-TASK-REVIEW-BRIEF.md](PER-TASK-REVIEW-BRIEF.md) to `review-rubric.md` — solo runs no per-task review, but the final rubric's **Quality of the whole diff** axis reads its per-diff checks from that file. Every copy is **verbatim** — byte-for-byte, never a retype or a "fill it in." Do this now, before any task is implemented: with no diff yet in view there is nothing to pre-judge, so the rubrics freeze clean.

Completion criterion: the filled block is in your reply, `.crank/<slug>/exec/` exists and its path is stated once, every rubric copy this shape requires is on disk byte-for-byte, and in a subagent mode `implementer-rules.md` and a filled `orientation.md` sit beside them.

### 3. Per task

1. **Dispatch and implement.** Record the task's **BASE** — the current `HEAD` SHA — before any edit; the review diffs against it.

   In a subagent mode, hand the implementer a **task brief file**, not pasted task text — pasted text stays resident in your context and is re-read on every later turn, bloating the run as it grows. Use [IMPLEMENTER-BRIEF.md](IMPLEMENTER-BRIEF.md) to write `task-<N>-brief.md` in the run's brief directory, point it at `orientation.md` and `implementer-rules.md`, and require `task-<N>-report.md` plus the thin implementer return. Tell the implementer to read those three files, not the whole plan or the tree at large. Dispatch parallel implementers in a single message only when their files-blocks don't overlap. Every spawn then blocks (Hard Rules → A dispatch is a blocking call).

   The implementation itself — yours in solo, the implementer's otherwise — runs the TDD cycle per behavior in the task: failing test → watch it fail for the expected reason → minimal impl → the task's `verify` step. The RED is a fresh test only at a fresh seam; where a journey test already walks this seam, it is a failing assertion extended onto that test. Several behaviors mean several cycles: **tracer bullets**, never a **horizontal slice**. Commit once the task is green, with a message that names the task. Skip TDD only when the plan explicitly does (config flips, doc edits, generated code). When the task lands, flip its line in the ledger to `[x]` with the commit SHA(s).

   A return missing RED→GREEN evidence where TDD applies, or carrying one bulk pair for a multi-behavior task, is a `CHANGES_REQUESTED`. Implementer status: `DONE` → review; `DONE_WITH_CONCERNS` → read first, address if they affect correctness; `NEEDS_CONTEXT` → provide and re-dispatch; `BLOCKED` → a report naming a reroute (the destination itself must move) surfaces to the user directly; otherwise escalate to the heavy tier once (the sole exception to the standard-tier default), then surface to the user.

2. **Review (subagent modes only).** Review each task **unless it is low-risk** — a test-only, config, doc, or generated-code task, or a diff under ~15 lines that introduces no new module and touches nothing in the plan's **Refactor scope** — *and* the implementer returned green TDD evidence; those ride straight to the final review (record the skip on the ledger line as `— review skipped (low-risk)`). A task that returned `DONE_WITH_CONCERNS` is never low-risk. For every other task, dispatch a standard reviewer subagent for the task, per the **Reviewers judge independently** rule, handing it: the **BASE SHA** you recorded, whose diff range is `<BASE>..HEAD` (never `HEAD~1`, which silently drops all but the last commit of a multi-commit task); the **plan path and this task's number**, with the plan's **Global Constraints** as a standing lens; the path to the implementer's **`task-<N>-report.md`** for the TDD evidence; and `review-rubric.md` plus `orientation.md` in the brief dir.

   It returns a line per rubric check, then a verdict, then its `Cannot verify:` list. A check returned `n/a` with no reason, or a check missing from the line, is an unrun check — send it back rather than reading the verdict. Resolve each `Cannot verify:` item yourself before marking the task done, then verdict it per References → Review verdicts: you hold the cross-task context and the Coverage table the reviewer doesn't, so a narrow reviewer never has to widen its search. Your cross-task knowledge belongs here, not in the brief: if a returned finding is a false positive it disproves (the reviewer flagged correct reuse, or read a cohesive single-seam test as a horizontal slice), dismiss it with that reasoning.

3. **Fix round, on `CHANGES_REQUESTED`.** Run it before the next task — carrying a defect forward costs more than fixing it now. Record **FIX_BASE** — the HEAD the reviewer just judged — and write the surviving findings **verbatim** to `task-<N>-findings.md` in the brief dir (later rounds append under a `## Round <R>` heading); that file, not pasted text, is what the fixer and the re-reviewer read. Write the fixer's brief from [IMPLEMENTER-BRIEF.md](IMPLEMENTER-BRIEF.md)'s `task-<N>-fix-brief.md` template — it carries the round's scope, the files block widened to what the findings cite, and the verify re-run appended to `task-<N>-report.md` that the re-reviewer reads instead of running tests itself — then dispatch a standard implementer against it.

   After the fixer lands, dispatch a **re-review, not a fresh review**: the same pointer shape as the first review, except the rubric is `re-review-rubric.md`, the findings file replaces the plan-task pointer, and the diff range is FIX_BASE — tell it to run `git diff <FIX_BASE>..HEAD` itself, and hand it the task's BASE SHA too for the rubric's comparative exception. A re-review that returns `CHANGES_REQUESTED` starts the next round from a new FIX_BASE. Its Out-of-scope observations route as Notes do (References → Review verdicts). The loop runs until approved — but that is not "obey every round": oscillation stops the loop (see Hard Rules), and a re-review verdict that merely restyles or reopens a point the last round settled is a finding to dismiss here, not an order to follow.

### 4. Verify the whole

Before claiming completion, three gates in order — any failure stops the run:

1. **Plan walk.** Re-tick every task in the plan against an actual commit. Run the plan's gate commands — its `Gates:` header line, or suite / lint / typecheck / build if the plan predates one — fresh this turn and read the output.
2. **Coverage walk.** Walk the plan's Coverage table row by row; for each row, confirm its verify step ran green *this session* — re-run any that are stale or that earlier tasks may have broken. Rows marked human-only go in the retro's Open items, not silently skipped. If the plan has no Coverage table, walk the spec's acceptance criteria (or, with no spec, the plan's stated goal) and check each against the diff yourself.
3. **Final review (fresh eyes).** The per-task reviewers each saw a single task, so this fresh-eyes pass over the whole diff catches what they couldn't; in solo it is the run's only review — the final brief applies `review-rubric.md`'s code-quality checks to the whole diff. Dispatch one heavy reviewer subagent for the final review, per the **Reviewers judge independently** rule, giving it: the **spec path** (or the plan path if no spec exists) and the **plan path**, including its Coverage table and, when present, its **Global Constraints**; the **ledger path**, whose task lines record each detour taken; the **BASE SHA** the ledger recorded at the start of the run, whose diff range is `<BASE>..HEAD`; and `final-review-rubric.md` in the brief dir for its review axes and return format.

On `CHANGES_REQUESTED`, vet each finding before you touch code, per References → Review verdicts. The final reviewer is fresh-eyes but context-starved by design (pointers only, no cross-task memory), so a finding can be a false positive your spec-and-plan context disproves: it read correct reuse as duplication, or called an acceptance criterion missing that a file outside its narrow read already satisfies. Dismiss those here, recorded in the retro's Final review section. Apply the surviving fixes and nothing else — failing test first for behavioral fixes, separate commits, no amending. A horizontal-slice finding is settled by demonstrating each sliced test still fails without its implementation; the demonstrated slice is then recorded in the retro's Final review section rather than re-committed. Then re-review once: the same dispatch shape, re-using `final-review-rubric.md`, plus the **FIX_BASE** (the HEAD the reviewer judged) and the surviving findings, which route it into the rubric's **Fix round** branch. A finding you can't fix becomes a retro Open item, stated plainly. A surviving finding that would reverse a change an earlier per-task review required is oscillation — stop and surface per Hard Rules.

### 5. Close the loop

You ship finished work. Before writing the retro, gather every loose end the run produced — reviewer Notes, deferred findings, plan risks, human-only Coverage rows, your own "worth noting" observations — and triage each:

1. **Settle it.** If a command, read, or test can settle it this session, run it now and read the output — a verified fact is settled and appears nowhere in the hand-back. Settling is verification, not rework: a check that reveals a real defect routes to the next bucket, and a confirmed nit stays a deferred finding in the retro, never a fresh fix-loop.
2. **Fix it.** A defect in shipped code fails the final gate — route it back through Verify the whole.
3. **Escalate it as a decision.** What genuinely needs the user survives: a tradeoff only they can weigh, or an action only a human can perform (a visual smoke check, a credential you don't hold).

Completion criterion: every loose end is settled, fixed, or written as a decision with a recommendation — none merely restates a fact you could have checked this session.

### 6. Retro

Write a retro to `.crank/<slug>/retro.md` at the repository root, with the sections listed in **Deliverables → Retro**.

### 7. Hand back

Report finished work: what shipped, the verification that proves it, and — only when items survived Close the loop — each one as written there.

Don't end on a disposition menu — take the safe defaults, state them, and lead with the durable next step:

- The retro stays at its `.crank/<slug>/` path; commits stay local on `<branch>` — one line each, stated, not asked.
- **Next:** the single command or decision that moves the work forward — e.g. `git merge <branch>` from the base branch, or the one surviving decision from Close the loop.

Close with a single trailing sentence noting the alternatives on request (open a PR, discard the branch, copy or print the retro) — prose, not a numbered question. Then stop.
