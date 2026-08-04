---
name: crank-review
description: Review a PR, commit range, or uncommitted changes into a short list of high-confidence findings, each independently validated.
disable-model-invocation: true
argument-hint: "[what to review] [optional focus, e.g. 'especially simplicity']"
---

# Review

## Goal

A short list of findings you'd stake your name on — each one a senior engineer would hold the merge for. Three questions drive every finding, defined in full in [REVIEW-BRIEF.md](REVIEW-BRIEF.md):

1. **Does this code do what it says, clearly?** — the contract in the names, types, and messages vs. what the implementation does.
2. **What can be deleted, consolidated, or refactored away?** — *how could this be simpler and still mean the same thing?*
3. **What edge case slips through?** — the empty, the boundary, the error path, the broken invariant.

Precision over coverage. A review of three real problems beats one of thirty nits — the nits spend the trust the three needed.

## Hard Rules

- **High-confidence only — every finding survives refutation.** A finding ships only after an independent validator tried to refute it and couldn't. "Might be an issue" is not a finding; cut it.
- **Not a linter.** Never raise what a compiler, type-checker, formatter, or linter already catches, nor a matter of taste (naming preference, ordering, "consider maybe"). Those are nits, and nits do not ship.
- **Bias toward deletion and consolidation — but never cut required behavior.** Prefer the finding that removes or unifies code over the one that merely rearranges it — collapsing parallel structures into one counts as deletion. Such a finding ships only when the validator confirms the code is redundant, unreachable, or that the simpler shape preserves the same observable behavior. Required behavior is never "unnecessary surface" — the brief's [_Never cut required behavior_](REVIEW-BRIEF.md) list names what that covers.
- **Read-only.** This skill reviews; it never edits, stages, commits, or mutates the tree. Fixes are a separate, approved step (see Flow → Report).
- **Subagents pull their own facts.** Hand each finder and validator pointers — the BASE SHA, the rubric path, the cited `file:line` — never your characterization of the diff or a defense of a finding. They form their own read; you pre-judge nothing.

## Flow

### 1. Scope the diff

From the argument, settle exactly what "the changes" are and pin a single BASE SHA plus one diff command that you and every subagent run. Three shapes:

