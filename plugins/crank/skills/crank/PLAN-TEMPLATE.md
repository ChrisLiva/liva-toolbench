# Plan markdown skeleton

Replace every angle-bracket placeholder before review.

```markdown
# <Plan title>

Spec: <absolute path, when one exists>
Grounding: <absolute path to .crank/<slug>/grounding.md, when that file holds entries>
Goal: <one sentence>
Architecture: <2-3 sentences>
Tech stack: <pinned versions>
Gates: <exact test / lint / typecheck / build commands, each proven to run>
Base: <the HEAD SHA grounding read>

## Global Constraints

- <Exact project-wide rule copied from the spec.>

## Updates since spec

- <Drift found while grounding, or omit section.>

## Refactor scope

- `<path>` — <intended reshape copied from the spec.>

## File structure

| path | action | responsibility |
|---|---|---|
| `<path>` | create/modify/delete | <one clear responsibility> |

## Tasks

### Task 1 — <independently committable outcome>

Files:
- `<path>` — <create/modify/delete, responsibility>

Interfaces:
- Consumes: `<signature or contract>`
- Produces: `<signature or contract>`

Check: <test-first | lightest-check | probe>, model after `<anchor of the existing test or file grounding found>`
Stop if: <the assumption this task rests on that grounding could not prove, or omit>
Prototype: <the winning variant's path, or `in chat` with the winning block beneath, and what the user left out of the winner, or omit>

- [ ] Behavior 1: <what the code must do>. Oracle: `<exact input>` → `<exact expected output>`. Seam: <production seam the test drives>
      <pseudo-code or embedded code, only where PLAN.md's ladder calls for it>
- [ ] Behavior 2: <next behavior in tracer-bullet order — or a directive line for a mechanical change>
- [ ] Verify: `<exact command>` → <exact success reading; for a count, grep, or probe: base: <what it prints on the tree this task starts from, `read at task start`, or `Task <N>'s recorded reading`> → target: <what it must print>>

### Task 2 — <independently committable outcome>

<repeat every block above in full — the implementer sees only this task and tests only its Behavior lines: no line points at Task 1, and every requirement is a Behavior line>

## Stages

| stage | tasks | closes criteria | exit state |
|---|---|---|---|
| 1 | Task 1–Task <N> | <criteria proved at this gate, or `scaffolding` for a first stage that closes none> | <what works at the gate and what stage 2 adds> |

## Coverage

| criterion | task # | verify step that proves it | fails when |
|---|---|---|---|
| <acceptance criterion> | Task 1 | <behavior or verify line that proves it> | <the production line whose deletion or reversion turns that check red, one per site> |

## Smoke tests for the user

- <Human-only check, if needed.>

## Out of scope

- <Cut copied from the spec.>
```
