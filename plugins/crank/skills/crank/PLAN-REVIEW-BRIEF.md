# Adversarial plan review brief

Pass this brief verbatim to a heavy subagent, substituting the plan path and spec path. If the spec exists only in the conversation, drop the spec-path sentence and paste the spec's behavior list or acceptance criteria into the brief instead.

<brief>
Read the plan at `<plan-path>` and the spec at `<spec-path>`. You will execute this plan tomorrow with no further design conversation.

Flag every instance of:

- **non-runnable steps** — path / command / expected / instruction not concrete enough to type code from.
- **coverage holes** — walk the spec yourself (every acceptance criterion and every behavior the body describes: interaction, keybinding, alias, edge case, state transition, validation) and check the plan's Coverage table against your walk; flag criteria missing from the table, rows whose verify step doesn't actually exercise the behavior, and empty verify cells with no stated reason.
- **name / type / path inconsistencies** — across tasks or against the codebase.
- **placeholder language** — `TODO` / `TBD` / `similar to Task N` / "add appropriate handling" / vague instructional prose / undefined symbols.
- **dead-seam verify steps** — a test that drives a node, handler, or endpoint the production code never wires up, so it would pass even if the feature were absent.
- **horizontal slicing** — a multi-behavior task whose steps list two or more tests before any implementation, instead of interleaving `test → impl` per behavior; reorder into vertical slices.
- **implementation-detail tests** — an embedded test that mocks an internal collaborator, asserts on call counts or order, reaches a private method, or verifies through a back channel instead of the interface; rewrite it to drive the seam.
- **spaghetti growth** — a step threads a one-off conditional, flag, or special case through a file or flow the spec never named, instead of routing it behind the module that owns the concept.
- **bespoke duplication** — embedded code re-implements a helper the codebase already provides; grep to confirm, and rewrite the step to call the canonical one.
- **needless dependency** — a step adds or imports a new third-party dependency where the stdlib, a native platform feature, an already-installed dependency, or a few lines would do; flag it, name the lighter route, and treat any new dependency the spec's Tech stack didn't pin as an **Updates since spec** item, not a silent import.
- **scattered guards** — two or more tasks each add the same guard, validation, or check at a different call site where one shared function at the root would be shallower and cover every caller (including the sibling callers no task names); flag it as a candidate to centralize and route the callers through it. Not a mandate — a caller that legitimately needs its own guard stays put; flag the duplication, name the shared home, leave the call.
- **boundary smells** — embedded code uses casts, `any`, or new optional parameters to paper over an unclear contract.
- **interface drift** — a task's `Consumes` names a signature no earlier task `Produces` or that contradicts the codebase, or a `Produces` no later task and no acceptance criterion ever uses.
- **Global Constraints violations** — a task contradicts a rule in the plan's Global Constraints, or a Global Constraints value isn't copied verbatim from the spec.
- **order problems** — a task imports what no earlier task built.

None of the flags above licenses cutting a trust-boundary validation, data-loss or error path, security check, or accessibility affordance — those are required behavior, not surface or duplication; never recommend folding one away, and where the plan drops one the spec relies on, flag the hole.

Don't re-open spec-level decisions. Then edit **the plan file at `<plan-path>`** in place to fix every item you flagged — that plan file is the only artifact you may modify. You read the spec and grep the codebase **only to inform your plan edits**: never edit the spec, and never touch any production, test, or source file. A flagged duplication, inconsistency, or dead seam gets *rewritten in the plan step that describes it* — never fixed in the code itself. End your reply with a one-line summary of what changed.
</brief>
