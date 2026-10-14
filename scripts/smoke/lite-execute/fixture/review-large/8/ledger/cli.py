"""Command line entry point: python3 -m ledger <command>."""
from __future__ import annotations

import argparse
import sys

from ledger.importer import merge_statement
from ledger.money import format_cents
from ledger.statement import StatementError, read_statement
from ledger.store import Entry, LedgerLocked, ledger_lock, load_entries, save_entries

# sysexits.h: input data that is not in the expected format.
EX_DATAERR = 65
# sysexits.h: a temporary failure the user can retry.
EX_TEMPFAIL = 75


def _row(e: Entry) -> str:
    return f"{e.date}  {e.payee:<30} {format_cents(e.amount_cents):>12}  {e.category}".rstrip()


def _uncategorized(entries: list[Entry]) -> list[Entry]:
    return [e for e in entries if not e.category]


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="ledger")
    parser.add_argument("--file", default="data/sample.tsv", help="ledger file (default: data/sample.tsv)")
    sub = parser.add_subparsers(dest="command", required=True)
    lst = sub.add_parser("list", help="print every entry with its category")
    lst.add_argument("--uncategorized", action="store_true", help="print only the entries with no category")
    lst.add_argument("--category", help="print only the entries in this category, ignoring case")
    imp = sub.add_parser("import", help="add a bank statement's new rows to the ledger")
    imp.add_argument("statement", help="the bank's statement CSV export")
    imp.add_argument("--dry-run", action="store_true", help="print what the import would add, and change nothing")
    return parser


def _run(args: argparse.Namespace) -> int:
    if args.command == "list":
        entries = load_entries(args.file)
        if args.category:
            entries = [e for e in entries if e.category.casefold() == args.category.casefold()]
        for e in entries:
            print(_row(e))
    elif args.command == "import":
        rows = read_statement(args.statement)
        if args.dry_run:
            _, added, skipped = merge_statement(load_entries(args.file), rows)
            print(f"would add {added}, skip {skipped} already imported")
            return 0
        with ledger_lock(args.statement):
            merged, added, skipped = merge_statement(load_entries(args.file), rows)
            save_entries(args.file, merged)
        print(f"added {added}, skipped {skipped} already imported")
    return 0


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        return _run(args)
    except LedgerLocked as e:
        print(f"ledger is locked: {e}", file=sys.stderr)
        return EX_TEMPFAIL
    except StatementError as e:
        print(f"error: {e}", file=sys.stderr)
        return EX_DATAERR


if __name__ == "__main__":
    sys.exit(main())
