# Readback protocol

The phase file lists the artifact's sections; this file decides which earn a pause, and how much.

## Readback opens on an empty frontier

Readback is the veto pass over settled material. It begins once the interview's frontier is empty, so the user strikes or amends lines, never answers questions. A decision the interview missed gets one more interview round: ask it, fold in the answer, then resume the readback.

Open it by sending the first readback message, whatever the last reply said. A reply to an interview round that says "approve the rest" settles that round and approves no readback item, because none has been shown yet.

## Select what earns a pause

Read back only what the user could veto:

- **New or changed** — content settled since the previous phase's approved artifact (or, with none, since the interview's settled answers).
- **Judgment calls** — decisions where a defensible alternative was rejected; name the rejected option, so the veto is a real choice.

State everything else as carried-forward in one line ("Sections X and Y carry forward from the approved spec unchanged") and move on. A Grounding section is always carried-forward.

## Pace

- **The first message opens with what the artifact commits to and what's explicitly out of scope**, and ends with a standing exit: "Say **approve the rest** at any point and I'll carry the remaining sections as shown."
- **"Approve the rest" approves only items a readback message has already shown.** On it, carry every shown item the user has not struck or amended. If a selected item has not been shown yet, send every such item in one more message and pause on it before writing the artifact.
- **Every section closes with the settled decisions it rests on** — `settled: Q3 (in-memory cache), Q8 (fail closed)` — so no locked decision is silently elided; if the user re-raises one, point at that line rather than re-litigating it.
- **A few readback messages, whatever the artifact's size.** Group into logical sections rather than a message per item, harder as the artifact grows, but drop no selected item to fit.
- Pause after each message for questions, refutations, or changes, and fold each change in before the next.
- **The readback is done when every selected item has been shown and approved** — each by the user's assent or an amendment folded in, or the remaining shown ones by "approve the rest" — not when the last message is sent. An unanswered objection is not approval.

## Make the veto easy

- **Show the actual items** — the decisions, criteria, cuts, and rows themselves — not a description of them.
- **Prefer pictures where they're easier to veto.** Where an interface, flow, or logic reads better as a picture, show it as pseudo-code, a call graph, or a small plain-text diagram (ASCII; chat renders mermaid as raw text).
- **The test for each message: could the user veto a specific item from it, with every item already answered?** If all they can say is "sounds good", you've sent a summary; if they have to pick an option, you've sent an interview round.

## Carry what was approved

A sketch, diagram, or list the user approved during readback goes into the artifact as vetted — the next phase inherits the exact shape, not a prose paraphrase.

A decision first composed after the readback carries no approval. Such decisions include a recommended answer attached to an open question, a judgment call the draft or the review adds, shown with the alternative it rejected, and an item settled differently from how it was shown. Detail that elaborates a shown item without changing it is not one. Once the artifact is written and any review of it has landed its edits, send one message that shows every such decision as the actual item, pause on it as on a readback message, and fold each strike or amendment into the artifact before the hand-off. Until the user approves, strikes, or amends each one, neither the artifact nor your messages call it approved. When writing composed none, hand off without mentioning this check.
