#!/usr/bin/env python3
"""Score lite-execute smoke runs.

    python3 score.py <batch-dir>          # runs at <batch-dir>/<arm>/<scenario>-<model>-<rep>/
    python3 score.py --json <batch-dir>   # one JSON object per run instead of the table

Each check reads a run's orchestrator stream, its subagents' streams, and the repo and
.crank/ state run.sh saved. A Claude run's stream is its stream-json turns (orchestrator
events carry no parent_tool_use_id); a Codex run's is the rollout files under rollouts/,
one per thread. A check scores 1 when the run did what lite-execute's rules ask, 0 when it
did not, and None when the run never reached the point the check judges. The table prints
each check's pass rate per arm.
"""

import json
import re
import subprocess
import sys
from collections import defaultdict, namedtuple
from pathlib import Path

HERE = Path(__file__).resolve().parent
SHA = re.compile(r"\b[0-9a-f]{7,40}\b")
# The model each harness's user-level instruction file names for all subagent work.
USER_SUBAGENT_MODEL = {"claude": "opus", "codex": "sol"}
Stream = namedtuple("Stream", "harness items sub_cmds final")


def load_events(run):
    events = []
    for f in sorted((run / "turns").glob("*.jsonl"), key=lambda p: int(p.stem)):
        for line in f.read_text(encoding="utf-8").splitlines():
            try:
                events.append(json.loads(line))
            except ValueError:
                pass
    return events


def orchestrator_items(events):
    """Ordered (kind, payload) items from the orchestrator's own messages."""
    items = []
    for e in events:
        if e.get("type") != "assistant" or e.get("parent_tool_use_id"):
            continue
        for c in e["message"]["content"]:
            if c["type"] == "text":
                items.append(("text", c["text"]))
            elif c["type"] == "tool_use":
                items.append((c["name"], c))
    return items


def subagent_bash(events):
    cmds = []
    for e in events:
        if e.get("type") == "assistant" and e.get("parent_tool_use_id"):
            for c in e["message"]["content"]:
                if c["type"] == "tool_use" and c["name"] == "Bash":
                    cmds.append(c["input"].get("command", ""))
    return cmds


def final_text(events):
    texts = [e.get("result") or "" for e in events if e.get("type") == "result"]
    return texts[-1] if texts else ""


def claude_stream(run):
    events = load_events(run)
    return Stream("claude", orchestrator_items(events), subagent_bash(events), final_text(events))


PATCH_PATH = re.compile(r"\*\*\* (?:Add|Update|Delete) File: ([^\n\\\"]+)")
JS_CMD = re.compile(r"""["']?cmd["']?\s*:\s*("(?:[^"\\]|\\.)*")""")


def codex_threads(run):
    """Each Codex rollout's records, working directory, and parent thread, keyed by thread id."""
    threads = {}
    for f in (run / "rollouts").glob("*.jsonl"):
        recs = [json.loads(l) for l in f.read_text(encoding="utf-8").splitlines() if l.strip()]
        meta = recs[0]["payload"]
        src = meta.get("source")
        spawn = src.get("subagent", {}).get("thread_spawn", {}) if isinstance(src, dict) else {}
        threads[meta["id"]] = {"parent": spawn.get("parent_thread_id"), "cwd": meta.get("cwd", ""), "recs": recs}
    return threads


def assistant_texts(recs, phase=None):
    return ["".join(c.get("text", "") for c in p.get("content", []) if c.get("type") == "output_text")
            for r in recs for p in [r.get("payload", {})]
            if r.get("type") == "response_item" and p.get("type") == "message" and p.get("role") == "assistant"
            and (phase is None or p.get("phase") == phase)]


def codex_calls(thread):
    """Ordered (kind, payload) items from one Codex thread, in the shapes a Claude stream gives.

    A Codex `exec` tool call is a script; each tools.exec_command cmd in it becomes a Bash
    item, and each file an apply_patch names becomes an Edit item."""
    items = []
    for r in thread["recs"]:
        p = r.get("payload", {})
        if r.get("type") != "response_item":
            continue
        if p.get("type") == "message" and p.get("role") == "assistant":
            text = "".join(c.get("text", "") for c in p.get("content", []) if c.get("type") == "output_text")
            if text:
                items.append(("text", text))
            continue
        if p.get("type") not in ("custom_tool_call", "function_call"):
            continue
        name, raw = p.get("name"), p.get("input") or p.get("arguments") or ""
        if name == "spawn_agent":
            args = json.loads(raw or "{}")
            items.append(("Agent", {"call_id": p.get("call_id"), "input": {
                "model": args.get("model", ""), "task_name": args.get("task_name", ""), "prompt": ""}}))
            continue
        cmds = []
        if p.get("type") == "function_call" and name in ("exec_command", "shell", "shell_command"):
            cmd = json.loads(raw or "{}")
            cmd = cmd.get("cmd") or cmd.get("command") or ""
            cmds = [" ".join(cmd) if isinstance(cmd, list) else cmd]
        elif name == "exec":
            for m in JS_CMD.finditer(raw):
                try:
                    cmds.append(json.loads(m.group(1)))
                except ValueError:
                    cmds.append(m.group(1))
            if not cmds and "apply_patch" not in raw:
                cmds = [raw]
        items += [("Bash", {"input": {"command": c}}) for c in cmds]
        for path in (x.strip() for x in PATCH_PATH.findall(raw)):
            items.append(("Edit", {"input": {"file_path": path if path.startswith("/") else f"{thread['cwd']}/{path}",
                                             "patch": raw}}))
    return items


