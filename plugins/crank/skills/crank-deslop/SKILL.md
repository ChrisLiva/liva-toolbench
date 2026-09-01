---
name: crank-deslop
description: Deslop a scope of code — strip AI-generated slop, hunt code-judo restructurings, and prune comments and docs the code has outgrown, then deliver a concise fix plan and offer to apply it. Scope is a PR, a branch diff, a logical area, or the entire codebase. Use for "deslop", "remove AI slop", "clean up AI-generated code", "thermonuclear code quality review", or "deep code quality audit".
argument-hint: "[scope: PR number | branch | area path | codebase] [optional focus]"
disable-model-invocation: true
---

# Deslop

## Goal

A concise fix plan over one declared scope, built from three altitudes of opportunity. The first two are defined in full in [DESLOP-BRIEF.md](DESLOP-BRIEF.md), the third in [PROSE-BRIEF.md](PROSE-BRIEF.md):

- **Slop** — the residue agent-written code leaves behind: reflexive guards, type-silencing casts, needless nesting, style at odds with the surrounding file. Removed surgically, behavior identical.
- **Structure** — code-judo moves: restructurings that keep behavior while whole branches, flags, wrappers, or layers disappear.
- **Prose** — comments, docstrings, and in-scope docs: deleted when they restate the code, trimmed, consolidated to one site, corrected where the code has made them untrue, and freed of fragile references such as line numbers.

High conviction over coverage: a plan of five moves worth making beats an inventory of fifty observations.

## Hard Rules

- **Three finders, ever.** Partition the scope into at most two logical sections and spawn one section finder per section, plus one prose finder over the whole scope, all in a single wave. A scope one section finder can read whole gets one section finder and the prose finder. Never a fourth finder, never a second wave — a scope too large for two section finders is narrowed with the user, not fanned wider.
- **Read-only until approval.** Scoping, finding, and planning mutate nothing. Fixes land only after the user accepts the plan.
- **Behavior unchanged.** Every planned fix preserves behavior; the one exception is a clear bug, and its plan row declares the behavior change explicitly.
- **Not a linter.** Anything a compiler, type-checker, formatter, or linter catches — and any matter of taste — never reaches the plan.
- **Never cut required behavior.** Trust-boundary validation, data-loss and error paths, security checks, and accessibility affordances are not slop; the brief's [Never cut required behavior](DESLOP-BRIEF.md) section governs.

## Flow

### 1. Scope

The user names the scope when invoking; the argument resolves to one of four shapes. If it names none, ask which before anything else.

- **PR** — `gh pr view <n> --json headRefName,baseRefName` then `gh pr diff <n>`; the target is the changed files at their current state, judged where the diff touched them.
- **Branch diff** — `git diff main...HEAD` (three-dot, so unrelated `main` commits stay out), plus `git diff HEAD` and untracked files from `git status --short` when uncommitted work is present.
- **Logical area** — a directory, module, or named slice; the target is its files read whole. Inventory them with `git ls-files <path>`.
- **Entire codebase** — every tracked source file; inventory with `git ls-files`.

**Done when:** the shape, the file inventory (or the exact diff command), and any focus from the argument are pinned and stated.

### 2. Find

Partition the scope into at most two logical sections — split along module, layer, or directory boundaries so each section is coherent, never by raw file count alone. Spawn one standard finder per section, handing each only [DESLOP-BRIEF.md](DESLOP-BRIEF.md), its section's file inventory or diff command, and any user focus — pointers, never your characterization of the code. In the same wave, spawn one standard prose finder over the whole scope, handing it only [PROSE-BRIEF.md](PROSE-BRIEF.md), the full file inventory or diff command, and any user focus; comments, docstrings, and in-scope docs are its material, so the section finders leave them alone. Each finder returns opportunity rows per its brief's return format.

**Done when:** every finder has returned its rows.

### 3. Plan

Merge the rows yourself. Each section finder saw one section, so cross-section work is yours: dedupe rows that are one pattern surfacing twice, fold repeats of the same slop shape into one plan item listing its sites, and drop any row you cannot ground in the code when you read its cited lines. A prose row about a comment a structure move deletes anyway folds into that move. Order structure, then slop, then prose, biggest deletion first.

Render the plan:

```markdown
## Deslop plan — <scope>

### Structure (<n>)
1. `<file:line>` — <problem> · **move:** <restructuring, behavior preserved>
   <!-- a row fixing a clear bug declares the behavior change here -->

### Slop (<n>)
- `<file:line>` — <pattern> · **fix:** <surgical removal>
  <!-- fold repeated sites of one pattern into one row listing them -->

### Prose (<n>)
- `<file:line>` — <delete | trim | consolidate | correct> · <problem> · **fix:** <remedy>
  <!-- a consolidate row lists every site it folds; a correct row quotes the untrue claim -->
```

If every finder returns clean, say so and stop — never manufacture a plan.

**Done when:** the plan is rendered with every surviving row grounded.

### 4. Offer

Present the plan and ask whether to apply it — all of it, or a subset the user picks. Make no edits without approval. A structure move large enough to be its own project routes to `/crank plan` instead of being applied inline; say so in the offer.

**Done when:** the offer is made and the user's answer is recorded.

### 5. Apply (on approval)

Apply the accepted items — smallest diff per item, structure moves one at a time, slop sweeps batched. Then run the project's checks (format, lint, type-check, tests) and repair any breakage the fixes caused.

**Done when:** every accepted item is applied and the project's checks pass.

## References

### Subagents

This skill spawns finders at the **standard** tier — resolve it to your harness per [SUBAGENT-TIERS.md](SUBAGENT-TIERS.md). Each finder gets a clean, fresh context and forms its own read of its section or of the scope's prose; the three run concurrently in one wave.

### Vocabulary

Defined in [VOCABULARY.md](VOCABULARY.md). This skill leans on the **deletion test**, **depth**, and **spaghetti growth** — read their meanings there.

### Rubric

The fixed rubric every section finder applies — the two code altitudes, the conviction bar, the never-cut list, and the return format — lives in [DESLOP-BRIEF.md](DESLOP-BRIEF.md). The prose finder's rubric — the four kinds of prose opportunity, fragile references, the never-cut list for tool-read prose, and its return format — lives in [PROSE-BRIEF.md](PROSE-BRIEF.md). Point each finder at its brief; don't reproduce it in the dispatch.
