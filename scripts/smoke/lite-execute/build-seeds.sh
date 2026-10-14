#!/bin/bash
# build-seeds.sh <out-dir>: build the five seed repos the runner clones.
#   <out-dir>/seed-fresh     ledger repo, no export work yet (scenarios A and C)
#   <out-dir>/seed-stop-if   every route goes through json_middleware, and Task 1 is
#                            already committed (scenario B)
#   <out-dir>/seed-stop-if-detour   the same, but json_middleware already offers an opt-out
#                            that the /health route uses (scenario D)
#   <out-dir>/seed-prototype   a ledger CSV reader with no report page yet (the prototype scenarios)
#   <out-dir>/seed-review    all five CSV-export tasks committed, one commit each, carrying the
#                            review scenario's planted defects (README.md lists them)
set -euo pipefail
here=$(cd "$(dirname "$0")" && pwd)
out=$1
rm -rf "$out/seed-fresh" "$out/seed-stop-if" "$out/seed-stop-if-detour" "$out/seed-prototype" "$out/seed-review"
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

cp -R "$here/fixture/prototype/repo" "$out/seed-prototype"
git -C "$out/seed-prototype" init -q -b main
git -C "$out/seed-prototype" add -A
commit "$out/seed-prototype" "feat: read ledger entries"

d=$out/seed-review
cp -R "$here/fixture/repo" "$d"
git -C "$d" init -q -b main
git -C "$d" add -A
commit "$d" "chore: seed ledger"
msgs=("feat(export): add the CSV serializer" "feat(export): serve the ledger as a CSV download"
      "feat(export): add the export CLI command" "feat(export): stream large ledgers to the CSV file"
      "docs: document the list and export commands")
for task in 1 2 3 4 5; do
  cp -R "$here/fixture/review/$task/." "$d/"
  git -C "$d" add -A
  commit "$d" "${msgs[$((task - 1))]}"
done
echo "seeds in $out"
