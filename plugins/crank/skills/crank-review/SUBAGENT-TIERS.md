# Subagent tiers

The crank skills delegate to subagents at two capability tiers — **standard** (bulk work) and **heavy** (work that rewards the strongest reasoning). A tier names *intent*, not a model; each skill's Subagents section assigns its dispatches to tiers.

**Resolving a tier to a model:** resolve once per run and reuse the mapping at every dispatch. The source of truth is a subagent model preference in the user instructions already loaded this session (user- and project-level `CLAUDE.md` / `AGENTS.md`), and it is binding: heavy = their strongest-reasoning choice, standard = their bulk-work choice, even when it names a weaker model than a fallback below (Terra only means heavy review runs on Terra); a preference covering all subagent work covers standard-tier implementers too. The harness models below are a **fallback only**, for a session whose loaded instruction files state no such preference. Where a skill's Pre-flight block carries a Subagents line, that line names the source beside the models: the instruction file whose preference was mapped, or `harness fallback`.

Harness fallbacks:

- **Claude Code** — spawn via the `Agent` tool; fallback: standard → `model: sonnet`, heavy → `model: opus`. Inheriting the session model is fine where it already sits at the needed tier; report it by name, never as `inherited`. A typed read-only agent (e.g. `Explore`) counts as standard; set `model` explicitly for anything heavy.
- **Codex** — fallback: standard → `gpt-5.6-terra` at `medium` effort (Terra-Medium), heavy → `gpt-5.6-sol` at `high` effort (Sol-High).
- **Cursor** — fallback: standard → `cursor-composer-2-5`, heavy → `gpt-5.6-sol-high` (Sol-High).

## Dispatch or main thread

Do a one-symbol lookup in a known file yourself; dispatch anything wider — a pattern sweep, a version check, a library comparison, an off-plan investigation. Dispatch keeps your synthesis window clean and runs independent investigations in parallel; main-thread reading keeps the conversation's nuance but fills your window with source you'll never reread.
