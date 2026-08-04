# Interview & readback

The shared discipline for every crank-lite phase. Each phase file says *what* to interview about and what its artifact holds; this file is *how* to interview and how to read the artifact back.

## Interview

- Ask questions one at a time — exactly one question mark per message; a sub-question or "and also…" rider is the next message, sent after this answer lands — and wait for feedback before continuing.
- Lead every question with your recommended answer.
- Answer your own questions first: if a *fact* can be found in the codebase or docs, dispatch a standard-tier subagent (see Subagent tiers) to look it up rather than asking. The *decisions* are the user's — put each one to them and wait for their answer.

## Readback

Once you've reached a shared understanding, read the artifact back to the user before writing anything: one logical section per message, pausing after each so they can question, refute, or change it.

- Show each section's actual content — the decisions, criteria, constraints, and cuts themselves — so the user can strike or amend specific items.
- Lead with what the artifact commits to, what's explicitly out of scope, and what remains open — those are what the user vetoes.
- Where a shape, interface, flow, or piece of logic is easier to veto in picture form, show it as pseudo-code, a call graph, or a small plain-text diagram (ASCII; chat renders mermaid as raw text).
- If the only possible reply is "sounds good", you've sent a summary, not a readback.

## Subagent tiers

The user's own configuration wins: if their global or project instructions state subagent model preferences, map the tier onto them. Otherwise resolve per harness:

<subagent-tiers>
- **standard** (exploration and codebase lookups): Claude Code `model: sonnet` · Codex GPT-5.6-Terra at medium effort · Cursor `cursor-composer-2-5`
</subagent-tiers>
