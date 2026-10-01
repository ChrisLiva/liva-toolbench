# lite-execute smoke harness

Runs crank-lite's `lite-execute` skill headless against a small standard-library Python repo and scores what the orchestrator did, so a change to the skill's prose is measured on the models that execute it instead of judged by reading.

## Scenarios

The fixture plan (`fixture/crank/plan.md`) adds a CSV export to a ledger package in five tasks across two stages. It carries a Global Constraint (every CSV is UTF-8 with a BOM), a stale function name in Task 3 (`read_all`, which the repo calls `load_entries`), tasks with no named check, a Coverage table with a human-only row, and a `Stop if:` line on Task 2.

| Scenario | Seed | Invocation | What it exercises |
| --- | --- | --- | --- |
| `fresh` | `seed-fresh`, plus an uncommitted README edit | `/crank-lite:lite-execute .crank/csv-export/plan.md` | The whole run: Pre-flight, dispatch briefs, per-task commits, the stage gate, Coverage, review, retro |
| `stop-if` | `seed-stop-if`: Task 1 committed, every route forced through `json_middleware` | the same, plus `stop at the stage 1 gate` | A resumed bounded run that must stop at Task 2's `Stop if:` and leave a short-run ledger |
| `spec-path` | `seed-fresh` | `/crank-lite:lite-execute .crank/csv-export/spec.md` | Refusing a file that is not a plan |

## Run

```bash
S=<scratch dir>
git worktree add --detach $S/wt-base main            # one arm per plugin copy
./scripts/smoke/lite-execute/batch.sh $S/batch 5 6 base=$S/wt-base/plugins/crank-lite fix=<worktree>/plugins/crank-lite
python3 scripts/smoke/lite-execute/score.py $S/batch          # pass rate per check, per arm
python3 scripts/smoke/lite-execute/score.py --json $S/batch   # one JSON object per run
```

`batch.sh <batch-dir> <reps> <parallel> <arm>=<plugin-dir> ...` runs every scenario for Sonnet and Haiku orchestrators. `run.sh` drives one session and saves its stream (`turns/*.jsonl`), the repo, and `.crank/` before and after. Each session works in a throwaway clone with permission prompts skipped: in auto mode a headless implementer's `Write` calls were denied and the run stalled on Task 1. Set `SMOKE_PERMISSION_MODE=<mode>` to run under a permission mode instead.

The sessions load the user-level `CLAUDE.md`, so its subagent model preference sets the implementer and reviewer models. `--settings` disables the marketplace installs of crank and crank-lite, so only the `--plugin-dir` copy loads.

## Reading the scores

A check scores 1 when the run did what the skill's rules ask, 0 when it did not, and `n/a` when the run never reached the point the check judges. Read the transcript behind a surprising number before trusting it: a keyword count catches a run narrating a rule as well as following it.
