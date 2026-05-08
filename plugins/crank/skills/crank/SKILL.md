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

## Phase 4 — execute (default model — execute self-triages)

**Status before:** `Executing plan (Haiku impl + Sonnet review, managed by execute)…`

Spawn:

- Tool: `Agent`
- `subagent_type`: `general-purpose`
- `model`: omit (let `execute` operate at session default; it manages its own Haiku/Sonnet workers internally)
- `description`: `Crank: execute phase`
- `prompt`:
  > Invoke the `crank:execute` skill via the `Skill` tool with this argument: `<RUN_DIR>`. Run the plan to completion. The skill handles its own non-interactive triage (solo / sequential / parallel) and writes `retro.md`. End your final message with the sentinel `RETRO_PATH=<absolute path to retro.md>` on its own line. If you hit a hard blocker, end with `BLOCKER: <summary>` on its own line, then the sentinel.

Extract `RETRO_PATH=...`. Halt on missing sentinel or `BLOCKER:`.

**Status after:** `Retro written: <path>`

## Final summary

After Phase 4 succeeds, print one block:

```
Crank complete:
  brainstorm  <BRAINSTORM_PATH>
  spec        <SPEC_PATH>
  plan        <PLAN_PATH>
  retro       <RETRO_PATH>
```

If any phase halted on a blocker, the summary instead lists only the artifacts that were produced and the blocker line that ended the run.
