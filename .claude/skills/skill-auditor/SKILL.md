---
name: skill-auditor
description: >-
  Audit and grade Claude Code skills against the agentskills.io skill-writing
  best practices. Use whenever the user wants to evaluate, grade, audit, score,
  or critique the quality of a skill or set of skills — e.g. "how good are the
  crank skills", "grade these skills against best practices", "audit our skills",
  "are these skills well-written". Spawns one subagent per best-practice area and
  returns a per-area grade out of 10 with evidence-backed rationale (what added to
  the score, what detracted). Defaults to the crank component skills when no
  target is named.
allowed-tools: Agent Read Glob Grep Bash
---

# Skill Auditor

Grade one or more skills against the agentskills.io skill-writing best practices,
one practice-area at a time. The output is a scorecard plus a per-area writeup of
what earned the grade and what cost points, backed by `file:line` evidence and a
short list of the highest-value fixes.

The rubric is the five best-practice areas in [references/RUBRIC.md](references/RUBRIC.md).
You assess against that file, not your general intuitions about "good skills" — it
carries the scoring anchors and the project-specific ground rules that stop you from
penalizing deliberate design choices (see the gotchas below).

## Step 1 — Resolve the target

If the user named skills (paths or names), audit those. Otherwise default to the
**four crank component skills**:

```
plugins/crank/skills/crank-brainstorm/
plugins/crank/skills/crank-spec/
plugins/crank/skills/crank-plan/
plugins/crank/skills/crank-execute/
```

The top-level `crank` orchestrator is **out of scope** by default — it's a thin
dispatcher, not a content skill. Include it only if the user asks.

List every file under each target directory (SKILL.md plus any `references/`,
templates, briefs) so the subagents grade the whole skill, not just SKILL.md:

```bash
find <target-dirs> -type f \( -name '*.md' -o -name '*.json' \)
```

The Context-economy lens is backed by a bundled script — measure, don't eyeball.
Run it once and hand the table to that subagent (it reports lines + tokens per
file and flags any SKILL.md over the 500-line / 5,000-token budget):

```bash
python3 scripts/count_lines_tokens.py <target-dirs>
```

## Step 2 — Launch one subagent per area, in parallel

