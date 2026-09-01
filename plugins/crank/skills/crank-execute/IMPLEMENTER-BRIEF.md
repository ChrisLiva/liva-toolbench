# Implementer artifacts

Use these templates only in subagent execution modes.

## `orientation.md`

Write this once per run, after the brief/report directory is chosen. Bounds: one Touched areas bullet per directory named across the plan's Files blocks; every Commands row filled with a command or the literal `none`; each Local conventions line quoting a real file the implementer can open. Done when no `<…>` remains and no plan Files-block directory is missing from Touched areas. The Commands block copies the plan's `Gates:` header line when the plan carries one — don't re-discover the toolchain. The `Grounding:` line copies the plan's `Grounding:` header path, or the effort's `grounding.md` when it holds entries the plan predates; `none` otherwise.

```md
# Crank execute orientation

Branch: <branch>
Plan: <plan path>
Grounding: <absolute path to .crank/<slug>/grounding.md, or "none"> — facts earlier phases proved, one `claim | evidence | phase, date` per line; confirm an entry at its citation before building on it
Run base: <base SHA from the progress ledger>

## Commands

- Test: `<command or "none">`
- Lint: `<command or "none">`
- Typecheck: `<command or "none">`
- Build: `<command or "none">`
- Single-test pattern: `<command/pattern or "unknown">`

## Touched areas

- `<directory/module>`: <why this run touches it>

## Local conventions

- Imports: <project-specific import idiom>
- Tests: <where tests live and naming pattern>
- Fixtures/helpers: <canonical helpers to reuse>

## Run boundaries

- Read this file and your task brief. Open the plan only at the section your brief names by heading, and read no other part of it.
```

## `implementer-rules.md`

Copy this block into the brief directory once per run, verbatim — every task brief and fix brief points at it, so it is written once and read by every implementer.

```md
# Implementer rules

- Do not push, amend earlier commits, or rewrite history.
- Return only when every command you started has finished. Run long verifications synchronously and read their output in the same turn you report it — work parked behind a background watcher at return time is work not done.
- The task's destination — what it ships — is frozen; the road is not. When a bug, stale detail (renamed symbol, moved file), or failed assumption blocks this task, fix it as a detour: the smallest change, inside the files block, that still ships exactly what the task promises — and record it in the report's Deviations. A fix that would change what ships is not yours to make — return `BLOCKED` naming the reroute; a detour needing files outside the block returns `NEEDS_CONTEXT` first. A `Stop if:` condition in your task's plan section, once observed, is a `BLOCKED` return naming what you observed, never something to work around.
- Before writing a new function, class, or helper, check for one that already exists: read orientation.md's Fixtures/helpers and grep the areas this task touches. If one does the job, call it instead of re-implementing it; if none does, note that in the report's Concerns so the reviewer knows the codebase was searched.
- Before reaching for a new third-party dependency, exhaust the lighter options in order: an existing in-repo helper, the stdlib, a native platform feature, then a dependency already in the manifest. Don't add a dependency for what a few lines do; if the task genuinely needs one the plan didn't name, return `NEEDS_CONTEXT` instead of importing it silently.

## Standing defect rules

- A probe step (a throwaway deterministic check the plan embeds) runs from the OS temp dir, never the working tree: watch it fail once, run it green, paste its output into the report's Verification, and delete it — `git status` shows no probe artifact at commit time.
- Any encode/decode, save/restore, or serialize/parse pair gets a round-trip assertion using a hostile real value — sub-millisecond timestamps, unicode, boundary sizes — not a friendly fixture.
- When you handle one member of an error family, check its siblings (EPERM beside EACCES, ENOTDIR beside ENOENT): handle the family, or record the single-case choice in the report's Concerns.
- Every parser or loop over external input gets the empty / zero-length / missing case exercised once.
- Address entries in parsed structures by name — a named capture group, or search for the entry; a positional index into parsed output breaks on the first reordering.
- When modifying user-owned files (configs, gitignores), assert the lines your change doesn't touch survive byte-identical.

## TDD

- Follow TDD where the task changes behavior: RED for the expected reason, minimal GREEN, then the task verify command; for a multi-behavior task, one cycle per behavior as tracer bullets: test A -> impl A -> test B -> impl B.
- A new test file is for a new seam: when a test already walks this seam, RED is a failing assertion extended onto that test.
- A test not born RED gets one deliberate mutation of the code under test to watch it fail before you trust its pass — the same rule probes follow.
- The `- [ ] Behavior N:` lines in your brief's **Behaviors** list are the test list — one RED→GREEN cycle per numbered behavior, and no test outside the list. Every committed test pins an observable behavior no other test already pins, and would survive a rewrite of the implementation in another language.
```

