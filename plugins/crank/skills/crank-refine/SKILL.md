---
name: crank-refine
description: Refine a crank or crank-lite spec or plan into a concise list of simplifications, each citing the section it changes (a simpler design, existing code or libraries in place of invention, scope the needs never asked for), then offer to apply it.
argument-hint: "[path to a spec or plan .md] [optional focus]"
disable-model-invocation: true
---

# Refine

## Goal

Three finders, one per altitude, build a concise list of refinements over one spec or plan before anyone builds it. Each finder's brief defines its altitude in full:

- **Structure**, per [STRUCTURE-BRIEF.md](STRUCTURE-BRIEF.md): design-judo moves that meet the same criteria with whole modules, modes, tasks, or layers gone.
- **Reuse**, per [REUSE-BRIEF.md](REUSE-BRIEF.md): what the artifact invents that the codebase, the standard library, the platform, or a dependency already provides.
- **Scope**, per [SCOPE-BRIEF.md](SCOPE-BRIEF.md): requirements, options, safeguards, and ceremony the artifact's own stated needs never asked for.

[ARTIFACTS.md](ARTIFACTS.md) maps each spec and plan shape `crank` and `crank-lite` write onto the four roles the finders work from: **needs**, **criteria**, **design**, and **proof**.

High conviction over coverage: a list of the refinements worth making beats an inventory of observations. An artifact already at its simplest returns clean.

## Hard Rules

- **Three finders, one wave.** Dispatch exactly one finder per altitude, each over the whole artifact, all together and exactly once.
- **Read-only until the user accepts the list.**
- **Needs and criteria hold.** Every structure and reuse row leaves the artifact's needs and criteria as written. A scope row is the exception: it may cut a criterion no stated need asks for, and it declares what stops shipping.
- **Simpler, never more complete.** An ambiguity, an inaccuracy, a missing detail, a coverage hole, or an unverifiable step is a flag for the adversarial review each pipeline's phase runs, and none is a row here. Neither is a matter of taste, or a design traded for one no simpler.
- **Decisions are open; verdicts are not.** A row may challenge a decision the artifact records with its reason, by quoting the reason and showing that the simpler shape still meets it or naming what it gives up. No row reverses a verdict, as [ARTIFACTS.md](ARTIFACTS.md) → Outside every row lists them.
- **A plan refines under its spec.** Over a plan, the spec its `Spec:` line names is settled, decisions included. A simpler design the spec ruled out surfaces as a lead to refine the spec, never as a row.
- **Required behavior stays.** Trust-boundary validation, data-loss and error paths, security checks, and accessibility affordances are required behavior, and each brief's never-cut section governs.

## Flow

### 1. Scope

The user's invocation names one spec or plan. If it names none, ask which before anything else; handed an effort directory that holds both, ask which one.

Read [ARTIFACTS.md](ARTIFACTS.md) and the artifact in full, then state:

- **The artifact's path.** Write an artifact pasted inline, with no file of its own, to the OS temp dir first, and state that path.
- **Its shape**, one of the four in [ARTIFACTS.md](ARTIFACTS.md) → Shapes, told by content and structure. For any other spec or plan, state which of its sections fill each role. Ask once when the shape is genuinely ambiguous.
- **Where its needs and criteria live**: the section headings as the file spells them, or for a plan the spec path its `Spec:` line names, confirmed to exist.
- **The repository root** the design lands in (`git rev-parse --show-toplevel`), or `greenfield` when no code exists yet.
- **Any focus** the invocation names, such as "especially reuse". A focus weights the finders and never suppresses a row.

**Done when:** the path, the shape, the location of the needs and criteria, the repository root, and any focus are stated.

### 2. Find

Dispatch the finders. Hand each its brief, [ARTIFACTS.md](ARTIFACTS.md), and step 1's statement, as pointers; each finder forms its own read of the artifact and the code.

**Done when:** every finder has returned its rows.

### 3. List

Merge the rows yourself, since no finder saw another's altitude:

- Read the section every row cites, and the code, manifest, or documentation its evidence cites. Drop any row they do not bear out.
- Drop a structure or reuse row that leaves a criterion unmet, and any row that reverses a verdict.
- A reuse or scope row inside a piece a structure move deletes folds into that move.
- One piece named from two altitudes becomes one row, at the altitude that deletes more.
- A finder's closing line about a sibling's altitude, or about the spec above a plan, is a lead, not a row, until you ground it yourself.

Render the list, largest deletion first within each section. Every row opens with the artifact section it changes, cited as an **anchor**:

```markdown
## Refinements — <artifact path> (<shape>)

### Structure (<n>)
1. `<section>` → `<label>` — <kind>: <problem> · **move:** <the simpler design> · **deletes:** <what no longer gets built> · **holds:** <the criteria the move touches, and why each still passes>

### Reuse (<n>)
- `<section>` → `<label>` — <rung>: <what the artifact builds> · **use:** <the replacement, at its anchor, manifest line, or documentation link> · **gap:** <what the replacement leaves uncovered, or none>

### Scope (<n>)
- `<section>` → `<label>` — <pattern>: <what no stated need asks for> · **cut:** <the removal> · **loses:** <what stops shipping, or nothing a need names>

### Spec-level leads (<n>)
- `<spec section>` → `<label>` — <the simpler design the spec ruled out>
  <!-- a plan's list only; omit the section when no lead survived your own read -->
```

A row that reverses a recorded decision quotes that decision's stated reason. If every finder returns clean, say so and stop.

**Done when:** the list is rendered, with every surviving row grounded in a section and in evidence you read.

### 4. Offer

Present the list and ask whether to apply all of it or a subset the user picks. Two kinds of row are offered as a handoff instead of an inline edit:

- **A row over a plan that needs new task blocks or new oracles.** The pipeline's plan phase grounds and reviews what it writes, so hand that phase the accepted row as its input.
- **A spec-level lead.** Offer to run this skill over the spec, then re-plan from the refined spec.

**Done when:** the user's answer is recorded.

### 5. Apply (on approval)

Apply the accepted rows to the artifact in place, structure moves one at a time, following [ARTIFACTS.md](ARTIFACTS.md) → Where an accepted row lands. Then re-read the artifact end to end and grep it for every name a row removed: no section still builds, consumes, verifies, or stages a piece that is gone.

Close with the shape's line from [ARTIFACTS.md](ARTIFACTS.md) → Next command, for the user to run.

**Done when:** every accepted row is in the artifact, the grep for each removed name returns nothing, and the next command is stated.

## References

### Subagents

The structure finder runs at the **heavy** tier and the reuse and scope finders at the **standard** tier; resolve both per [SUBAGENT-TIERS.md](SUBAGENT-TIERS.md): a loaded instruction file's preference first, its harness models only as the fallback.

### Vocabulary

Defined in [VOCABULARY.md](VOCABULARY.md). This skill leans on the **deletion test**, **depth**, **port / adapter**, **spaghetti growth**, and the **anchor**.
