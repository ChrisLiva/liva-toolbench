---
name: crank
description: Run the full Crank pipeline (brainstorm → spec → plan → execute) autonomously from a single prompt. Use when the user types /crank or asks to take an idea from raw thought to shipped code without back-and-forth.
argument-hint: "<idea or feature description>"
---

# Crank (autonomous)

You are a non-interactive orchestrator. The user has handed you an idea — `$ARGUMENTS` — and wants you to drive it end-to-end through the four sibling skills (`crank:brainstorm`, `crank:spec`, `crank:plan`, `crank:execute`) without stopping to ask them anything.

You do not write any docs yourself. Each phase runs in its own freshly-spawned subagent. The phases hand off via files on disk in `docs/crank/<slug>/` — the brainstorm subagent picks the slug; subsequent subagents auto-resolve siblings from the same directory.

## Hard rules

- **Never ask the user a question.** Not at the start, not between phases, not at the end.
- **One subagent per phase.** Spawn via the `Agent` tool with the model override specified for that phase. Each subagent invokes the relevant `crank:*` sibling skill.
- **File-based handoff.** Capture the absolute path the subagent returns; `dirname` it to derive the shared run directory; pass that directory as `$ARGUMENTS` to subsequent subagents.
- **Halt on blocker, don't retry.** If a subagent's final message contains a line starting with `BLOCKER:`, surface that line to the user along with whatever partial artifacts exist and stop. Do not attempt to fix or rerun.
- **One short status line before each phase, one after.** No verbose narration between phases.

## The headless override block

Prepend this **verbatim** to every subagent prompt in Phases 1–3 (brainstorm, spec, plan). Phase 4 (execute) does not need it — `execute` is already non-interactive.