## `task-<N>-brief.md`

Write one file per dispatched task; the implementer reads this file, `orientation.md`, and the one plan section the Task block names. That block is a pointer plus the task's behavior lines — never the task's steps pasted in. Fill every `<…>` slot; the Files block sentence and the Return section are fixed text — copy them byte-for-byte, never summarized or trimmed for the task at hand. Completion criterion: the written brief has no unfilled `<…>` and its fixed sections diff clean against this template.

```md
# Task <N>: <title>

Branch: <branch>
BASE: <HEAD SHA before this task starts>
Orientation: <path to orientation.md>
Report path: <path to task-<N>-report.md>

## Task

Plan: <plan path>, section `### Task <N> — <title>`. Read that one section for your steps, its `Check:` line, and its `Stop if:` line — and nothing else from the plan.

Behaviors — your test list, each line copied verbatim from that section:

- [ ] Behavior 1: <the plan's behavior line>
- [ ] Behavior 2: <…>

## Interfaces

Consumes:
- <interface/input, or "none listed">

Produces:
- <interface/output, or "none listed">

## Files block

- <path/glob this task may touch>

Do not touch files outside this block unless you return `NEEDS_CONTEXT` first.

## Verify

`<exact verify command from the plan>`

## Constraints

- Rules: `implementer-rules.md` in this directory — read it before your first edit.
- <constraint this task adds beyond the rules file — a Global Constraint value the task must honor — or "none">

## Return

Put the full detail in the report path above. Return only this thin summary, filled in (under ~15 lines):

    Status: DONE | DONE_WITH_CONCERNS | NEEDS_CONTEXT | BLOCKED
    Commits:
    - <sha> <subject>
    Tests: <one-line summary>
    TDD: <RED/GREEN evidence summary; one pair per behavior, or "skipped: <reason>">
    Deviations: <none, or one-line detour summary>
    Concerns: <none, or one-line summary>
    Report: <path to task-<N>-report.md>
```

## `task-<N>-fix-brief.md`

Write one file per fix round, in the same directory. The fixer reads it, `implementer-rules.md`, and the findings file it names — never a pasted finding list.

```md
# Task <N> fix round <R>

Branch: <branch>
FIX_BASE: <the HEAD the reviewer judged>
Findings: <path to task-<N>-findings.md>
Orientation: <path to orientation.md>
Report path: <path to task-<N>-report.md>

## Scope

Apply the findings under the findings file's newest `## Round <R>` heading (every finding in the file when it carries no round headings) — the fix diff is this round's whole scope. A behavioral fix gets its failing test first; the original brief's behavior list does not bound this round. Rules: `implementer-rules.md` in this directory — read it before your first edit.

## Files block

- <every path the findings cite, plus the files their fixes reach>

Do not touch files outside this block unless you return `NEEDS_CONTEXT` first.

## Verify

`<exact verify command from the plan>` — re-run it after the fixes land and append its fresh output under a `## Verify (round <R>)` heading in the report above before returning. The re-reviewer reads that output instead of re-running the suite.

## Return

    Status: DONE | DONE_WITH_CONCERNS | NEEDS_CONTEXT | BLOCKED
    Commits:
    - <sha> <subject>
    Findings:
    - <finding one-liner> — fixed at <file:line>
    Verify: <one-line result of the appended re-run>
    Report: <path to task-<N>-report.md>
```

## `task-<N>-report.md`

The implementer writes this before returning. It can be verbose because it stays out of the orchestrator's chat context.

```md
# Task <N> report

Status: DONE | DONE_WITH_CONCERNS | NEEDS_CONTEXT | BLOCKED
Commits:
- <sha> <subject>

## TDD evidence

Behavior <N>: <name> — one block per behavior line in the brief's Behaviors list
- RED: `<command>` -> <output proving the expected failure>
- GREEN: `<command>` -> <passing output>

TDD skipped because: <plan explicitly allowed config/doc/generated/no-behavior change, or "not skipped">

## Verification

- `<verify command>` -> <result>

## Changes

- <short bullet list of what changed>

## Deviations

- <detour: what blocked -> the smallest fix, or "none">

## Concerns

- <concern, or "none">
```
