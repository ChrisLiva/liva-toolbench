#!/bin/bash
# run.sh <plugin-dir> <scenario> <model> <seed-dir> <run-dir>
# Drives one headless crank-lite phase session against a clone of the ledger seed and saves
# each turn's stream, the git state, and the .crank/ artifacts under <run-dir>.
# Scenarios: brainstorm-ui, brainstorm-backend, spec-ui, spec-ui-verdict, spec-backend, plan.
# The scripted user agrees with each round, says "done" once the phase's artifact exists,
# and the run ends one turn later, so a phase that loads the next one on its own shows there.
# A gpt-* model runs under `codex exec` at SMOKE_EFFORT (default high), any other under `claude -p`.
set -u
here=$(cd "$(dirname "$0")" && pwd)
PD=$(cd "$1" && pwd); scenario=$2; model=$3; seeds=$(cd "$4" && pwd)
rm -rf "$5"; mkdir -p "$5/turns"; run=$(cd "$5" && pwd)
SETTINGS='{"enabledPlugins":{"crank@liva-toolbench":false,"crank-lite@liva-toolbench":false}}'
REPLY="Agreed with your recommendations on these questions."
case $model in
  gpt-*) harness=codex inv='$crank-lite' ;;
  *) harness=claude inv=/crank-lite:crank-lite ;;
esac
git clone -q "$seeds/seed-fresh" "$run/repo"
cd "$run/repo"
case $scenario in
  brainstorm-ui)
    artifact=brainstorm.md
    ASK="$inv brainstorm a monthly spending report page for the ledger, something I can open in a browser to see where the money went" ;;
  brainstorm-backend)
    artifact=brainstorm.md
    ASK="$inv brainstorm importing bank CSV exports into the ledger without creating duplicate entries" ;;
  spec-ui|spec-ui-verdict|spec-backend)
    mkdir -p .crank && printf '*\n' > .crank/.gitignore
    cp -R "$here/fixture/$scenario/"* .crank/
    slug=$(ls "$here/fixture/$scenario")
    artifact=spec.md ASK="$inv spec .crank/$slug/brainstorm.md" ;;
  plan)
    mkdir -p .crank/csv-export && printf '*\n' > .crank/.gitignore
    cp "$here/../lite-execute/fixture/crank/spec.md" .crank/csv-export/
    artifact=plan.md ASK="$inv plan .crank/csv-export/spec.md" ;;
  *) echo "unknown scenario $scenario" >&2; exit 2 ;;
esac
if [ "$harness" = codex ]; then
  # Codex loads the arm's copy as a repo skill; the exclude keeps it out of git status.
  mkdir -p .agents/skills
  cp -R "$PD/skills/crank-lite" .agents/skills/
  echo /.agents/ >> .git/info/exclude
fi
cp -R .crank "$run/crank-before" 2> /dev/null || true
echo "$scenario $model" > "$run/arm"
echo "$artifact" > "$run/artifact"
sid=$(uuidgen | tr 'A-Z' 'a-z')
cx=(--json -m "$model" -c "model_reasoning_effort=\"${SMOKE_EFFORT:-high}\"" -c 'approval_policy="never"'
    -c 'sandbox_mode="workspace-write"' -c "sandbox_workspace_write.writable_roots=[\"$run/repo/.git\"]"
    -c 'notify=[]' -c 'plugins."crank@liva-toolbench".enabled=false'
    -c 'plugins."crank-lite@liva-toolbench".enabled=false')
start=$(date +%s)
cap=${SMOKE_CAP:-12}; written=0
for n in $(seq 1 "$cap"); do
  if [ "$n" = 1 ]; then msg=$ASK; elif [ "$written" = 1 ]; then msg=done; else msg=$REPLY; fi
  echo "$msg" > "$run/turns/$n.sent"
  if [ "$harness" = codex ]; then
    if [ "$n" = 1 ]; then codex exec "${cx[@]}" "$msg"; else codex exec resume "${cx[@]}" "$sid" "$msg"; fi \
      < /dev/null > "$run/turns/$n.jsonl" 2> "$run/turns/$n.err"
    if [ "$n" = 1 ]; then
      sid=$(python3 -c 'import json,sys; print(json.loads(open(sys.argv[1]).readline())["thread_id"])' "$run/turns/1.jsonl")
    fi
  else
    if [ "$n" = 1 ]; then first=(--session-id "$sid"); else first=(--resume "$sid"); fi
    claude -p "${first[@]}" --model "$model" --output-format stream-json --verbose \
      --dangerously-skip-permissions --strict-mcp-config --settings "$SETTINGS" --plugin-dir "$PD" \
      "$msg" < /dev/null > "$run/turns/$n.jsonl" 2> "$run/turns/$n.err"
  fi
  if [ "$written" = 1 ]; then break; fi
  if ls .crank/*/"$artifact" > /dev/null 2>&1; then written=1; fi
done
echo $(( $(date +%s) - start )) > "$run/seconds"
echo "$n" > "$run/turn-count"
echo "$sid" > "$run/session-id"
git status --porcelain > "$run/status.txt"
cp -R .crank "$run/crank-after" 2> /dev/null || true
python3 "$here/extract.py" "$run"
