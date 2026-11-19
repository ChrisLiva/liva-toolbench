#!/bin/bash
# skill-eval-tier3.sh <skill-name> [cases]
# Runs SkillEvaluator Tier 3 on one skill: Claude Code attempts each case with and without the skill,
# and Opus writes the cases and grades the attempts through claude_chat_shim.py. Every session runs
# on your Claude subscription. Each case starts two agent sessions plus the writing and grading calls,
# and the agent sessions count against a skill change's three-run budget (AGENTS.md, Iteration loop).
# Reports go to reports/skill-eval/tier3/<skill>/.
# Needs: a token from `claude setup-token`, stored with
#          security add-generic-password -a "$USER" -s skill-eval-claude-oauth -w
#        (or exported as CLAUDE_CODE_OAUTH_TOKEN).
set -euo pipefail
skill=${1:?usage: skill-eval-tier3.sh <skill-name> [cases]}
cases=${2:-1}
case $cases in ''|*[!0-9]*) echo "cases must be a positive integer" >&2; exit 2;; esac
repo=$(cd "$(dirname "$0")/.." && pwd)
out=$repo/reports/skill-eval/tier3/$skill
kept=$repo/scripts/skill-eval-cases/$skill.json
venv=${XDG_DATA_HOME:-$HOME/.local/share}/liva-toolbench/skillevaluator-tier3
patch=$repo/scripts/skillevaluator-oauth.patch

stamp=$(shasum -a 256 "$patch" | cut -c1-16)
if [ "$(cat "$venv/.patched" 2>/dev/null)" != "$stamp" ]; then
  echo "building $venv"
  rm -rf "$venv"
  uv venv -q --python 3.13 "$venv"
  uv pip install -q --python "$venv/bin/python" "skillevaluator[tier3]==1.0.1"
  patch -s -p1 -d "$("$venv/bin/python" -c 'import sysconfig; print(sysconfig.get_paths()["purelib"])')" < "$patch"
  echo "$stamp" > "$venv/.patched"
fi

token=${CLAUDE_CODE_OAUTH_TOKEN:-$(security find-generic-password -s skill-eval-claude-oauth -w 2>/dev/null || true)}
[ -n "$token" ] || { echo "no subscription token: run 'claude setup-token', then: security add-generic-password -a \"\$USER\" -s skill-eval-claude-oauth -w" >&2; exit 2; }

cd "$repo"
src=
for d in plugins/*/skills/"$skill"; do [ -d "$d" ] && src=$d; done
[ -n "$src" ] || { echo "no skill named $skill" >&2; exit 2; }
rm -rf "$out"; mkdir -p "$out"
git ls-files -z --cached --others --exclude-standard -- "$src" |
  while IFS= read -r -d '' f; do [ -f "$f" ] && printf '%s\0' "$f"; done |
  tar --null -T - -cf - | tar -xf - --strip-components 3 -C "$out"
# SkillEvaluator ignores disable-model-invocation, but Claude Code honors it, so the staged copy drops
# it: the with-skill arm then measures the skill an agent could choose, not one it can never load.
sed -i '' '/^disable-model-invocation: true$/d' "$out/$skill/SKILL.md"

model=${SKILL_EVAL_LLM_MODEL:-claude-opus-5-5}
CLAUDE_CODE_OAUTH_TOKEN=$token python3 "$repo/scripts/claude_chat_shim.py" "$model" > "$out/shim.port" 2> "$out/shim.log" &
shim=$!
trap 'kill "$shim" 2>/dev/null || true' EXIT
until [ -s "$out/shim.port" ]; do
  kill -0 "$shim" 2>/dev/null || { cat "$out/shim.log" >&2; exit 1; }
  sleep 0.2
done
port=$(cat "$out/shim.port")
export SKILL_EVAL_LLM_PROVIDER=openai-compatible SKILL_EVAL_LLM_BASE_URL="http://127.0.0.1:$port/v1" \
  SKILL_EVAL_LLM_API_KEY=subscription SKILL_EVAL_LLM_MODEL=$model
mkdir -p "$out/$skill/evals"
if [ -f "$kept" ]; then
  cp "$kept" "$out/$skill/evals/evals.json"
else
  full=(); [ "$cases" -gt 1 ] && full=(--full)
  "$venv/bin/skillevaluator" tier3 create-eval-dataset "$out/$skill" --grounding skill "${full[@]+"${full[@]}"}" < /dev/null
  echo "starter cases written; review them, then keep them with: cp $out/$skill/evals/evals.json $kept"
fi

CLAUDE_FORCE_OAUTH=1 CLAUDE_CODE_OAUTH_TOKEN=$token "$venv/bin/skillevaluator" tier3 evaluate "$out/$skill" \
  --agents claude-code --env-mode local --n-attempts 1 --n-concurrent 1 --max-cases "$cases" \
  --agent-model claude-code="${SKILL_EVAL_AGENT_MODEL:-claude-sonnet-5-5}" --results-dir "$out/results" < /dev/null
