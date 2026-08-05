---
name: crank-deepen
description: Scan a codebase for deepening opportunities — shallow modules, leaking
  seams — present them as a visual HTML report, grill through your pick, and emit a
  brainstorm brief for the crank pipeline. Use to improve codebase architecture,
  find refactor targets, or deepen modules.
argument-hint: "[module, subsystem, or pain point]"
disable-model-invocation: true
---

# Deepen

## Goal

Surface architectural friction in an existing codebase and propose **deepening opportunities** — changes that turn shallow modules into deep ones. Aim at testability and navigability, not tidiness.

The run is: scope → parallel explorers → a visual HTML report of the candidates → a grill through the one the user picks → a brainstorm brief the crank pipeline routes to its **spec** phase. The report is what the *user* reads; the brief is what the *pipeline* reads.

## Hard Rules

- **The target repo is read-only.** This run scans, it doesn't refactor. The report and the brief go to the OS temp dir; the only things that may land in the working tree are the two deliberate side effects the user approves during the grill — a term written into `CONTEXT.md`, and an offered ADR. Nothing else, and neither of them silently.
- **The report is presentation only.** It exists to let the user *see* the candidates and pick one. It is never re-read as a source of truth — not by a later step of this run, not by the spec phase, not by a fresh session. Everything downstream needs travels in the brief.
- **One candidate per grill loop.** The user picks one card; the grill walks that one to ground. Re-entry is cheap for as long as the report file survives — when a loop ends, offer to reopen the report and pick another card rather than rescanning by reflex.
- **No interfaces before the grill.** Explorers don't propose them and cards don't commit to them. The single permitted exception is a card's **structural** pseudo-code panel — what a module exposes and what it hides — with no parameter lists, no return types, and no names anyone will be held to. Signatures are earned in the grill, not before it.
- **Explorers are read-only and standard tier.** They read, classify, and report; they change nothing, and they don't rank across each other's territory. Dedupe and ranking happen on this thread, where the whole picture is.

## Flow

Create a task for each step below and mark each complete as you finish it, live, so the user can watch progress.

### 1. Scope

Scope before you scan. Deepening pays off by making future changes to a module easier, so weight the parts of the codebase that keep changing.

- **The user's direction wins.** If they named a module, a subsystem, or a pain point, take it and skip the inference below.
- **Otherwise infer from churn.** Walk back a good stretch of history with `git log --oneline` and find the hot spots — the files and areas that keep coming up — and let those paths pull your attention first. If the changes are scattered with no clear hot spot, widen the net.

Before exploring, read the target repo's `CONTEXT.md` (its domain glossary) and any ADRs touching the area you're about to scan — commonly `docs/adr/`. Both are optional; skip whichever isn't there. ADRs record decisions this run should not re-litigate.

Then do the explorer arithmetic — how many explorers, and what each one owns:

- **One territory per hot spot: 2–4 explorers, hard cap 4.** Carve the scope into territories along the hot spots, one explorer each, and name them so no two overlap. Four is the ceiling however many hot spots you found — fold the weakest into the neighbouring territory rather than adding a fifth.
- **No clear hot spots?** Split by code structure instead — top-level directories, subsystems, layers — same 2–4 count. Churn is the better carve when it exists; structure is the fallback when history is too scattered to point anywhere.
- **A small repo gets 1.** A scope one explorer can read end to end isn't worth splitting; splitting it just buys duplicate reading.
- **Explicit user direction gets 1.** The user already carved the territory. Send one explorer at what they named.

Completion criterion: the scope is fixed, and the explorer count and each explorer's territory are named — from the history and the tree, not from a guess.

### 2. Explore

Dispatch the explorers from step 1 **in parallel, in a single batch** — each read-only, each at the **standard** tier (References → Subagents), each holding this brief filled in for its own territory.

<brief>
Explore `<territory>` in this codebase and report **deepening opportunities** — places where a shallow module could become a deep one. Read only: change nothing, and do not propose interfaces. Other explorers cover the rest of the codebase; stay inside your territory.

Hunt four friction patterns:

