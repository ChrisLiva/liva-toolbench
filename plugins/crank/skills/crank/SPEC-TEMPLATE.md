# Spec markdown skeleton

Use this as the starting shape for the spec at its `.crank/` path (see ARTIFACT-HOME.md). Keep only sections that earn their place for the topic, replace every angle-bracket placeholder before review, and obey the Deliverables rules in `SPEC.md`.

```markdown
# <Spec title>

Grounding: <absolute path to .crank/<slug>/grounding.md, when that file holds entries>

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
- **Prototype:** <winner, what the user took from the other variants, what the user left out of the winner, `<winning variant's path>`, the surface the mock stood in for>, or `declined`, or `no verdict`. A mock the brainstorm brief's **Key decisions** recorded carries here with its path, beside the decision it settled. Omit when no offer fired and the brief recorded no mock.

## Testing approach

- <test, seam, prior art>
- <oracle, when checkable logic is in play>

## Refactor scope

- `<path>` — <boundary intentionally open to reshape, and existing tests superseded.>

## Out of scope

- <Discussed cut, with the reason it stays out.>
```
