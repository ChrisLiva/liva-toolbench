"""The effort's HTTP server: `python -m pilot.server <effort-dir>`. It holds no state beyond the files."""

import hmac
import json
import os
import re
import secrets
import sys
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import NamedTuple
from urllib.parse import unquote

from pilot.store import Store, image_extension, write_atomic
from pilot.validate import inside, response_problems

PAGE = Path(__file__).resolve().parent.parent / "page"
WRITES = ("POST", "PUT", "DELETE")
OCTET_STREAM = "application/octet-stream"
EFFORT_TYPES = {".md": "text/plain; charset=utf-8", ".html": "text/plain; charset=utf-8", ".png": "image/png",
                ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".gif": "image/gif", ".webp": "image/webp"}
PAGE_TYPES = {".html": "text/html; charset=utf-8", ".css": "text/css; charset=utf-8",
              ".js": "text/javascript; charset=utf-8"}


_NotJson = object()
_Refused = object()


class Route(NamedTuple):
    method: str
    pattern: re.Pattern
    handler: str
    public: bool = False
    cap: int | None = None
    raw: bool = False

JSON_CAP = 1 << 20
IMAGE_CAP = 10 << 20
DRAIN_LIMIT = 4 << 20
ROUTES = (
    Route("GET", re.compile(r"/"), "index", public=True),
    Route("GET", re.compile(r"/page/(?P<rel>.*)"), "page_file", public=True),
    Route("GET", re.compile(r"/api/file/(?P<rel>.*)"), "effort_file"),
    Route("GET", re.compile(r"/api/ping"), "ping"),
    Route("GET", re.compile(r"/api/state"), "poll"),
    Route("PUT", re.compile(r"/api/draft/(?P<n>\d+)"), "put_draft", cap=JSON_CAP),
    Route("POST", re.compile(r"/api/response/(?P<n>\d+)"), "post_response", cap=JSON_CAP),
    Route("POST", re.compile(r"/api/bye"), "bye", public=True, cap=JSON_CAP),
    Route("POST", re.compile(r"/api/attachment/(?P<n>\d+)"), "post_attachment", cap=IMAGE_CAP, raw=True),
    Route("DELETE", re.compile(r"/api/attachment/(?P<n>\d+)/(?P<k>\d+)"), "delete_attachment"),
)


class Server(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, store: Store, token: str) -> None:
        super().__init__(("127.0.0.1", 0), Handler)
        self.store = store
        self.token = token


