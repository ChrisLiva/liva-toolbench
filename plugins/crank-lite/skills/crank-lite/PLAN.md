# Phase: Plan

Interview the user at an implementation level about every aspect of their idea, spec, or PRD — the build strategy, code boundaries, risks, and verification approach — until the frontier is empty.

## Interview

Resolve every implementation decision, and plan the smallest change that ships the spec: a new or reshaped module that fails the **deletion test** folds into its caller.

Before the first question, read:

- The incoming artifact in full, when one exists.
- The winning variant the incoming artifact's `Prototype:` line names, and any other mock it records, read at its path.
- `CONTEXT.md`, any ADRs, and the conventions in `CLAUDE.md`/`AGENTS.md`, where they exist.
- The incoming artifact's Grounding section, or the `grounding.md` its `Grounding:` header names, when one exists, verify-then-trusted per [ARTIFACT-HOME.md](ARTIFACT-HOME.md) → Grounding. Rewrite a drifted entry in place where it lives, in that section or that `grounding.md`, with the new evidence, phase, and date, then carry the drift into the plan's updates since spec.
- Each earlier effort's `grounding.md` and `retro.md` under `.crank/` that names a file the incoming artifact names (one grep of `.crank/` for those paths), for its banked facts, open items, and deferred findings, verify-then-trusted the same way; carry each that bears on this plan into the plan's updates since spec, in scope or out with its reason.

Offer a prototype, 3 to 5 variants behind one switcher, once, when all three hold:

- the change touches a page, screen, component, CLI output, flags, help text, or TUI;
- the incoming artifact, if any, carries no `Prototype:` line (a verdict, `declined`, or `no verdict`);
- a look or interaction decision is still open.

When `.crank/<slug>/prototype/` already holds files, offer to reopen them in place of a build. On a yes, read [PROTOTYPE.md](PROTOTYPE.md) and follow it; on a no, record `Prototype: declined` under the plan's assumptions. When the incoming artifact is a brainstorm brief, copy its `Prototype:` line, with any block beneath it, under the plan's assumptions as written. When no offer fires, move to the questions without mentioning a prototype.

A risk no check can retire is a decision, and so are a spec clause the code contradicts, a threshold no run measured, and a spec decision whose stated reason the interview's lookups overturned: put each to the user during the interview, so the plan ships with no open questions.

Run it, don't recall:

- During the interview's fact lookups, run each behavior of code the repo does not own that the plan leans on (a build tool, CLI flag, pinned dependency, library call, or OS or shell behavior) once in the form the task uses it, with the same command, flags, shell, platform, and target, and record what it printed: an exact output, exit code, or API contract, in prose or as an embedded block. A neighbor's run (`node` for `tsc`) settles nothing, and an external API's response shape cites the provider's documented example or a recorded call.
- When the work keys, transforms, or migrates existing data, run the proposed invariant over the full real dataset, not a canned fixture, and record the count checked.

## Vocabulary

Read [VOCABULARY.md](VOCABULARY.md) before you write the verification checks: this phase leans on **anchor**, **probe**, **oracle**, **seam**, **dead seam**, **deletion test**, **journey test**, **redundant test**, and **rewrite test**.

## Plan

The plan's file is `plan.md`, in the effort's directory ([ARTIFACT-HOME.md](ARTIFACT-HOME.md)). Its parts, in order:

1. `Spec: <absolute path to the spec>`, a header line above the goal when a spec exists; lite-execute hands that spec to its reviewer.
2. Goal.
3. Global Constraints: the project-wide rules every task must honor, such as version floors, dependency limits, naming and copy rules, and platform requirements, one line each, with values copied verbatim from the spec. Omit it when the spec names no such rule.
4. Assumptions.
5. Updates since spec: drift found in the spec's grounding and any gap the spec leaves that the plan must resolve. Omit it when there is none.
6. Ordered tasks.
7. Stages, for a long plan: read [STAGES.md](STAGES.md) once the task list settles, and read each cut back beside the cut it rejected.
8. Verification checks.
9. Coverage: a table, `criterion | task | verify step that proves it | fails when`, with one row per acceptance criterion in the spec, or with no spec, per behavior the goal names. The `fails when` cell names the production line whose deletion or reversion turns that check red, one per site when the change lands at two, and the row covering the plan's riskiest behavior change names a committed test, not a probe, or says why a probe suffices. A criterion no machine check can prove reads `human-only: <what a person checks>` in its verify cell.
10. Risks, each paired with the check that retires it during execution.
11. Grounding: what the interview's runs printed and its banked entries (ARTIFACT-HOME.md → Grounding).

Verification checks:

- Prefer checks a machine can judge: the repo's exact gate commands (typecheck, lint, test, build), or a **probe** where no committed test fits. The check that retires a risk names one of these instruments.
- A check whose reading is a count or a probe output records what the tree the task starts from prints beside what it must print: the tree now, or, when an earlier task changes what the check reads, `read at task start` or the reading that task's check records; equal readings are a **dead seam**. The target comes from a run on a scratch copy with the change applied when the change is mechanical (a formatter, a codemod, a retype), or reads as measured at task time with the `Stop if:` band it must land in.
- A check reads named tests or a gate passing, never a full-suite total, and a task scoped by a linter's or type checker's report scopes to what that tool reports at task start under a named path.
- Tests follow the spec's methodology, or with no spec, one **journey test** per workflow that passes the **rewrite test**; a **redundant test** stays out of the plan. An oracle's expected value comes from a source independent of the change (the spec, a hand-verified literal, a naive reference), never from the code under test or the code it replaces, and no planned test pins a schema's, migration's, or config's shape or incidental prose.
- A step the executor may not or cannot take (a push or merge, a write to production data, a destructive git command, a gesture in a GUI no tool in the session drives) is the user's: the task prints the exact command for the user, and its check reads the result the user reports.
- As you write, confirm at its source each fact the interview never asked, such as a signature, a file a task edits, or a count a check pins, and record what you read in Grounding. Any fact you cannot confirm this session follows the `Stop if:` case below.

