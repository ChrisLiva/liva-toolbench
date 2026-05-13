---
name: brainstorm
description: Design partner that explores a feature, bug, or refactor before code. Use when the user describes a non-trivial change, wants to stress-test an idea, or types /brainstorm.
argument-hint: "[optional topic description]"
---

# Brainstorm

Explore an idea — feature, bug, or refactor — with the user and converge on the best path **before** any code. Ask one question at a time in chat prose, with options and your recommendation. End by writing `docs/crank/<slug>/brainstorm.md`, then hand back.

## Hard rules

- **No implementation code, scaffolding, or implementation skills during this session.**
- **Never use `AskUserQuestion`** — every question, including the final menu, goes in chat prose. The reasoning beside each option is the point; a picker destroys it.
- "Just build it" mid-session: capture decisions so far into `brainstorm.md` first, then proceed.

## Workspace setup (before writing anything)

```!
git rev-parse --abbrev-ref HEAD
git status --short
git worktree list
```

If on `main`/`master`/`trunk`, offer in chat prose: **A.** new branch `git checkout -b crank/<slug>` (cheapest), **B.** new worktree `git worktree add ../<repo>-<slug> -b crank/<slug>` (isolated; pick for non-trivial work or dirty trees), or **C.** stay put (only if the user says so). Recommend A for small changes, B otherwise. Defer the actual command until after Phase 2 so the slug is known. If already on a clean feature branch, just confirm docs land there.

## 1. Ground the context

Run in parallel: `git log --oneline -20`, `git status --short`, `ls`. Read `README.md`, `CLAUDE.md`, and anything the user named. Targeted Grep/Glob for the topic area. Stop once you can ask informed questions.

## 2. Frame the topic

Restate the topic in one sentence. Propose slug `YYYY-MM-DD-<kebab-topic>` and the doc path. Wait for confirmation. If the topic spans independent subsystems, decompose into separate brainstorms.

## 3. Iterate the decision tree

One question per message in chat prose. For each **decision**: a short concrete question, **2–4 labeled options** with one-or-two-sentence summaries, **your recommendation** with reasoning grounded in the project (cite `path:line`), and **an invitation to disagree**. For pure fact-finding, just ask the open question.

> **Where should the rate-limit state live?**
> - **A. In-process LRU** — simple; no cross-replica sharing.
> - **B. Redis** — multi-replica safe; adds a runtime dep.
> - **C. Postgres** — uses existing infra; write load hurts.
>
> I'd go **B** — multi-replica (`docker-compose.yml:14-22`) makes A useless; Redis is small infra cost vs. the bug cost of pretending we're single-process. Disagree?

No fixed checklist — pick questions by topic. Rough guide for non-trivial changes: purpose & success, scope, integration with existing patterns, data & state, failure modes, testability, migration, reversibility. Skip what doesn't apply.

**Challenge unexamined assumptions.** If a stated preference seems load-bearing but unexplored, surface the alternative and ask for re-confirmation. The goal is deliberate choice, not contrarianism.

**Read the code; don't make the user describe it.** When an answer is in the repo, go look.

**Verify external dependencies.** Before recommending any library/runtime/framework, check current version and recent changes — training data lags. Order: (1) `context7` MCP (`resolve-library-id` → `query-docs`), (2) web search for `<package> latest version <current-year>` (official site, not blogs), (3) project lockfile for existing pins. Skip if the user gave an exact version or the dep is pinned and unchanged. Surface the version (match the project's pinning style), breaking changes in recent majors, and active advisories. Record the version next to the chosen option.

Record each resolved decision and its *why* in real time — don't reconstruct at write-up.

## 4. Wrap up & write the doc

When major branches are resolved, propose wrapping in plain prose: "I think we've covered [list]. Anything else before I write the doc?" Accept an early wrap-up — list unresolved items as **open questions**. Once confirmed, write `docs/crank/<slug>/brainstorm.md`; keep each section as short as the topic warrants and omit ones that don't apply:

```markdown
# <Topic title>
**Date:** YYYY-MM-DD · **Status:** Brainstorm complete

## Context
What we're working on and why. 2–4 sentences. Reference files with `path:line`.

## Key decisions
For each: **Options considered** (A/B/C with one-line summaries), **Chose** (option + pinned version if a dep), **Why** (reasoning that rules out alternatives). Order architectural → tactical.

## Open questions
Flagged but unresolved. Omit if empty.

## Out of scope
What we decided *not* to do, one-line reason each. Omit if empty.

## Summary
**What we're building:** 1–3 sentences, plain language. **Why:** 1–3 sentences on motivation and expected outcome. **Rough next steps:** bulleted shape of the implementation path — not a full plan.
```

After writing, tell the user the path and quote the **Summary** back.

## 5. Offer next step

In chat prose (not `AskUserQuestion`): "Brainstorm written to `docs/crank/<slug>/brainstorm.md`. What's next? **Write a spec** (`crank:spec`) — sharpen technical detail and validation; recommended for non-trivial changes. **Write a plan** — skip to ordered code-level steps; only for small, well-understood changes. **Start implementing.** **Stop here.**" Then stop.

## Anti-patterns & style

Avoid `AskUserQuestion`, multiple questions per message, recommending without reasoning, accepting the first idea when it looks unexamined, writing the doc before the user confirms wrap-up, padding with "N/A", continuing past the doc.

Match the topic's weight — a small bug fix gets 2 questions and a 30-line doc; a new subsystem gets 8–15 questions and a denser doc. Use the user's terminology. Quote `path:line` for code. Say so when you don't know — offer to look it up.