> **Headless mode.** You are running under autonomous orchestration. You have no user to ask. Override every interactive gate in the skill you are about to invoke as follows:
> - At every options-and-recommendation decision, pick the **recommended** option silently. Do not surface the menu.
> - For non-obvious picks (anything where the recommendation isn't clearly the best fit for the stated idea), write an `Assumption: <what you assumed and why>` line into the relevant section of the output doc.
> - Skip all confirmation gates: scope confirm, slug confirm, ingest gate, sharpen-questions gate, pre-write gate, phase-split confirm, next-step menu. Proceed directly to writing the output doc.
> - **Never** emit a question back to the orchestrator. If you hit a true blocker (missing file, contradictory spec, tool failure you cannot work around), write what you have to the output doc, append a `## Blocker` section describing the issue, and end your final message with `BLOCKER: <one-line summary>` on its own line followed by `<ARTIFACT>_PATH=<absolute path>` on the next line.
> - On success, end your final message with **only** `<ARTIFACT>_PATH=<absolute path>` on its own line. No next-step menu. No summary prose beyond what's already in the doc.
> - Skip any adversarial Sonnet sub-review the skill normally runs — the orchestrator owns review cadence.

`<ARTIFACT>` is the phase name uppercased: `BRAINSTORM`, `SPEC`, `PLAN`, `RETRO`.

## Phase 1 — brainstorm (Opus)

**Status before:** `Brainstorming with Opus…`

Spawn:

- Tool: `Agent`
- `subagent_type`: `general-purpose`
- `model`: `opus`
- `description`: `Crank: brainstorm phase`
- `prompt`: the headless override block above, followed by:
  > Now invoke the `crank:brainstorm` skill via the `Skill` tool with these arguments: `$ARGUMENTS`. Run it under the headless rules above. End your final message with the sentinel `BRAINSTORM_PATH=<absolute path to brainstorm.md>` on its own line.

When the subagent returns, extract `BRAINSTORM_PATH=...` from its final message. `dirname` that path → call it `RUN_DIR`. If the sentinel is missing, halt: print "brainstorm subagent did not return BRAINSTORM_PATH sentinel" along with the last ~20 lines of the subagent's return.

**Status after:** `Brainstorm ready: <path>`

If the return also contained `BLOCKER:`, halt now and surface it.

## Phase 2 — spec (Opus)

**Status before:** `Drafting spec with Opus…`

Spawn:

- Tool: `Agent`
- `subagent_type`: `general-purpose`
- `model`: `opus`
- `description`: `Crank: spec phase`
- `prompt`: the headless override block, followed by:
  > Now invoke the `crank:spec` skill via the `Skill` tool with this argument (the run directory containing brainstorm.md): `<RUN_DIR>`. Run it under the headless rules above. End your final message with the sentinel `SPEC_PATH=<absolute path to spec.md>` on its own line.

Extract `SPEC_PATH=...`. Halt on missing sentinel or `BLOCKER:`.

**Status after:** `Spec ready: <path>`

## Phase 3 — plan (Sonnet)

**Status before:** `Planning with Sonnet…`

Spawn:

- Tool: `Agent`
- `subagent_type`: `general-purpose`
- `model`: `sonnet`
- `description`: `Crank: plan phase`
- `prompt`: the headless override block, plus the line **"Default to a single-file plan unless the spec is unambiguously L/XL — bias toward fewer files."**, followed by:
  > Now invoke the `crank:plan` skill via the `Skill` tool with this argument: `<RUN_DIR>`. Run it under the headless rules above. End your final message with the sentinel `PLAN_PATH=<absolute path to plan.md>` on its own line.

Extract `PLAN_PATH=...`. Halt on missing sentinel or `BLOCKER:`.

**Status after:** `Plan ready: <path>`

## Phase 4 — execute (Sonnet)

**Status before:** `Executing plan…`

Spawn:

- Tool: `Agent`
- `subagent_type`: `general-purpose`
- `model`: `sonnet`
- `description`: `Crank: execute phase`
- `prompt`:
  > Invoke the `crank:execute` skill via the `Skill` tool with this argument: `<RUN_DIR>`. Run the plan to completion. The skill handles its own non-interactive triage (solo / sequential / parallel) and writes `retro.md`. End your final message with the sentinel `RETRO_PATH=<absolute path to retro.md>` on its own line. If you hit a hard blocker, end with `BLOCKER: <summary>` on its own line, then the sentinel.

Extract `RETRO_PATH=...`. Halt on missing sentinel or `BLOCKER:`.

**Status after:** `Retro written: <path>`

## Phase 5 — Self-review & remediate (orchestrator + Sonnet)

This phase runs **in the main thread** — you do it yourself, no subagent. The per-task reviewer inside `execute` only sees one task at a time; this phase catches cross-task drift against the original spec.

**Status before:** `Reviewing implementation against spec…`

### 5a. Read the inputs

Read these directly:

- `<RUN_DIR>/spec.md` — the frozen intent.
- `<RUN_DIR>/retro.md` — what `execute` reported (commits, deviations, open items).

Derive the diff that landed. Retro's `## Summary` lists `commits <first>..<last> on branch <branch>`. Run `git log --oneline <first>^..<last>` and `git diff <first>^..<last>` to see the actual change. If retro names a branch but no SHA range, fall back to `git diff main...<branch>`.

### 5b. Review

Evaluate the diff against:

1. **Spec coverage** — every validation/acceptance criterion in `spec.md` met? Anything missing or quietly substituted?
2. **Retro red flags** — open items or "punted" work that were actually in-scope per the spec and shouldn't have been deferred. Deviations whose justification is weak.
3. **Cross-task coherence** — gaps the per-task reviewer couldn't see (inconsistent naming across tasks, dead code from an early task once a later task landed, missing wiring between independently-built pieces).

Be concrete. Cite `file:line`. Don't restyle code or expand scope — this review is about whether the *shipped* diff matches the *original* spec.

### 5c. Persist the review

Write `<RUN_DIR>/review.md`:

```markdown
# Review: <plan title>

## Verdict
<APPROVED | CHANGES_REQUESTED>

## Findings
- <file:line — what's wrong, which spec/retro item it relates to>
- ...

## Remediation scope (only if CHANGES_REQUESTED)
- <specific, bounded fix the remediation agent should make>
- ...
```

Print one line to the user: `Review verdict: APPROVED` or `Review verdict: CHANGES_REQUESTED (<N> findings)`.

### 5d. Remediate (only if CHANGES_REQUESTED)

Spawn **one** Sonnet agent. No loop — single pass. The review is the contract.

- Tool: `Agent`
- `subagent_type`: `general-purpose`
- `model`: `sonnet`
- `description`: `Crank: post-implementation remediation`
- `prompt`:
  > Apply the fixes listed in the `## Remediation scope` section of `<RUN_DIR>/review.md`. Read `<RUN_DIR>/spec.md` and `<RUN_DIR>/retro.md` for context, and `<RUN_DIR>/review.md` in full for the findings.
  >
  > Constraints:
  > - Stay strictly inside the remediation scope. Do not refactor, redesign, or expand.
  > - For each behavioral fix: write a failing test first, implement, run verification.
  > - Commit each logical fix separately with a message like `fix(<area>): <what>`. Do NOT amend earlier commits. Do NOT push.
  > - When done, append a `## Remediation` section to `<RUN_DIR>/retro.md` listing each fix, the commit SHA, and verification output.
  >
  > End your final message with `REMEDIATION_DONE=<count of fixes applied>` on its own line. If you cannot proceed on a finding, leave it and continue with the rest; only emit `BLOCKER: <summary>` if no fix can be applied at all.

When the agent returns, extract `REMEDIATION_DONE=<N>`.

**Status after:** `Remediation complete: <N> fixes applied.` (or, if APPROVED, `Review approved — no remediation needed.`)

## Final summary

After Phase 5 finishes, print one block:

```
Crank complete:
  brainstorm  <BRAINSTORM_PATH>
  spec        <SPEC_PATH>
  plan        <PLAN_PATH>
  retro       <RETRO_PATH>
  review      <RUN_DIR>/review.md  (<APPROVED | CHANGES_REQUESTED — N fixes applied>)
```

If any phase halted on a blocker, the summary instead lists only the artifacts that were produced and the blocker line that ended the run.
