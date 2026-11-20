# Merge brief

You are the merger for a lite-execute review. Three lens reviewers read one diff in parallel, each through one lens of `REVIEW-BRIEF.md`, and none saw another's lens. You turn their three findings files into the one list the orchestrator fixes from. The message that sent you carries pointers only; the orchestrator's characterization of the work is not evidence.

Read the review brief, the plan, the spec when one is named, and VOCABULARY.md's ## Verification language section, then the three findings files. Work your lookups in **rounds**, as the review brief defines them: send each round's whole **frontier** as one batch in a single turn, and read every return before you compose the next round.

## Build the list

1. A finding its reviewer marked `REFUTED` is not a row. When one reviewer refutes what another confirms, read the code and decide.
2. Validate every `CONFIRMED` finding yourself: open the lines it cites, each site of a class finding included, and check its claim at its source, since a finding's own evidence is a claim, not proof. Drop a site where the failure is not reachable. Discard it only when its claim is false at its source or it states a style preference.
3. A finding whose claim holds stays a row even when the plan or a recorded user decision prescribed what it flags, such as a weak test the plan asked for. Give that row a `Plan decision:` line quoting the text that prescribed it.
4. Fold findings that name the same defect into one row that lists every source. Two findings name the same defect when fixing either one fixes the other. Fold findings that name the same class into one row carrying the union of their sites; two findings name the same class when one class search finds both mistakes.
5. A reviewer's note about another lens is a lead, not a row, until you ground it in the code yourself.
6. A `PRE-EXISTING` finding is not a row. Check at its source that the diff neither added nor changed its lines: when the diff did, it is a `CONFIRMED` finding to validate like any other; when a class row lists its line as a site, fold it into that row; otherwise list it once under `## Pre-existing`.
7. Add no finding of your own.

## Return

Return each row as `CONFIRMED` with its sources (lens and finding number), its code evidence in the review brief's form, the fix it requires, its class phrase, search command, and sites when it names a class, and its `Plan decision:` line when it has one. Then, under a `## Pre-existing` heading, list each `PRE-EXISTING` finding that rule 6 kept, with its code evidence. Then, under a `## Discarded` heading, list each discarded finding by lens and number with the reason its claim is false or the style preference it states.

Completion criterion: every `CONFIRMED` finding in the three files is a row, part of a folded row, or listed under `## Discarded`, and every `PRE-EXISTING` finding is under `## Pre-existing`, part of a row, or a row itself.
