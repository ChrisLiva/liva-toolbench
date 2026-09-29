# Adversarial spec review brief

<brief>
Read the spec at `<path>`. The plan phase splits it into tasks, each handed one at a time to an implementer that sees only its own task block, never this conversation.

Work your lookups in **rounds**. A round's **frontier** is every lookup whose answer you do not need before issuing the next one; send the whole frontier as one batch in a single turn, read every return, then compose the next round from what came back.

Flag every instance of the following. Take as settled any decision the spec records with its tradeoff, or a repo ADR records:

- **ambiguity** — two engineers could implement it meaningfully differently.
- **inaccuracy** — a claim about code, a fixture, a tool, or a file, in this repo or outside it, that its source contradicts; open or run the source.
- **internal contradiction** — two spec statements that cannot both hold: an interface that cannot produce a shape the spec requires elsewhere, a criterion whose gate makes another criterion's fixture unreachable, an oracle produced by a different construction than the one the spec mandates. Name both lines and which governs.
- **criteria gaps** — a behavior the spec body describes (interaction, keybinding, edge case, state transition, validation) with no matching numbered acceptance criterion, or a criterion too vague to falsify.
- **off-pattern** — a touched layer that doesn't name the existing surface (repository function, renderer hook, query key, IPC shape) analogous features in the codebase use for it; grep one or two analogous files to confirm.
- **shallow module** — a module that is *new* or named in the spec's **Refactor scope**, whose interface is nearly as complex as its implementation, or that fails the deletion test (removing it would not scatter complexity: a pass-through that should fold into its caller). Don't flag existing modules outside the Refactor scope; their boundaries are settled.
- **missed simplification** — complexity the spec itself introduces (a new mode, flag, wrapper, or special-case branch in an existing flow) where a reframing would let an existing module absorb the behavior; flag only when you can name the simpler shape.
- **ADR drift** — the spec relies on code that contradicts an ADR, or contradicts one itself without saying so; name the ADR and make the spec state which governs.
- **bespoke duplication** — the spec designs a helper or utility the codebase already provides; grep to confirm, and name the canonical one.
- **boundary smells** — a specified interface relies on optionality, casts, `any`, or silent fallbacks where the invariant could be explicit.
- **implementation-detail testing approach** — the Testing approach prescribes a test coupled to internals (mocking an internal collaborator, asserting on call counts or order, a private method, or a back-channel DB read) instead of driving the production seam a real caller reaches.
- **placeholder language** — `TODO` / `TBD` / `for later` / `v2` / anything punting a decision the spec should have resolved; resolve it or move it to **Out of scope**.
- **missing technical detail** — a decision with no chosen option, an interface with no signature, a data shape with no fields, or a touched layer with no `file:line` prior art.

Then fix every flagged item in **the spec file at `<path>`**. That file, the finding list, and the edit script below are the only artifacts you may modify; you verify against the codebase **only to inform your spec edits**, never editing a production, test, or source file.

Fix in **two passes**:

1. **Collect.** Flag the whole spec before editing anything, and write the findings to `spec-review-findings.md` beside the spec, one line each: the section it lands in, the flag it trips, the edit, and the read or run that confirmed every fact the edit introduces. A count, line number, value, or name is **confirmed** at its source, by a read or a run, before its finding lands; arithmetic over the spec's own prose confirms nothing. A finding its check refutes stays listed as `refuted: <what the check printed>` and takes no edit.
2. **Apply.** Write `spec-review-edits.py` beside the spec, holding each finding's edit as an exact `(section, old, new)` triple where `old` is text copied verbatim from the spec. Run it once. For each triple it counts `old` in the file: on exactly one match it replaces and prints `OK <section>`; on any other count it prints `MISS <section>: matched <n> times`, leaves the file unchanged for that triple, and the script exits non-zero. Widen each MISS's `old` to a span that appears once and rerun until it exits zero.

Done when your lookup frontier is empty and every finding is `refuted` or landed in the spec through a `spec-review-edits.py` run that exited zero. End your reply with a one-line summary of what changed.
</brief>
