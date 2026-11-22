#!/usr/bin/env python3
"""pilot_client.py <effort-dir>: the page's side of crank-pilot for a headless run, answering what the server shows.

Every 0.5 s it reads <effort-dir>/pilot/server.json and polls GET /api/state with the token. When an interaction has
no response yet, it posts the response that accepts it: each question's recommended option, a readback approved, a
prototype's first variant. It runs until killed, so run.sh starts it before the first turn and kills it after the last.
"""
import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

INTERVAL = 0.5


def answer(question):
    return {"id": question["id"], "accepted": True, "option": question.get("recommended"), "text": "", "note": "", "attachments": []}


def accepting(interaction):
    """The response body that accepts `interaction`."""
    if interaction["kind"] == "questions":
        return {"answers": [answer(q) for q in interaction["questions"]]}
    if interaction["kind"] == "readback":
        return {"verdict": "approve", "version": interaction["version"], "answers": [answer(q) for q in interaction.get("decisions", [])], "marks": []}
    return {"winner": interaction["variants"][0]["key"], "take": "nothing", "leave_out": "nothing", "attachments": [], "comments": []}


def call(record, method, path, body=None):
    request = urllib.request.Request(
        f"http://127.0.0.1:{record['port']}{path}", method=method, data=None if body is None else json.dumps(body).encode(),
        headers={"X-Pilot-Token": record["token"], **({"Content-Type": "application/json"} if body is not None else {})})
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    with opener.open(request, timeout=5) as reply:
        return json.loads(reply.read() or b"null")


def step(effort):
    """One beat: poll the state and answer a pending interaction. A missing record or a refused connection is a beat with nothing to do."""
    try:
        record = json.loads((effort / "pilot" / "server.json").read_text())
        state = call(record, "GET", "/api/state")
        interaction = state["interaction"]
        if interaction is not None and state["response"] is None:
            call(record, "POST", f"/api/response/{interaction['number']}", accepting(interaction))
    except (OSError, ValueError, KeyError, TypeError):
        pass  # urllib.error.URLError and HTTPError are OSErrors; the next beat reads the record and the state again


def main(effort):
    while True:
        step(Path(effort))
        time.sleep(INTERVAL)


if __name__ == "__main__":
    main(sys.argv[1])
