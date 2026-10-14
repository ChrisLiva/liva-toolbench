"""Command line entry point: python3 -m ledger <command>."""
from __future__ import annotations

import argparse
import sys

from ledger.store import LedgerLocked, load_entries

# sysexits.h: a temporary failure the user can retry.
EX_TEMPFAIL = 75


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="ledger")
    parser.add_argument("--file", default="data/sample.tsv", help="ledger file (default: data/sample.tsv)")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("list", help="print every entry")
    return parser


def _run(args: argparse.Namespace) -> int:
    if args.command == "list":
        for e in load_entries(args.file):
            print(f"{e.date}  {e.payee:<30} {e.amount_cents / 100:>10.2f}")
    return 0


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        return _run(args)
    except LedgerLocked as e:
        print(f"ledger is locked: {e}", file=sys.stderr)
        return EX_TEMPFAIL


if __name__ == "__main__":
    sys.exit(main())
