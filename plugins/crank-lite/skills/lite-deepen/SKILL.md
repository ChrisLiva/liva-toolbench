---
name: lite-deepen
description: Scan a codebase for deepening opportunities — shallow modules, leaking
  seams — present them as chat cards with ASCII before/after diagrams, grill through
  your pick, and emit a brainstorm brief for the crank-lite pipeline. Use to improve
  codebase architecture, find refactor targets, or deepen modules.
argument-hint: "[module, subsystem, or pain point]"
disable-model-invocation: true
---

# Lite Deepen

Surface architectural friction and propose **deepening opportunities** — changes that turn shallow modules into deep ones. Aim at testability and navigability, not tidiness.

The whole run happens in chat: scope → explore → cards → grill → brief. No report file, no task tracking. The only thing written is the brief, plus the two target-repo side effects the user approves during the grill.

## Tone

The shared design language lives in [VOCABULARY.md](VOCABULARY.md) — read it before you write a card. Use these words, with these meanings, exactly: **module**, **interface**, **implementation**, **depth**, **deep**, **shallow**, **seam**, **adapter**, **leverage**, **locality**.

Near-synonyms blur the distinction each word carries. Never substitute:

| Use | Never |
| --- | --- |
| module | component, service, unit, layer, wrapper |
| interface | API, signature |
| seam | boundary |

That is the *architecture* vocabulary. The *domain* vocabulary comes from the target repo's own glossary: if its `CONTEXT.md` defines "Order", say "the Order intake module" — not "the FooBarHandler", and not "the Order service".

## Scope

Scope before you scan. Deepening pays off by making future changes to a module easier, so weight the parts of the codebase that keep changing.

- **The user's direction wins.** If they named a module, a subsystem, or a pain point, take it and skip the inference below.
- **Otherwise infer from churn.** Walk back a good stretch of history with `git log --oneline` and find the hot spots — the files and areas that keep coming up — and let those paths pull your attention first. If the changes are scattered with no clear hot spot, widen the net.

Before exploring, read the target repo's `CONTEXT.md` (its domain glossary) and any ADRs touching the area you're about to scan — commonly `docs/adr/`. Both are optional; skip whichever isn't there. ADRs record decisions this run should not re-litigate.

## Explore

Dispatch **one** standard-tier read-only explorer subagent (see Subagent tiers) with this brief, filled in. One dispatch, not a fan-out — ranking is the coordinator's job, on this thread.

<brief>
Explore `<scope>` in this codebase and report **deepening opportunities** — places where a shallow module could become a deep one. Read only: change nothing, and do not propose interfaces.

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

Report fewer than four rather than padding the list, and say so plainly if the scope is already deep.
</brief>

## Cards

Dedupe and rank what comes back yourself, and keep the **2–4** candidates the evidence actually supports. Drop overlaps into the strongest version of the same idea; drop anything you can't back with a `file:line`.

Present each survivor as one card in chat:

- **Title** — the deepening in a few words, in the repo's domain nouns.
- **Badge** — one of `Strong`, `Worth exploring`, `Speculative`.
- **Files** — what's involved.
- **Problem** — one sentence.
- **Solution** — one sentence.
- **Wins** — a few bullets, six words or fewer each, stated as **leverage** or **locality**.
- **Before / after** — a small ASCII diagram of the shallowness and the deepening. Chat renders mermaid as raw text, so draw in plain characters:

  ```
  before                                  after

  caller ──> parse_order                  caller ──> Order intake
  caller ──> validate_order                             │
  caller ──> normalize_order                ┌───────────┴───────────┐
  caller ──> save_order                     │ parse · validate ·    │
                                            │ normalize · save      │
  4 pieces of interface to learn            └───────────────────────┘
  call order known only to callers        1 interface; ordering held inside
  ```

