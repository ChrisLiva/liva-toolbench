# Subagent tiers

The crank skills delegate to subagents at two capability tiers — **standard** (bulk work: codebase grounding, exploration, per-task review) and **heavy** (work that rewards the strongest reasoning: drafting, adversarial review, final cross-task review). The tiers describe *intent*, not fixed models.

**Resolving a tier to a model:** check the user's own configuration first — global or project instructions (e.g. `~/.claude/CLAUDE.md`, a user-level `AGENTS.md`, harness settings, machine-level agent defaults). A stated subagent model preference there is binding: map the tiers onto it — heavy = their strongest-reasoning choice, standard = their bulk-work choice — and it wins even when it names a weaker model than a fallback below. A tier is never a license to escalate past the user's stated choice: if they say Terra only, heavy review runs on Terra. Read the harness fallbacks below only when no such preference exists:

- **Claude Code** — spawn via the `Agent` tool; fallback: standard → `model: sonnet`, heavy → `model: opus`. Omitting `model` is fine when inheriting the session model matches the user's preference. (A *typed* agent dispatched for its own role — e.g. `Explore` for read-only grounding — carries its own tier either way.)
- **Codex** — spawn a subagent; fallback: standard → `gpt-5.6-terra` at `medium` effort (Terra-Medium), heavy → `gpt-5.6-sol` at `high` effort (Sol-High).
- **Cursor** — spawn a subagent; fallback: standard → `cursor-composer-2-5`, heavy → `gpt-5.6-sol-high` (Sol-High).

## Dispatch or main thread

Shared default for the exploration and research subagents the crank skills spawn:

<tradeoff>
**Default:** a one-symbol lookup in a known file you do yourself; anything wider — a pattern sweep, a library comparison, a version check, prior-art research — you dispatch. Dispatch keeps your synthesis window clean and runs independent investigations in parallel; main-thread reading keeps the conversation's nuance but fills your window with source you'll never reread.
</tradeoff>
