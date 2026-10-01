#!/bin/bash
# batch.sh <batch-dir> <reps> <parallel> <arm>=<plugin-dir> [<arm>=<plugin-dir> ...]
# Runs every scenario x model x rep for each arm, <parallel> sessions at a time, then
# scores the batch: python3 score.py <batch-dir>
set -euo pipefail
here=$(cd "$(dirname "$0")" && pwd)
batch=$1 reps=$2 par=$3; shift 3
mkdir -p "$batch"
"$here/build-seeds.sh" "$batch/seeds" > /dev/null
jobs=$batch/jobs.txt; : > "$jobs"
for scenario in fresh stop-if spec-path; do
  for rep in $(seq 1 "$reps"); do
    for model in sonnet haiku; do
      for armspec in "$@"; do
        arm=${armspec%%=*} pd=${armspec#*=}
        echo "$pd $scenario $model $batch/seeds $batch/$arm/$scenario-$model-$rep" >> "$jobs"
      done
    done
  done
done
echo "$(wc -l < "$jobs") runs, $par at a time; progress: ls $batch/*/*/seconds | wc -l"
xargs -P "$par" -L 1 "$here/run.sh" < "$jobs" > "$batch/batch.log" 2>&1
python3 "$here/score.py" "$batch"
