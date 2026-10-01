"""A minimal route table. Each handler returns a body or a Response."""
from __future__ import annotations

import json

from ledger.store import load_entries

ROUTES = {}


class Response:
    def __init__(self, body: str, content_type: str = "application/json", headers: dict | None = None):
        self.body = body
        self.content_type = content_type
        self.headers = dict(headers or {})


def route(path: str, content_type: str = "application/json"):
    """Register a handler under path. A handler that returns a Response keeps its own content type."""

    def register(handler):
        def wrapped(*args, **kwargs):
            body = handler(*args, **kwargs)
            if isinstance(body, Response):
                return body
            return Response(body, content_type)

        ROUTES[path] = wrapped
        return handler

    return register


@route("/entries")
def entries(store_path):
    return json.dumps([e.__dict__ for e in load_entries(store_path)])
