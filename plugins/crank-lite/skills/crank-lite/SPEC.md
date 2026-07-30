# Phase: Spec

Interview the user relentlessly at a PRD/Spec level about every aspect of their idea until you reach a shared understanding of the user-facing behavior, acceptance criteria, key technical decisions, and validation strategy.

## Interview

Resolve the key technical decisions: data structures, interfaces/seams, test methodology, validation strategies, and the general shape an implementation might take. When speccing existing codebases, proactively suggest refactors, simplifications, or new codebase designs that would improve the codebase as a whole and also accomplish the user's idea.

Walk down each branch of the decision tree for their idea, resolving dependencies between decisions one-by-one.

Ask questions one at a time — exactly one question mark per message; a sub-question or "and also…" rider is the next message, sent after this answer lands — and wait for feedback before continuing. For each question, provide your recommended answer.

Proactively spawn Sonnet/GPT-5.6-Terra-Medium subagents to explore the codebase and investigate your own questions before resorting to asking the user: if a *fact* can be found in the codebase, look it up rather than asking. The *decisions* are the user's — put each one to them and wait for their answer.

## Readback

Once you've reached a shared understanding, read the spec back to the user before writing anything: one logical section per message, pausing after each so they can question, refute, or change it.

- Show each section's actual content — the criteria, decisions, and cuts themselves — so the user can strike or amend specific items.
- Lead with what the spec commits to, what's explicitly out of scope, and which questions remain open — those are what the user vetoes.
- Where an interface, data flow, or piece of logic is easier to veto in picture form, show it as pseudo-code, a call graph, or a small plain-text diagram (ASCII; chat renders mermaid as raw text).
- If the only possible reply is "sounds good", you've sent a summary, not a readback.

## Spec

When every section stands approved, record the concise spec to a new temp file (e.g. `${TMPDIR:-/tmp}/lite-spec-<slug>.md`) and stop.

Keep the artifact light: include the problem, proposed solution, acceptance criteria, key technical decisions, testing/validation, out of scope, and open questions when those sections earn their place. Carry any pseudo-code or diagram the user approved during readback into the spec — downstream planning inherits the exact shape that was vetted, not a prose paraphrase of it.

Tell the user the temp file path and offer to continue to the plan phase ([PLAN.md](PLAN.md)) when implementation planning is the natural next step. Load the next phase file only on an explicit "continue"; never auto-advance.
