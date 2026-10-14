"""A minimal route table. Each handler returns a body or a Response."""
from __future__ import annotations

import json
from pathlib import Path

from ledger.report import load_budgets, monthly_report
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
def entries(store_path, category=None):
    """Every entry as JSON, or only the entries in category when the request names one."""
    found = load_entries(store_path)
    if category is not None:
        found = [e for e in found if e.category == category]
    return json.dumps([e.__dict__ for e in found])


@route("/report")
def report(store_path, month):
    """The month's spending against each budget in budgets.tsv beside the ledger, amounts in integer cents."""
    limits = load_budgets(Path(store_path).with_name("budgets.tsv"))
    lines = monthly_report(load_entries(store_path), limits, month)
    return json.dumps({"month": month, "budgets": [
        {"category": l.category, "spent_cents": l.spent_cents, "limit_cents": l.limit_cents, "over": l.over}
        for l in lines]})
