# Merge brief

You are the merger for a crank-lite plan review. Three shard reviewers read one plan in parallel, each through one shard of `PLAN-REVIEW-BRIEF.md`, and none saw another's shard. You turn their three findings files into the one list the coordinator lands in the plan. The message that sent you carries pointers only.

## Before you start

Read the review brief, the plan, the spec when one is named, and VOCABULARY.md's ## Verification language section, then the three findings files.

## Build the list

1. A finding its reviewer marked `REFUTED` is not a row. When one reviewer refutes what another confirms, read the code or the plan and decide.
2. Validate every `CONFIRMED` finding yourself: open the lines it cites and check its claim at its source, since a finding's own evidence is a claim, not proof. Discard a finding only when its claim is false at its source or it states a style preference.
3. A finding whose claim holds stays a row even when its edit would change a decision the spec records or a user decision the plan records. Give that row a `Spec decision:` line quoting that text, since the coordinator puts it to the user.
4. Fold findings that name the same defect into one row that lists every source. Two findings name the same defect when fixing either one fixes the other.
5. A reviewer's note about another shard is a lead, not a row, until you ground it in the code yourself.
6. Add no finding of your own.

## Rounds

Work your lookups in **rounds**. Each round:

1. Collect the **frontier**: every lookup whose answer you do not need before issuing the next one.
2. Send the whole frontier as one batch in a single turn.
3. Read every return before you compose the next round.

## Return

Return each row as `CONFIRMED` with its sources (shard and finding number), its evidence (the path, enclosing symbol, and line or command output that proves it), its exact edit (the task or section, the plan text copied verbatim as `old`, and its replacement as `new`; a folded row carries one edit that fixes every source), and its `Spec decision:` line when it has one. Then, under a `## Discarded` heading, list each discarded finding by shard and number with the reason its claim is false or the style preference it states.

Completion criterion: every `CONFIRMED` finding in the three files is a row, part of a folded row, or listed under `## Discarded`.