Write every task for the weakest executor it may get, one that sees only the task's text with its `Stop if:` line, its file paths, its check, the plan's Global Constraints, the grounding lines for those files, the `Prototype:` line when the task builds or reshapes that line's surface, and the commits already landed. Each task carries:

- its own paths, contract, and check;
- the existing test or file to model after;
- by name, each helper the repo already has, or an earlier task in this plan builds, that it needs. A helper two tasks need is built by the first and named by the second, whose paths list its home file when it may extend it.

A claim about the code as it stands cites its **anchor** ([VOCABULARY.md](VOCABULARY.md) → Verification language), or the command and what it printed.

By case:

- **The task builds or reshapes the surface a `Prototype:` line covers**, in the spec or the plan: before you write it, read the winning variant at the line's path, or the block beneath a line reading `in chat`. The task names that path, or `in chat`, as its reference, and which part of the verdict it builds.
- **A module being reshaped has no test at its seam**: a characterization task comes first.
- **No gate command runs**: the first task establishes one.
- **The task renames, moves, deletes, retypes, or changes the meaning of a symbol, file, value, or documented behavior** (a tightened contract included: a field made required, a validator narrowed): it carries every hit of one whole-repo grep for the name, and for the old value where that value is distinctive (a hash, a count prose repeats, a unique string), tests, fixtures, docs, and agent instruction files included, or names a hit it leaves alone with the reason.
- **The task defines a schema, helper, store, query, constant, or condition**: grep the repo for its shape (the expression, SQL, or literal it would hold), not only its name, and record the result in Grounding. Reuse a hit by name, export or extract a module-private one rather than copy it, and move a check or follow-up call that another caller wraps around a function the task consumes into that function rather than repeat it.
- **The task builds a module that holds state across an await** (a lifecycle such as start and stop, a queue or lock, a cache, a window opened around a callback): it carries a check for each pair of operations that can overlap, the same one twice included, with the first call left unawaited; a guard for one pair leaves the others open. An invariant the design rests on but the code does not enforce (a callback with no await, a branch called unreachable) gets a guard that fails loudly and a check that breaks it on purpose.
- **A criterion is read on an environment the tests stand in for** (a live model or service, the real corpus or the user's data, a build target the suite does not build, a person using the UI): the first task that wires that path end to end takes one reading there, its `Stop if:` carrying the criterion's caps, before any task that tunes, extends, or presents the path. A reading that needs the user's data, credentials, or hands is the user's step at that task.
- **The task rests on a fact you could not confirm this session, and the fact being false would change what that task ships**: the task carries a `Stop if: <what the executor would observe if the fact is false>` line, and the fact stays off Risks. An unconfirmed fact whose check an executor can run without changing what ships goes under Risks with that check.

## Review

Once `plan.md` is written, read [PLAN-REVIEW-BRIEF.md](PLAN-REVIEW-BRIEF.md) and dispatch the review ([INTERVIEW.md](INTERVIEW.md) → Subagent tiers). Every dispatch carries pointers only, each an absolute path, and each is a blocking call, so wait on it as INTERVIEW.md says to wait on a lookup batch:

- **A plan with one stage or no Stages table**: one heavy-tier reviewer, handed the brief, the plan, the spec when one exists, and this skill's `VOCABULARY.md`.
- **A plan with two or more stages**: three reviewers in one wave, each handed those pointers plus a `Shard: <A | B | X>` line and a `Findings: <absolute path to .crank/<slug>/plan-review-<a | b | x>.md>` line.
  - Shard A and Shard B run at the standard tier, and each is also handed a `Tasks: <first>-<last>` line naming its task range. Shard A takes Task 1 through the last task of the stage whose cut leaves the two ranges closest in task count, the earlier cut on a tie, and Shard B takes the rest.
  - Shard X runs at the heavy tier.
  - Once all three return, dispatch one heavy-tier merger handed [PLAN-MERGE-BRIEF.md](PLAN-MERGE-BRIEF.md), the review brief, the plan, the spec when one exists, `VOCABULARY.md`, and the three findings paths.

Land each finding the reviewer returns, or each row the merger returns:

- **`CONFIRMED`, correcting a fact**: land its `old` → `new` edit in `plan.md` verbatim, widening `old` to a span the file holds once when it matches elsewhere.
- **`CONFIRMED`, with more than one defensible replacement, or a merged row carrying a `Spec decision:` line**: a decision. Land it as the review wrote it, and show it in the readback beside the replacement it beat.
- **`REFUTED`**: no edit.

Then strike or rewrite any Grounding entry a landed edit contradicts ([ARTIFACT-HOME.md](ARTIFACT-HOME.md) → Grounding).

Completion criterion: every `CONFIRMED` finding or merged row is in `plan.md`, each decision among them marked for the readback.

Next step: `/lite-execute .crank/<slug>/plan.md` — in this session or a fresh one; one run carries the plan through its last task. For a staged plan, add one sentence: the user may bound a run at any stage gate (`stop after Task <N>`, the gate's last task), and a gate short of the last task ends a short run, reviewed when the last stage lands.
