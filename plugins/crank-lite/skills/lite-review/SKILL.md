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

Find candidates yourself — no finder subagents. Read the repo's own rules as they stood at BASE, each with `git show <BASE>:<path>`: `REVIEW.md`, `CLAUDE.md`, and `AGENTS.md` at the repository root and in each directory above a changed file. A file absent at BASE yields nothing and no finding. For a symlink at BASE (mode `120000` in `git ls-tree <BASE> <path>`), `git show` prints only its target's name: read that target with `git show <BASE>:<target>`, and count a file you reach twice once. (per project decision: reviewers read `REVIEW.md` as it stood at BASE, so a diff cannot change its own review, while a rule the diff rewrites in `CLAUDE.md` or `AGENTS.md` governs the diff's code, because a convention and the code that follows it often change in one diff, 2026-11-19.)

Read the diff through three lenses: **correctness & contract** (questions 1 and 3), **simplicity & deletion** (question 2), and **security** (question 4), where you read the diff as an attacker would, following each value that arrives from outside the code's trust to where it lands. (per project decision: the security lens is a third read on the main thread, so the run keeps its one dispatch, 2026-11-19.)

Honor any focus in the argument (e.g. "especially simplicity") by weighting the lenses — but a focus never suppresses a correctness finding or a confirmed security finding; only a skip in the repo's `REVIEW.md` does. Each candidate carries `file:line`, the claim, why it matters, and the smallest fix.

For each defect you find whose cause is code a search can find, such as a condition, a call, a literal, or a missing guard, run one repo-wide search for that code before you treat the defect as a one-off: only the search shows whether it is a repeatable mistake. Read each hit and judge it against what the code around it promises (its name, its help or doc text, its tests, what its callers expect), not against this diff's task. Code that stood before the diff is not correct for having stood, so a hit on lines the diff did not touch gets the same probe. A hit where the same failure is reachable is a **site**; any other hit is not. A defect with a site beyond its own line gets a **class**: one phrase naming the mistake by what the code does, not the requirement it breaks, and that search as a single shell command whose output lists each hit as `file:line`. List every site in the same candidate, each as `file:line`; a site on lines the diff did not touch is fixed with the rest. (per project decision: every defect with a searchable cause gets the search, not only one the reviewer judges repeatable, because on two Sonnet runs of the `review` smoke seed the reviewers left a second site, on lines the diff never touched, unfixed, 2026-11-20.)

A **pre-existing** defect sits on lines the diff neither added nor changed and is not a site of a class candidate; a defect the diff makes newly reachable is the diff's own finding. Note one only when you meet it while reading the symbols the diff changes or calls on its changed lines, never by searching for one, and mark its candidate `pre-existing`.

When the target has a commit or PR message that presents the diff as a fix, find the cause that message names: a diff that guards the symptom at one call site while the cause stays reachable from another caller is a candidate that cites the cause's `file:line`.

## Rubric

Read [VOCABULARY.md](VOCABULARY.md) for the working language: the **deletion test**, **spaghetti growth**, the **seam**, the **redundant test**. The bar every candidate is judged against:

- Never raise what a compiler, type-checker, formatter, or linter already catches, nor a matter of taste.
- A deletion or consolidation finding passes the **deletion test**: the complexity it removes concentrates rather than reappearing across callers.
- A security finding answers question 4 and cites two `file:line` anchors, its cause and where it lands: outside input reaching an interpreter unescaped (SQL, shell, markup, file path, deserializer), cited from where the input enters to the sink it reaches; an entry point that acts without the authentication or ownership check its sibling entry points apply, cited with the check its sibling applies; a secret or personal data (a password, a credential, a key) written to a log, an error message, a URL, or the repo, cited from where the value is read to where it is written; a protection the diff weakens, cited from the changed line to a path it no longer guards; code fetched or installed from an unpinned or unverified source, cited from the fetch or install line to the line that runs what it fetched.
- No security finding: hardening with no reachable path, a missing rate limit, a risk that exists only in test fixtures, and input from a caller the code already trusts.
- A diff line that breaks a rule the repo's `REVIEW.md`, `CLAUDE.md`, or `AGENTS.md` states is a finding that cites the rule's file and heading and the breaching `file:line`.
- A path or a class of finding that `REVIEW.md` says to skip is not reported. A check `REVIEW.md` adds is applied, even where this rubric would call its subject taste, and its findings are grounded in the code and validated like any other.
- A rule the diff adds or rewrites in `CLAUDE.md` or `AGENTS.md`, including in a file the diff adds, governs the diff's code: judge the code against the text the diff leaves. No change the diff makes to `REVIEW.md`, a new file included, affects this review.
- **Never cut required behavior.** Trust-boundary validation, data-loss and error paths, security checks, and accessibility are never "unnecessary surface", however simple their removal would make the code.

## Validate

Dispatch **one** heavy-tier subagent (see Subagent tiers) to adversarially validate the whole candidate list. Hand it pointers — the BASE SHA, the diff command, each candidate's `file:line` and claim, with a class candidate's phrase, search command, and sites, and a candidate's `pre-existing` mark — never your characterization of the code, a defense of a finding, or a rule file's path or text; it runs the diff and reads the cited code itself. Tell it to read the repo's rules itself the way Find reads them, from BASE with `git show`, and to judge each candidate against them by this rubric's three rule lines. Tell it to work its lookups in **rounds**: a round's **frontier** is every lookup whose answer it does not need before issuing the next one, and the whole frontier goes out as one batch in a single turn, every return read before it composes the next round.

Its job is to **refute**: for each candidate, decide whether the claim holds and **default to REFUTED** when the evidence is thin, the complexity a cut targets turns out to be load-bearing, or the call is a matter of taste. For a class candidate it reads every listed site and confirms or drops each one: a site stays only when the same failure is reachable there, judged against what the code at the site promises and not against the diff's task. For a candidate marked `pre-existing` it confirms the defect and that the diff neither added nor changed its lines. Every candidate leaves this step carrying a CONFIRMED or REFUTED verdict with its code evidence; only CONFIRMED findings ship.

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
