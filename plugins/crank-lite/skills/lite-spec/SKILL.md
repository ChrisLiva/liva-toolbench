---
name: lite-spec
description: Spec an idea, bug, or brainstorm into a PRD plus technical spec. Use when the user needs acceptance criteria, key technical decisions, and validation before planning.
---

Interview the user relentlessly at a PRD/Spec level about every aspect of their idea until you reach a shared understanding of the user-facing behavior, acceptance criteria, key technical decisions, and validation strategy.

The interview should resolve key technical decisions such as data structures, interfaces/seams, test methodology, validation strategies, and the general shape that an implementation might take. When speccing existing codebases, be proactive in suggesting refactors, simplifications, or new codebase designs that would improve the codebase as a whole and also accomplish the user's idea.

Walk down each branch of the decision tree for their idea, resolving dependencies between decisions one-by-one. For each question you have, provide your recommended answer.

Only ask questions one at a time, and wait for feedback before continuing.

Proactively spawn Sonnet/GPT-5.5-Medium subagents to explore the codebase and investigate your own questions before resorting to asking the user. You should only ask the user questions that the codebase itself cannot answer.

Once you've reached a shared understanding, summarize the decisions and get the user's confirmation, then record a concise spec to a new temp file (e.g. `${TMPDIR:-/tmp}/lite-spec-<slug>.md`) and stop. Keep the artifact light: include the problem, proposed solution, acceptance criteria, key technical decisions, testing/validation, out of scope, and open questions when those sections earn their place. Tell the user the temp file path and recommend `lite-plan` next when implementation planning is the natural next step.
