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

These hold at every step; a rule that binds one step lives with that step.

- **Evidence before claims.** Never report a task done without running its verification this turn and reading the output.
- **Destination frozen, road flexible.** What the plan ships — each task's goal, its contract, the architecture — is frozen. The road there is not: when a bug, stale detail (renamed symbol, moved file), or failed assumption blocks a task, fix it as a **detour** — the smallest change that still ships exactly what the task promises — and log it on the ledger line. A fix that would change what ships is a **reroute**: stop and surface it with your recommendation. Off-path surprises (a pre-existing bug the task doesn't hit) stay retro entries, never side quests.
- **Reviewers judge independently.** Every review dispatch is **cold**: the reviewer pulls its own facts — it runs the diff, reads its task from the plan, reads the implementer's evidence from the report file, and applies the fixed rubric file. Your dispatch hands it only pointers and the BASE SHA; anything more — a description or defense of the diff, a reproduced or annotated rubric — pre-judges the review you asked for.
- **Verify once; trust the evidence.** A task's TDD evidence (the implementer's RED/GREEN output) is the suite's authoritative run for that task; the final gate's plan-and-coverage walk is the single authoritative re-run across the whole diff.
- **A stated dispatch binds you to spawn.** The moment your output says a task gets a subagent — or the run's chosen shape says so — your *next* action is that spawn, never the work done inline (the pre-flight roster is not itself the dispatch). If main-thread work is the right call, say you're staying on-thread and why (for a shape change, re-state the shape) instead of announcing a dispatch.
- **A dispatch is a blocking call.** From spawn to return the subagent owns the work: your next action is reading its return, and everything else — the next task, edits near its files, a peek at its progress — queues behind that return. In parallel mode the batch of spawns goes out in one message and blocks as one; every return is read before anything else moves. When a subagent is out past the point you expected it back, reconcile against durable state — `git log` since BASE, the ledger, its report file on disk — then resume the agent or surface the stall with your recommendation.
- **Oscillation stops the loop.** A review round that demands reversing what a prior round required is oscillation, not progress — never flip the code blind; stop and surface both verdicts to the user with your recommendation.
- **Never** force-push, amend earlier commits, rewrite history, or delete a branch without explicit approval.

## References

### Subagents

This skill spawns subagents at two tiers — resolve each to your harness per [SUBAGENT-TIERS.md](SUBAGENT-TIERS.md). **standard** = exploration, implementation, per-task review; **heavy** = the final cross-task review (and a one-time escalation for a `BLOCKED` task). That file's **Dispatch or main thread** default governs off-plan investigation; the execution shape (Flow step 2) governs implementation and review.

### Vocabulary

Read [VOCABULARY.md](VOCABULARY.md) before step 2. Step 3's prose leans on the **seam**, the **journey test**, and the **tracer bullet** against its opposite the **horizontal slice**. Hold the **deletion test**, **depth** (**deep** / **shallow**), **spaghetti growth**, the **implementation-detail test**, and the **redundant test** when you verdict a reviewer's findings at steps 3 and 5 — a finding that misapplies one of these meanings is a dismissal.

### Review verdicts

Both review gates, per task (Flow step 3) and final (Flow step 5), resolve a verdict the same way:

- Dismiss only what you can disprove, and record the reasoning that disproved it. You hold the cross-task context, the spec, and the Coverage table the reviewer doesn't, so a false positive is yours to disprove rather than the reviewer's to widen its search for: correct reuse read as duplication, a cohesive single-seam test read as a horizontal slice, an acceptance criterion called missing that a file outside the reviewer's read already satisfies. A dismissal is recorded with its reasoning — on the task's ledger line for a per-task review, in the retro's Final review section for the final one.
- A confirmed gap is a failed review.
- An `APPROVED` carrying non-blocking **Notes** is still done: record the Notes as deferred findings — on the task's ledger line for a per-task review, in the retro's Final review section for the final one — and move on, never into a fix round. A re-review's Out-of-scope observations route the same way.

## Deliverables

The primary deliverable is **shipped code** — the task-by-task commits, recorded in the progress ledger. The **retro** is a secondary doc.

### Progress ledger

The ledger is the durable record of what has shipped: track task completion here, not only in your todos, in every execution shape, solo included. Its home is the git directory first; on refusal, the worktree fallback:

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

