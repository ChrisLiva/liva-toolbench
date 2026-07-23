---
name: lite-brainstorm
description: Brainstorm a raw idea at design altitude before a spec or plan. Use when the user wants to explore possibilities, product direction, UX/workflows, or major approach choices.
---

Interview the user at a high level about every aspect of their idea until you reach a shared understanding of the problem, desired experience, important constraints, and the concept's overall shape.

## Interview

Settle the destination first: one or two lines on the problem and what "done" looks like, confirmed by the user. Every later question, approach, and cut orients to it.

For greenfield, ask about user experience, design, workflows. For existing projects, ask how their idea fits into the current project, and if the current project needs to change significantly to incorporate their idea.

Survey before you drill: share a short agenda of the consequential decisions you can already name, then walk it one decision at a time, keeping questions and decisions at a high level and resolving dependencies between them one-by-one. Keep the agenda live — add decisions as answers surface them, strike ones they moot. If the survey turns up nothing genuinely open, say so and recommend jumping straight to `lite-spec`.

Ask questions one at a time — exactly one question mark per message; a sub-question or "and also…" rider is the next message, sent after this answer lands — and wait for feedback before continuing. For each question, provide your recommended answer.

When a question is experiential — how something should look, behave, or read — offer a cheap throwaway artifact (a sketch, stub, or sample output) to react to instead of another prose question.

Proactively spawn Sonnet/GPT-5.6-Terra-Medium subagents to explore the codebase and investigate your own questions before resorting to asking the user: if a *fact* can be found in the codebase, look it up rather than asking. The *decisions* are the user's — put each one to them and wait for their answer.

## Readback

Once you've reached a shared understanding, read the brief back to the user before writing anything: one logical section per message, pausing after each so they can question, refute, or change it.

- Show each section's actual content — the decisions, constraints, and shape themselves — so the user can strike or amend specific items.
- When the shape involves a flow — data, control, or a user workflow — sketch it as a small plain-text diagram (ASCII; chat renders mermaid as raw text): easier to veto than prose.
- If the only possible reply is "sounds good", you've sent a summary, not a readback.

## Brief

When every section stands approved, record the concise brainstorm brief to a new temp file (e.g. `${TMPDIR:-/tmp}/lite-brainstorm-<slug>.md`) and stop.

Keep the artifact light: include the idea, goals/constraints, chosen shape, key decisions, open questions, and suggested next step when those sections earn their place. Carry any sketch or diagram the user approved during readback into the brief. An open question earns its place only when it's stated sharply enough for the spec to answer it — anything you can't phrase that precisely yet is a design hole to resolve here first.

Tell the user the temp file path and recommend `lite-spec` next, or `lite-plan` if the idea is already implementation-ready.