- **Structural pseudo-code** (optional) — when the shape is hard to see from the diagram alone. **Structural only**: what the module exposes and what it hides, eight lines at most, and no committed signatures — no parameter lists, no return types, no names anyone will be held to. Interfaces are never proposed before the grill.

  ```
  module: Order intake
    exposes  one entry point for accepting a raw order
    hides    parsing, validation, normalization, persistence
    seam     the store it writes through
  ```

- **ADR callout** (optional) — only when the friction is real enough to warrant reopening a recorded decision. Mark it in the card: *"contradicts ADR-0007 — worth reopening because…"*. Don't list every refactor an ADR theoretically forbids.

Then ask, plainly, which candidate the user wants to pursue. **One candidate per grill loop.** The cards stay in the chat, so re-entry is cheap: when a loop ends, the user can come back and pick another card without a rescan.

## Grill

Run the grilling per [INTERVIEW.md](INTERVIEW.md) — read it before your first question. The agenda, which is also the decision tree to walk in rounds:

- **Constraints** — what can't move: callers you don't own, wire formats, performance floors, timelines.
- **Dependencies** — what the module leans on and who leans on it; which of those crossings deserves a port (two adapters justify a port; one is indirection).
- **The deepened module's shape** — what it owns, what its one entry point is for, what stays out.
- **What sits behind the seam** — what moves inside, what the seam hides, and exactly where it lands.
- **Which tests survive** — which existing tests keep testing behavior through the new interface, which were implementation-detail tests that die with the change, and what the new seam makes testable that wasn't.

Pseudo-code earns signatures here. As the shape firms up, sketch the interface at signature level so the user can veto a parameter or a return value rather than a paragraph. Keep it small and keep it in chat.

Two side effects land on the target repo during the grill. Offer each inline as the decision crystallizes — offer, never perform silently:

- **New or sharpened terms go to `CONTEXT.md`.** When the deepened module is named after a concept the glossary doesn't carry, or the conversation sharpens a fuzzy term, offer to write it into the target's `CONTEXT.md` right then. Create the file lazily if it doesn't exist.
- **A rejected recommendation earns an ADR** — only when the user rejects a load-bearing recommendation for a reason a future scan would need in order not to re-suggest it. Frame it: *"Want me to record this as an ADR so future scans don't re-suggest it?"* Skip ephemeral reasons ("not worth it right now") and self-evident ones.

## Brief

When the readback stands approved, write the brief to `.crank/deepen-brief-<slug>.md` at the working root — create `.crank/` if missing, with a `.crank/.gitignore` containing `*` so it never enters version control (outside a git repo, fall back to a temp file and say so). Nothing else lands in the repo. Tell the user the path once.

Sections, omitting any that didn't earn its place:

- **Idea / Problem** — the friction in the user's words, with the evidence `file:line`.
- **Approach** — the chosen deepening and why it won, in **leverage** and **locality** terms.
- **Shape** — the before/after ASCII diagram as amended during the grill, alongside the settled interface pseudo-code; signatures belong here, because the grill settled them.
- **Key decisions** — the consequential calls, one line of why each, including where the seam lands and which tests survive.
- **Open questions** — questions for the spec to answer, admitted only when you can state each one precisely now. Anything you can't phrase that sharply is a design hole — resolve it in the grill instead.
- **Out of scope** — the candidates that lost and one line each on why, plus pointers to any ADR this run wrote or left standing.

**No acceptance criteria** — those belong to the spec phase.

End by recommending the next step: `/crank-lite spec .crank/deepen-brief-<slug>.md`. A brainstorm brief is exactly what that route consumes, and the brief is self-contained, so a fresh session works as well as this one.

## Subagent tiers

The user's own configuration wins: if their global or project instructions state subagent model preferences, map the tier onto them. Otherwise resolve per harness:

<subagent-tiers>
- **standard** (codebase exploration): Claude Code `model: sonnet` · Codex GPT-5.6-Terra at medium effort · Cursor `cursor-composer-2-5`
</subagent-tiers>
