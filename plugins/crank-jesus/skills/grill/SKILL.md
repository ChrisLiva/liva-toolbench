---
name: grill
description: User-only wrapper that runs Matt Pocock's grill-with-docs skill and persists the resolved Q&A to docs/crank/<slug>/grill.md.
disable-model-invocation: true
argument-hint: "[slug or topic]"
---

Resolve slug: use `$ARGUMENTS` if given (assume it's already `YYYY-MM-DD-<kebab-topic>` or upgrade it to that shape using today's date), otherwise propose one in prose from the topic and wait for confirmation. Then `mkdir -p docs/crank/<slug>/`.
Invoke `Skill(name="grill-with-docs")` to run the grilling session — let it update `CONTEXT.md` and `docs/adr/` in their normal locations.
When the session winds down, write a transcript-style synthesis to `docs/crank/<slug>/grill.md`: for each resolved branch use `## Q<n>: <question>` followed by `Resolved: <answer>`, then an `## Open threads` tail for anything unresolved.
Print `CRANK_JESUS_GRILL=docs/crank/<slug>/grill.md` as the final line.
