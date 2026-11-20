---
name: lite-review
description: Review a PR, commit range, or uncommitted changes into a short list of validated findings, then offer to apply the fixes.
argument-hint: "[what to review] [optional focus]"
disable-model-invocation: true
---

# Lite Review

## Goal

A short list of findings a senior engineer would hold the merge for. Four questions drive every finding:

1. **Does this code do what it says, clearly?**
2. **What can be deleted, consolidated, or refactored away?**
3. **What edge case slips through?**
4. **What can an attacker make it do?**

Precision over coverage: three real problems beat thirty nits. The run is read-only until the user approves fixes.

## Scope

From the argument, settle exactly what "the changes" are. Three target shapes:

- **PR** — `gh pr diff <n>`; on a forge `gh` does not serve, the forge tool the project names, else the branch diff against the PR's base. BASE = the merge-base with the PR's base branch. Ask before reviewing local commits the PR's head lacks. Don't re-raise what the PR's existing review threads settled.
- **Commit range / branch vs main** — `git diff main...HEAD` (three-dot, so unrelated `main` commits stay out of the diff). A given range like `A..B` works too.
- **Uncommitted** — `git diff HEAD`, plus untracked files from `git status --short` read in full — `git diff` never shows them.

If the target is ambiguous (committed work *and* uncommitted changes both present), state which you're reviewing and why.

**Done when:** one BASE SHA and the one diff command the whole run uses (with the untracked-files read for the uncommitted shape) are pinned and stated, before finding starts.

## Find

Find candidates yourself — no finder subagents. Read the diff through three lenses: **correctness & contract** (questions 1 and 3), **simplicity & deletion** (question 2), and **security** (question 4), where you read the diff as an attacker would, following each value that arrives from outside the code's trust to where it lands. (per project decision: the security lens is a third read on the main thread, so the run keeps its one dispatch, 2026-11-19.)

Honor any focus in the argument (e.g. "especially simplicity") by weighting the lenses — but a focus never suppresses a correctness finding or a confirmed security finding. Each candidate carries `file:line`, the claim, why it matters, and the smallest fix.

A defect that is one instance of a repeatable mistake gets a **class**: one phrase naming the mistake, and the one repo-wide search that finds its instances, written as a single shell command whose output lists each hit as `file:line`. Run that search, read each hit, and list in the same candidate every **site**, each as `file:line`: a hit where the same failure is reachable. A hit where the failure is not reachable is not a site, and a site on lines the diff did not touch stays in the candidate and is fixed with it.

A **pre-existing** defect sits on lines the diff neither added nor changed and is not a site of a class candidate; a defect the diff makes newly reachable is the diff's own finding. Note one only when you meet it while reading the symbols the diff changes or calls on its changed lines, never by searching for one, and mark its candidate `pre-existing`.

When the target has a commit or PR message that presents the diff as a fix, find the cause that message names: a diff that guards the symptom at one call site while the cause stays reachable from another caller is a candidate that cites the cause's `file:line`.

## Rubric

Read [VOCABULARY.md](VOCABULARY.md) for the working language: the **deletion test**, **spaghetti growth**, the **seam**, the **redundant test**. The bar every candidate is judged against:

- Never raise what a compiler, type-checker, formatter, or linter already catches, nor a matter of taste.
- A deletion or consolidation finding passes the **deletion test**: the complexity it removes concentrates rather than reappearing across callers.
- A security finding answers question 4 and cites two `file:line` anchors, its cause and where it lands: outside input reaching an interpreter unescaped (SQL, shell, markup, file path, deserializer), cited from where the input enters to the sink it reaches; an entry point that acts without the authentication or ownership check its sibling entry points apply, cited with the check its sibling applies; a secret or personal data (a password, a credential, a key) written to a log, an error message, a URL, or the repo, cited from where the value is read to where it is written; a protection the diff weakens, cited from the changed line to a path it no longer guards; code fetched or installed from an unpinned or unverified source, cited from the fetch or install line to the line that runs what it fetched.
- No security finding: hardening with no reachable path, a missing rate limit, a risk that exists only in test fixtures, and input from a caller the code already trusts.
- **Never cut required behavior.** Trust-boundary validation, data-loss and error paths, security checks, and accessibility are never "unnecessary surface", however simple their removal would make the code.

## Validate

Dispatch **one** heavy-tier subagent (see Subagent tiers) to adversarially validate the whole candidate list. Hand it pointers — the BASE SHA, the diff command, each candidate's `file:line` and claim, with a class candidate's phrase, search command, and sites, and a candidate's `pre-existing` mark — never your characterization of the code or a defense of a finding; it runs the diff and reads the cited code itself. Tell it to work its lookups in **rounds**: a round's **frontier** is every lookup whose answer it does not need before issuing the next one, and the whole frontier goes out as one batch in a single turn, every return read before it composes the next round.

Its job is to **refute**: for each candidate, decide whether the claim holds and **default to REFUTED** when the evidence is thin, the complexity a cut targets turns out to be load-bearing, or the call is a matter of taste. For a class candidate it reads every listed site and confirms or drops each one: a site stays only when the same failure is reachable there. For a candidate marked `pre-existing` it confirms the defect and that the diff neither added nor changed its lines. Every candidate leaves this step carrying a CONFIRMED or REFUTED verdict with its code evidence; only CONFIRMED findings ship.

## Report

Render the validated review, findings ordered by severity:

```markdown
## Review — <target>

1. `<file:line>` — <what's wrong> · **fix:** <smallest fix>
   sites: `<file:line>`, `<file:line>` <!-- a class finding only: every confirmed site -->
<!-- if none: "No validated findings — the diff is clean." -->

Pre-existing: `<file:line>` — <what's wrong>
<!-- one line per validated pre-existing defect, after the numbered findings; leave the line out when there is none -->

Refuted: <n> candidate(s) killed in validation.
```

Then offer to apply the small fixes in-session on the user's approval, a class finding's fix covering every confirmed site, name the pre-existing defects as a separate choice, since the diff did not introduce them, and recommend `/crank-lite plan` for any finding that implies design work rather than a spot fix.

## Subagent tiers

Resolve the heavy tier:

1. A subagent model preference stated in the user instructions already loaded this session (user- and project-level `CLAUDE.md` / `AGENTS.md`) is binding: map the tier onto it, even when it names a weaker model than the fallback below.
2. Otherwise, use this fallback:

<subagent-tiers>
- **heavy** fallback (adversarial validation): Claude Code `model: opus` · Codex Sol at high effort · Cursor Sol at high effort
</subagent-tiers>
