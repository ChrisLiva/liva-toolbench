# Plan markdown skeleton

Use this as the starting shape for the temp-file plan. Keep only sections that earn their place for the change, replace every angle-bracket placeholder before review, and obey the Deliverables rules in `SKILL.md`.

```markdown
# <Plan title>

Spec: <absolute path, when one exists>
Goal: <one sentence>
Architecture: <2-3 sentences>
Tech stack: <pinned versions>

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

- [ ] Step 1: <failing behavior test or lightest-check setup>
- [ ] Step 2: <minimal implementation or mechanical change>
- [ ] Step 3: Verify <exact command/result>, seam: <production seam>
- [ ] Step 4: Commit: `<message>`

## Coverage

| criterion | task # | verify step that proves it |
|---|---|---|
| <acceptance criterion> | Task 1 | Step 3 |

## Smoke tests for the user

- <Human-only check, if needed.>

## Out of scope

- <Cut copied from the spec.>
```
