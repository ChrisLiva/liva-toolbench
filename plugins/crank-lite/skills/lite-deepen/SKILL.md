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

The run happens in chat: scope → explore → cards → grill → brief. It writes only the brief and the two target-repo side effects the user approves during the grill.

## Tone

Read [VOCABULARY.md](VOCABULARY.md) before you write a card. Use these words, with these meanings, exactly: **module**, **interface**, **implementation**, **depth**, **deep**, **shallow**, **seam**, **adapter**, **leverage**, **locality**.

Never substitute a near-synonym:

| Use | Never |
| --- | --- |
| module | component, service, unit, layer, wrapper |
| interface | API, signature |
| seam | boundary |

Domain nouns come from the target repo's own glossary: if its `CONTEXT.md` defines "Order", say "the Order intake module", not "the FooBarHandler" or "the Order service".

## Scope

Scope before you scan; deepening pays off on code that keeps changing.

- **The user's direction wins.** If they named a module, subsystem, or pain point, take it.
- **Otherwise infer from churn.** Rank paths by how often they appear in a good stretch of `git log --name-only` history and scan the top of the list first; if churn is scattered with no clear hot spot, widen the net.

Before exploring, read, where they exist, the target repo's `CONTEXT.md` (its domain glossary) and any ADRs touching the area you'll scan (commonly `docs/adr/`), whose decisions this run does not re-litigate. Read too the Grounding section of any crank-lite artifact the run was handed, verify-then-trusted per [ARTIFACT-HOME.md](ARTIFACT-HOME.md) → Grounding.

## Explore

Dispatch **one** standard-tier read-only explorer subagent ([INTERVIEW.md](INTERVIEW.md) → Subagent tiers) with this brief, filled in.

<brief>
Explore `<scope>` in this codebase and report **deepening opportunities** — places where a shallow module could become a deep one. Read only: change nothing, and do not propose interfaces.

Hunt four friction patterns:

- **Shallow module** — the interface exposes nearly as much as the implementation hides. Apply the **deletion test**: imagine the module gone. Does its complexity *concentrate* into a deeper neighbor (report it), or merely spread across every caller (drop it, the boundary earned its place)? Bouncing between many small modules to understand one concept is the same smell at scale.
- **Seam leakage** — callers reach past a module's interface into its internals, depend on call ordering the interface never states, or hold knowledge the module should own.
- **Extracted for testability without locality** — pure functions pulled out to be tested in isolation, while the real bugs live in how they are called.
- **Untestable through the interface** — code that is untested, or that cannot be driven through its current interface without a synthetic stand-in.

Note where *you* hit friction reading the code, then classify it.

Return **at most 4** candidates, strongest first. For each:

- **files** — the files or modules involved
- **friction pattern** — which of the four
- **deletion-test verdict** — one line: what happens to the complexity if this module goes
- **evidence** — anchors a reader can check, each `` `<path>` → `<symbol>` `` with every name spelled as the source spells it, or `` `<path>:<line>` (no symbol) `` where no symbol can be named
- **problem** — one sentence on the friction it causes today
- **solution** — one sentence on what would change

Report fewer than four rather than padding the list, and say so plainly if the scope is already deep.
</brief>

## Cards

Dedupe and rank what comes back: fold overlaps into the strongest version, drop anything you can't back with an anchor, and keep the **2–4** the evidence supports.

Present each survivor as one card in chat:

- **Title** — the deepening in a few words, in the repo's domain nouns.
- **Badge** — one of `Strong`, `Worth exploring`, `Speculative`.
- **Files** — what's involved.
- **Problem** — one sentence.
- **Solution** — one sentence.
- **Wins** — a few short bullets, stated as **leverage** or **locality**.
- **Before / after** — a small ASCII diagram of the shallowness and the deepening; chat renders mermaid as raw text:

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

- **Structural pseudo-code** (optional) — when the diagram alone doesn't show the shape: what the module exposes and what it hides, in a few lines, with no signatures — no parameter lists, return types, or names anyone will be held to.

  ```
  module: Order intake
    exposes  one entry point for accepting a raw order
    hides    parsing, validation, normalization, persistence
    seam     the store it writes through
  ```

- **ADR callout** (optional) — only when the friction justifies reopening a recorded decision, marked in the card: *"contradicts ADR-0007 — worth reopening because…"*. Don't list every refactor an ADR theoretically forbids.

Then ask, plainly, which candidate the user wants to pursue. **One candidate per grill loop.** The cards stay in chat, so picking another when this loop ends costs no rescan.

## Grill

Run the grilling per [INTERVIEW.md](INTERVIEW.md) — read it before your first question. The agenda, which is also the decision tree:

- **Constraints** — what can't move: callers you don't own, wire formats, performance floors, timelines.
- **Dependencies** — what the module leans on and who leans on it; which of those crossings deserves a port (two adapters justify a port; one is indirection).
- **The deepened module's shape** — what it owns, what its one entry point is for, what stays out.
- **What sits behind the seam** — what moves inside, what the seam hides, and exactly where it lands.
- **Which tests survive** — which existing tests keep testing behavior through the new interface, which implementation-detail tests die with the change, and what the new seam makes testable that wasn't.

Pseudo-code earns signatures here: as the shape firms up, sketch the interface at signature level, small and in chat, so the user can veto a parameter or a return value rather than a paragraph.

Offer each of the grill's two target-repo side effects inline as its decision crystallizes; never perform one silently:

- **New or sharpened terms go to `CONTEXT.md`** — when the deepened module is named after a concept the glossary doesn't carry, or the conversation sharpens a fuzzy term. Create the file if it doesn't exist.
- **A rejected recommendation earns an ADR** — only when the user rejects a load-bearing recommendation for a reason a future scan needs to avoid re-suggesting it. Frame it: *"Want me to record this as an ADR so future scans don't re-suggest it?"* Skip ephemeral reasons ("not worth it right now") and self-evident ones.

## Brief

When the grill's frontier is empty, write the brief to `.crank/<slug>/deepen-brief.md` per [ARTIFACT-HOME.md](ARTIFACT-HOME.md) — read it before writing the file. Then read it back per [READBACK.md](READBACK.md).

Sections, omitting any that didn't earn its place:

- **Idea / Problem** — the friction in the user's words, with the evidence anchor.
- **Approach** — the chosen deepening and why it won, in **leverage** and **locality** terms.
- **Shape** — the before/after ASCII diagram as amended during the grill, alongside the settled interface pseudo-code.
- **Key decisions** — the consequential calls, one line of why each, including where the seam lands and which tests survive.
- **Open questions** — only those you can state precisely now, for the spec to answer; one you can't phrase that sharply is a design hole to resolve in the grill.
- **Grounding** — the grill's banked entries, one line each ([ARTIFACT-HOME.md](ARTIFACT-HOME.md) → Grounding).
- **Out of scope** — the losing candidates, one line each on why, plus pointers to any ADR this run wrote or left standing.

**No acceptance criteria** — those belong to the spec phase.

Write the brief so a fresh session can run it without this chat. Once the readback is done, end by recommending `/crank-lite spec .crank/<slug>/deepen-brief.md`.