def codex_stream(run):
    """The orchestrator's items, every subagent's shell commands, and the final reply of a Codex run.

    Codex encrypts the message a spawn sends, so a dispatch's prompt stays empty; its
    child_cmds field carries the commands the spawned thread ran instead."""
    threads = codex_threads(run)
    root = (run / "session-id").read_text().strip()
    if root not in threads:
        return Stream("codex", [], [], "")
    spawned = {}
    for r in threads[root]["recs"]:
        it = r.get("payload", {}).get("item", {})
        if it.get("type") == "SubAgentActivity" and it.get("kind") == "started":
            spawned[it["id"]] = it["agent_thread_id"]
    calls = {t: codex_calls(th) for t, th in threads.items()}
    items = calls[root]
    for kind, payload in items:
        if kind == "Agent":
            tid = spawned.get(payload["call_id"])
            payload["input"]["child_cmds"] = "\n".join(bash_cmd(it) for it in calls.get(tid, []))
            recs = threads[tid]["recs"] if tid in threads else []
            payload["input"]["child_text"] = "\n".join(assistant_texts(recs, "final_answer") or assistant_texts(recs)[-1:])
    sub_cmds = [bash_cmd(it) for t, c in calls.items() if t != root for it in c]
    finals = assistant_texts(threads[root]["recs"], "final_answer") or assistant_texts(threads[root]["recs"])
    return Stream("codex", items, sub_cmds, finals[-1] if finals else "")


def first_index(items, pred):
    for i, it in enumerate(items):
        if pred(it):
            return i
    return None


def bash_cmd(it):
    return it[1]["input"].get("command", "") if it[0] == "Bash" else ""


def is_mutation(it):
    if it[0] in ("Edit", "Write", "NotebookEdit", "Agent"):
        return True
    cmd = bash_cmd(it)
    return bool(re.search(r"(^|\s)(cat|tee|printf|echo)\b.*>|sed -i|git commit|python3 - ", cmd))


def preflight(items):
    for kind, payload in items:
        if kind == "text" and "**Pre-flight**" in payload:
            return payload[payload.index("**Pre-flight**"):]
    return None


def preflight_file(run):
    """The Pre-flight lines a run wrote at the top of the plan's Progress block, if any."""
    m = re.search(r"^## Progress\n(.*?)^Base:", plan_text(run, "crank-after"), re.M | re.S)
    return m.group(1) if m and re.search(r"^-? ?Shape:", m.group(1), re.M) else None


def preflight_line(block, field):
    """A field's value from a Pre-flight block written one field per line or as one `·`-joined line."""
    if not block:
        return None
    m = re.search(rf"(?:^|·)\s*-?\s*{field}:([^\n]*)", block, re.M)
    if not m:
        return None
    return re.split(r" · (?:Plan|Branch|Shape|Subagents|Tasks|Bound):", m.group(1))[0].strip()


def plan_text(run, which):
    """The plan of the one effort run.sh copied into .crank/."""
    plans = sorted((run / which).glob("*/plan.md"))
    return plans[0].read_text(encoding="utf-8") if plans else ""


def progress_lines(plan):
    return re.findall(r"^- \[([ x])\] Task (\d+):(.*)$", plan, re.M)


def grounding_lines(plan):
    m = re.search(r"^## Grounding\n(.*?)(?=^## |\Z)", plan, re.M | re.S)
    return [l for l in (m.group(1).splitlines() if m else []) if l.startswith("- ")]


def git(run, *args):
    return subprocess.run(["git", "-C", str(run / "repo"), *args], capture_output=True, text=True).stdout


def dispatches(items):
    agents = [(i, it[1]["input"]) for i, it in enumerate(items) if it[0] == "Agent"]
    def is_review(a):
        p = a.get("prompt", "")
        return ("REVIEW-BRIEF" in p + a.get("child_cmds", "") or "review" in a.get("task_name", "").lower()
                or bool(re.search(r"\breview", p, re.I) and re.search(r"\bdiff\b", p)))
    reviewer = [(i, a) for i, a in agents if is_review(a)]
    impl = [(i, a) for i, a in agents if not is_review(a)]
    return impl, reviewer


def rate(hits, total):
    return None if total == 0 else round(hits / total, 2)


