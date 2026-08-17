# Grilling protocol

The shared interview discipline for walking open decisions to ground with the user. Each skill's flow says *what* to grill and when; this file is *how*.

Map what's open as a **decision tree** — every decision branches into the decisions that hang off it — and work the tree in **rounds**. The **frontier** is every question whose prerequisites are already settled: the ones askable *now* without guessing at answers you haven't heard yet.

- **Ask the whole frontier in one round** — a numbered list in plain chat prose (not a structured-question UI: prose shows your reasoning and leaves room for follow-up), each question in this fixed shape so the user can answer by number:

  ```
  ❓ **Q1 — <title>**: <the question; prose, or discrete options when the choice is genuinely between them>

  ➡️ <your recommended answer and the trade-off it accepts>
  ```

  Every question leads with your pick on its `➡️` line — options are never a neutral menu. A question whose answer depends on another question still open in this round belongs to a *later* round.
- **Recompute between rounds.** Wait for the user's answers; they reshape the tree — settled decisions push the frontier outward and unblock what hung on them, and new branches an answer surfaces join it. Then ask the next frontier.
- **Facts are yours; decisions are the user's.** If the codebase, current docs, or a search can settle a question, dispatch a subagent rather than spend the user's attention on it. Lookups precede questions: send the round's lookups as one parallel batch, and the batch is a blocking call — compose the round only after every lookup has returned, each finding folded into the recommendation it informs, some questions retired outright by what came back. The user receives one grounded round per turn, every recommendation already informed.
- **Settled means settled.** Keep at a question until it's genuinely resolved, not waved past — a hedge or a "we'll see" is not a resolution. Once resolved, don't reopen it in a later round.

The grill is done when the frontier is empty — every branch visited, nothing left silently assumed.
