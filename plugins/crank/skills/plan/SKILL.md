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

### 2. Re-ground in code

Run `git log --oneline -10` and `git status --short`. Re-read the files the spec named plus any new file in recent commits that overlaps the change area. Surface drift (renamed function, new dep, deleted file) as "Updates since spec" or as a blocker. Stop when you can write code blocks for the touched files without guessing imports, types, or signatures.

### 3. Map the file structure

For every file the plan touches: **path** (from repo root), **action** (`create`/`modify`/`delete`), **responsibility** (one line). If a file's responsibility needs more than one line, that's SRP tension — split now (as a task) or note as an open item. Follow existing patterns; don't unilaterally restructure unless a file you're already modifying has grown unwieldy.

### 4. Decompose into tasks

A **task** is independently committable (green tree at end), has a clear file set, implements one cohesive thing, and takes ~2–5 minutes to execute. Order so each task builds on the prior green tree. Default rhythm: **test** → **impl** → **verify** → **commit** (one commit per task, not per step). Skip honestly when seams don't exist:

- **No test seam** (config, docs, CSS, irreversible scaffold) — drop test/verify; replace with the lightest agent-verifiable check from the spec (`pnpm build`, `pnpm typecheck`, curl). Don't manufacture fake tests.
- **Refactor-only** — existing tests are the contract; verify runs them.

**Size check.** Split into phases when **any** holds (two+ is strong): estimated >1000 lines (~80/task), >12 tasks, spec sized L/XL, natural review seams (data model → API → UI; migration → backfill → cutover). Propose the split in chat before writing — phase boundaries with one-line scopes, recommendation, reasoning. Multi-phase layout: `plan.md` (thin index), `01-<slug>.md`, `02-<slug>.md`, …, plus `retro.md` appended per phase at execution. Numbers zero-padded for sort order; slugs kebab-case.

### 5. Write the steps

Every step is concrete enough to execute without re-asking a design question. Bar: a capable implementer reads the step alone and types code without ambiguity. Either a code block **or** unambiguous prose-with-signatures clears it.

**Embed code when** the shape matters and freedom degrades the outcome: tests (assertions *are* the contract), non-obvious signatures/types, regexes/queries/migrations, structural patterns to mirror (`path/to/template.ts:1-30`), algorithmic cores. **Skip the block when** prose-with-signature is just as clear: mechanical edits (`change < to <= at foo.ts:18`), standard CRUD ("match the existing `GET /api/posts` at `routes/posts.ts`"), trivial refactors, config/docs/CSS tweaks.

**Form.** Full paths from repo root; line numbers on `modify`. Copy-pasteable commands (cwd = repo root unless stated). Every `verify` names exact success (`1 passed`, exit 0, status 200) — "tests pass" is not enough. No comments in embedded code unless the *why* is non-obvious. No throwaway scaffolding (no `// TODO` followed by a fill-in step). Tasks must be readable out of order — repeat structure rather than writing "see Task 3."

**Task principles.** YAGNI — implement what the spec requires; trust framework/type guarantees; validate only at boundaries. DRY — extract when the same logic hits ≥3 places; two copies are fine. SOLID — SRP per file (caught in phase 3); dependency inversion at external integration seams. **No placeholders** — "TBD," "implement later," "similar to Task N," vague prose that *sounds* instructional but doesn't tell the implementer what to type ("add appropriate error handling" → "wrap in try/except for `ConnectionError`; log WARN; re-raise as `AuthServiceError`"). No backwards-compat shims unless the spec calls for them.

### 6. Self-review

Fresh-eyes pass over the draft (not in `plan.md` yet): **spec coverage** (every goal/interface/validation/blast bullet maps to a task), **placeholder scan** (could an implementer execute each step without asking?), **name/type/path consistency** across tasks and the file map, **YAGNI/DRY/SOLID sweep**, **order check** (each task assumes a green tree from the prior). Fix inline; don't re-review.

### 7. Resolve and write

**Pre-write gate.** Classify every decision: **Resolved** (into plan body), **Deferred-OK** (implementer can pick reasonably — into Open items), **Blocking** (would change a code block, command, file path, or test). Most plan blockers are spec gaps — default move is to surface them and offer `crank:spec`. If the user rolls forward, ask in chat (options + recommendation + reasoning); re-walk until zero blockers. Bar is conservative: style/future-scope/low-risk defaults flow into Open items without asking. **Headless fallback** — pick the most defensible option, write it, add `Assumption: X — invalidated by Y` under Open items.

Then write `<spec-dir>/plan.md` (and phase files if multi-phase). Keep each section as short as the topic allows; omit empty ones rather than padding with "N/A".

