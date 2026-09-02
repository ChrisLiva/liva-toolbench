---
name: crank-deslop
description: Deslop a declared scope of code into a concise fix plan, then offer to apply it. Strips agent-written slop, hunts code-judo restructurings, and prunes comments and docs the code has outgrown.
argument-hint: "[scope: PR number | branch | area path | codebase] [optional focus]"
disable-model-invocation: true
---

# Deslop

## Goal

A concise fix plan over one declared scope, built by three finders, one per altitude. Each altitude lives in full in its finder's brief:

- **Slop**, per [SLOP-BRIEF.md](SLOP-BRIEF.md): the residue agent-written code leaves behind, removed surgically with behavior identical.
- **Structure**, per [STRUCTURE-BRIEF.md](STRUCTURE-BRIEF.md): the thermonuclear pass, code-judo moves that keep behavior while whole branches, flags, wrappers, or layers disappear.
- **Prose**, per [PROSE-BRIEF.md](PROSE-BRIEF.md): comments, docstrings, and in-scope docs, deleted, trimmed, consolidated, or corrected where the code has outgrown them.

High conviction over coverage: a plan of five moves worth making beats an inventory of fifty observations.

## Hard Rules

- **Three finders, one wave.** One slop finder, one structure finder, one prose finder, each over the whole scope, dispatched together: exactly three, exactly once. A scope one finder cannot read whole is narrowed with the user.
- **Read-only until approval.** Scoping, finding, and planning mutate nothing; fixes land after the user accepts the plan.
- **Behavior unchanged.** Every planned fix preserves behavior. The one exception is a clear bug, and its plan row declares the behavior change.
- **Not a linter.** The plan carries only what no compiler, type-checker, formatter, or linter catches, and nothing that is a matter of taste.
- **Required behavior stays.** Trust-boundary validation, data-loss and error paths, security checks, and accessibility affordances are required behavior, and each brief's never-cut section governs.

## Flow

### 1. Scope

The user names the scope when invoking; the argument resolves to one of four shapes. If it names none, ask which before anything else.

- **PR**: `gh pr view <n> --json headRefName,baseRefName` then `gh pr diff <n>`; the target is the changed files at their current state, judged where the diff touched them.
- **Branch diff**: `git diff main...HEAD` (three-dot, so unrelated `main` commits stay out), plus `git diff HEAD` and untracked files from `git status --short` when uncommitted work is present.
- **Logical area**: a directory, module, or named slice; the target is its files read whole. Inventory them with `git ls-files <path>`.
- **Entire codebase**: every tracked source file; inventory with `git ls-files`.

**Done when:** the shape, the file inventory (or the exact diff command), and any focus from the argument are pinned and stated.

### 2. Find

Spawn the three finders in one wave, each over the whole scope. Hand each its brief (mapped under Goal), the file inventory or diff command, and any user focus, as pointers; each finder forms its own read of the code.

Each finder owns one altitude and returns opportunity rows per its brief's return format. A finder's closing line may point at a sibling's altitude; that line is a lead for step 3, not a row.

**Done when:** every finder has returned its rows.

### 3. Plan

Merge the rows yourself. Each finder saw one altitude, so cross-altitude work is yours:

- Read the lines every row cites. A row the code does not bear out is dropped.
- A slop or prose row inside code a structure move deletes anyway folds into that move.
- Repeats of one slop shape fold into one row listing its sites.
- A finder's lead about a sibling's altitude becomes a row only once you ground it in the code yourself.

Order structure, then slop, then prose, biggest deletion first. Render the plan:

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

If every finder returns clean, say so and stop.

**Done when:** the plan is rendered, with every surviving row grounded in a line you read.

### 4. Offer

Present the plan and ask whether to apply all of it or a subset the user picks. A structure move large enough to be its own project routes to `/crank plan` instead of being applied inline; say so in the offer.

**Done when:** the offer is made and the user's answer is recorded.

### 5. Apply (on approval)

Apply the accepted items: smallest diff per item, structure moves one at a time, slop sweeps batched. Then run the project's checks (format, lint, type-check, tests) and repair any breakage the fixes caused.

**Done when:** every accepted item is applied and the project's checks pass.

## References

### Subagents

Finders run at the **standard** tier; resolve it to your harness per [SUBAGENT-TIERS.md](SUBAGENT-TIERS.md).

### Vocabulary

Defined in [VOCABULARY.md](VOCABULARY.md). This skill leans on the **deletion test**, **depth**, and **spaghetti growth**.
