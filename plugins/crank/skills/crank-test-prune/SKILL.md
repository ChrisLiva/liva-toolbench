---
name: crank-test-prune
description: Prune a test suite for utility — verdict every test KEEP, DELETE, or REFACTOR so only behavior-pinning tests survive.
argument-hint: "[scope, default: the whole test tree]"
disable-model-invocation: true
---

# Test Prune

## Goal

A leaner suite where every surviving test pins a distinct, observable behavior through a **seam**. The keep test: would this test still earn its place if the implementation were rewritten in another language? Tests exist to catch behavior regressions, not to pin the shape of the code — prune aggressively; a suite of fewer, sharper tests beats a thicker one that resists refactoring.

## Hard Rules

- **Every test in scope gets exactly one verdict** — KEEP, DELETE, or REFACTOR. No sampling; the verdict table accounts for every test.
- **Expected values come from an independent source of truth** — a hand-verified literal from a real fixture or committed snapshot — never recomputed with the same formula the code under test uses (a tautological assertion passes by construction and can never disagree with the code).
- **Redundancy is judged suite-wide, not per file** — two tests pinning the same behavior at the same seam are one KEEP and one DELETE, even when they live in different files.
- **Tests only.** This skill edits and deletes test code; production code is never touched. A pruning pass that surfaces a production bug reports it, it doesn't fix it.
- **Green gate.** The full suite runs after applying; the pass isn't done until it's green.

## Verdicts

- **KEEP** — pins a distinct observable behavior at a seam.
- **DELETE** — an **implementation-detail test**, a tautological assertion, contract-shaped (asserts structure, types, or wiring rather than behavior), or redundant with a kept test.
- **REFACTOR** — behavior worth pinning, assertion too weak to pin it. The common weak shape: scanning all values for a property instead of asserting one known concrete case — replace "no value in the map is undefined" with "this specific known key resolves to this hand-verified literal."

## Flow

### 1. Scope

From the argument, settle the test tree under review (default: the whole suite) and capture the test-file inventory plus the suite's run command. **Done when:** the file list and run command are pinned and stated.

### 2. Verdict

Fan out standard subagents — one per directory or module on a large suite — each returning one verdict row per test: file, test name, verdict, one-line reason. Merge the rows, then reconcile redundancy suite-wide yourself: each subagent sees only its slice, so cross-slice duplicates are yours to catch. **Done when:** every test in the inventory has exactly one verdict.

### 3. Apply

Apply the DELETEs and REFACTORs. **Done when:** every DELETE and REFACTOR row is applied.

### 4. Verify

Run the full suite and repair any breakage the pruning itself caused. **Done when:** the suite is green.

### 5. Report

Render the verdict table (every test in scope), counts per verdict, the net line delta, and any production bug the pass surfaced. **Done when:** the table is rendered.

## References

### Subagents

This skill spawns verdict subagents at the **standard** tier — resolve it to your harness (Claude Code / Codex / Cursor) per [SUBAGENT-TIERS.md](SUBAGENT-TIERS.md).

### Vocabulary

Shared crank design language, defined once in [VOCABULARY.md](VOCABULARY.md). This skill leans on the **seam** and the **implementation-detail test** — read their meanings there.
