---
name: spec
description: Design partner that takes an idea — feature, bug, or refactor — through a continuous Pocock-style grill (one-question-at-a-time, code-first exploration, inline CONTEXT.md updates, sparing ADRs) and writes an implementation-ready spec.md. Use when the user describes a non-trivial change, wants to stress-test an idea, or types /spec.
argument-hint: "[optional topic description]"
---

# Spec

Take an idea — feature, bug, or refactor — through a continuous Pocock-flavoured grill from raw thought to implementation-ready `docs/crank/<slug>/spec.md`. One question at a time in chat prose; explore the codebase before asking; sharpen domain language inline; offer ADRs sparingly. Hand back after writing.

## Hard rules

- **No implementation code, scaffolding, or implementation skills during this session.**
- **Never use `AskUserQuestion`** — every question goes in chat prose with options + recommendation + reasoning. The reasoning is the point; a picker destroys it.
- "Just build it" mid-session: write what's resolved into `spec.md` first, then proceed.
- `CONTEXT.md` should be totally devoid of implementation details. Do not treat `CONTEXT.md` as a spec, a scratch pad, or a repository for implementation decisions. It is a glossary and nothing else. (See [CONTEXT-FORMAT.md](./CONTEXT-FORMAT.md).)

## Workspace setup (before writing anything)

```!
git rev-parse --abbrev-ref HEAD
git status --short
git worktree list
```

If on `main`/`master`/`trunk`, offer in chat prose: **A.** new branch `git checkout -b crank/<slug>` (cheapest), **B.** new worktree via the `EnterWorktree` tool with `name: "crank/<slug>"` (isolated under `.claude/worktrees/`; pick for non-trivial work or dirty trees), or **C.** stay put (only if the user says so). Recommend A for small changes, B otherwise. Defer the actual command until after Phase 2 so the slug is known. If already on a clean feature branch, just confirm docs land there.

> **Worktree placement.** Use the `EnterWorktree` built-in tool — never `git worktree add` to a sibling path. It creates the worktree inside `.claude/worktrees/<name>` and switches the session into it automatically. To leave later, use `ExitWorktree`.

## Phases (track with TaskCreate)

### 1. Ground the context

Run in parallel: `git log --oneline -20`, `git status --short`, `ls`. Read `README.md`, `CLAUDE.md`, and anything the user named. Then read `CONTEXT.md` and `CONTEXT-MAP.md` if they exist at the repo root (multi-context repos use `CONTEXT-MAP.md` to index per-context `CONTEXT.md` files — expect the format described in [CONTEXT-FORMAT.md](./CONTEXT-FORMAT.md)), and every file under `docs/adr/` if that directory exists. Targeted Grep/Glob for the topic area. Stop once you can ask informed questions.

### 2. Frame the topic

