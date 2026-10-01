#!/bin/bash
# run.sh <plugin-dir> <scenario: fresh|stop-if|spec-path> <model> <seed-dir> <run-dir>
# Drives one headless lite-execute session against a clone of a seed repo and saves
# the stream, the git state, and the .crank/ artifacts under <run-dir>.
set -u
here=$(cd "$(dirname "$0")" && pwd)
PD=$(cd "$1" && pwd); scenario=$2; model=$3; seeds=$(cd "$4" && pwd)
rm -rf "$5"; mkdir -p "$5/turns"; run=$(cd "$5" && pwd)
SETTINGS='{"enabledPlugins":{"crank@liva-toolbench":false,"crank-lite@liva-toolbench":false}}'
REPLY="Go with your recommendation on anything open, and continue."
# The session works in a throwaway clone, so the default skips permission prompts: in auto
# mode a headless implementer's Write calls were denied and the run stalled on Task 1.
case ${SMOKE_PERMISSION_MODE:-bypass} in
  bypass) perm=(--dangerously-skip-permissions) ;;
  *) perm=(--permission-mode "$SMOKE_PERMISSION_MODE") ;;
esac
# SMOKE_SETTING_SOURCES=project,local leaves out the user-level CLAUDE.md, to test whether
# its instructions override a skill rule.
if [ -n "${SMOKE_SETTING_SOURCES:-}" ]; then perm+=(--setting-sources "$SMOKE_SETTING_SOURCES"); fi

case $scenario in
  fresh|spec-path) seed=$seeds/seed-fresh ;;
  stop-if) seed=$seeds/seed-stop-if ;;
  *) echo "unknown scenario $scenario" >&2; exit 2 ;;
esac
git clone -q "$seed" "$run/repo"
cd "$run/repo"
mkdir -p .crank/csv-export
cp "$here/fixture/crank/spec.md" .crank/csv-export/spec.md
cp "$here/fixture/crank/plan.md" .crank/csv-export/plan.md

case $scenario in
  fresh)
    printf '\nTODO(local): check the Q3 import before the release.\n' >> README.md
    ASK="/crank-lite:lite-execute .crank/csv-export/plan.md"; cap=4 ;;
  stop-if)
    base=$(git rev-parse --short HEAD~1); t1=$(git rev-parse --short HEAD)
    python3 - "$base" "$t1" <<'PY'
import sys
p = ".crank/csv-export/plan.md"
lines = open(p, encoding="utf-8").read().split("\n")
block = ["", "## Progress", "", f"Base: {sys.argv[1]}", f"- [x] Task 1: CSV serializer — {sys.argv[2]}",
         "- [ ] Task 2: Export route", "- [ ] Task 3: CLI export command",
         "- [ ] Task 4: Streaming export for large ledgers", "- [ ] Task 5: Docs"]
open(p, "w", encoding="utf-8").write("\n".join(lines[:1] + block + lines[1:]))
PY
    ASK="/crank-lite:lite-execute .crank/csv-export/plan.md stop at the stage 1 gate"; cap=1 ;;
  spec-path)
    ASK="/crank-lite:lite-execute .crank/csv-export/spec.md"; cap=1 ;;
esac
cp -R .crank "$run/crank-before"
git rev-parse HEAD > "$run/seed-head"
echo "$scenario $model" > "$run/arm"

sid=$(uuidgen | tr 'A-Z' 'a-z'); echo "$sid" > "$run/session-id"
start=$(date +%s)
for n in $(seq 1 "$cap"); do
  if [ "$n" = 1 ]; then first=(--session-id "$sid"); msg=$ASK; else first=(--resume "$sid"); msg=$REPLY; fi
  claude -p "${first[@]}" --model "$model" --output-format stream-json --verbose \
    "${perm[@]}" --strict-mcp-config --settings "$SETTINGS" --plugin-dir "$PD" \
    "$msg" < /dev/null > "$run/turns/$n.jsonl" 2> "$run/turns/$n.err"
  if [ "$scenario" = fresh ] && [ -f .crank/csv-export/retro.md ]; then break; fi
done
echo $(( $(date +%s) - start )) > "$run/seconds"
echo "$n" > "$run/turn-count"
git log --format='%h %s' > "$run/gitlog.txt"
git status --porcelain > "$run/status.txt"
git diff HEAD > "$run/diff.txt"
cp -R .crank "$run/crank-after"
