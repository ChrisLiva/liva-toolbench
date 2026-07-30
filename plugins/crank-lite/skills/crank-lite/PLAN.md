# Phase: Plan

Interview the user relentlessly at an implementation level about every aspect of their idea, spec, or PRD until you reach a shared understanding of the build strategy, task order, code boundaries, risks, and verification approach.

## Interview

Resolve every implementation decision, and keep the planned code minimal.

Walk down each branch of the decision tree for their implementation, resolving dependencies between decisions one-by-one.

Ask questions one at a time — exactly one question mark per message; a sub-question or "and also…" rider is the next message, sent after this answer lands — and wait for feedback before continuing. For each question, provide your recommended answer.

Proactively spawn Sonnet/GPT-5.6-Terra-Medium subagents to explore the codebase and investigate your own questions before resorting to asking the user: if a *fact* can be found in the codebase, look it up rather than asking. The *decisions* are the user's — put each one to them and wait for their answer.

A risk no check can retire is a decision: put it to the user during the interview, not into the artifact. The interview resolves open questions; the plan ships without any.

## Readback

Once you've reached a shared understanding, read the plan back to the user before writing anything: one logical section per message, pausing after each so they can question, refute, or change it.

- Show each section's actual content — the tasks, the decisions behind them, and the risks themselves — so the user can strike or amend specific items.
- Optimize for what the user actually vetoes: lead with what the plan commits to build, what's explicitly out of scope, and anything still unsettled. Commit sequencing and test breadth stay background — a sentence, not a list.
- Where a task's logic or data flow is easier to veto in picture form, show it as pseudo-code, a call graph, or a small plain-text diagram (ASCII; chat renders mermaid as raw text).
- If the only possible reply is "sounds good", you've sent a summary, not a readback.

## Plan

When every section stands approved, record the concise implementation plan to a new temp file (e.g. `${TMPDIR:-/tmp}/lite-plan-<slug>.md`) and stop.

Keep the artifact light: include the goal, assumptions, ordered tasks, verification checks, and risks — each risk paired with the check that retires it during execution — when those sections earn their place. Carry any pseudo-code, call graph, or diagram the user approved during readback into the plan — the executing agent inherits the exact logic shape that was vetted, not a prose paraphrase of it.

Tell the user the temp file path and recommend `lite-execute` next when the plan is ready to build.