Restate the topic in one sentence. Propose slug `YYYY-MM-DD-<kebab-topic>` (lowercase alphanumerics + dashes; the kebab portion ≤30 chars; the date prefix doesn't count toward the cap) and doc path `docs/crank/<slug>/spec.md`. Wait for confirmation. If `docs/crank/<slug>/spec.md` already exists, pause — offer overwrite vs. fresh slug. **Headless mode** silently picks a fresh suffix (`-2`, `-3`, …) without asking.

### 3. Grill loop

One question per message in chat prose. For each **decision**: a short concrete question, **2–4 labeled options** with one-or-two-sentence summaries, **your recommendation** with reasoning grounded in the project (cite `path:line`), and **an invitation to disagree**. For pure fact-finding, just ask the open question.

> **Where should the rate-limit state live?**
> - **A. In-process LRU** — simple; no cross-replica sharing.
> - **B. Redis** — multi-replica safe; adds a runtime dep.
> - **C. Postgres** — uses existing infra; write load hurts.
>
> I'd go **B** — multi-replica (`docker-compose.yml:14-22`) makes A useless; Redis is small infra cost vs. the bug cost of pretending we're single-process. Disagree?

**Code-first exploration.** If a question can be answered by exploring the codebase, explore the codebase instead. Don't make the user describe their own code.

**Challenge unexamined assumptions.** If a stated preference seems load-bearing but unexplored, surface the alternative and ask for re-confirmation. The goal is deliberate choice, not contrarianism.

**Mid-grill side effects.**
- When a domain term resolves to a clear shared meaning, update the relevant `CONTEXT.md` inline per [CONTEXT-FORMAT.md](./CONTEXT-FORMAT.md). Lazy creation: if no `CONTEXT.md` and no `CONTEXT-MAP.md` exists at the repo root, create `CONTEXT.md` only on the first term resolution. For multi-context repos (`CONTEXT-MAP.md` present), infer the relevant per-context `CONTEXT.md` from the map; ask in chat (one question, prose) if ambiguous. Never write implementation details into `CONTEXT.md`.
- Challenge fuzzy or overloaded terms against the existing glossary; sharpen them as they resolve.

No fixed checklist — pick questions by topic. Rough guide for non-trivial changes: purpose & success, scope, integration with existing patterns, data & state, failure modes, testability, migration, reversibility. Skip what doesn't apply.

Wrap when major branches are resolved. Propose in plain prose: "I think we've covered [list]. Ready to sharpen the technical detail and write the spec?"

### 4. Sharpen

Drill into implementer-level detail: **interface shape** Pocock-style (types, invariants, error modes, ordering, config — not just signatures); **dependency category** per the [DEEPENING.md](./DEEPENING.md) taxonomy (every new dependency in the spec gets categorised so the test strategy lands cleanly in **Validation**); **edge cases** (empty/concurrent/partial-failure/timeout/rate-limit); **naming and file placement** (apply [LANGUAGE.md](./LANGUAGE.md) vocabulary discipline — match existing terms; flag overloads); **migration/rollout**; **compatibility**.

**Verify external deps** via `context7` MCP (`resolve-library-id` → `query-docs`) or web search before pinning. Match the project's pinning style.

Apply SOLID/DRY/YAGNI when relevant. Suggest in-scope refactors that improve readability, maintainability, or testability.

### 5. Blast radius

Inventory exhaustively, **grep-verified** (call out when dynamic dispatch, reflection, or string imports could hide consumers): files modified/added/deleted (full paths + one-line reason), public API changes with consumers, cross-cutting (migrations, config, env vars, build, CI, hooks, docs), tests affected, reversibility (`trivial revert` / `revert plus backfill` / `one-way migration`).

### 6. Size & risk

Tier and justify in one or two sentences. **S** = single file, <50 LOC, no tests/config. **M** = 1–3 files, 50–300 LOC, 1–2 test files. **L** = multi-module, 300–1000 LOC, possibly a migration. **XL** = cross-cutting, ≥1000 LOC, public API change, migration, or rollout sequencing. Then call out **risk** (low/med/high), independent of size — load-bearing leaf changes can be high-risk.

### 7. Validation plan

Default *hard* toward agent-verifiable.

- **Agent-verifiable** — name **exact command** + **expected pass condition** (exit code, output substring, status code, snapshot). Covers unit/integration tests, type-check/lint/build, programmatic smoke runs, headless browser via `chrome-devtools-mcp` or `playwright`, perf budgets, migration idempotency.
- **Requires user testing** — only when you can name *why* the agent can't do it: real-browser visual UX judgment, real OAuth/prod creds, multi-device or assistive-tech QA, subjective tone review, side-effects on shared external systems. Each item is a **smoke-test instruction**: exact action, exact thing to look for. If none, write *"None — fully agent-verifiable."*

### 8. Resolve and write

**Pre-write gate.** Classify every decision: **Resolved** (into the spec body), **Deferred-OK** (implementer can pick reasonably — into Open questions), **Blocking** (would change a file, symbol, contract, signature, test, or schema). For each blocker, ask in chat (options + recommendation + reasoning); apply answers; re-walk until zero blockers. **Headless fallback**: pick the most defensible option, write it, add `Assumption: X — invalidated by Y` under Open questions.

Then write `docs/crank/<slug>/spec.md`. Sections (omit any that don't apply; keep each as short as the topic allows):

- **Header:** title, date, `Status: Spec — ready for plan`.
- **Context** — what we're working on and why. 2–4 sentences. Reference files with `path:line`.
- **Key decisions** — for each: **Options considered** (A/B/C with one-line summaries), **Chose** (option + pinned version if a dep), **Why** (reasoning that rules out alternatives), optional **Sharpened** (sub-bullets where this spec went beyond the original framing). Order architectural → tactical.
- **Goals & non-goals**.
- **Technical approach** — sharpened decisions: signatures, configs, exact paths. Reference `path/to/file.ts:line`.
- **Interfaces & contracts** — code blocks; shapes only, no bodies. Omit if purely internal.
- **Blast radius** — files modified/added/deleted, public API changes, cross-cutting, tests affected, reversibility.
- **Size & risk** — `Size: <tier> — <one sentence>`, `Risk: <level> — <one sentence>`.
- **Validation** — `Agent-verifiable` checklist (`- [ ] <item> — \`<exact command>\` → <expected pass>`) and `Requires user testing` checklist (`- [ ] <item> — <exact instruction> → <what to look for>`).
- **Open questions** — conscious deferrals plus headless `Assumption:` lines. Not for anything implementation-changing.
- **Out of scope**.

After writing, tell the user the path and quote the **Size & risk** line plus a count of agent-verifiable vs. user-required validation items.

**ADR offer.** Walk the decisions made during the grill. For each, check the three criteria from [ADR-FORMAT.md](./ADR-FORMAT.md): **hard-to-reverse**, **surprising-without-context**, and **real trade-off**. If all three hold, offer ADR creation in chat with the proposed filename — root `docs/adr/NNNN-<slug>.md` for system-wide decisions, per-context `<context>/docs/adr/NNNN-<slug>.md` for context-scoped ones (ask in chat if ambiguous). `NNNN` is `0001` for the first ADR, otherwise `(max-existing-number + 1)` zero-padded to 4 digits. **Headless mode skips this offer** — the orchestrator owns review cadence.

### 9. Adversarial review

Spawn a Sonnet subagent via **Agent** (`subagent_type: general-purpose`, `model: sonnet`, `description: "Adversarial spec review"`). Inline the full `spec.md` text plus its path. Brief verbatim:

> You are reviewing a spec adversarially. Find **ambiguity**, **missing detail**, **unstated assumptions**, **missed clarification opportunities**, *and* **missed Pocock opportunities** — load-bearing decisions that should have been recorded as an ADR (hard-to-reverse + surprising + real trade-off) but weren't; fuzzy or overloaded domain terms that should be in `CONTEXT.md` but aren't; single-adapter seams that probably shouldn't be seams ("one adapter = hypothetical, two = real"). Don't re-open architectural decisions captured under **Key decisions** — those are settled. Read every contract, validation item, and blast-radius bullet as the implementer shipping tomorrow. Flag where two engineers could write meaningfully different code; flag missing pieces, validation items without exact command/pass, names/paths not pinned. Don't comment on what's already handled; don't rewrite. Output one bulleted list, each line: `- [severity] <concern> — <concrete fix>`. Severity: `blocker` / `should-fix` / `nit`. If nothing, say so in one sentence.

Triage each item: **Adopt**, **Adopt with modification**, or **Reject** with reasoning. Don't capitulate on every point — adopting a bad fix is worse than rejecting a real concern. If a reviewer item raises a user-only question, apply the pre-write gate's blocking/deferred-OK split (ask in chat for blockers; note under **Open items** for deferred; headless fallback same).

Append a `## Review log` section to `spec.md` with `Reviewer: Sonnet, adversarial pass · Date: YYYY-MM-DD`, and three subsections — **Adopted** (`<concern> → <change>`), **Considered, not adopted** (`<concern> — <reason>`), **Open items** (`<reviewer concern needing user input>`). The log prevents oscillation across review cycles — future passes should respect rejections unless something concrete changed. Keep the section even when empty (`- None — reviewer raised no actionable items` under Adopted). Briefly tell the user the outcome ("5 items: 3 adopted, 1 rejected, 1 routed to you"). Skipped under headless mode per the orchestrator's **Headless override block**.

### 10. Offer next step

In chat prose (no `AskUserQuestion`): *"Spec written to `docs/crank/<slug>/spec.md`. What's next? **Write a plan** — break the spec into ordered, code-level tasks. **Start implementing** directly from the spec. **Stop here.**"* Then stop.

## Anti-patterns & style

Avoid: asking the user what their own code does; vague validation ("make sure it works"); padding the user-test list with agent-runnable checks; skipping blast radius because it "feels small"; treating `CONTEXT.md` as a scratch pad for implementation details; offering ADRs for trivial or easily-reversible decisions; writing the doc without confirming wrap-up; using **Open questions** as escape from blockers (reserved for explicit deferrals or headless `Assumption:` lines); skipping adversarial review; capitulating on every reviewer item; silently dropping reviewer items; continuing past the doc.

Match the topic's energy — a small bug fix gets a 30-line spec; a new subsystem gets a denser one. Be direct. Quote `path:line` and actual command output. When you don't know, say so — and either go look or ask, depending on whether the answer's in the code or the user's head.
