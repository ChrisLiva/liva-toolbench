---
name: ab-eval
description: Scaffold and run an A/B eval — a blind-judged regression harness that compares a baseline vs candidate version of a skill or prompt and reports whether the candidate measurably beat, matched, or regressed. Asks what to evaluate, scaffolds a self-contained eval folder, runs paired trials, blind-judges, and aggregates. Use to set up or run a skill/prompt eval.
disable-model-invocation: true
argument-hint: "[eval-name]"
allowed-tools: Read Grep Glob Write Edit Bash Agent AskUserQuestion TaskCreate TaskUpdate
---

# A/B eval harness

You orchestrate an **A/B eval**: a blind-judged comparison of two versions — a
**baseline** arm and a **candidate** arm — of a skill or prompt, to answer "did this
change measurably help, hurt, or neither?"

This skill is **self-contained**. Everything you need is bundled alongside this
`SKILL.md`:

- `references/methodology.md` — the two-agent file-mailbox runner, isolation rules,
  paired-transcript record→replay, blind judging, noise-floor calibration. The
  authoritative how-to for running trials. Read it before Phase 0.
- `references/authoring.md` — how to author a grounded topic + gold-answer key and a
  blind judge rubric. Read it when scaffolding.
- `references/scaffolding.md` — the exact layout of an eval folder and the scaffold
  steps. Read it when scaffolding.
- `templates/` — `runner.md`, `judge.md`, `user-brief.md`, `record-user.md`,
  `replay-user.md`: the files copied/filled into a scaffolded eval folder.

You do **not** depend on any eval folder existing in advance — you either scaffold a
fresh one or run one the user points you at. You never hardcode a path to a specific
eval.

## Step 1 — scope the eval

Ask the user (one `AskUserQuestion`) whether they are **scaffolding a new eval** or
**re-running an existing eval folder**. If `$ARGUMENTS` named an eval, treat it as a
hint for which.

**Re-running an existing folder:** ask for its path. Read its `config.md` and `README.md`
to recover the arms, topics, trial counts, and whether it is grill-based. Skip to
Step 3.

**Scaffolding a new eval:** interview the user — use `AskUserQuestion` for discrete
choices, plain questions otherwise — to settle:

1. **Eval name** and where the eval folder should live (default: `evals/<name>/`).
2. **Thing under test** — which skill or prompt, and the **two arms**: how to obtain the
   baseline version (e.g. `git HEAD`, a path, a branch) and the candidate version (e.g.
   the working tree, another path). Either arm may be byte-identical — that is a valid
   noise-floor check; say so if it is.
3. **Grill-based or not** — does the thing under test interview a user (a grill /
   clarifying questions)? If **yes**, the eval uses the two-agent runner + record→replay
   (`references/methodology.md`). If **no** (pure input→output), it uses a single runner
   and no user-player.
4. **Target codebase** — the read-only repo the thing under test reasons about, if any,
   and its absolute path. It is **strictly read-only** for the whole eval.
5. **Topics** — how many scenarios, and their rough shape. Each topic needs a real,
   grounded gold-answer key (`references/authoring.md`). Offer to author at least one
   deliberately **adversarial** topic that baits the failure mode the candidate change
   targets — without it, an eval often cannot resolve the change.
6. **Trial counts and model** — default: 3 trials/arm/topic for grill evals, 2 for
   noise-floor or non-grill evals; Sonnet runners and judges.

Then scaffold (Step 2). Create a `TaskCreate` list mirroring the steps below.

## Step 2 — scaffold the eval folder

Read `references/scaffolding.md` and `references/authoring.md`, then build the eval
folder exactly as `scaffolding.md` specifies: copy the `templates/` files in, fill the
runner and judge templates for this thing under test, author each topic's `user-brief.md`
(ground the gold key in the real target repo — spawn an `Explore` agent for that; never
invent file paths or symbols), and write `config.md` recording the frozen run config so
the eval is reproducible.

Show the user the scaffolded folder and the diff/arms summary. Get explicit confirmation
before running.

## Step 3 — Phase 0: freeze the arms

1. Create a run root under the eval folder: `runs/<YYYY-MM-DD-HHMM>/`.
2. Freeze both arms into `<eval-dir>/arms/{baseline,candidate}/` per `config.md` (e.g.
   `git archive HEAD <path> | tar -x` for a committed baseline; a copy of the working
   tree for the candidate).
3. `diff -r` the two arms and show the user. If byte-identical, confirm with the user
   that this is an intended noise-floor check before proceeding.
4. If there is a target repo, record its `git rev-parse HEAD` and `git status --short`
   as the Phase 0 snapshot — you re-check it after every phase.

## Step 4 — Phase R: record the reference grills (grill-based evals only)

For each topic, run **one unscored recording run** that produces a frozen answer bank,
exactly as `references/methodology.md` → "Record → replay" specifies. The recording run
uses the **baseline** arm and the `record-user.md` user-player; its scored artifact is
discarded — only `runs/<ts>/answer-bank-<topic>.md` matters. Skip this phase for
non-grill evals.

## Step 5 — Phase 1: trials + blind judge

For each topic and each arm, run the trial count from `config.md` per
`references/methodology.md`:

- **Grill-based:** spawn the `runner.md` skill-player + the `replay-user.md` user-player,
  which share a `relay/` mailbox; the user-player serves the frozen answer bank so both
  arms get byte-identical answers.
- **Non-grill:** spawn the `runner.md` runner alone.

**Smoke-test first** — 1 trial/arm for one topic, inspect fully, confirm the target repo
is untouched, report to the user — then launch the rest in the background, in parallel.

**Blind judge:** per topic, shuffle the trials' artifacts into blind labels in a
`judge-<topic>/` dir, write a private `mapping.md`, and spawn a judge subagent briefed
with the eval's `judges/judge.md`. Never let the judge see `mapping.md` or run-dir names.

## Step 6 — aggregate

Write `runs/<ts>/results.md`: per-arm weighted scores (decode blind labels via
`mapping.md` only now), means, ranges, whether the bands overlap, the objective
sub-metrics, the judge rubric version, the replay-trace fallback rate if asymmetric, and
a verdict — did the candidate beat / match / regress, and does the gap clear run-to-run
noise (overlapping bands = within noise). Note caveats: n, model, single-topic limits.
If several evals ran, finish with a short cross-eval `SUMMARY-<date>.md`.

## Hard rules

- **You are never in the data path.** You spawn agents and wait. Never compose a user
  answer, never hand-edit a `q-NN`/`a-NN` mailbox file or an answer bank, never give a
  skill-player the user-brief, the bank, or their paths. Never read a topic's
  `user-brief.md` once trials are running — it is the recording user-player's alone.
- **The target repo is strictly read-only** for the whole eval. Re-check its `git status`
  against the Phase 0 snapshot after every phase; if it diverges, STOP and tell the user.
- **Blind-judge integrity:** a judge subagent never sees `mapping.md` or run-dir names.
- The bundled `templates/` and `references/` are the spec — do not improvise the
  methodology. Brief subagents with the eval folder's prompt/judge files verbatim.
- Spawn runners in the background and in parallel within a phase. A grill skill-player
  runs its whole trial in one continuous turn; the trial is done only when it ends with
  `=== TRIAL COMPLETE ===`. Wait for all of a phase's trials before judging.
- Report at each checkpoint: scoped · scaffolded · arms frozen + diff shown · banks
  recorded · smoke test done + repo clean · full runs launched · judged · results written.
