---
name: lite-execute
description: "Execute a PRD, spec, or implementation plan: implement, verify, review, and commit the work."
argument-hint: "[path to plan.md, or a .crank/ plan slug]"
disable-model-invocation: true
---

Implement the work described in the plan (or PRD/spec) the user provides. Every effort's artifacts live in one directory, `.crank/<slug>/`, per [ARTIFACT-HOME.md](ARTIFACT-HOME.md), read before writing any artifact. Resolve the plan first:

1. **Explicit path** — read it as-is; the slug is the plan's parent directory name.
2. **Bare slug** — resolves to `.crank/<slug>/plan.md`.
3. **No argument, plan in the conversation** — use it; derive a slug from the plan's title.
4. **No argument, exactly one plan on disk** — use it without asking.
5. **No argument, several plans** — ask via a structured question listing each plan with its derived status per the `## Progress` block under Implement. An effort directory without a `plan.md` (e.g. spec-only) shows as "no plan yet" and is not executable.
6. **No argument, no plans anywhere** — say so and recommend the plan phase (`/crank-lite plan …`).

**Adopt legacy artifacts on encounter.** Resolving an artifact checks the per-plan path first, then the legacy flat path; on a hit there, migrate it per [ARTIFACT-HOME.md](ARTIFACT-HOME.md).

## Execution shape

Pick the execution shape and **call out the pre-flight**: write the block below into your reply with every line filled, then continue in the same turn — every invocation, resumed runs included. Completion criterion: the filled block stands in your reply text ahead of the Progress block, the first edit, and the first dispatch.

```
**Pre-flight**
- Plan: .crank/<slug>/plan.md (spec: spec.md · brainstorm: brainstorm.md)
- Branch: <current branch>
- Shape: <solo | orchestrate>
- Subagents: standard = <model> (implementers) · heavy = <model> (adversarial review)
- Tasks: <N> (<M> remaining)
```

The Plan line's parenthetical names only sibling artifacts that actually exist in `.crank/<slug>/` — drop it when there are none. Models are the resolved names (see Subagent tiers), never bare tier labels. Solo's Subagents line reads `heavy = <model> (adversarial review) — implementation inline`. `<M>` is the Progress block's unchecked boxes (see Implement); a fresh run has `M = N`.

Decide from the plan's coupling, not its task count:

- **Solo** — the work is confined to one module or one area of code, or the tasks share deep in-flight state. Implement inline on this thread.
- **Orchestrate** — tasks touch genuinely disjoint file sets: you are the orchestrator; standard-tier subagents implement (see Subagent tiers). Dispatch one subagent per task, each with a brief, targeted instruction carrying five things:
  1. the task text;
  2. the file paths it touches, plus the absolute path to this skill's `VOCABULARY.md`;
  3. the verification command it must run and report output from;
  4. the detour rule from Implement below, with any detour taken reported back in its return;
  5. the return rule — return only when every command it started has finished; long verifications run synchronously, their output read in the same turn that reports them.

  Done when the brief carries all five. Verify each returned task yourself with a cheap check (typecheck, targeted test) instead of re-reading the whole diff. When a dispatched agent is out past the point you expected it back, reconcile against durable state — `git log`, the Progress block, its report — then resume it or surface the stall; a "standing by" turn is never the move.

A stated shape binds the run: if you said orchestrate, the first action on each task is a dispatch, not an inline edit. Drop back to solo only by saying so and why.

Every dispatch — implementer or reviewer — is a blocking call: from spawn to return the subagent owns the work, and everything else queues behind reading its return. Parallel dispatches go out in one message and block as one. The wait breaks only for the stalled-dispatch reconcile above.

## Implement

Track the run with tasks — one entry per plan task, created before work starts and flipped complete the moment the task lands. Every run gets this, solo included.

Durable progress lives in the plan file, not the task list (which dies with the session). Before the first task, add a `## Progress` block at the top of the plan — `Base: <HEAD SHA before the first task>`, then one `- [ ] Task N: <subject>` line per task — and flip each line to `[x] — <commit SHA>` once that task's check has passed and its commit lands. On invocation, read this block first: an `[x]` line is done — confirm it against `git log` and never redo it. A plan's status reads off this block: *not started* (no block), *in progress* (unchecked boxes remain), *done* (all `[x]`).

