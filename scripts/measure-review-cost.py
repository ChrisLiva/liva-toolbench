#!/usr/bin/env python3
"""Measure how an adversarial-review thread spent its turns.

Handed a transcript file or a directory, reports per thread: request count,
billed input, the four-bucket split of requests (apply / probe / report /
other), the tool-calls-per-request histogram, and the early-resident share --
the fraction of billed input that arrived as cache reads rather than fresh
cache writes, so a thread that keeps re-reading the same artifact is visible.

A directory is walked recursively, which reaches <session>/subagents/**/*.jsonl:
a subagent's turns never appear in its parent's transcript.

    python3 scripts/measure-review-cost.py <transcript.jsonl | directory>
"""

import json
import re
import sys
from collections import Counter
from pathlib import Path

APPLY_TOOLS = {"Edit", "MultiEdit", "Write", "NotebookEdit"}
READ_TOOLS = {"Read", "Grep", "Glob", "LS", "NotebookRead", "WebFetch", "WebSearch"}
SHELL_WRITE = re.compile(r"write_text|\.replace\(|sed -i|tee ")


def is_apply(name, tool_input):
    if name in APPLY_TOOLS:
        return True
    if name == "Bash":
        return bool(SHELL_WRITE.search(str(tool_input.get("command", ""))))
    return False


def is_read(name, tool_input):
    if name in READ_TOOLS:
        return True
    return name == "Bash" and not is_apply(name, tool_input)


def bucket(calls):
    if not calls:
        return "report"
    if any(is_apply(n, i) for n, i in calls):
        return "apply"
    if all(is_read(n, i) for n, i in calls):
        return "probe"
    return "other"


def read_thread(path):
    """Fold a transcript's assistant records into one entry per requestId."""
    requests = {}
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue
        if record.get("type") != "assistant":
            continue
        request_id = record.get("requestId")
        if not request_id:
            continue
        message = record.get("message") or {}
        entry = requests.setdefault(request_id, {"calls": [], "usage": None})
        for block in message.get("content") or []:
            if isinstance(block, dict) and block.get("type") == "tool_use":
                entry["calls"].append((block.get("name", ""), block.get("input") or {}))
        usage = message.get("usage")
        # The same usage repeats on every record of one request; count it once.
        if usage and entry["usage"] is None:
            entry["usage"] = usage
    return requests


def report(path, requests):
    billed = resident = 0
    buckets = Counter()
    histogram = Counter()
    for entry in requests.values():
        usage = entry["usage"] or {}
        cache_read = usage.get("cache_read_input_tokens", 0)
        billed += usage.get("input_tokens", 0) + usage.get("cache_creation_input_tokens", 0) + cache_read
        resident += cache_read
        buckets[bucket(entry["calls"])] += 1
        if entry["calls"]:
            histogram[len(entry["calls"])] += 1
    share = f"{resident / billed:.1%}" if billed else "n/a"
    print(f"thread: {path}")
    print(f"  requests: {len(requests)}")
    print(f"  billed: {billed}")
    print(f"  apply: {buckets['apply']}  probe: {buckets['probe']}  "
          f"report: {buckets['report']}  other: {buckets['other']}")
    print(f"  calls/request: {dict(sorted(histogram.items()))}")
    print(f"  early-resident: {share}")


def main(argv):
    if len(argv) != 2:
        print(__doc__.strip(), file=sys.stderr)
        return 2
    target = Path(argv[1])
    if target.is_dir():
        paths = sorted(target.rglob("*.jsonl"))
    elif target.is_file():
        paths = [target]
    else:
        print(f"no such transcript: {target}", file=sys.stderr)
        return 2
    if not paths:
        print(f"no .jsonl transcripts under {target}", file=sys.stderr)
        return 2
    for path in paths:
        requests = read_thread(path)
        if requests:
            report(path, requests)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
