---
name: lite-brainstorm
description: Brainstorm a raw idea at design altitude before a spec or plan. Use when the user wants to explore possibilities, product direction, UX/workflows, or major approach choices.
---

Interview the user at a high level about every aspect of their idea until you reach a shared understanding of the problem, desired experience, important constraints, and the concept's overall shape.

For greenfield, ask about user experience, design, workflows. For existing projects, ask how their idea fits into the current project, and if the current project needs to change significantly to incorporate their idea.

Walk down each branch of possibilities for their idea, refining as you go but keeping the questions and decisions at a high level and resolving dependencies between decisions one-by-one. For each question you have, provide your recommended answer.

Only ask questions one at a time, and wait for feedback before continuing.

Proactively spawn Sonnet/GPT-5.5-Medium subagents to explore the codebase and investigate your own questions before resorting to asking the user. You should only ask the user questions that the codebase itself cannot answer.

Once you've reached a shared understanding, read the brief back to the user piece by piece before writing anything: walk the planned sections one at a time, pausing after each so the user can question, refute, or change it. When every piece stands approved, record the concise brainstorm brief to a new temp file (e.g. `${TMPDIR:-/tmp}/lite-brainstorm-<slug>.md`) and stop. Keep the artifact light: include the idea, goals/constraints, chosen shape, key decisions, open questions, and suggested next step when those sections earn their place. Tell the user the temp file path and recommend `lite-spec` next, or `lite-plan` if the idea is already implementation-ready.
