"""A minimal route table. Each handler returns a body or a Response."""
from __future__ import annotations

import json
from pathlib import Path

from ledger.csv_export import to_csv
from ledger.store import load_entries

ROUTES = {}
DATA_DIR = Path("data")


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


def export_csv(store_path=None, ledger=None):
    """Serve a ledger as a CSV download: the file at store_path, or the one named ledger in the data directory."""
    if ledger is not None:
        store_path = DATA_DIR / ledger
    return Response(
        to_csv(load_entries(store_path)),
        "text/csv",
        {"Content-Disposition": 'attachment; filename="export.csv"'},
    )
