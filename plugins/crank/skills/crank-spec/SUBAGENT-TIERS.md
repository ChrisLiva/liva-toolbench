# Subagent tiers

The crank skills delegate to subagents at two capability tiers — **standard** (bulk work: codebase grounding, exploration, per-task review) and **heavy** (work that rewards the strongest reasoning: drafting, adversarial review, final cross-task review). Where a skill body says to spawn a standard or heavy subagent, resolve the tier to the harness you are running in:

- **Claude Code** — spawn via the `Agent` tool and set `model` per tier: standard → `model: sonnet`, heavy → `model: opus`. Set per spawn; nothing else to configure.
- **Codex** — spawn a subagent and set its reasoning effort per tier on `gpt-5.5`: standard → `medium`, heavy → `high`. Set per spawn; nothing else to configure.
- **Cursor** — spawn a subagent and set its `model` per tier: standard → `cursor-composer-2-5`, heavy → `gpt-5.5-high`. Set per spawn; nothing else to configure.
