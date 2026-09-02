---
name: crank-deslop
description: Deslop a scope of code — strip AI-generated slop, hunt code-judo restructurings, and prune comments and docs the code has outgrown, then deliver a concise fix plan and offer to apply it. Scope is a PR, a branch diff, a logical area, or the entire codebase. Use for "deslop", "remove AI slop", "clean up AI-generated code", "thermonuclear code quality review", or "deep code quality audit".
argument-hint: "[scope: PR number | branch | area path | codebase] [optional focus]"
disable-model-invocation: true
---

# Deslop

## Goal

A concise fix plan over one declared scope, built by three specialized finders, one per altitude of opportunity. Each altitude is defined in full in its finder's brief:

- **Slop**, per [SLOP-BRIEF.md](SLOP-BRIEF.md): the residue agent-written code leaves behind: reflexive guards, type-silencing casts, needless nesting, style at odds with the surrounding file. Removed surgically, behavior identical.
- **Structure**, per [STRUCTURE-BRIEF.md](STRUCTURE-BRIEF.md): the thermonuclear pass. Code-judo moves: restructurings that keep behavior while whole branches, flags, wrappers, or layers disappear, plus spaghetti growth, shallow abstractions, muddy type boundaries, logic in the wrong layer, and files past a thousand lines.
- **Prose**, per [PROSE-BRIEF.md](PROSE-BRIEF.md): comments, docstrings, and in-scope docs: deleted when they restate the code, trimmed, consolidated to one site, corrected where the code has made them untrue, and freed of fragile references such as line numbers.

High conviction over coverage: a plan of five moves worth making beats an inventory of fifty observations.

## Hard Rules

- **Three finders, ever.** One slop finder, one structure finder, and one prose finder, each over the whole scope, all in a single wave. Never a fourth finder, never a second wave, never a partition: a scope one finder cannot read whole is narrowed with the user, not fanned wider.
- **Read-only until approval.** Scoping, finding, and planning mutate nothing. Fixes land only after the user accepts the plan.
- **Behavior unchanged.** Every planned fix preserves behavior; the one exception is a clear bug, and its plan row declares the behavior change explicitly.
- **Not a linter.** Anything a compiler, type-checker, formatter, or linter catches — and any matter of taste — never reaches the plan.
- **Never cut required behavior.** Trust-boundary validation, data-loss and error paths, security checks, and accessibility affordances are not slop; the *Never cut required behavior* section each brief carries governs.

## Flow

### 1. Scope

The user names the scope when invoking; the argument resolves to one of four shapes. If it names none, ask which before anything else.

- **PR** — `gh pr view <n> --json headRefName,baseRefName` then `gh pr diff <n>`; the target is the changed files at their current state, judged where the diff touched them.
- **Branch diff** — `git diff main...HEAD` (three-dot, so unrelated `main` commits stay out), plus `git diff HEAD` and untracked files from `git status --short` when uncommitted work is present.
- **Logical area** — a directory, module, or named slice; the target is its files read whole. Inventory them with `git ls-files <path>`.
- **Entire codebase** — every tracked source file; inventory with `git ls-files`.

**Done when:** the shape, the file inventory (or the exact diff command), and any focus from the argument are pinned and stated.

### 2. Find

Spawn the three standard finders in one wave, each over the whole scope. Hand each only its brief, the full file inventory or diff command, and any user focus: pointers, never your characterization of the code.

- The **slop finder** gets [SLOP-BRIEF.md](SLOP-BRIEF.md).
- The **structure finder** gets [STRUCTURE-BRIEF.md](STRUCTURE-BRIEF.md).
- The **prose finder** gets [PROSE-BRIEF.md](PROSE-BRIEF.md).

Each finder owns one altitude and returns opportunity rows per its brief's return format. A finder's closing line may point at a sibling's altitude; that line is a lead for step 3, not a row.

**Done when:** every finder has returned its rows.

### 3. Plan

Merge the rows yourself. Each finder saw one altitude, so cross-altitude work is yours: a slop or prose row inside code a structure move deletes anyway folds into that move; a lead a finder left about a sibling's altitude becomes a row only once you ground it in the code yourself; fold repeats of the same slop shape into one plan item listing its sites; drop any row you cannot ground in the code when you read its cited lines. Order structure, then slop, then prose, biggest deletion first.

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

This skill spawns finders at the **standard** tier — resolve it to your harness per [SUBAGENT-TIERS.md](SUBAGENT-TIERS.md). Each finder gets a clean, fresh context and forms its own read of the whole scope at its altitude; the three run concurrently in one wave.

### Vocabulary

Defined in [VOCABULARY.md](VOCABULARY.md). This skill leans on the **deletion test**, **depth**, and **spaghetti growth** — read their meanings there.

### Rubric

Each finder applies one fixed rubric. The slop finder's, the four slop patterns, the conviction bar, the never-cut list, and its return format, lives in [SLOP-BRIEF.md](SLOP-BRIEF.md). The structure finder's, the code-judo bar, the nine kinds of structural opportunity, the never-cut list, and its return format, lives in [STRUCTURE-BRIEF.md](STRUCTURE-BRIEF.md). The prose finder's, the four kinds of prose opportunity, fragile references, the never-cut list for tool-read prose, and its return format, lives in [PROSE-BRIEF.md](PROSE-BRIEF.md). Point each finder at its brief; don't reproduce it in the dispatch.
