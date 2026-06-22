# Skill-Writing Rubric

Source: agentskills.io best practices for skill creators. Five areas, each graded
out of 10. This file is the standard the auditor judges against — not general
intuition about "good skills."

---

## Shared ground rules (read first, applies to every area)

### Scoring scale — use the whole range, anchor to these

- **9–10 Exemplary** — this skill could be cited as a *reference example* of the
  principle. Nothing material is deductible (and you must say why).
- **7–8 Solid** — the principle is clearly and consistently applied; only minor,
  non-blocking gaps remain.
- **5–6 Mixed** — applied in places, violated in others. Net usable but visibly
  improvable.
- **3–4 Weak** — the principle is largely neglected and it concretely hurts the skill.
- **1–2 Absent / anti-pattern** — the skill actively works against the principle.

Do not cluster grades at 7. Most real skills land 5–8 with a clear reason for the
exact number. Every grade needs `file:line` evidence on both sides; a grade above 8
must explicitly argue why nothing more was deductible.

### Evidence discipline

Every booster and every detractor cites a concrete location (`SKILL.md:42`,
`HTML-REVIEW.md:110`). "Feels generic" is not a finding; "the 'handle errors
appropriately' line at SKILL.md:88 is generic filler the model already knows" is.

### Project context that must NOT be graded as a flaw

The crank skills are **cross-harness** (Claude Code + Codex). The following are
deliberate and correct — do not deduct for them:

- **No `${CLAUDE_*}` substitution, no `@file` includes, no `` !`cmd` `` bang
  execution, no scripts reached by `${CLAUDE_PLUGIN_ROOT}`.** None of that runs under
  Codex, so the skills avoid it on purpose. "No bundled scripts" is therefore *not*
  an automatic Instruction-patterns deduction here — judge whether a deterministic
  step that COULD be harness-neutral prose is instead left vague, not whether a
  `.py` file exists.
- **Symlinked shared reference docs** (e.g. `crank-plan/HTML-REVIEW.md` →
  `crank-spec/HTML-REVIEW.md`) are the intended sharing mechanism, not duplication.
- **Prose sub-skill composition** ("Run the crank-spec skill") is harness-neutral by
  design, not vagueness.
- **Skill invocation ID = directory name**, not the `name:` frontmatter field.

You are grading skill-*writing* quality against the rubric — not whether crank's
spec→plan→execute pipeline is a sound product idea.

---

## Area 1 — Grounded in real expertise

**The principle.** Valuable skills encode domain-specific knowledge the model
wouldn't already have: the actual API patterns, project conventions, schemas,
failure modes, and corrections a practitioner learned the hard way. The failure
mode is generic LLM filler ("handle errors appropriately," "follow best practices").

**Adds points**
- Concrete, project-specific facts, conventions, vocabulary, or constraints (e.g. a
  defined term set, a named pipeline contract, specific file/section layouts).
- Gotchas that read like folded-in real corrections, not textbook advice.
- Named tools/commands/formats specific to this workflow rather than abstractions.

**Detracts**
- Generic advice the base model already follows without being told.
- Vague verbs ("appropriately," "as needed," "properly") standing in for a real rule.
- Content that would apply unchanged to any skill in any domain.

**Calibration.** A skill dense with project-specific contracts and vocabulary that
the model demonstrably wouldn't invent → 8–10. A skill that's mostly sensible-but-
generic process the model would do anyway → 3–5.

---

## Area 2 — Refined through real execution

**The principle.** Good skills show the fingerprints of having been run against real
tasks and corrected — specific failure cases anticipated, traps called out, defaults
chosen because the obvious alternative went wrong. You can't see the iteration
history in the text, so judge by observable proxies.

**Adds points**
- Gotchas / "don't do X, do Y" rules that clearly answer a *specific* past mistake.
- Anticipated failure cases and edge handling that only experience surfaces.
- References to retros, changelogs, or recorded decisions ("per project decision: …").
- (Optional evidence) `git log --oneline -- <skill dir>` showing real iteration, not
  a single drop. You may run this read-only.

**Detracts**
- Reads like a first draft: plausible structure, no scar tissue, no anticipated
  failure modes.
- Edge cases waved off with "use your judgment" where a learned default belongs.

**Calibration.** Skill visibly shaped by real runs (specific traps, recorded
decisions, iteration history) → 8–10. Clean but untested-feeling → 4–6.

