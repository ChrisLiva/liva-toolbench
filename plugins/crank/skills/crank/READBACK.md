# Readback protocol

The shared discipline for reading a drafted-to-be artifact back to the user before it hardens. Each skill's flow says *what* material it covers; this file is *how* — and how much.

## Select what earns a pause

Read back only what the user could veto:

- **New or changed** — content settled since the previous phase's approved artifact (or, with no prior artifact, since the interview's settled answers).
- **Judgment calls** — decisions where a defensible alternative was rejected; name the rejected option, so the veto is a real choice between stated options.

Everything else is carried-forward: state it in one line ("Sections X and Y carry forward from the approved spec unchanged") and move on. Each section closes by naming the settled decisions it rests on — `settled: Q3=a, Q8=a` — so a decision the interview locked is restated, never silently elided; if the user re-raises one, point at that line rather than re-litigating it.

## Pace

- **At most 4 readback messages, whatever the artifact's size.** Group material into logical sections to fit the cap rather than giving each item its own message.
- **The first readback message ends with a standing exit:** "Say **approve the rest** at any point and I'll carry the remaining sections as shown."
- Pause after each message so the user can question, refute, or change it, and fold each change in before the next.

## Make the veto easy

- **Show the actual items** — the decisions, criteria, cuts, and rows themselves — so the user can strike or amend specific lines, not react to finished prose.
- **Prefer pictures where they're easier to veto.** Where an interface, flow, or piece of logic reads better in picture form, show it as pseudo-code, a call graph, or a small plain-text diagram (ASCII; chat renders mermaid as raw text).
- **The test for each message: could the user veto a specific item from it?** If all they can say is "sounds good", you've sent a summary, not a readback.
- **Carry what was approved.** A sketch, diagram, or list the user approved during readback goes into the artifact as vetted — the next phase inherits the exact shape, not a prose paraphrase of it.

A change caught in the readback costs a sentence; the same change after drafting re-litigates the draft and everything downstream.
