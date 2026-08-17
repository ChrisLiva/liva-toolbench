# Interview & readback

The shared discipline for every crank-lite phase. Each phase file says *what* to interview about and what its artifact holds; this file is *how* to interview and how to read the artifact back.

## Interview

- Map what's open as a decision tree and interview in **rounds**: each round asks the whole **frontier** — every question whose prerequisites are already settled — as a numbered list in plain chat prose, then waits for the user's answers. Recompute the frontier from the answers and ask the next round; a question that depends on one still open in this round waits for a later round.
- Format each question `❓ **Q1 — <title>**: <body>`, with your recommended answer on its own `➡️` line beneath, so the user can answer by number. Offer discrete options when the choice is genuinely between them — never as a neutral menu; your pick still leads.
- Answer your own questions first: if a *fact* can be found in the codebase or docs, dispatch a standard-tier subagent (see Subagent tiers) to look it up rather than asking. Lookups precede questions: send the round's lookups as one parallel batch, and the batch is a blocking call — compose the round only after every lookup has returned, each finding folded into the recommendation it informs, some questions retired outright by what came back. The user receives one grounded round per turn. The *decisions* are the user's — put each one to them and wait for their answer.
- Settled means settled: a hedge or a "we'll see" is not a resolution, and a resolved decision doesn't reopen in a later round. The interview is done when the frontier is empty.

## Readback

Once you've reached a shared understanding, read the artifact back to the user before writing anything — but only what they could veto:

- **New or changed** — content settled since the previous phase's approved artifact (or, with no prior artifact, since the interview's settled answers).
- **Judgment calls** — decisions where a defensible alternative was rejected; name the rejected option, so the veto is a real choice between stated options.

Everything else is carried-forward: state it in one line and move on. Each section closes by naming the settled interview decisions it rests on — `settled: Q3=a, Q8=a` — so a locked decision is restated, never silently elided; if the user re-raises one, point at that line rather than re-litigating it.

- **At most 4 readback messages, whatever the artifact's size** — group material into logical sections to fit the cap. End the first message with a standing exit: "Say **approve the rest** at any point and I'll carry the remaining sections as shown." Pause after each message; fold each change in before the next.
- Show each section's actual content — the decisions, criteria, constraints, and cuts themselves — so the user can strike or amend specific items.
- Lead with what the artifact commits to, what's explicitly out of scope, and what remains open — those are what the user vetoes.
- Where a shape, interface, flow, or piece of logic is easier to veto in picture form, show it as pseudo-code, a call graph, or a small plain-text diagram (ASCII; chat renders mermaid as raw text).
- Carry what was approved: a sketch, pseudo-code, call graph, or diagram approved during readback goes into the artifact as vetted — the next phase inherits the exact shape, not a prose paraphrase of it.
- If the only possible reply is "sounds good", you've sent a summary, not a readback.

## Subagent tiers

The user's own configuration wins: if their global or project instructions state subagent model preferences, map the tier onto them. Otherwise resolve per harness:

<subagent-tiers>
- **standard** (exploration and codebase lookups): Claude Code `model: sonnet` · Codex GPT-5.6-Terra at medium effort · Cursor `cursor-composer-2-5`
</subagent-tiers>