def common(run, items):
    reply = preflight(items)
    in_plan = preflight_file(run)
    block = reply or in_plan
    mut_idx = first_index(items, is_mutation)
    if reply is not None:
        pf_idx = first_index(items, lambda it: it[0] == "text" and "**Pre-flight**" in it[1])
        first = int(mut_idx is None or pf_idx < mut_idx)
    elif in_plan is not None:
        first = int(mut_idx is not None and "Shape:" in json.dumps(items[mut_idx][1].get("input", {})))
    else:
        first = None
    subagents = preflight_line(block, "Subagents") or ""
    return block, {
        "preflight_present": int(block is not None),
        "preflight_in_reply": int(reply is not None),
        "preflight_in_plan": int(in_plan is not None),
        "preflight_first": first,
        "tiers_resolved_from_user": None if block is None else int(
            bool(re.search(r"user (CLAUDE|AGENTS)\.md|~/\.(claude|codex)/", subagents))),
        "no_sleep_polling": int(not any("sleep" in bash_cmd(it) for it in items)),
    }


def score_fresh(run, st, block, s):
    items = st.items
    impl, reviewer = dispatches(items)
    rev_idx = reviewer[0][0] if reviewer else len(items)
    shape = (preflight_line(block, "Shape") or "").lower()
    subagents = preflight_line(block, "Subagents") or ""
    std = re.search(r"standard = ([^(,·]+)", subagents)
    s["shape_sequential"] = None if block is None else int("sequential" in shape)
    s["standard_tier_user_model"] = None if not std else int(USER_SUBAGENT_MODEL[st.harness] in std.group(1).lower())
    s["impl_dispatches"] = len(impl)
    s["impl_dispatch_per_task"] = int(len(impl) == 5)
    s["impl_model_user"] = rate(
        sum(USER_SUBAGENT_MODEL[st.harness] in str(a.get("model", "")).lower() for _, a in impl), len(impl))
    briefs = [a["prompt"] for _, a in impl if a.get("prompt")]
    s["brief_carries_constraints"] = rate(sum(bool(re.search(r"BOM|utf-8-sig", b)) for b in briefs), len(briefs))
    s["brief_carries_defect_rules"] = rate(
        sum(bool(re.search(r"round-trip|mutation|IMPLEMENTER-BRIEF", b, re.I)) for b in briefs), len(briefs))
    if st.harness == "codex":
        s["impl_reads_brief"] = rate(sum("IMPLEMENTER-BRIEF" in a.get("child_cmds", "") for _, a in impl), len(impl))
    s["implementers_never_commit"] = int(not any("git commit" in c for c in st.sub_cmds))
    inline = [it for it in items[:rev_idx]
              if (it[0] in ("Edit", "Write") and re.search(r"/repo/(ledger|tests|docs)/", it[1]["input"].get("file_path", "")))
              or re.search(r">\s*\S*\b(ledger|tests|docs)/", bash_cmd(it))]
    s["no_inline_source_edits"] = int(not inline)

    seed = (run / "seed-head").read_text().strip()
    commits = [l for l in git(run, "log", "--format=%h", f"{seed}..HEAD").splitlines() if l]
    s["commits_after_seed"] = len(commits)
    s["commit_per_task"] = int(len(commits) >= 5)
    plan = plan_text(run, "crank-after")
    lines = progress_lines(plan)
    s["progress_all_checked"] = int(len(lines) == 5 and all(b == "x" for b, _, _ in lines))
    shas_ok = [bool(SHA.search(rest)) and git(run, "cat-file", "-t", SHA.search(rest).group(0)).strip() == "commit"
               for b, _, rest in lines if b == "x"]
    s["progress_shas_resolve"] = rate(sum(shas_ok), len(shas_ok))
    s["progress_format"] = rate(sum(bool(re.fullmatch(r" .+? — [0-9a-f]{7,40}( — (open|note):.*)?", rest)) for b, _, rest in lines if b == "x"),
                                sum(b == "x" for b, _, _ in lines))
    s["readme_edit_untouched"] = int(" M README.md" in (run / "status.txt").read_text()
                                     and "README.md" not in git(run, "log", "--format=", "--name-only", f"{seed}..HEAD"))
    before = grounding_lines(plan_text(run, "crank-before"))
    after = grounding_lines(plan)
    s["grounding_banks_detour"] = int(any(re.search(r"read_all|load_entries", l) for l in after[len(before):])
                                      or any(re.search(r"read_all|load_entries", l) for l in after if l not in before))

    def orch_bash_between(lo, hi, pattern):
        return any(re.search(pattern, bash_cmd(it)) for it in items[lo:hi])

    if len(impl) >= 3:
        s["stage1_gate_run"] = int(orch_bash_between(impl[1][0], impl[2][0], r"unittest discover"))
    else:
        s["stage1_gate_run"] = None
    last_impl = impl[-1][0] if impl else 0
    s["full_suite_before_review"] = None if not reviewer else int(orch_bash_between(last_impl, rev_idx, r"unittest discover"))
    s["coverage_bom_row_before_review"] = None if not reviewer else int(
        orch_bash_between(0, rev_idx, r"ledger export") and orch_bash_between(0, rev_idx, r"od |head -c|xxd|hexdump"))
    s["reviewer_dispatched"] = int(bool(reviewer))
    s["reviewer_pointers"] = None if not reviewer or not reviewer[0][1].get("prompt") else int(
        bool(re.search(r"/lite-execute/REVIEW-BRIEF\.md", reviewer[0][1].get("prompt", "")))
        and "git diff" in reviewer[0][1].get("prompt", ""))
    s["retro_written"] = int((run / "crank-after" / "csv-export" / "retro.md").exists())
    # A run that ends its turn after a dispatch returns, or to report progress, needs run.sh's
    # "continue" reply to finish, so it shows here as more than one turn.
    s["finished_first_turn"] = int(s["retro_written"] and turns(run) == 1)
    texts = " ".join(p for k, p in items if k == "text")
    s["stage_labels_in_replies"] = int(bool(re.search(r"Task \d+ \(stage \d of 2", texts)))
    s["final_report_shas"] = int(len(set(SHA.findall(st.final))) >= 2)

    out = subprocess.run(["python3", "-m", "ledger", "export", "--out", str(run / "export.csv")],
                         cwd=run / "repo", capture_output=True, text=True)
    s["export_writes_bom"] = int(out.returncode == 0 and (run / "export.csv").exists()
                                 and (run / "export.csv").read_bytes()[:3] == b"\xef\xbb\xbf")
    t = subprocess.run(["python3", "-m", "unittest", "discover", "-s", "tests"], cwd=run / "repo",
                       capture_output=True, text=True)
    s["suite_green"] = int(t.returncode == 0)


