# Judge template — blind scoring rubric for an A/B eval

> SCAFFOLDING NOTE — this is a template. Replace every `<<...>>` placeholder when copying
> it to an eval's `judges/judge.md`, then delete this note. Follow
> `references/authoring.md` → "Authoring a judge rubric": gold capture is ×3, the axis a
> change targets must be a scored dimension, version the rubric.

**Rubric version: <<vN>>** (<<date>>). <<One line on what this version scores and the
composite max; on a later change, note what moved and re-version.>>

You are the blind judge for the **<<EVAL NAME>>** eval. You score
**<<ARTIFACT TYPE — e.g. `spec.md` documents>>** that were each produced from the **same
topic** by two versions of the thing under test. You do NOT know which version produced
which artifact — score on merit only.

## Inputs (provided by the orchestrator)

- `{{JUDGE_DIR}}` — holds the shuffled, blind-labelled artifacts: `<<artifact>>-A`,
  `<<artifact>>-B`, … Score every artifact present.
- `{{BRIEF_PATH}}` — the topic's `user-brief.md`: topic + gold-answer key G1–Gn.
- `{{TARGET_REPO}}` — reference codebase, read-only, for sanity-checking paths.
- Do NOT read `{{JUDGE_DIR}}/mapping.md` — it decodes the blind labels.

## Step 1 — ground truth

Read `{{BRIEF_PATH}}`. The **G** items are the non-obvious correct decisions — the
primary signal. <<Add any other ground-truth inputs the artifact must satisfy.>>

## Step 2 — score each artifact on these dimensions (0–5, one sentence of justification)

1. **Gold capture (weight ×3)** — of G1–Gn, how many did the artifact get *correct*?
   Score = `round(5 × correct / n)`. List per artifact which G's are Correct / Wrong
   (decided the opposite way) / Missing (absent).
2. **<<Quality dimension>>** — <<criterion>>.
3. **<<Quality dimension>>** — <<criterion>>.
   <<… add the quality dimensions this eval needs; each ×1 …>>
N. **<<Targeted dimension, if a change targets a specific axis>>** — score from the
   objective sub-metric below using a deterministic anchor, e.g. `0 → 5, 1 → 3, 2 → 1,
   ≥3 → 0`. The axis a change targets MUST appear here as a scored dimension.

## Step 2b — objective sub-metrics (compute, report, and anchor the dimensions above)

- **<<Sub-metric>>** — <<exact countable definition>>. Anchors dimension <<N>>.
- **<<Sub-metric>>** — <<exact countable definition>>.

Report the raw counts; they are the deterministic anchor and stay interpretable alone.

## Step 3 — output

Write `{{JUDGE_DIR}}/scores.md`. Begin it with the line
`Rubric: <<vN>> (composite max <<M>>)`.

- Per-artifact table: rows = each label, columns = the dimensions + **Weighted total**
  (Gold ×3, others ×1; max = `<<5×3 + 5×(#other dimensions)>>`).
- A second table: rows = each artifact, columns = the raw Step 2b sub-metrics.
- Per artifact: the G Correct/Wrong/Missing breakdown + the one-sentence justifications.
- A "Notable differences" paragraph: what consistently separates stronger from weaker
  artifacts.

Do not guess which arm is which. Score only the files in `{{JUDGE_DIR}}`.
