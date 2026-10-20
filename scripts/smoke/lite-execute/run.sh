#!/bin/bash
# run.sh <plugin-dir> <scenario: fresh|stop-if|stop-if-detour|spec-path|prototype|prototype-solo|review|review-large> <model> <seed-dir> <run-dir>
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
inv=/crank-lite:lite-execute
# Smoke sessions bill the claude.ai subscription. An API key in the environment would switch them
# to API billing, so drop it, and refuse to start (status 255 stops batch.sh's xargs) unless the
# CLI still reports the subscription login.
unset ANTHROPIC_API_KEY ANTHROPIC_AUTH_TOKEN
auth=$(claude auth status 2>/dev/null | python3 -c 'import json, sys; print(json.load(sys.stdin).get("authMethod", ""))' 2>/dev/null)
if [ "$auth" != claude.ai ]; then
  echo "run.sh: claude auth method is '$auth', not claude.ai; run claude auth login" >&2
  exit 255
fi

case $scenario in
  fresh|spec-path) seed=$seeds/seed-fresh ;;
  stop-if|stop-if-detour|review|review-large) seed=$seeds/seed-$scenario ;;
  prototype|prototype-solo) seed=$seeds/seed-prototype ;;
  *) echo "unknown scenario $scenario" >&2; exit 2 ;;
esac
git clone -q "$seed" "$run/repo"
cd "$run/repo"
case $scenario in
  prototype|prototype-solo)
    slug=ledger-report; plan=plan.md
    if [ "$scenario" = prototype-solo ]; then plan=plan-solo.md; fi
    mkdir -p .crank/$slug
    cp -R "$here/fixture/prototype/crank/spec.md" "$here/fixture/prototype/crank/prototype" .crank/$slug/
    cp "$here/fixture/prototype/crank/$plan" .crank/$slug/plan.md ;;
  review-large)
    slug=bank-import
    mkdir -p .crank/$slug
    cp "$here/fixture/review-large/crank/spec.md" "$here/fixture/review-large/crank/plan.md" .crank/$slug/ ;;
  *)
    slug=csv-export
    mkdir -p .crank/$slug
    cp "$here/fixture/crank/spec.md" .crank/$slug/spec.md
    cp "$here/fixture/crank/plan.md" .crank/$slug/plan.md ;;
esac

# progress <base> <sha>...: write the plan's Progress block, one checked task per sha in task order.
progress() {
  python3 - ".crank/$slug/plan.md" "$@" <<'PY'
import re, sys
p, base, shas = sys.argv[1], sys.argv[2], sys.argv[3:]
lines = open(p, encoding="utf-8").read().split("\n")
titles = [m.group(1) for m in map(re.compile(r"^### Task \d+: (.+)$").match, lines) if m]
tasks = [f"- [x] Task {n}: {t} — {shas[n - 1]}" if n <= len(shas) else f"- [ ] Task {n}: {t}"
         for n, t in enumerate(titles, 1)]
open(p, "w", encoding="utf-8").write("\n".join(lines[:1] + ["", "## Progress", "", f"Base: {base}"] + tasks + lines[1:]))
PY
}
case $scenario in
  fresh)
    printf '\nTODO(local): check the Q3 import before the release.\n' >> README.md
    ASK="$inv .crank/csv-export/plan.md"; cap=4 ;;
  stop-if|stop-if-detour)
    progress "$(git rev-parse --short HEAD~1)" "$(git rev-parse --short HEAD)"
    ASK="$inv .crank/csv-export/plan.md stop at the stage 1 gate"; cap=1
    # A run that stops to ask on the settleable Stop if gets one reply, so turn-count records the stop.
    if [ "$scenario" = stop-if-detour ]; then cap=2; fi ;;
  spec-path)
    ASK="$inv .crank/csv-export/spec.md"; cap=1 ;;
  review)
    # Every task is committed and checked, so the run goes straight to Review.
    progress "$(git rev-parse --short HEAD~5)" $(git log --reverse --format=%h -5)
    ASK="$inv .crank/csv-export/plan.md"; cap=2 ;;
  review-large)
    progress "$(git rev-parse --short HEAD~12)" $(git log --reverse --format=%h -12)
    ASK="$inv .crank/bank-import/plan.md"; cap=2 ;;
  prototype|prototype-solo)
    ASK="$inv .crank/ledger-report/plan.md"; cap=4 ;;
esac
cp -R .crank "$run/crank-before"
git rev-parse HEAD > "$run/seed-head"
echo "$scenario $model" > "$run/arm"

sid=$(uuidgen | tr 'A-Z' 'a-z'); echo "$sid" > "$run/session-id"
start=$(date +%s)
for n in $(seq 1 "$cap"); do
  if [ "$n" = 1 ]; then msg=$ASK; else msg=$REPLY; fi
  if [ "$n" = 1 ]; then first=(--session-id "$sid"); else first=(--resume "$sid"); fi
  claude -p "${first[@]}" --model "$model" --output-format stream-json --verbose \
    "${perm[@]}" --strict-mcp-config --settings "$SETTINGS" --plugin-dir "$PD" \
    "$msg" < /dev/null > "$run/turns/$n.jsonl" 2> "$run/turns/$n.err"
  case $scenario in fresh|prototype|prototype-solo|review|review-large) if [ -f .crank/$slug/retro.md ]; then break; fi ;; esac
  if [ "$scenario" = stop-if-detour ] && grep -q '^- \[x\] Task 2' .crank/csv-export/plan.md; then break; fi
done
echo $(( $(date +%s) - start )) > "$run/seconds"
echo "$n" > "$run/turn-count"
git log --format='%h %s' > "$run/gitlog.txt"
git status --porcelain > "$run/status.txt"
git diff HEAD > "$run/diff.txt"
cp -R .crank "$run/crank-after"
# A subagent's turns live in the session's transcript directory, keyed on the clone's resolved
# path: on macOS a mktemp dir under /var/folders resolves to /private/var/folders.
proj=$(cd "$run/repo" && pwd -P | tr -d '\n' | tr -c 'A-Za-z0-9' '-')
subs=${CLAUDE_CONFIG_DIR:-$HOME/.claude}/projects/$proj/$sid/subagents
if [ -d "$subs" ]; then cp -R "$subs" "$run/subagents"; fi
