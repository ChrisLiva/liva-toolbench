# Merge brief

You are the merger for a crank-lite plan review. Three shard reviewers read one plan in parallel, each through one shard of `PLAN-REVIEW-BRIEF.md`, and none saw another's shard. You turn their three findings files into the one list the coordinator lands in the plan. The message that sent you carries pointers only.

Read the review brief, the plan, the spec when one is named, and VOCABULARY.md's ## Verification language section, then the three findings files. Work your lookups in **rounds**, as the review brief defines them: send each round's whole **frontier** as one batch in a single turn, and read every return before you compose the next round.

## Build the list

1. A finding its reviewer marked `REFUTED` is not a row. When one reviewer refutes what another confirms, read the code or the plan and decide.
2. Validate every `CONFIRMED` finding yourself: open the lines it cites and check its claim at its source, since a finding's own evidence is a claim, not proof. Discard it only when its claim is false at its source or it states a style preference.
3. A finding whose claim holds stays a row even when its edit would change a decision the spec records or a user decision the plan records, or would make a choice the user would see that neither settles (a new module, a renamed surface, added scope). Give that row a `Spec decision:` line quoting that text, or naming the choice it makes, since the coordinator puts it to the user.
4. Fold findings that name the same defect into one row that lists every source. Two findings name the same defect when fixing either one fixes the other.
5. A reviewer's note about another shard is a lead, not a row, until you ground it in the plan or the code yourself.
6. Add no finding of your own.

## Return

Return each row as `CONFIRMED` with its sources (shard and finding number), its evidence and its exact edit in the review brief's form (a folded row carries one edit, `old` to `new`, that fixes every source), and its `Spec decision:` line when it has one. Then, under a `## Discarded` heading, list each discarded finding by shard and number with the reason its claim is false or the style preference it states.

Completion criterion: every `CONFIRMED` finding in the three files is a row, part of a folded row, or listed under `## Discarded`.
