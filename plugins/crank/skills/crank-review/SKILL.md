---
name: crank-review
description: Review a PR, commit range, or uncommitted changes into a short list of high-confidence findings, each independently validated.
disable-model-invocation: true
argument-hint: "[what to review] [optional focus, e.g. 'especially simplicity']"
---

# Review

## Goal

A short list of findings, each one a senior engineer would hold the merge for. Three questions drive every finding, defined in [REVIEW-BRIEF.md](REVIEW-BRIEF.md):

1. **Does this code do what it says, clearly?**
2. **What can be deleted, consolidated, or refactored away?**
3. **What edge case slips through?**

Precision over coverage. Each nit spends trust the real findings need.

## Hard Rules

- **High-confidence only.** A finding ships only after an independent validator tried to refute it and couldn't; "might be an issue" is not a finding.
- **Not a linter.** A nit, anything a compiler, type-checker, formatter, or linter catches, or a matter of taste (naming preference, ordering, "consider maybe"), never ships.
- **Bias toward deletion and consolidation, never past required behavior.** Collapsing parallel structures into one counts as deletion. The brief's [_Never cut required behavior_](REVIEW-BRIEF.md) section lists what required behavior covers.
- **Read-only.** Never edit, stage, commit, or otherwise mutate the tree; fixes are a separate, approved step after the report.
- **Subagents pull their own facts.** A dispatch carries pointers only: the brief's path, the BASE SHA, the diff command with any untracked-files list, and either the finder's lens or the validator's one candidate, given as `file:line` and the claim as the finder worded it. Never add the rubric's text, your characterization of the diff, or a defense of a finding.

## Flow

### 1. Scope the diff

From the argument, pin one BASE SHA and one diff command that you and every subagent run. Three shapes:

- **PR.** `gh pr view <n> --json headRefName,baseRefName`, then `gh pr diff <n>`; BASE is the merge-base with the PR's base branch. Also fetch the PR's prior review: `gh pr view <n> --json comments,reviews` for the conversation, and the inline threads with their resolution state via `gh api graphql` over `repository.pullRequest.reviewThreads.nodes { isResolved path line comments }`. Carry both into step 4, every thread tagged resolved or unresolved.
- **Commit range or branch against main.** `git diff main...HEAD`, whose three dots diff against the merge-base so unrelated `main` commits stay out, or a given range like `A..B`.
- **Uncommitted.** `git diff HEAD` for staged and unstaged changes, plus the untracked files `git status --short` lists, read in full because `git diff` never shows them. The user's "branch with uncommitted changes" lands here; include it when uncommitted work is present.

Capture the commit list once with `git log <BASE>..HEAD --oneline` for step 4's oscillation walk. If the target is genuinely ambiguous, with committed and uncommitted work both present, state which you're reviewing and why.

**Done when:** you have stated the BASE SHA, the exact diff command, the untracked-files list for an uncommitted target, and the commit list.

### 2. Find

Spawn one standard-tier finder per lens, each with the pointers **Subagents pull their own facts** lists. Default lenses:

- **Correctness and contract.** The brief's questions 1 and 3.
- **Simplicity and deletion.** The brief's question 2 and the sections it points to.

A focus in the argument, such as "especially simplicity", weights the lenses, but a focus never suppresses a high-confidence correctness finding.

**Done when:** every finder has returned and you've deduped identical claims into one candidate each.

### 3. Validate

For each candidate, spawn a standard-tier validator with the pointers **Subagents pull their own facts** lists. Launch them in waves, each wave returning before the next starts. Each tries to **refute** its candidate on the defaults in the brief's [_If you are a validator_](REVIEW-BRIEF.md) section; only a code-grounded CONFIRMED survives.

**Done when:** every candidate carries a CONFIRMED or REFUTED verdict with its evidence.

### 4. Reconcile against prior review

- **Commits: oscillation.** Walk the commit list from step 1 and flag any change in this diff that **reverses a recent prior commit**: a value flipped back, a guard an earlier commit added now removed, a fix undone. Confirm each pair by reading both commits with `git show <sha>`, not by message alone. Report each reversal as its own warning, a settled decision reopened, and offer to record the decision in an ADR. A reversal of a decision an earlier PR thread settled goes under the same warning, named by the decision in place of a SHA pair, with no commit pair to confirm.

- **PR threads (PR target only).** Read the prior review fetched in step 1 and disposition each thread by its state:
  - **Resolved.** Settled: note it resolved, leave it closed, and drop any surviving finding it covers.
  - **Unresolved.** Drop a surviving finding that **echoes** a point it raised or **reverses** a decision it settled. The only exception to keep or add is a **critical or blocking comment the current diff still hasn't addressed** and has ignored unintentionally: verify it against the diff and surface it under question 1.
  - **Either state.** A **bug the diff newly introduced**, including one introduced while answering a comment, is never settled. Surface it as a finder's catch, not a reopened thread.

**Done when:** you have confirmed every reversal against both commits and, for a PR, closed, pruned, or surfaced every thread.

### 5. Report

Render the review in this shape, findings ordered by severity; the Refuted list shows the reader what validation and the PR threads removed:

```markdown
## Review — <target>

### Findings (<n>)
1. `<file:line>` — <what's wrong> · _<contract | deletion | edge>_ · **fix:** <smallest fix>
   <!-- tie a deletion finding to the deletion test or the code-judo move -->
<!-- if none: "No high-confidence findings." -->

### Oscillation
- `<sha>` reversed by `<sha>`: <settled decision the diff reopens>. Offer an ADR.
<!-- if none: "None." -->

### Refuted (<n>)
- `<file:line>` — <why the validator killed it, or "already covered in PR thread">
```

Then suggest the user run `/crank plan` to turn the surviving findings into a fix plan.

**Done when:** the report is rendered in this shape and the handoff is offered.

## References

### Subagents

Finders and validators run at the **standard** tier; resolve it per [SUBAGENT-TIERS.md](SUBAGENT-TIERS.md): a loaded instruction file's preference first, its harness models only as the fallback. Dispatch each one even on a small diff, because a fresh context that never saw your read of the diff is what makes validation independent. Step 4's oscillation walk and thread read are factual reads, not independent judgments, so they stay on the main thread.

### Vocabulary

[VOCABULARY.md](VOCABULARY.md) defines the brief's **deletion test**, **spaghetti growth**, **seam**, **implementation-detail test**, **redundant test**, and **journey test**. **Bespoke duplication** and **boundary smells** are review-specific smells the brief's Code judo section defines.
