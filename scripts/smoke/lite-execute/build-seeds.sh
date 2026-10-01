#!/bin/bash
# build-seeds.sh <out-dir>: build the two seed repos the runner clones.
#   <out-dir>/seed-fresh     ledger repo, no export work yet (scenarios A and C)
#   <out-dir>/seed-stop-if   every route goes through json_middleware, and Task 1 is
#                            already committed (scenario B)
set -euo pipefail
here=$(cd "$(dirname "$0")" && pwd)
out=$1
rm -rf "$out/seed-fresh" "$out/seed-stop-if"
mkdir -p "$out"
commit() { git -C "$1" -c user.name=smoke -c user.email=smoke@example.invalid commit -qm "$2"; }

cp -R "$here/fixture/repo" "$out/seed-fresh"
git -C "$out/seed-fresh" init -q -b main
git -C "$out/seed-fresh" add -A
commit "$out/seed-fresh" "chore: seed ledger"

cp -R "$here/fixture/repo" "$out/seed-stop-if"
cp "$here/fixture/variants/api_stop_if.py" "$out/seed-stop-if/ledger/api.py"
git -C "$out/seed-stop-if" init -q -b main
git -C "$out/seed-stop-if" add -A
commit "$out/seed-stop-if" "chore: seed ledger"
cp "$here/fixture/variants/csv_export.py" "$out/seed-stop-if/ledger/"
cp "$here/fixture/variants/test_csv_export.py" "$out/seed-stop-if/tests/"
git -C "$out/seed-stop-if" add -A
commit "$out/seed-stop-if" "feat(export): add the CSV serializer"
echo "seeds in $out"
