# Adversarial spec review brief

Substitute the spec path into `<path>` below.

<brief>
Read the spec at `<path>`. The plan phase decomposes this spec into tasks handed one at a time to an implementer that sees only its own task block, never this conversation.

Work your lookups in **rounds**. A round's **frontier** is every lookup whose answer you do not need before issuing the next one; send the whole frontier as one batch in a single turn, read every return, then compose the next round from what came back.

Flag every instance of the following, taking as settled any decision the spec records with its tradeoff and any decision an ADR in the repo records:

- **ambiguity** — two engineers could implement it meaningfully differently.
- **inaccuracy** — a claim that contradicts the codebase; verify against the repo.
- **criteria gaps** — a behavior the spec body describes (interaction, keybinding, edge case, state transition, validation) with no matching numbered acceptance criterion, or a criterion too vague to falsify.
- **off-pattern** — a layer is touched without naming the existing surface for that layer (repository function, renderer hook, query key, IPC shape) that analogous features in the codebase use; grep one or two analogous files to confirm.
- **shallow module** — a module that is *new* or named in the spec's **Refactor scope**, whose interface is nearly as complex as its implementation, or that fails the deletion test (removing it would not scatter complexity, so it's a pass-through that should fold into its caller). Don't flag existing modules outside the Refactor scope; their boundaries are settled.
- **missed simplification** — complexity the spec itself introduces (a new mode, flag, wrapper, or special-case branch in an existing flow) where a reframing would let an existing module absorb the behavior; flag only when you can name the simpler shape.
- **ADR drift** — the spec relies on code that contradicts an ADR, or contradicts one itself without saying so; name the ADR and make the spec state which governs.
- **bespoke duplication** — the spec designs a helper or utility the codebase already provides; grep to confirm, and name the canonical one.
- **boundary smells** — a specified interface relies on optionality, casts, `any`, or silent fallbacks where the invariant could be explicit.
- **implementation-detail testing approach** — the Testing approach prescribes a test coupled to internals (mocking an internal collaborator, asserting on call counts or order, a private method, or a back-channel DB read) instead of driving the production seam a real caller reaches.
- **placeholder language** — `TODO` / `TBD` / `for later` / `v2` / anything punting a decision the spec should have resolved; resolve it or move it to **Out of scope**.
- **missing technical detail** — a decision named with no chosen option, an interface named with no signature, a data shape referenced with no fields, or a layer touched with no `file:line` prior art.

Then fix every item you flagged in **the spec file at `<path>`** — that spec file, the finding list below, and the edit script that lands them are the only artifacts you may modify; you verify against the codebase **only to inform your spec edits**, never editing any production, test, or source file.

Fix in **two passes**:

1. **Collect.** Finish flagging the whole spec before you edit anything, and write the findings to `spec-review-findings.md` beside the spec — one line each: the section it lands in, the flag it trips, the edit it takes.
2. **Apply.** Write `spec-review-edits.py` beside the spec, holding every finding's edit as an exact `(section, old, new)` triple where `old` is text copied verbatim from the spec. Run it once. For each triple it counts `old` in the file: on exactly one match it replaces and prints `OK <section>`; on any other count it prints `MISS <section>: matched <n> times`, leaves the file unchanged for that triple, and the script exits non-zero. Widen each MISS's `old` to a span that appears once and run the script again, until it exits zero.

Done when your lookup frontier is empty and every item on your finding list has landed in the spec file through a `spec-review-edits.py` run that exited zero. End your reply with a one-line summary of what changed.
</brief>
