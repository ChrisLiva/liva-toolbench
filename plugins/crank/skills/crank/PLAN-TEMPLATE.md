# Plan markdown skeleton

Use this as the starting shape for the plan at its `.crank/` path (see ARTIFACT-HOME.md). Keep only sections that earn their place for the change, replace every angle-bracket placeholder before review, and obey the Deliverables rules in `PLAN.md`.

```markdown
# <Plan title>

Spec: <absolute path, when one exists>
Goal: <one sentence>
Architecture: <2-3 sentences>
Tech stack: <pinned versions>
Gates: <exact test / lint / typecheck / build commands, each proven to run>

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

Check: <test-first | lightest-check | probe>, model after `<path to the existing test or file grounding found>`
Stop if: <the assumption this task rests on that grounding could not prove, or omit>

- [ ] Behavior 1: <what the code must do>. Oracle: `<exact input>` → `<exact expected output>`. Seam: <production seam the test drives>
      <pseudo-code or embedded code, only where PLAN.md's ladder calls for it; embedded code names its evidence>
- [ ] Behavior 2: <next behavior in tracer-bullet order — or a directive line for a mechanical change>
- [ ] Verify: `<exact command>` → <exact success reading>

### Task 2 — <independently committable outcome>

<repeat every block above in full — the implementer sees only this task, so no line may point at Task 1>

## Coverage

| criterion | task # | verify step that proves it |
|---|---|---|
| <acceptance criterion> | Task 1 | <behavior or verify line that proves it> |

## Smoke tests for the user

- <Human-only check, if needed.>

## Out of scope

- <Cut copied from the spec.>
```