**Line grammar.** Each item below is appended to a task's line after ` — `:

- `<sha> — <verdict>`, with the box flipped to `[x]`, the moment the task lands: its commit SHA(s), then `APPROVED`, `review skipped (clean return)`, or in solo `no per-task review`. On resume, an `[x]` line means done: confirm it against `git log` and skip it.
- `detour: <one line>` — every detour the task took, settled or open, so the retro's Deviations and the final review read them here.
- `open: <one line>` — a question about the task nobody has settled; whoever reads the task's body at step 3 settles it, where the steps, `Check:`, and Files block usually decide it.
- `note: <one line>` — a fact this task must carry: a landed interface, path, or contract its plan text no longer matches, read at step 3.
- Reviewer **Notes**, deferred findings, and dismissals with their reasoning, on the line of the task that landed them, so the retro reads them off the ledger.

One line lives under the anchor instead: `Stopped: <why> — resume at Task <N>`, written when a run ends short (step 4) and overwritten by the run that resumes.

**Where a loose fact lives.** A fact one later task must carry goes on that task's line as `note:`. A corrected repo fact — the renamed symbol's current name, the moved file's current path, a fixture landmine — goes with its evidence to `.crank/<slug>/grounding.md` ([ARTIFACT-HOME.md](ARTIFACT-HOME.md) → Grounding), which seeds `orientation.md`. Everything else goes to the retro's Open items.

### Retro

Written by the run that lands the **last** plan task, to `.crank/<slug>/retro.md` (Flow step 7); a short run hands the ledger forward instead (Flow step 4). Sections:

- **Summary** — what shipped, commits `<first>..<last>` on `<branch>`.
- **Deviations** — every detour taken (what blocked, the fix), plus anywhere else the diff meaningfully differs from the plan and why. "None" if none.
- **Final review** — verdict, findings fixed (with commit SHAs), findings dismissed as false positives, findings deferred: each per References → Review verdicts.
- **Open items** — only what survived Flow → Close the loop, each written to that step's completion criterion. Deferred findings and dismissals stay in the Final review section above — this section holds nothing you could have settled yourself.
- **Promoted** — each fact this run sent outliving the effort: the fact, its evidence line, and the `file:line` it landed at. Empty when the run promoted nothing.
- **Validation evidence** — commands run, outcomes.

## Flow

Track progress with live tasks the user can watch. Create **one tracked task per plan task** (the work that visibly advances), not one per Flow step below; the steps are your own orientation. Flip each plan task to complete the instant it lands — one update per transition.

### 1. Load and critically review

Resolve the plan and its `.crank/<slug>/` home per [RESOLVE-PLAN.md](RESOLVE-PLAN.md).

Read the plan's frame yourself — its header (`Spec:`, `Goal:`, `Gates:`), **Global Constraints**, **Refactor scope**, **File structure**, **Coverage**, **Out of scope**, and every task's title. The task bodies come one at a time, each read as you reach it at step 3. If the plan's header names a spec (`Spec:` line), read that too — it is the contract the final review runs against; the plan is only its decomposition. If the plan has a **Global Constraints** section, its values bind every task.

Open the progress ledger (Deliverables → Progress ledger); one that already exists for this plan in this worktree is an interrupted run, resumed per that section; otherwise start fresh.

Then dispatch the plan walk at the **standard** tier ([SUBAGENT-TIERS.md](SUBAGENT-TIERS.md) → Dispatch or main thread), handing it the plan path, the effort's `.crank/<slug>/grounding.md` where one exists, and the three buckets below verbatim. It returns one line per task naming each finding with its bucket, or `none`. The walk confirms what the plan cites: a claim carrying its evidence — `path:line`, a command and the output it printed, `searched <scope>, none found` — is confirmed at that citation with one read or one re-run, per [ARTIFACT-HOME.md](ARTIFACT-HOME.md) → Grounding's verify-then-trust rule; a grounding entry covering the same fact is confirmed the same way; a claim carrying no citation is derived in full. A finding stops the run only on a check the walk actually ran, quoted with its evidence — `path:line`, or the search that came back empty.

The walk reports; you land its corrections. A citation that confirmed at a different line or symbol is rewritten in place in the plan section that carries it, with the new anchor, before pre-flight, so the one section each implementer reads is already true. A citation that fails to confirm routes through a bucket like any other finding, with the corrected fact banked to grounding. Two buckets **stop** the run; the third is **carried** into it:

