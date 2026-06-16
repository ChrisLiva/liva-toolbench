---
name: execute
description: Execute an implementation plan task-by-task — TDD where the seam exists, verification evidence before every "done" claim, optional per-task subagents — then write a retro. Use when the user types /execute or hands you a plan to ship.
argument-hint: "[optional path to plan.md]"
---

# Execute

Ship the plan. Treat the plan as the source of truth — direct, don't redesign.

<rules>
- **Evidence before claims.** Never report a task done without running its verification this turn and reading the output.
- **Plan is frozen** during execution — surprises become retro entries, not silent reroutes.
- **Every subagent this skill spawns runs on Sonnet** (`model: sonnet`) unless otherwise specified.
- **Never** force-push, amend earlier commits, rewrite history, or delete a branch without explicit approval.
</rules>

## Subagents

Bias toward dispatch over main-thread work: exploring the codebase to settle a question, validating a plan claim against the source, implementing tasks, reviewing diffs.

<tradeoff>
**Dispatching** gives each task a clean Sonnet context — implementation quality doesn't degrade as the session grows, and reviewers see the diff with fresh eyes. It costs dispatch overhead and forces you to write self-contained briefs (the subagent knows nothing you don't pass it). **Main-thread work** keeps in-flight state (an import you just added, a convention you just noticed) at zero handoff cost — but every task's source and noise accumulates in your window, and your own review of your own work is the weakest kind. Lean toward dispatch as task count grows; stay on-thread for quick fixes that share state.
</tradeoff>

## Vocabulary

Shared design language across the crank skills (the spec skill defines the full set). The terms this skill leans on:

- **Depth** — how much an interface hides. A **deep** module exposes a small interface over substantial behavior; a **shallow** one exposes nearly as much as it hides.
- **Deletion test** — imagine the module gone. If its complexity simply vanishes, it was a pass-through; if that complexity reappears across many callers, the boundary earned its place.
- **Seam** — a place where behavior can be swapped without editing in that place; the location of an interface, and the surface tests drive (the production node/endpoint/entry point a real user reaches, never a synthetic stand-in).
- **Spaghetti growth** — a one-off conditional, flag, or special case bolted onto a flow the plan never named. A design problem, not a style nit: route the behavior behind the module that owns the concept.

## Workflow

Copy this checklist and check off steps as you complete them:

```
Execute progress:
- [ ] Plan loaded (and spec, via the plan's Spec: header); blockers surfaced
- [ ] Execution shape picked and stated in one sentence
- [ ] Per task: implement → verify → review → commit (repeat for all tasks)
- [ ] Verify the whole: plan walk → coverage walk → final review
- [ ] Retro written
- [ ] Hand back
```

## Load and critically review

If `$ARGUMENTS` is a path, read it; otherwise use the plan already in the conversation. Read it in full. If the plan's header names a spec (`Spec:` line), read that too — it is the contract the final review runs against; the plan is only its decomposition. Before starting, flag anything that would block execution: missing context, ambiguous step, undefined symbol, contradiction with the codebase. If you find blockers, surface them and stop — don't push through. Check `git status --short` and the current branch; if you're on `main`/`master` with a non-trivial change, ask once before committing.

## Pick the execution shape

You decide based on the plan — there is no required mode. State the choice in one sentence and proceed.

- **Solo (in this session)** — *Gains:* zero dispatch overhead; full in-flight state carries between tasks. *Costs:* every task's source and noise stays in your window, degrading later tasks; self-review is the weakest review. *Fits:* small plans (~3 tasks or fewer), tasks that share in-flight state, quick fixes.
- **Sequential subagents** — *Gains:* fresh context per task; an independent reviewer per diff. *Costs:* each dispatch pays re-orientation; you must brief completely or the implementer guesses. *Fits:* the default for >3 tasks.
- **Parallel subagents** — *Gains:* wall-clock speed. *Costs:* no shared state between implementers; overlapping edits conflict. *Fits:* only when tasks touch disjoint files with no shared state.

## Per task

