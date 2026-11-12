---
name: crank-lite
description: Front door to the crank-lite pipeline — routes the ask to brainstorm, spec, or plan and runs that phase.
argument-hint: "[brainstorm|spec|plan] [idea, topic, or artifact path]"
disable-model-invocation: true
---

# Crank Lite

Route the user's ask to the right phase: **brainstorm → spec → plan**, then run that phase. Load the phase file you route to; the other two load only on an explicit "continue" (Phase end):

| Route | Phase file | Right when |
| --- | --- | --- |
| `brainstorm` | [BRAINSTORM.md](BRAINSTORM.md) | The idea is raw: approach, shape, or product direction still open. |
| `spec` | [SPEC.md](SPEC.md) | The idea is formed and needs acceptance criteria and key technical decisions. |
| `plan` | [PLAN.md](PLAN.md) | Behavior and design are settled, in a finished spec or a well-understood change like a scoped bug fix, and only "how to build it" remains. |

Every phase interviews per [INTERVIEW.md](INTERVIEW.md); read it before the phase's first question.

When a plan is done, recommend `/lite-execute` and stop.

## Triage

First rule that applies wins:

1. **Explicit route argument**: take it.
2. **Pipeline artifact given**: resolve the path per [ARTIFACT-HOME.md](ARTIFACT-HOME.md), then route to the *next* phase, classifying by content, not filename:
   - a brainstorm brief → `spec`;
   - acceptance criteria → `plan`;
   - ordered, committable tasks → recommend `/lite-execute`.
3. **Infer from the ask**: judge how settled the work is. Only when two routes are genuinely arguable, ask one question naming both, your recommendation first. Otherwise announce the best-fitting route in one line and run it.
4. **Nothing to route**: ask what the user wants to work on, then triage that answer.

## Phase end

Every phase ends in this order:

1. **Write the artifact** when the interview's frontier is empty (the plan phase then reviews it per [PLAN.md](PLAN.md) → Review). Read [ARTIFACT-HOME.md](ARTIFACT-HOME.md) first when this is the effort's first artifact, when `.crank/<slug>/` already holds a different effort, or outside a git repo; a later artifact writes straight into its existing `.crank/<slug>/`. Either way, create a missing `.crank/` with a `.gitignore` containing `*`, and tell the user the path once.
2. **Read it back** per [READBACK.md](READBACK.md).
3. **Offer to continue** once the readback is done: the phase file's next-step line, then one sentence saying the artifact can be copied elsewhere, printed inline, or deleted on request. After a long or compacted session, recommend a fresh session invoked with the artifact.
4. **Stop.** Load the next phase file only on an explicit "continue".