- **Shallow module** — the interface exposes nearly as much as the implementation hides. Apply the **deletion test**: imagine the module gone. Does its complexity *concentrate* — collapsing into a deeper neighbor — or does it merely spread across every caller? "Concentrates" is the signal worth reporting; "spreads" means the boundary earned its place, so drop it. Needing to bounce between many small modules to understand one concept is the same smell at scale.
- **Seam leakage** — tightly-coupled modules leak across their seam: callers reach past the interface into internals, depend on call ordering the interface never states, or hold knowledge the module should own.
- **Extracted for testability without locality** — pure functions pulled out so they could be tested in isolation, while the real bugs live in how they are called. The extraction bought coverage but no **locality**.
- **Untestable through the interface** — code that is untested, or that cannot be driven through its current interface without a synthetic stand-in.

Explore organically rather than by rigid heuristic: note where *you* hit friction reading the code, then classify it.

Return **at most 4** candidates, strongest first. For each:

- **files** — the files or modules involved
- **friction pattern** — which of the four
- **deletion-test verdict** — one line: what happens to the complexity if this module goes
- **evidence** — `file:line` references a reader can check
- **problem** — one sentence on the friction it causes today
- **solution** — one sentence on what would change

Report fewer than four rather than padding the list, and say so plainly if the territory is already deep.
</brief>

Completion criterion: every dispatched explorer has returned, and each returned candidate carries a `file:line` you could open.

### 3. Report

Synthesis happens **here, on this thread** — each explorer saw one territory; only you see all of them.

Dedupe and rank the returns yourself: merge overlapping candidates into the strongest version of the same idea, drop anything you can't back with a `file:line`, and keep the **3–6** the evidence actually supports, strongest first. Then pick the one you'd tackle first and say why in a sentence — that's the report's top recommendation.

Read [VOCABULARY.md](VOCABULARY.md) (References → Vocabulary) before you write a card, and the target repo's `CONTEXT.md` names the domain nouns: if it defines "Order", the candidate is about "the Order intake module", not "the FooBarHandler" and not "the Order service".

Render the report per [HTML-REPORT.md](HTML-REPORT.md) — read that file here — as a single self-contained HTML file in the OS temp dir: `${TMPDIR:-/tmp}/deepen-report-<timestamp>.html`, a fresh file per run so an earlier report is never overwritten. Nothing lands in the repo.

Open it for the user with whichever opener the platform has — `open` on macOS, `xdg-open` on Linux, `start` on Windows — and tell them the **absolute path** in chat, so they can reopen it later without hunting for it.

Then ask, plainly, which candidate they want to pursue. One per loop (Hard Rules).

Completion criterion: the report is written, opened, its absolute path stated, and the user's pick is in hand — having shown the report is not a pick.

### 4. Grill

Run the grilling per [GRILLING.md](GRILLING.md) — read it before your first question. The agenda, which is also the decision tree to walk in rounds:

- **Constraints** — what can't move: callers you don't own, wire formats, performance floors, timelines.
- **Dependencies** — what the module leans on and who leans on it; which of those crossings deserves a port (two adapters justify a port; one is indirection).
- **The deepened module's shape** — what it owns, what its one entry point is for, what stays out.
- **What sits behind the seam** — what moves inside, what the seam hides, and exactly where it lands.
- **Which tests survive** — which existing tests keep testing behavior through the new interface, which were implementation-detail tests that die with the change, and what the new seam makes testable that wasn't.

Pseudo-code earns signatures here. As the shape firms up, sketch the interface at signature level so the user can veto a parameter or a return value rather than a paragraph. Keep it small and keep it in chat.

Two side effects land on the target repo during the grill. Offer each inline as the decision crystallizes — offer, never perform silently:

- **New or sharpened terms go to `CONTEXT.md`.** When the deepened module is named after a concept the glossary doesn't carry, or the conversation sharpens a fuzzy term, offer to write it into the target's `CONTEXT.md` right then. Create the file lazily if it doesn't exist.
- **A rejected recommendation earns an ADR** — only when the user rejects a load-bearing recommendation for a reason a future scan would need in order not to re-suggest it. Frame it: *"Want me to record this as an ADR so future scans don't re-suggest it?"* Skip ephemeral reasons ("not worth it right now") and self-evident ones.