def score_stop_if(run, st, block, s):
    items = st.items
    impl, reviewer = dispatches(items)
    shape = (preflight_line(block, "Shape") or "").lower()
    bound = preflight_line(block, "Bound") or ""
    s["bound_task2"] = None if block is None else int(bool(re.search(r"Task 2\b", bound)))
    s["shape_solo"] = None if block is None else int("solo" in shape)
    seed = (run / "seed-head").read_text().strip()
    s["no_new_commits"] = int(git(run, "rev-parse", "HEAD").strip() == seed)
    plan = plan_text(run, "crank-after")
    lines = {int(n): (b, rest) for b, n, rest in progress_lines(plan)}
    s["task2_unchecked"] = int(lines.get(2, ("x", ""))[0] == " ")
    s["stopped_line"] = int(bool(re.search(r"^Base: \S+\nStopped: .*resume at Task 2", plan, re.M)))
    s["task2_annotated"] = int(bool(re.search(r"open:|note:", lines.get(2, ("", ""))[1])))
    s["unchecked_all_annotated"] = int(all(re.search(r"open:|note:", lines.get(n, ("", ""))[1]) for n in (2, 3, 4, 5)))
    s["api_untouched"] = int("ledger/api.py" not in (run / "diff.txt").read_text())
    s["no_review_no_retro"] = int(not reviewer and not (run / "crank-after" / "csv-export" / "retro.md").exists())
    texts = " ".join(p for k, p in items if k == "text")
    s["stage_label_gate"] = int(bool(re.search(r"Task 2 \(stage 1 of 2, gate\)", texts)))
    before = grounding_lines(plan_text(run, "crank-before"))
    s["grounding_banks_fact"] = int(any(re.search(r"middleware", l, re.I) for l in grounding_lines(plan) if l not in before))
    # json_middleware offers no opt-out, so every route around it edits shared code: a decision,
    # put to the user as numbered options with one recommended.
    s["decision_options"] = int(bool(re.search(r"^\W*1[.)]", st.final, re.M) and re.search(r"^\W*2[.)]", st.final, re.M)
                                     and re.search(r"recommend", st.final, re.I)))


ROUTE_PROBE = """
from ledger.api import ROUTES
r = ROUTES["/export.csv"]("data/sample.tsv")
assert r.content_type == "text/csv", r.content_type
assert "attachment" in r.headers.get("Content-Disposition", ""), r.headers
assert r.body.lstrip("\\ufeff").startswith("date,payee,amount_cents"), r.body[:40]
"""


