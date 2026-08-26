# Spec markdown skeleton

Use this as the starting shape for the spec at its `.crank/` path (see ARTIFACT-HOME.md). Keep only sections that earn their place for the topic, replace every angle-bracket placeholder before review, and obey the Deliverables rules in `SPEC.md`.

```markdown
# <Spec title>

## Problem

<one paragraph>

## Solution

<one paragraph>

## User stories

- As an <actor>, I want <feature>, so that <benefit>.

## Acceptance criteria

1. <criterion>

## Technical decisions

- **<Decision>** — <chosen option>. Why: <one sentence>. Gives up: <trade-off, when relevant>. Prior art: `<path>:<line>`.
- **Surfaces** — <layer>: `<path>:<line>` — one line per layer touched, or "no analogous surface" where grounding found none.

## Testing approach

- <test, seam, prior art>
- <oracle, when checkable logic is in play>

## Refactor scope

- `<path>` — <boundary intentionally open to reshape, and existing tests superseded.>

## Out of scope

- <Discussed cut, with the reason it stays out.>
```