- **Blockers** — the plan names a symbol the walk grepped for and did not find, cites a path that is gone, or states a precondition another task contradicts.
- **Plan-mandated defects** — the plan's own words instruct something the review rubric rejects: a test that asserts nothing, verbatim duplication of a helper the codebase already provides, a cast or `any` papering over a contract. Quote the instruction. Overriding what the plan explicitly instructs is a reroute, never a detour — surface it and let the user say which governs.
- **Carried** — what the walk read as open rather than broken: a step open to two readings, a name used loosely, a symbol it could not place. Each rides its task's ledger line as `open:`. A fact the walk verified along the way — the renamed symbol's current name, the moved file's path — banks to grounding.

Raise the two stopping buckets in a **single batched question**, not one interrupt per discovery, and stop until answered. Then check `git status --short` and the current branch; on `main`/`master` with a non-trivial change, ask once before committing.

Completion criterion: every task judged with its findings bucketed or `none`, every cited claim confirmed at its citation or bucketed, the stopping buckets raised in one question and answered, every carried item on its ledger line or in grounding, the branch and `git status --short` checked, and the ledger open with one line per plan task.

### 2. Pre-flight

Every run, fresh or resumed, opens with the block below as reply text — every line filled — ahead of the brief directory, the first edit, and the first dispatch. Pick the execution shape from the plan — there is no required mode — then continue in the same turn.

```
**Pre-flight**
- Plan: .crank/<slug>/plan.md (spec: spec.md · brainstorm: brainstorm.md)
- Grounding: <.crank/<slug>/grounding.md — N entries seeded | none>
- Branch: <current branch>
- Shape: <solo | sequential | parallel>
- Subagents: standard = <model> (implement, per-task review) · heavy = <model> (final review) · resolved from <user CLAUDE.md | project CLAUDE.md/AGENTS.md | harness fallback>
- Tasks: <N> (<M> remaining)
```

Line rules: the Plan line's parenthetical names only sibling artifacts that actually exist in `.crank/<slug>/`, plus a spec the plan's `Spec:` header names — omit it when there are none. The Grounding line reads `none` when the effort's grounding file is absent or empty; otherwise it names the file and how many of its entries were seeded into `orientation.md` (in solo, which stocks no `orientation.md`, name the file and its entry count). Models are the **resolved** names after [SUBAGENT-TIERS.md](SUBAGENT-TIERS.md) is applied for this harness, never bare tier labels, and `resolved from` names the instruction file whose subagent preference the tiers were mapped onto, or `harness fallback` when no loaded instruction file states one; `harness fallback` beside a stated preference is a wrong line. In solo the Subagents line reads `heavy = <model> (final review) — implementation inline`, with the same `resolved from` tail. `<M> remaining` counts the ledger's unchecked boxes; a fresh run has `M = N`.

- **Solo (in this session)** — *Gains:* zero dispatch overhead, in-flight state carries between tasks. *Costs:* every task's source stays in your window; no per-task review — the final gate is solo's one review. *Fits:* small plans (~3 tasks or fewer), tasks that share in-flight state, quick fixes.
- **Sequential subagents** — *Gains:* fresh context per task, an independent reviewer per diff. *Costs:* you must brief completely or the implementer guesses. *Fits:* the default for >3 tasks.
- **Parallel subagents** — *Gains:* wall-clock speed. *Costs:* overlapping edits conflict. *Fits:* only when tasks touch disjoint files with no shared state.

Once stated, the shape binds the run (Hard Rules → A stated dispatch binds you to spawn).

Whatever the shape, create this run's **brief directory** — where briefs, reports, and rubrics go — at `.crank/<slug>/exec/` under the repository root and state the path once; the progress ledger keeps its own home. Stock it before the first task. Every copy is **verbatim** — a file copy, never a retype.