def score_stop_if_detour(run, st, block, s):
    """json_middleware forces JSON, but its keep_content_type opt-out, which /health uses, ships
    the CSV route without editing shared code, so the observed Stop if is a detour to settle."""
    impl, reviewer = dispatches(st.items)
    shape = (preflight_line(block, "Shape") or "").lower()
    bound = preflight_line(block, "Bound") or ""
    s["bound_task2"] = None if block is None else int(bool(re.search(r"Task 2\b", bound)))
    s["shape_solo"] = None if block is None else int("solo" in shape)
    plan = plan_text(run, "crank-after")
    lines = {int(n): (b, rest) for b, n, rest in progress_lines(plan)}
    box, rest = lines.get(2, (" ", ""))
    sha = SHA.search(rest)
    s["task2_committed"] = int(box == "x" and bool(sha) and git(run, "cat-file", "-t", sha.group(0)).strip() == "commit")
    s["no_user_stop"] = int(s["task2_committed"] and turns(run) == 1)
    middleware = re.search(r"^def json_middleware.*?(?=^\S)", (HERE / "fixture/variants/api_stop_if_detour.py").read_text(),
                           re.M | re.S).group(0)
    s["middleware_untouched"] = int(middleware in (run / "repo" / "ledger" / "api.py").read_text())
    probe = subprocess.run(["python3", "-c", ROUTE_PROBE], cwd=run / "repo", capture_output=True, text=True)
    s["route_serves_csv"] = int(probe.returncode == 0)
    s["stopped_line"] = int(bool(re.search(r"^Base: \S+\nStopped: .*resume at Task 3", plan, re.M)))
    s["no_review_no_retro"] = int(not reviewer and not (run / "crank-after" / "csv-export" / "retro.md").exists())
    before = grounding_lines(plan_text(run, "crank-before"))
    s["grounding_banks_fact"] = int(any(re.search(r"middleware|keep_content_type", l, re.I)
                                        for l in grounding_lines(plan) if l not in before))
    t = subprocess.run(["python3", "-m", "unittest", "discover", "-s", "tests"], cwd=run / "repo",
                       capture_output=True, text=True)
    s["suite_green"] = int(t.returncode == 0)


def score_spec_path(run, st, block, s):
    impl, reviewer = dispatches(st.items)
    same = all((run / "crank-before" / "csv-export" / n).read_bytes() == (run / "crank-after" / "csv-export" / n).read_bytes()
               for n in ("plan.md", "spec.md"))
    seed = (run / "seed-head").read_text().strip()
    s["refused"] = int(same and not impl and git(run, "rev-parse", "HEAD").strip() == seed
                       and not (run / "diff.txt").read_text().strip())
    s["recommends_plan_phase"] = int(bool(re.search(r"crank-lite plan|plan phase", st.final)))


VARIANT = "variant-b"


def touches_variant(it):
    return it[0] in ("Read", "Bash", "Grep") and VARIANT in json.dumps(it[1].get("input", {}))


def subagent_variant_readers(run, st):
    """The orchestrator tool_use ids whose subagent read the winning variant (Claude streams only)."""
    if st.harness != "claude":
        return set()
    readers = set()
    for e in load_events(run):
        if e.get("type") == "assistant" and e.get("parent_tool_use_id"):
            for c in e["message"]["content"]:
                if c["type"] == "tool_use" and touches_variant((c["name"], c)):
                    readers.add(e["parent_tool_use_id"])
    return readers


def filter_in_sidebar(html):
    """The memo filter, the winner's primary affordance, sits inside the sidebar."""
    inp = html.find("<input")
    aside = re.search(r"<aside\b.*?</aside>", html, re.S)
    if aside:
        return aside.start() < inp < aside.end()
    side = re.search(r"<\w+[^>]*class=\"[^\"]*side", html)
    table = html.find("<table")
    return bool(side) and side.start() < inp < (table if table > 0 else len(html))


def month_net(html):
    """A 2026-09 month header carries that month's net, 2,218.25, ahead of the month's first entry."""
    for m in re.finditer(r"2026-09(?!-\d)", html):
        nxt = re.compile(r"2026-09-\d\d").search(html, m.end())
        if re.search(r"2,?218\.25", html[m.end():nxt.start() if nxt else len(html)]):
            return True
    return False


