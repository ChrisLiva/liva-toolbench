#!/bin/bash
# skill-eval.sh [skill-name ...]
# Scans skills with NVIDIA SkillEvaluator and writes reports to reports/skill-eval/:
#   Tier 1 (static and security checks, no model) for each named skill, or every skill;
#   Tier 2 similarity of every skill's name and description, on local Ollama embeddings.
# It scans a copy of the tracked and unignored files under plugins/, so ignored caches
# (__pycache__, .complexipy_cache) never count as shipped content.
# Needs: uv tool install --python 3.13 "skillevaluator[tier2]==1.0.1"
#        ollama pull nomic-embed-text   (Tier 2 is skipped when Ollama is not serving)
set -euo pipefail
repo=$(cd "$(dirname "$0")/.." && pwd)
out=$repo/reports/skill-eval
command -v skillevaluator >/dev/null || { echo 'skillevaluator not found: uv tool install --python 3.13 "skillevaluator[tier2]==1.0.1"' >&2; exit 2; }

work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT
cd "$repo"
git ls-files -z --cached --others --exclude-standard -- plugins |
  while IFS= read -r -d '' f; do [ -f "$f" ] && printf '%s\0' "$f"; done |
  tar --null -T - -cf - | tar -xf - -C "$work"
mkdir -p "$work/collection"
for d in "$work"/plugins/*/skills/*/; do cp -R "$d" "$work/collection/$(basename "$d")"; done

rm -rf "$out"; mkdir -p "$out"
[ $# -gt 0 ] || { cd "$work/collection"; set -- *; cd "$repo"; }
failed=0
for n in "$@"; do
  [ -d "$work/collection/$n" ] || { echo "no skill named $n" >&2; exit 2; }
  skillevaluator tier1 "$work/collection/$n" --no-llm -r cli,json,html -o "$out/tier1/$n" > "$out/tier1-$n.txt" 2>&1 || failed=1
  python3 - "$out/tier1/$n/skillevaluator-tier1.json" "$n" <<'EOF'
import json, sys
d = json.load(open(sys.argv[1]))
bad = [f'{r["validator"]} {r["status"]}' for r in d["results"] if r["status"] in ("failed", "incomplete")]
print(f'tier1 {sys.argv[2]:18} {d["overall_status"]:9} {"; ".join(bad)}')
EOF
done

if curl -sf -m 3 http://localhost:11434/api/version >/dev/null; then
  SKILL_EVAL_EMBEDDING_PROVIDER=openai-compatible \
  SKILL_EVAL_EMBEDDING_BASE_URL=http://localhost:11434/v1 \
  SKILL_EVAL_EMBEDDING_MODEL=nomic-embed-text \
  SKILL_EVAL_EMBEDDING_API_KEY=local-no-key \
    skillevaluator similarity-check "$work/collection" --type skill -r cli,json,html -o "$out/tier2" > "$out/tier2.txt" 2>&1 || true
  python3 - "$out/tier2/skillevaluator-similarity.json" <<'EOF'
import json, sys
for r in json.load(open(sys.argv[1]))["results"]:
    for f in r["findings"]:
        m = f["metadata"]
        print(f'tier2 {m["score"]:.3f} {m["classification"]:15} {m["entry_a"]} <-> {m["entry_b"]}')
EOF
else
  echo "tier2 skipped: Ollama is not serving on localhost:11434"
fi
echo "reports: $out"
exit $failed
