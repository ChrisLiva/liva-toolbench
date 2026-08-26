# Interview & readback

The shared discipline for every crank-lite phase. Each phase file says *what* to interview about and what its artifact holds; this file is *how* to interview and how to read the artifact back.

## Interview

- Map what's open as a decision tree and interview in **rounds**: each round asks the whole **frontier** — every question whose prerequisites are already settled — as a numbered list in plain chat prose — options questions included, since prose shows your reasoning and the trade-off and leaves room for follow-up — then waits for the user's answers. Recompute the frontier from the answers and ask the next round; a question that depends on one still open in this round waits for a later round.
- Format each question `❓ **Q1 — <title>**: <body>`, with your recommended answer on its own `➡️` line beneath, so the user can answer by number. Offer discrete options when the choice is genuinely between them — never as a neutral menu; your pick still leads.
- Answer your own questions first: if a *fact* can be found in the codebase or docs, dispatch a standard-tier subagent (see Subagent tiers) to look it up rather than asking. Lookups precede questions: send the round's lookups as one parallel batch, and the batch is a blocking call — compose the round only after every lookup has returned, each finding folded into the recommendation it informs, some questions retired outright by what came back. The user receives one grounded round per turn. The *decisions* are the user's — put each one to them and wait for their answer.
- Settled means settled: a hedge or a "we'll see" is not a resolution, and a resolved decision doesn't reopen in a later round. The interview is done when the frontier is empty.

## Readback

Once the frontier is empty, read the artifact back to the user before writing anything, per [READBACK.md](READBACK.md): read it before the first readback message.

## Subagent tiers

Resolve the tier once per run and reuse it. A subagent model preference stated in the user instructions already loaded this session (user- and project-level `CLAUDE.md` / `AGENTS.md`) is binding: map the tier onto it, even when it names a weaker model than the fallback below. With no such preference stated, use your harness's fallback:

<subagent-tiers>
- **standard** (exploration and codebase lookups): Claude Code `model: sonnet` · Codex GPT-5.6-Terra at medium effort · Cursor `cursor-composer-2-5`
</subagent-tiers>
