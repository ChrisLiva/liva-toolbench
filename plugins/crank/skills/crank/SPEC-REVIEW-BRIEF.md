# Adversarial spec review brief

Pass this brief verbatim to a heavy subagent, substituting the spec path.

<brief>
Read the spec at `<path>`.

Flag every instance of:

- **ambiguity** — two engineers could implement it meaningfully differently.
- **inaccuracy** — a claim that contradicts the codebase; verify against the repo.
- **criteria gaps** — a behavior the spec body describes (interaction, keybinding, edge case, state transition, validation) with no matching numbered acceptance criterion, or a criterion too vague to falsify.
- **off-pattern** — a layer is touched without naming the existing surface for that layer (repository function, renderer hook, query key, IPC shape) that analogous features in the codebase use; grep one or two analogous files to confirm.
- **shallow module** — a module that is *new* or named in the spec's **Refactor scope**, whose interface is nearly as complex as its implementation, or that fails the deletion test (removing it would not scatter complexity, so it's a pass-through that should fold into its caller). Don't flag existing modules outside the Refactor scope; their boundaries are settled.
- **missed simplification** — complexity the spec itself introduces (a new mode, flag, wrapper, or special-case branch in an existing flow) where a reframing would let an existing module absorb the behavior; flag only when you can name the simpler shape, and don't flag a decision the spec records with its tradeoff.
- **bespoke duplication** — the spec designs a helper or utility the codebase already provides; grep to confirm, and name the canonical one.
- **boundary smells** — a specified interface relies on optionality, casts, `any`, or silent fallbacks where the invariant could be explicit.
- **implementation-detail testing approach** — the Testing approach prescribes a test coupled to internals (mocking an internal collaborator, asserting on call counts or order, a private method, or a back-channel DB read) instead of driving the production seam a real caller reaches.
- **placeholder language** — `TODO` / `TBD` / `for later` / `v2` / anything punting a decision the spec should have resolved; resolve it or move it to **Out of scope**.
- **missing technical detail** — anything that would block an implementer.

Don't re-open settled decisions.

Then edit **the spec file at `<path>`** in place to fix every item you flagged — that spec file is the only artifact you may modify; you verify against the codebase **only to inform your spec edits**, never editing any production, test, or source file.

End your reply with a one-line summary of what changed.
</brief>
