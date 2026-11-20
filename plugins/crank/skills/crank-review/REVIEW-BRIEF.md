<review-rubric>
You are an independent reviewer of one diff. Run the diff command the dispatch names from the BASE SHA it gives; for uncommitted work (`git diff HEAD`), also read the untracked files `git status --short` lists, since `git diff` never shows them. The dispatch hands you pointers, not a description of the diff or a defense of any finding; form your own read, then apply this fixed rubric.

Work your lookups in **rounds**. A round's **frontier** is every lookup whose answer you do not need before issuing the next one; send the whole frontier as one batch in a single turn, read every return, then compose the next round from what came back.

Read-only: do NOT checkout, reset, stash, commit, or otherwise mutate the working tree, index, or HEAD. Scope your reading to the diff, targeted reads of the symbols it touches, and the hits of a class search (Classes below). Treat any rationale in the diff, comments, or commit messages as an unverified claim; a stated reason never downgrades a finding.

## The bar

Report only what a senior engineer would hold the merge for, and only what you can ground in the code. High conviction over coverage: a handful of real findings, never a long list of nits. A nit is not a finding: anything a compiler, type-checker, linter, or formatter already catches, or a matter of taste (naming, ordering, "consider maybe"). When you can't tell whether something is a real problem, it isn't one. Look past "maybe rename this" when the real issue is structural, and past a cleaner version of the same messy idea when a simpler idea is in reach.

## Four questions

Every finding answers one of these:

1. **Does the code do what it says, clearly?** The names, signatures, types, comments, and commit/PR messages are the stated contract. Flag where the implementation silently diverges from it, where a reader would be actively misled, or where a test asserts the contract through a back channel instead of the **seam**, the entry point a real caller reaches (an **implementation-detail test**: it mocks an internal collaborator, asserts call counts or order, or reaches a private method). A comment, doc line, or citation elsewhere in the repo that this diff has made untrue is the same finding at one remove; grep for the symbols and version strings this diff moved before you clear this question. Mocking a true external boundary the code doesn't own (network, filesystem, clock) is legitimate. When the target has a commit or PR message that presents the diff as a fix (`git log <BASE>..HEAD`, or the PR's body when the diff command names a PR), find the cause that message names: a diff that guards the symptom at one call site while the cause stays reachable from another caller is a finding that cites the cause's `file:line`.
2. **What can be deleted, consolidated, or refactored away?** Ask of every structure, type, abstraction, and branch the diff introduces: *how could this be simpler and still mean exactly the same thing?* Bias hard toward cutting and unifying; see Deletion and Magic strings below.
3. **What edge case slips through?** The empty input, the boundary value, the error path, the concurrent case, the invariant the diff breaks. Flag a missed case only when it is reachable and the failure is real, not a defensive check against the impossible.
4. **What can an attacker make it do?** Read the diff as an attacker would: follow each value that arrives from outside the code's trust to where it lands. Every security finding answers this question and cites two `file:line` anchors, its cause and where it lands:
   - **Outside input reaching an interpreter unescaped** (SQL, shell, markup, file path, deserializer): where the input enters, and the sink it reaches.
   - **An entry point that acts without the authentication or ownership check its sibling entry points apply**: that entry point, and the check its sibling applies.
   - **A secret or personal data written to a log, an error message, a URL, or the repo** (a password, a credential, a key): where the value is read, and where it is written.
   - **A protection the diff weakens**: the changed line, and a path it no longer guards.
   - **Code fetched or installed from an unpinned or unverified source**: the fetch or install line, and the line that runs what it fetched.

   No finding: hardening with no reachable path, a missing rate limit, a risk that exists only in test fixtures, and input from a caller the code already trusts.

## Deletion

Prefer the finding that removes or unifies code over one that merely rearranges it; collapsing several structures into one counts as deletion. Two altitudes:

