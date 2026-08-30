---
name: crank
description: Front door to the crank design pipeline — routes the ask to brainstorm, spec, or plan and runs that phase.
argument-hint: "[brainstorm|spec|plan] [idea, topic, or artifact path]"
disable-model-invocation: true
---

# Crank

## Goal

Route the user's ask to the right phase of the design pipeline — **brainstorm → spec → plan** — then run that phase. Each phase's full discipline lives in its own file in this directory:

| Route | Phase file | Right when |
| --- | --- | --- |
| `brainstorm` | [BRAINSTORM.md](BRAINSTORM.md) | The idea is raw — the approach, shape, or product direction is still open. |
| `spec` | [SPEC.md](SPEC.md) | The idea is formed (or a brainstorm brief exists) and needs acceptance criteria and technical decisions. |
| `plan` | [PLAN.md](PLAN.md) | The behavior and design are already settled — a finished spec, or a well-understood change like a scoped bug fix — and only "how to build it" remains. |

Execution is deliberately **not** a route: when a plan is done, recommend the user run `/crank-execute` and stop. Sharpening an existing artifact without advancing it is `/crank-refine`'s job, not this one's.

Three asks enter the pipeline elsewhere: a codebase-wide hunt for shallow modules or leaking seams is `/crank-deepen` (it hands back a brainstorm brief); judging changes that already exist is `/crank-review`, and a test suite is `/crank-test-prune`.

## Triage

Pick the route in this order — first rule that applies wins:

1. **Explicit route argument.** If the arguments name a route (`brainstorm`, `spec`, `plan`), take it.
2. **Pipeline artifact given.** If the arguments (or conversation) hand you an existing crank artifact, route to the **next** phase: a brainstorm brief → `spec`; a spec → `plan`. Classify the artifact by its **content and structure**, never just its filename — a brief sketches approach and shape; a spec carries acceptance criteria; a plan carries ordered, committable tasks. (A plan needs no route here — recommend `/crank-execute`.) Resolve the handed-in path per [ARTIFACT-HOME.md](ARTIFACT-HOME.md), read here: a legacy flat artifact moves to its per-plan home before the phase runs, and you state the new path.
3. **Infer from the ask.** Judge how settled the work already is (see the "Right when" column above). Then **announce and go**: state the route and a one-line rationale — e.g. "This is a formed bug with a known cause — starting at **plan**" — and immediately load the phase file and run its flow. No confirmation stop: the phase opens with its own agenda/grilling, so a misroute surfaces and is corrected within the first exchange.
4. **Torn between two routes.** Only when two routes are *genuinely* arguable — a formed idea touching unfamiliar architecture, a "small" ask hiding an open product question — ask the user one question, naming both candidate routes with a one-line case each and your recommendation first.
5. **Nothing to route.** Invoked bare with no usable conversation context: ask what the user wants to work on, then triage that answer from rule 1 — and against the three sibling entry points named in the Goal, which rules 1–4 don't cover.

## Phase gates

- **Load one phase at a time.** Read a phase file only when routing into it; the shared reference docs and templates beside it load when that phase file says, never at triage — the one exception is the artifact-home read triage rule 2 names.
- **Track the flow live.** On entering a phase, create a task for each step in its Flow and mark each complete as you finish it, so the user can watch progress.
- **Read back before drafting.** Where a phase's flow has a read-back step, walk the material that step names, per [READBACK.md](READBACK.md) — which also fixes when it opens. Completion criterion: everything READBACK.md selects has had its actual content read back and user-approved; objections resolved now, none carried into the draft.
- **The adversarial review is one heavy dispatch.** Where a phase's flow has one: read that phase's review brief, spawn one heavy subagent resolved per [SUBAGENT-TIERS.md](SUBAGENT-TIERS.md), pass it the brief verbatim with the artifact paths the step names substituted in, and quote the reviewer's summary line back to the user. Completion criterion: the reviewer's edits are in the artifact file and its one-line summary is quoted back to the user.
- **Hand off the same way in every phase.** Filing is already decided, so state it rather than asking how to file the artifact: the artifact stays at its `.crank/` path (one line, with the path), then the step's **Next:** line. Close with a single trailing sentence noting the artifact can instead be copied elsewhere, printed inline, or deleted on request — prose, not a numbered question — then stop.
- **Advancing is the user's call.** Load the next phase file only on an explicit "continue" — never auto-advance because momentum feels natural.
- **Continuing is also a context call.** "Continue" keeps this conversation as the next phase's primary source — the reasoning travels verbatim, not as a summary — so recommend it while this session has run at most one phase and has not been compacted. Once a second phase would follow a compaction, recommend the fresh-session command on the step's **Next:** line instead: each artifact is self-contained, so a new session invoked with the artifact path loses nothing the file doesn't carry — `.crank/<slug>/grounding.md` is an optional cache beside the artifacts, read when present, that no artifact ever depends on.
