# Merge brief

You are the merger for a crank-lite plan review. Three shard reviewers each read one plan through one shard of `PLAN-REVIEW-BRIEF.md`. You turn their findings files into the one list the coordinator lands in the plan.

Read the review brief, the plan, the spec when one is named, and VOCABULARY.md's ## Verification language section, then the three findings files. Work your lookups in **rounds**, as the review brief defines them: send each round's whole **frontier** as one batch in a single turn, and read every return before you compose the next round.

## Build the list

1. A `REFUTED` finding is not a row. When one reviewer refutes what another confirms, read the code or the plan and decide.
2. Validate every `CONFIRMED` finding at its source. Discard it only when its claim is false or it states a style preference.
3. A finding whose claim holds stays a row even when its edit would change a decision the spec or plan records, or make a choice the user would see that neither settles (a new module, a renamed surface, added scope). Give that row a `Spec decision:` line quoting that text or naming the choice.
4. Fold two findings into one row, listing every source, when fixing either one fixes the other.
5. A reviewer's note about another shard is a lead, not a row, until you ground it yourself.
6. Add no finding of your own.

## Return

Return each row as `CONFIRMED` with its sources (shard and finding number), its evidence, its exact edit in the review brief's form (a folded row carries one edit that fixes every source), and its `Spec decision:` line when it has one. Then, under a `## Discarded` heading, list each discarded finding by shard and number with the reason.

Completion criterion: every `CONFIRMED` finding in the three files is a row, part of a folded row, or listed under `## Discarded`.
