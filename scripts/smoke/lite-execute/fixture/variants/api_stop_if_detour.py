"""A minimal route table. Every route passes through json_middleware."""
from __future__ import annotations

import json

from ledger.store import load_entries

ROUTES = {}


class Response:
    def __init__(self, body: str, content_type: str = "application/json", headers: dict | None = None,
                 keep_content_type: bool = False):
        self.body = body
        self.content_type = content_type
        self.headers = dict(headers or {})
        self.keep_content_type = keep_content_type


def json_middleware(response: Response) -> Response:
    """Shared by every route: sets the JSON content type, except on a Response built with keep_content_type=True."""
    if not response.keep_content_type:
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


@route("/health")
def health(store_path):
    return Response("ok", content_type="text/plain", keep_content_type=True)
