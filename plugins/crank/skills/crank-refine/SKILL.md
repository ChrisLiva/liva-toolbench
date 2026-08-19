---
name: crank-refine
description: Grill an existing brainstorm, spec, or plan until nothing consequential is left undecided at its altitude — sharpened in place.
disable-model-invocation: true
argument-hint: "[path to a brainstorm, spec, or plan .md]"
---

# Refine

## Goal

Take an existing crank artifact — a brainstorm brief, a spec, or a plan — and **sharpen it until nothing consequential is left undecided at its altitude**. The engine is a relentless **grill**: an informed, round-by-round interview that walks the artifact's open decisions to the ground, each question led by a recommendation you've already researched. The artifact is sharpened in place. This is a standalone pass — it does not advance the pipeline; it hands a sharper artifact to whatever comes next.

## Hard Rules

- **Grill at the artifact's altitude — never below it.** The altitude table (References → Grilling altitude by phase) sets what each artifact's questions may reach for; a below-altitude item is recorded as a deferred item for the next phase, never grilled. Dragging a brainstorm into schemas, or a spec into code, is the most common way this skill fails.
- **Sharpen in place.** Edit the input artifact file directly as decisions land. Handed a legacy flat artifact (`.crank/<phase>-<slug>.md`), move it to its per-plan home (`.crank/<slug>/<artifact>.md`) first, state the new path, then sharpen it there. Only if the artifact was pasted inline with no file of its own, write the sharpened version to a new temp file (e.g. `${TMPDIR:-/tmp}/crank-<slug>/<artifact>.md`) and tell the user the path once. Never start a parallel rewrite — the user's file is the single source of truth.
- **Grill in rounds, every question informed.** Follow the shared interview discipline in [GRILLING.md](GRILLING.md): each round asks every open item whose prerequisites are settled. A question you could answer yourself, you answer yourself first (see References → Subagents & research).

## References

### Grilling altitude by phase

The artifact's phase sets what a question may reach for. Settle everything *in bounds*; push everything *below* to the next phase as a deferred item rather than answering it now.

| Artifact | In bounds — grill these | Below altitude — defer, don't grill |
| --- | --- | --- |
| **Brainstorm brief** | The problem, the chosen approach vs. its alternatives, the major pieces and how they relate, and the consequential decisions that change everything downstream. | Signatures, schemas, field names, file maps, exact libraries/versions — *unless one is load-bearing for an approach decision*. Defer to the spec. |
| **Spec** | Acceptance criteria, the technical decisions (contracts and data shapes at the interface level, library/approach choice, error and edge behavior), and what "done" looks like. | File-by-file breakdown, concrete code, task ordering. Defer to the plan. |
| **Plan** | Task decomposition and ordering, each behavior's oracle and the prose, pseudo-code, or surveyed code carried with it, file targets, the test seam for each task, and any placeholder or hand-wave (`TODO`, "similar to Task N", a symbol no task defines). | Nothing — a plan is the bottom of the pipeline. Grill until every task is executable with no further design conversation. |

For the full design rules behind a phase, read that phase's file in the `crank` skill's directory (`BRAINSTORM.md`, `SPEC.md`, `PLAN.md`).

### Subagents & research

**Answer your own questions first.** The user's attention is for what only they know — intent, priorities, preferences, external constraints; anything the codebase, the current docs, or a web search could settle is research, and research is what makes each grilling question *informed*: you arrive with the current fact, not a guess, so the user decides against a real recommendation. Three jobs:

- **Explore the codebase** — does this surface exist, what pattern do analogous features follow, is a claim the artifact makes actually true.
- **Research an approach** — compare libraries or techniques, find prior art, see how comparable projects solve this. Web search in scope.
- **Check current facts** — the latest stable version of a package, the current shape of an API, today's documentation for a tool the artifact will lean on. This is the antidote to a recommendation built on a stale training cutoff.

Whether to dispatch or read on the main thread follows the shared default in [SUBAGENT-TIERS.md](SUBAGENT-TIERS.md) → Dispatch or main thread. Each job has a fill-in brief in [DISPATCH-BRIEFS.md](DISPATCH-BRIEFS.md), read at Flow step 3. This skill spawns subagents at the **standard** tier — resolve it to your harness per [SUBAGENT-TIERS.md](SUBAGENT-TIERS.md).

