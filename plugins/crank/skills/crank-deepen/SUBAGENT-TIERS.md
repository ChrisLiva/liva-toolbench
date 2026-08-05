# Subagent tiers

The crank skills delegate to subagents at two capability tiers — **standard** (bulk work: codebase grounding, exploration, per-task review) and **heavy** (work that rewards the strongest reasoning: drafting, adversarial review, final cross-task review). The tiers describe *intent*, not fixed models.

**Resolving a tier to a model:** the user's own configuration wins. If the user's global or project instructions (e.g. `~/.claude/CLAUDE.md`, harness settings, machine-level agent defaults) state subagent model preferences, follow those and map the tiers onto them — heavy = their strongest-reasoning choice, standard = their bulk-work choice. Only when no such preference exists, fall back to the harness defaults below:

- **Claude Code** — spawn via the `Agent` tool; fallback: standard → `model: sonnet`, heavy → `model: opus`. Omitting `model` is fine when inheriting the session model matches the user's preference. (A *typed* agent dispatched for its own role — e.g. `Explore` for read-only grounding — carries its own tier either way.)
- **Codex** — spawn a subagent; fallback: standard → `gpt-5.6-terra` at `medium` effort (Terra-Medium), heavy → `gpt-5.6-sol` at `high` effort (Sol-High).
- **Cursor** — spawn a subagent; fallback: standard → `cursor-composer-2-5`, heavy → `gpt-5.6-sol-high` (Sol-High).

## Dispatch or main thread

Shared default for the exploration and research subagents the crank skills spawn:

<tradeoff>
**Default:** a one-symbol lookup in a known file you do yourself; anything wider — a pattern sweep, a library comparison, a version check, prior-art research — you dispatch. Dispatch keeps your synthesis window clean and runs independent investigations in parallel; main-thread reading keeps the conversation's nuance but fills your window with source you'll never reread.
</tradeoff>