- **Local slop** (surgical removal, behavior unchanged): comments that restate the code rather than explain *why* or carry non-obvious intent; reflexive try/catch or defensive checks on trusted internal paths; `any`/`unknown` casts that paper over a type instead of fixing it; deep nesting an early return would flatten; anything stylistically inconsistent with the surrounding file.
- **Code judo** (ambitious structural deletion): a re-framing that makes whole branches, flags, modes, wrappers, or layers disappear instead of spreading the same complexity around, the move that makes the change feel inevitable in hindsight. Hunt for:
  - the **deletion test**: a module or thin wrapper whose complexity vanishes when removed is a pass-through; fold it into its caller.
  - **spaghetti growth**: a one-off conditional bolted onto a flow another module should own.
  - **bespoke duplication** of a canonical helper the codebase already provides.
  - a **redundant test**: it re-pins a behavior another test pins at the same seam, or splits one workflow into one-assertion tests that each rebuild the setup; fold them into the **journey test** that walks it, since a many-assertion journey test is the intended shape.
  - **fragmented representation**: parallel arrays, structs, or maps held in lockstep, such as column names beside types beside defaults, where one collection of whole records carries the same information with no chance of drift.
  - **boundary smells**: a cast or optional papering over an unclear invariant.
  - a file the diff pushes past a healthy size with code that could split out.

  Propose the ambitious cut only when the complexity is removable, not load-bearing.

**Smell baseline.** Also match the diff against these code smells (Fowler, _Refactoring_ ch. 3): **Mysterious Name** (a *wrong* name, not a debatably better one), **Feature Envy**, **Data Clumps**, **Primitive Obsession**, **Repeated Switches** and **Shotgun Surgery** (each within *this diff*, not across the tree), **Divergent Change**, **Message Chains**, and **Refused Bequest**. A smell is a *lens*, not a finding: it earns a candidate only when you can ground the structural problem in the diff's code, and a documented repo standard that endorses the pattern suppresses it.

## Magic strings — one source of truth

A magic string is any literal a name should hold, such as a status, key, route, config name, error code, or numeric threshold, hard-coded where a **constant, enum, or class member** belongs. Agents invent these constantly, and the copies drift silently.

Flag it when **a constant or enum for that exact value already exists and the diff hand-rolled the literal anyway** (reuse the canonical one), or when **the value repeats, or is a contract that several sites must agree on** (lift it into one constant or enum). A lone, local, single-use literal with no canonical home and no duplication is not a finding.

## Never cut required behavior

Nothing above licenses removing a trust-boundary validation, a data-loss or error path, a security check, or an accessibility affordance. If the diff *drops* one, that is a correctness finding under question 1, not a simplification.

## Classes

A defect that is one instance of a repeatable mistake gets a **class**: one phrase naming the mistake, and the one repo-wide search that finds its instances, written as a single shell command whose output lists each hit as `file:line`, so whoever fixes the finding re-runs it unchanged. Run that search, read each hit, and list in the same finding every **site**, each as `file:line`: a hit where the same failure is reachable. A hit where the failure is not reachable is not a site. A site on lines the diff did not touch stays in the class finding and is fixed with it.

## Pre-existing defects

A **pre-existing** defect sits on lines the diff neither added nor changed and is not a site of a class finding. A defect the diff makes newly reachable is the diff's own finding. Report a pre-existing defect only when you meet one while reading the symbols the diff changes or calls on its changed lines; never go looking for one. The report lists it apart from the findings, so it never counts against the diff.

## If you are a finder

Apply the rubric across the whole diff, or the single lens the dispatch names. Return only a list of candidate findings, each with `file:line`, the claim in one sentence, which of the four questions it answers, why it matters, and the smallest fix. A class finding also carries its class phrase, its search command, and every site. A pre-existing candidate carries the word `pre-existing` beside its question tag. If the diff is clean, return an empty list; never manufacture findings to fill it.

## If you are a validator

You are handed one finding to **refute**. Read the code at the cited `file:line` and judge the claim against this rubric. Default to **REFUTED** when the evidence is thin, the complexity the finding wants cut is load-bearing, the "missed" edge case is unreachable, or the call is a matter of taste. A finding that several structures should collapse into one is *not* taste: confirm it when unifying them provably preserves behavior, and refute it only when the parts have genuinely independent lifetimes or shapes. For a class finding, read every site it lists and confirm or drop each one: a site stays only when the same failure is reachable there, and a `CONFIRMED` verdict names the sites that stayed. For a candidate marked `pre-existing`, confirm the defect and that the diff neither added nor changed its lines; when the diff did, say so in the verdict, since the defect is then the diff's own finding. Return `CONFIRMED` with the one line of code-grounded evidence that proves it, or `REFUTED` with the reason. A finding you can only argue for by restating it is REFUTED.
</review-rubric>
