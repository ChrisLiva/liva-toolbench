# lite-execute smoke harness

Runs crank-lite's `lite-execute` skill headless against a small standard-library Python repo and scores what the orchestrator did, so a change to the skill's prose is measured on the models that execute it instead of judged by reading.

## Scenarios

The CSV-export fixture plan (`fixture/crank/plan.md`) adds a CSV export to a ledger package in five tasks across two stages. It carries a Global Constraint (every CSV is UTF-8 with a BOM), a stale function name in Task 3 (`read_all`, which the repo calls `load_entries`), tasks with no named check, a Coverage table with a human-only row, and a `Stop if:` line on Task 2.

The prototype fixture (`fixture/prototype/`) adds an HTML report page to a ledger CSV reader. Its spec's `Prototype:` line names the winning variant, `prototype/variant-b.html`, with what the user took from variant A (sticky month headers) and left out of B (sparklines). Its plans restate the verdict as "totals in a left sidebar" and never mention the prototype, the shape a plan takes when its writer summarized the verdict into task text. No artifact's text places the memo filter, but variant B puts it inside the sidebar as the winner's primary affordance, so the verdict commits that placement. Variant B also shows two open details that no artifact's text names: negatives in parentheses, and each month header carrying that month's net.

| Scenario | Seed | Invocation | What it exercises |
| --- | --- | --- | --- |
| `fresh` | `seed-fresh`, plus an uncommitted README edit | `/crank-lite:lite-execute .crank/csv-export/plan.md` | The whole run: Pre-flight, dispatch briefs, per-task commits, the stage gate, Coverage, review, retro |
| `stop-if` | `seed-stop-if`: Task 1 committed, every route forced through `json_middleware` | the same, plus `stop at the stage 1 gate` | A resumed bounded run whose Task 2 `Stop if:` has no route the code offers: it must stop, put the decision to the user as numbered options, and leave a short-run ledger |
| `stop-if-detour` | `seed-stop-if-detour`: the same, but `json_middleware` honors a `keep_content_type=True` opt-out that `/health` already uses | the same | A `Stop if:` the orchestrator must settle itself: commit Task 2 through the opt-out without editing the middleware, reach the Bound in one turn, and bank the fact in grounding |
| `spec-path` | `seed-fresh` | `/crank-lite:lite-execute .crank/csv-export/spec.md` | Refusing a file that is not a plan |
| `prototype` | `seed-prototype` | `/crank-lite:lite-execute .crank/ledger-report/plan.md` | A four-task sequential run whose page task restates a prototype verdict: the page dispatch carries the spec's `Prototype:` line, its implementer reads the winning variant, and the page follows the verdict and the mock's open details |
| `prototype-solo` | `seed-prototype` | the same, with the three-task `plan-solo.md` | The same page built inline by a solo orchestrator |

## Run

```bash
S=<scratch dir>
SMOKE_SCENARIOS="fresh stop-if" ./scripts/smoke/lite-execute/batch.sh $S/batch 1 2 fix=<worktree>/plugins/crank-lite
python3 scripts/smoke/lite-execute/score.py $S/batch          # pass rate per check, per arm
python3 scripts/smoke/lite-execute/score.py --json $S/batch   # one JSON object per run
```

`batch.sh <batch-dir> <reps> <parallel> <arm>=<plugin-dir> ...` runs each scenario `SMOKE_SCENARIOS` names for a Sonnet orchestrator under Claude Code and a gpt-6-luna orchestrator under Codex; `SMOKE_MODELS=sonnet` narrows it to one model. It exits before starting a batch of more than `SMOKE_MAX_RUNS` sessions (default 6). A base arm is a second `<arm>=<plugin-dir>` on a `git worktree add --detach $S/wt-base main` copy. `run.sh` drives one session and saves its stream (`turns/*.jsonl`), the repo, and `.crank/` before and after. Each session works in a throwaway clone with permission prompts skipped: in auto mode a headless implementer's `Write` calls were denied and the run stalled on Task 1. Set `SMOKE_PERMISSION_MODE=<mode>` to run under a permission mode instead. Set `SMOKE_SETTING_SOURCES=project,local` to leave out the user-level `CLAUDE.md`; implementers then fall back to the skill's harness tiers.

Start with one rep of each scenario the change touches on both models, one arm, as the command above runs, and compare it against an earlier batch's base runs; add a rep or a base arm, raising `SMOKE_MAX_RUNS` when the batch needs it, only for a check that moved (per project decision: run fewer runs overall, after a 72-run batch hit the account's usage limit). The 2026-10-02 batch (crank-lite 1.50.0 against 1.51.0, 59 Claude runs and 18 Codex runs at three reps per arm) had six checks where the arms differed by two or more runs, such as Haiku's `decision_options` going from 0/3 to 3/3 in `stop-if`, and the first rep alone showed all six. The third rep changed 17 verdicts, each by a single run, so settle a one-run difference between arms by reading both runs' transcripts.

The sessions load the user-level `CLAUDE.md`, so its subagent model preference sets the implementer and reviewer models. `--settings` disables the marketplace installs of crank and crank-lite, so only the `--plugin-dir` copy loads.

`run.sh` runs a `gpt-*` model under `codex exec`, with `SMOKE_EFFORT` setting `model_reasoning_effort` (default `high`), and every other model under `claude -p`.

A Codex session loads the arm's `skills/lite-execute` as a repo skill under the clone's `.agents/skills/`, kept out of `git status` by `.git/info/exclude`, and runs with the installed crank and crank-lite plugins disabled. It runs in Codex's `workspace-write` sandbox with approvals off and the clone's `.git` as an extra writable root, so it writes only inside the clone. The `--json` stream leaves out spawns and some commands, so `run.sh` copies the session's rollout files (the orchestrator thread and every subagent thread under it) from `~/.codex/sessions` into `rollouts/`, and `score.py` reads those. Codex encrypts the message a spawn sends, so the brief checks score `n/a` on Codex; `impl_reads_brief` scores whether each implementer opened `IMPLEMENTER-BRIEF.md` instead. The user-level `~/.codex/AGENTS.md` sets the subagent model, which `impl_model_user` checks against.

## Reading the scores

A check scores 1 when the run did what the skill's rules ask, 0 when it did not, and `n/a` when the run never reached the point the check judges. `finished_first_turn` (fresh and both prototype scenarios) and `no_user_stop` (stop-if-detour) catch an orchestrator that ends its turn after a subagent returns or after settling a stop: `run.sh` answers such a stop with a "continue" reply, so the run still finishes but takes more than one turn. Read the transcript behind a surprising number before trusting it: a keyword count catches a run narrating a rule as well as following it.

In the prototype scenarios, `filter_in_sidebar`, `sticky_month_headers`, and `no_sparklines` follow the verdict, and `parenthesized_negatives` and `month_net` follow the open details. The open-detail pair carries the signal: on Sonnet orchestrators with three reps per arm, crank-lite 1.49.0 scored 0/6 on each across both scenarios, and 1.50.0 scored 5/6 and 6/6 (2026-10-02). A solo orchestrator may render the page in a headless browser to compare it with the mock, and the `sleep` in its cleanup trips `no_sleep_polling`.
