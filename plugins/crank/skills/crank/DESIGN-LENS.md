# Design lens

Apply to any module that is **new** (the grounding subagents reported no analogous surface) **or named in the Refactor scope** (an existing module the spec intends to reshape). Any other module follows its prior art's established pattern and skips this lens. For an in-scope module, before you name the chosen design:

- **Deletion test.** A module that fails it folds into its caller; don't spec it as a module.
- **Design it twice.** Sketch the module two ways under *different binding constraints*, e.g. *minimize the interface* (1–3 entry points, max capability each) versus *maximize flexibility* (the caller composes the behavior). A near-twin second sketch means the constraint wasn't binding: re-sketch it. Pick the **deeper** one; when the two are close on depth, pick the one whose behavior a test at the seam proves with fewer stand-ins, since the executor succeeds at those. Record the chosen shape, one sentence on why it beat the alternative, and one sentence on what it gives up (the alternative's strongest property).
- **Seam & dependencies.** Classify each dependency the module crosses: **in-process** (the interface is the seam — no port; tests drive it directly), **local-substitutable** (test stand-in like PGLite/in-memory FS — internal seam), **remote-but-owned** or **true-external** (define a port at the seam; production adapter + test adapter).

Keep the interface as the test surface (SPEC.md → Deliverables → Testing approach): the seam you name here is the one the tests drive.
