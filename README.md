# liva-toolbench

A Claude Code plugin marketplace for design-first development tools. Install the marketplace to get one-command access to every plugin here, or load a single plugin directly with `--plugin-dir` for fast iteration.

---

## Install the marketplace

```bash
# inside Claude Code
/plugin marketplace add https://github.com/ChrisLiva/liva-toolbench
```

Once added, install any plugin by name:

```bash
/plugin install crank
```

## Load a plugin without installing (for development)

```bash
claude --plugin-dir ./plugins/crank
```

Then `/reload-plugins` after any edits.

---

## Plugins

### `crank` — design-first development pipeline

Forces a spec → plan → execute sequence before any code is written. Each stage produces a markdown artifact in `docs/crank/<slug>/` that feeds the next, so every implementation decision is documented and reviewable.

**Skills:**

| Skill | Invoke | What it does |
|---|---|---|
| `crank:spec` | `/spec` | Takes an idea or prompt through a continuous one-question-at-a-time grill — exploring the codebase, sharpening decisions, updating CONTEXT.md inline, and offering ADRs sparingly. Produces an implementation-ready spec.md with a Key decisions section, exact interfaces, blast radius, size/risk, and validation plan. |
| `crank:plan` | `/plan` | Takes a `spec.md` and decomposes it into ordered, bite-sized tasks — each with file paths, commands, exact test code, and expected output. Runs an adversarial subagent review before handing back. Produces `plan.md`. |
| `crank:execute` | `/execute` | Executes a plan task-by-task — auto-triages between solo, sequential, or parallel subagents; runs TDD per task; gates on real verification evidence; writes retro.md. |
| `crank:crank` | `/crank` | Runs the full pipeline (spec → plan → execute) autonomously from one prompt. Each phase runs in its own subagent inside a fresh git worktree. |

**Typical flow:**

```text
/spec I want to add rate limiting to the API
  → docs/crank/2026-05-06-rate-limiting/spec.md

/plan
  → docs/crank/2026-05-06-rate-limiting/plan.md

/execute
  → docs/crank/2026-05-06-rate-limiting/retro.md
```

Then execute the plan task-by-task in a fresh session.

---

## Repository layout

```
.claude-plugin/
  marketplace.json       # marketplace catalog
plugins/
  crank/
    .claude-plugin/
      plugin.json
    skills/
      spec/SKILL.md
      plan/SKILL.md
```
