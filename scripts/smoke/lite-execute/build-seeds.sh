#!/bin/bash
# build-seeds.sh <out-dir>: build the three seed repos the runner clones.
#   <out-dir>/seed-fresh     ledger repo, no export work yet (scenarios A and C)
#   <out-dir>/seed-stop-if   every route goes through json_middleware, and Task 1 is
#                            already committed (scenario B)
#   <out-dir>/seed-stop-if-detour   the same, but json_middleware already offers an opt-out
#                            that the /health route uses (scenario D)
set -euo pipefail
here=$(cd "$(dirname "$0")" && pwd)
out=$1
rm -rf "$out/seed-fresh" "$out/seed-stop-if" "$out/seed-stop-if-detour"
mkdir -p "$out"
commit() { git -C "$1" -c user.name=smoke -c user.email=smoke@example.invalid commit -qm "$2"; }

cp -R "$here/fixture/repo" "$out/seed-fresh"
git -C "$out/seed-fresh" init -q -b main
git -C "$out/seed-fresh" add -A
commit "$out/seed-fresh" "chore: seed ledger"

for seed in stop-if stop-if-detour; do
  d=$out/seed-$seed
  cp -R "$here/fixture/repo" "$d"
  cp "$here/fixture/variants/api_${seed//-/_}.py" "$d/ledger/api.py"
  git -C "$d" init -q -b main
  git -C "$d" add -A
  commit "$d" "chore: seed ledger"
  cp "$here/fixture/variants/csv_export.py" "$d/ledger/"
  cp "$here/fixture/variants/test_csv_export.py" "$d/tests/"
  git -C "$d" add -A
  commit "$d" "feat(export): add the CSV serializer"
done
echo "seeds in $out"