def score_prototype(run, st, block, s):
    """The spec's Prototype: line names variant-b.html; the plan only restates the verdict as a sidebar.

    The committed checks follow the verdict: the filter in the sidebar (the winner's layout),
    sticky month headers (taken from variant A), and no sparklines (left out). The open-detail
    checks follow what only the mock shows: parenthesized negatives and a net on each month header."""
    items = st.items
    impl, reviewer = dispatches(items)
    rev_idx = reviewer[0][0] if reviewer else len(items)
    solo = (run / "arm").read_text().split()[0] == "prototype-solo"
    shape = (preflight_line(block, "Shape") or "").lower()
    s["shape_expected"] = None if block is None else int(("solo" if solo else "sequential") in shape)
    s["orch_reads_variant"] = int(any(touches_variant(it) for it in items[:rev_idx]))
    page = [(i, a) for i, a in impl if "Render the report page" in a.get("prompt", "")]
    if solo:
        s["page_dispatch_carries_variant"] = None
        s["page_builder_reads_variant"] = s["orch_reads_variant"]
    elif st.harness == "codex":
        s["page_dispatch_carries_variant"] = None
        s["page_builder_reads_variant"] = None if not impl else int(
            any(VARIANT in a.get("child_cmds", "") for _, a in impl))
    else:
        readers = subagent_variant_readers(run, st)
        s["page_dispatch_carries_variant"] = None if not page else int(any(f"{VARIANT}.html" in a["prompt"] for _, a in page))
        s["page_builder_reads_variant"] = None if not page else int(any(items[i][1].get("id") in readers for i, _ in page))

    plan = plan_text(run, "crank-after")
    lines = progress_lines(plan)
    s["progress_all_checked"] = int(len(lines) == (3 if solo else 4) and all(b == "x" for b, _, _ in lines))
    s["retro_written"] = int((run / "crank-after" / "ledger-report" / "retro.md").exists())
    s["finished_first_turn"] = int(s["retro_written"] and turns(run) == 1)
    out = run / "report.html"
    r = subprocess.run(["python3", "-m", "ledger.report", "data/ledger.csv", str(out)], cwd=run / "repo",
                       capture_output=True, text=True)
    html = out.read_text(encoding="utf-8") if r.returncode == 0 and out.exists() else ""
    s["page_renders"] = int(bool(html))
    for k, check in [("filter_in_sidebar", filter_in_sidebar),
                     ("sticky_month_headers", lambda h: "sticky" in h),
                     ("no_sparklines", lambda h: not re.search(r"<svg|<canvas|sparkline|polyline", h, re.I)),
                     ("parenthesized_negatives", lambda h: bool(re.search(r"\(\d[\d,]*\.\d\d\)", h))),
                     ("month_net", month_net)]:
        s[k] = int(check(html)) if html else None
    source = "".join(f.read_text(encoding="utf-8") for d in ("ledger", "tests") for f in (run / "repo" / d).glob("*.py"))
    s["no_mock_in_source"] = int("Mock memo" not in source)
    t = subprocess.run(["python3", "-m", "unittest"], cwd=run / "repo", capture_output=True, text=True)
    s["suite_green"] = int(t.returncode == 0)


def agent_returns(run, st, agents):
    """The text each dispatched subagent returned, in dispatch order."""
    if st.harness == "codex":
        return [a.get("child_text", "") for _, a in agents]
    ids = [st.items[i][1].get("id") for i, _ in agents]
    texts = {}
    for e in load_events(run):
        if e.get("type") != "user" or e.get("parent_tool_use_id"):
            continue
        content = e["message"].get("content")
        for c in content if isinstance(content, list) else []:
            if c.get("type") == "tool_result" and c.get("tool_use_id") in ids:
                body = c.get("content")
                texts[c["tool_use_id"]] = body if isinstance(body, str) else "".join(
                    b.get("text", "") for b in body or [] if isinstance(b, dict))
    return [texts.get(i, "") for i in ids]


def confirmed_text(text):
    """The lines of a review return under a CONFIRMED verdict, up to the next REFUTED one."""
    keep, confirmed = [], False
    for line in text.splitlines():
        heading = line.lstrip().startswith("#")
        if re.search(r"\bREFUTED\b", line) or heading and re.search(r"refuted", line, re.I):
            confirmed = False
        elif re.search(r"\bCONFIRMED\b", line) or heading and re.search(r"confirmed", line, re.I):
            confirmed = True
        if confirmed:
            keep.append(line)
    return "\n".join(keep)


def near(text, a, b, span=400):
    """Whether patterns a and b both match within span characters of each other."""
    return any(re.search(b, text[max(0, m.start() - span):m.end() + span]) for m in re.finditer(a, text))


# The review seed's planted defects: (name, the shard territory it sits in, whether a lowercased
# CONFIRMED finding names it). Each leaves the suite and the Coverage walk green.
DEFECTS = [
    ("newline_flattened", "stage 1", lambda t: near(t, r"newline|line break|\\n",
                                                   r"replace|flatten|space|corrupt|lost|lose|lossy|alter|mangl|strip|round.trip")),
    ("mock_writer_test", "stage 1", lambda t: near(t, r"mock|patch", r"writer|writerow|call_count|call count")),
    ("route_unregistered", "stage 1", lambda t: near(t, r"export_csv|/export\.csv|export route",
                                                    r"regist|decorat|@route|routes\b|dead seam|wired|unreachable|404")),
    ("filename_mismatch", "cross-cut", lambda t: near(t, r"filename|content-disposition",
                                                     r"export\.csv\"|ledger\.csv|wrong|mismatch|untested|not (?:checked|tested|asserted)|never (?:checked|tested|asserted)|no test")),
    ("chardet_import", "cross-cut", lambda t: "chardet" in t),
    ("fragmented_cli_tests", "stage 2", lambda t: near(t, r"test_cli_export|cli test|cliexporttest",
                                                      r"redundant|fragment|one.assertion|single.assertion|same setup|rebuild|duplicat|merge|journey")),
    ("stream_joins", "stage 2", lambda t: near(t, r"join|(?:one|single|whole|entire) (?:large |csv )?string",
                                              r"iter_csv|stream|memory|large|whole|string")),
    ("bom_large_branch", "cross-cut", lambda t: near(t, r"\bbom\b|utf-8-sig", r"10[,_]?000|threshold|large|stream|branch")),
    ("docs_delimiter", "stage 2", lambda t: "delimiter" in t),
]

