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

Forces a brainstorm → spec → plan sequence before any code is written. Each stage produces a markdown artifact in `docs/crank/<slug>/` that feeds the next, so every implementation decision is documented and reviewable.

**Skills:**

| Skill | Invoke | What it does |
|---|---|---|
| `crank:brainstorm` | `/brainstorm` | Explores a feature, bug, or refactor through guided one-question-at-a-time conversation. Produces `brainstorm.md` capturing all decisions and a clear summary of what you're building and why. |
| `crank:spec` | `/spec` | Takes a `brainstorm.md` and sharpens it into an implementation-ready spec: exact interfaces, blast radius, size/risk estimate, and a validation plan with precise pass conditions. Produces `spec.md`. |
| `crank:plan` | `/plan` | Takes a `spec.md` and decomposes it into ordered, bite-sized tasks — each with file paths, commands, exact test code, and expected output. Runs an adversarial subagent review before handing back. Produces `plan.md`. |

**Typical flow:**

```
/brainstorm I want to add rate limiting to the API
  → docs/crank/2026-05-06-rate-limiting/brainstorm.md

/spec
  → docs/crank/2026-05-06-rate-limiting/spec.md

/plan
  → docs/crank/2026-05-06-rate-limiting/plan.md
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
      brainstorm/SKILL.md
      spec/SKILL.md
      plan/SKILL.md
```
