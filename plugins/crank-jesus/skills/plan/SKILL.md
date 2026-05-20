---
name: plan
description: User-only wrapper that runs superpowers:writing-plans against docs/crank/<slug>/spec.md and forces the plan doc to land at docs/crank/<slug>/plan.md.
disable-model-invocation: true
argument-hint: "[slug]"
---

Resolve slug from `$ARGUMENTS`; if absent, pick the newest `docs/crank/<slug>/` directory that contains `spec.md` and confirm in prose before proceeding. Require `docs/crank/<slug>/spec.md` to exist — if it doesn't, stop and tell the user to run `/crank-jesus:spec` first.
Read `docs/crank/<slug>/spec.md` and invoke `Skill(name="superpowers:writing-plans")`, overriding the default path: instruct it explicitly to write the plan to `docs/crank/<slug>/plan.md` and **not** to `docs/superpowers/plans/`.
Print `CRANK_JESUS_PLAN=docs/crank/<slug>/plan.md` as the final line.
