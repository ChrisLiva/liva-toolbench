---
name: crank-lite
description: Front door to the crank-lite pipeline — routes the ask to brainstorm, spec, or plan and runs that phase.
argument-hint: "[brainstorm|spec|plan] [idea, topic, or artifact path]"
disable-model-invocation: true
---

# Crank Lite

Route the user's ask to the right phase: **brainstorm → spec → plan**, then run that phase. Load **only** the phase file you route to:

| Route | Phase file | Right when |
| --- | --- | --- |
| `brainstorm` | [BRAINSTORM.md](BRAINSTORM.md) | The idea is raw — approach, shape, or product direction still open. |
| `spec` | [SPEC.md](SPEC.md) | The idea is formed (or a brainstorm brief exists) and needs acceptance criteria and key technical decisions. |
| `plan` | [PLAN.md](PLAN.md) | Behavior and design are settled — a finished spec, or a well-understood change like a scoped bug fix — and only "how to build it" remains. |

Every phase interviews and reads back per [INTERVIEW.md](INTERVIEW.md); read it before the phase's first question.

When a plan is done, recommend the user run `/lite-execute` and stop.

## Triage

First rule that applies wins:

1. **Explicit route argument** (`brainstorm`, `spec`, `plan`): take it.
2. **Pipeline artifact given**: resolve the handed-in path per [ARTIFACT-HOME.md](ARTIFACT-HOME.md), then route to the *next* phase, classifying by content, not filename:
   - approach and shape sketched (a brainstorm brief) → `spec`;
   - acceptance criteria (a spec) → `plan`;
   - ordered, committable tasks (a plan) → recommend `/lite-execute`.
3. **Infer from the ask**: judge how settled the work is (the "Right when" column). When two routes are genuinely arguable, and only then, ask the user one question naming both candidates, your recommendation first. Otherwise announce the best-fitting route with a one-line rationale and immediately run it.
4. **Nothing to route**: ask what the user wants to work on, then triage that answer from rule 1.

## Phase end

Every phase ends the same way, in this order:

1. **Write the artifact** when the interview's frontier is empty (the plan phase then reviews it per [PLAN.md](PLAN.md) → Review). Read [ARTIFACT-HOME.md](ARTIFACT-HOME.md) before writing when this is the effort's first artifact (it fixes the slug), when `.crank/<slug>/` already holds a different effort, or when you are outside a git repo; a later artifact of the same effort writes straight into its existing `.crank/<slug>/` directory. Either way, create `.crank/` if it is missing, with a `.gitignore` containing `*`, and tell the user the path once.
2. **Read it back** per [READBACK.md](READBACK.md).
3. **Offer to continue** once the readback is done. The hand-off is prose: the phase file's next-step line, then a single trailing sentence noting the artifact can be copied elsewhere, printed inline, or deleted on request. Continuing keeps this conversation as the next phase's primary source, so recommend it while the interview is still fully in context; after a long or compacted session, recommend a fresh session invoked with the artifact instead.
4. **Stop.** Load the next phase file only on an explicit "continue".
