"""The command: argument parsing and one function per verb."""

import argparse
import http.client
import json
import os
import subprocess
import sys
import time
import urllib.request
import webbrowser
from pathlib import Path

from pilot.store import Store, scaled
from pilot.validate import interaction_problems

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
POLL = 0.1
SERVER_START = 5
OPEN_TIMEOUT = 30
GRACE = 90
CLOSING = 5
SUSPEND_GAP = 10
WAIT_POLL = 1
WAIT_TIMEOUT = 540


def fail(message: str, code: int) -> int:
    print(message, file=sys.stderr)
    return code


def open_store(args: argparse.Namespace) -> Store | None:
    return Store(args.effort) if args.effort.is_dir() else None


def is_running(record: dict) -> bool:
    """True when the record's process exists and the server on its port answers with that pid."""
    try:
        os.kill(record["pid"], 0)
    except PermissionError:
        pass
    except OSError:
        return False
    ping = urllib.request.Request(f"http://127.0.0.1:{record['port']}/api/ping", headers={"X-Pilot-Token": record["token"]})
    try:
        with urllib.request.build_opener(urllib.request.ProxyHandler({})).open(ping, timeout=2) as reply:
            return reply.status == 200 and json.load(reply).get("pid") == record["pid"]
    except (OSError, ValueError, http.client.HTTPException):
        return False


def ensure_server(store: Store) -> dict:
    """Return the running server's record, starting the server first when none runs; exit 1 when it does not start."""
    record = store.record()
    if record and is_running(record):
        return record
    process = subprocess.Popen(
        [sys.executable, "-m", "pilot.server", str(store.effort.resolve())], cwd=PLUGIN_ROOT,
        stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True,
    )
    give_up = time.time() + SERVER_START
    while time.time() < give_up:
        record = store.record()
        if record and record["pid"] == process.pid:
            return record
        if process.poll() is not None:
            break
        time.sleep(scaled(POLL))
    sys.exit(fail("server did not start", 1))


def open_page(record: dict) -> None:
    """Open the page in a browser; whatever the launcher prints stays off stdout, which carries only the number."""
    sys.stdout.flush()
    saved = os.dup(1)
    with open(os.devnull, "w") as quiet:
        os.dup2(quiet.fileno(), 1)
        try:
            webbrowser.open(f"http://127.0.0.1:{record['port']}/?t={record['token']}")
        finally:
            os.dup2(saved, 1)
            os.close(saved)


def cmd_show(args: argparse.Namespace) -> int:
    store = open_store(args)
    if store is None:
        return fail(f"no such effort directory: {args.effort}", 2)
    try:
        interaction = json.loads(args.interaction.read_text())
    except OSError as error:
        return fail(f"cannot read {args.interaction}: {error.strerror}", 2)
    except ValueError:
        return fail(f"{args.interaction} is not valid JSON", 2)
    problems = interaction_problems(interaction, args.effort)
    if problems:
        return fail("\n".join(problems), 2)
    started = time.time()
    if interaction["kind"] == "readback":
        interaction = {**interaction, "version": store.keep_version(interaction["artifact"])}
    number = store.add_interaction(interaction)
    record = ensure_server(store)
    beat, bye = store.heartbeat()
    if beat and not bye and started - beat <= scaled(GRACE):
        print(number)
        return 0
    if not os.environ.get("CRANK_PILOT_NO_OPEN"):
        open_page(record)
    give_up = started + scaled(OPEN_TIMEOUT)
    while True:
        beat, bye = store.heartbeat()
        if beat >= started and not bye:
            print(number)
            return 0
        if time.time() >= give_up:
            return fail("page did not open", 4)
        time.sleep(scaled(POLL))


def cmd_wait(args: argparse.Namespace) -> int:
    store = open_store(args)
    if store is None:
        return fail(f"no such effort directory: {args.effort}", 2)
    start = grace_from = last_poll = time.time()
    while True:
        now = time.time()
        latest = store.latest()
        if latest is None:
            return fail("nothing pending", 2)
        if store.pending() is None:
            print(store.responses.resolve() / f"{latest:03d}.json")
            return 0
        if now - last_poll > scaled(SUSPEND_GAP):
            grace_from = now
        last_poll = now
        ensure_server(store)
        beat, bye = store.heartbeat()
        since = max(beat, grace_from)
        if (bye and now - since > scaled(CLOSING)) or now - since > scaled(GRACE):
            return fail("page closed", 4)
        if now - start >= scaled(args.timeout):
            return fail("still waiting", 3)
        time.sleep(scaled(WAIT_POLL))


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
    if store.record() is None:
        return 0
    return fail("closing a running server is not built yet", 1)


def parser() -> argparse.ArgumentParser:
    top = argparse.ArgumentParser(prog="crank-pilot")
    verbs = top.add_subparsers(dest="verb", required=True)
    show = verbs.add_parser("show", help="put an interaction on the page and wait for the page to open")
    show.add_argument("effort", type=Path)
    show.add_argument("interaction", type=Path)
    show.set_defaults(run=cmd_show)
    wait = verbs.add_parser("wait", help="block until the pending interaction is answered")
    wait.add_argument("effort", type=Path)
    wait.add_argument("--timeout", type=float, default=WAIT_TIMEOUT, help="seconds to wait before exiting 3")
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
