---
name: crank-lite
description: Front door to the crank-lite pipeline — routes the ask to brainstorm, spec, or plan and runs that phase.
argument-hint: "[brainstorm|spec|plan] [idea, topic, or artifact path]"
disable-model-invocation: true
---

# Crank Lite

Route the user's ask to the right phase — **brainstorm → spec → plan** — then run that phase. Each phase lives in its own file in this directory; load **only** the phase you route to:

| Route | Phase file | Right when |
| --- | --- | --- |
| `brainstorm` | [BRAINSTORM.md](BRAINSTORM.md) | The idea is raw — approach, shape, or product direction still open. |
| `spec` | [SPEC.md](SPEC.md) | The idea is formed (or a brainstorm brief exists) and needs acceptance criteria and key technical decisions. |
| `plan` | [PLAN.md](PLAN.md) | Behavior and design are settled — a finished spec, or a well-understood change like a scoped bug fix — and only "how to build it" remains. |

Execution is not a route: when a plan is done, recommend the user run `/lite-execute` and stop.

## Triage

First rule that applies wins:

1. **Explicit route argument** (`brainstorm`, `spec`, `plan`) — take it, no second-guessing.
2. **Pipeline artifact given** — route to the *next* phase: a brainstorm brief → `spec`; a spec → `plan`. Classify by content and structure, not filename. A finished plan → recommend `/lite-execute`.
3. **Infer from the ask** — judge how settled the work is (the "Right when" column), then announce the route with a one-line rationale and immediately run it. No confirmation stop; a misroute surfaces in the phase's first question.
4. **Torn between two routes** — only when genuinely arguable, ask the user one question naming both candidates, your recommendation first.
5. **Nothing to route** — ask what the user wants to work on, then triage that answer from rule 1.

## Writing the artifact

Every phase ends the same way: when every readback section stands approved, write the phase's artifact to its `.crank/<slug>/` path per [ARTIFACT-HOME.md](ARTIFACT-HOME.md), read that file before writing, and stop. Keep the artifact light: the phase file lists the sections, and each one earns its place or is left out.

## Phase gates

Each phase ends by offering to continue to the next; load the next phase file only on an explicit "continue" — never auto-advance. The hand-off is the phase file's next-step line, then a single trailing sentence noting the artifact can be copied elsewhere, printed inline, or deleted on request: prose, not a numbered question.

Continuing keeps this conversation as the next phase's primary source, so recommend it while enough context window remains for the next phase to fit; deep in a long session, recommend a fresh session invoked with the artifact instead.
