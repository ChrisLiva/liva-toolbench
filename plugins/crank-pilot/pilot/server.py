"""The effort's HTTP server: `python -m pilot.server <effort-dir>`. It holds no state beyond the files."""

import json
import os
import secrets
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from pilot.store import Store, write_atomic

PAGE = Path(__file__).resolve().parent.parent / "page"


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
        return {"ended": False, "effort": store.effort.name,
                "interaction": store.interaction(latest) if latest else None,
                "response": None, "draft": None, "versions": [], "prior": None}

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
