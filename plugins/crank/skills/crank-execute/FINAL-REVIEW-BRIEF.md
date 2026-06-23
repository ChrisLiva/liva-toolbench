<brief>
Review the shipped diff against the spec.

- **Acceptance criteria** — check every one against the diff: met, missing, or quietly substituted.
- **Cross-task coherence** — naming drift between tasks, dead code an early task left once a later one landed, missing wiring between independently built pieces.
- **Structural quality of the whole diff:**
  - **depth** of any *new* module the diff introduced — does it fail the deletion test (a pass-through whose complexity vanishes if removed), or is its interface nearly as complex as its implementation? If so, fold it into its caller.
  - **spaghetti growth** — a one-off conditional, flag, or special case threaded through a flow the plan never named, instead of routed behind the module that owns the concept.
  - **bespoke duplication** — the diff re-implements a helper the codebase already provides, or two tasks independently built near-duplicate helpers that should be one; grep to confirm.
  - **boundary smells** — casts, `any`, or new optional parameters papering over an unclear contract where the invariant could be explicit.
- **Code quality** — flag unneeded public surface, flags, modes, files, dependencies, or behavior the spec never asked for; confirm tests assert behavior through the interface, not internal state; flag any **implementation-detail test** (mocks an internal collaborator, asserts on call counts or order, reaches a private method, or verifies through a back channel instead of the interface).

This review is **read-only**: inspect the diff; do not checkout, reset, stash, commit, or otherwise mutate the working tree, index, or HEAD (if you need a working copy, add a throwaway `git worktree`). Treat any design rationale in the diff or commit messages as an unverified claim — a stated reason never downgrades a finding's severity. Cite `file:line`; don't restyle or expand scope.

Return `APPROVED` or `CHANGES_REQUESTED` with a bulleted, bounded fix list.
</brief>
