---
name: lite-execute
description: "Execute a PRD, spec, or implementation plan: implement, verify, review, and commit the work."
disable-model-invocation: true
---

Implement the work described in the plan (or PRD/spec) the user provides.

Run typechecking regularly, single test files regularly, and the full test suite once at the end.

If the plan is large, or touches many files, spawn Sonnet/GPT-5.5-Medium subagents to implement tasks sequentially or in parallel. Provide the subagents brief, targeted instructions.

Once done implementing the entire plan, spawn an Opus/GPT-5.5-High subagent to adversarially review your work against the original plan. Address confirmed findings before committing.

Before committing, inspect the worktree and stage only the files changed for this task. If unrelated user changes are present, leave them untouched and ask before committing only when you cannot separate your changes safely.

Once you've finished implementation and review, record a concise retro to a new temp file (e.g. `${TMPDIR:-/tmp}/lite-retro-<slug>.md`) and stop. Keep the artifact light: include what changed, verification run, review outcome, deviations from the plan, open items, and further suggestions when those sections earn their place. Tell the user the commit SHA and temp file path.
