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

From the argument, settle exactly what "the changes" are. Three target shapes:

- **PR** — `gh pr diff <n>`; on a forge `gh` does not serve, the forge tool the project names, else the branch diff against the PR's base. BASE = the merge-base with the PR's base branch. Ask before reviewing local commits the PR's head lacks. Don't re-raise what the PR's existing review threads settled.
- **Commit range / branch vs main** — `git diff main...HEAD` (three-dot, so unrelated `main` commits stay out of the diff). A given range like `A..B` works too.
- **Uncommitted** — `git diff HEAD`, plus untracked files from `git status --short` read in full — `git diff` never shows them.

If the target is ambiguous (committed work *and* uncommitted changes both present), state which you're reviewing and why.

**Done when:** one BASE SHA and the one diff command the whole run uses (with the untracked-files read for the uncommitted shape) are pinned and stated, before finding starts.

## Find

Find candidates yourself — no finder subagents. Read the diff through two lenses: **correctness & contract** (questions 1 and 3) and **simplicity & deletion** (question 2).

Honor any focus in the argument (e.g. "especially simplicity") by weighting the lenses — but a focus never suppresses a correctness finding. Each candidate carries `file:line`, the claim, why it matters, and the smallest fix.

## Rubric

Read [VOCABULARY.md](VOCABULARY.md) for the working language: the **deletion test**, **spaghetti growth**, the **seam**, the **redundant test**. The bar every candidate is judged against:

- Never raise what a compiler, type-checker, formatter, or linter already catches, nor a matter of taste.
- A deletion or consolidation finding passes the **deletion test**: the complexity it removes concentrates rather than reappearing across callers.
- **Never cut required behavior.** Trust-boundary validation, data-loss and error paths, security checks, and accessibility are never "unnecessary surface", however simple their removal would make the code.

## Validate

Dispatch **one** heavy-tier subagent (see Subagent tiers) to adversarially validate the whole candidate list. Hand it pointers — the BASE SHA, the diff command, each candidate's `file:line` and claim — never your characterization of the code or a defense of a finding; it runs the diff and reads the cited code itself. Tell it to work its lookups in **rounds**: a round's **frontier** is every lookup whose answer it does not need before issuing the next one, and the whole frontier goes out as one batch in a single turn, every return read before it composes the next round.

Its job is to **refute**: for each candidate, decide whether the claim holds and **default to REFUTED** when the evidence is thin, the complexity a cut targets turns out to be load-bearing, or the call is a matter of taste. Every candidate leaves this step carrying a CONFIRMED or REFUTED verdict with its code evidence; only CONFIRMED findings ship.

## Report

Render the validated review, findings ordered by severity:

```markdown
## Review — <target>

1. `<file:line>` — <what's wrong> · **fix:** <smallest fix>
<!-- if none: "No validated findings — the diff is clean." -->

Refuted: <n> candidate(s) killed in validation.
```

Then offer to apply the small fixes in-session on the user's approval, and recommend `/crank-lite plan` for any finding that implies design work rather than a spot fix.

## Subagent tiers

Resolve the heavy tier:

1. A subagent model preference stated in the user instructions already loaded this session (user- and project-level `CLAUDE.md` / `AGENTS.md`) is binding: map the tier onto it, even when it names a weaker model than the fallback below.
2. Otherwise, use this fallback:

<subagent-tiers>
- **heavy** fallback (adversarial validation): Claude Code `model: opus` · Codex Sol at high effort · Cursor Sol at high effort
</subagent-tiers>
