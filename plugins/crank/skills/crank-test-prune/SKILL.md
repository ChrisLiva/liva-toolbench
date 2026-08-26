---
name: crank-test-prune
description: Prune a test suite for utility — verdict every test KEEP, DELETE, REFACTOR, or MERGE so only behavior-pinning tests survive.
argument-hint: "[scope, default: the whole test tree]"
disable-model-invocation: true
---

# Test Prune

## Goal

A leaner suite judged against the **rewrite test**: tests exist to catch behavior regressions, not to pin the shape of the code. Prune aggressively; fewer, sharper tests beat a thicker suite that resists refactoring.

## Hard Rules

- **Every test in scope gets exactly one verdict** — KEEP, DELETE, REFACTOR, or MERGE. No sampling; the verdict table accounts for every test.
- **Expected values come from an oracle** — a hand-verified literal from a real fixture or committed snapshot — never recomputed with the same formula the code under test uses.
- **Redundancy is judged suite-wide, not per file** — two tests pinning the same behavior at the same seam are one KEEP and one DELETE, even when they live in different files. Which one keeps: the test at the truer seam; at equal seam fidelity, the cheaper, faster one — a slow end-to-end test duplicating behavior already pinned lower survives only as one of a handful of happy-path journeys.
- **Tests only.** This skill edits and deletes test code; production code is never touched. A pruning pass that surfaces a production bug reports it, it doesn't fix it.
- **Baselines come from a throwaway worktree, never `git stash`.** Any clean-tree comparison (formatter, lint, the suite at HEAD) runs in a disposable `git worktree add` checkout of HEAD, removed after. `git stash` stays banned for the whole run, coordinator and subagents alike: a later drop destroys the uncommitted user work it swept up.
- **Green gate.** The full suite runs after applying; the pass isn't done until it's green.

## Verdicts

- **KEEP** — passes the **rewrite test**: pins a distinct observable behavior at a seam.
- **DELETE** — an **implementation-detail test**, a tautological assertion (expected value recomputed with the code's own formula, so it passes by construction), contract-shaped (asserts structure, types, or wiring rather than behavior — including re-checking what the type system or schema validation already guarantees), **copy-pinning** (asserts that incidental prose appears — a description, label, warning, or log message; a kept test pins the behavior or a stable structured contract, not the wording), or a **redundant test** beside a kept one.
- **REFACTOR** — behavior worth pinning, assertion too weak to pin it. The common weak shape: scanning all values for a property instead of asserting one known concrete case — replace "no value in the map is undefined" with "this specific known key resolves to this hand-verified literal."
- **MERGE** — behavior worth pinning, test not worth its own setup. The common shapes: one-assertion fragments of a single workflow, or an isolated test pinning an incidental transition state a broader workflow passes through anyway. Fold the assertions into the **journey test** that walks the workflow end-to-end and delete the shell; the verdict row names the destination test.

## Flow

### 1. Scope

From the argument, settle the test tree under review (default: the whole suite) and capture the test-file inventory plus the suite's run command. **Done when:** the file list and run command are pinned and stated.

### 2. Verdict

Fan out standard subagents — one per directory or module on a large suite — each returning one verdict row per test: file, test name, verdict, one-line reason (a MERGE row's reason names its destination test). Merge the rows, then reconcile redundancy and consolidation suite-wide yourself: each subagent sees only its slice, so cross-slice duplicates — and workflow fragments whose destination test lives in another slice — are yours to catch. **Done when:** every test in the inventory has exactly one verdict.

### 3. Apply

Apply the DELETEs, REFACTORs, and MERGEs. Every apply agent's instruction carries three standing constraints: touch only the test files in your assigned verdict rows; never move, rename, or delete repository configuration (formatter configs, hooks, manifests) to work around tooling — report the interference and stop instead; and siblings are editing the same tree concurrently, so unexplained `git status` entries are expected — leave them alone, never investigate or revert them. **Done when:** every DELETE, REFACTOR, and MERGE row is applied.

### 4. Verify

Run the full suite and repair any breakage the pruning itself caused. **Done when:** the suite is green.

### 5. Report

Render the verdict table (every test in scope), counts per verdict, the net line delta, and any production bug the pass surfaced. **Done when:** the table is rendered.

## References

### Subagents

This skill spawns verdict subagents at the **standard** tier — resolve it to your harness per [SUBAGENT-TIERS.md](SUBAGENT-TIERS.md).

### Vocabulary

Read [VOCABULARY.md](VOCABULARY.md) before the verdicts in step 2: this skill leans on the **seam**, the **oracle**, the **implementation-detail test**, the **rewrite test**, the **journey test**, and the **redundant test**.