| File in the brief dir | Source | Subagent modes | Solo |
| --- | --- | --- | --- |
| `implementer-rules.md` | the block in [IMPLEMENTER-BRIEF.md](IMPLEMENTER-BRIEF.md) | copy | copy — its **Standing defect rules** and **TDD** sections bind step 3's inline implementation, with what those rules route to an implementer's report landing in your retro instead |
| `orientation.md` | the template in [IMPLEMENTER-BRIEF.md](IMPLEMENTER-BRIEF.md), filled per the sweep below | write | skip |
| `review-rubric.md` | [PER-TASK-REVIEW-BRIEF.md](PER-TASK-REVIEW-BRIEF.md) | copy | copy — the final rubric's **Quality of the whole diff** axis reads its per-diff checks here |
| `final-review-rubric.md` | [FINAL-REVIEW-BRIEF.md](FINAL-REVIEW-BRIEF.md) | copy | copy |
| `re-review-rubric.md` | [RE-REVIEW-BRIEF.md](RE-REVIEW-BRIEF.md) | copy | skip |

The orientation sweep: write the template into the brief dir, seed its unfilled slots from `.crank/<slug>/grounding.md` entries where that file exists ([ARTIFACT-HOME.md](ARTIFACT-HOME.md) → Grounding), then dispatch a standard-tier subagent to fill the rest from a repo sweep — except the Commands block, which copies the plan's `Gates:` line. The sweep verifies each seeded line at its citation instead of skipping filled slots, so `orientation.md` carries only facts verified this run.

Completion criterion: the filled block is in your reply, `.crank/<slug>/exec/` exists and its path is stated once, every file the table requires for this shape is on disk — copies byte-identical to their source, `orientation.md` filled in a subagent mode.

### 3. Per task

1. **Dispatch and implement.** Record the task's **BASE** — the current `HEAD` SHA — before any edit; the review diffs against it as `<BASE>..HEAD`, which keeps every commit of a multi-commit task. Read this task's section in the plan now — its steps, its `Check:` and `Stop if:` lines, its Files block, Interfaces, and `Verify:` step — and no other task's. Where the ledger shows an earlier task in this run already touched a file this section cites, confirm that citation against HEAD rather than the run's BASE and rewrite the anchor in the plan section itself: every later task reads this section, not the ledger.

   In a subagent mode, write `task-<N>-brief.md` in the brief dir from [IMPLEMENTER-BRIEF.md](IMPLEMENTER-BRIEF.md): its Task block points at the task's plan section by heading and carries the task's `- [ ] Behavior N:` lines, it points at `orientation.md` and `implementer-rules.md`, and it names the report path `task-<N>-report.md`. The dispatch hands the implementer that brief file and asks for the thin return. Dispatch parallel implementers in a single message only when their Files blocks don't overlap. Every spawn then blocks (Hard Rules → A dispatch is a blocking call).

   The implementation itself — yours in solo, bound by `implementer-rules.md` in the brief dir, the implementer's otherwise — runs the TDD cycle per behavior in the task: failing test → watch it fail for the expected reason → minimal impl → the task's `verify` step. The RED is a fresh test only at a fresh seam; where a journey test already walks this seam, it is a failing assertion extended onto that test. Several behaviors mean several cycles: **tracer bullets**, never a **horizontal slice**. Skip TDD only when the plan explicitly does (config flips, doc edits, generated code). Commit once the task is green, with a message that names the task, and flip its ledger line.

   Implementer status: `DONE` and `DONE_WITH_CONCERNS` → the triage at 2; `NEEDS_CONTEXT` → provide and re-dispatch; `BLOCKED` naming a reroute (the destination itself must move) → surface to the user directly; any other `BLOCKED` → escalate to the heavy tier once (the sole exception to the standard-tier default), then surface to the user. A return missing RED→GREEN evidence where TDD applies, or carrying one bulk pair for a multi-behavior task, is a `CHANGES_REQUESTED`.

