#!/usr/bin/env bash
# Partition a repo into projects and say which analyzers each one already owns.
# Read-only: git ls-files plus file reads. Prints plain text, one section per project.
#
#   scripts/detect.sh [repo-root] [project-dir …]   (project dirs limit the per-project sections)
#
# A project is a directory holding package.json / pyproject.toml / *.csproj / *.sln / go.mod.
# Every tracked source file belongs to its nearest project; a candidate that keeps no source
# of its own is a workspace shell and is reported as such. Vendored and generated trees are
# left out the way git already leaves out ignored files.
set -euo pipefail
trap "" PIPE
root="${1:-.}"
shift $(( $# > 0 ? 1 : 0 ))
only=("$@")
cd "$root"
git rev-parse --is-inside-work-tree >/dev/null 2>&1 || { echo "not a git repo: $root" >&2; exit 2; }

files=$(git ls-files -z --cached --others --exclude-standard \
  | tr '\0' '\n' \
  | grep -v -E '(^|/)(node_modules|vendor|dist|build|bin|obj|\.venv|venv|__pycache__|coverage|\.git)/' \
  | grep -v -E '(^|/)\.[^/]+/' ; true)
gh=$(git ls-files --cached --others --exclude-standard | grep -E '(^|/)\.github/' ; true)
files=$(printf '%s\n%s\n' "$files" "$gh" | sed '/^$/d' | sort -u)

# --- candidate project directories -------------------------------------------------------------
manifests=$(printf '%s\n' "$files" | grep -E '(^|/)(package\.json|pyproject\.toml|go\.mod|[^/]+\.csproj|[^/]+\.sln)$' ; true)
dirs=$(printf '%s\n' "$manifests" | sed -E 's#(^|/)[^/]+$#\1#; s#/$##; s#^$#.#' | sort -u)
[ -z "$dirs" ] && dirs="."

lang_of() {
  case "$1" in
    *.ts|*.tsx|*.mts|*.cts|*.js|*.jsx|*.mjs|*.cjs) echo js-ts ;;
    *.py|*.pyi) echo python ;;
    *.cs) echo csharp ;;
    *.go) echo go ;;
    *.css) echo css ;;
    *.graphql|*.gql) echo graphql ;;
    *) echo other ;;
  esac
}

