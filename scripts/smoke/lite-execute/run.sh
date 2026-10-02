#!/bin/bash
# run.sh <plugin-dir> <scenario: fresh|stop-if|stop-if-detour|spec-path> <model> <seed-dir> <run-dir>
# Drives one headless lite-execute session against a clone of a seed repo and saves
# the stream, the git state, and the .crank/ artifacts under <run-dir>.
# SMOKE_HARNESS=codex drives `codex exec` instead of `claude -p`, at SMOKE_EFFORT (default high).
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
harness=${SMOKE_HARNESS:-claude}
case $harness in
  claude) inv=/crank-lite:lite-execute ;;
  codex) inv='$lite-execute' ;;
  *) echo "unknown harness $harness" >&2; exit 2 ;;
esac

case $scenario in
  fresh|spec-path) seed=$seeds/seed-fresh ;;
  stop-if|stop-if-detour) seed=$seeds/seed-$scenario ;;
  *) echo "unknown scenario $scenario" >&2; exit 2 ;;
esac
git clone -q "$seed" "$run/repo"
cd "$run/repo"
mkdir -p .crank/csv-export
cp "$here/fixture/crank/spec.md" .crank/csv-export/spec.md
cp "$here/fixture/crank/plan.md" .crank/csv-export/plan.md
if [ "$harness" = codex ]; then
  # Codex loads the arm's copy as a repo skill. The exclude keeps it out of every git status
  # the session and the scorer read.
  mkdir -p .agents/skills
  cp -R "$PD/skills/lite-execute" .agents/skills/
  echo /.agents/ >> .git/info/exclude
fi

case $scenario in
  fresh)
    printf '\nTODO(local): check the Q3 import before the release.\n' >> README.md
    ASK="$inv .crank/csv-export/plan.md"; cap=4 ;;
  stop-if|stop-if-detour)
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
    ASK="$inv .crank/csv-export/plan.md stop at the stage 1 gate"; cap=1
    # A run that stops to ask on the settleable Stop if gets one reply, so turn-count records the stop.
    if [ "$scenario" = stop-if-detour ]; then cap=2; fi ;;
  spec-path)
    ASK="$inv .crank/csv-export/spec.md"; cap=1 ;;
esac
cp -R .crank "$run/crank-before"
git rev-parse HEAD > "$run/seed-head"
echo "$scenario $model" > "$run/arm"

sid=$(uuidgen | tr 'A-Z' 'a-z'); echo "$sid" > "$run/session-id"
# Codex runs in its workspace-write sandbox with approvals off, so it writes only inside this
# clone and its .git. The installed crank plugins stay off so only the arm's copy loads.
cx=(--json -m "$model" -c "model_reasoning_effort=\"${SMOKE_EFFORT:-high}\"" -c 'approval_policy="never"'
    -c 'sandbox_mode="workspace-write"' -c "sandbox_workspace_write.writable_roots=[\"$run/repo/.git\"]"
    -c 'notify=[]' -c 'plugins."crank@liva-toolbench".enabled=false'
    -c 'plugins."crank-lite@liva-toolbench".enabled=false')
start=$(date +%s)
for n in $(seq 1 "$cap"); do
  if [ "$n" = 1 ]; then msg=$ASK; else msg=$REPLY; fi
  if [ "$harness" = codex ]; then
    if [ "$n" = 1 ]; then codex exec "${cx[@]}" "$msg"; else codex exec resume "${cx[@]}" "$sid" "$msg"; fi \
      < /dev/null > "$run/turns/$n.jsonl" 2> "$run/turns/$n.err"
    if [ "$n" = 1 ]; then
      sid=$(python3 -c 'import json,sys; print(json.loads(open(sys.argv[1]).readline())["thread_id"])' "$run/turns/1.jsonl")
      echo "$sid" > "$run/session-id"
    fi
  else
    if [ "$n" = 1 ]; then first=(--session-id "$sid"); else first=(--resume "$sid"); fi
    claude -p "${first[@]}" --model "$model" --output-format stream-json --verbose \
      "${perm[@]}" --strict-mcp-config --settings "$SETTINGS" --plugin-dir "$PD" \
      "$msg" < /dev/null > "$run/turns/$n.jsonl" 2> "$run/turns/$n.err"
  fi
  if [ "$scenario" = fresh ] && [ -f .crank/csv-export/retro.md ]; then break; fi
  if [ "$scenario" = stop-if-detour ] && grep -q '^- \[x\] Task 2' .crank/csv-export/plan.md; then break; fi
done
echo $(( $(date +%s) - start )) > "$run/seconds"
echo "$n" > "$run/turn-count"
git log --format='%h %s' > "$run/gitlog.txt"
git status --porcelain > "$run/status.txt"
git diff HEAD > "$run/diff.txt"
cp -R .crank "$run/crank-after"
if [ "$harness" = codex ]; then
  # The --json stream leaves out spawns and some commands, so the scorer reads the session's
  # rollout files: the orchestrator's thread and every subagent thread under it.
  mkdir -p "$run/rollouts"
  python3 - "$sid" "${CODEX_HOME:-$HOME/.codex}/sessions" "$run/rollouts" "$run/arm" <<'PY'
import json, shutil, sys
from pathlib import Path
root, sessions, out, marker = sys.argv[1], Path(sys.argv[2]), Path(sys.argv[3]), Path(sys.argv[4])
since = marker.stat().st_mtime
parents = {}
for f in sessions.rglob("rollout-*.jsonl"):
    if f.stat().st_mtime < since:
        continue
    with f.open(encoding="utf-8") as fh:
        meta = json.loads(fh.readline()).get("payload", {})
    src = meta.get("source")
    spawn = src.get("subagent", {}).get("thread_spawn", {}) if isinstance(src, dict) else {}
    parents[meta.get("id")] = (f, spawn.get("parent_thread_id"))
keep = {root}
while True:
    more = {t for t, (_, parent) in parents.items() if parent in keep} - keep
    if not more:
        break
    keep |= more
for t in keep & parents.keys():
    shutil.copy(parents[t][0], out / parents[t][0].name)
PY
fi
