# Phase: Plan

Interview the user at an implementation level about the build strategy, code boundaries, risks, and verification approach until the frontier is empty.

## Interview

Resolve every implementation decision, and plan the smallest change that ships the spec: a new or reshaped module that fails the **deletion test** folds into its caller.

Before the first question, read:

- The incoming artifact in full, with the winning variant its `Prototype:` line names and any other mock it records.
- `CONTEXT.md`, any ADRs, and the conventions in `CLAUDE.md`/`AGENTS.md`, where they exist.
- The incoming artifact's Grounding section, or the `grounding.md` its `Grounding:` header names, verify-then-trusted per [ARTIFACT-HOME.md](ARTIFACT-HOME.md) → Grounding. Rewrite a drifted entry where it lives and carry the drift into the plan's updates since spec.
- Each earlier effort's `grounding.md` and `retro.md` under `.crank/` that names a file the incoming artifact names (one grep), verified the same way. Carry what bears on this plan into the updates since spec, in scope or out with its reason.

Offer a prototype, 3 to 5 variants behind one switcher, once, when the change touches a page, screen, component, CLI output, flags, help text, or TUI, a look or interaction decision is still open, and the incoming artifact carries no `Prototype:` line (a verdict, `declined`, or `no verdict`). When `.crank/<slug>/prototype/` already holds files, offer to reopen them. On a yes, read [PROTOTYPE.md](PROTOTYPE.md) and follow it; on a no, record `Prototype: declined` under the plan's assumptions. Copy a brainstorm brief's `Prototype:` line, with any block beneath it, under the assumptions as written. When no offer fires, move on without mentioning a prototype.

Put each of these to the user as a decision: a risk no check can retire, a spec clause the code contradicts, a threshold no run measured, a spec decision whose stated reason the lookups overturned, a fixed value the person running what ships might set (a window, limit, or count), and a spec-wide rule the site count below does not support.

Run it, don't recall:

- During the interview's lookups, run each behavior of code the repo does not own that the plan leans on (a build tool, CLI flag, pinned dependency, library call, or OS or shell behavior) once, in the exact form the task uses it, and record what it printed. A neighbor's run (`node` for `tsc`) settles nothing; an external API's response shape cites its documented example or a recorded call.
- When the work keys, transforms, or migrates existing data, run the proposed invariant over the full real dataset and record the count checked.
- When the spec applies a rule at every site, count where its case really arises and recommend the sites that count supports.

## Vocabulary

Read [VOCABULARY.md](VOCABULARY.md) before you write the verification checks.

## Plan

The plan's file is `plan.md`, in the effort's directory ([ARTIFACT-HOME.md](ARTIFACT-HOME.md)). Its parts, in order:

1. `Spec: <absolute path to the spec>`, a header line above the goal when a spec exists.
2. Goal.
3. Global Constraints: the project-wide rules every task must honor (version floors, dependency limits, naming and copy rules, platform requirements), one line each, values verbatim from the spec. Omit it when the spec names none.
4. Assumptions.
5. Updates since spec: drift in the spec's grounding and any spec gap the plan must resolve. Omit it when there is none.
6. Ordered tasks.
7. Stages, for a long plan: read [STAGES.md](STAGES.md) once the task list settles, and read each cut back beside the cut it rejected.
8. Verification checks.
9. Coverage: a table, `criterion | task | verify step that proves it | fails when`, one row per spec acceptance criterion, or with no spec, per behavior the goal names. `fails when` names the production line whose deletion or reversion turns that check red, one per site when the change lands at two. The row for the riskiest behavior change names a committed test, or says why a probe suffices. A criterion no machine check can prove reads `human-only: <what a person checks>` in its verify cell.
10. Risks, each paired with the check that retires it during execution.
11. Grounding: what the interview's runs printed and its banked entries (ARTIFACT-HOME.md → Grounding).

Verification checks:

- Prefer the repo's exact gate commands, or a **probe** where no committed test fits. A risk's check names one of these.
- A count or probe reading records the task's starting reading (`read at task start` when an earlier task changes it) beside its target; equal readings are a **dead seam**. For a mechanical change, take the target from a run on a scratch copy; otherwise give the `Stop if:` band it must land in.
- A check reads named tests or a gate passing, never a full-suite total.
- Tests follow the spec's methodology, or with no spec, one **journey test** per workflow that passes the **rewrite test**, with no **redundant test**. An oracle's expected value comes from a source independent of the change, never the code under test or the code it replaces. No planned test pins a schema's, migration's, or config's shape or incidental prose.
- A step the executor may not or cannot take (a push or merge, a production write, a destructive git command, a GUI gesture) is the user's: the task prints the exact command, and its check reads the result the user reports.
- Confirm at its source each fact the interview never settled (a signature, a file a task edits, a count a check pins) and record it in Grounding. A fact you cannot confirm follows the `Stop if:` case below.

