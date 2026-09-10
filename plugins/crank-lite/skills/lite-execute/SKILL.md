---
name: lite-execute
description: "Execute a PRD, spec, or implementation plan: implement, verify, review, and commit the work."
argument-hint: "[path to plan.md, or a .crank/ plan slug]"
disable-model-invocation: true
---

Every effort's artifacts live in one directory, `.crank/<slug>/`, per [ARTIFACT-HOME.md](ARTIFACT-HOME.md); read it before resolving or writing any artifact. Resolve the plan first:

1. **Explicit path** — read it as-is; the slug is the plan's parent directory name.
2. **Bare slug** — resolves to `.crank/<slug>/plan.md`.
3. **No argument, plan in the conversation** — use it; derive a slug from the plan's title.
4. **No argument, exactly one plan on disk** — use it without asking.
5. **No argument, several plans** — ask via a structured question listing each plan with its status (see Plan state). An effort directory without a `plan.md` (e.g. spec-only) shows as "no plan yet" and is not executable.
6. **No argument, no plans anywhere** — say so and recommend the plan phase (`/crank-lite plan …`).

## Plan state

Durable progress lives in the plan file. Before the first task, add a `## Progress` block at the top of the plan — `Base: <HEAD SHA before the first task>`, then one `- [ ] Task N: <subject>` line per task — and flip each line to `[x] — <commit SHA>` once that task's **check** has passed and its commit lands. On invocation, read this block first: an `[x]` line is done — confirm it against `git log` and never redo it. A plan's status reads off this block: *not started* (no block), *in progress* (unchecked boxes remain), *done* (all `[x]`).

A task's **check** is the first of these that exists:

1. the check the plan names for that task;
2. the gate the plan's grounding records ([ARTIFACT-HOME.md](ARTIFACT-HOME.md) → Grounding);
3. the repo's typecheck plus the test file covering the touched behavior.

Read the check's output in the same turn it runs. When a change has no test seam, validate it with a **probe** and treat its passing output as the check.

## Subagent tiers

Resolve the tiers once per run, before the Pre-flight block, and reuse the mapping at every dispatch. The source of truth is a subagent model preference stated in the user instructions already loaded this session (user- and project-level `CLAUDE.md` / `AGENTS.md`); it is binding: map the tiers onto it, even when it names a weaker model than a fallback below, and a preference that covers all subagent work covers implementers too. The block below is a fallback only, for a session whose loaded instruction files state no such preference:

<subagent-tiers>
- **standard** fallback (implementers): Claude Code `model: sonnet` · Codex GPT-5.6-Terra at medium effort · Cursor `cursor-composer-2-5`
- **heavy** fallback (adversarial review): Claude Code `model: opus` · Codex GPT-5.6-Sol at high effort · Cursor GPT-5.6-Sol at high effort
</subagent-tiers>

## Shape

Decide the shape from the plan's coupling alone:

- **Solo** — the work is confined to one module or one area of code, or the tasks share deep in-flight state. Implement inline on this thread.
- **Orchestrate** — tasks touch genuinely disjoint file sets: you are the orchestrator; standard-tier subagents implement, one per task, dispatched per [DISPATCH.md](DISPATCH.md).

A stated shape binds the run: if you said orchestrate, the first action on each task is a dispatch, not an inline edit. Drop back to solo only by saying so and why. Every dispatch — implementer or reviewer — is a **blocking call**: everything else queues behind reading its return. The wait breaks only for a **stalled** dispatch — one out past the point you expected it back: reconcile against durable state (`git log`, the Progress block, its report), then resume it or surface the stall.

## Pre-flight

Write this block into your reply with every line filled, then continue in the same turn — every invocation, resumed runs included:

```
**Pre-flight**
- Plan: .crank/<slug>/plan.md (spec: spec.md · brainstorm: brainstorm.md)
- Branch: <current branch>
- Shape: <solo | orchestrate>
- Subagents: standard = <model> (implementers) · heavy = <model> (adversarial review) · resolved from <user CLAUDE.md | project CLAUDE.md/AGENTS.md | harness fallback>
- Tasks: <N> (<M> remaining)
```

The Plan line's parenthetical names only sibling artifacts present in `.crank/<slug>/`; drop it when there are none. Models are the resolved names, never bare tier labels, and `resolved from` names the instruction file whose subagent preference the tiers were mapped onto, or `harness fallback` when no loaded instruction file states one; `harness fallback` beside a stated preference is a wrong line. Solo's Subagents line reads `heavy = <model> (adversarial review) — implementation inline`, with the same `resolved from` tail. `<M>` is the Progress block's unchecked boxes, or `<N>` before the block exists. Completion criterion: the filled block stands in your reply text ahead of the Progress block, the first edit, and the first dispatch.