- **PR** — `gh pr view <n> --json headRefName,baseRefName` then `gh pr diff <n>`; BASE = the merge-base with the PR's base branch. Also fetch the PR's **prior review** — `gh pr view <n> --json comments,reviews` plus inline thread comments via `gh api repos/{owner}/{repo}/pulls/<n>/comments`, and — since the REST comments don't carry it — each thread's **resolution state** via GraphQL (`gh api graphql` over `repository.pullRequest.reviewThreads.nodes { isResolved comments }`). Carry it all into step 4, every thread tagged resolved or unresolved.
- **Commit range / branch vs main** — `git diff main...HEAD` (three-dot: compares against the merge-base, so unrelated `main` commits don't pollute the diff). A given range like `A..B` works too.
- **Uncommitted** — `git diff HEAD` (staged + unstaged working-tree changes). The user's "branch with uncommitted changes" lands here; include it when uncommitted work is present.

Capture the commit list once — `git log <BASE>..HEAD --oneline` — for the oscillation walk (step 4). If the target is genuinely ambiguous (committed work *and* uncommitted changes both present), state which you're reviewing and why.

**Done when:** BASE SHA, the exact diff command, and the commit list are pinned and stated.

### 2. Find — fan out the finders

Spawn standard finders, each pointed at [REVIEW-BRIEF.md](REVIEW-BRIEF.md) and the BASE SHA, each running the diff itself. Default to two lenses, matching the driving questions:

- **Correctness & contract** — the brief's questions 1 and 3: does the code do what it says, and what edge case slips through.
- **Simplicity & deletion** — the brief's question 2: what to cut, consolidate, or refactor, per its Deletion, Magic strings, and smell-baseline sections.

Honor any focus in the argument (e.g. "especially simplicity") by weighting the lenses — but a focus never suppresses a high-confidence correctness finding. Each finder returns candidate findings only (`file:line`, the claim, why it matters, the smallest fix) — no prose review, no manufactured findings to fill a clean diff.

**Done when:** every finder has returned and you've deduped identical claims into one candidate each.

### 3. Validate — fan out the refuters

For each candidate, spawn a standard validator pointed at the same [REVIEW-BRIEF.md](REVIEW-BRIEF.md), the cited `file:line`, and the BASE SHA. Its job is to **refute**: read the actual code, decide whether the claim holds, and **default to REFUTED** when the evidence is thin, the complexity it wants cut turns out to be load-bearing, or the call is a matter of taste. A candidate survives only on a clear, code-grounded CONFIRMED.

This is the gate that turns a long candidate list into a short trustworthy one. Don't soften it — a finding you can't get an independent agent to confirm is a finding you shouldn't report.

**Done when:** every candidate carries a CONFIRMED or REFUTED verdict with its evidence.

### 4. Reconcile against prior review

The diff has already been reviewed once — by the commits that built it, and, for a PR, by its conversation. That settled ground is not yours to reopen or re-state. Two sources:

- **Commits — oscillation.** Walk the commit list from step 1. Flag any change in this diff that **reverses a recent prior commit** — a value flipped back, a guard an earlier commit added now removed, a fix undone. Confirm each pair by reading both commits (`git show <sha>`), not by message alone. Oscillation means a settled decision is being reopened: surface it as its own warning, and offer to record the decision in an ADR so the next review doesn't reopen it again.

- **PR threads (PR target only).** Read the prior review fetched in step 1. **A resolved thread is settled ground — note it as resolved and leave it closed; never re-investigate a resolved conversation or resurrect a finding it covers** (a maintainer already closed it, so reopening it is noise). For each **unresolved** thread, drop any surviving finding that **echoes** a point it raised or **reverses** a decision it settled — that ground is covered, and re-stating it is noise, like a nit; the one carve-out you keep or add is a **critical or blocking comment the current diff still hasn't addressed** (unintentionally ignored — verify against the diff, then surface it under question 1). Independent of resolution: a **bug the diff newly introduced** — including one introduced while responding to a comment — is never "settled"; surface it whether or not a thread on that code is resolved (it's a finder's catch, not a re-investigation of the thread).

**Done when:** commit reversals are confirmed against both commits; and, for a PR, the threads are read, resolved threads are noted and left closed (never re-investigated), echoed or settled points from unresolved threads are pruned from the findings, and any ignored-critical comment or newly introduced regression is surfaced.

### 5. Report

Render the validated review in this shape — survivors first (ordered by severity), then oscillation, then the refuted receipt so the filter stays visible:

```markdown
## Review — <target>

### Findings (<n>)
1. `<file:line>` — <what's wrong> · _<contract | deletion | edge>_ · **fix:** <smallest fix>
   <!-- tie a deletion finding to the deletion test or the code-judo move -->
<!-- if none: "No high-confidence findings — the diff is clean." -->

### Oscillation
- `<sha>`→`<sha>`: <settled decision the diff reopens> — offer an ADR
<!-- a thread-settled reversal names the decision in place of a SHA pair; if none: "None." -->

### Refuted (<n>)
- `<file:line>` — <why the validator killed it, or "already covered in PR thread">
```

Then **recommend the handoff**: suggest the user run `/crank plan` to turn the surviving findings into a fix plan. Make no edits without approval.

**Done when:** the report is rendered in this shape and the handoff is offered.

## References

### Subagents

This skill spawns finders and validators at the **standard** tier — resolve it to your harness (Claude Code / Codex / Cursor) per [SUBAGENT-TIERS.md](SUBAGENT-TIERS.md). Bias toward dispatch: each finder and validator gets a clean, fresh context and sees the diff with fresh eyes, which is the whole point of independent validation. **Fan out in small waves** — a handful of concurrent spawns at a time, letting one wave return before launching the next; a large concurrent burst (one validator per candidate on a big diff) trips transient API errors. (Step 4's reconciliation — the oscillation walk and, for a PR, the thread read — is a factual read; keep it on-thread or dispatch one standard agent, your call.)

### Vocabulary

Shared crank design language, defined once in [VOCABULARY.md](VOCABULARY.md). This skill leans on the **deletion test**, **depth**, **spaghetti growth**, **bespoke duplication**, **boundary smells**, the **seam**, and the **implementation-detail test** — read their meanings there.

### Review rubric

The fixed rubric every finder and validator applies — the three questions, the high-confidence bar, the deletion bias, and the never-cut list — lives in [REVIEW-BRIEF.md](REVIEW-BRIEF.md). Point each subagent at it; don't reproduce it in the dispatch.
