# Subagent tiers

The crank skills delegate to subagents at two capability tiers — **standard** (bulk work: codebase grounding, exploration, per-task review) and **heavy** (work that rewards the strongest reasoning: drafting, adversarial review, final cross-task review). Where a skill body says to spawn a standard or heavy subagent, resolve the tier to the harness you are running in:

- **Claude Code** — spawn via the `Agent` tool and **always set `model` explicitly on every spawn**: standard → `model: sonnet`, heavy → `model: opus`. Never omit `model` — an unset `model` makes the subagent inherit the orchestrator's model (heavy/opus), silently breaking the standard tier and spending heavy-tier budget on bulk work. (A *typed* agent dispatched for its own role — e.g. `Explore` for read-only grounding — carries its own tier and is the one exception.)
- **Codex** — spawn a subagent and set its reasoning effort per tier on `gpt-5.6-terra`: standard → `medium` (Terra-Medium), heavy → `high` (Terra-High). Set per spawn; nothing else to configure.
- **Cursor** — spawn a subagent and set its `model` per tier: standard → `cursor-composer-2-5`, heavy → `gpt-5.6-terra-high` (Terra-High). Set per spawn; nothing else to configure.

## Dispatch or main thread

Shared default for the exploration and research subagents the crank skills spawn:

<tradeoff>
**Default:** a one-symbol lookup in a known file you do yourself; anything wider — a pattern sweep, a library comparison, a version check, prior-art research — you dispatch. Dispatch keeps your synthesis window clean and runs independent investigations in parallel; main-thread reading keeps the conversation's nuance but fills your window with source you'll never reread.
</tradeoff>
