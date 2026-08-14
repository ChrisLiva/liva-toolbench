# liva-toolbench

A plugin marketplace for design-first development tools, shipping for both **Claude Code and Codex**. Install the marketplace to get one-command access to every plugin here, or load a single plugin directly with `--plugin-dir` for fast iteration.

---

## Install the marketplace

```bash
# inside Claude Code
/plugin marketplace add https://github.com/ChrisLiva/liva-toolbench
```

Once added, install any plugin by name:

```bash
/plugin install crank
/plugin install crank-lite
/plugin install effective-html
```

For Codex, the repo doubles as a local marketplace (`.agents/plugins/marketplace.json`):

```bash
codex plugin add crank@liva-toolbench
```

## Load a plugin without installing (for development)

```bash
claude --plugin-dir ./plugins/crank
```

Then `/reload-plugins` after any edits.

---

## Plugins

All three plugins ship **cross-harness** — the same `skills/` tree runs under both Claude Code and Codex (each carries a `.claude-plugin/` and a `.codex-plugin/` manifest).

### `crank` — design-first development pipeline

Forces a **spec → plan → execute** sequence before any code is written. Each stage produces a markdown artifact (brainstorm → spec → plan → retro) that feeds the next, so every implementation decision is written down and reviewable before it ships. Artifacts live in a per-effort `.crank/<slug>/` directory at the working root (gitignored via `.crank/.gitignore`), so a later session resumes from the file, not from a pasted path.

**Skills:**

| Skill | Invoke | What it does |
|---|---|---|
| `crank:crank` | `/crank [brainstorm\|spec\|plan]` | The pipeline's **front door and router**. Takes an explicit route, or triages the ask itself — a raw idea routes to **brainstorm** (design brief), a formed idea or brief to **spec** (PRD + technical spec, adversarially reviewed), a settled design or scoped bug fix to **plan** (ordered TDD-flavored tasks, adversarially reviewed). Each phase hands off to the next only on an explicit "continue". |
| `crank:crank-execute` | `/crank-execute` | Executes a plan **task-by-task** — picks a solo / sequential / parallel shape, runs TDD where a real seam exists, gates every "done" on verification evidence, runs a fresh-eyes final review, and writes `retro.md`. |
| `crank:crank-deepen` | `/crank-deepen` | Scans a codebase for **deepening opportunities** — shallow modules, leaking seams — presents them as a visual HTML report, grills through your pick, and emits a brainstorm brief that feeds the pipeline. |
| `crank:crank-refine` | `/crank-refine` | Grills an existing brainstorm, spec, or plan **at its own altitude** until nothing consequential is left undecided — one informed question at a time, sharpening the artifact in place. Standalone pass; doesn't advance the pipeline. |
| `crank:crank-review` | `/crank-review` | Reviews a PR, commit range, or uncommitted changes for a **short list of high-confidence findings** — does the code do what it says, what can be deleted, what edge case slips through — each independently validated before it ships. |
| `crank:crank-test-prune` | `/crank-test-prune` | Verdicts every test in scope **KEEP / DELETE / REFACTOR / MERGE** so only behavior-pinning tests survive — redundancy judged suite-wide, expected values from an independent source of truth, full suite green after applying. |

**Typical flow:**

```text
/crank  add rate limiting to the API
  → routes to spec ("formed idea"), grills, writes
    .crank/rate-limiting/spec.md
  → on "continue", the plan phase produces
    .crank/rate-limiting/plan.md

/crank-execute  .crank/rate-limiting/plan.md
  → .crank/rate-limiting/retro.md
```

### `crank-lite` — the lightweight pipeline

The same brainstorm → spec → plan → execute shape as `crank`, with less ceremony — fewer subagents and review gates, suited to smaller efforts. Artifacts share the `.crank/<slug>/` convention.

| Skill | Invoke | What it does |
|---|---|---|
| `crank-lite:crank-lite` | `/crank-lite [brainstorm\|spec\|plan]` | Front door and router — triages the ask to brainstorm, spec, or plan and runs that phase. |
| `crank-lite:lite-execute` | `/lite-execute` | Executes a PRD, spec, or plan: implement, verify, review, and commit the work. |
| `crank-lite:lite-deepen` | `/lite-deepen` | The lightweight deepening scan — presents opportunities as chat cards with ASCII before/after diagrams and emits a brainstorm brief for the pipeline. |

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
      crank/SKILL.md            # router; BRAINSTORM.md / SPEC.md / PLAN.md
                                #   phase files beside it, plus the canonical
                                #   shared reference docs (VOCABULARY.md,
                                #   SUBAGENT-TIERS.md, GRILLING.md, READBACK.md)
      crank-execute/SKILL.md    # carries hand-synced real copies of the
      crank-deepen/…            #   shared docs (never symlinks); same for
      crank-refine/…            #   the other crank skills
      crank-review/…
      crank-test-prune/…
  crank-lite/
    .claude-plugin/plugin.json
    .codex-plugin/plugin.json
    skills/
      crank-lite/SKILL.md       # router + BRAINSTORM/SPEC/PLAN phase files
      lite-execute/SKILL.md
      lite-deepen/SKILL.md
  effective-html/
    .claude-plugin/plugin.json
    .codex-plugin/plugin.json
    skills/effective-html/SKILL.md
```

See `CLAUDE.md` for authoring conventions, the cross-harness rules, and the version-bump checklist.
