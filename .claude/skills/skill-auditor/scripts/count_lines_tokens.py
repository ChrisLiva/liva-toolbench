#!/usr/bin/env python3
"""Count lines and tokens per file, against the skill-size budget.

agentskills.io recommends a SKILL.md stay under 500 lines and ~5,000 tokens —
that's the core-instruction layer loaded on *every* run, so it competes for the
model's attention. Reference files (references/, assets/, briefs) are loaded on
demand, so they're expected to be larger: this script reports them but only
*flags* SKILL.md files that bust the budget.

Usage:
    python count_lines_tokens.py SKILL.md references/RUBRIC.md   # explicit files
    python count_lines_tokens.py path/to/skill/                  # dir → recurse for *.md
    python count_lines_tokens.py --max-lines 500 --max-tokens 5000 <paths...>

Token counts use tiktoken (cl100k_base) when it's installed, otherwise a
chars/4 estimate, marked with '~' in the header. Exits non-zero if any SKILL.md
is over budget, so it can double as a validation gate.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path


def _token_counter():
    """Return (count_fn, exact). Prefer tiktoken; fall back to a chars/4 estimate."""
    try:
        import tiktoken

        enc = tiktoken.get_encoding("cl100k_base")
        return (lambda text: len(enc.encode(text)), True)
    except Exception:
        return (lambda text: round(len(text) / 4), False)


def iter_files(paths, ext):
    """Yield files: directories recurse for *<ext>, explicit files pass through."""
    for p in paths:
        path = Path(p)
        if path.is_dir():
            yield from sorted(path.rglob(f"*{ext}"))
        elif path.is_file():
            yield path
        else:
            print(f"warning: skipping {p!r} (not found)", file=sys.stderr)


def count_lines(text: str) -> int:
    if not text:
        return 0
    return text.count("\n") + (0 if text.endswith("\n") else 1)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        description="Count lines and tokens per file against the skill-size budget."
    )
    ap.add_argument("paths", nargs="+", help="Files or directories (dirs recurse for --ext).")
    ap.add_argument("--max-lines", type=int, default=500, help="SKILL.md line budget (default 500).")
    ap.add_argument("--max-tokens", type=int, default=5000, help="SKILL.md token budget (default 5000).")
    ap.add_argument("--ext", default=".md", help="Extension to glob inside directories (default .md).")
    args = ap.parse_args(argv)

    count_tokens, exact = _token_counter()
    files = list(iter_files(args.paths, args.ext))
    if not files:
        print("No files matched.", file=sys.stderr)
        return 1

    rows = []
    for f in files:
        text = f.read_text(encoding="utf-8", errors="replace")
        lines = count_lines(text)
        tokens = count_tokens(text)
        is_skill = f.name == "SKILL.md"
        over_lines = is_skill and lines > args.max_lines
        over_tokens = is_skill and tokens > args.max_tokens
        rows.append((f, lines, tokens, is_skill, over_lines, over_tokens))

    tok_label = "tokens" if exact else "tokens~"
    name_w = max(len("file"), *(len(str(f)) for f, *_ in rows))
    print(f"{'file':<{name_w}}  {'lines':>6}  {tok_label:>8}  flag")
    print(f"{'-' * name_w}  {'-' * 6}  {'-' * 8}  ----")

    any_over = False
    for f, lines, tokens, is_skill, over_lines, over_tokens in rows:
        if over_lines or over_tokens:
            parts = []
            if over_lines:
                parts.append(f">{args.max_lines}L")
            if over_tokens:
                parts.append(f">{args.max_tokens}T")
            flag = "OVER " + ",".join(parts)
            any_over = True
        else:
            flag = "" if is_skill else "ref"
        print(f"{str(f):<{name_w}}  {lines:>6}  {tokens:>8}  {flag}")

    print(
        f"\nBudget: SKILL.md ≤ {args.max_lines} lines, ≤ {args.max_tokens} tokens. "
        "Reference files load on demand and aren't flagged.",
        file=sys.stderr,
    )
    if not exact:
        print("Tokens are an estimate (chars/4); install tiktoken for exact counts.", file=sys.stderr)

    return 1 if any_over else 0


if __name__ == "__main__":
    raise SystemExit(main())