1. **Implement.** Failing test → watch it fail → minimal impl → run the task's `verify` step → commit with a message that names the task. Skip TDD only when the plan explicitly does (config flips, doc edits, generated code).
2. **Review.** Either self-review (solo mode) or dispatch a Sonnet reviewer subagent (`Agent` tool, `description: "Review task <N>"`). Two-stage rubric, in order:
   - **Spec compliance** — does the diff implement what the task says, nothing more, nothing less?
   - **Code quality** — DRY / SOLID / YAGNI, error handling at boundaries, tests assert behavior through the interface, not internal state. Within code quality, check **depth** for any *new* module the task introduced: does it fail the deletion test (a pass-through whose complexity vanishes if removed), or is its interface nearly as complex as its implementation (shallow)? If so, the fix is to fold it into its caller — a bounded cleanup of this task's own diff, not a redesign of the plan's structure. Apply this to modules the task newly introduced and to any the plan's **Refactor scope** named for reshaping (there, the reshape *is* the task — hold it to the depth bar the spec set); existing modules outside that scope keep frozen boundaries. Also flag, bounded to this task's own diff: **spaghetti growth** (the diff threads a one-off conditional, flag, or special case through a flow the plan never named — route it behind the module that owns the concept), **bespoke duplication** (the diff re-implements a helper the codebase already provides — call the canonical one instead), and **boundary smells** (the diff uses casts, `any`, or new optional parameters to paper over an unclear contract — make the invariant explicit; if the contract itself is the problem, that's a retro entry, not a cast).

   Reviewer returns `APPROVED` or `CHANGES_REQUESTED` with a bulleted issue list. On changes, re-implement and re-review until approved — the loop costs turns now, but carrying a critical or important issue into the next task costs more later, because subsequent tasks build on the defect.

**Subagent dispatch.** When you delegate the implementer, pass the full task text (don't make the subagent read the plan) plus context: branch, files-block, exact verify command, "do not push, do not amend earlier commits, do not touch files outside the files-block." Dispatch parallel implementers in a single message only when their files-blocks don't overlap. Implementer status: `DONE` → review; `DONE_WITH_CONCERNS` → read first, address if they affect correctness; `NEEDS_CONTEXT` → provide and re-dispatch; `BLOCKED` → escalate the model once (the Sonnet rule's sole exception), then surface to the user.

## Verify the whole

Before claiming completion, three gates in order — any failure stops the run:

1. **Plan walk.** Re-tick every task in the plan against an actual commit. Run the plan's overall validation commands (suite, lint, typecheck, build) fresh this turn and read the output.
2. **Coverage walk.** Walk the plan's Coverage table row by row; for each row, confirm its verify step ran green *this session* — re-run any that are stale or that earlier tasks may have broken. Rows marked human-only go in the retro's Open items, not silently skipped. If the plan has no Coverage table, walk the spec's acceptance criteria (or, with no spec, the plan's stated goal) and check each against the diff yourself.
3. **Final review (fresh eyes).** Per-task reviewers saw one task at a time; this pass catches what they couldn't. Dispatch one Opus reviewer subagent (`Agent` tool, `description: "Final review vs spec"`, `model: opus`) with the spec path (or the plan path if no spec exists), the Coverage table, and the diff range (`git diff <first-commit>^..HEAD`). Pass this brief verbatim:

<brief>
Review the shipped diff against the spec. Check every acceptance criterion against the diff — met, missing, or quietly substituted. Then check cross-task coherence: naming drift between tasks, dead code an early task left once a later one landed, missing wiring between independently built pieces. Then check structural quality of the whole diff: **spaghetti growth** (a one-off conditional, flag, or special case threaded through a flow the plan never named, instead of routed behind the module that owns the concept), **bespoke duplication** (the diff re-implements a helper the codebase already provides, or two tasks independently built near-duplicate helpers that should be one — grep to confirm), and **boundary smells** (casts, `any`, or new optional parameters papering over an unclear contract where the invariant could be explicit). Cite `file:line`; don't restyle or expand scope. Return `APPROVED` or `CHANGES_REQUESTED` with a bulleted, bounded fix list.
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