**Design it twice — offer, never auto-run.** When the deepened module's **interface** turns out to be the contested node of the grill — the shape keeps moving, or two framings each look defensible — offer to settle it by building both: dispatch **2–3 heavy**-tier subagents in parallel (References → Subagents), each briefed to propose a *radically different* interface for that one module, not three shades of the same idea. Compare the returns in glossary terms — which is **deeper** (more behavior behind a smaller interface), which buys more **leverage** at the call sites, which concentrates **locality** — and put the comparison to the user, who picks one, asks for a hybrid, or declines. Never launch it unasked: it's a detour the user chooses, and the grill continues without it just fine.

Completion criterion: the frontier is empty — every agenda branch visited, both side effects either done or explicitly declined, and nothing about the chosen deepening left silently assumed.

### 5. Brief

Once the grill's frontier is empty and the user has approved the shape, write the brief to a new temp file in the OS temp dir — e.g. `${TMPDIR:-/tmp}/deepen-brief-<slug>.md`. Nothing else lands in the repo. Tell the user the path once.

Sections, omitting any that didn't earn its place:

- **Idea / Problem** — the friction in the user's words, with the evidence `file:line`.
- **Approach** — the chosen deepening and why it won, in **leverage** and **locality** terms.
- **Shape** — the before/after as an ASCII diagram (see below), amended for whatever the grill changed, alongside the settled interface pseudo-code; signatures belong here, because the grill settled them.
- **Key decisions** — the consequential calls, one line of why each, including where the seam lands and which tests survive.
- **Open questions** — questions for the spec to answer, admitted only when you can state each one precisely now. Anything you can't phrase that sharply is a design hole — resolve it in the grill instead.
- **Out of scope** — the candidates that lost and one line each on why, plus pointers to any ADR this run wrote or left standing.

**Translate the chosen card's diagram into ASCII.** The card's before/after lives in the HTML report, and the report is presentation only (Hard Rules) — the brief has to carry the picture on its own, in plain characters a fresh session can read. Don't transcribe the markup; redraw what the diagram *argued*. Whatever it made obvious at a glance has to survive the translation: the thin shallow pieces against the one thick deep module, where the seam falls, what leaks across it. Boxes, arrows, and a label or two are enough — if it needs a paragraph to be understood, redraw it.

A worked translation:

```
before                                after
┌─────────┐  ┌───────────┐          ┌──────────────────────┐
│ handler │─→│ validator │          │     order intake     │
└────┬────┘  └─────┬─────┘          │  (validator, repo,   │
     ▼             ▼                │   pricing internal)  │
┌─────────┐  ┌───────────┐         └──────────┬───────────┘
│  repo   │─→│  pricing  │  leak              │ one interface
└─────────┘  └───────────┘          ──────── seam ────────
```

**No acceptance criteria** — those belong to the spec phase.

End by recommending the next step: run `/crank` on this brief and take the **spec** route. A brainstorm brief is exactly what its triage sends there, and the brief is self-contained, so a fresh session works as well as this one.

Completion criterion: the brief file exists with every section that earned its place, its path is stated once, and the spec route is recommended — the next phase is the user's to start, never yours.

## References

### Subagents

This skill spawns subagents at two tiers — resolve each to your harness (Claude Code / Codex / Cursor) per [SUBAGENT-TIERS.md](SUBAGENT-TIERS.md). **standard** = the read-only explorers of Flow step 2, the bulk of the run's dispatch; **heavy** = the design-it-twice interface proposals of Flow step 4, the only heavy dispatch this skill makes and only on the user's say-so.

### Vocabulary

Shared design language across the crank pipeline, defined once in [VOCABULARY.md](VOCABULARY.md) — read it before you write a card. This skill leans on **module**, **interface**, **implementation**, **depth** (**deep** / **shallow**), the **deletion test**, **seam**, **port / adapter**, and depth's two payoffs, **leverage** and **locality**. Use these words, with these meanings, exactly.

Near-synonyms blur the distinction each word carries. Never substitute:

| Use | Never |
| --- | --- |
| module | component, service, unit, layer, wrapper |
| interface | API, signature |
| seam | boundary |

That is the *architecture* vocabulary. The *domain* vocabulary comes from the target repo's own glossary: if its `CONTEXT.md` defines "Order", say "the Order intake module" — not "the FooBarHandler", and not "the Order service".
