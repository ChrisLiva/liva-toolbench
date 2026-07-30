# Readback protocol

The shared discipline for reading a drafted-to-be artifact back to the user before it hardens. Each skill's flow says *what* to read back and in what order; this file is *how*.

- **Content, not a table of contents.** Walk the material one section per message, pausing after each so the user can question, refute, or change it, and fold each change in before the next.
- **Show the actual items** — the decisions, criteria, cuts, and rows themselves — so the user can strike or amend specific lines, not react to finished prose.
- **Prefer pictures where they're easier to veto.** Where an interface, flow, or piece of logic reads better in picture form, show it as pseudo-code, a call graph, or a small plain-text diagram (ASCII; chat renders mermaid as raw text).
- **The test for each message: could the user veto a specific item from it?** If all they can say is "sounds good", you've sent a summary, not a readback.
- **Carry what was approved.** A sketch, diagram, or list the user approved during readback goes into the artifact as vetted — the next phase inherits the exact shape, not a prose paraphrase of it.

A change caught in the readback costs a sentence; the same change after drafting re-litigates the draft and everything downstream.
