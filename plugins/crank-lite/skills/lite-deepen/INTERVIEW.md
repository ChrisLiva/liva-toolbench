# Interview & readback

The shared discipline for every crank-lite phase. Each phase file says *what* to interview about and what its artifact holds; this file is *how* to interview and how to read the artifact back.

## Interview

- Map what's open as a decision tree and interview in **rounds**: each round asks the whole **frontier** — every question whose prerequisites are already settled — as a numbered list in plain chat prose — options questions included, since prose shows your reasoning and the trade-off and leaves room for follow-up — then waits for the user's answers. Recompute the frontier from the answers and ask the next round; a question that depends on one still open in this round waits for a later round.
- Format each question `❓ **Q1 — <title>**: <body>`, with your recommended answer on its own `➡️` line beneath, so the user can answer by number. Offer discrete options when the choice is genuinely between them — never as a neutral menu; your pick still leads.
- **Facts are yours; decisions are the user's.** If a *fact* can be found in the codebase or docs, dispatch a standard-tier subagent (see Subagent tiers) rather than asking; every *decision* goes to the user. Lookups precede questions: send the round's lookups as one parallel batch. The batch is a **blocking call**. Wait on it with the harness's blocking wait, or end your turn at it when the harness resumes you with a completion notification; a wait that times out is no return, so wait again. Compose the round only after every lookup has returned, each finding folded into the recommendation it informs, some questions retired outright by what came back. The user receives one grounded round per turn. A finding that carries a `file:line` or a command's output is also banked as a grounding entry for the artifact's Grounding section ([ARTIFACT-HOME.md](ARTIFACT-HOME.md) → Grounding) — having evidence is the trigger, not a forecast of downstream reliance.
- Settled means settled: a hedge or a "we'll see" is not a resolution, and a resolved decision doesn't reopen in a later round. The interview is done when the frontier is empty — every branch visited, nothing left silently assumed.

## Readback

Once the frontier is empty, write the artifact. Once any review of it has landed its edits, read it back to the user per [READBACK.md](READBACK.md): read that file before the readback message.

## Subagent tiers

Resolve the tiers once per run and reuse the mapping at every dispatch. The source of truth is a subagent model preference stated in the user instructions already loaded this session (user- and project-level `CLAUDE.md` / `AGENTS.md`); it is binding: map the tiers onto it, even when it names a weaker model than a fallback below. The block below is a fallback only, for a session whose loaded instruction files state no such preference:

<subagent-tiers>
- **standard** fallback (exploration and codebase lookups): Claude Code `model: sonnet` · Codex Terra at medium effort · Cursor Composer
- **heavy** fallback (adversarial review): Claude Code `model: opus` · Codex Sol at high effort · Cursor Sol at high effort
</subagent-tiers>