# Prints, as JSON, whether the run's final tree has fixed each planted defect.
DEFECT_PROBE = r"""
import csv, io, json, subprocess, sys, tempfile
from pathlib import Path

def big_export_has_bom():
    d = Path(tempfile.mkdtemp())
    (d / "big.tsv").write_text("".join(f"2026-09-01\tpayee {i}\t{i}\n" for i in range(10_001)), encoding="utf-8")
    r = subprocess.run([sys.executable, "-m", "ledger", "--file", str(d / "big.tsv"), "export", "--out", str(d / "big.csv")],
                       capture_output=True)
    return r.returncode == 0 and (d / "big.csv").read_bytes()[:3] == b"\xef\xbb\xbf"

def text(path):
    return Path(path).read_text(encoding="utf-8") if Path(path).exists() else ""

def route_headers():
    from ledger.api import ROUTES
    return ROUTES["/export.csv"]("data/sample.tsv").headers.get("Content-Disposition", "")

def newline_round_trips():
    from ledger.csv_export import to_csv
    from ledger.store import Entry
    return list(csv.reader(io.StringIO(to_csv([Entry("2026-09-01", "a\nb", 1)]))))[1][1] == "a\nb"

checks = {
    "newline_flattened": newline_round_trips,
    "mock_writer_test": lambda: "mock" not in text("tests/test_csv_export.py"),
    "route_unregistered": lambda: route_headers() is not None,
    "filename_mismatch": lambda: 'filename="ledger.csv"' in route_headers(),
    "chardet_import": lambda: not any("chardet" in p.read_text(encoding="utf-8") for p in Path("ledger").glob("*.py")),
    "fragmented_cli_tests": lambda: text("tests/test_cli_export.py").count("def test_") < 3,
    "stream_joins": lambda: '"".join(iter_csv' not in text("ledger/cli.py"),
    "bom_large_branch": big_export_has_bom,
    "docs_delimiter": lambda: "--delimiter" not in text("docs/cli.md") or "--delimiter" in text("ledger/cli.py"),
}
fixed = {}
for name, check in checks.items():
    try:
        fixed[name] = bool(check())
    except Exception:
        fixed[name] = False
print(json.dumps(fixed))
"""

# $/MTok at Anthropic first-party rates (claude-api skill table, cached 2026-10-06): input, output,
# cache read. Cache writes bill at 1.25x input, the 5-minute TTL these sessions use.
PRICES = {"opus": (4.0, 20.0, 0.20), "sonnet": (2.0, 10.0, 0.20)}


def review_cost(run):
    """Dollars, requests, tool calls per request, and wall-clock seconds across a Claude run's reviewer
    threads, read from the session's subagent transcripts run.sh copied; None on Codex."""
    out = {"review_dollars": None, "review_requests": None, "review_calls_per_request": None, "review_seconds": None}
    files = []
    for f in sorted((run / "subagents").glob("*.jsonl")):
        recs = [json.loads(l) for l in f.read_text(encoding="utf-8").splitlines() if l.strip()]
        first = next((r for r in recs if r.get("type") == "user"), {})
        if "REVIEW-BRIEF" in json.dumps(first.get("message", {}).get("content", ""))[:3000]:
            files.append(recs)
    if not files:
        return out
    dollars, requests, calls, stamps = 0.0, 0, 0, []
    for recs in files:
        usage, outputs = {}, {}
        for r in recs:
            stamps += [r["timestamp"]] if r.get("timestamp") else []
            if r.get("type") != "assistant" or not r.get("requestId"):
                continue
            msg = r.get("message") or {}
            rid = r["requestId"]
            usage.setdefault(rid, (msg.get("model", ""), msg.get("usage") or {}))
            # Later records of one request repeat its input counts and carry its final output count.
            outputs[rid] = max(outputs.get(rid, 0), (msg.get("usage") or {}).get("output_tokens", 0))
            calls += sum(1 for c in msg.get("content") or [] if isinstance(c, dict) and c.get("type") == "tool_use")
        for rid, (model, u) in usage.items():
            price = next((v for k, v in PRICES.items() if k in model), None)
            if price is None:
                return out
            inp, outp, read = price
            dollars += (u.get("input_tokens", 0) * inp + u.get("cache_creation_input_tokens", 0) * inp * 1.25
                        + u.get("cache_read_input_tokens", 0) * read + outputs[rid] * outp) / 1e6
        requests += len(usage)
    stamps.sort()
    seconds = subprocess.run(["python3", "-c", "import sys; from datetime import datetime as d; "
                              "print(int((d.fromisoformat(sys.argv[2].replace('Z', '+00:00')) - "
                              "d.fromisoformat(sys.argv[1].replace('Z', '+00:00'))).total_seconds()))",
                              stamps[0], stamps[-1]], capture_output=True, text=True).stdout.strip()
    return {"review_dollars": round(dollars, 2), "review_requests": requests,
            "review_calls_per_request": round(calls / requests, 2) if requests else None,
            "review_seconds": int(seconds) if seconds else None}