2. **Review (subagent modes only).** Triage the thin return; the report stays on disk. A **clean return** — `Status: DONE`, `Detours: none` or `settled only`, `Concerns: none`, and a RED→GREEN pair per behavior or the plan line that skips TDD quoted — skips this review. Record `review skipped (clean return)` on the ledger line. (per project decision: a week of runs showed 40 of 41 per-task reviews approving, most dispatched on observations and on settled detours, so only open detours and Concerns earn a review.) A settled detour is one the brief, `orientation.md`, grounding, or you already directed, so its judgment was made before the implementer started; it still lands on the ledger line as `detour:`.

   An **open detour** or a **Concern** is a judgment neither the plan nor you have made — so is a doubt of your own about the return, which you write on the ledger line — so dispatch a standard reviewer, cold (Hard Rules → Reviewers judge independently), handing it: the **BASE SHA** you recorded; the **plan path and this task's number**, with the plan's **Global Constraints** as a standing lens; the path to the implementer's **`task-<N>-report.md`** for the TDD evidence; `review-rubric.md` plus `orientation.md` in the brief dir; and the **review path** `task-<N>-review.md` in the brief dir, where its full review goes. Observations trigger no review; route each per Deliverables → Progress ledger → Where a loose fact lives.

   It returns a line per rubric check, then a verdict, then its `Cannot verify:` list. A check returned `n/a` with no reason, or a check missing from the line, is an unrun check — send it back rather than reading the verdict. Resolve each `Cannot verify:` item yourself, then verdict per References → Review verdicts.

3. **Fix round, on `CHANGES_REQUESTED`.** Run it before the next task. Record **FIX_BASE** — the HEAD the reviewer just judged — and write the surviving findings **verbatim** to `task-<N>-findings.md` in the brief dir (later rounds append under a `## Round <R>` heading); the fixer and the re-reviewer read that file. Write the fixer's brief from [IMPLEMENTER-BRIEF.md](IMPLEMENTER-BRIEF.md)'s `task-<N>-fix-brief.md` template — it carries the round's scope, the Files block widened to what the findings cite, and the verify re-run appended to `task-<N>-report.md` that the re-reviewer reads instead of running tests itself — then dispatch a standard implementer against it.

   After the fixer lands, dispatch a **re-review**: the first review's pointer shape, except the rubric is `re-review-rubric.md`, the findings file replaces the plan-task pointer, the review path is the same `task-<N>-review.md` appended under a `## Round <R>` heading, and the diff range is `<FIX_BASE>..HEAD`, which it runs itself; hand it the task's BASE SHA too for the rubric's comparative exception. A re-review that returns `CHANGES_REQUESTED` starts the next round from a new FIX_BASE. The loop runs until approved — which is not "obey every round": oscillation stops the loop (Hard Rules), and a re-review verdict that merely restyles or reopens a point the last round settled is a finding to dismiss here.

Completion criterion, per task: its ledger line is `[x]` with the commit SHA(s) and its verdict slot filled per Line grammar, every detour it took is on the line as `detour:`, and — when a review ran — `task-<N>-review.md` is on disk with every `Cannot verify:` item resolved by you.

### 4. Short run: hand the ledger forward

A run whose task loop ends with boxes still unchecked on the ledger is a **short run** — the user bounded it ("do task 3, then stop"), or a reroute or a `BLOCKED` report stopped it; the final gate, the loop-close, and the retro belong to the run that lands the **last** plan task. A stop instruction bounds the unit of work, not the phase: the run ends after that unit's verification, whatever it uncovers — newly discovered defects become surfaced findings with a recommendation, never a new fix round. The short run ends here, with the ledger left able to brief whoever picks the plan up.

Read each unchecked task against what this run actually shipped, then write what changed, per Deliverables → Progress ledger → Line grammar:

- on each unchecked task's line, `open:` for a question this run raised about it and `note:` for a landed interface, path, or contract its plan text no longer matches;
- on each landed task's line, the reviewer Notes and deferred findings it left;
- in `.crank/<slug>/grounding.md`, every corrected repo fact with its evidence — a fact wider than one task lands there, not on a line;
- under the anchor, the `Stopped:` line.

Then hand back per step 8.

Completion criterion: every unchecked task has been read against this run's diff and either carries what it needs or is confirmed unaffected, each landed task's Notes are on its line, the `Stopped:` line names the resume point, and `git status --short` is clean or its leftovers named in the hand-back.

### 5. Verify the whole

Every plan task is `[x]` on the ledger by now — a run that stopped earlier left through step 4. Before claiming completion, three gates in order — any failure stops the run:

