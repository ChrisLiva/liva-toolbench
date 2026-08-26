# Design lens

Apply to any module that is **new** (the grounding subagents reported no analogous surface) **or named in the Refactor scope** (an existing module the spec intends to reshape). For a module that merely extends existing prior art and isn't in the Refactor scope, follow the established pattern and skip this lens. For an in-scope module, before you name the chosen design:

- **Deletion test.** Run it on the module: one that fails folds into its caller — don't spec it as a module.
- **Design it twice.** Sketch the module two ways under *different binding constraints* so they genuinely diverge — e.g. one *minimize the interface*: 1–3 entry points, max capability each; the other *maximize flexibility*: let the caller compose the behavior. Pick the **deeper** one. Record the chosen shape, one sentence on why it beat the alternative, and one sentence on what it gives up (the alternative's strongest property). A second sketch that's a near-twin of the first means the constraint wasn't binding — re-sketch it. When the two sketches are close on depth, pick the one with the cleaner verification story: its behavior provable by a test at the seam with fewer stand-ins. The executor succeeds at those.
- **Seam & dependencies.** Classify each dependency the module crosses: **in-process** (the interface is the seam — no port; tests drive it directly), **local-substitutable** (test stand-in like PGLite/in-memory FS — internal seam), **remote-but-owned** or **true-external** (define a port at the seam; production adapter + test adapter).

<tradeoff>
**A port** buys swappability and a clean test seam — at the cost of an extra layer every reader must traverse. **Direct use** keeps the call path flat and obvious — at the cost of coupling tests to the real dependency. That second adapter is exactly what the **remote-but-owned** / **true-external** rows above buy you — outside them a single-adapter seam pays the indirection cost and buys nothing.
</tradeoff>

Keep the interface as the test surface (SPEC.md → Deliverables → Testing approach): the seam you name here is the one the tests drive.
