---
name: lite-plan
description: "Plan implementation for a spec, PRD, or formed idea. Use when the user is ready to decide how to build: ordered tasks, code boundaries, verification, and sequencing."
---

Interview the user relentlessly at an implementation level about every aspect of their idea, spec, or PRD until you reach a shared understanding of the build strategy, task order, code boundaries, risks, and verification approach.

The interview should resolve all ambiguity and implementation decisions for bringing their vision to life. The implementation plan should keep the code minimal.

Walk down each branch of the decision tree for their implementation, resolving dependencies between decisions one-by-one. For each question you have, provide your recommended answer.

Only ask questions one at a time — exactly one question mark per message; a sub-question or "and also…" rider is the next message, sent after this answer lands — and wait for feedback before continuing.

Proactively spawn Sonnet/GPT-5.5-Medium subagents to explore the codebase and investigate your own questions before resorting to asking the user: if a *fact* can be found in the codebase, look it up rather than asking. The *decisions*, though, are the user's — put each one to them and wait for their answer.

Once you've reached a shared understanding, read the plan back to the user piece by piece before writing anything: one section per message, showing that section's actual content — the tasks, checks, and risks themselves, so the user can strike or amend specific items — and pausing after each so they can question, refute, or change it. If the only possible reply is "sounds good", you've sent a summary, not a readback. When every piece stands approved, record the concise implementation plan to a new temp file (e.g. `${TMPDIR:-/tmp}/lite-plan-<slug>.md`) and stop. Keep the artifact light: include the goal, assumptions, ordered tasks, verification checks, risks, and open questions when those sections earn their place. Tell the user the temp file path and recommend `lite-execute` next when the plan is ready to build.