## Implement

Track the run with tasks — one entry per plan task, created before work starts and flipped complete the moment the task lands. Every run gets this, solo included.

Before you implement, read the `## Verification language` section of [VOCABULARY.md](VOCABULARY.md), plus the **seam** entry above it: this skill leans on the **probe**, its **oracle**, the **seam**, the **journey test**, the **redundant test**, and the **rewrite test**.

Run each task's check before flipping its box. Run the full suite once, before the review dispatch.

Standing defect rules while implementing:

- Any encode/decode or save/restore pair gets a round-trip assertion on a hostile real value (sub-millisecond timestamps, unicode, boundary sizes).
- Handling one member of an error family means checking its siblings (EPERM beside EACCES) or noting the single-case choice.
- Every parser or loop over external input gets its empty case exercised once.
- A test that passed on its first run gets one deliberate mutation to watch it fail.
- Edits to user-owned files (configs, gitignores) assert untouched lines survive byte-identical.
- A new test earns its place only if it is not a **redundant test** and it survives the **rewrite test**; otherwise extend the **journey test** at that seam with a failing assertion.

The plan's destination is frozen; the road is not. When a bug, stale detail (renamed symbol, moved file), or failed assumption blocks a task, fix it as a **detour** — the smallest change that still ships exactly what the plan promises — and note it in the retro's deviations; beside the task's Progress flip, append the corrected fact as one line to the plan's grounding, so a resumed run stops re-hitting the same stale detail. A fix that would change what ships is a **reroute**: stop and surface it with your recommendation. Pre-existing bugs off the plan's path stay retro notes, never side quests.

## Short run

A run that ends with boxes still unchecked in the `## Progress` block — the user bounded it ("do task 2, then stop"), or a reroute stopped it — is a **short run**: the review, the loop-close, and the retro below belong to the run that lands the **last** plan task, since the reviewer reads the whole diff against the whole plan. Leave the plan able to brief whoever picks it up instead:

- On each unchecked task's line, append `— open: <a question this run raised about it>` and `— note: <an interface, path, or contract its task text no longer matches>`; on each task that landed this run, append the review findings and observations the retro would otherwise have carried.
- Bank each corrected repo fact, detour or not, with its evidence in the plan's grounding as under Implement.
- Under the Progress block's `Base:` line, write `Stopped: <why> — resume at Task <N>`; the run that resumes overwrites it.

Then report the tasks that landed with their commit SHAs, the tasks that remain, and `/lite-execute <plan path>` to resume. Completion criterion: every unchecked task carries what this run changed for it or is confirmed unaffected, and the `Stopped:` line names the resume point.

## Review and commit

Once done implementing the entire plan, dispatch a heavy-tier reviewer to adversarially review the work against the plan, handing it pointers only — the absolute path to this skill's [REVIEW-BRIEF.md](REVIEW-BRIEF.md), the plan path, the Progress block's `Base` SHA, the diff command `git diff <Base>..HEAD`, and the absolute path to this skill's `VOCABULARY.md` — never your characterization of the diff. It returns each finding as `CONFIRMED` or `REFUTED` with the code evidence. Completion criterion: every `CONFIRMED` finding is fixed and re-verified by the same check, or recorded in the retro's deviations with the reason it stands.

Before committing, inspect the worktree and stage only the files this plan's work changed. If unrelated user changes are present, leave them untouched and ask before committing only when you cannot separate your changes safely.

## Close the loop

Before the retro, settle every loose end (what earlier short runs parked on the Progress lines, reviewer findings, plan risks, your own "worth noting" observations) with a command, read, or test this session; a loose end survives only as a decision the user must make or an action only a human can perform, written with your recommendation. A fact that cost this run a detour and would cost the next run the same — a fixture landmine, a known flake, a toolchain trap — outlives the effort: append one line carrying its evidence to the repo's `CLAUDE.md`, `CONTEXT.md`, or an ADR, whichever the repo already has, and name where it landed in the retro; with no such file it survives as a decision naming the line and its target.

## Retro

Record the retro to `.crank/<slug>/retro.md` and stop. Include, when each earns its place: what changed, verification run, review outcome, deviations from the plan, where any promoted fact landed, and any surviving decisions. Tell the user the commit SHA and retro path; when nothing survived the loop-close, say the work is complete.
