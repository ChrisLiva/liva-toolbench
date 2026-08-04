---
name: crank
description: Front door to the crank design pipeline — routes the ask to brainstorm, spec, or plan and runs that phase.
argument-hint: "[brainstorm|spec|plan] [idea, topic, or artifact path]"
disable-model-invocation: true
---

# Crank

## Goal

Route the user's ask to the right phase of the design pipeline — **brainstorm → spec → plan** — then run that phase. Each phase's full discipline lives in its own file in this directory:

| Route | Phase file | Produces | Right when |
| --- | --- | --- | --- |
| `brainstorm` | [BRAINSTORM.md](BRAINSTORM.md) | High-level design brief | The idea is raw — the approach, shape, or product direction is still open. |
| `spec` | [SPEC.md](SPEC.md) | PRD + technical spec | The idea is formed (or a brainstorm brief exists) and needs acceptance criteria and technical decisions. |
| `plan` | [PLAN.md](PLAN.md) | Ordered, committable task plan | The behavior and design are already settled — a finished spec, or a well-understood change like a scoped bug fix — and only "how to build it" remains. |

Execution is deliberately **not** a route: when a plan is done, recommend the user run `/crank-execute` and stop. Sharpening an existing artifact without advancing it is `/crank-refine`'s job, not this one's.

## Triage

Pick the route in this order — first rule that applies wins:

1. **Explicit route argument.** If the arguments name a route (`brainstorm`, `spec`, `plan`), take it.
2. **Pipeline artifact given.** If the arguments (or conversation) hand you an existing crank artifact, route to the **next** phase: a brainstorm brief → `spec`; a spec → `plan`. Classify the artifact by its **content and structure**, never just its filename — a brief sketches approach and shape; a spec carries acceptance criteria; a plan carries ordered, committable tasks. (A plan needs no route here — recommend `/crank-execute`.)
3. **Infer from the ask.** Judge how settled the work already is (see the "Right when" column above). Then **announce and go**: state the route and a one-line rationale — e.g. "This is a formed bug with a known cause — starting at **plan**" — and immediately load the phase file and run its flow. No confirmation stop: the phase opens with its own agenda/grilling, so a misroute surfaces and is corrected within the first exchange.
4. **Torn between two routes.** Only when two routes are *genuinely* arguable — a formed idea touching unfamiliar architecture, a "small" ask hiding an open product question — ask the user one question, naming both candidate routes with a one-line case each and your recommendation first. An obvious route is a convention: proceed and state it. A genuinely arguable one is a decision: the user's.
5. **Nothing to route.** Invoked bare with no usable conversation context: ask what the user wants to work on, then triage that answer from rule 1.

## Phase gates

- **Load one phase at a time.** Read a phase file only when routing into it; the shared reference docs and templates beside it load when that phase file says, never at triage.
- **Advancing is the user's call.** Each phase ends with a hand-off that offers "continue to the next phase" among other options. Load the next phase file only on an explicit "continue" — never auto-advance because momentum feels natural. Continuing stays cheap (same conversation, artifact path already known); the authority stays with the user.
