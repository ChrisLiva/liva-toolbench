---
name: crank-lite
description: Front door to the crank-lite pipeline — routes the ask to brainstorm, spec, or plan and runs that phase.
argument-hint: "[brainstorm|spec|plan] [idea, topic, or artifact path] [--pilot]"
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

Wherever they sit in the arguments, `--pilot` and `--no-pilot` are mode words: set them aside before applying the rules above, never reading one as a route or as part of the idea. **Interactive mode** is on when the invocation carried `--pilot`, or a loaded instruction file asks for interactive mode, and the invocation carried no `--no-pilot`. In interactive mode, read [PILOT.md](PILOT.md) when the phase reaches its first question round, readback, or prototype review.

## Phase end

Every phase ends in this order:

1. **Write the artifact** when the interview's frontier is empty (the plan phase then reviews it per [PLAN.md](PLAN.md) → Review). Read [ARTIFACT-HOME.md](ARTIFACT-HOME.md) first when this is the effort's first artifact, when `.crank/<slug>/` already holds a different effort, or outside a git repo; a later artifact writes straight into its existing `.crank/<slug>/`. Either way, create a missing `.crank/` with a `.gitignore` containing `*`, and tell the user the path once.
2. **Read it back** per [READBACK.md](READBACK.md). In interactive mode, send the readback to the page per [PILOT.md](PILOT.md).
3. **Offer to continue** once the readback is done: one line naming each glossary and ADR file the phase wrote, uncommitted in the working tree, when it wrote any, then the phase file's next-step line, then one sentence saying the artifact can be copied elsewhere, printed inline, or deleted on request. After a long or compacted session, recommend a fresh session invoked with the artifact. In interactive mode, finish the hand-off per [PILOT.md](PILOT.md) → Hand-off.
4. **Stop.** Load the next phase file only on an explicit "continue". A phase loaded on "continue" keeps the interactive mode the phase before it ran in.
