---
name: lite-spec
description: Spec an idea, bug, or brainstorm into a PRD plus technical spec. Use when the user needs acceptance criteria, key technical decisions, and validation before planning.
---

Interview the user relentlessly at a PRD/Spec level about every aspect of their idea until you reach a shared understanding of the user-facing behavior, acceptance criteria, key technical decisions, and validation strategy.

The interview should resolve key technical decisions such as data structures, interfaces/seams, test methodology, validation strategies, and the general shape that an implementation might take. When speccing existing codebases, be proactive in suggesting refactors, simplifications, or new codebase designs that would improve the codebase as a whole and also accomplish the user's idea.

Walk down each branch of the decision tree for their idea, resolving dependencies between decisions one-by-one. For each question you have, provide your recommended answer.

Only ask questions one at a time — exactly one question mark per message; a sub-question or "and also…" rider is the next message, sent after this answer lands — and wait for feedback before continuing.

Proactively spawn Sonnet/GPT-5.6-Terra-Medium subagents to explore the codebase and investigate your own questions before resorting to asking the user: if a *fact* can be found in the codebase, look it up rather than asking. The *decisions*, though, are the user's — put each one to them and wait for their answer.

Once you've reached a shared understanding, read the spec back to the user before writing anything: one logical section per message, showing that section's actual content — the criteria, decisions, and cuts themselves, so the user can strike or amend specific items — and pausing after each so they can question, refute, or change it. If the only possible reply is "sounds good", you've sent a summary, not a readback. When every section stands approved, record the concise spec to a new temp file (e.g. `${TMPDIR:-/tmp}/lite-spec-<slug>.md`) and stop. Keep the artifact light: include the problem, proposed solution, acceptance criteria, key technical decisions, testing/validation, out of scope, and open questions when those sections earn their place. Tell the user the temp file path and recommend `lite-plan` next when implementation planning is the natural next step.
