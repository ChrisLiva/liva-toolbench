---
name: execute
description: Execute an implementation plan task-by-task — TDD where the seam exists, verification evidence before every "done" claim, optional per-task subagents — then write a retro. Use when the user types /execute or hands you a plan to ship.
argument-hint: "[optional path to plan.md]"
---

# Execute

Ship the plan. Treat the plan as the source of truth — direct, don't redesign. **Evidence before claims:** never report a task done without running its verification this turn and reading the output. **Plan is frozen** during execution — surprises become retro entries, not silent reroutes.

## Vocabulary

Shared design language across the crank skills (spec → plan → execute). Use these terms with these meanings:

- **Module** — anything with an interface and an implementation: a function, class, file, or larger slice.
- **Interface** — the full contract a caller must understand: signatures, invariants, ordering, errors, config.
- **Depth** — how much an interface hides. A **deep** module exposes a small interface over substantial behavior; a **shallow** one exposes nearly as much as it hides.
- **Deletion test** — imagine the module gone. If its complexity simply vanishes, it was a pass-through; if that complexity reappears across many callers, the boundary earned its place.
- **Seam** — a place where behavior can be swapped without editing in that place; the location of an interface, and the surface tests drive (the production node/endpoint/entry point a real user reaches, never a synthetic stand-in).
- **Port / adapter** — a seam that crosses a dependency: the **port** is the interface, an **adapter** is a concrete fill (production HTTP/db vs. in-memory test double). Two adapters justify a port; one is just indirection.

## Load and critically review

If `$ARGUMENTS` is a path, read it; otherwise use the plan already in the conversation. Read it in full. Before starting, flag anything that would block execution: missing context, ambiguous step, undefined symbol, contradiction with the codebase. If you find blockers, surface them and stop — don't push through. Check `git status --short` and the current branch; if you're on `main`/`master` with a non-trivial change, ask once before committing.

## Pick the execution shape

You decide based on the plan — there is no required mode:

- **Solo (in this session)** — small plans (~3 tasks or fewer), tasks that share in-flight state, or quick fixes.
- **Sequential subagents** — larger plans where fresh context per task beats a crowded session. Default for >3 tasks.
- **Parallel subagents** — only when tasks touch disjoint files with no shared state.

State the choice in one sentence and proceed.

## Per task

1. **Implement.** Failing test → watch it fail → minimal impl → run the task's `verify` step → commit with a message that names the task. Skip TDD only when the plan explicitly does (config flips, doc edits, generated code).
2. **Review.** Either self-review (solo mode) or dispatch a reviewer subagent (`Agent` tool, `description: "Review task <N>"`). Two-stage rubric: **spec compliance** first (does the diff implement what the task says, nothing more, nothing less?), then **code quality** (DRY / SOLID / YAGNI, error handling at boundaries, tests assert behavior through the interface, not internal state). Within code quality, check **depth** for any *new* module the task introduced: does it fail the deletion test (a pass-through whose complexity vanishes if removed), or is its interface nearly as complex as its implementation (shallow)? If so, the fix is to fold it into its caller — a bounded cleanup of this task's own diff, not a redesign of the plan's structure. Apply this to modules the task newly introduced and to any the plan's **Refactor scope** named for reshaping (there, the reshape *is* the task — hold it to the depth bar the spec set); existing modules outside that scope keep frozen boundaries. Reviewer returns `APPROVED` or `CHANGES_REQUESTED` with a bulleted issue list. On changes, re-implement and re-review until approved — don't carry critical or important issues into the next task.

**Subagent dispatch.** When you delegate the implementer, pass the full task text (don't make the subagent read the plan) plus context: branch, files-block, exact verify command, "do not push, do not amend earlier commits, do not touch files outside the files-block." Pick the model by task complexity — cheap for mechanical single-file work, standard for multi-file integration, capable for design judgment. Dispatch parallel implementers in a single message only when their files-blocks don't overlap. Implementer status: `DONE` → review; `DONE_WITH_CONCERNS` → read first, address if they affect correctness; `NEEDS_CONTEXT` → provide and re-dispatch; `BLOCKED` → escalate model once, then surface to the user.

## Verify the whole

Before claiming completion: re-tick every task in the plan against an actual commit. Run the plan's overall validation commands (suite, lint, typecheck, build) fresh this turn and read the output. Any failure stops the run.

## Retro

Write a retro to a fresh OS temp file: `$(mktemp -t crank-retro).md`. Sections:

- **Summary** — what shipped, commits `<first>..<last>` on `<branch>`.
- **Deviations** — anywhere the diff meaningfully differs from the plan and why. "None" if none.
- **Open items** — follow-ups, surprises future related work should know about.
- **Validation evidence** — commands run, outcomes.

## Hand back

In chat prose, offer for the retro:

- **Keep the temp file** (default) — the path is known; user can move it or feed it elsewhere later.
- **Copy into the repo** — copy to a user-named path under the working directory.
- **Print inline and delete** — paste the final contents and remove the temp file.

For the branch and commits, **ask the user how to finish** (merge / PR / leave / discard) — never force-push, amend, rewrite history, or delete a branch without explicit approval. Then stop.
