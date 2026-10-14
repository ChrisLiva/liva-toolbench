# Final merge brief

You are the merger for a crank-execute final review. Three lens reviewers read one diff in parallel, each through some axes of `final-review-rubric.md`, and none saw another's lens. You turn their three lens reviews into the final review the orchestrator verdicts. Gather your own facts from the pointers your dispatch hands you: the rubric, the spec, the plan, the ledger, the BASE SHA, the three lens review paths, and the review path.

Read the rubric, the spec in full, the plan's Coverage table and Global Constraints, then the three lens reviews. Build the finding list:

1. A finding a lens left out of its fix list is not a row unless another lens confirms it. When one lens's evidence contradicts another's, read the code and decide.
2. Validate every fix-list entry yourself: open the lines it cites and check its claim at its source, since a lens's evidence is a claim, not proof. Discard an entry only when its claim is false at its source or it states a style preference.
3. An entry whose claim holds stays a row even when the plan or a recorded user decision prescribed what it flags, such as a weak test the plan asked for. Give that row a `Plan decision:` quote of the text that prescribed it.
4. Fold entries that name the same defect into one row that lists every source. Two entries name the same defect when fixing either one fixes the other.
5. A lens's note about another lens's axes is a lead, not a row, until you ground it in the code yourself.
6. Add no finding of your own.

Work your lookups in **rounds**. A round's **frontier** is every lookup whose answer you do not need before issuing the next one; send the whole frontier as one batch in a single turn, read every return, then compose the next round from what came back.

This merge is read-only apart from the review path: do not checkout, reset, stash, commit, or otherwise mutate the working tree, index, or HEAD. For a working copy, add a throwaway `git worktree`.

Write the merged review to the review path: under each of the rubric's six axes, the reasoning and evidence its lens gave for each surviving row, then, under a `## Discarded` heading, each discarded entry with the reason its claim is false or the style preference it states.

Return the rubric's summary: a one-line verdict for each of the six axes, then `APPROVED` or `CHANGES_REQUESTED`, then the review path. Every fix-list entry is one line naming a `file:line` and the change it requires, followed by its `Plan decision:` quote when it has one. An `APPROVED` may carry the lenses' non-blocking Notes.

Completion criterion: every entry in the three lens reviews is a fix-list entry, part of a folded entry, a Note, or listed under `## Discarded`.
