---
name: crank-brainstorm
description: Brainstorm a raw idea into a high-level design brief before writing a spec — through dialogue, codebase exploration, and research. Use when the user wants to brainstorm, think an idea through, or explore approaches before building.
argument-hint: "[optional idea or topic]"
---

# Brainstorm

Turn a raw idea into a **high-level design brief** — the problem, the chosen approach, the major pieces and how they relate, the decisions that change everything downstream. The brief is the input to `crank:crank-spec`, which grounds it in the codebase, grills the open technical decisions, and writes the full spec. Stay at design altitude: settle *what* you're building and *which shape* it takes, not the signatures and schemas the spec and plan will pin down.

<subagent-tiers>
This skill spawns subagents at two tiers — resolve each to your harness (Claude Code / Codex / Cursor) per [SUBAGENT-TIERS.md](SUBAGENT-TIERS.md). **standard** = grounding, exploration, topic research; **heavy** = the downstream skills (brainstorm rarely needs it).
</subagent-tiers>

<rules>
- **Stay at design altitude.** A brainstorm settles the problem, the approach, the major pieces, and the consequential decisions — not exact signatures, schemas, field names, or file-by-file breakdowns. Drill into a detail only when it's *load-bearing for a key decision* (if approach A vs. B hinges on whether the database supports X, resolve X; otherwise leave it for the spec). When you catch yourself specifying something an implementer would type, you've dropped below altitude — pull back up.
- **Answer your own questions first.** If exploring the codebase or researching a topic could settle a question, dispatch a standard subagent to find out before asking the user. Reserve questions for what only the user knows — intent, priorities, preferences, external context.
- **Write the brief to a fresh OS temp file:** `$(mktemp -t crank-brainstorm).md`. Do not write into the working directory unless the user explicitly asks. Tell the user the path once.
- **Every subagent this skill spawns runs at the standard tier** (see <subagent-tiers>) unless otherwise specified.
</rules>

## Subagents

