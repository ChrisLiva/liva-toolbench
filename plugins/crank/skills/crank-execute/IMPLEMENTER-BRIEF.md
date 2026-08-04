# Implementer artifacts

Use these templates only in subagent execution modes. They keep verbose task context in files instead of chat, so the orchestrator's window stays small while implementers and reviewers still get a complete brief.

## `orientation.md`

Write this once per run, after the brief/report directory is chosen. Keep it compact: a repo map, not a second plan. The Commands block copies the plan's `Gates:` header line when the plan carries one — don't re-discover the toolchain.

```md
# Crank execute orientation

Branch: <branch>
Plan: <plan path>
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

- Implementers read this file and their task brief, not the whole plan unless the brief says otherwise.
- Reviewers use this file as the repo map and scope exploration to the diff plus targeted symbol reads.
```

## `task-<N>-brief.md`

Write one file per dispatched task. The implementer reads this and `orientation.md`; do not paste the full task into chat.

```md
# Task <N>: <title>

Branch: <branch>
BASE: <HEAD SHA before this task starts>
Orientation: <path to orientation.md>
Report path: <path to task-<N>-report.md>

## Task text

<quote the plan task verbatim>

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

- Do not push, amend earlier commits, or rewrite history.
- Before writing a new function, class, or helper, check for one that already exists: read orientation.md's Fixtures/helpers and grep the areas this task touches. If one does the job, call it instead of re-implementing it; if none does, note that in the report's Concerns so the reviewer knows the codebase was searched.
- Before reaching for a new third-party dependency, exhaust the lighter options in order: an existing in-repo helper, the stdlib, a native platform feature, then a dependency already in the manifest. Don't add a dependency for what a few lines do; if the task genuinely needs one the plan didn't name, return `NEEDS_CONTEXT` instead of importing it silently.
- A probe step (a throwaway deterministic check the plan embeds) runs from the OS temp dir, never the working tree: watch it fail once, run it green, paste its output into the report's Verification, and delete it — `git status` shows no probe artifact at commit time.
- Follow TDD where the task changes behavior: RED for the expected reason, minimal GREEN, then the task verify command.
- For multi-behavior tasks, work as tracer bullets: test A -> impl A -> test B -> impl B.

## Return

Return only the thin summary described in this file's "Thin implementer return" template. Put the full detail in the report path above.
```

## `task-<N>-report.md`

The implementer writes this before returning. It can be verbose because it stays out of the orchestrator's chat context.

```md
# Task <N> report

Status: DONE | DONE_WITH_CONCERNS | NEEDS_CONTEXT | BLOCKED
Commits:
- <sha> <subject>

## TDD evidence

Behavior 1: <name>
- RED: `<command>` -> <output proving the expected failure>
- GREEN: `<command>` -> <passing output>

Behavior 2: <name, omit if none>
- RED: `<command>` -> <output proving the expected failure>
- GREEN: `<command>` -> <passing output>

TDD skipped because: <plan explicitly allowed config/doc/generated/no-behavior change, or "not skipped">

## Verification

- `<verify command>` -> <result>

## Changes

- <short bullet list of what changed>

## Concerns

- <concern, or "none">
```

## Thin implementer return

The chat return must stay under about 15 lines:

```md
Status: DONE | DONE_WITH_CONCERNS | NEEDS_CONTEXT | BLOCKED
Commits:
- <sha> <subject>
Tests: <one-line summary>
TDD: <RED/GREEN evidence summary; one pair per behavior, or "skipped: <reason>">
Concerns: <none, or one-line summary>
Report: <path to task-<N>-report.md>
```

If TDD applies and the return lacks RED/GREEN evidence, or a multi-behavior task shows only one bulk RED/GREEN pair, treat the task as `CHANGES_REQUESTED`.
