---
name: crank
description: Front door to the crank design pipeline — routes the ask to brainstorm, spec, or plan and runs that phase.
argument-hint: "[brainstorm|spec|plan] [idea, topic, or artifact path]"
disable-model-invocation: true
---

# Crank

## Goal

Route the user's ask to the right phase of the design pipeline — **brainstorm → spec → plan** — then run that phase from its own file in this directory:

| Route | Phase file | Right when |
| --- | --- | --- |
| `brainstorm` | [BRAINSTORM.md](BRAINSTORM.md) | The idea is raw; its approach, shape, or product direction is still open. |
| `spec` | [SPEC.md](SPEC.md) | The idea is formed (or a brainstorm brief exists) and needs acceptance criteria and technical decisions. |
| `plan` | [PLAN.md](PLAN.md) | Behavior and design are settled — a finished spec, or a well-understood change like a scoped bug fix — and only "how to build it" remains. |

Execution is deliberately **not** a route: when a plan is done, recommend `/crank-execute` and stop. Sharpening an artifact without advancing it is `/crank-refine`'s job.

Four asks enter elsewhere: a codebase-wide hunt for shallow modules or leaking seams is `/crank-deepen` (it hands back a brainstorm brief); judging existing changes is `/crank-review`, a test suite is `/crank-test-prune`, and stripping AI slop, hunting code-judo restructurings, or pruning outgrown comments over a declared scope is `/crank-deslop`.

## Triage

The first rule that applies wins:

1. **Explicit route argument.** If the arguments name a route (`brainstorm`, `spec`, `plan`), take it.
2. **Pipeline artifact given.** Handed an existing crank artifact (in the arguments or conversation), route to the **next** phase: a brainstorm brief → `spec`; a spec → `plan`; a plan → recommend `/crank-execute`. Classify it by **content and structure**, never just its filename — a brief sketches approach and shape; a spec carries acceptance criteria; a plan carries ordered, committable tasks. Resolve the handed-in path per [ARTIFACT-HOME.md](ARTIFACT-HOME.md), read here.
3. **Infer from the ask.** Judge how settled the work is against the "Right when" column, then **announce and go**: state the route and a one-line rationale ("This is a formed bug with a known cause — starting at **plan**"), then load and run the phase file at once. No confirmation stop: the phase opens with its own agenda, so the first exchange corrects a misroute.
4. **Torn between two routes.** Only when two routes are *genuinely* arguable — a formed idea touching unfamiliar architecture, a "small" ask hiding an open product question — ask one question naming both routes, a one-line case for each, your recommendation first.
5. **Nothing to route.** Invoked bare with no usable conversation context: ask what the user wants to work on, then triage the answer from rule 1 and against the sibling entry points named in the Goal.

## Phase gates

- **Load one phase at a time.** Read a phase file only when routing into it; the reference docs and templates beside it load when that phase file says, never at triage, except the artifact-home read in triage rule 2.
- **The adversarial review fans out, then merges.** Where a phase's flow has a review, the phase names its reviewers' lenses or shards and their tiers, resolved per [SUBAGENT-TIERS.md](SUBAGENT-TIERS.md).
  - Spawn the three reviewers in one wave, each passed the phase's review brief verbatim with the step's artifact paths, its lens or shard, and its findings path substituted in.
  - Once all three return, spawn one heavy subagent passed [MERGE-BRIEF.md](MERGE-BRIEF.md) verbatim, with the same paths, the artifact's absolute path as `<artifact-path>`, the phase's review brief's absolute path as `<brief-path>`, the three findings paths as `<findings-paths>`, and the phase's findings file and edit script as `<findings-file>` and `<edits-script>`.
  - A plan review of a plan with one stage or no Stages table instead spawns one heavy subagent with the plan brief alone, its **Shard.** paragraph dropped. That reviewer lands its own edits.

  Completion criterion: the merger's or the single reviewer's edits are in the artifact file.
- **Read back after the review.** Each phase writes its artifact, runs its adversarial review where its flow has one, then reads the artifact back per [READBACK.md](READBACK.md), which fixes what the one readback message shows, how feedback lands, and when the readback is done.
- **Hand off the same way in every phase.** Once the readback is done, state the filing without asking: one line saying the artifact stays at its `.crank/` path, with the path, then the step's **Next:** line. Close with one prose sentence, not a numbered question, noting the artifact can instead be copied elsewhere, printed inline, or deleted on request, then stop.
- **Advancing is the user's call.** Load the next phase file only on an explicit "continue".
- **Continuing is also a context call.** "Continue" carries this conversation's reasoning verbatim into the next phase, so recommend it while this session has run at most one phase and has not been compacted. Once a second phase would follow a compaction, recommend the **Next:** line's fresh-session command instead: each artifact is self-contained, and `.crank/<slug>/grounding.md` is an optional cache, read when present, that no artifact depends on.
