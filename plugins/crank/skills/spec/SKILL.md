---
name: spec
description: Promotes a brainstorm.md into a sibling spec.md with sharpened technical decisions, blast radius, and validation criteria. Use after a brainstorm exists and the user types /spec or asks to write the spec.
argument-hint: "[optional path to brainstorm.md or its directory]"
---

# Spec

Sharpen `brainstorm.md` into an implementation-ready `<brainstorm-dir>/spec.md` so a planner — or you tomorrow — can break it into steps without further design questions. Then hand back.

## Hard rules

- **No implementation code, scaffolding, or implementation skills during this session.**
- **Never use `AskUserQuestion`** — every question goes in chat prose with options + recommendation + reasoning. The reasoning is the point; a picker destroys it.
- "Just build it" mid-session: write what's resolved into `spec.md` first, then proceed.

## Setup

Check git state (`git rev-parse --abbrev-ref HEAD`, `git status --short`, `git worktree list`). If brainstorm already created `crank/<slug>`, confirm and continue. If on `main`/`master`/`trunk`, offer in chat prose: **A.** new branch (default), **B.** new worktree via the `EnterWorktree` tool with `name: "crank/<slug>"` (dirty tree or L/XL — lands under `.claude/worktrees/`), or **C.** stay put (only if user says so). Wait for confirmation. Never `git worktree add` to a sibling path; always use `EnterWorktree`.

Locate the brainstorm: (1) `$ARGUMENTS` if it points to `brainstorm.md` or its directory, (2) auto-detect via `ls -1t docs/crank/*/brainstorm.md | head -5` — use it if exactly one; if multiple, list with mtimes and ask, (3) none — say so and offer `crank:brainstorm` rather than fabricating one. Read it in full first.

## Phases (track with TaskCreate)

### 1. Ingest

State back in 2–3 sentences: what the change is, the most load-bearing brainstorm decision, what you'll need to sharpen. Ask once: *"Does this still reflect what you want, or has anything shifted?"* Capture changes under **Updates since brainstorm**; don't overwrite the brainstorm itself — it's a record of the decision moment.

### 2. Re-ground in code

Run `git log --oneline -20` and `git status --short`. Read every file the brainstorm references plus immediate neighbors (siblings, call sites, related tests). For each touched module, know its public interface, tests, and conventions (errors, async, types, naming). Stop when you can describe the existing system without guessing. Explore unanticipated areas too — and report what you found.

### 3. Sharpen

Walk brainstorm decisions and find what's under-specified for an implementer: interface shape (signatures, types, errors), data flow, edge cases (empty/concurrent/partial-failure/timeout/rate-limit), configuration, naming & file placement, migration/rollout, compatibility. For each gap:

- **Explore first** when the answer is in the codebase — don't make the user describe their own code.
- **Ask in chat** only for judgment calls: 2–4 options, your recommendation, your reasoning, an invitation to disagree.
- **Verify external deps** via `context7` MCP (`resolve-library-id` → `query-docs`) or web search before pinning. Match the project's pinning style.

Apply SOLID/DRY/YAGNI when relevant. Suggest in-scope refactors that improve readability, maintainability, or testability.

### 4. Blast radius

Inventory exhaustively, **grep-verified** (call out when dynamic dispatch, reflection, or string imports could hide consumers): files modified/added/deleted (full paths + one-line reason), public API changes with consumers, cross-cutting (migrations, config, env vars, build, CI, hooks, docs), tests affected, reversibility (`trivial revert` / `revert plus backfill` / `one-way migration`).

### 5. Estimate size & risk

Tier and justify in one or two sentences. **S** = single file, <50 LOC, no tests/config. **M** = 1–3 files, 50–300 LOC, 1–2 test files. **L** = multi-module, 300–1000 LOC, possibly a migration. **XL** = cross-cutting, ≥1000 LOC, public API change, migration, or rollout sequencing. Then call out **risk** (low/med/high), independent of size — load-bearing leaf changes can be high-risk.

### 6. Validation plan

Default *hard* toward agent-verifiable.

- **Agent-verifiable** — name **exact command** + **expected pass condition** (exit code, output substring, status code, snapshot). Covers unit/integration tests, type-check/lint/build, programmatic smoke runs, headless browser via `chrome-devtools-mcp` or `playwright`, perf budgets, migration idempotency.
- **Requires user testing** — only when you can name *why* the agent can't do it: real-browser visual UX judgment, real OAuth/prod creds, multi-device or assistive-tech QA, subjective tone review, side-effects on shared external systems. Each item is a **smoke-test instruction**: exact action, exact thing to look for. If none, write *"None — fully agent-verifiable."*

