---
name: lite-execute
description: "Execute a PRD, spec, or implementation plan: implement, verify, review, and commit the work."
argument-hint: "[path to plan.md, or a .crank/ plan slug]"
disable-model-invocation: true
---

Implement the work described in the plan (or PRD/spec) the user provides. Resolve the plan first — every effort's artifacts live in one directory, `.crank/<slug>/` at the working root:

1. **Explicit path** — read it as-is; the slug is the plan's parent directory name.
2. **Bare slug** — resolves to `.crank/<slug>/plan.md`.
3. **No argument, plan in the conversation** — use it; derive a slug from the plan's title — its artifacts live in `.crank/<slug>/`.
4. **No argument, exactly one plan on disk** — use it without asking.
5. **No argument, several plans** — ask via a structured question listing each plan with its derived status: *not started* (no `## Progress` block), *in progress* (unchecked boxes remain), *done* (all `[x]`). An effort directory without a `plan.md` (e.g. spec-only) shows as "no plan yet" and is not executable.
6. **No argument, no plans anywhere** — say so and recommend the plan phase (`/crank-lite plan …`).

**Adopt legacy artifacts on encounter.** Resolving an artifact checks the per-plan path first, then the legacy flat path (`.crank/<phase>-<slug>.md`). On a legacy hit, move the file into `.crank/<slug>/…` and state the new path so a user's saved link is updated once. Never clobber: if both the legacy and per-plan copies exist, stop and ask instead of overwriting either.

## Execution shape

**Before touching any file, pick the execution shape and state it** — you decide based on the plan's coupling, not its task count; there is no required mode:

- **Solo** — the work is confined to one module or one area of code, or the tasks share deep in-flight state — whatever the task count. Implement inline on this thread.
- **Orchestrate** — tasks touch genuinely disjoint file sets: you are the orchestrator; standard-tier subagents implement (see Subagent tiers). Dispatch one subagent per task (parallel only when tasks touch disjoint files), each with a brief, targeted instruction: the task text, the relevant file paths, the verification command it must run and report output from, the detour rule from Implement below — with any detour taken reported back in its return — and the return rule: return only when every command it started has finished; long verifications run synchronously, their output read in the same turn that reports them. Verify each returned task yourself with a cheap check (typecheck, targeted test) instead of re-reading the whole diff — keep this thread's context for coordination, not implementation. When a dispatched agent is out past the point you expected it back, reconcile against durable state — `git log`, the Progress block, its report — then resume it or surface the stall; a "standing by" turn is never the move.

A stated shape binds the run: if you said orchestrate, the first action on each task is a dispatch, not an inline edit. Drop back to solo only by saying so and why.

## Implement

Track the run with tasks: create one entry per plan task before starting work, mark it in progress when you begin it, and completed the moment it lands. Every run gets this, solo included — it is how the user sees progress mid-run.

Durable progress lives in the plan file, not the task list (which dies with the session). Before the first task, add a `## Progress` block at the top of the plan — one `- [ ] Task N: <subject>` line per task — and flip each line to `[x] — <commit SHA>` the moment that task's commit lands. On invocation, read this block first: an `[x]` line is done — confirm it against `git log` and never redo it. This block is how an interrupted run resumes in a fresh session.

Run typechecking regularly, single test files regularly, and the full test suite once at the end. When a change has no test seam, validate it with a probe — a small throwaway script in the OS temp dir that asserts exact outputs and exits non-zero on failure; watch it fail once before trusting its pass, treat its output as the verification evidence, and delete it before commit.

Standing defect rules while implementing: any encode/decode or save/restore pair gets a round-trip assertion on a hostile real value (sub-millisecond timestamps, unicode, boundary sizes), not a friendly fixture; handling one member of an error family means checking its siblings (EPERM beside EACCES) or noting the single-case choice; every parser or loop over external input gets its empty case exercised once; a test not born RED gets one deliberate mutation to watch it fail before you trust its pass; edits to user-owned files (configs, gitignores) assert untouched lines survive byte-identical; and a new test earns its place only by pinning a behavior no existing test pins — extend the journey test already walking that seam with a failing assertion rather than adding a sibling that rebuilds its setup, and commit only tests that would survive a rewrite of the implementation in another language.

The plan's destination is frozen; the road is not. When a bug, stale detail (renamed symbol, moved file), or failed assumption blocks a task, fix it as a detour — the smallest change that still ships exactly what the plan promises — and note it in the retro's deviations. A fix that would change what ships is a reroute: stop and surface it with your recommendation. Pre-existing bugs off the plan's path stay retro notes, never side quests.

## Review and commit

Once done implementing the entire plan, spawn a heavy-tier subagent (see Subagent tiers) to adversarially review your work against the original plan. Address confirmed findings before committing.

Before committing, inspect the worktree and stage only the files this plan's work changed. If unrelated user changes are present, leave them untouched and ask before committing only when you cannot separate your changes safely.

## Close the loop

Before the retro, close the loop — you ship finished work: settle every loose end (reviewer findings, plan risks, your own "worth noting" observations) with a command, read, or test this session; a loose end survives only as a decision the user must make or an action only a human can perform, written with your recommendation.

## Retro

Once you've finished implementation and review, record a concise retro to `.crank/<slug>/retro.md` at the working root (create `.crank/` if missing, with a `.crank/.gitignore` containing `*`; only outside a git repo, fall back to `${TMPDIR:-/tmp}/lite-<slug>/retro.md` and say so) and stop. Keep the artifact light: include what changed, verification run, review outcome, deviations from the plan, and any surviving decisions when those sections earn their place. Tell the user the commit SHA and retro path; when nothing survived the loop-close, say the work is complete.

## Subagent tiers

The user's own configuration wins: if their global or project instructions state subagent model preferences, map the tiers onto them. Otherwise resolve per harness:

<subagent-tiers>
- **standard** (implementers): Claude Code `model: sonnet` · Codex GPT-5.6-Terra at medium effort · Cursor `cursor-composer-2-5`
- **heavy** (adversarial review): Claude Code `model: opus` · Codex GPT-5.6-Sol at high effort · Cursor GPT-5.6-Sol at high effort
</subagent-tiers>
