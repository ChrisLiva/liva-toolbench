# Subagent tiers

The crank skills delegate to subagents at two capability tiers — **standard** (bulk work) and **heavy** (work that rewards the strongest reasoning). The tiers describe *intent*, not fixed models; each skill's own Subagents section says which of its dispatches runs at which tier.

**Resolving a tier to a model:** resolve once per run and reuse the mapping at every dispatch. Read the user instructions already loaded this session — user- and project-level `CLAUDE.md` / `AGENTS.md`. A subagent model preference stated there is binding: heavy = their strongest-reasoning choice, standard = their bulk-work choice, even when it names a weaker model than a fallback below (Terra only means heavy review runs on Terra). With no such preference stated, use your harness's fallback:

- **Claude Code** — spawn via the `Agent` tool; fallback: standard → `model: sonnet`, heavy → `model: opus`. Inheriting the session model is fine where it already sits at the tier you need; report it by name, never as `inherited`. A typed read-only agent (e.g. `Explore`) counts as standard; set `model` explicitly for anything heavy.
- **Codex** — spawn a subagent; fallback: standard → `gpt-5.6-terra` at `medium` effort (Terra-Medium), heavy → `gpt-5.6-sol` at `high` effort (Sol-High).
- **Cursor** — spawn a subagent; fallback: standard → `cursor-composer-2-5`, heavy → `gpt-5.6-sol-high` (Sol-High).

## Dispatch or main thread

A one-symbol lookup in a known file you do yourself; anything wider — a pattern sweep, a version check, a library comparison, an off-plan investigation — you dispatch. Dispatch keeps your synthesis window clean and runs independent investigations in parallel; main-thread reading keeps the conversation's nuance but fills your window with source you'll never reread.
