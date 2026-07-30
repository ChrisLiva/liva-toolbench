# Spec markdown skeleton

Use this as the starting shape for the temp-file spec. Keep only sections that earn their place for the topic, replace every angle-bracket placeholder before review, and obey the Deliverables rules in `SKILL.md`.

```markdown
# <Spec title>

## Problem

<What the user is trying to solve, in their words.>

## Solution

<The proposed change in user-facing terms.>

## User stories

- As an <actor>, I want <feature>, so that <benefit>.

## Acceptance criteria

1. <Falsifiable behavior, state transition, interaction, validation, or edge case.>

## Technical decisions

- **<Decision>** — <chosen option>. Why: <one sentence>. Gives up: <trade-off, when relevant>. Prior art: `<path>:<line>`.

## Testing approach

- <Behavior seam to test, using the same path real users or callers hit. Prior art: `<path>:<line>`.>

## Refactor scope

- `<path>` — <boundary intentionally open to reshape, and existing tests superseded.>

## Out of scope

- <Discussed cut, with the reason it stays out.>
```
