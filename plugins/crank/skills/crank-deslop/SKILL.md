---
name: crank-deslop
description: Deslop a declared scope of code into a concise fix plan for agent-written slop, code-judo restructurings, and comments and docs the code has outgrown, then offer to apply it.
argument-hint: "[scope: PR number | branch | area path | codebase] [optional focus]"
disable-model-invocation: true
---

# Deslop

## Goal

Three finders, one per altitude, build a concise fix plan over one declared scope. Each finder's brief defines its altitude in full:

- **Slop**, per [SLOP-BRIEF.md](SLOP-BRIEF.md): the residue agent-written code leaves behind.
- **Structure**, per [STRUCTURE-BRIEF.md](STRUCTURE-BRIEF.md): code-judo moves that make whole branches, flags, wrappers, or layers disappear.
- **Prose**, per [PROSE-BRIEF.md](PROSE-BRIEF.md): comments, docstrings, and in-scope docs the code has outgrown.

High conviction over coverage: a plan of the moves worth making beats an inventory of observations. Prose is the exception. Every comment or docstring that is not load-bearing is a row, so that section runs long.

## Hard Rules

- **Three finders, one wave.** Dispatch exactly one finder per altitude, each over the whole scope, all together and exactly once. With the user, narrow any scope one finder cannot read whole.
- **Read-only until the user accepts the plan.**
- **Behavior unchanged.** Every planned fix preserves behavior except a clear bug fix, whose plan row declares the behavior change.
- **Not a linter.** The plan carries nothing a compiler, type-checker, formatter, or linter catches, and no matter of taste.
- **Required behavior stays.** Trust-boundary validation, data-loss and error paths, security checks, and accessibility affordances are required behavior, and each brief's never-cut section governs.

## Flow

### 1. Scope

The user's invocation names the scope as one of four shapes. If it names none, ask which before anything else.

- **PR**: `gh pr view <n> --json headRefName,baseRefName` then `gh pr diff <n>`; the target is the changed files at their current state, judged where the diff touched them.
- **Branch diff**: `git diff <default-branch>...HEAD`, whose three dots keep unrelated default-branch commits out, plus `git diff HEAD` and untracked files from `git status --short` when uncommitted work is present.
- **Logical area**: a directory, module, or named slice, read whole; inventory its files with `git ls-files <path>`.
- **Entire codebase**: every tracked source file; inventory with `git ls-files`.

**Done when:** the shape, the file inventory or exact diff command, and any focus are stated.

### 2. Find

Dispatch the finders. Hand each its brief, the file inventory or diff command, and any user focus, as pointers; each finder forms its own read of the code.

**Done when:** every finder has returned its rows.

### 3. Plan

Merge the rows yourself, since no finder saw another's altitude:

- Read the lines every row cites and drop any row the code does not bear out.
- A slop or prose row inside code a structure move deletes anyway folds into that move.
- Repeats of one slop shape fold into one row listing its sites.
- A finder's closing line about a sibling's altitude is a lead, not a row, until you ground it in the code yourself.

Render the plan, largest deletion first within each section:

```markdown
## Deslop plan — <scope>

### Structure (<n>)
1. `<file:line>` — <problem> · **move:** <restructuring, behavior preserved>

### Slop (<n>)
- `<file:line>` — <pattern> · **fix:** <surgical removal>

### Prose (<n>)
- `<file:line>` — <delete | trim | consolidate | correct> · <problem> · **fix:** <remedy>
  <!-- a consolidate row lists every site it folds; a correct row quotes the untrue claim -->
```

If every finder returns clean, say so and stop.

**Done when:** the plan is rendered, with every surviving row grounded in a line you read.

### 4. Offer

Present the plan and ask whether to apply all of it or a subset the user picks. Offer any structure move large enough to be its own project as a `/crank plan` handoff instead of an inline fix.

**Done when:** the user's answer is recorded.

### 5. Apply (on approval)

Apply the accepted rows: smallest diff per row, structure moves one at a time, slop sweeps batched. Then run the project's checks (format, lint, type-check, tests) and repair any breakage the fixes caused.

**Done when:** every accepted row is applied and the project's checks pass.

## References

### Subagents

Finders run at the **standard** tier; resolve it per [SUBAGENT-TIERS.md](SUBAGENT-TIERS.md): a loaded instruction file's preference first, its harness models only as the fallback.

### Vocabulary

Defined in [VOCABULARY.md](VOCABULARY.md). This skill leans on the **deletion test**, **depth**, and **spaghetti growth**.
