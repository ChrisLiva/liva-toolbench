"""The command: argument parsing and one function per verb."""

import argparse
import sys
from pathlib import Path

from pilot.store import Store


def fail(message: str, code: int) -> int:
    print(message, file=sys.stderr)
    return code


def open_store(args: argparse.Namespace) -> Store | None:
    return Store(args.effort) if args.effort.is_dir() else None


def cmd_wait(args: argparse.Namespace) -> int:
    store = open_store(args)
    if store is None:
        return fail(f"no such effort directory: {args.effort}", 2)
    if store.pending() is None:
        return fail("nothing pending", 2)
    return fail("a pending interaction needs the server, which is not built yet", 1)


def cmd_resolve(args: argparse.Namespace) -> int:
    store = open_store(args)
    if store is None:
        return fail(f"no such effort directory: {args.effort}", 2)
    if store.pending() is None:
        return fail("nothing pending", 2)
    return fail("resolving a pending interaction is not built yet", 1)


def cmd_close(args: argparse.Namespace) -> int:
    store = open_store(args)
    if store is None:
        return fail(f"no such effort directory: {args.effort}", 2)
    if not store.server_json.exists():
        return 0
    return fail("closing a running server is not built yet", 1)


def parser() -> argparse.ArgumentParser:
    top = argparse.ArgumentParser(prog="crank-pilot")
    verbs = top.add_subparsers(dest="verb", required=True)
    wait = verbs.add_parser("wait", help="block until the pending interaction is answered")
    wait.add_argument("effort", type=Path)
    wait.set_defaults(run=cmd_wait)
    resolve = verbs.add_parser("resolve", help="settle the pending interaction")
    resolve.add_argument("effort", type=Path)
    resolve.add_argument("--chat", action="store_true", required=True, help="the user answered in chat")
    resolve.set_defaults(run=cmd_resolve)
    close = verbs.add_parser("close", help="stop the effort's server")
    close.add_argument("effort", type=Path)
    close.set_defaults(run=cmd_close)
    return top


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    return args.run(args)
