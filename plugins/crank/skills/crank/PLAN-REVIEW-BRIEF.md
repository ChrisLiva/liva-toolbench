# Adversarial plan review brief

<brief>
Read the spec at `<spec-path>` in full: it is the contract. Read the plan's frame at `<plan-path>` — its header (`Spec:`, `Goal:`, `Gates:`), **Global Constraints**, **Updates since spec**, **Refactor scope**, **File structure**, **Coverage**, and **Out of scope**, plus every task's title. Each task body comes as you reach it in the walk, read by heading from that same file. Each task will be handed alone to a standard-tier implementer that sees only that task's block and a repo orientation, never the spec, the other tasks, or this review. Read each task as that implementer receives it: a gap you can fill from the spec or a neighboring task is a gap it cannot.

Work your lookups in **rounds**. A round's **frontier** is every lookup whose answer you do not need before issuing the next one; send the whole frontier as one batch in a single turn, read every return, then compose the next round from what came back.

First, walk the spec yourself and list every acceptance criterion and every behavior its body describes (interaction, keybinding, alias, edge case, state transition, validation). Then flag every instance of:

- **underspecified steps** — a behavior missing its oracle (exact input → expected output), an interface missing a concrete signature: not concrete enough to build from without a design conversation.
- **unsurveyed embedded code** — an embedded block with no evidence line naming what verified it (a probe run, a read of the live file, a doc check); verify it against the codebase yourself and fix it, or rewrite the behavior as prose-with-contract or pseudo-code.
- **unprobed oracle** — a behavior or `Verify:` pinning a third-party tool's exact output, exit code, or API contract with no evidence line naming the run that produced it; run it yourself and correct the pinned value, or rewrite the step to derive it at task time.
- **coverage holes** — a behavior from your walk that no Coverage row proves, a row whose verify step doesn't exercise the behavior, an empty verify cell whose stated reason doesn't hold.
- **name / type / path inconsistencies** — across tasks or against the codebase.
- **placeholder language** — `similar to Task N` / "add appropriate handling" / vague instructional prose / a symbol no task defines.
- **dead-seam verify steps** — a test that drives a node, handler, or endpoint the production code never wires up, so it would pass even if the feature were absent.
- **unverifiable verify steps** — a verify step missing its exact command, or whose success can't be read from an exit code or exact output ("looks right", "renders correctly") outside the plan's human-only smoke rows; also a probe step missing its oracle, its exact expected output, or its deletion before commit. Rewrite it as a deterministic check.
- **horizontal slicing** — a multi-behavior task whose steps batch every test before any implementation instead of landing one behavior at a time; reorder into vertical slices.
- **implementation-detail tests** — an embedded test or specified test case that mocks an internal collaborator, asserts on call counts or order, reaches a private method, or reads its oracle through a back channel instead of the interface; rewrite it to drive the seam.
- **redundant tests** — two steps spec tests that pin the same behavior at the same seam, or a single workflow is fragmented into one-assertion tests that each rebuild the same setup; merge them into one journey test, rewriting the steps to name the surviving destination. A journey test proving several criteria with many assertions is the intended shape, not a flag.
- **spaghetti growth** — a step threads a one-off conditional, flag, or special case through a file or flow the spec never named, instead of routing it behind the module that owns the concept.
- **bespoke duplication** — a step embeds or directs building a helper the codebase already provides; grep to confirm, and rewrite the step to call the canonical one.
- **needless dependency** — a step adds or imports a new third-party dependency where the stdlib, a native platform feature, an already-installed dependency, or a few lines would do; flag it, name the lighter route, and treat any new dependency the spec's Tech stack didn't pin as an **Updates since spec** item, not a silent import.
- **scattered guards** — two or more tasks each add the same guard, validation, or check at a different call site where one shared function at the root would be shallower and cover every caller (including the sibling callers no task names); flag it as a candidate to centralize and route the callers through it. Not a mandate — a caller that legitimately needs its own guard stays put; flag the duplication, name the shared home, leave the call.
- **boundary smells** — a contract or embedded code papers over an unclear invariant with casts, `any`, or new optional parameters.
- **interface drift** — a task's `Consumes` names a signature no earlier task `Produces` or that contradicts the codebase, or a `Produces` no later task and no acceptance criterion ever uses.
- **Global Constraints violations** — a task contradicts a rule in the plan's Global Constraints, or a Global Constraints value isn't copied verbatim from the spec.
- **order problems** — a task imports what no earlier task built.
- **layering** — a task adds an import that crosses layers the wrong way or closes a cycle; route it through the layer that owns the dependency.
- **unpinned refactor** — a Refactor scope task reshapes a module with no characterization step before it, or a task's `Check:` names no exemplar to model after.

None of the flags above licenses cutting a trust-boundary validation, data-loss or error path, security check, or accessibility affordance — those are required behavior, not surface or duplication; never recommend folding one away, and where the plan drops one the spec relies on, flag the hole.

Take the spec's decisions as settled. Then fix every item you flagged in **the plan file at `<plan-path>`** — that plan file, the finding list below, and the edit script that lands them are the only files you write to. Read the spec and grep the codebase to inform those edits. A flagged duplication, inconsistency, or dead seam gets rewritten *in the plan step that describes it*.

Fix in **two passes**:

1. **Collect.** Finish flagging the entire plan before you edit anything, and write the findings to `plan-review-findings.md` beside the plan — one line each: the task block it lands in, the flag it trips, the edit it takes.
2. **Apply.** Write `plan-review-edits.py` beside the plan, holding every finding's edit as an exact `(block, old, new)` triple where `old` is text copied verbatim from the plan. Run it once. For each triple it counts `old` in the file: on exactly one match it replaces and prints `OK <block>`; on any other count it prints `MISS <block>: matched <n> times`, leaves the file unchanged for that triple, and the script exits non-zero. Widen each MISS's `old` to a span that appears once and run the script again, until it exits zero.

Done when your lookup frontier is empty, every task block in the plan has been read against all of the flags above, every Coverage row has been judged against the behavior it claims to prove, and every item on your finding list has landed in the plan file through a `plan-review-edits.py` run that exited zero. End your reply with a one-line summary of what changed.
</brief>