---

## Area 3 — Context economy

**The principle.** Everything in SKILL.md competes for attention once loaded. Spend
tokens on what the model lacks; cut what it knows. Keep coherent scope. Aim for
moderate detail. Use progressive disclosure: SKILL.md under ~500 lines / ~5,000
tokens with core instructions; heavier material in `references/` loaded *on demand*
with explicit "read this file WHEN <trigger>" pointers.

**Measure, don't eyeball.** Run the bundled
`scripts/count_lines_tokens.py <skill dirs>` for exact per-file line and token
counts against the budget. Judge **tokens, not just lines** — a SKILL.md can sit
at a third of the line budget yet near the token ceiling because the prose is
dense, and that's the number that reflects attention cost. The script flags only
SKILL.md files (reference files load on demand and are reported as `ref`).

**Adds points**
- Lean SKILL.md focused on non-obvious instructions; explanations the model needs.
- Reference/asset files used for the heavy detail, with clear *when-to-load* triggers
  ("read HTML-REVIEW.md before rendering the review"), not a generic "see references/."
- Coherent, single-purpose scope that composes rather than sprawls.

**Detracts**
- Bloat: restating what the model knows, ceremony, redundant sections.
- A monolithic SKILL.md past the line/token budget that should have been split.
- Reference files with no trigger telling the model when to open them.
- Scope so broad the skill is hard to apply precisely, or so narrow it forces several
  skills to co-load for one task.

**Calibration.** Lean SKILL.md + well-triggered progressive disclosure → 8–10.
Over-long or padded body, or reference files no one's told to open → 4–6.

---

## Area 4 — Calibrated control

**The principle.** Match specificity to fragility. Be prescriptive (exact commands,
fixed sequences) only where the operation is fragile or consistency is mandatory.
Give freedom — and explain *why* — where multiple approaches are valid. Provide
defaults, not menus. Favor reusable procedures over one-off declarations. The smell:
ALL-CAPS MUST/NEVER and rigid scaffolding used where reasoning would serve better.

**Adds points**
- Prescriptive steps exactly where fragility demands them (a fixed command, an
  ordered gated workflow), looser guidance elsewhere.
- Instructions that explain the *why*, trusting the model to adapt.
- A clear default with a brief escape hatch, rather than a menu of equal options.
- Methods that generalize ("read the schema, then…") over instance-specific answers.

**Detracts**
- ALL-CAPS MUST/NEVER or rigid structure where judgment would do — control out of
  proportion to fragility.
- Menus of equivalent options with no default ("you can use A, B, C, or D…").
- Over-prescription that will misfire on tasks slightly off the template.
- Under-specification on a genuinely fragile step (no exact command/sequence).

**Calibration.** Specificity tracks fragility, defaults are clear, the *why* is
present → 8–10. Heavy-handed mandates or option-menus throughout → 3–5.

---

## Area 5 — Instruction patterns

**The principle.** Reusable techniques for structuring skill content — use the ones
that fit, not all of them: **gotchas** sections (highest-value: concrete env-specific
corrections, kept where the model reads them before the trap); **output templates**
(concrete structures beat prose descriptions); **checklists** for multi-step
workflows with dependencies/gates; **validation loops** (do → validate → fix →
repeat); **plan-validate-execute** for batch/destructive ops; **bundling reusable
scripts** when the model would otherwise reinvent the same logic each run.

**Adds points**
- A real gotchas section with concrete, non-obvious corrections placed before the
  situation arises.
- Output templates for any format the skill must produce reliably.
- Checklists / validation gates where steps depend on each other or must not be skipped.
- Plan-then-execute structure for risky or batch operations.

**Detracts**
- Output format described only in prose where a template would pattern-match better.
- Multi-step gated workflow with no checklist or validation, easy to half-complete.
- A gotcha buried in a reference file with no trigger, so the model hits the trap first.
- Reinvented-each-run logic that a harness-neutral procedure (or, where the harness
  allows, a script) should capture once.

**Cross-harness note (do not deduct).** "No bundled `.py` scripts" is not a flaw for
crank — see the ground rules. Judge whether a deterministic, repeatable step is
captured as a clear reusable procedure, not whether it's shipped as code.

**Calibration.** Fitting patterns applied where they help (templates, gotchas,
gates) → 8–10. Prose where structure was needed, or missing gotchas/validation on
fragile flows → 4–6.
