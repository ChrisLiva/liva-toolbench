---
name: implement
description: User-only wrapper that executes docs/crank/<slug>/plan.md after recommending an execution mode (inline, subagent-driven-development, or executing-plans) and writes the retro to docs/crank/<slug>/retro.md.
disable-model-invocation: true
argument-hint: "[slug]"
---

Resolve slug from `$ARGUMENTS`; if absent, pick the newest `docs/crank/<slug>/` directory that contains `plan.md` and confirm in prose. Require `docs/crank/<slug>/plan.md` to exist — if it doesn't, stop and tell the user to run `/crank-jesus:plan` first.
Read `plan.md` and assess task coupling, then recommend a mode in prose with reasoning: **inline** (no skill — Claude executes herself) for tightly-coupled plans where each task depends on the previous one's exact output; **`superpowers:subagent-driven-development`** for mostly-independent tasks in this session; **`superpowers:executing-plans`** for a parallel session. Note that subagent-driven-development is generally higher quality when same-session is fine. Wait for confirmation or an override.
Invoke the chosen skill via `Skill(name=...)` (or execute inline if that's the choice), instructing it explicitly to write the execution retro to `docs/crank/<slug>/retro.md` and **not** to the upstream default. Honor BLOCKED status by stopping and asking rather than guessing.
Print `CRANK_JESUS_RETRO=docs/crank/<slug>/retro.md` as the final line.