Before you implement, read the `## Verification language` section of [VOCABULARY.md](VOCABULARY.md), plus the **seam** entry above it: this skill leans on the **probe**, its **oracle**, the **seam**, the **journey test**, the **redundant test**, and the **rewrite test**.

Before flipping a task's box, run the check the plan names for that task — or, when it names none, the gate its Grounding section records, else the repo's typecheck plus the test file covering the touched behavior — and read its output in the same turn. Run the full suite once, before the review dispatch. When a change has no test seam, validate it with a **probe** and treat its passing output as that task's verification evidence.

Standing defect rules while implementing:

- Any encode/decode or save/restore pair gets a round-trip assertion on a hostile real value (sub-millisecond timestamps, unicode, boundary sizes), not a friendly fixture.
- Handling one member of an error family means checking its siblings (EPERM beside EACCES) or noting the single-case choice.
- Every parser or loop over external input gets its empty case exercised once.
- A test that passed on its first run gets one deliberate mutation to watch it fail.
- Edits to user-owned files (configs, gitignores) assert untouched lines survive byte-identical.
- A new test earns its place only if it is not a **redundant test** and it survives the **rewrite test**; otherwise extend the **journey test** at that seam with a failing assertion.

The plan's destination is frozen; the road is not. When a bug, stale detail (renamed symbol, moved file), or failed assumption blocks a task, fix it as a detour — the smallest change that still ships exactly what the plan promises — and note it in the retro's deviations; beside the task's Progress flip, append the corrected fact as one line in the plan's Grounding section ([ARTIFACT-HOME.md](ARTIFACT-HOME.md) → Grounding), so a resumed run stops re-hitting the same stale detail. A fix that would change what ships is a reroute: stop and surface it with your recommendation. Pre-existing bugs off the plan's path stay retro notes, never side quests.

## Review and commit

Once done implementing the entire plan, dispatch a heavy-tier reviewer (see Subagent tiers) to adversarially review the work against the plan, handing it pointers only — the plan path, the Progress block's `Base` SHA, the diff command `git diff <Base>..HEAD`, and the absolute path to this skill's `VOCABULARY.md`, whose **dead seam**, **implementation-detail test**, and **redundant test** the review turns on — never your characterization of the diff. Tell it to work its lookups in **rounds**: a round's **frontier** is every lookup whose answer it does not need before issuing the next one, and the whole frontier goes out as one batch in a single turn, every return read before it composes the next round. It returns each finding as `CONFIRMED` or `REFUTED` with the code evidence, defaulting to `REFUTED` when the evidence is thin. Completion criterion: every `CONFIRMED` finding is fixed and re-verified by the same check, or recorded in the retro's deviations with the reason it stands.

Before committing, inspect the worktree and stage only the files this plan's work changed. If unrelated user changes are present, leave them untouched and ask before committing only when you cannot separate your changes safely.

## Close the loop

Before the retro, settle every loose end (reviewer findings, plan risks, your own "worth noting" observations) with a command, read, or test this session; a loose end survives only as a decision the user must make or an action only a human can perform, written with your recommendation. A fact that cost this run a detour and would cost the next run the same — a fixture landmine, a known flake, a toolchain trap — outlives the effort: append one line carrying its evidence to the repo's `CLAUDE.md`, `CONTEXT.md`, or an ADR, whichever the repo already has, and name where it landed in the retro; with no such file it survives as a decision naming the line and its target.

## Retro

Record a concise retro to `.crank/<slug>/retro.md` per [ARTIFACT-HOME.md](ARTIFACT-HOME.md), read before writing the file, and stop. Keep the artifact light: include what changed, verification run, review outcome, deviations from the plan, where any promoted fact landed, and any surviving decisions when those sections earn their place. Tell the user the commit SHA and retro path; when nothing survived the loop-close, say the work is complete.

## Subagent tiers

Resolve the tiers once per run and reuse the mapping. A subagent model preference stated in the user instructions already loaded this session (user- and project-level `CLAUDE.md` / `AGENTS.md`) is binding: map the tiers onto it, even when it names a weaker model than a fallback below. With no such preference stated, use your harness's fallback:

<subagent-tiers>
- **standard** (implementers): Claude Code `model: sonnet` · Codex GPT-5.6-Terra at medium effort · Cursor `cursor-composer-2-5`
- **heavy** (adversarial review): Claude Code `model: opus` · Codex GPT-5.6-Sol at high effort · Cursor GPT-5.6-Sol at high effort
</subagent-tiers>