1. **Plan walk.** Re-tick every task in the plan against an actual commit. Run the plan's gate commands — its `Gates:` header line, or suite / lint / typecheck / build if the plan predates one — fresh this turn and read the output.
2. **Coverage walk.** Walk the plan's Coverage table row by row; for each row, confirm its verify step ran green *this session* — re-run any that are stale or that earlier tasks may have broken. Rows marked human-only go in the retro's Open items. If the plan has no Coverage table, walk the spec's acceptance criteria (or, with no spec, the plan's stated goal) and check each against the diff yourself.
3. **Final review (fresh eyes).** Dispatch one heavy reviewer, cold (Hard Rules → Reviewers judge independently), handing it: the **spec path** (or the plan path if no spec exists) and the **plan path**, including its Coverage table and, when present, its **Global Constraints**; the **ledger path**, whose task lines record each detour taken; the **BASE SHA** the ledger recorded at the start of the run, whose diff range is `<BASE>..HEAD`; `final-review-rubric.md` in the brief dir for its review axes and return format; and the **review path** `final-review.md` in the brief dir, where its full review goes.

On `CHANGES_REQUESTED`, vet each finding before you touch code, per References → Review verdicts. Apply the surviving fixes and nothing else — failing test first for behavioral fixes, separate commits. A horizontal-slice finding is settled by demonstrating each sliced test still fails without its implementation; the demonstrated slice is then recorded in the retro's Final review section. Then re-review once: the same dispatch shape, re-using `final-review-rubric.md` and appending to `final-review.md` under a `## Round <R>` heading, plus the **FIX_BASE** (the HEAD the reviewer judged) and the surviving findings, which route it into the rubric's **Fix round** branch. A finding you can't fix becomes a retro Open item, stated plainly. A surviving finding that would reverse a change an earlier per-task review required is oscillation — stop and surface per Hard Rules.

Completion criterion: the gate commands ran green this session, every Coverage row ran green this session or is human-only and in the retro's Open items, `final-review.md` holds its latest round's verdict, and every finding that round left open is fixed in its own commit, dismissed with its reasoning recorded, or written to the retro as an Open item.

### 6. Close the loop

You ship finished work. Before writing the retro, gather every loose end the plan produced — what earlier short runs parked on the ledger's task lines, plus this run's reviewer Notes, deferred findings, plan risks, human-only Coverage rows, and your own "worth noting" observations — and triage each:

1. **Settle it.** If a command, read, or test can settle it this session, run it now and read the output — a verified fact is settled and appears nowhere in the hand-back. Settling is verification, not rework: a check that reveals a real defect routes to the next bucket, and a confirmed nit stays a deferred finding in the retro.
2. **Fix it.** A defect in shipped code fails the final gate — route it back through Verify the whole. A fix that isn't a plan task is bounded: exactly one investigation, one test-first fix, one review — routed through this skill's own dispatch shapes — then stop and report, whatever that review finds.
3. **Promote it.** A fact that cost this run a detour and would cost the next run the same — a fixture landmine, a known flake, a toolchain trap — outlives the effort ([ARTIFACT-HOME.md](ARTIFACT-HOME.md) → Grounding). Append one line carrying its evidence to the repo's `CLAUDE.md`, `CONTEXT.md`, or an ADR, whichever the repo already has, and record the `file:line` it landed at in the retro's **Promoted** section. With no such file in the repo it degrades to the next bucket — a decision naming the line and where you would put it, never a file you create unasked.
4. **Escalate it as a decision.** What genuinely needs the user survives: a tradeoff only they can weigh, or an action only a human can perform (a visual smoke check, a credential you don't hold).

Completion criterion: every loose end is settled, fixed, promoted with the `file:line` it landed at, or written as a decision with a recommendation — none merely restates a fact you could have checked this session.

### 7. Retro

Write the retro to `.crank/<slug>/retro.md` at the repository root, with the sections listed in Deliverables → Retro.

### 8. Hand back

Report finished work: what shipped, the verification that proves it, and — only when items survived Close the loop — each one as written there.

A short run reports what it has instead: the tasks that landed with their commit SHAs, the tasks that remain, why it stopped, and the ledger path, with **Next:** `/crank-execute .crank/<slug>/plan.md` to resume — the ledger carries the rest.

Take the safe defaults, state them, and lead with the durable next step:

- The retro stays at its `.crank/<slug>/` path; commits stay local on `<branch>` — one line each, stated.
- **Next:** the single command or decision that moves the work forward — e.g. `git merge <branch>` from the base branch, or the one surviving decision from Close the loop.

Close with a single trailing sentence noting the alternatives on request (open a PR, discard the branch, copy or print the retro) — prose, not a numbered question. Then stop.
