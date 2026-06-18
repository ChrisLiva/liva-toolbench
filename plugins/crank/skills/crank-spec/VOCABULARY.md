# Vocabulary

Shared design language across the crank pipeline (brainstorm → spec → plan → execute). Defined once here; each skill points at this file and names the terms it leans on. Use these terms with these meanings.

- **Module** — anything with an interface and an implementation: a function, class, file, or larger slice.
- **Interface** — the full contract a caller must understand: signatures, invariants, ordering, errors, config.
- **Depth** — how much an interface hides. A **deep** module exposes a small interface over substantial behavior; a **shallow** one exposes nearly as much as it hides. Depth lives in the interface, not the implementation — a deep module may be built of many small internal parts, so long as they don't show through. Prefer the deeper shape: more capability behind a smaller interface.
- **Leverage / locality** — the two payoffs of depth. Callers get **leverage**: more behavior per unit of interface they must learn. Maintainers get **locality**: change, bugs, and knowledge concentrate in one place instead of spreading across callers. Use these words when recording why a chosen design beat its alternative.
- **Deletion test** — imagine the module gone. If its complexity simply vanishes, it was a pass-through and shouldn't be its own piece; if that complexity reappears across many callers, the boundary earned its place.
- **Seam** — a place where behavior can be swapped without editing in that place; the location of an interface, and the surface tests drive (the production node/endpoint/entry point a real user reaches, never a synthetic stand-in).
- **Port / adapter** — a seam that crosses a dependency: the **port** is the interface, an **adapter** is a concrete fill (production HTTP/db vs. in-memory test double). Two adapters justify a port; one is just indirection.
- **Dead seam** — a verify step that drives a node, handler, or endpoint the production code never wires up. It passes even if the feature is absent — worse than no check, because it hides the gap.
- **Spaghetti growth** — a one-off conditional, flag, or special case bolted onto a flow the spec/plan never named. A design problem, not a style nit: route the behavior behind the module that owns the concept, or surface the spec gap.
