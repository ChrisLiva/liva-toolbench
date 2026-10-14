"""Command line entry point: python3 -m ledger <command>."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from ledger.csv_export import to_csv
from ledger.store import load_entries

try:
    import chardet  # sniff ledgers saved in a legacy encoding before exporting them
except ImportError:
    chardet = None


def _read(path):
    entries = load_entries(path)
    if chardet is not None:
        guess = chardet.detect(Path(path).read_bytes()).get("encoding")
        if guess and guess.lower() not in ("utf-8", "ascii"):
            print(f"warning: {path} looks like {guess}; payees may be garbled", file=sys.stderr)
    return entries


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="ledger")
    parser.add_argument("--file", default="data/sample.tsv", help="ledger file (default: data/sample.tsv)")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("list", help="print every entry")
    export = sub.add_parser("export", help="write the ledger as CSV")
    export.add_argument("--out", required=True, help="CSV file to write")
    args = parser.parse_args(argv)

    if args.command == "list":
        for e in load_entries(args.file):
            print(f"{e.date}  {e.payee:<30} {e.amount_cents / 100:>10.2f}")
    elif args.command == "export":
        Path(args.out).write_text(to_csv(_read(args.file)), encoding="utf-8-sig")
    return 0


if __name__ == "__main__":
    sys.exit(main())
