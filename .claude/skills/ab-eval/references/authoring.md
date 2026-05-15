# Authoring topics and judge rubrics

How to author the two pieces of an eval that carry its signal: the **topic** (with its
gold-answer key) and the **judge rubric**. Read this when scaffolding.

## Authoring a topic

A **topic** is one scenario the thing under test runs against. It lives at
`topics/<topic>/user-brief.md` and is the **ground truth** the user-player answers from.
The `templates/user-brief.md` gives the structure; fill it as follows.

### The gold-answer key must be real

The gold key — `G1 … Gn` — is a list of **non-obvious correct decisions** a competent run
should reach. It is the primary signal. Every gold item must be **grounded in the real
target repo**: a real file path, a real symbol, a real table, a real documented decision.
**Never invent a path or symbol.** Spawn an `Explore` agent against the (read-only)
target repo to find genuine grounding before writing any gold item, and verify each
`path:line` reference directly.

A good gold item:

- States a decision and a one-line *why*.
- Is non-obvious — a naive run would plausibly get it wrong.
- Has a clearly correct answer the judge can check, not a matter of taste.

### Persona priorities

Below the gold key, give a short list of **persona priorities** — the stable preferences
the user-player uses to answer any question *not* in the gold key, and the only input the
replay fallback may use. Keep them decisive and consistent with the gold key.

### Consider an adversarial topic

An eval often cannot resolve a change because no topic *triggers* the failure mode the
change targets — both arms behave the same, so there is nothing to measure. Author at
least one **adversarial topic**: a scenario where the *tempting* decision is the *wrong*
one, so a weak run fails it and a strong run does not. Frame it honestly in the brief: it
measures "does the thing resist this failure mode *when the failure is tempting*", not
"is the candidate good in general". Writing a topic that *naturally* baits the failure
(rather than feeling engineered) is the hard part — mine real past artifacts that
genuinely exhibited the failure for an authentic example.

## Authoring a judge rubric

The judge (`judges/judge.md`, from `templates/judge.md`) blind-scores each artifact. Key
design rules:

### Weighted dimensions

Score each artifact on a handful of **0–5 dimensions**, each with one sentence of
justification. Make **gold capture** a dimension weighted **×3** — it is the correctness
axis: `score = round(5 × correct / n)`. The other dimensions are quality axes at ×1.

### Score the axis the change targets

If a change targets a specific axis X, that axis **must** be a weighted scored dimension
— otherwise the headline number barely moves and the eval reads zero for a real effect.
Do not leave the targeted metric as an unweighted "objective sub-metric". Two ways to get
a metric onto the headline:

- **Promote** it to a new weighted dimension, with a deterministic count→score anchor
  table (e.g. `0 → 5, 1 → 3, 2 → 1, ≥3 → 0`).
- **Anchor** an existing dimension to the raw count, if the metric already overlaps that
  dimension — anchoring avoids double-counting.

Still **report the raw objective counts** alongside the scores; they are the deterministic
anchor and stay interpretable on their own.

### Version the rubric

Any change to the dimensions or the composite max **re-versions the rubric** (`v1`,
`v2`, …). Put the version and the composite max in the judge file's header and have the
judge write `Rubric: vN (composite max M)` at the top of its `scores.md`. Scores from
different rubric versions are not directly comparable — versioning keeps old runs
interpretable.

### Blind output

The judge writes a `scores.md` with: a per-artifact table (dimensions + weighted total),
a second table of the raw objective counts, the per-artifact gold Correct/Wrong/Missing
breakdown, and a "notable differences" paragraph. It must not guess which arm is which.
