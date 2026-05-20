---
name: spec
description: User-only wrapper that runs superpowers:brainstorming end-to-end (explore → design → write) and forces the design doc to land at docs/crank/<slug>/spec.md.
disable-model-invocation: true
argument-hint: "[slug or topic]"
---

Resolve slug from `$ARGUMENTS` (assume `YYYY-MM-DD-<kebab-topic>`), or propose one in prose using today's date plus the topic and wait for confirmation. Then `mkdir -p docs/crank/<slug>/` and read `docs/crank/<slug>/grill.md` if it exists for context.
Invoke `Skill(name="superpowers:brainstorming")` for the full flow (explore → propose approaches → present design → write design doc → self-review → user review), but override its default path: instruct it explicitly to write the design doc to `docs/crank/<slug>/spec.md` and **not** to `docs/superpowers/specs/`.
Print `CRANK_JESUS_SPEC=docs/crank/<slug>/spec.md` as the final line.
