# Phase: Brainstorm

## Goal

Turn a raw idea into a **high-level design brief** at **design altitude**: the input the spec phase ([SPEC.md](SPEC.md)) turns into a full spec.

## Hard Rules

- **Stay at design altitude.** Settle *what* you're building and *which shape* it takes — not exact signatures, schemas, field names, or file-by-file breakdowns. Drill into a detail only when it's *load-bearing for a key decision* (if approach A vs. B hinges on whether the database supports X, resolve X; otherwise record it as an **Open question** for the spec).
- **Write the brief to `.crank/<slug>/brainstorm.md`** per [ARTIFACT-HOME.md](ARTIFACT-HOME.md) — read it before writing the file.

## Guidelines

**Design for isolation.** Give each piece of the Shape a **module**'s shape: one purpose, and an **interface** you can state without its internals. A piece you can't describe that way is a boundary that needs another pass. Name the boundaries here; designing the interfaces across them is the spec's job.

**Working in an existing codebase.** Follow the patterns you explored rather than inventing parallel ones. Where existing code genuinely gets in the way of the idea (a file that's grown too large, a tangled responsibility the work has to touch), fold a targeted improvement into the Approach. Propose no refactoring that doesn't serve the idea.

## Deliverables

The high-level design brief. Include the sections that apply; this is a brief, not a spec:

- **Header** — title, then `Grounding:` per [ARTIFACT-HOME.md](ARTIFACT-HOME.md) → Grounding.
- **Idea / Problem** — what the user wants and why, in their words.
- **Approach** — the chosen direction in a few sentences, plus the main alternatives considered and one line on why this one won (leverage / locality).
- **Shape** — the major pieces and how they relate: one line of responsibility each, and the data or control flow between them. A rough sketch or short list, not a file map.
- **Key decisions** — the consequential choices settled during brainstorming, each with one line on why; the spec inherits and details them.
- **Open questions** — technical decisions left for the spec to ground and settle; this list becomes the spec's grilling agenda. The admission test: the question is spec-level and you can state it precisely *now*. One you can't yet phrase that sharply is a design hole, not an open question — resolve it with the user before handing off.
- **Out of scope** — what was discussed and explicitly cut.

## Flow

### 1. Explore project context

Before asking the user anything, read recent commits, relevant docs, and the surfaces the idea would touch. Dispatch the wide reads with the **Explore the codebase** brief at References → Subagents.

Completion criterion: every surface the idea touches is named with the `file:line` you read it at, or "not found"; every established pattern the idea should follow is named with the existing feature that demonstrates it — none from assumption, each banked in-thread as a grounding entry ([ARTIFACT-HOME.md](ARTIFACT-HOME.md) → Grounding) until the step-6 flush, so an abandoned brainstorm leaves no directory behind.

### 2. Name the destination

Settle the problem being solved and what "done" means for the user, in one or two lines. The destination fixes scope: every later question, approach, and cut orients to it. If the user's opening message already states it, read your version back for confirmation instead of re-asking; if not, this is your first question.

Completion criterion: the user has explicitly confirmed the destination; it anchors the brief's **Idea / Problem** section.

### 3. Scope check

Before refining details, assess scope. If the idea describes several independent subsystems (e.g., "a platform with chat, file storage, billing, and analytics"), flag it now — don't spend questions polishing one corner of a project that needs decomposing first. Help the user split it: name the independent pieces, how they relate, and what order to build them. Then brainstorm the first sub-project through the normal flow; each sub-project gets its own brief → spec → plan → execute cycle.

Completion criterion: the idea is confirmed buildable as one project, or split — pieces named, order agreed, first sub-project chosen.

### 4. Grill the open questions

Walk the open design questions per [GRILLING.md](GRILLING.md) (read it here); the agenda it opens with is this phase's decision tree. If that fan-out shows the way from idea to spec is already clear, say so and offer to skip to the spec phase rather than manufacture a brainstorm.

- **Raise fidelity when words stall.** When a question is experiential, about how something should look, behave, or read, offer a throwaway artifact in place of the question and record the reaction as the answer: a sketch, a sample output or mock data shape, a single self-contained HTML file the user double-clicks and drives when the behavior is the question, or variants to compare per [PROTOTYPE.md](PROTOTYPE.md) when the look is the question, read once the user accepts. The brief records the artifact's path beside the decision it settled.

Completion criterion: the frontier is empty — every consequential design question settled with the user or recorded as an **Open question**, none waved past.

### 5. Propose approaches

Propose **2–3 approaches, each optimizing for a different thing**, conversationally, naming the axis each wins on and its trade-offs (e.g. fewest moving parts, most flexible for the likely next ask, closest to the existing idiom). Two approaches that optimize for the same thing are one approach; drop one. If two genuinely combine, recommend the hybrid rather than leaving the user to merge them. Lead with your recommendation and why. Prefer the approach whose central piece is **deeper**, and name the **leverage** and **locality** it buys over the alternatives. If an approach's key piece fails the **deletion test**, say so; that's a reason to drop it.

Completion criterion: the user has explicitly picked an approach (or your recommended hybrid) — having heard the options isn't a pick.

### 6. Draft the high-level brief

Once the user has picked the approach, write the brief file, every applicable Deliverables section shaped per the Guidelines. When the Shape involves a flow — data, control, or a user workflow — sketch it in the brief as a small plain-text diagram. Once the brief file exists, flush the entries banked at step 1 to the effort's grounding file.

Completion criterion: every applicable Deliverables section is in the brief file, the banked grounding entries are flushed, and the brief's header names the grounding file.

### 7. Read back the brief

Read back the brief per [SKILL.md](SKILL.md) → Phase gates, reading [READBACK.md](READBACK.md) here. Its message shows the Approach beside the alternatives it beat, the Shape's diagram, and each Open question as the sharp question it hands the spec.

### 8. Hand off

Hand off per [SKILL.md](SKILL.md) → Phase gates.

- **Next:** say "continue" to run the spec phase ([SPEC.md](SPEC.md)) on the approved brief now, or in a fresh session: `/crank spec .crank/<slug>/brainstorm.md`.

## References

### Subagents

**Facts are yours; decisions are the user's** — two jobs to dispatch: **explore the codebase** (does this surface exist, what pattern do analogous features follow, is a claim you're about to make true) and **research a topic** (compare libraries or approaches, find prior art — web search in scope). Both run at the **standard** tier; resolve the tier, and the dispatch-or-main-thread call, per [SUBAGENT-TIERS.md](SUBAGENT-TIERS.md): a loaded instruction file's preference first, its harness models only as the fallback. Dispatch each job with its brief below, filled in.

