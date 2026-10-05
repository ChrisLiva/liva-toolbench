#!/bin/bash
# batch.sh <batch-dir> <reps> <parallel> <arm>=<plugin-dir> [<arm>=<plugin-dir> ...]
# Runs every scenario x model x rep for each arm, <parallel> sessions at a time, then scores
# the batch: python3 score.py <batch-dir>
# SMOKE_SCENARIOS names the scenarios to run (required) and SMOKE_MODELS the models (default: sonnet gpt-6-luna).
# A batch of more than SMOKE_MAX_RUNS sessions (default 6) exits before it starts any.
set -euo pipefail
here=$(cd "$(dirname "$0")" && pwd)
batch=$1 reps=$2 par=$3; shift 3
: "${SMOKE_SCENARIOS:?set it to the scenarios the change touches, from: brainstorm-ui brainstorm-backend spec-ui spec-ui-verdict spec-backend plan}"
mkdir -p "$batch"
jobs=$batch/jobs.txt; : > "$jobs"
for scenario in $SMOKE_SCENARIOS; do
  for rep in $(seq 1 "$reps"); do
    for model in ${SMOKE_MODELS:-sonnet gpt-6-luna}; do
      for armspec in "$@"; do
        arm=${armspec%%=*} pd=${armspec#*=}
        echo "$pd $scenario $model $batch/seeds $batch/$arm/$scenario-$model-$rep" >> "$jobs"
      done
    done
  done
done
runs=$(wc -l < "$jobs" | tr -d ' ') max=${SMOKE_MAX_RUNS:-6}
if [ "$runs" -gt "$max" ]; then
  echo "batch.sh: $runs runs exceed SMOKE_MAX_RUNS=$max; drop scenarios, reps, models, or arms, or raise SMOKE_MAX_RUNS for a check that moved" >&2
  exit 1
fi
"$here/../lite-execute/build-seeds.sh" "$batch/seeds" > /dev/null
echo "$runs runs, $par at a time; progress: ls $batch/*/*/seconds | wc -l"
xargs -P "$par" -L 1 "$here/run.sh" < "$jobs" > "$batch/batch.log" 2>&1
python3 "$here/score.py" "$batch"
