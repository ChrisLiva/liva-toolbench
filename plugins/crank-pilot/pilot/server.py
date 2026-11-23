"""The effort's HTTP server: `python -m pilot.server <effort-dir>`. It keeps no session
state beyond the files."""

import contextlib
import hmac
import json
import os
import re
import secrets
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import NamedTuple, cast
from urllib.parse import unquote

from pilot.store import (
    Store,
    attachment_rel,
    image_extension,
    response_rel,
    scaled,
    version_rel,
    write_atomic,
)
from pilot.validate import inside, response_problems

PAGE = Path(__file__).resolve().parent.parent / "page"
WRITES = ("POST", "PUT", "DELETE")
OCTET_STREAM = "application/octet-stream"
EFFORT_TYPES = {
    ".md": "text/plain; charset=utf-8",
    ".html": "text/plain; charset=utf-8",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".gif": "image/gif",
    ".webp": "image/webp",
}
PAGE_TYPES = {
    ".html": "text/html; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".js": "text/javascript; charset=utf-8",
}


_NotJson = object()
_Refused = object()


class Route(NamedTuple):
    method: str
    pattern: re.Pattern
    handler: str
    public: bool = False
    cap: int | None = None
    raw: bool = False


TOKEN = re.compile(r"[0-9a-f]{64}")
ENDED = 5
IDLE = 30 * 60
MIN_TICK = 0.01
WATCH = 1
POLL = 0.5
JSON_CAP = 1 << 20
IMAGE_CAP = 10 << 20
DRAIN_LIMIT = 4 << 20
ROUTES = (
    Route("GET", re.compile(r"/"), "index", public=True),
    Route("GET", re.compile(r"/page/(?P<rel>.*)"), "page_file", public=True),
    Route("GET", re.compile(r"/api/file/(?P<rel>.*)"), "effort_file"),
    Route("GET", re.compile(r"/api/ping"), "ping"),
    Route("GET", re.compile(r"/api/state"), "poll"),
    Route("PUT", re.compile(r"/api/draft/(?P<n>\d{1,9})"), "put_draft", cap=JSON_CAP),
    Route(
        "POST",
        re.compile(r"/api/response/(?P<n>\d{1,9})"),
        "post_response",
        cap=JSON_CAP,
    ),
    Route("POST", re.compile(r"/api/bye"), "bye", public=True, cap=JSON_CAP),
    Route("POST", re.compile(r"/api/close"), "close", cap=JSON_CAP),
    Route("POST", re.compile(r"/api/code"), "new_code", cap=JSON_CAP),
    Route("POST", re.compile(r"/api/session"), "session", public=True, cap=JSON_CAP),
    Route(
        "POST",
        re.compile(r"/api/attachment/(?P<n>\d{1,9})"),
        "post_attachment",
        cap=IMAGE_CAP,
        raw=True,
    ),
    Route(
        "DELETE",
        re.compile(r"/api/attachment/(?P<n>\d{1,9})/(?P<k>\d{1,9})"),
        "delete_attachment",
    ),
)


def modified(path: Path) -> float:
    """When `path` was last written, or 0 when it does not exist."""
    try:
        return path.stat().st_mtime
    except OSError:
        return 0.0


class Server(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, store: Store, token: str, port: int = 0) -> None:
        super().__init__(("127.0.0.1", port), Handler)
        self.store = store
        self.token = token
        self.closing_until: float | None = None
        self._closing_lock = threading.Lock()
        self.codes: set[str] = set()
        self._codes_lock = threading.Lock()

    def start_closing(self) -> None:
        """Open the `ended` window once; a second call leaves it as it was."""
        with self._closing_lock:
            if self.closing_until is None:
                self.closing_until = time.time() + scaled(ENDED)

    def add_code(self) -> str:
        """A new single-use code the page may exchange for the token."""
        code = secrets.token_hex(16)
        with self._codes_lock:
            self.codes.add(code)
        return code

    def take_code(self, code: object) -> bool:
        """True and the code is spent when it is a live code; two callers with one code
        never both get True."""
        with self._codes_lock:
            if isinstance(code, str) and code in self.codes:
                self.codes.remove(code)
                return True
            return False

    def watch(self) -> None:
        """Stop serving when the `ended` window has passed (after removing the heartbeat
        and the record), or when the record is gone or names another process or nothing
        has touched `heartbeat` or `contact` for 30 scaled minutes (leaving it as it
        is)."""
        started = time.time()
        while True:
            time.sleep(max(scaled(WATCH), MIN_TICK))
            record = self.store.record()
            if record is None or record["pid"] != os.getpid():
                return self.shutdown()
            touched = (self.store.heartbeat()[0], modified(self.store.contact))
            if time.time() - max(started, *touched) > scaled(IDLE):
                return self.shutdown()
            if self.closing_until is not None and time.time() >= self.closing_until:
                self.store.heartbeat_file.unlink(missing_ok=True)
                self.store.server_json.unlink(missing_ok=True)
                return self.shutdown()


