# Phase: Brainstorm

## Goal

Turn a raw idea into a **high-level design brief** — the problem, the chosen approach, the major pieces and how they relate, and the decisions that change everything downstream, all at **design altitude**. It's the input to the spec phase ([SPEC.md](SPEC.md)), which turns the brief into a full spec.

## Hard Rules

- **Stay at design altitude.** Settle *what* you're building and *which shape* it takes — not exact signatures, schemas, field names, or file-by-file breakdowns. Drill into a detail only when it's *load-bearing for a key decision* (if approach A vs. B hinges on whether the database supports X, resolve X; otherwise leave it for the spec). When you catch yourself specifying something an implementer would type, you've dropped below altitude — pull back up.
- **Write the brief to `.crank/<slug>/brainstorm.md` at the working root** — one directory per effort, the durable artifact home every crank phase shares, so a later session resumes from the file, not from a pasted path; if `.crank/<slug>/` already holds a *different* effort (judge by content, not name), use `<slug>-2`, `<slug>-3`, …, never renaming an existing directory — create `.crank/` if missing, with a `.crank/.gitignore` containing `*` so the directory never enters version control; only outside a git repo, fall back to `${TMPDIR:-/tmp}/crank-<slug>/brainstorm.md` and say so. Handed a legacy flat artifact (`.crank/<phase>-<slug>.md`), move it to its per-plan home first and state the new path. Tell the user the path once. Write nothing else into the working tree unless the user explicitly asks.

## Guidelines

