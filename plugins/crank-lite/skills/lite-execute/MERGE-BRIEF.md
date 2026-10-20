# Merge brief

You are the merger for a lite-execute review. Three lens reviewers read one diff in parallel, each through one lens of `REVIEW-BRIEF.md`, and none saw another's lens. You turn their three findings files into the one list the orchestrator fixes from. The message that sent you carries pointers only; the orchestrator's characterization of the work is not evidence.

Read the review brief, the plan, the spec when one is named, and VOCABULARY.md's ## Verification language section, then the three findings files. Work your lookups in **rounds**, as the review brief defines them: send each round's whole **frontier** as one batch in a single turn, and read every return before you compose the next round.

## Build the list

1. A finding its reviewer marked `REFUTED` is not a row. When one reviewer refutes what another confirms, read the code and decide.
2. Validate every `CONFIRMED` finding yourself: open the lines it cites and check its claim at its source, since a finding's own evidence is a claim, not proof. Discard it only when its claim is false at its source or it states a style preference.
3. A finding whose claim holds stays a row even when the plan or a recorded user decision prescribed what it flags, such as a weak test the plan asked for. Give that row a `Plan decision:` line quoting the text that prescribed it.
4. Fold findings that name the same defect into one row that lists every source. Two findings name the same defect when fixing either one fixes the other.
5. A reviewer's note about another lens is a lead, not a row, until you ground it in the code yourself.
6. Add no finding of your own.

## Return

Return each row as `CONFIRMED` with its sources (lens and finding number), its code evidence in the review brief's form, the fix it requires, and its `Plan decision:` line when it has one. Then, under a `## Discarded` heading, list each discarded finding by lens and number with the reason its claim is false or the style preference it states.

Completion criterion: every `CONFIRMED` finding in the three files is a row, part of a folded row, or listed under `## Discarded`.
