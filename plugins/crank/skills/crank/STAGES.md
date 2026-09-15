# Stages

A **stage** is a contiguous range of the plan's ordered tasks that ends on a **stage gate**: a tree the user can stop at, merge, and resume from later. A staged plan keeps every stage within ten tasks.

## Stage gate

The last task of a stage leaves all of:

- every gate command the plan names green;
- the acceptance criteria the stage closes proved by the checks the plan names for them. A first stage may close none when it builds what later stages stand on: the gate command, the characterization test, the expand half of an expand–contract;
- an **exit state**: one line naming what works at the gate and what the next stage adds.

A wide refactor is green only at its integrate task, so its whole expand–migrate–contract sequence sits inside one stage.

## Where to cut

Cut where the decomposition already turns: after the task that establishes the gate; after a characterization-and-reshape pair, before the feature that rides on it; between the criteria groups one journey test proves; at a milestone the spec itself names.

## Shape

The plan's **Stages** table has one row per stage: `stage | tasks | closes criteria | exit state`. Tasks keep their global numbers and headings; a stage is a range over them.

Completion criterion: every task number falls in exactly one stage row, every stage closes a criterion or is the named first scaffolding stage, and every exit state names the check that proves it at the gate.
