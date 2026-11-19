#!/usr/bin/env python3
"""claude_chat_shim.py <model>: serve OpenAI chat completions on 127.0.0.1 by running `claude -p --model <model>`.

SkillEvaluator writes and grades Tier 3 cases through an OpenAI-compatible endpoint. This one answers each request
with one headless Claude Code session signed in with the subscription token in CLAUDE_CODE_OAUTH_TOKEN. The session
has no tools, MCP servers or slash commands, runs in an empty directory with an empty CLAUDE_CONFIG_DIR so no
CLAUDE.md, plugin, hook or setting of the user's reaches it, and keeps only sandboxed_claude.py's environment
allowlist. Prints the port it bound, then serves until killed.
"""
import hashlib
import json
import os
import shutil
import signal
import subprocess
import sys
import tempfile
import threading
import time
from concurrent.futures import Future
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "smoke"))
from sandboxed_claude import clean_env  # noqa: E402

EFFORTS = {"low", "medium", "high", "xhigh", "max"}
HOME = tempfile.mkdtemp(prefix="claude-chat-shim-")
ENV = {**clean_env(), "CLAUDE_CONFIG_DIR": f"{HOME}/config", "CLAUDE_CODE_OAUTH_TOKEN": os.environ["CLAUDE_CODE_OAUTH_TOKEN"]}
# A verifier that times out retries the same body; the retry joins the session already answering it.
calls: dict[str, Future] = {}
calls_lock = threading.Lock()


def text(message):
    content = message.get("content") or ""
    return content if isinstance(content, str) else "".join(p.get("text", "") for p in content if isinstance(p, dict))


def complete(body):
    messages = body["messages"]
    system = "\n\n".join(text(m) for m in messages if m["role"] in ("system", "developer"))
    turns = [m for m in messages if m["role"] not in ("system", "developer")]
    prompt = text(turns[-1]) if len(turns) == 1 else "\n\n".join(f"{m['role'].title()}: {text(m)}" for m in turns)
    command = ["claude", "-p", "--model", body["model"], "--tools", "", "--strict-mcp-config", "--disable-slash-commands",
               "--no-session-persistence", "--output-format", "json"]
    schema = (body.get("response_format") or {}).get("json_schema", {}).get("schema")
    if schema:
        command += ["--json-schema", json.dumps(schema)]
    elif (body.get("response_format") or {}).get("type") == "json_object":
        system += "\n\nRespond with one JSON object and nothing else."
    if system:
        command += ["--system-prompt", system]
    if body.get("reasoning_effort") in EFFORTS:
        command += ["--effort", body["reasoning_effort"]]
    done = subprocess.run(command, input=prompt, capture_output=True, text=True, env=ENV, cwd=HOME, timeout=1800)
    try:
        result = json.loads(done.stdout)
    except json.JSONDecodeError:
        raise RuntimeError(f"claude exited {done.returncode}: {(done.stderr or done.stdout)[-500:]}") from None
    if result.get("is_error"):
        raise RuntimeError(f"claude reported {result.get('subtype')}: {str(result.get('result'))[-500:]}")
    content = json.dumps(result["structured_output"]) if schema and "structured_output" in result else result["result"]
    usage = result.get("usage") or {}
    prompt_tokens = sum(usage.get(k, 0) for k in ("input_tokens", "cache_read_input_tokens", "cache_creation_input_tokens"))
    return {"id": f"chatcmpl-{result.get('session_id', '')}", "object": "chat.completion", "created": int(time.time()),
            "model": body["model"],
            "choices": [{"index": 0, "message": {"role": "assistant", "content": content}, "finish_reason": "stop"}],
            "usage": {"prompt_tokens": prompt_tokens, "completion_tokens": usage.get("output_tokens", 0),
                      "total_tokens": prompt_tokens + usage.get("output_tokens", 0)}}


class Handler(BaseHTTPRequestHandler):
    def reply(self, status, payload):
        data = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path.rstrip("/").endswith("/models"):
            self.reply(200, {"object": "list", "data": [{"id": MODEL, "object": "model", "owned_by": "anthropic"}]})
        else:
            self.reply(404, {"error": {"message": "not found"}})

    def do_POST(self):
        if not self.path.rstrip("/").endswith("/chat/completions"):
            return self.reply(404, {"error": {"message": "not found"}})
        raw = self.rfile.read(int(self.headers.get("Content-Length", 0)))
        key = hashlib.sha256(raw).hexdigest()
        with calls_lock:
            future, owner = calls.get(key), False
            if future is None:
                future, owner = calls.setdefault(key, Future()), True
        if owner:
            try:
                future.set_result(complete(json.loads(raw)))
            except Exception as exc:  # the caller gets the reason; a later retry starts a fresh session
                with calls_lock:
                    calls.pop(key, None)
                future.set_exception(exc)
        try:
            self.reply(200, future.result())
        except Exception as exc:
            self.reply(502, {"error": {"message": str(exc), "type": "upstream_error"}})

    def log_message(self, fmt, *args):
        sys.stderr.write(f"{time.strftime('%H:%M:%S')} {fmt % args}\n")


if __name__ == "__main__":
    MODEL = sys.argv[1]
    os.makedirs(ENV["CLAUDE_CONFIG_DIR"])
    signal.signal(signal.SIGTERM, lambda *_: sys.exit(0))
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    print(server.server_address[1], flush=True)
    try:
        server.serve_forever()
    finally:
        shutil.rmtree(HOME, ignore_errors=True)
