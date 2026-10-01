"""Command line entry point: python3 -m ledger <command>."""
from __future__ import annotations

import argparse
import sys

from ledger.store import load_entries


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="ledger")
    parser.add_argument("--file", default="data/sample.tsv", help="ledger file (default: data/sample.tsv)")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("list", help="print every entry")
    args = parser.parse_args(argv)

    if args.command == "list":
        for e in load_entries(args.file):
            print(f"{e.date}  {e.payee:<30} {e.amount_cents / 100:>10.2f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