nearest() { # nearest candidate dir for a file path
  local f="$1" best="." d
  while read -r d; do
    [ "$d" = "." ] && continue
    case "$f" in "$d"/*) [ ${#d} -gt ${#best} ] && best="$d" ;; esac
  done <<<"$dirs"
  echo "$best"
}

# --- assign files, count lines ------------------------------------------------------------------
tmp=$(mktemp)
while IFS= read -r f; do
  [ -f "$f" ] || continue
  l=$(lang_of "$f"); [ "$l" = other ] && continue
  n=$(wc -l <"$f" | tr -d ' ')
  printf '%s\t%s\t%s\t%s\n' "$(nearest "$f")" "$l" "$n" "$f"
done <<<"$files" >"$tmp"

echo "repo: $(pwd)"
echo "head: $(git rev-parse --short HEAD 2>/dev/null || echo none)"
echo "dirty: $(git status --porcelain | wc -l | tr -d ' ') paths"
echo

owns() { # owns <dir> <glob...>  — a config in the dir or any ancestor owns the tool
  local d="$1"; shift
  local p
  while :; do
    for p in "$@"; do
      # shellcheck disable=SC2086
      m=$(ls -d "$d"/$p 2>/dev/null | head -1) && [ -n "$m" ] && { echo "$m"; return 0; }
    done
    [ "$d" = "." ] && return 1
    d=$(dirname "$d")
  done
}
dep() { # dep <dir> <name>: package.json dependency in dir or ancestors
  local d="$1" n="$2"
  while :; do
    [ -f "$d/package.json" ] && grep -Eq "\"$n\"[[:space:]]*:" "$d/package.json" && { echo "$d/package.json"; return 0; }
    [ "$d" = "." ] && return 1
    d=$(dirname "$d")
  done
}
pytool() { # pytool <dir> <section>: [tool.<section>] in pyproject.toml, dir or ancestors
  local d="$1" s="$2"
  while :; do
    [ -f "$d/pyproject.toml" ] && grep -Eq "^\[tool\.$s([.\]]|$)" "$d/pyproject.toml" && { echo "$d/pyproject.toml [tool.$s]"; return 0; }
    [ "$d" = "." ] && return 1
    d=$(dirname "$d")
  done
}
report() { printf '  %-14s %s\n' "$1" "${2:-(none)}"; }

while read -r d; do
  if [ ${#only[@]} -gt 0 ]; then keep=0; for o in "${only[@]}"; do [ "${o%/}" = "$d" ] && keep=1; done; [ $keep -eq 1 ] || continue; fi
  total=$(awk -F'\t' -v d="$d" '$1==d{s+=$3} END{print s+0}' "$tmp")
  nfiles=$(awk -F'\t' -v d="$d" '$1==d && $2!="css" && $2!="graphql"{c++} END{print c+0}' "$tmp")
  echo "## project $d"
  if [ "$nfiles" -eq 0 ]; then echo "  workspace shell: no source of its own"; echo; continue; fi
  echo "  manifests: $(printf '%s\n' "$manifests" | awk -v d="$d" '{p=$0; sub(/(^|\/)[^\/]+$/,"",p); if(p=="")p="."; if(p==d)printf "%s ", $0}')"
  awk -F'\t' -v d="$d" '$1==d && $2!="css" && $2!="graphql"{l[$2]+=$3; c[$2]++} END{for(k in l) printf "  %-8s %6d files %8d lines (%.1f KLOC)\n", k, c[k], l[k], l[k]/1000}' "$tmp" | sort
  report "lint assets" "$(awk -F'\t' -v d="$d" '$1==d && ($2=="css"||$2=="graphql"){l[$2]+=$3; c[$2]++} END{for(k in l) printf "%s %d files %d lines (%.1f KLOC); ", k, c[k], l[k], l[k]/1000}' "$tmp" | sed 's/; $//')"
  echo "  owned tools:"
  langs=$(awk -F'\t' -v d="$d" '$1==d && $2!="css" && $2!="graphql"{print $2}' "$tmp" | sort -u)
  if grep -q js-ts <<<"$langs"; then
    report tsc        "$(ls "$d"/tsconfig*.json 2>/dev/null | head -1 || true)"
    report eslint     "$(owns "$d" 'eslint.config.*' '.eslintrc*' || dep "$d" eslint || true)"
    report biome      "$(owns "$d" 'biome.json' 'biome.jsonc' || dep "$d" @biomejs/biome || true)"
    report oxlint     "$(owns "$d" '.oxlintrc.json' 'oxlint.config.*' || dep "$d" oxlint || true)"
    report prettier   "$(owns "$d" '.prettierrc*' 'prettier.config.*' || dep "$d" prettier || true)"
    report knip       "$(owns "$d" 'knip.json' 'knip.jsonc' 'knip.ts' 'knip.config.*' || dep "$d" knip || true)"
    report fallow     "$(owns "$d" 'fallow.config.*' '.fallowrc*' || dep "$d" fallow || true)"
    report stryker    "$(owns "$d" 'stryker.config.*' 'stryker.conf.*' || dep "$d" @stryker-mutator/core || true)"
    report node_modules "$( [ -d "$d/node_modules" ] && echo "$d/node_modules" || (owns "$d" node_modules || true) )"
  fi
  if grep -q python <<<"$langs"; then
    report ruff       "$(pytool "$d" ruff || owns "$d" 'ruff.toml' '.ruff.toml' || true)"
    report mypy       "$(pytool "$d" mypy || owns "$d" 'mypy.ini' '.mypy.ini' 'setup.cfg' || true)"
    report pyright    "$(pytool "$d" pyright || owns "$d" 'pyrightconfig.json' || true)"
    report ty         "$(pytool "$d" ty || owns "$d" 'ty.toml' || true)"
    report vulture    "$(pytool "$d" vulture || true)"
    report bandit     "$(pytool "$d" bandit || owns "$d" '.bandit' 'bandit.yaml' 'bandit.yml' || true)"
    report cosmic-ray "$(owns "$d" 'cosmic-ray.toml' '*.cosmic-ray.toml' || true)"
    report venv       "$(owns "$d" '.venv' 'venv' || true)"
  fi
  if grep -q csharp <<<"$langs"; then
    report editorconfig "$(owns "$d" '.editorconfig' || true)"
    report stryker.net  "$(owns "$d" 'stryker-config.json' 'stryker-config.yaml' || true)"
    report dotnet-sdk   "$(command -v dotnet >/dev/null && dotnet --version 2>/dev/null || echo 'missing')"
  fi
  if grep -q go <<<"$langs"; then
    report golangci   "$(owns "$d" '.golangci.yml' '.golangci.yaml' '.golangci.toml' '.golangci.json' || true)"
    report gremlins   "$(owns "$d" '.gremlins.yaml' '.gremlins.yml' || true)"
    report go-toolchain "$(command -v go >/dev/null && go version 2>/dev/null || echo 'missing')"
  fi
  echo
done <<<"$dirs"

echo "## repo-wide"
report gitleaks    "$(command -v gitleaks >/dev/null && gitleaks version 2>/dev/null | head -1 || echo 'missing: brew install gitleaks')"
report opengrep    "$(command -v opengrep >/dev/null && opengrep --version 2>/dev/null | head -1 || echo 'missing: brew install opengrep')"
report osv-scanner "$(command -v osv-scanner >/dev/null && osv-scanner --version 2>/dev/null | head -1 || echo 'missing: brew install osv-scanner')"
report workflows   "$(printf '%s\n' "$files" | grep -cE '(^|/)\.github/workflows/[^/]+\.ya?ml$' || true) files"
report configs     "$(ls -d .gitleaks.toml zizmor.yml .zizmor.yml osv-scanner.toml .opengrep .semgrep .jscpd.json jscpd.json .aislop .aislopignore 2>/dev/null | tr '\n' ' ')"
report snapshots   "$(printf '%s\n' "$files" | grep -oE '(^|.*/)(captured|golden|__snapshots__|fixtures|testdata|snapshots)/' | sort -u | tr '\n' ' ')"
report lockfiles   "$(printf '%s\n' "$files" | grep -E '(^|/)(package-lock\.json|pnpm-lock\.yaml|yarn\.lock|uv\.lock|poetry\.lock|go\.sum|packages\.lock\.json)$' | tr '\n' ' ')"
report unassessed  "$(awk -F'\t' '{a[$4]=1} END{}' "$tmp"; printf '%s\n' "$files" | while IFS= read -r f; do [ -f "$f" ] && [ "$(lang_of "$f")" = other ] && echo "${f##*.}"; done | sort | uniq -c | sort -rn | head -8 | awk '{printf "%s:%s ", $2, $1}')"
rm -f "$tmp"
