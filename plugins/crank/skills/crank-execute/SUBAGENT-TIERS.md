# Subagent tiers

The crank skills delegate to subagents at two capability tiers: **standard** for bulk work and **heavy** for work that needs the strongest reasoning. A tier names *intent*, not a model; each skill's Subagents section assigns its dispatches to tiers.

Resolve each tier to a model once per run and reuse the mapping at every dispatch. The source of truth is a subagent model preference in the user instructions already loaded this session, from user- or project-level `CLAUDE.md` or `AGENTS.md`, and it is binding. Heavy maps to its strongest-reasoning choice and standard to its bulk-work choice, even when that names a weaker model than a fallback below: a user who says "Terra only" gets heavy review on Terra. A preference that covers all subagent work covers standard-tier implementers too. The harness models below are a **fallback only**, for a session whose loaded instruction files state no such preference.

Harness fallbacks:

- **Claude Code.** Spawn with the `Agent` tool; standard falls back to `model: sonnet` and heavy to `model: opus`. Inheriting the session model is fine where it already sits at the needed tier; report it by name, never as `inherited`. A typed read-only agent such as `Explore` counts as standard; set `model` explicitly for anything heavy.
- **Codex.** Standard falls back to Luna at `high` effort; heavy to Sol at `high` effort.
- **Cursor.** Standard falls back to Composer; heavy to Sol at `high` effort.

## Dispatch or main thread

Do a one-symbol lookup in a known file yourself. Dispatch anything wider, such as a pattern sweep, a version check, a library comparison, or an off-plan investigation. Dispatch runs independent investigations in parallel; main-thread reading keeps the conversation's nuance but fills your context with source you won't reread.