Spawn all five in a single turn (`subagent_type: general-purpose`, model `opus` —
grading is judgment-heavy, so it's worth the stronger model). Each reads
`references/RUBRIC.md` and is told to grade **only its one area — but to grade each
of the four skills *separately* on it.** Keeping one grader per area means the
scorecard's columns are calibrated by a single consistent judge, so skills compare
fairly against each other. Independent lenses keep the grades honest and contexts clean.

The five areas (faithful to the rubric's H2 sections):

1. **Grounded in real expertise**
2. **Refined through real execution**
3. **Context economy**
4. **Calibrated control**
5. **Instruction patterns**

Use this prompt template for each (substitute `<AREA>`; keep the skill→files map):

```
You are auditing FOUR Claude Code skills against ONE area of the agentskills.io
best-practices rubric: "<AREA>".

Read the rubric first — focus on the "Shared ground rules" at the top (they prevent
you from penalizing deliberate design choices) and the "<AREA>" section:
  .claude/skills/skill-auditor/references/RUBRIC.md

Then read every file and grade EACH of the four skills SEPARATELY on your one area
(not the suite as a whole). Attribute each shared reference doc to the skills that
actually use it:
  crank-brainstorm  → crank-brainstorm/SKILL.md
  crank-spec        → crank-spec/SKILL.md + HTML-REVIEW.md + VOCABULARY.md + SUBAGENT-TIERS.md
  crank-plan        → crank-plan/SKILL.md  (+ HTML-REVIEW.md via symlink)
  crank-execute     → crank-execute/SKILL.md + PER-TASK-REVIEW-BRIEF.md + FINAL-REVIEW-BRIEF.md
(VOCABULARY.md and SUBAGENT-TIERS.md are shared by all four.)

Return EXACTLY this structure, nothing else:

### <AREA>
| Skill | Grade | One-line rationale (with file:line) |
|-------|-------|--------------------------------------|
| crank-brainstorm | N/10 | … |
| crank-spec | N/10 | … |
| crank-plan | N/10 | … |
| crank-execute | N/10 | … |

**What earned points** (across the skills, with file:line)
- …
**What cost points** (across the skills, with file:line)
- …
**Per-skill highest-value fix**
- crank-brainstorm: <concrete fix, or "—" if nothing material>
- crank-spec: …
- crank-plan: …
- crank-execute: …

Rules:
- Grade each skill on its OWN surface for this area. A skill with little surface here
  (e.g. crank-brainstorm has no reference files) is graded on what it has — say so
  rather than inventing deductions or rewarding absence.
- Cite file:line for every claim. A bare assertion is not evidence.
- Use the full 1–10 scale and the rubric anchors. Don't park every skill at the same
  number — if two skills differ on this area, their grades should differ.
- Judge the skills for their cross-harness context (see ground rules) — the ABSENCE
  of Claude-only machinery is not a defect.
```

## Step 3 — Assemble the report

Collect the five area returns. Each gives you a per-skill grade and a per-skill fix
for its area. Transpose that into a **skill × area scorecard**, justify it with the
per-area evidence, then regroup the fixes **per skill** (and surface cross-cutting
ones for the suite). Present inline; offer to save to a file only if the user asks.

```markdown
# Skill Audit — <target description>

**Skills:** crank-brainstorm, crank-spec, crank-plan, crank-execute
**Rubric:** agentskills.io best practices (5 areas)

## Scorecard
| Skill | Real expertise | Real execution | Context econ. | Calibrated control | Instruction patterns | **Overall** |
|-------|:--:|:--:|:--:|:--:|:--:|:--:|
| crank-brainstorm | N | N | N | N | N | **N.N** |
| crank-spec | N | N | N | N | N | **N.N** |
| crank-plan | N | N | N | N | N | **N.N** |
| crank-execute | N | N | N | N | N | **N.N** |
| **Suite avg** | N.N | N.N | N.N | N.N | N.N | **N.N** |

<one-paragraph read: the strongest and weakest skills, and the single biggest lever.
Per-skill Overall is the mean of its five area grades unless one area's severity
clearly dominates — say so if you weight it.>

## Findings by area
Cross-skill evidence per area — what earned points and what cost them, with
`file:line`. This is where the grades are justified.

### <Area>
**Earned** — …  **Cost** — …
(repeat for all five areas)

## Recommendations
### Per skill
**crank-brainstorm** — <its 1–3 highest-value fixes, gathered from the five areas>
**crank-spec** — …
**crank-plan** — …
**crank-execute** — …
### Suite-wide
1. <cross-cutting fix touching multiple skills/areas, ordered by impact>
```

Keep the `file:line` evidence in *Findings by area* (it makes the grades auditable);
keep the actions in *Recommendations* grouped by skill (it makes them easy to act on).
A fix that recurs across skills belongs in *Suite-wide*, not repeated under each.

## Gotchas — read before you grade

These are deliberate choices in this repo. Mis-reading them as flaws is the most
likely way to produce a wrong grade. (They're repeated in the rubric's ground rules
so the subagents see them too.)

- **Crank is cross-harness (Claude Code + Codex).** Skill bodies *deliberately avoid*
  `${CLAUDE_PLUGIN_ROOT}`/`${CLAUDE_*}` substitution, `@file` includes, `` !`cmd` ``
  bang execution, and bundled scripts reached by those paths — none of it runs under
  Codex. Their absence is correct, not a missing best practice. Don't dock
  "Instruction patterns" for "no bundled scripts."
- **Shared reference docs are symlinked, not duplicated** (e.g. `crank-plan` symlinks
  `crank-spec/HTML-REVIEW.md`). That's the intended cross-harness sharing pattern —
  not duplication and not odd structure.
- **Sub-skills compose via prose** ("Run the X skill"), not a Claude-only `Skill()`
  call — harness-neutral by design. Don't read it as vague.
- **Skill invocation ID is the directory name**, not the `name:` field.
- The grade is about **skill-writing quality vs. the rubric**, not whether crank's
  pipeline is a good idea. Stay on the rubric.
