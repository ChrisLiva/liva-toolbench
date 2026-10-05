# crank-lite phase smoke harness

Runs one crank-lite phase headless against the ledger seed repo that `../lite-execute/build-seeds.sh` builds, and scores what the phase did, so a change to crank-lite's phase prose is measured on the models that run it instead of judged by reading.

## Scenarios

A scripted user replies "Agreed with your recommendations on these questions." to every round, then "done" once the phase's artifact exists, and the run ends one turn later.

| Scenario | Starts from | Invocation | What it exercises |
| --- | --- | --- | --- |
| `brainstorm-ui` | the bare seed | `brainstorm a monthly spending report page …` | Destination first, the agenda, the round loop, a mock or prototype on an experiential question, the brief's sections, the readback, the stop after "done" |
| `brainstorm-backend` | the bare seed | `brainstorm importing bank CSV exports …` | The same interview with no experiential question, so no mock offer and no narrated skip |
| `spec-ui` | `fixture/spec-ui/`, a brief with no `Prototype:` line and one single-file mock | `spec .crank/monthly-spending-report/brainstorm.md` | The grounding verify, VOCABULARY.md before the design questions, the prototype offer on a look question, the failure catalogue, the spec's sections |
| `spec-ui-verdict` | `fixture/spec-ui-verdict/`, a brief whose `Prototype:` line names `prototype/variant-a.html` | the same | Copying the brief's `Prototype:` line into the spec's key technical decisions, with no second offer |
| `spec-backend` | `fixture/spec-backend/`, a brief with no look or interaction question | `spec .crank/csv-import-dedupe/brainstorm.md` | The same with no prototype offer: `prototype_mentions` counts a narrated skip |
| `plan` | `../lite-execute/fixture/crank/spec.md` | `plan .crank/csv-export/spec.md` | The plan's parts, its stages, the heavy reviewer dispatch, the readback, and the hand-off to `/lite-execute` |

Each `fixture/<scenario>/` holds the `.crank/` directory a `brainstorm-*` run on crank-lite 1.52.0 left, copied whole so every mock path its brief names resolves.

## Run

```bash
S=<scratch dir>
SMOKE_SCENARIOS="spec-ui plan" ./scripts/smoke/crank-lite/batch.sh $S/batch 1 2 fix=<worktree>/plugins/crank-lite
python3 scripts/smoke/crank-lite/score.py $S/batch          # rates per scenario, per arm
python3 scripts/smoke/crank-lite/score.py --json $S/batch   # one JSON object per run
```

Run one rep of the scenarios the change touches on both models and compare against an earlier batch's base runs, the same budget as `../lite-execute/README.md` sets. `batch.sh <batch-dir> <reps> <parallel> <arm>=<plugin-dir> ...` runs each scenario `SMOKE_SCENARIOS` names for a Sonnet session under Claude Code and a gpt-6-luna session under Codex, narrowed to one model by `SMOKE_MODELS=sonnet`, and exits before starting a batch of more than `SMOKE_MAX_RUNS` sessions (default 6). `run.sh` drives one session the way `../lite-execute/run.sh` does, with the same settings, permission bypass, and Codex repo-skill copy, and writes `transcript.md`, each turn's sent message and assistant text with one line per tool call.

## Reading the scores

`score.py` counts what a stream shows: the artifact and its sections, question rounds and `❓`/`➡️` lines before the artifact, lookup dispatches, prototype mentions and builds, whether the next phase's file was read, VOCABULARY.md reads, failure-catalogue items in the spec, and the plan reviewer dispatch (n/a under Codex, whose stream hides spawn messages). A keyword count catches a run narrating a rule as well as following it, so read the transcript behind a surprising number.

The behaviors that need judgment, such as the destination settled before other decisions, dependent questions held for a later round, and the readback's shape, are scored by reading transcripts. Blind them first: copy each `transcript.md` under a neutral run name with the arm's paths replaced, and keep the mapping aside. The 2026-10-05 brainstorm batch (8 runs per arm) scored this way showed the INTERVIEW.md round loop at or above main on every judged behavior but question format, where two Sonnet runs replaced the format's em dash under the user-level no-em-dash rule.