**Explore the codebase:**

<brief>
Explore `<area or claim>` in this codebase. We're brainstorming `<one-sentence idea>`. Read-only: change nothing in the codebase or on the machine.

Work your lookups in **rounds**: a round's **frontier** is every read or grep whose answer you do not need before issuing the next one; send the whole frontier as one batch in a single turn, read every return, then compose the next round from what came back.

Report:

- whether the surface or pattern in question exists, and the `file:line` where it lives (or "not found");
- one or two existing features that do something analogous, and the convention each follows (`file:line`);
- any canonical helper, module, or pattern an implementer would be expected to reuse or extend for this idea (`file:line`).

Report each item — one surface, one analogous feature, one helper — in a few sentences. Cite `file:line` instead of pasting the code around it, and quote source only where the exact text is the answer. An exact signature is the answer: reproduce it in full, however long. An item that outgrows a few sentences goes to a file in the OS temp dir, returned as its path plus a one-line summary.

Don't propose a design; surface what exists and what's true. If the claim I'm checking is wrong, say so plainly.
</brief>

**Research a topic** (web search in scope):

<brief>
Research `<question>` to inform a design decision. We're weighing `<the options on the table>`. Read-only: you may fetch and read, but do not install, uninstall, run vendor install scripts, or delete anything outside your own temp dir — anything that would require installing something is reported as an open question instead.

Report:

- the leading approaches or libraries, and for each what it optimizes for and its main trade-off;
- how comparable projects solve this, with a source link each;
- a recommendation for our context (`<one line of constraints>`) and what it gives up.

Cite sources, and flag what you're unsure of rather than asserting it.
</brief>

### Vocabulary

[VOCABULARY.md](VOCABULARY.md) → **Design language** — read that section before step 5; this phase uses its terms bare.
