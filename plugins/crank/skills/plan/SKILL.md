---
name: plan
description: Promotes a spec.md into an executable, code-level implementation plan with ordered tasks. Use after a spec exists and the user types /plan or asks to break the spec into steps.
argument-hint: "[optional path to spec.md or its directory]"
---

# Plan

Turn `spec.md` into an executable plan — ordered tasks with exact paths, commands, and code blocks where they disambiguate. The implementer is capable: **direct, don't dictate**. Pin the non-obvious (signatures, regexes, migrations, multi-step API order); trust prose-with-paths for the mechanical (CRUD, renames, config tweaks). Terminal artifact: `<spec-dir>/plan.md` (single-file) or thin index + `01-<slug>.md`, `02-<slug>.md`, … (multi-phase). Both end with a final task that writes `retro.md` at execution time. Hand back after writing.

## Hard rules

- **No source-file edits, scaffolding, or implementation skills during this session.** Exact code blocks live inside `plan.md`, not the tree.
- **Never use `AskUserQuestion`** — every question goes in chat prose with options + recommendation + reasoning. The reasoning is the point.
- "Just build it" mid-session: write what's resolved into `plan.md` first, then proceed.

## Setup

Check git state (`git rev-parse --abbrev-ref HEAD`, `git status --short`, `git worktree list`). If spec already created `crank/<slug>`, confirm and continue. If on `main`/`master`/`trunk`, offer in chat: **A.** new branch, **B.** new worktree via the `EnterWorktree` tool with `name: "crank/<slug>"` (recommended for L/XL or dirty tree — lands under `.claude/worktrees/`), or **C.** stay put (only if user says so). Wait for confirmation. Never `git worktree add` to a sibling path; always use `EnterWorktree`.

Locate the spec: (1) `$ARGUMENTS` if it points to `spec.md` or its directory, (2) auto-detect via `ls -1t docs/crank/*/spec.md | head -5` — use it if exactly one; if multiple, list with mtimes and ask, (3) none — say so and offer `crank:spec` rather than fabricating one. Read it in full; the **Key decisions** section captures upstream rationale.

## Phases (track with TaskCreate)

### 1. Ingest