class Handler(BaseHTTPRequestHandler):
    server: Server

    def reply(self, status: int, body: bytes, content_type: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def reply_json(self, status: int, payload: object) -> None:
        self.reply(status, json.dumps(payload).encode(), "application/json")

    def has_token(self) -> bool:
        return hmac.compare_digest(self.headers.get("X-Pilot-Token", "").encode(), self.server.token.encode())

    def state(self) -> dict:
        store = self.server.store
        latest = store.latest()
        response = store.response(latest) if latest else None
        draft = store.draft(latest) if latest and response is None else None
        interaction = store.interaction(latest) if latest else None
        readback = interaction is not None and interaction["kind"] == "readback"
        return {"ended": False, "effort": store.effort.name, "interaction": interaction,
                "response": {"via": response["via"]} if response else None, "draft": draft,
                "versions": store.kept_versions(interaction["artifact"]) if readback else [],
                "prior": store.prior(latest) if readback else None}

    def require_pending(self, n: int) -> bool:
        """True when `n` is the pending interaction; otherwise answer 409 and return False."""
        if self.server.store.pending() == n:
            return True
        self.reply_json(409, {"error": "that interaction is not pending"})
        return False

    def read_body(self, cap: int) -> bytes | object:
        """The request body bytes, or `_Refused` after answering a refusal: 411 with no `Content-Length`, 400 when it
        is not a plain number of at most 15 digits, 413 over `cap`, all on the header alone. A 413's body is discarded
        after the reply, up to `DRAIN_LIMIT`, so a client still sending reads the 413 instead of a reset. A body the
        client cut short is dropped without a reply."""
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
        """The two `Host` values this server answers to."""
        port = self.server.server_address[1]
        return f"127.0.0.1:{port}", f"localhost:{port}"

    def dispatch(self) -> None:
        """Every request's one path: Host, Origin on a write, the route, the token, then the body."""
        if self.headers.get("Host") not in self.home():
            return self.reply_json(403, {"error": "forbidden"})
        origin = self.headers.get("Origin")
        if self.command in WRITES and origin is not None and origin not in map("http://{}".format, self.home()):
            return self.reply_json(403, {"error": "forbidden"})
        path = self.path.partition("?")[0]
        matches = [(route, match) for route in ROUTES if (match := route.pattern.fullmatch(path))]
        found = next(((route, match) for route, match in matches if route.method == self.command), None)
        if not found:
            return self.reply_json(405 if matches else 404, {"error": "not allowed" if matches else "not found"})
        route, match = found
        if not (route.public or self.has_token()):
            return self.reply_json(403, {"error": "forbidden"})
        body = None
        if route.cap is not None:
            if (body := self.read_body(route.cap)) is _Refused:
                return
            if not route.raw:
                try:
                    body = json.loads(body)
                except ValueError:
                    body = _NotJson
        getattr(self, route.handler)(match, body)

    do_GET = do_PUT = do_POST = do_DELETE = dispatch

    def index(self, match: re.Match, body: object) -> None:
        self.reply(200, (PAGE / "index.html").read_bytes(), "text/html; charset=utf-8")

    def page_file(self, match: re.Match, body: object) -> None:
        self.serve_file(PAGE, match["rel"], PAGE_TYPES)

    def effort_file(self, match: re.Match, body: object) -> None:
        self.serve_file(self.server.store.effort, match["rel"], EFFORT_TYPES)

    def ping(self, match: re.Match, body: object) -> None:
        write_atomic(self.server.store.contact, b"")
        self.reply_json(200, {"pid": os.getpid()})

    def poll(self, match: re.Match, body: object) -> None:
        write_atomic(self.server.store.heartbeat_file, b"")
        self.reply_json(200, self.state())

    def bye(self, match: re.Match, body: object) -> None:
        write_atomic(self.server.store.heartbeat_file, b"bye")
        self.reply(204, b"", "application/json")

    def put_draft(self, match: re.Match, body: object) -> None:
        n = int(match["n"])
        if not self.require_pending(n):
            return
        if not isinstance(body, dict):
            return self.reply_json(400, {"problems": ["draft: must be a JSON object"]})
        self.server.store.write_draft(n, body)
        self.reply(204, b"", "application/json")

    def post_response(self, match: re.Match, body: object) -> None:
        n = int(match["n"])
        if not self.require_pending(n):
            return
        store = self.server.store
        interaction = store.interaction(n)
        problems = ["body: must be valid JSON"] if body is _NotJson else response_problems(interaction, body, store.effort)
        if problems:
            return self.reply_json(400, {"problems": problems})
        saved = {**body, "interaction": n, "kind": interaction["kind"], "via": "page",
                 "submitted_at": datetime.now(timezone.utc).isoformat()}
        if not store.write_response(n, saved):
            return self.reply_json(409, {"error": "that interaction is not pending"})
        self.reply_json(201, {"path": f"pilot/responses/{n:03d}.json"})

    def post_attachment(self, match: re.Match, body: bytes) -> None:
        n = int(match["n"])
        if not self.require_pending(n):
            return
        extension = image_extension(body)
        if extension is None:
            return self.reply_json(415, {"error": "unsupported image type: accepted types are PNG, JPEG, GIF, WebP"})
        k = self.server.store.add_attachment(n, body, extension)
        if k is None:
            return self.reply_json(409, {"error": "ten images are already attached"})
        self.reply_json(201, {"path": f"pilot/attachments/{n:03d}-{k}.{extension}", "k": k})

    def delete_attachment(self, match: re.Match, body: object) -> None:
        n = int(match["n"])
        if not self.require_pending(n):
            return
        if not self.server.store.remove_attachment(n, int(match["k"])):
            return self.reply_json(404, {"error": "no such attachment"})
        self.reply(204, b"", "application/json")

    def serve_file(self, root: Path, rel: str, types: dict[str, str]) -> None:
        """Answer with the file `rel` names inside `root`, or 404 when `inside` refuses it."""
        target = inside(root, unquote(rel))
        if target is None:
            return self.reply_json(404, {"error": "not found"})
        self.reply(200, target.read_bytes(), types.get(target.suffix.lower(), OCTET_STREAM))

    def log_message(self, format: str, *args: object) -> None:
        pass


def main(argv: list[str]) -> int:
    store = Store(Path(argv[1]))
    server = Server(store, secrets.token_hex(32))
    store.root.mkdir(parents=True, exist_ok=True)
    record = {"pid": os.getpid(), "port": server.server_address[1], "token": server.token}
    write_atomic(store.server_json, json.dumps(record).encode(), 0o600)
    server.serve_forever()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
