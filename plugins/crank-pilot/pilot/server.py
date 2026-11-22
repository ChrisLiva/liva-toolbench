"""The effort's HTTP server: `python -m pilot.server <effort-dir>`. It holds no state beyond the files."""

import json
import os
import re
import secrets
import sys
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from pilot.store import Store, write_atomic
from pilot.validate import response_problems

PAGE = Path(__file__).resolve().parent.parent / "page"
INTERACTION_ROUTE = re.compile(r"/api/(?P<what>draft|response)/(?P<n>\d+)")


_NotJson = object()


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
        return secrets.compare_digest(self.headers.get("X-Pilot-Token", ""), self.server.token)

    def state(self) -> dict:
        store = self.server.store
        latest = store.latest()
        response = store.response(latest) if latest else None
        draft = store.draft(latest) if latest and response is None else None
        return {"ended": False, "effort": store.effort.name,
                "interaction": store.interaction(latest) if latest else None,
                "response": {"via": response["via"]} if response else None,
                "draft": draft, "versions": [], "prior": None}

    def require_pending(self, n: int) -> bool:
        """True when `n` is the pending interaction; otherwise answer 409 and return False."""
        if self.server.store.pending() == n:
            return True
        self.reply_json(409, {"error": "that interaction is not pending"})
        return False

    def read_json(self) -> object:
        """The request body parsed as JSON, or a problem line standing in for it when it is not."""
        raw = self.rfile.read(int(self.headers.get("Content-Length") or 0))
        try:
            return json.loads(raw)
        except ValueError:
            return _NotJson

    def do_PUT(self) -> None:
        self.write_route()

    def do_POST(self) -> None:
        self.write_route()

    def write_route(self) -> None:
        route = INTERACTION_ROUTE.fullmatch(self.path)
        if not route or route["what"] != {"PUT": "draft", "POST": "response"}.get(self.command):
            self.reply_json(404, {"error": "not found"})
        elif not self.has_token():
            self.reply_json(403, {"error": "forbidden"})
        else:
            body = self.read_json()
            n = int(route["n"])
            if self.require_pending(n):
                (self.put_draft if route["what"] == "draft" else self.post_response)(n, body)

    def put_draft(self, n: int, body: object) -> None:
        if not isinstance(body, dict):
            return self.reply_json(400, {"problems": ["draft: must be a JSON object"]})
        self.server.store.write_draft(n, body)
        self.reply(204, b"", "application/json")

    def post_response(self, n: int, body: object) -> None:
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

    def do_GET(self) -> None:
        if self.path == "/":
            self.reply(200, (PAGE / "index.html").read_bytes(), "text/html; charset=utf-8")
        elif self.path in ("/api/ping", "/api/state") and not self.has_token():
            self.reply_json(403, {"error": "forbidden"})
        elif self.path == "/api/ping":
            self.reply_json(200, {"pid": os.getpid()})
        elif self.path == "/api/state":
            write_atomic(self.server.store.heartbeat_file, b"")
            self.reply_json(200, self.state())
        else:
            self.reply_json(404, {"error": "not found"})

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
