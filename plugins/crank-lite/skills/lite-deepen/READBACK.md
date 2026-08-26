# Readback protocol

The shared discipline for reading a drafted-to-be artifact back to the user before it hardens. The phase file lists the artifact's sections; this file decides which of them earn a pause, and how much.

## Readback opens on an empty frontier

Readback is the veto pass over settled material. It begins once the interview's frontier is empty, so the user's move is to strike or amend a line, never to answer a question. A decision the interview missed surfaces here as one more interview round: ask it, take the answer, fold it in, then resume the readback.

## Select what earns a pause

Read back only what the user could veto:

- **New or changed** — content settled since the previous phase's approved artifact (or, with no prior artifact, since the interview's settled answers).
- **Judgment calls** — decisions where a defensible alternative was rejected; name the rejected option, so the veto is a real choice between stated options.

Everything else is carried-forward: state it in one line ("Sections X and Y carry forward from the approved spec unchanged") and move on.

## Pace

- **The first message opens with what the artifact commits to and what's explicitly out of scope**, and ends with a standing exit: "Say **approve the rest** at any point and I'll carry the remaining sections as shown."
- **Every section closes with the settled decisions it rests on** — `settled: Q3 (in-memory cache), Q8 (fail closed)` — so a decision the interview locked is restated, never silently elided; if the user re-raises one, point at that line rather than re-litigating it.
- **At most 4 readback messages, whatever the artifact's size.** Group material into logical sections to fit the cap rather than giving each item its own message; a selected item is grouped harder, never dropped, to fit it.
- Pause after each message so the user can question, refute, or change it, and fold each change in before the next.
- **The readback is done when every selected item has been shown and approved** — each by the user's assent or an amendment folded in, or the remaining ones by "approve the rest" — not when the fourth message is sent. An unanswered objection is not approval.

## Make the veto easy

- **Show the actual items** — the decisions, criteria, cuts, and rows themselves — so the user can strike or amend specific lines, not react to finished prose.
- **Prefer pictures where they're easier to veto.** Where an interface, flow, or piece of logic reads better in picture form, show it as pseudo-code, a call graph, or a small plain-text diagram (ASCII; chat renders mermaid as raw text).
- **The test for each message: could the user veto a specific item from it, with every item already answered?** If all they can say is "sounds good", you've sent a summary; if they have to pick an option, you've sent an interview round.

## Carry what was approved

A sketch, diagram, or list the user approved during readback goes into the artifact as vetted — the next phase inherits the exact shape, not a prose paraphrase of it.
