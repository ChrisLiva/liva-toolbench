# Phase: Plan

Interview the user relentlessly at an implementation level about every aspect of their idea, spec, or PRD until you reach a shared understanding of the build strategy, code boundaries, risks, and verification approach. Interview and readback follow the shared discipline in [INTERVIEW.md](INTERVIEW.md) — read it before your first question.

## Interview

Resolve every implementation decision, and keep the planned code minimal.

A risk no check can retire is a decision: put it to the user during the interview, the plan ships with no open questions.

Probe, don't recall: any build-tool, CLI-flag, or pinned-dependency behavior the plan leans on gets run once during the interview's fact lookups — never asserted from memory. And when the work keys, transforms, or migrates data that already exists, run the proposed invariant over the full real dataset and record the count checked; canned fixtures can't stand in for it.

## Vocabulary

Shared design language across the crank pipeline, defined once in [VOCABULARY.md](VOCABULARY.md). Read it before you write the verification checks: this phase leans on the **probe**, its **oracle**, the **seam**, the **journey test**, the **redundant test**, and the **rewrite test**.

## Plan

The plan goes to `.crank/<slug>/plan.md`. Its sections: the goal, assumptions, ordered tasks, verification checks, and risks, each risk paired with the check that retires it during execution. Prefer checks a machine can judge: the repo's exact gate commands (typecheck, lint, test, build), or — where no committed test fits — a **probe**; the check that retires a risk names one of these instruments. Plan tests as a minimalist: one **journey test** per workflow, accreting one assertion per behavior; a **redundant test**, or one that fails the **rewrite test**, stays out of the plan.

Write for the executor `/lite-execute` will dispatch: a standard-tier subagent that receives the task text and file paths, nothing else. Every task carries its own paths, contract, and check; a task that leans on another task's text or on this interview is a task it cannot build. Route reuse by name: a task that needs a helper the repo already has names it. Each task names the existing test or file to model after. A module being reshaped with no test at its seam gets a characterization task first. If no gate command runs, the first task establishes one.

Next step: `/lite-execute .crank/<slug>/plan.md` — in this session or a fresh one.
