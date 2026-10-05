#!/usr/bin/env python3
"""extract.py <run-dir>: write <run-dir>/transcript.md, the session's turns as readable text.

Each turn lists what the driver sent, then the assistant's messages and a one-line summary
of each tool call, from a Claude stream-json or a Codex --json stream.
"""
import json
import sys
from pathlib import Path


def short(value, n=240):
    text = value if isinstance(value, str) else json.dumps(value)
    text = " ".join(text.split())
    return text if len(text) <= n else text[:n] + " …"


def tool_line(name, inp):
    if not isinstance(inp, dict):
        return f"[{name}] {short(inp)}"
    for key in ("file_path", "command", "pattern", "skill", "description"):
        if key in inp:
            extra = f" | prompt: {short(inp.get('prompt', ''), 160)}" if "prompt" in inp else ""
            return f"[{name}] {key}={short(inp[key], 200)}{extra}"
    return f"[{name}] {short(inp)}"


def claude_events(lines):
    for line in lines:
        try:
            ev = json.loads(line)
        except ValueError:
            continue
        if ev.get("type") != "assistant" or ev.get("parent_tool_use_id"):
            continue
        for part in ev.get("message", {}).get("content", []):
            if part.get("type") == "text" and part["text"].strip():
                yield "text", part["text"].strip()
            elif part.get("type") == "tool_use":
                yield "tool", tool_line(part["name"], part.get("input"))


def codex_events(lines):
    for line in lines:
        try:
            ev = json.loads(line)
        except ValueError:
            continue
        item = ev.get("item") or {}
        if ev.get("type") != "item.completed":
            continue
        kind = item.get("type")
        if kind == "agent_message" and item.get("text", "").strip():
            yield "text", item["text"].strip()
        elif kind == "command_execution":
            yield "tool", f"[shell] {short(item.get('command', ''), 200)}"
        elif kind:
            yield "tool", f"[{kind}] {short({k: v for k, v in item.items() if k not in ('id', 'type')}, 200)}"


def main(run):
    run = Path(run)
    out = [f"# {run.name}", ""]
    turns = sorted(run.glob("turns/*.jsonl"), key=lambda p: int(p.stem))
    for t in turns:
        sent = (run / "turns" / f"{t.stem}.sent")
        out += [f"## Turn {t.stem}", "", f"> SENT: {sent.read_text().strip() if sent.exists() else '?'}", ""]
        lines = t.read_text(encoding="utf-8", errors="replace").splitlines()
        is_codex = any('"thread_id"' in l or '"item.completed"' in l for l in lines[:5])
        for kind, body in (codex_events if is_codex else claude_events)(lines):
            out += [body, ""] if kind == "text" else [f"    {body}"]
        out.append("")
    (run / "transcript.md").write_text("\n".join(out), encoding="utf-8")


if __name__ == "__main__":
    for arg in sys.argv[1:]:
        main(arg)
