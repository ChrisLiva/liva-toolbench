---
name: lite-plan
description: "Plan implementation for a spec, PRD, or formed idea. Use when the user is ready to decide how to build: ordered tasks, code boundaries, verification, and sequencing."
---

Interview the user relentlessly at an implementation level about every aspect of their idea, spec, or PRD until you reach a shared understanding of the build strategy, task order, code boundaries, risks, and verification approach.

The interview should resolve all ambiguity and implementation decisions for bringing their vision to life. The implementation plan should focus on clean, minimal, and excellent code.

Walk down each branch of the decision tree for their implementation, resolving dependencies between decisions one-by-one. For each question you have, provide your recommended answer.

Only ask questions one at a time, and wait for feedback before continuing.

Proactively spawn Sonnet/GPT-5.5-Medium subagents to explore the codebase and investigate your own questions before resorting to asking the user. You should only ask the user questions that the codebase itself cannot answer.

Once you've reached a shared understanding, record a concise implementation plan to a temp file on the user's OS `$(mktemp -t lite-plan).md` and stop. Keep the artifact light: include the goal, assumptions, ordered tasks, verification checks, risks, and open questions when those sections earn their place. Tell the user the temp file path and recommend `lite-execute` next when the plan is ready to build.