class Handler(BaseHTTPRequestHandler):
    @property
    def pilot(self) -> Server:
        return cast(Server, self.server)

    def reply(self, status: int, body: bytes, content_type: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def reply_json(self, status: int, payload: object) -> None:
        self.reply(status, json.dumps(payload).encode(), "application/json")

    def has_token(self) -> bool:
        return hmac.compare_digest(
            self.headers.get("X-Pilot-Token", "").encode(), self.pilot.token.encode()
        )

    def state(self) -> dict:
        store = self.pilot.store
        latest = store.latest()
        response = store.response(latest) if latest else None
        draft = store.draft(latest) if latest and response is None else None
        interaction = store.interaction(latest) if latest else None
        readback = interaction is not None and interaction["kind"] == "readback"
        versions = []
        if readback:
            artifact = cast(dict, interaction)["artifact"]
            versions = [
                {"n": n, "file": version_rel(artifact, n)}
                for n in store.kept_versions(artifact)
            ]
        return {
            "ended": self.pilot.closing_until is not None,
            "effort": store.effort.name,
            "interaction": interaction,
            "response": {"via": response["via"]} if response else None,
            "draft": draft,
            "versions": versions,
            "prior": store.prior(cast(int, latest)) if readback else None,
        }

    def require_pending(self, n: int) -> bool:
        """True when `n` is the pending interaction; otherwise answer 409 and return
        False."""
        if self.pilot.store.pending() == n:
            return True
        self.reply_json(409, {"error": "that interaction is not pending"})
        return False

    def read_body(self, cap: int) -> bytes | object:
        """The request body bytes, or `_Refused` after answering a refusal: 411 with no
        `Content-Length`, 400 when it is not a plain number of at most 15 digits, 413
        over `cap`, all on the header alone. A 413's body is discarded after the reply,
        up to `DRAIN_LIMIT`, so a client still sending reads the 413 instead of a reset.
        A body the client cut short is dropped without a reply."""
        length = self.headers.get("Content-Length")
        if length is None:
            self.reply_json(411, {"error": "length required"})
        elif not re.fullmatch(r"[0-9]{1,15}", length):
            self.reply_json(400, {"error": "bad content-length"})
        elif int(length) > cap:
            self.reply_json(413, {"error": "body too large"})
            self.rfile.read(min(int(length), DRAIN_LIMIT))
        else:
            body = self.rfile.read(int(length))
            if len(body) == int(length):
                return body
            self.close_connection = True
        return _Refused

    def home(self) -> tuple[str, str]:
        port = self.pilot.server_address[1]
        return f"127.0.0.1:{port}", f"localhost:{port}"

    def foreign(self) -> bool:
        """Whether the Host names another server, or a write comes from another
        origin."""
        if self.headers.get("Host") not in self.home():
            return True
        origin = self.headers.get("Origin")
        return (
            self.command in WRITES
            and origin is not None
            # aislop-ignore-next-line ai-slop/hardcoded-url -- loopback Origin check
            and origin not in map("http://{}".format, self.home())
        )

    def find_route(self) -> tuple[Route, re.Match] | None:
        """The route and match for this request, or None after answering 404 for a
        path no route has and 405 for a path with another method."""
        path = self.path.partition("?")[0]
        matches = [
            (route, match)
            for route in ROUTES
            if (match := route.pattern.fullmatch(path))
        ]
        found = next(
            (
                (route, match)
                for route, match in matches
                if route.method == self.command
            ),
            None,
        )
        if not found:
            self.reply_json(
                405 if matches else 404,
                {"error": "not allowed" if matches else "not found"},
            )
        return found

    def read_json(self, route: Route) -> object:
        """The request body for `route`: `_Refused` after answering a refusal,
        `_NotJson` for a JSON route whose body does not parse, else the bytes or the
        parsed JSON."""
        body = self.read_body(cast(int, route.cap))
        if body is _Refused or route.raw:
            return body
        try:
            return json.loads(cast(bytes, body))
        except ValueError:
            return _NotJson

    def dispatch(self) -> None:
        if self.foreign():
            return self.reply_json(403, {"error": "forbidden"})
        if (found := self.find_route()) is None:
            return
        route, match = found
        if not (route.public or self.has_token()):
            return self.reply_json(403, {"error": "forbidden"})
        body = None
        if route.cap is not None and (body := self.read_json(route)) is _Refused:
            return
        getattr(self, route.handler)(match, body)

    do_GET = do_PUT = do_POST = do_DELETE = dispatch

    def index(self, match: re.Match, body: object) -> None:
        self.reply(200, (PAGE / "index.html").read_bytes(), "text/html; charset=utf-8")

    def page_file(self, match: re.Match, body: object) -> None:
        self.serve_file(PAGE, match["rel"], PAGE_TYPES)

    def effort_file(self, match: re.Match, body: object) -> None:
        self.serve_file(self.pilot.store.effort, match["rel"], EFFORT_TYPES)

    def ping(self, match: re.Match, body: object) -> None:
        write_atomic(self.pilot.store.contact, b"")
        closing = {"closing": True} if self.pilot.closing_until is not None else {}
        self.reply_json(200, {"pid": os.getpid(), **closing})

    def poll(self, match: re.Match, body: object) -> None:
        if self.pilot.closing_until is None:
            write_atomic(self.pilot.store.heartbeat_file, b"")
        self.reply_json(200, self.state())

    def bye(self, match: re.Match, body: object) -> None:
        write_atomic(self.pilot.store.heartbeat_file, b"bye")
        self.reply(204, b"", "application/json")

    def close(self, match: re.Match, body: object) -> None:
        self.pilot.start_closing()
        self.reply(202, b"", "application/json")

    def new_code(self, match: re.Match, body: object) -> None:
        self.reply_json(201, {"code": self.pilot.add_code()})

    def session(self, match: re.Match, body: object) -> None:
        if isinstance(body, dict) and self.pilot.take_code(body.get("code")):
            return self.reply_json(200, {"token": self.pilot.token})
        self.reply_json(403, {"error": "forbidden"})

    def put_draft(self, match: re.Match, body: object) -> None:
        n = int(match["n"])
        if not self.require_pending(n):
            return
        if not isinstance(body, dict):
            return self.reply_json(400, {"problems": ["draft: must be a JSON object"]})
        self.pilot.store.write_draft(n, body)
        self.reply(204, b"", "application/json")

    def post_response(self, match: re.Match, body: object) -> None:
        n = int(match["n"])
        if not self.require_pending(n):
            return
        store = self.pilot.store
        interaction = store.interaction(n)
        problems = (
            ["body: must be valid JSON"]
            if body is _NotJson
            else response_problems(interaction, body, store.effort)
        )
        if problems:
            return self.reply_json(400, {"problems": problems})
        if not store.respond(n, cast(dict, body), "page"):
            return self.reply_json(409, {"error": "that interaction is not pending"})
        self.reply_json(201, {"path": response_rel(n)})

    def post_attachment(self, match: re.Match, body: bytes) -> None:
        n = int(match["n"])
        if not self.require_pending(n):
            return
        extension = image_extension(body)
        if extension is None:
            return self.reply_json(
                415,
                {
                    "error": "unsupported image type: "
                    "accepted types are PNG, JPEG, GIF, WebP"
                },
            )
        k = self.pilot.store.add_attachment(n, body, extension)
        if k is None:
            return self.reply_json(
                409,
                {
                    "error": "ten images are already attached",
                    "code": "attachment_limit",
                },
            )
        self.reply_json(201, {"path": attachment_rel(n, k, extension)})

    def delete_attachment(self, match: re.Match, body: object) -> None:
        n = int(match["n"])
        if not self.require_pending(n):
            return
        if not self.pilot.store.remove_attachment(n, int(match["k"])):
            return self.reply_json(404, {"error": "no such attachment"})
        self.reply(204, b"", "application/json")

    def serve_file(self, root: Path, rel: str, types: dict[str, str]) -> None:
        target = inside(root, unquote(rel))
        if target is None:
            return self.reply_json(404, {"error": "not found"})
        self.reply(
            200, target.read_bytes(), types.get(target.suffix.lower(), OCTET_STREAM)
        )

    def log_message(self, format: str, *args: object) -> None:
        pass


def main(argv: list[str]) -> int:
    store = Store(Path(argv[1]))
    store.root.mkdir(parents=True, exist_ok=True)
    server = None
    if (
        (earlier := store.record())
        and 0 < earlier["port"] < 1 << 16
        and TOKEN.fullmatch(earlier["token"])
    ):
        with contextlib.suppress(OSError):
            server = Server(store, earlier["token"], earlier["port"])
    if server is None:
        store.heartbeat_file.unlink(missing_ok=True)
        server = Server(store, secrets.token_hex(32))
    record = {
        "pid": os.getpid(),
        "port": server.server_address[1],
        "token": server.token,
    }
    write_atomic(store.server_json, json.dumps(record).encode(), 0o600)
    threading.Thread(target=server.watch, daemon=True).start()
    server.serve_forever(poll_interval=max(scaled(POLL), MIN_TICK))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
