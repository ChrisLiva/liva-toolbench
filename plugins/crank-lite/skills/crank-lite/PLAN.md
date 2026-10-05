# Phase: Plan

Interview the user at an implementation level about every aspect of their idea, spec, or PRD — the build strategy, code boundaries, risks, and verification approach — until the frontier is empty.

## Interview

Resolve every implementation decision, and plan the smallest change that ships the spec: a new or reshaped module that fails the **deletion test** folds into its caller.

Before the first question, read:

- The incoming artifact in full, when one exists.
- The winning variant the incoming artifact's `Prototype:` line names, and any other mock it records, read at its path.
- `CONTEXT.md`, any ADRs, and the conventions in `CLAUDE.md`/`AGENTS.md`, where they exist.
- The incoming artifact's Grounding section, or the `grounding.md` its `Grounding:` header names, when one exists, verify-then-trusted per [ARTIFACT-HOME.md](ARTIFACT-HOME.md) → Grounding. Rewrite a drifted entry in place where it lives, in that section or that `grounding.md`, with the new evidence, phase, and date, then carry the drift into the plan's updates since spec.

Offer a prototype, 3 to 5 variants behind one switcher, once, when all three hold:

- the change touches a page, screen, component, CLI output, flags, help text, or TUI;
- the spec carries no `Prototype:` line, or no spec exists;
- a look or interaction decision is still open.

A `Prototype:` line reading a verdict, `declined`, or `no verdict` suppresses the offer. When `.crank/<slug>/prototype/` already holds files, offer to reopen them in place of a build. On a yes, read [PROTOTYPE.md](PROTOTYPE.md) and follow it. Its `Prototype:` line, or `Prototype: declined` on a no, lands under the plan's assumptions. When the incoming artifact is a brainstorm brief, copy its `Prototype:` line, with any block copied beneath it, under the plan's assumptions as written. When no offer fires, move to the questions without mentioning a prototype.

Risks:

- A risk no check can retire is a decision: put it to the user during the interview, so the plan ships with no open questions.
- A fact you cannot confirm this session is a risk, paired with the check that would settle it, unless a task's `Stop if:` line carries it (Plan → By case).

Run it, don't recall:

- During the interview's fact lookups, run once each build-tool, CLI-flag, or pinned-dependency behavior the plan leans on, and record what the run printed: an exact output, exit code, or API contract, stated in prose or as an embedded block.
- When the work keys, transforms, or migrates existing data, run the proposed invariant over the full real dataset, not a canned fixture, and record the count checked.

## Vocabulary

Read [VOCABULARY.md](VOCABULARY.md) before you write the verification checks: this phase leans on the **probe**, its **oracle**, the **seam**, the **dead seam**, the **deletion test**, the **journey test**, the **redundant test**, and the **rewrite test**.

## Plan

The plan's file is `plan.md`, in the effort's directory ([ARTIFACT-HOME.md](ARTIFACT-HOME.md)). Its parts, in order:

1. `Spec: <absolute path to the spec>`, a header line above the goal when a spec exists; lite-execute reads it to hand the spec to its reviewer.
2. Goal.
3. Global Constraints: the project-wide rules every task must honor, such as version floors, dependency limits, naming and copy rules, and platform requirements, one line each, with exact values copied verbatim from the spec. lite-execute hands this section to every implementer and its reviewer holds the whole diff to it. Omit it when the spec names no such rule.
4. Assumptions.
5. Updates since spec: drift found in the spec's grounding and any gap the spec leaves that the plan must resolve. Omit it when there is none.
6. Ordered tasks.
7. Stages, for a long plan: read [STAGES.md](STAGES.md) once the task list settles, and read each cut back beside the cut it rejected.
8. Verification checks.
9. Coverage: a table, `criterion | task | verify step that proves it`, with one row per acceptance criterion in the spec, or with no spec, per behavior the goal names. A criterion no machine check can prove reads `human-only: <what a person checks>` in its verify cell. lite-execute walks this table before its review.
10. Risks, each paired with the check that retires it during execution.
11. Grounding: what the interview's runs printed and its banked entries (ARTIFACT-HOME.md → Grounding).

Verification checks:

- Prefer checks a machine can judge: the repo's exact gate commands (typecheck, lint, test, build), or a **probe** where no committed test fits. The check that retires a risk names one of these instruments.
- A check whose reading is a count or a probe output records what the tree prints now beside what it must print; equal readings are a **dead seam**.
- Tests follow the spec's methodology, or with no spec, one **journey test** per workflow that passes the **rewrite test**; a **redundant test** stays out of the plan.
- As you write, confirm at its source each fact the interview never asked, such as a signature, a file a task edits, or a count a check pins, and record what you read in Grounding. One you cannot confirm now lands on a task's `Stop if:` line or under Risks, per the `Stop if:` case below.

Write every task for the weakest executor it may get, one that sees only the task's text with its `Stop if:` line, its file paths, its check, the plan's Global Constraints, the grounding lines for those files, the `Prototype:` line when the task builds or reshapes that line's surface, and the commits already landed. Each task carries:

- its own paths, contract, and check;
- the existing test or file to model after;
- by name, each helper the repo already has that it needs.

A claim about the code as it stands cites its **anchor**, `path:line` plus the enclosing symbol, or the command and what it printed.

By case:

- **The task builds or reshapes the surface a `Prototype:` line covers**, in the spec or the plan: before you write it, read the winning variant at the line's path, or the block copied beneath a line reading `in chat`. The task names that path, or `in chat`, as its reference, and which part of the verdict it builds.
- **A module being reshaped has no test at its seam**: a characterization task comes first.
- **No gate command runs**: the first task establishes one.
- **The task tightens a shared contract** (a field made required, a shared symbol renamed, a validator narrowed): it carries every call site the grep found.
- **The task rests on a fact you could not confirm this session, and the fact being false would change what that task ships**: the task carries a `Stop if: <what the executor would observe if the fact is false>` line, and the fact stays off Risks. lite-execute settles an observed `Stop if:` through a route the code already offers, or stops and puts it to the user. An unconfirmed fact whose check an executor can run without changing what ships goes under Risks with that check.

## Review

Once `plan.md` is written, read [PLAN-REVIEW-BRIEF.md](PLAN-REVIEW-BRIEF.md) and dispatch one heavy-tier subagent ([INTERVIEW.md](INTERVIEW.md) → Subagent tiers) with pointers only, each an absolute path: the brief, the plan, the spec when one exists, and this skill's `VOCABULARY.md`. The dispatch is a blocking call, so wait on it the way INTERVIEW.md says to wait on a lookup batch.

Land each finding the review returns. Facts are yours; decisions are the user's ([INTERVIEW.md](INTERVIEW.md)):

- **`CONFIRMED`, correcting a fact**: land its `old` → `new` edit in `plan.md` verbatim, widening `old` to a span the file holds once when it matches elsewhere.
- **`CONFIRMED`, with more than one defensible replacement**: a decision. Land it as the reviewer wrote it, and show it in the readback beside the replacement it beat.
- **`REFUTED`**: no edit.

Then strike or rewrite any Grounding entry a landed edit contradicts ([ARTIFACT-HOME.md](ARTIFACT-HOME.md) → Grounding).

Completion criterion: every `CONFIRMED` finding is in `plan.md`, and each decision among them is marked for the readback beside the replacement it beat.

Next step: `/lite-execute .crank/<slug>/plan.md` — in this session or a fresh one; one run carries the plan through its last task. For a staged plan, add one sentence: the user may bound a run at any stage gate (`stop after Task <N>`, the gate's last task), and a gate short of the last task ends a short run, reviewed when the last stage lands.
