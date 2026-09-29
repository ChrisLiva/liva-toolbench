# Grilling protocol

How to walk open decisions to ground with the user; each skill's flow says *what* to grill and when.

Map what's open as a **decision tree**, each decision branching into the ones that hang off it, and work it in **rounds**. The **frontier** is every question whose prerequisites are settled, askable *now* without guessing at answers.

- **Share the agenda first.** Before resolving anything, fan out: write the tree down as a short agenda, one line per consequential decision you can already name, and share it with the user, bare or atop the first round. It keeps the first branch from silently eating the session, lets the user reorder or strike items, and shows what's left. Keep it live: add decisions that answers surface, strike ones they moot.
- **Ask the whole frontier in one round** — a numbered list in plain chat prose (not a structured-question UI: prose shows your reasoning and leaves room for follow-up), each question in this fixed shape so the user can answer by number:

  ```
  ❓ **Q1 — <title>**: <the question; prose, or discrete options when the choice is genuinely between them>

  ➡️ <your recommended answer and the trade-off it accepts>
  ```

  Every question leads with your pick on its `➡️` line; options are never a neutral menu.
- **Recompute between rounds.** Wait for the answers, recompute the frontier, then ask it.
- **Facts are yours; decisions are the user's.** The user owns intent, priorities, preferences, external context, and the trade-off only they can tip; the codebase owns what its chosen idiom dictates, so if grounding found the surface, follow it. Settle what the codebase, current docs, or a search can answer yourself or through a **standard**-tier subagent per [SUBAGENT-TIERS.md](SUBAGENT-TIERS.md) → Dispatch or main thread, rather than spend the user's attention on it. Lookups precede questions, and the effort's grounding file precedes lookups where one exists ([ARTIFACT-HOME.md](ARTIFACT-HOME.md) → Grounding): a covered lookup becomes a confirm at its cited evidence, and a return carrying a `file:line` or a command's output is banked there. Send the round's lookups as one parallel batch, a blocking call — compose the round only after every lookup returns, folding each finding into the recommendation it informs and retiring the questions it answers. The user receives one grounded round per turn.
- **Settled means settled.** A resolution is an answer the user commits to. On a hedge or a "we'll see", re-ask in your next message narrowed to two named options with your pick beside them; if the hedge survives, the question stays on the agenda and opens the next round, unbanked.

The grill is done when the frontier is empty — every branch visited, nothing left silently assumed.
