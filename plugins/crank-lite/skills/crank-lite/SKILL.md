---
name: crank-lite
description: Front door to the crank-lite pipeline — routes the ask to the right phase and runs it. Phases: brainstorm (explore a raw idea at design altitude), spec (turn an idea or brainstorm into a PRD plus technical spec), plan (turn a spec or formed idea into ordered tasks, boundaries, and verification). Use when the user wants to brainstorm or explore an idea, spec out what's been discussed, plan how to build something, or crank on an idea, feature, or bug.
argument-hint: "[brainstorm|spec|plan] [idea, topic, or artifact path]"
---

# Crank Lite

Route the user's ask to the right phase — **brainstorm → spec → plan** — then run that phase. Each phase lives in its own file in this directory; load **only** the phase you route to:

| Route | Phase file | Right when |
| --- | --- | --- |
| `brainstorm` | [BRAINSTORM.md](BRAINSTORM.md) | The idea is raw — approach, shape, or product direction still open. |
| `spec` | [SPEC.md](SPEC.md) | The idea is formed (or a brainstorm brief exists) and needs acceptance criteria and key technical decisions. |
| `plan` | [PLAN.md](PLAN.md) | Behavior and design are settled — a finished spec, or a well-understood change like a scoped bug fix — and only "how to build it" remains. |

Execution is not a route: when a plan is done, recommend the `lite-execute` skill and stop.

## Triage

First rule that applies wins:

1. **Explicit route argument** (`brainstorm`, `spec`, `plan`) — take it, no second-guessing.
2. **Pipeline artifact given** — route to the *next* phase: a brainstorm brief → `spec`; a spec → `plan`. Classify by content and structure, not filename. A finished plan → recommend `lite-execute`.
3. **Infer from the ask** — judge how settled the work is (the "Right when" column), then announce the route with a one-line rationale and immediately run it. No confirmation stop; a misroute surfaces in the phase's first question.
4. **Torn between two routes** — only when genuinely arguable, ask the user one question naming both candidates, your recommendation first.
5. **Nothing to route** — ask what the user wants to work on, then triage that answer from rule 1.

## Phase gates

Load one phase file at a time. Each phase ends by offering to continue to the next; load the next phase file only on an explicit "continue" — never auto-advance. A user returning later with a phase's artifact is triage rule 2.