### Vocabulary

Shared design language across the crank pipeline, defined once in [VOCABULARY.md](VOCABULARY.md). Lean on **module / interface / depth** (and **leverage / locality**) and the **deletion test** when a brainstorm or spec decision is about shape; on **seam**, **tracer bullet**, and **implementation-detail test** when a plan decision is about how a task is tested.

## Deliverables

The same artifact, sharpened: every in-bounds ambiguity resolved, every consequential decision made and written into the file (with a one-line rationale where it isn't self-evident), and every below-altitude item parked in the artifact's open-questions / deferred list for the next phase. No new document — the input artifact, now sharp.

## Flow

Create a task for each step below and mark each complete as you finish it, live, so the user can watch progress.

### 1. Identify the artifact and its phase

Read the artifact in full. Determine which phase it belongs to — brainstorm brief, spec, or plan — from its **content and structure**, not just its filename (a brief sketches approach and shape; a spec carries acceptance criteria; a plan carries ordered, committable tasks). If it's genuinely ambiguous which phase it is, ask the user once. Set the grilling altitude from that phase (References → Grilling altitude by phase).

Completion criterion: the artifact's phase is fixed and its grilling altitude set from it — and if classification was ambiguous, the user confirmed it. Everything downstream judges against this; misclassify here and every altitude call is wrong.

### 2. Build the grilling agenda

Scan the artifact for what's unsettled *at its altitude*: vague or hedged language, decisions named but not made, alternatives raised but not chosen, assumptions stated without grounding, and gaps where a consequential decision is simply missing. Each becomes an agenda item. Order them so dependencies come first — a decision that constrains others is grilled before them.

Completion criterion: every consequential decision the phase owns is either already settled in the artifact or on the agenda — none left implicit.

### 3. Research the agenda

Before grilling, ground the agenda. For each item a fact could inform — a library choice, a version assumption, an API the artifact leans on, a pattern the codebase may already have — dispatch the matching subagent, filling its brief from [DISPATCH-BRIEFS.md](DISPATCH-BRIEFS.md) (read that file here, before you dispatch). Send independent investigations together rather than one after another.

Completion criterion: every agenda item a fact could settle has its fact in hand — you are not about to ask the user something the docs already answer.

### 4. Grill

Walk the agenda per [GRILLING.md](GRILLING.md) (read it here) — the agenda is its decision tree — until every item is resolved, each question led by the recommendation your research produced.

Two defaults keep the grill from stalling. **When the user overrides your recommendation,** record their choice and the reason they gave, then move on. **When a decision won't converge** after a real exchange, don't loop: name the deadlock, record the leading option as *provisional* with the open tension noted in the artifact, and move to the next item.

A dependency an answer surfaces gets inserted into the agenda in order.

Completion criterion: every agenda item is resolved or explicitly deferred — nothing left hanging.

### 5. Fold decisions back in

Write each landed decision into the artifact in place — at the section it belongs to, with a one-line rationale where the reason isn't self-evident. Two shapes recur — a settled decision folded in at its section (e.g. `**Decision:** chose X over Y — *why:* <one line>`) and a parked item in the open-questions / deferred list (e.g. `- [defer → <next phase>] <below-altitude item>`); keep them light and matched to the artifact's existing format. Sharpen the wording the grilling exposed as vague; move every below-altitude item to that deferred list. Do this as you go or in a closing pass, but the file must end the session reflecting every decision made.

Completion criterion: re-reading the artifact end to end, no resolved decision is missing from it and no settled ambiguity survives in its prose.

### 6. Hand back

The artifact is sharp and the file already holds every decision. Offer in chat prose:

- **Continue in the pipeline** — point the user at the command for the natural next phase: from a sharpened brainstorm or spec, `/crank <artifact path>` (its triage routes the artifact to the next phase — brief → spec, spec → plan); from a sharpened plan, `/crank-execute <path>`.
- **Keep the file as-is** (default) — it's already updated in place; iterate further or hand it off later.
- **Print the changes inline** — summarize what the grill resolved and show the key edits, for a quick review without opening the file.

Wait for the user's pick. The next pipeline skill is user-invoked — recommend its command for the user to run; never invoke it yourself.

Completion criterion: the user has picked, and you've done exactly what they picked — the pipeline advanced only by the user running the next command.