**Design for isolation.** Describe each piece of the Shape as a **module** with one clear purpose and a clean boundary — you should be able to say what it does, how you'd use it, and what it depends on without reading its internals. If you can't, the boundaries need another pass. (You're naming the boundaries here, not designing the interfaces across them — that's the spec's job.)

**Working in an existing codebase.** Let the structure you explored shape the brief: follow the established patterns rather than inventing parallel ones. Where existing code genuinely gets in the way of the idea (a file that's grown too large, a tangled responsibility the work has to touch), fold a targeted improvement into the Approach — the way a good engineer improves code they're working in. Don't propose unrelated refactoring; stay on what serves the idea.

## References

### Subagents

**Answer your own questions first.** If exploring the codebase or researching a topic could settle a question, dispatch a standard subagent to find out before asking the user. Reserve questions for what only the user knows — intent, priorities, preferences, external context.

Lean on subagents for two jobs: **explore the codebase** (does this surface exist, what pattern do analogous features follow, is a claim you're about to make actually true) and **research a topic** (compare libraries or approaches, find prior art, check how others solve this) — the latter can use web search. Both run at the **standard** tier; resolve the tier to your harness (Claude Code / Codex / Cursor), and the dispatch-or-main-thread call, per [SUBAGENT-TIERS.md](SUBAGENT-TIERS.md).

Dispatch each job with the matching brief, filled in.

**Explore the codebase:**

<brief>
Explore `<area or claim>` in this codebase. We're brainstorming `<one-sentence idea>`. Read-only: change nothing in the codebase or on the machine.

Report:

- whether the surface or pattern in question exists, and the `file:line` where it lives (or "not found");
- one or two existing features that do something analogous, and the convention each follows (`file:line`);
- any canonical helper, module, or pattern an implementer would be expected to reuse or extend for this idea (`file:line`).

Don't propose a design — just surface what already exists and what's true. If the claim I'm checking is wrong, say so plainly.
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

Shared design language across the crank pipeline, defined once in [VOCABULARY.md](VOCABULARY.md). This skill leans on **module**, **interface**, **depth** (and its payoffs, **leverage** / **locality**), and the **deletion test** when weighing one shape against another — read their meanings there.

## Deliverables

The high-level design brief, written to the `.crank/` file (see Hard Rules). Include whichever sections apply (omit ones that don't earn their place — this is a brief, not a spec):

- **Idea / Problem** — what the user wants and why, in their words.
- **Approach** — the chosen direction in a few sentences, plus the main alternatives considered and one line on why this one won (leverage / locality).
- **Shape** — the major pieces and how they relate: one line of responsibility each, and the data or control flow between them. High-level — no signatures or schemas. A rough sketch or short list, not a file map.
- **Key decisions** — the consequential choices settled during brainstorming, each with one line on why. These are what the spec inherits and details.
- **Open questions** — technical decisions deliberately left for the spec to ground and settle; this list becomes the spec's grilling agenda. The admission test: you can state the question precisely *now*, even though answering it is the spec's job. Anything you can't yet phrase that sharply is a design hole, not an open question — resolve it with the user before handing off. Only genuinely spec-level detail goes on this list.
- **Out of scope** — what was discussed and explicitly cut.

## Flow

Create a task for each step below and mark each complete as you finish it, live, so the user can watch progress.

### 1. Explore project context

Before asking the user anything, learn the lay of the land: recent commits, relevant docs, and the surfaces the idea would touch. **Bias toward delegating** wide reads to a standard subagent (see References → Subagents) so its window — not yours — holds the source. In an existing codebase, note the established patterns the idea should follow; you'll lean on them when proposing approaches.

Completion criterion: you can name the surfaces the idea touches and the established patterns it should follow — from exploration, not assumption.

### 2. Name the destination

Before refining anything, settle what reaching the end looks like: the problem being solved and what "done" means for the user, in one or two lines. The destination fixes scope — every later question, approach, and cut orients to it — so it's settled first. If the user's opening message already states it, read your one-or-two-line version back for confirmation instead of re-asking; if not, this is your first question.

Completion criterion: a one-or-two-line destination the user has explicitly confirmed — it anchors the brief's **Idea / Problem** section and every scope call after it.

### 3. Scope check

Before refining details, assess scope. If the idea describes several independent subsystems (e.g., "a platform with chat, file storage, billing, and analytics"), flag it now — don't spend questions polishing one corner of a project that needs decomposing first. Help the user split it: name the independent pieces, how they relate, and what order to build them. Then brainstorm the first sub-project through the normal flow; each sub-project gets its own brief → spec → plan → execute cycle.

Completion criterion: the idea is confirmed buildable as one project, or split — pieces named, order agreed, first sub-project chosen.

### 4. Grill the open questions

**Survey breadth-first, then drill.** Before resolving anything, fan out: list the consequential decisions you can already name — a short agenda, one line each — and share it with the user, bare or atop the first round of questions. The agenda keeps the first branch from silently eating the session, lets the user reorder or strike items, and shows what's left as the grilling proceeds. Keep it live: add decisions that answers surface, strike ones they moot. If the survey turns up nothing genuinely open — the way from idea to spec is already clear — say so and offer to skip straight to the spec phase rather than manufacture a brainstorm.

Then walk the agenda in rounds per [GRILLING.md](GRILLING.md) (read it here) — the agenda is the decision tree; each round asks every item whose prerequisites are already settled — until you and the user share a clear picture. This is the heart of the skill.

- **Raise fidelity when words stall.** When a question is experiential — how something should look, behave, or read — a cheap throwaway artifact beats another round of prose: a sketch, a sample output or mock data shape, or — when the behavior itself is the question — a single self-contained HTML file (plain HTML/CSS/JS, no build, no server) the user double-clicks and drives. Offer it in place of the question, and record the reaction as the answer. An artifact that settled a key decision is a primary source: offer to commit it to a throwaway `prototype/<slug>` branch and note the branch beside the decision in the brief — the brief keeps the decision, the branch keeps the evidence.
- **Stay at altitude.** A technical detail earns a question only when it's load-bearing for a *what*/*which-approach* decision; otherwise note it as an **Open question** for the spec and move on.
- Keep the destination in view — constraints and success criteria against it, and what's explicitly not in this.

Completion criterion: the agenda is empty — every consequential design question genuinely settled with the user or recorded as an **Open question** for the spec, none waved past.

### 5. Propose approaches

Once the shape is clear enough, propose **2–3 approaches, each optimizing for a different thing**, conversationally, with trade-offs — name the axis each one wins on (e.g. one minimizes the moving parts, one stays most flexible for the likely next ask, one hugs the existing idiom closest). Two approaches that optimize for the same thing are the same approach — drop one. If two genuinely combine, propose the hybrid as your recommendation rather than leaving the user to merge them. Lead with your recommendation and why. Reach for the Vocabulary here: prefer the approach whose central piece is *deeper* (more behavior behind a smaller interface), and name the leverage and locality the chosen shape buys over its alternative. If an approach's key piece fails the deletion test, say so — that's a reason to drop it.

Completion criterion: the user has explicitly picked an approach (or your recommended hybrid) — having heard the options isn't a pick.

### 6. Draft the high-level brief

Once the user has signed off on the approach, crystallize it into the brief, section by section per **Deliverables**, reading the material back before it lands per [READBACK.md](READBACK.md) (read it here) — its selection rule and message cap decide what earns a pause; decisions the grilling already locked carry as one-line `settled:` restatements, not re-reads. When the Shape involves a flow — data, control, or a user workflow — sketch it as a small plain-text diagram: easier to veto than prose.

Capture each approved section in the brief file as you go. As you shape the pieces, apply the **Design for isolation** and **Working in an existing codebase** guidelines (see Guidelines).

Completion criterion: every Deliverables section that applies is user-approved and captured in the brief file.

### 7. Hand off

The brief is the front door to the crank pipeline (brainstorm → spec → plan → execute); the natural next step is the spec phase, which turns it into a full PRD-plus-technical-spec. Don't ask how to file the artifact — state the default and hand over the resume command:

- The brief stays at its `.crank/` path (one line, with the path).
- **Next:** continue to the spec now — say "continue" and you'll read [SPEC.md](SPEC.md) and run its flow on the approved brief — or in a fresh session: `/crank spec .crank/<slug>/brainstorm.md`.

Close with a single trailing sentence noting the brief can instead be copied elsewhere, printed inline, or deleted on request — prose, not a numbered question — then stop.

Completion criterion: the path and resume command are stated and you've stopped — the spec phase loaded only on an explicit "continue".
