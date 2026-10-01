"""A minimal route table. Every route passes through json_middleware."""
from __future__ import annotations

import json

from ledger.store import load_entries

ROUTES = {}


class Response:
    def __init__(self, body: str, content_type: str = "application/json", headers: dict | None = None):
        self.body = body
        self.content_type = content_type
        self.headers = dict(headers or {})


def json_middleware(response: Response) -> Response:
    """Shared by every route: the API speaks JSON, so this sets the content type on every response."""
    response.content_type = "application/json"
    response.headers["Content-Type"] = "application/json"
    return response


def route(path: str):
    def register(handler):
        def wrapped(*args, **kwargs):
            body = handler(*args, **kwargs)
            response = body if isinstance(body, Response) else Response(body)
            return json_middleware(response)

        ROUTES[path] = wrapped
        return handler

    return register


@route("/entries")
def entries(store_path):
    return json.dumps([e.__dict__ for e in load_entries(store_path)])