### 7. Resolve and write

**Pre-write gate.** Classify every decision: **Resolved** (into the spec body), **Deferred-OK** (implementer can pick reasonably — into Open questions), **Blocking** (would change a file, symbol, contract, signature, test, or schema). For each blocker, ask in chat (options + recommendation + reasoning); apply answers; re-walk until zero blockers. **Headless fallback**: pick the most defensible option, write it, add `Assumption: X — invalidated by Y` under Open questions.

Then write `<brainstorm-dir>/spec.md`. Sections (omit any that don't apply; keep each as short as the topic allows):

- **Header:** title, date, `Status: Spec — ready for plan`, link to `./brainstorm.md`
- **Updates since brainstorm** · **Goals & non-goals**
- **Technical approach** — sharpened decisions: where brainstorm said "use Redis," give the exact key schema, TTL, eviction policy, client at a pinned version. Reference `path/to/file.ts:line`.
- **Interfaces & contracts** — signatures, types, message shapes, route handlers, event payloads. Code blocks; shapes only, no bodies. Omit if purely internal.
- **Blast radius** — files modified/added/deleted, public API changes, cross-cutting, tests affected, reversibility.
- **Size & risk** — `Size: <tier> — <one sentence>`, `Risk: <level> — <one sentence>`.
- **Validation** — `Agent-verifiable` checklist (`- [ ] <item> — \`<exact command>\` → <expected pass>`) and `Requires user testing` checklist (`- [ ] <item> — <exact instruction> → <what to look for>`).
- **Open questions** — conscious deferrals plus headless `Assumption:` lines. Not for anything implementation-changing.
- **Out of scope**

After writing, tell the user the path and quote the **Size & risk** line plus a count of agent-verifiable vs. user-required validation items.

### 8. Adversarial review

Spawn a Sonnet subagent via **Agent** (`subagent_type: general-purpose`, `model: sonnet`, `description: "Adversarial spec review"`). Inline the full `spec.md` text plus its path and the brainstorm path. Brief verbatim:

> You are reviewing a spec adversarially. Find **ambiguity**, **missing detail**, **unstated assumptions**, **missed clarification opportunities** — not architecture (brainstorm settled that). Read every contract, validation item, and blast-radius bullet as the implementer shipping tomorrow. Flag where two engineers could write meaningfully different code; flag missing pieces, validation items without exact command/pass, names/paths not pinned. Don't comment on what's already handled; don't rewrite. Output one bulleted list, each line: `- [severity] <concern> — <concrete fix>`. Severity: `blocker` / `should-fix` / `nit`. If nothing, say so in one sentence.

Triage each item: **Adopt**, **Adopt with modification**, or **Reject** with reasoning. Don't capitulate on every point — adopting a bad fix is worse than rejecting a real concern. If a reviewer item raises a user-only question, apply the pre-write gate's blocking/deferred-OK split (ask in chat for blockers; note under **Open items** for deferred; headless fallback same).

Append a `## Review log` section to `spec.md` with `Reviewer: Sonnet, adversarial pass · Date: YYYY-MM-DD`, and three subsections — **Adopted** (`<concern> → <change>`), **Considered, not adopted** (`<concern> — <reason>`), **Open items** (`<reviewer concern needing user input>`). The log prevents oscillation across review cycles — future passes should respect rejections unless something concrete changed. Keep the section even when empty (`- None — reviewer raised no actionable items` under Adopted). Briefly tell the user the outcome ("5 items: 3 adopted, 1 rejected, 1 routed to you").

### 9. Offer next step

In chat prose (no `AskUserQuestion`): *"Spec written to `<brainstorm-dir>/spec.md`. What's next? **Write a plan** — break the spec into ordered, code-level tasks. **Start implementing** directly from the spec. **Stop here.**"* Then stop.

## Anti-patterns & style

Avoid: asking the user what their own code does; vague validation ("make sure it works"); padding the user-test list with agent-runnable checks; skipping blast radius because it "feels small"; re-litigating brainstorm decisions (surface shifts under **Updates since brainstorm**); writing the doc without confirming wrap-up; using **Open questions** as escape from blockers (reserved for explicit deferrals or headless `Assumption:` lines); skipping adversarial review; capitulating on every reviewer item; silently dropping reviewer items; continuing past the doc.

Match the brainstorm's energy — a small bug fix gets a 30-line spec; a new subsystem gets a denser one. Be direct. Quote `path:line` and actual command output. When you don't know, say so — and either go look or ask, depending on whether the answer's in the code or the user's head.