def score_review(run, st, block, s):
    """Every task is committed and checked, so the run goes straight to Review over a diff carrying
    the nine planted defects in DEFECTS. A defect counts as caught when a CONFIRMED finding in a
    reviewer's return names it, or on Codex when the reviewer's final answer does, and as fixed when
    DEFECT_PROBE finds it gone from the final tree."""
    impl, reviewer = dispatches(st.items)
    s["reviewer_dispatched"] = int(bool(reviewer))
    s["review_dispatches"] = len(reviewer)
    # Codex encrypts the findings a reviewer sends; its plaintext final answer summarizes the confirmed ones.
    returns = agent_returns(run, st, reviewer)
    text = "\n".join(returns if st.harness == "codex" else map(confirmed_text, returns)).lower()
    for name, _, named in DEFECTS:
        s[f"caught_{name}"] = int(named(text)) if reviewer else None
    s["caught_total"] = sum(s[f"caught_{n}"] for n, _, _ in DEFECTS) if reviewer else None
    probe = subprocess.run(["python3", "-c", DEFECT_PROBE], cwd=run / "repo", capture_output=True, text=True)
    fixed = json.loads(probe.stdout) if probe.returncode == 0 else {}
    for name, _, _ in DEFECTS:
        s[f"fixed_{name}"] = int(fixed[name]) if name in fixed else None
    s["fixed_total"] = sum(fixed.values()) if fixed else None
    s.update(review_cost(run))
    s["retro_written"] = int((run / "crank-after" / "csv-export" / "retro.md").exists())
    t = subprocess.run(["python3", "-m", "unittest", "discover", "-s", "tests"], cwd=run / "repo",
                       capture_output=True, text=True)
    s["suite_green"] = int(t.returncode == 0)


def turns(run):
    return int((run / "turn-count").read_text()) if (run / "turn-count").exists() else None


SCORERS = {"fresh": score_fresh, "stop-if": score_stop_if, "stop-if-detour": score_stop_if_detour,
           "spec-path": score_spec_path, "prototype": score_prototype, "prototype-solo": score_prototype,
           "review": score_review}


def score(run):
    scenario, model = (run / "arm").read_text().split()
    st = codex_stream(run) if (run / "rollouts").is_dir() else claude_stream(run)
    block, s = common(run, st.items)
    SCORERS[scenario](run, st, block, s)
    s["seconds"] = int((run / "seconds").read_text()) if (run / "seconds").exists() else None
    s["turns"] = turns(run)
    return scenario, model, s


def main():
    args = sys.argv[1:]
    as_json = "--json" in args
    batch = Path([a for a in args if a != "--json"][0])
    table = defaultdict(lambda: defaultdict(list))
    for run in sorted(p for p in batch.glob("*/*") if (p / "arm").exists()):
        if not (run / "seconds").exists():
            print(f"skip unfinished {run}", file=sys.stderr)
            continue
        scenario, model, s = score(run)
        arm = run.parent.name
        if as_json:
            print(json.dumps({"run": str(run.relative_to(batch)), **s}))
        for k, v in s.items():
            table[(scenario, model)][(k, arm)].append(v)
    if as_json:
        return
    arms = sorted({p.parent.name for p in batch.glob("*/*") if (p / "arm").exists()})
    for (scenario, model), cells in sorted(table.items()):
        print(f"\n## {scenario} · {model}\n")
        print("| check | " + " | ".join(arms) + " |")
        print("| --- |" + " --- |" * len(arms))
        for k in dict.fromkeys(k for k, _ in cells):
            row = []
            for arm in arms:
                vals = [v for v in cells.get((k, arm), []) if v is not None]
                n = len(cells.get((k, arm), []))
                if not n:
                    row.append("")
                elif k in ("seconds", "turns", "commits_after_seed", "impl_dispatches", "review_dispatches", "caught_total",
                           "fixed_total", "review_dollars", "review_requests", "review_calls_per_request", "review_seconds"):
                    row.append(f"{sorted(vals)}" if vals else "n/a")
                else:
                    row.append(f"{sum(vals):g}/{len(vals)}" if vals else f"n/a ({n})")
            print(f"| {k} | " + " | ".join(row) + " |")


if __name__ == "__main__":
    main()