Lean on subagents for two jobs: **explore the codebase** (does this surface exist, what pattern do analogous features follow, is a claim you're about to make actually true) and **research a topic** (compare libraries or approaches, find prior art, check how others solve this) — the latter can use web search. Dispatch one the moment a question is answerable without the user, rather than asking them or guessing.

<tradeoff>
**Default:** a one-symbol lookup in a known file you do yourself; anything wider — a pattern sweep, a library comparison, prior-art research — you dispatch. Dispatch keeps your synthesis window clean and runs explorations in parallel; main-thread reading keeps the conversation's nuance but fills your window with source you'll never reread.
</tradeoff>

## Vocabulary

Shared design language across the crank pipeline, defined once in [VOCABULARY.md](VOCABULARY.md). This skill leans on **module**, **interface**, **depth** (and its payoffs, **leverage** / **locality**), and the **deletion test** when weighing one shape against another — read their meanings there.

## Workflow

Create a task for each step below and mark each one complete as you finish it — update them live as you go, not in a batch at the end — so the user can watch progress:

- Explore project context (recent commits, docs, the surfaces the idea touches — delegate wide reads)
- Scope check: one project, or decompose into sub-projects?
- Grill the open questions (one at a time, recommendation each; dispatch a subagent for anything the codebase or research can answer)
- Propose 2–3 approaches with trade-offs and a recommendation
- Draft the high-level brief (sections scaled to the idea, approval per section)
- Hand off (offer to continue to the spec)

## Explore project context first

Before asking the user anything, learn the lay of the land: recent commits, relevant docs, and the surfaces the idea would touch. **Bias toward delegating** wide reads to a standard subagent (see Subagents) so its window — not yours — holds the source. In an existing codebase, note the established patterns the idea should follow; you'll lean on them when proposing approaches.

## Scope check

Before refining details, assess scope. If the idea describes several independent subsystems (e.g., "a platform with chat, file storage, billing, and analytics"), flag it now — don't spend questions polishing one corner of a project that needs decomposing first. Help the user split it: name the independent pieces, how they relate, and what order to build them. Then brainstorm the first sub-project through the normal flow; each sub-project gets its own brief → spec → plan → execute cycle.

## Grill the open questions

Walk the design tree branch by branch, resolving dependencies between decisions one at a time until you and the user share a clear picture. This is the heart of the skill — keep at a question until it's genuinely settled, not waved past.

- **One question per message, in plain chat text** — not the structured-question UI, so you have room to show your reasoning. Lead with your recommended answer and the reasoning behind it, and wait for the response before the next question. Offer discrete options when the choice is genuinely between them — no forced lettering or length limits.
- **Explore before you ask.** If the codebase or a quick piece of research can answer it, dispatch a standard subagent and bring back the finding instead of putting the question to the user. Save their attention for intent, priorities, and preferences.
- **Stay at altitude.** Grill the decisions that shape *what* gets built and *which* approach wins. A technical detail earns a question only when it's load-bearing for one of those decisions; otherwise it's an **Open question** the spec will ground and settle — note it and move on.
- Focus on purpose, constraints, and success criteria — what done looks like, and what's explicitly not in this.

## Propose approaches

Once the shape is clear enough, propose **2–3 genuinely different approaches**, conversationally, with trade-offs. Lead with your recommendation and why. Reach for the Vocabulary here: prefer the approach whose central piece is *deeper* (more behavior behind a smaller interface), and name the leverage and locality the chosen shape buys over its alternative. If an approach's key piece fails the deletion test, say so — that's a reason to drop it.

## Draft the high-level brief

Once the user has signed off on the approach, crystallize it into the brief. Present it in sections, scaled to the idea — a few sentences where it's straightforward, a paragraph where it's nuanced — and check after each section that it reads right before moving on. Capture the approved sections in the temp file as you go; tell the user the path once.

Include whichever sections apply (omit ones that don't earn their place — this is a brief, not a spec):

- **Idea / Problem** — what the user wants and why, in their words.
- **Approach** — the chosen direction in a few sentences, plus the main alternatives considered and one line on why this one won (leverage / locality).
- **Shape** — the major pieces and how they relate: one line of responsibility each, and the data or control flow between them. High-level — no signatures or schemas. A rough sketch or short list, not a file map.
- **Key decisions** — the consequential choices settled during brainstorming, each with one line on why. These are what the spec inherits and details.
- **Open questions** — technical decisions deliberately left for the spec to ground and settle. This list becomes the spec's grilling agenda, so make each item a real, answerable question. *High-level design holes don't belong here — resolve those with the user before handing off; only genuinely spec-level detail goes on this list.*
- **Out of scope** — what was discussed and explicitly cut.

**Design for isolation and clarity.** When you describe the Shape, break the system into pieces that each have one clear purpose and communicate through a well-defined boundary. For each, you should be able to say what it does, how you'd use it, and what it depends on — without reading its internals. If you can't, the boundaries need another pass. (Hold this at altitude: you're naming boundaries, not designing interfaces — the spec does that.)

**Working in an existing codebase.** Let the structure you explored shape the brief: follow the established patterns rather than inventing parallel ones. Where existing code genuinely gets in the way of the idea (a file that's grown too large, a tangled responsibility the work has to touch), fold a targeted improvement into the Approach — the way a good engineer improves code they're working in. Don't propose unrelated refactoring; stay on what serves the idea.

## Hand off

The brief is the front door to the crank pipeline (brainstorm → spec → plan → execute). The natural next step is the spec, which turns this high-level brief into a full PRD-plus-technical-spec — grounding it in the codebase, grilling you on the **Open questions**, and adding acceptance criteria. In chat prose, offer:

- **Continue to the spec** (recommended) — run the `crank:crank-spec` skill. The approved brief is already in the conversation; tell the spec skill the brief's temp-file path so it can build straight on it.
- **Keep the temp file** — the path is known; the user can hand it to the spec skill later, feed it elsewhere, or move it.
- **Copy into the repo** — copy to a user-named path under the working directory.
- **Print inline and delete** — paste the final brief into the chat and remove the temp file.

Wait for the user's pick. Only invoke `crank:crank-spec` if they choose to continue — don't auto-advance past the hand-off.