In 2–3 sentences, state back: the change, the size/risk tier, any spec section that looks hard to plan against (validation without exact command, interface without signature, blast bullet that contradicts the code). Ask once: *"Plan against this, or flag back to `crank:spec` first?"* Capture small gaps as pre-write blockers (would change a task) or open items (wouldn't).

### 2. Re-ground in code — delegate, don't read

Grounding means *facts* — exact signatures, types, import paths, drift since spec, patterns to mirror — not whole source files in your context. Reading the subsystem yourself is what blows a fresh session past 150k before you write a line. So delegate.

Dispatch the **`crank-scout`** agent via **Agent** (`subagent_type: "crank-scout"`). Pass it the spec's named files/areas, the path to `spec.md`, and any specific questions a code block will hinge on (a signature you must match, whether a module moved). For a large or multi-area spec, **fan out several scouts in one message** — one per area — and assemble their reports. Each scout burns its own context exploring; you keep only the distilled report.

You still run `git log --oneline -10` and `git status --short` yourself — cheap, and you need them for phase 1 and the branch check. But the file reading goes to scouts.

From the returned reports: fold drift into **Updates since spec** or raise it as a blocker; treat a "too-broad" signal as evidence the phase boundaries need re-cutting (route back to `crank:spec`). Stop when the reports let you write code blocks for the touched files without guessing imports, types, or signatures. If a report leaves a gap, re-dispatch that scout with a sharper question rather than opening the file yourself.

**Multi-phase:** you plan every phase in this one session, so ground the *whole* change area now — fan out scouts across every area the spec names, in one message. Assemble their reports into `<spec-dir>/grounding.md`. Once the phase split is set (phase 4), you hand each Opus phase-planner the slice of these facts its phase needs — the planners read `grounding.md` instead of re-scouting — so the file must be **complete and tightly cited before the fan-out**. A gap there becomes a phase-planner guessing.

### 3. Map the file structure

Build this from the scout reports, not a fresh read. For every file the plan touches: **path** (from repo root), **action** (`create`/`modify`/`delete`), **responsibility** (one line). If a file's responsibility needs more than one line, that's SRP tension — split now (as a task) or note as an open item. Follow the patterns the scouts cited; don't unilaterally restructure unless a file you're already modifying has grown unwieldy. If the table needs a file no scout covered, dispatch a scout for it — still don't read it yourself.

### 4. Decompose into tasks

A **task** is independently committable (green tree at end), has a clear file set, implements one cohesive thing, and takes ~2–5 minutes to execute. Order so each task builds on the prior green tree. Default rhythm: **test** → **impl** → **verify** → **commit** (one commit per task, not per step). Skip honestly when seams don't exist:

- **No test seam** (config, docs, CSS, irreversible scaffold) — drop test/verify; replace with the lightest agent-verifiable check from the spec (`pnpm build`, `pnpm typecheck`, curl). Don't manufacture fake tests.
- **Refactor-only** — existing tests are the contract; verify runs them.

**Size check.** Split into phases when **any** holds (two+ is strong): estimated >1000 lines (~80/task), >12 tasks, spec sized L/XL, natural review seams (data model → API → UI; migration → backfill → cutover). Propose the split in chat before writing — phase boundaries with one-line scopes, recommendation, reasoning. Multi-phase layout: `plan.md` (thin index), `01-<slug>.md`, `02-<slug>.md`, …, plus `retro.md` appended per phase at execution. Numbers zero-padded for sort order; slugs kebab-case.

**Single-file vs. multi-phase splits the work here.** For a **single-file** plan you decompose every task yourself, now. For a **multi-phase** plan you stop at the phase boundaries and one-line scopes — the per-phase task decomposition is delegated to one Opus phase-planner subagent per phase (phase 7). You still own the cross-phase view: the file map, phase ordering, and the index.

### 5. Write the steps

*Single-file: you write the steps now. Multi-phase: these rules are forwarded verbatim to the Opus phase-planners in phase 7 — they write the phase steps, you don't.*

Every step is concrete enough to execute without re-asking a design question. Bar: a capable implementer reads the step alone and types code without ambiguity. Either a code block **or** unambiguous prose-with-signatures clears it.

**Embed code when** the shape matters and freedom degrades the outcome: tests (assertions *are* the contract), non-obvious signatures/types, regexes/queries/migrations, structural patterns to mirror (`path/to/template.ts:1-30`), algorithmic cores. **Skip the block when** prose-with-signature is just as clear: mechanical edits (`change < to <= at foo.ts:18`), standard CRUD ("match the existing `GET /api/posts` at `routes/posts.ts`"), trivial refactors, config/docs/CSS tweaks.

**Form.** Full paths from repo root; line numbers on `modify`. Copy-pasteable commands (cwd = repo root unless stated). Every `verify` names exact success (`1 passed`, exit 0, status 200) — "tests pass" is not enough. No comments in embedded code unless the *why* is non-obvious. No throwaway scaffolding (no `// TODO` followed by a fill-in step). Tasks must be readable out of order — repeat structure rather than writing "see Task 3."

**Task principles.** YAGNI — implement what the spec requires; trust framework/type guarantees; validate only at boundaries. DRY — extract when the same logic hits ≥3 places; two copies are fine. SOLID — SRP per file (caught in phase 3); dependency inversion at external integration seams. **No placeholders** — "TBD," "implement later," "similar to Task N," vague prose that *sounds* instructional but doesn't tell the implementer what to type ("add appropriate error handling" → "wrap in try/except for `ConnectionError`; log WARN; re-raise as `AuthServiceError`"). No backwards-compat shims unless the spec calls for them.

### 6. Self-review

Fresh-eyes pass over the draft (not in `plan.md` yet): **spec coverage** (every goal/interface/validation/blast bullet maps to a task), **placeholder scan** (could an implementer execute each step without asking?), **name/type/path consistency** across tasks and the file map, **YAGNI/DRY/SOLID sweep**, **order check** (each task assumes a green tree from the prior). Fix inline; don't re-review.

*Multi-phase: each Opus phase-planner runs this over its own phase file before reporting back (the rule is forwarded with phase 5); the phase-8 per-phase reviewer is the external check.*

### 7. Resolve, then write

**Pre-write gate** (both tracks). Classify every decision: **Resolved** (into plan body), **Deferred-OK** (implementer can pick reasonably — into Open items), **Blocking** (would change a code block, command, file path, or test). Most plan blockers are spec gaps — default move is to surface them and offer `crank:spec`. If the user rolls forward, ask in chat (options + recommendation + reasoning); re-walk until zero blockers. Bar is conservative: style/future-scope/low-risk defaults flow into Open items without asking. **Headless fallback** — pick the most defensible option, write it, add `Assumption: X — invalidated by Y` under Open items. Resolve every blocker *before* writing or fanning out.

Keep each section as short as the topic allows; omit empty ones rather than padding with "N/A".

**Single-file — write `plan.md` yourself.** `<spec-dir>/plan.md` sections: header (title, date, `Status: Plan — ready to execute`, link to `./spec.md`) · **Goal** (one sentence) · **Architecture** (2–3 sentences) · **Tech stack** (pinned versions) · **Updates since spec** (omit if none) · **File structure** (table: path | action | responsibility) · **Tasks** (each with **Files:** block then `test`/`impl`/`verify`/`commit` checkbox steps) · **Smoke tests for the user** (copied verbatim from spec; omit if none) · **Open items** · **Out of scope**. **Final task** writes `<spec-dir>/retro.md` with: header, **Summary** (2–4 sentences on what shipped vs. goal), **Deviations from the plan** (per task meaningfully different), **Notes for future work**, **Loose ends**. Then report the task count + agent-verifiable vs. user-required smoke counts, and go to phase 8.

**Multi-phase — write the index, then fan out Opus phase-planners.** Two moves: you write the thin index; one Opus subagent per phase writes the phase files in parallel.

*Write the index yourself* — it's the cross-phase view only you hold. `<spec-dir>/plan.md` (index only — no task steps): header (title, date, `Status: Plan — ready to execute`, link to `./spec.md`) · **Goal** · **Architecture** · **Tech stack** · **Updates since spec** (omit if none) · **File structure (across phases)** table with an extra **Phase** column · **Phases** list linking each `NN-<slug>.md` with its one-line scope · cross-phase **Smoke tests** / **Open items** / **Out of scope**. Write it first so the phase-planners can link it.

*Fan out the phase-planners.* In one message, dispatch one **Agent** per phase — `subagent_type: general-purpose`, `model: opus`, `description: "Plan phase NN"`. They run in parallel; each burns its own context writing a single phase file. Every brief carries, inlined:

- the paths to `spec.md`, the index `plan.md`, and `grounding.md`;
- this phase's one-line scope **and** every other phase's one-line scope, naming which lower-numbered phases this one may build on and must not duplicate;
- this phase's **slice of the grounding facts** — paste the relevant `grounding.md` sections inline; the planner does **not** run scouts;
- the task-writing rules: **forward phases 4, 5, and 6 of this skill verbatim** (task definition, test→impl→verify→commit rhythm, no-seam skip rules, embed-code-vs-prose rules, task principles, form, self-review);
- the phase-file format below.

Phase-file format — each planner writes `<spec-dir>/NN-<slug>.md` (numbers zero-padded, slug kebab-case): header (links `plan.md`, names the phase it depends on) · **Scope** (2–3 sentences) · **Files this phase touches** (the subset of the file table for this phase) · **Tasks** (the standard shape from phase 5) · **Phase smoke tests** · **Phase open items**. The **final task of every phase** appends `## Phase NN — <name>` to `<spec-dir>/retro.md` (creating the file on phase 01) with **What was built**, **Deviations**, **Notes for downstream phases**; the **final phase** additionally inserts `## Summary` and (if needed) `## Loose ends` above the phase-01 section. Instruct each planner to report its file path and task count back, and to end with `BLOCKER: <summary>` if it cannot ground a task from the slice it was given rather than guessing.

Once every planner returns, tell the user the path(s) and report: phase count, total tasks, cross-phase smoke count. Then go to phase 8.

### 8. Review

**Single-file — adversarial review.** Spawn a Sonnet subagent via **Agent** (`subagent_type: general-purpose`, `model: sonnet`, `description: "Adversarial plan review"`). Inline the full `plan.md`; also pass the path to `spec.md`. Brief verbatim:

> You are reviewing an implementation plan adversarially. You will execute it tomorrow with no further design conversation. Find: **non-runnable tasks** (path/command/expected/instruction not concrete enough — bar is "could an implementer execute without asking?"; code block not required if prose names the signature/symbol/branch); **missing spec coverage**; **name/type/path inconsistencies**; **smuggled placeholders** ("TBD," "similar to Task N," instructional-sounding vagueness, references to undefined symbols); **YAGNI/DRY/SOLID violations**; **order problems** (task imports what no earlier task built). Stay in executability and coverage; don't re-open the spec. Output one bulleted list, each: `- [severity] <concern> — <concrete fix>`. Severity: `blocker` / `should-fix` / `nit`. If nothing, say so in one sentence.

Triage each item: **Adopt**, **Adopt with modification**, or **Reject** with reasoning. Don't capitulate on every point — adopting a bad fix is worse than rejecting a real concern. If an item raises a user-only question, apply the pre-write gate split (chat for blockers; **Open items** entry for deferrals; headless fallback same). Append the `## Review log` (format below), then go to phase 9.

**Multi-phase — per-phase review fan-out.** This replaces the single adversarial pass. Three moves: review every phase in parallel, revise the phases that drew feedback, then log it.

*Fan out the reviewers.* In one message, dispatch one Sonnet **Agent** per phase — `subagent_type: general-purpose`, `model: sonnet`, `description: "Review phase NN"`. Each brief inlines that one phase file, the index `plan.md`, the path to `spec.md`, and the one-line scopes of the adjacent phases. Brief verbatim:

> You are reviewing one phase of a multi-phase implementation plan adversarially; it will be executed with no further design conversation. Review **only this phase file**. Find: **non-runnable tasks** (path/command/expected/instruction not concrete enough — bar is "could an implementer execute without asking?"; a code block isn't required if prose names the signature/symbol/branch); **missing coverage** of this phase's stated scope; **name/type/path inconsistencies** within the phase or against the index; **smuggled placeholders** ("TBD," "similar to Task N," instructional-sounding vagueness, undefined symbols); **YAGNI/DRY/SOLID violations**; **order problems** (a task imports what no earlier task built); **phase-boundary problems** — the phase must be green at its end, depend only on lower-numbered phases per the scopes given, its file set must match the index, and the retro-append must be the final task. Don't re-open the spec. Output one bulleted list, each: `- [severity] <concern> — <concrete fix>`. Severity: `blocker` / `should-fix` / `nit`. If nothing is wrong, say so in one sentence.

*Revise the phases that drew feedback.* For every reviewer that returned actionable items, dispatch a Sonnet **Agent** — `subagent_type: general-purpose`, `model: sonnet`, `description: "Revise phase NN"` — in parallel. Each brief carries the phase file path, that reviewer's bulleted list, the index, and the path to `spec.md`. Instruct it to: triage each item — **Adopt**, **Adopt with modification**, or **Reject** with reasoning (don't capitulate on every point; adopting a bad fix is worse than rejecting a real concern); edit `NN-<slug>.md` in place to apply the adopted items; route any item that raises a user-only design question into that phase's **Phase open items** instead of guessing; and report back what it adopted, modified, rejected, and routed. Skip the reviser for any phase whose reviewer raised nothing actionable.

*Log it.* Append `## Review log` to the index — `Reviewers: Sonnet, per-phase adversarial pass · Date: YYYY-MM-DD` — with one `### Phase NN` block per phase, each carrying **Adopted** (`<concern> → <change>`), **Considered, not adopted** (`<concern> — <reason>`), and **Open items** (`<concern routed to the user>`), pulled from the revisers' reports. Keep empty subsections explicit (`- None`). Tell the user a one-line-per-phase summary ("phase 01: 3 items, 2 adopted, 1 routed · phase 02: clean · phase 03: 1 item, 1 adopted").

**`## Review log` format** (both tracks). Single-file uses the three flat subsections — **Adopted**, **Considered, not adopted**, **Open items**; multi-phase nests them under one `### Phase NN` block each. The log prevents oscillation across review cycles. Keep it even when empty (`- None — reviewer raised no actionable items`).

**Headless** (the override block is present): skip phase 8 entirely — the orchestrator owns review cadence. The phase-7 phase-planner fan-out still runs.

### 9. Offer next step

In chat prose (no `AskUserQuestion`):

- **Single-file:** *"Plan written to `<spec-dir>/plan.md`. **Execute now** in this session · **Hand off to a fresh context** · **Stop here**."*
- **Multi-phase:** *"Plan written to `<spec-dir>/`: index + N phase files. **Execute phase 01 now** (stop at phase boundary after retro append) · **Hand off per phase** · **Stop here**."*

Then stop.

## Anti-patterns & style

Avoid: editing source files mid-plan; reading the subsystem into your own context instead of dispatching `crank-scout` (the fast path to a blown context window); asking the user what their own code does; re-litigating spec decisions (surface shifts under **Updates since spec** or route back); vague verify steps ("tests pass"); skipping the failing test when a seam exists; manufacturing fake tests when no seam exists; step-level or batched commits (one per task, after verify); placeholders of any flavor; over-specifying mechanical work (no five-line block for a getter); YAGNI violations (`// for future use` → delete); premature DRY (extract on the third copy); skipping the pre-write gate or the phase-8 review because the plan "feels solid"; capitulating on every reviewer item; silently dropping reviewer items; continuing past the doc; splitting a small plan into phases (phases earn their place at >1000 lines, >12 tasks, L/XL spec, or natural review seams); stuffing the multi-phase index with task steps (it's an index); writing the phase files yourself instead of fanning out one Opus phase-planner per phase; making each phase-planner re-scout instead of grounding the whole area upfront and handing it a slice; handing a phase-planner an incomplete grounding slice (it will guess); skipping the per-phase reviewer or reviser fan-out outside headless mode; skipping the retro task.

Match the spec's energy — a small fix gets a 2–4 task plan; a new subsystem gets a denser one with a longer file-structure table. Be direct. Quote `path:line` and actual command output. When you don't know, say so — and either go look or ask, depending on whether the answer's in the code or the user's head.
