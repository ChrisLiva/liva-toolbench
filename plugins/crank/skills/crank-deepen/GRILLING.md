# Grilling protocol

The shared interview discipline for walking open decisions to ground with the user. Each skill's flow says *what* to grill and when; this file is *how*.

Map what's open as a **decision tree** — every decision branches into the decisions that hang off it — and work the tree in **rounds**. The **frontier** is every question whose prerequisites are already settled: the ones askable *now* without guessing at answers you haven't heard yet.

- **Share the agenda first.** Before resolving anything, fan out: list the consequential decisions you can already name — the tree written down as a short agenda, one line each — and share it with the user, bare or atop the first round. The agenda keeps the first branch from silently eating the session, lets the user reorder or strike items, and shows what's left as the rounds proceed. Keep it live: add decisions that answers surface, strike ones they moot.
- **Ask the whole frontier in one round** — a numbered list in plain chat prose (not a structured-question UI: prose shows your reasoning and leaves room for follow-up), each question in this fixed shape so the user can answer by number:

  ```
  ❓ **Q1 — <title>**: <the question; prose, or discrete options when the choice is genuinely between them>

  ➡️ <your recommended answer and the trade-off it accepts>
  ```

  Every question leads with your pick on its `➡️` line — options are never a neutral menu.
- **Recompute between rounds.** Wait for the user's answers, recompute the frontier — answers unblock questions and surface new branches — then ask it.
- **Facts are yours; decisions are the user's.** The user owns intent, priorities, preferences, external context, and the trade-off only they can tip; the codebase owns what the chosen idiom already dictates — if grounding found the surface, follow it. If the codebase, current docs, or a search can settle a question, settle it yourself or dispatch a **standard**-tier subagent per [SUBAGENT-TIERS.md](SUBAGENT-TIERS.md) → Dispatch or main thread, rather than spend the user's attention on it. Lookups precede questions, and the effort's grounding file precedes lookups where one exists ([ARTIFACT-HOME.md](ARTIFACT-HOME.md) → Grounding): a covered lookup becomes a confirm at its cited evidence, and a lookup return carrying a `file:line` or a command's output is banked there. Send the round's lookups as one parallel batch; the batch is a blocking call — compose the round only after every lookup has returned, each finding folded into the recommendation it informs, some questions retired outright by what came back. The user receives one grounded round per turn, every recommendation already informed.
- **Settled means settled.** A resolution is an answer the user commits to. On a hedge or a "we'll see", re-ask in your next message with the choice narrowed to two named options and your pick beside them; if the hedge survives, the question stays on the agenda and opens the next round rather than being banked. Once resolved, it stays resolved.

The grill is done when the frontier is empty — every branch visited, nothing left silently assumed.
