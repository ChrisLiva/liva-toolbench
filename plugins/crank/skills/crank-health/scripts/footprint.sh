#!/usr/bin/env bash
# Zero-footprint gate. `snapshot` before the scan, `check` after: any path the scan created
# or changed in the target repo is printed and the exit code is 1.
#
#   scripts/footprint.sh snapshot <repo-root> <snapshot-file>
#   scripts/footprint.sh check    <repo-root> <snapshot-file>
set -euo pipefail
mode="$1"; root="$2"; snap="$3"
state() { (cd "$root" && git status --porcelain --untracked-files=all --ignored=no | sort); }
case "$mode" in
  snapshot) state >"$snap"; echo "snapshot: $(wc -l <"$snap" | tr -d ' ') dirty paths recorded" ;;
  check)
    diff=$(diff <(cat "$snap") <(state) | grep '^>' | sed 's/^> //' || true)
    if [ -n "$diff" ]; then
      echo "FOOTPRINT: the scan left these paths behind in $root:"; printf '  %s\n' "$diff"
      echo "Remove them (or gitignore them if the repo's own tool wrote them) before reporting."; exit 1
    fi
    echo "footprint: clean" ;;
  *) echo "usage: footprint.sh snapshot|check <repo-root> <snapshot-file>" >&2; exit 2 ;;
esac
