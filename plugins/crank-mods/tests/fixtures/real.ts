// Excerpts of real crank ledgers, plans, Stopped: and Bound: lines, and
// hand-off answers from crank sessions up to 2026-10-01. Long cells and notes
// are cut.

/** ~/Gitea/liva-todo/.git/crank/progress-health-scan-fixes.md, its head and first boxes. */
export const HEALTH_LEDGER = `# Crank execute — main
Plan: .crank/health-scan-fixes/plan.md
Base: f89f28b17c9876b857b15aeeccdd34f23b62db36

- [x] Task 1: Unexport five in-file symbols and teach knip about settings.d.mts — 1a9a37e — review skipped (clean return)
- [x] Task 2: Put validateSearch in TanStack's documented order in /dex — 2307d46 — review skipped (clean return)
- [x] Task 3: Split one list's blocks out of printableBlocks — c33abd4 — review skipped (clean return)
- [ ] Task 4: Characterize, then split, reconcile and snapshot
`

/** Adapted from ~/GitHub/OrcaSlicer/.crank/miniature-removal-plan/plan.md: its Progress block cut to three boxes with Task 3 left open, a box line added under Global Constraints, and its Stages table. */
export const REMOVAL_PLAN = `# Plan: miniature removal plan

## Progress

Base: 65e864f4b0ccb990b0da58b90045716047125117

- [x] Task 1: The 23 process keys exist, persist and invalidate support — b706b9b556 — note: base \`[config]\` count read 65
- [x] Task 2: The Support tab shows the checkbox and the Removal planning group with the dependency greyed — faf693db30
- [ ] Task 3: The plan type, its storage, the stage skeleton, and a disabled slice equals the baseline

## Global Constraints

- [ ] Task 9 is not a progress box here: it sits outside the Progress block.

## Stages

| stage | tasks | closes criteria | exit state |
|---|---|---|---|
| 1 | Task 1–Task 3 | AC 1, 3 | Keys exist and persist. |
| 2 | Task 4–Task 7 | AC 4, 5, 7, 29 | Necks, pads, island, span and slenderness rules print. |
| 3 | Task 8–Task 11 | AC 15, 16 | The planner answers the coupon geometries. |

## Tasks

### Task 1 — The 23 process keys exist, persist and invalidate support

### Task 2 — The Support tab shows the checkbox and the Removal planning group with the dependency greyed

### Task 3 — The plan type, its storage, the stage skeleton, and a disabled slice equals the baseline
`

/** Stopped: lines from session 0ad4b731 and a run bounded to Phase 2. */
export const STOPPED_T25 = 'Stopped: T25 blocked on the Chrome extension disconnecting — resume at T25, then T27.'
export const STOPPED_PHASE_2 =
  'Stopped: the user bounded run 3 to Phase 2; Tasks 6–8 landed (4b2e0b7, f989f22, 187e573) with every gate green after each (`-L fast` 8 tests, `-L slow` 3 tests) — resume at Task 9'

/** A lite-execute Pre-flight Bound: line. */
export const BOUND_STAGE_GATE = 'Bound: Task 4, the stage 1 gate the user named'

/** The tails of sessions 03efdf6e, c63daa22 and 5d3b3c5a. */
export const HANDOFF_EXECUTE = `Commits stay local on \`main\`.

**Next:** \`/crank:crank-execute .crank/voice-notes-pipeline/plan.md\` resumes at Task 6 — the ledger's checked boxes are confirmed against \`git log\` and skipped.`

export const HANDOFF_LITE_PLAN = `and a Grounding section of the facts the interview proved.

Next step: \`/lite-execute .crank/pipeline-bug-fixes/plan.md\`. This session has consumed well over 100k of context, so run it in a fresh session invoked with the artifact rather than continuing here.`

export const HANDOFF_LITE_RESUME = `I also added the bed-exit and cutter-tip facts to \`.crank/cerebrum.md\`. Per the skill, the adversarial review and the retro wait for the run that lands Task 27. Run \`/lite-execute .crank/miniature-removal-plan/plan.md\` to resume at Task 12.`