**Single-file `plan.md`** sections: header (title, date, `Status: Plan — ready to execute`, link to `./spec.md`) · **Goal** (one sentence) · **Architecture** (2–3 sentences) · **Tech stack** (pinned versions) · **Updates since spec** (omit if none) · **File structure** (table: path | action | responsibility) · **Tasks** (each with **Files:** block then `test`/`impl`/`verify`/`commit` checkbox steps) · **Smoke tests for the user** (copied verbatim from spec; omit if none) · **Open items** · **Out of scope**. **Final task** writes `<spec-dir>/retro.md` with: header, **Summary** (2–4 sentences on what shipped vs. goal), **Deviations from the plan** (per task meaningfully different), **Notes for future work**, **Loose ends**.

**Multi-phase `plan.md`** (index only — tasks live in phase files): same header/Goal/Architecture/Tech stack/Updates · **File structure (across phases)** table with extra **Phase** column · **Phases** list linking each `NN-<slug>.md` with one-line scope · cross-phase **Smoke tests** / **Open items** / **Out of scope**. **Each `NN-<phase-slug>.md`**: header (links plan, names dependency), **Scope** (2–3 sentences), **Files this phase touches** (subset table), **Tasks** (same shape), **Phase smoke tests** / **Phase open items**. **Final task of every phase** appends `## Phase NN — <name>` to `retro.md` (creating it on phase 01) with **What was built**, **Deviations**, **Notes for downstream phases**. The final phase additionally inserts `## Summary` and (if needed) `## Loose ends` above the phase-01 section.

After writing, tell the user the path(s) and report: single-file — total task count + agent-verifiable vs. user-required smoke counts; multi-phase — phase count, total tasks, cross-phase smoke count.

### 8. Adversarial review

Spawn a Sonnet subagent via **Agent** (`subagent_type: general-purpose`, `model: sonnet`, `description: "Adversarial plan review"`). Inline the full `plan.md` plus every phase file in order; also pass the path to `spec.md`. Brief verbatim:

> You are reviewing an implementation plan adversarially. You will execute it tomorrow with no further design conversation. Find: **non-runnable tasks** (path/command/expected/instruction not concrete enough — bar is "could an implementer execute without asking?"; code block not required if prose names the signature/symbol/branch); **missing spec coverage**; **name/type/path inconsistencies**; **smuggled placeholders** ("TBD," "similar to Task N," instructional-sounding vagueness, references to undefined symbols); **YAGNI/DRY/SOLID violations**; **order problems** (task imports what no earlier task built); **phase boundary problems** *(multi-phase)* — each phase green at end, phase N depends only on ≤N, file map consistent with per-phase scopes, retro-append is the final task of every phase. Stay in executability and coverage; don't re-open the spec. Output one bulleted list, each: `- [severity] <concern> — <concrete fix>`. Severity: `blocker` / `should-fix` / `nit`. If nothing, say so in one sentence.

Triage each item: **Adopt**, **Adopt with modification**, or **Reject** with reasoning. Don't capitulate on every point — adopting a bad fix is worse than rejecting a real concern. If an item raises a user-only question, apply the pre-write gate split (chat for blockers; **Open items** entry for deferrals; headless fallback same).

Append `## Review log` at the end of single-file `plan.md` or the multi-phase index, with `Reviewer: Sonnet, adversarial pass · Date: YYYY-MM-DD` and three subsections — **Adopted** (`<concern> → <change>`), **Considered, not adopted** (`<concern> — <reason>`), **Open items** (`<concern needing user>`). The log prevents oscillation across review cycles. Keep the section even when empty (`- None — reviewer raised no actionable items` under Adopted). Briefly tell the user ("4 items: 2 adopted, 1 rejected, 1 routed").

### 9. Offer next step

In chat prose (no `AskUserQuestion`):

- **Single-file:** *"Plan written to `<spec-dir>/plan.md`. **Execute now** in this session · **Hand off to a fresh context** · **Stop here**."*
- **Multi-phase:** *"Plan written to `<spec-dir>/`: index + N phase files. **Execute phase 01 now** (stop at phase boundary after retro append) · **Hand off per phase** · **Stop here**."*

Then stop.

## Anti-patterns & style

Avoid: editing source files mid-plan; asking the user what their own code does; re-litigating spec decisions (surface shifts under **Updates since spec** or route back); vague verify steps ("tests pass"); skipping the failing test when a seam exists; manufacturing fake tests when no seam exists; step-level or batched commits (one per task, after verify); placeholders of any flavor; over-specifying mechanical work (no five-line block for a getter); YAGNI violations (`// for future use` → delete); premature DRY (extract on the third copy); skipping the pre-write gate or adversarial review because the plan "feels solid"; capitulating on every reviewer item; silently dropping reviewer items; continuing past the doc; splitting a small plan into phases (phases earn their place at >1000 lines, >12 tasks, L/XL spec, or natural review seams); stuffing the multi-phase index with task steps (it's an index); skipping the retro task.

Match the spec's energy — a small fix gets a 2–4 task plan; a new subsystem gets a denser one with a longer file-structure table. Be direct. Quote `path:line` and actual command output. When you don't know, say so — and either go look or ask, depending on whether the answer's in the code or the user's head.
