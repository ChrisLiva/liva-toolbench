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

from pilot.store import Store, response_rel, scaled
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


def open_store(args: argparse.Namespace) -> Store:
    """The store of the effort directory the command names; exit 2 when it is not a
    directory."""
    if not args.effort.is_dir():
        sys.exit(fail(f"no such effort directory: {args.effort}", 2))
    return Store(args.effort)


def call(
    record: dict, path: str, method: str = "GET", data: bytes | None = None
) -> bytes:
    """The body of the reply the server on the record's port gives `path`; raises
    `OSError` or `HTTPException` when it fails."""
    request = urllib.request.Request(
        f"http://127.0.0.1:{record['port']}{path}",
        data=data,
        method=method,
        headers={"X-Pilot-Token": record["token"]},
    )
    with urllib.request.build_opener(urllib.request.ProxyHandler({})).open(
        request, timeout=2
    ) as reply:
        return reply.read()


def ping(record: dict) -> dict | None:
    """The reply of the server on the record's port when it is the record's process,
    else None. A pid that `os.kill` refuses belongs to another user, so it is never this
    effort's server."""
    try:
        os.kill(record["pid"], 0)
    except OSError:
        return None
    try:
        answer = json.loads(call(record, "/api/ping"))
    except (OSError, ValueError, http.client.HTTPException):
        return None
    return (
        answer
        if isinstance(answer, dict) and answer.get("pid") == record["pid"]
        else None
    )


def ensure_server(store: Store) -> dict:
    """Return the running server's record, starting the server first when none runs;
    exit 1 when it does not start. A server in its closing window counts as gone: wait
    for its record to be removed, then start a new one."""
    while (record := store.record()) is not None:
        answer = ping(record)
        if answer is None:
            break
        if not answer.get("closing"):
            return record
        time.sleep(scaled(WAIT_POLL))
    process = subprocess.Popen(  # noqa: S603  starts this package's own server module
        [sys.executable, "-m", "pilot.server", str(store.effort.resolve())],
        cwd=PLUGIN_ROOT,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
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
    """Open the page in a browser with a one-time code in the URL, not the token;
    whatever the launcher prints stays off stdout, which carries only the number. Opens
    nothing when the server gives no code."""
    try:
        code = json.loads(call(record, "/api/code", "POST", b"{}"))["code"]
    except (OSError, http.client.HTTPException):
        return
    sys.stdout.flush()
    saved = os.dup(1)
    with open(os.devnull, "w") as quiet:
        os.dup2(quiet.fileno(), 1)
        try:
            webbrowser.open(f"http://127.0.0.1:{record['port']}/?c={code}")
        finally:
            os.dup2(saved, 1)
            os.close(saved)


def settle(store: Store, number: int, via: str) -> bool:
    """Close interaction `number` with a response that carries no answers; False when a
    response already exists."""
    return store.respond(number, {}, via)


def cmd_show(args: argparse.Namespace) -> int:
    store = open_store(args)
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
        interaction = {
            **interaction,
            "version": store.keep_version(interaction["artifact"]),
        }
    if (earlier := store.pending()) is not None:
        settle(store, earlier, "superseded")
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
    start = grace_from = last_poll = time.time()
    while True:
        now = time.time()
        latest = store.latest()
        if latest is None:
            return fail("nothing pending", 2)
        if store.pending() is None:
            print((store.effort / response_rel(latest)).resolve())
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
    pending = store.pending()
    if pending is None or not settle(store, pending, "chat"):
        return fail("nothing pending", 2)
    return 0


def cmd_close(args: argparse.Namespace) -> int:
    store = open_store(args)
    record = store.record()
    if record is None:
        return 0
    if ping(record) is None:
        store.server_json.unlink(missing_ok=True)
        return 0
    try:
        call(record, "/api/close", "POST", b"")
        return 0
    except (OSError, http.client.HTTPException):
        return fail("could not close the server", 1)


def parser() -> argparse.ArgumentParser:
    top = argparse.ArgumentParser(prog="crank-pilot")
    verbs = top.add_subparsers(dest="verb", required=True)
    show = verbs.add_parser(
        "show", help="put an interaction on the page and wait for the page to open"
    )
    show.add_argument("effort", type=Path)
    show.add_argument("interaction", type=Path)
    show.set_defaults(run=cmd_show)
    wait = verbs.add_parser(
        "wait", help="block until the pending interaction is answered"
    )
    wait.add_argument("effort", type=Path)
    wait.add_argument(
        "--timeout",
        type=float,
        default=WAIT_TIMEOUT,
        help="seconds to wait before exiting 3",
    )
    wait.set_defaults(run=cmd_wait)
    resolve = verbs.add_parser("resolve", help="settle the pending interaction")
    resolve.add_argument("effort", type=Path)
    resolve.add_argument(
        "--chat", action="store_true", required=True, help="the user answered in chat"
    )
    resolve.set_defaults(run=cmd_resolve)
    close = verbs.add_parser("close", help="stop the effort's server")
    close.add_argument("effort", type=Path)
    close.set_defaults(run=cmd_close)
    return top


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    return args.run(args)
