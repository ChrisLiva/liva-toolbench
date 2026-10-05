# Interview & readback

How every crank-lite phase interviews and reads its artifact back. The phase file says *what* to interview about and what its artifact holds.

## Interview

Map what's open as a decision tree. Its **frontier** is every question whose prerequisites are already settled.

### Round loop

- **Starts when:** the phase file reaches its first question round.
- **Each pass** is one round, and the user receives one grounded round per turn:
  1. **Look up.** **Facts are yours; decisions are the user's.** If a *fact* can be found in the codebase or docs, dispatch a standard-tier subagent (Subagent tiers) rather than asking; every *decision* goes to the user. Lookups precede questions: send the round's lookups as one parallel batch.
  2. **Wait on the lookup batch.** The batch is a **blocking call**. Wait on it with the harness's blocking wait, or end your turn at it when the harness resumes you with a completion notification; a wait that times out is no return, so wait again.
  3. **Fold in.** Compose the round only after every lookup has returned, each finding folded into the recommendation it informs, some questions retired outright by what came back. A finding that carries a `file:line` or a command's output is also banked as a grounding entry for the artifact's Grounding section ([ARTIFACT-HOME.md](ARTIFACT-HOME.md) → Grounding); having evidence is the trigger, not a forecast of downstream reliance.
  4. **Ask the whole frontier** as a numbered list in plain chat prose, options questions included, since prose shows your reasoning and the trade-off and leaves room for follow-up. A question that depends on one still open in this round waits for a later round. Format each question `❓ **Q1: <title>** <body>`, with your recommended answer on its own `➡️` line beneath, so the user can answer by number. Offer discrete options when the choice is genuinely between them, never as a neutral menu; your pick still leads.
  5. **Wait for the user's answers**, then recompute the frontier from them. Settled means settled: a resolved decision doesn't reopen in a later round.
- **Ends when:** the frontier is empty, every branch visited and nothing left silently assumed.
- **Escalate when:** never; a hedge or a "we'll see" is not a resolution, so its question stays on the frontier.

## Readback

Once the frontier is empty, write the artifact. Once any review of it has landed its edits, read it back to the user per [READBACK.md](READBACK.md): read that file before the readback message.

## Subagent tiers

Resolve the tiers once per run and reuse the mapping at every dispatch:

1. A subagent model preference stated in the user instructions already loaded this session (user- and project-level `CLAUDE.md` / `AGENTS.md`) is binding: map the tiers onto it, even when it names a weaker model than a fallback below.
2. Otherwise, use this fallback:

<subagent-tiers>
- **standard** fallback (exploration and codebase lookups): Claude Code `model: sonnet` · Codex Luna at high effort · Cursor Composer
- **heavy** fallback (adversarial review): Claude Code `model: opus` · Codex Sol at high effort · Cursor Sol at high effort
</subagent-tiers>
