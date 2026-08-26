---
name: lite-review
description: Review a PR, commit range, or uncommitted changes into a short list of validated findings, then offer to apply the fixes.
argument-hint: "[what to review] [optional focus]"
disable-model-invocation: true
---

# Lite Review

## Goal

A short list of findings a senior engineer would hold the merge for. Three questions drive every finding:

1. **Does this code do what it says, clearly?**
2. **What can be deleted, consolidated, or refactored away?**
3. **What edge case slips through?**

Precision over coverage: three real problems beat thirty nits. The run is read-only until the user approves fixes.

## Scope

From the argument, settle exactly what "the changes" are, and pin a single BASE SHA plus the one diff command the whole run uses. Three target shapes:

- **PR** — `gh pr diff <n>` for the changes; BASE = the merge-base with the PR's base branch. Skim the PR's existing review threads and don't re-raise what's settled there.
- **Commit range / branch vs main** — `git diff main...HEAD` (three-dot: compares against the merge-base, so unrelated `main` commits don't pollute the diff). A given range like `A..B` works too.
- **Uncommitted** — `git diff HEAD`, plus untracked files from `git status --short` read in full — `git diff` never shows them.

If the target is genuinely ambiguous (committed work *and* uncommitted changes both present), state which you're reviewing and why.

**Done when:** one BASE SHA and the exact diff command (with the untracked-files read for the uncommitted shape) are pinned and stated, before finding starts.

## Find

Find candidates yourself, on this thread — no finder subagents. Read the diff through two lenses, matching the driving questions:

- **Correctness & contract** — questions 1 and 3: does the code do what it says, and what edge case slips through.
- **Simplicity & deletion** — question 2: what to cut, consolidate, or refactor away.

Honor any focus in the argument (e.g. "especially simplicity") by weighting the lenses — but a focus never suppresses a correctness finding. Each candidate carries `file:line`, the claim, why it matters, and the smallest fix.

## Rubric

Read [VOCABULARY.md](VOCABULARY.md) for the working language: the **deletion test**, **spaghetti growth**, the **seam**, the **redundant test**. The bar every candidate is judged against:

- The three driving questions are the only sources of findings. Never raise what a compiler, type-checker, formatter, or linter already catches, nor a matter of taste.
- A deletion or consolidation finding passes the **deletion test**: the complexity it removes concentrates rather than reappearing across callers.
- **Never cut required behavior.** Trust-boundary validation, data-loss and error paths, security checks, and accessibility are never "unnecessary surface", however simple their removal would make the code.

## Validate

Dispatch **one** heavy-tier subagent (see Subagent tiers) to adversarially validate the whole candidate list in a single pass. Hand it pointers — the BASE SHA, the diff command, each candidate's `file:line` and claim — never your characterization of the code or a defense of a finding; it runs the diff and reads the cited code itself, forming its own view.

Its job is to **refute**: for each candidate, decide whether the claim holds and **default to REFUTED** when the evidence is thin, the complexity a cut targets turns out to be load-bearing, or the call is a matter of taste. A candidate survives only on clear, code-grounded evidence, never on plausibility; only CONFIRMED findings ship. Every candidate leaves this step carrying a CONFIRMED or REFUTED verdict with its evidence.

## Report

Render the validated review — findings first, ordered by severity, then the refuted receipt so the filter stays visible:

```markdown
## Review — <target>

1. `<file:line>` — <what's wrong> · **fix:** <smallest fix>
<!-- if none: "No validated findings — the diff is clean." -->

Refuted: <n> candidate(s) killed in validation.
```

Then offer the next step: apply the small fixes in-session on the user's approval, and recommend `/crank-lite plan` for any finding that implies design work rather than a spot fix. Make no edits without approval.

## Subagent tiers

Resolve the tier once per run and reuse it. A subagent model preference stated in the user instructions already loaded this session (user- and project-level `CLAUDE.md` / `AGENTS.md`) is binding: map the tier onto it, even when it names a weaker model than the fallback below. With no such preference stated, use your harness's fallback:

<subagent-tiers>
- **heavy** (adversarial validation): Claude Code `model: opus` · Codex GPT-5.6-Sol at high effort · Cursor GPT-5.6-Sol at high effort
</subagent-tiers>