Write every task for the weakest executor, one that sees only its text with its `Stop if:` line, file paths, and check, the plan's Global Constraints, the grounding lines for those files, the `Prototype:` line covering its surface, and the commits already landed. Each task carries:

- its own paths, contract, and check;
- the existing test or file to model after;
- by name, each helper it needs that the repo has or an earlier task builds. A helper two tasks need is built by the first.

A claim about the code as it stands cites its **anchor** ([VOCABULARY.md](VOCABULARY.md) → Verification language), or the command and what it printed.

By case, when a task:

- **Builds or reshapes a surface a `Prototype:` line covers**: read the winning variant first. The task names its path, or `in chat`, and which part of the verdict it builds.
- **Reshapes a module with no test at its seam**: a characterization task comes first.
- **Needs a gate and none runs**: the first task establishes one.
- **Renames, moves, deletes, retypes, or changes the meaning of a symbol, file, value, or documented behavior**: it carries every hit of one whole-repo grep for the name, and for a distinctive old value, docs and agent instruction files included, or names a hit it leaves alone with the reason.
- **Defines a schema, helper, store, query, constant, or condition**: grep the repo for its shape, not only its name, and record the result in Grounding. Reuse a hit rather than copy it, and move a check another caller wraps around a consumed function into that function.
- **Holds state across an await** (a lifecycle, queue, lock, or cache): it carries a check for each pair of operations that can overlap, the same one twice included, with the first call left unawaited. An invariant the code does not enforce gets a guard that fails loudly and a check that breaks it on purpose.
- **First wires a criterion read on an environment the tests stand in for** (a live service, the user's data, an unbuilt target, a person at the UI): it takes one reading there, its `Stop if:` carrying the criterion's caps, before any task tunes or extends the path. A reading that needs the user's data, credentials, or hands is the user's step.
- **Rests on an unconfirmed fact that would change what it ships if false**: it carries a `Stop if: <what the executor would observe>` line, and the fact stays off Risks. An unconfirmed fact an executor can check without changing what ships goes under Risks with that check.

## Review

Once `plan.md` is written, read [PLAN-REVIEW-BRIEF.md](PLAN-REVIEW-BRIEF.md) and dispatch the review ([INTERVIEW.md](INTERVIEW.md) → Subagent tiers). Every dispatch carries pointers only, each an absolute path, and blocks, so wait on it as INTERVIEW.md says to wait on a lookup batch:

- **A plan with one stage or no Stages table**: one heavy-tier reviewer, handed the brief, the plan, the spec when one exists, and this skill's `VOCABULARY.md`.
- **A plan with two or more stages**: three reviewers in one wave, each handed those pointers plus a `Shard: <A | B | X>` line and a `Findings: <absolute path to .crank/<slug>/plan-review-<a | b | x>.md>` line.
  - Shard A and Shard B run at the standard tier, each also handed a `Tasks: <first>-<last>` line. Split the tasks at the stage boundary that leaves the two ranges closest in task count, the earlier on a tie.
  - Shard X runs at the heavy tier.
  - Once all three return, dispatch one heavy-tier merger handed [PLAN-MERGE-BRIEF.md](PLAN-MERGE-BRIEF.md), the review brief, the plan, the spec when one exists, `VOCABULARY.md`, and the three findings paths.

Land each finding the reviewer returns, or each row the merger returns:

- **`CONFIRMED`, correcting a fact**: land its `old` → `new` edit in `plan.md` verbatim.
- **`CONFIRMED`, with more than one defensible replacement, or a merged row carrying a `Spec decision:` line**: a decision. Land it as written, and show it in the readback beside the replacement it beat.
- **`REFUTED`**: no edit.

Then strike or rewrite any Grounding entry a landed edit contradicts ([ARTIFACT-HOME.md](ARTIFACT-HOME.md) → Grounding).

Next step: `/lite-execute .crank/<slug>/plan.md`, in this session or a fresh one; one run carries the plan through its last task. For a staged plan, add that the user may bound a run at any stage gate (`stop after Task <N>`), and a run that ends short is reviewed when the last stage lands.
