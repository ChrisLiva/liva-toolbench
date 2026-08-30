# Phase: Plan

Interview the user relentlessly at an implementation level about every aspect of their idea, spec, or PRD — the build strategy, code boundaries, risks, and verification approach — until the frontier is empty. Interview and readback follow the shared discipline in [INTERVIEW.md](INTERVIEW.md) — read it before your first question.

## Interview

Resolve every implementation decision, and plan the smallest change that ships the spec: a new or reshaped module that fails the **deletion test** folds into its caller.

A risk no check can retire is a decision: put it to the user during the interview, the plan ships with no open questions.

Run it, don't recall: any build-tool, CLI-flag, or pinned-dependency behavior the plan leans on gets run once during the interview's fact lookups, and the plan records what the run printed; one you cannot run in this session becomes a plan risk, paired with the check that would settle it. And when the work keys, transforms, or migrates data that already exists, run the proposed invariant over the full real dataset and record the count checked; canned fixtures can't stand in for it.

## Vocabulary

Shared design language across the crank pipeline, defined once in [VOCABULARY.md](VOCABULARY.md). Read it before you write the verification checks: this phase leans on the **probe**, its **oracle**, the **seam**, the **deletion test**, the **journey test**, the **redundant test**, and the **rewrite test**.

## Plan

The plan's file is `plan.md`, in the effort's directory (see [ARTIFACT-HOME.md](ARTIFACT-HOME.md)). Its sections: the goal, assumptions, ordered tasks, verification checks, risks (each risk paired with the check that retires it during execution), and a Grounding section holding what the interview's runs printed and its banked entries (ARTIFACT-HOME.md → Grounding). Prefer checks a machine can judge: the repo's exact gate commands (typecheck, lint, test, build), or — where no committed test fits — a **probe**; the check that retires a risk names one of these instruments. Plan tests as a minimalist: one **journey test** per workflow, accreting one assertion per behavior; a **redundant test**, or one that fails the **rewrite test**, stays out of the plan.

Write every task for the weakest executor it may get — one that sees that task's text and file paths and nothing more: each task carries its own paths, contract, and check. Route reuse by name: a task that needs a helper the repo already has names it. Each task names the existing test or file to model after. A module being reshaped with no test at its seam gets a characterization task first. If no gate command runs, the first task establishes one.

Next step: `/lite-execute .crank/<slug>/plan.md` — in this session or a fresh one.
