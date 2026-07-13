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
/plugin install effective-html
```

## Load a plugin without installing (for development)

```bash
claude --plugin-dir ./plugins/crank
```

Then `/reload-plugins` after any edits.

---

## Plugins

### `crank` — design-first development pipeline

Forces a **spec → plan → execute** sequence before any code is written. Each stage produces a markdown artifact (spec → plan → retro) that feeds the next, so every implementation decision is written down and reviewable before it ships. Artifacts are written to OS temp files by default; each skill offers to copy them into the repo at hand-back.

`crank` ships **cross-harness** — the same `skills/` tree runs under both Claude Code and Codex (it carries both a `.claude-plugin/` and a `.codex-plugin/` manifest).

**Skills:**

| Skill | Invoke | What it does |
|---|---|---|
| `crank:crank-brainstorm` | `/crank-brainstorm` | Turns a raw idea into a high-level **design brief** through dialogue, codebase exploration, and research — settling the problem, approach, and consequential decisions before the spec. Optional front door to the pipeline. |
| `crank:crank-spec` | `/crank-spec` | Writes the conversation up as a **spec** (part PRD, part technical spec) — grounds it in the codebase, grills the open technical decisions one at a time, then adversarially reviews it in place. Produces `spec.md`. |
| `crank:crank-plan` | `/crank-plan` | Decomposes a spec into ordered, bite-sized, **TDD-flavored tasks** — each with file paths, commands, embedded test code, and exact expected output — then adversarially reviews the plan in place. Produces `plan.md`. |
| `crank:crank-execute` | `/crank-execute` | Executes a plan **task-by-task** — picks a solo / sequential / parallel shape, runs TDD where a real seam exists, gates every "done" on verification evidence, runs a fresh-eyes final review, and writes `retro.md`. |
| `crank:crank-refine` | `/crank-refine` | Grills an existing brainstorm, spec, or plan **at its own altitude** until nothing consequential is left undecided — one informed question at a time, sharpening the artifact in place. Standalone pass; doesn't advance the pipeline. |
| `crank:crank-review` | `/crank-review` | Reviews a PR, commit range, or uncommitted changes for a **short list of high-confidence findings** — does the code do what it says, what can be deleted, what edge case slips through — each independently validated before it ships. |
| `crank:crank-test-prune` | `/crank-test-prune` | Verdicts every test in scope **KEEP / DELETE / REFACTOR** so only behavior-pinning tests survive — redundancy judged suite-wide, expected values from an independent source of truth, full suite green after applying. |

**Typical flow:**

```text
/crank-spec  add rate limiting to the API
  → /tmp/crank-spec.<rand>.md     (spec — a temp file)

/crank-plan  /tmp/crank-spec.<rand>.md
  → /tmp/crank-plan.<rand>.md     (plan)

/crank-execute  /tmp/crank-plan.<rand>.md
  → /tmp/crank-retro.<rand>.md    (retro)
```

### `effective-html` — single-file HTML communication artifacts

A user-summoned skill that nudges the coding agent to answer with a **single self-contained `.html` file** — a review, report, explainer, or throwaway editor — instead of a wall of markdown, when that's the better medium. Distilled from `anthropics/html-effectiveness`. Artifacts are offline-safe: one file, inline CSS, system fonts, no CDN.

| Skill | Invoke | What it does |
|---|---|---|
| `effective-html:effective-html` | `/effective-html <what to make>` | Produces one offline-safe HTML artifact for the thing you describe. User-invoked only. |

---

## Repository layout

```
.claude-plugin/
  marketplace.json              # Claude Code marketplace catalog
.agents/plugins/
  marketplace.json              # Codex marketplace index (cross-harness plugins)
plugins/
  crank/
    .claude-plugin/plugin.json  # Claude manifest
    .codex-plugin/plugin.json   # Codex manifest (cross-harness)
    skills/
      crank/SKILL.md
      crank-brainstorm/SKILL.md
      crank-spec/SKILL.md       # owns the shared reference docs —
      crank-plan/SKILL.md       #   VOCABULARY.md, SUBAGENT-TIERS.md, HTML-REVIEW.md,
      crank-execute/SKILL.md    #   symlinked into the sibling skill dirs
  effective-html/
    .claude-plugin/plugin.json
    .codex-plugin/plugin.json
    skills/effective-html/SKILL.md
```

See `CLAUDE.md` for authoring conventions, the cross-harness rules, and the version-bump checklist.
