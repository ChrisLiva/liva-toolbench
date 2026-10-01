#!/usr/bin/env python3
"""Score lite-execute smoke runs.

    python3 score.py <batch-dir>          # runs at <batch-dir>/<arm>/<scenario>-<model>-<rep>/
    python3 score.py --json <batch-dir>   # one JSON object per run instead of the table

Each check reads a run's orchestrator stream (events with no parent_tool_use_id), its
subagents' streams, and the repo and .crank/ state run.sh saved. A check scores 1 when
the run did what lite-execute's rules ask, 0 when it did not, and None when the run never
reached the point the check judges. The table prints each check's pass rate per arm.
"""

import json
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

SHA = re.compile(r"\b[0-9a-f]{7,40}\b")


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
    p = run / which / "csv-export" / "plan.md"
    return p.read_text(encoding="utf-8") if p.exists() else ""


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
        return "REVIEW-BRIEF" in p or bool(re.search(r"\breview", p, re.I) and re.search(r"\bdiff\b", p))
    reviewer = [(i, a) for i, a in agents if is_review(a)]
    impl = [(i, a) for i, a in agents if not is_review(a)]
    return impl, reviewer


def rate(hits, total):
    return None if total == 0 else round(hits / total, 2)


def common(run, items, events):
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
        "tiers_resolved_from_user": None if block is None else int("user CLAUDE.md" in subagents),
        "no_sleep_polling": int(not any("sleep" in bash_cmd(it) for it in items)),
    }


def score_fresh(run, items, events, block, s):
    impl, reviewer = dispatches(items)
    rev_idx = reviewer[0][0] if reviewer else len(items)
    shape = (preflight_line(block, "Shape") or "").lower()
    subagents = preflight_line(block, "Subagents") or ""
    std = re.search(r"standard = ([^(,·]+)", subagents)
    s["shape_sequential"] = None if block is None else int("sequential" in shape)
    s["standard_tier_opus"] = None if not std else int("opus" in std.group(1).lower())
    s["impl_dispatches"] = len(impl)
    s["impl_dispatch_per_task"] = int(len(impl) == 5)
    s["impl_model_opus"] = rate(sum("opus" in str(a.get("model", "")).lower() for _, a in impl), len(impl))
    s["brief_carries_constraints"] = rate(sum(bool(re.search(r"BOM|utf-8-sig", a.get("prompt", ""))) for _, a in impl), len(impl))
    s["brief_carries_defect_rules"] = rate(
        sum(bool(re.search(r"round-trip|mutation|IMPLEMENTER-BRIEF", a.get("prompt", ""), re.I)) for _, a in impl), len(impl))
    s["implementers_never_commit"] = int(not any("git commit" in c for c in subagent_bash(events)))
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
    s["reviewer_pointers"] = None if not reviewer else int(
        bool(re.search(r"/lite-execute/REVIEW-BRIEF\.md", reviewer[0][1].get("prompt", "")))
        and "git diff" in reviewer[0][1].get("prompt", ""))
    s["retro_written"] = int((run / "crank-after" / "csv-export" / "retro.md").exists())
    texts = " ".join(p for k, p in items if k == "text")
    s["stage_labels_in_replies"] = int(bool(re.search(r"Task \d+ \(stage \d of 2", texts)))
    s["final_report_shas"] = int(len(set(SHA.findall(final_text(events)))) >= 2)

    out = subprocess.run(["python3", "-m", "ledger", "export", "--out", str(run / "export.csv")],
                         cwd=run / "repo", capture_output=True, text=True)
    s["export_writes_bom"] = int(out.returncode == 0 and (run / "export.csv").exists()
                                 and (run / "export.csv").read_bytes()[:3] == b"\xef\xbb\xbf")
    t = subprocess.run(["python3", "-m", "unittest", "discover", "-s", "tests"], cwd=run / "repo",
                       capture_output=True, text=True)
    s["suite_green"] = int(t.returncode == 0)


def score_stop_if(run, items, events, block, s):
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


def score_spec_path(run, items, events, block, s):
    impl, reviewer = dispatches(items)
    same = all((run / "crank-before" / "csv-export" / n).read_bytes() == (run / "crank-after" / "csv-export" / n).read_bytes()
               for n in ("plan.md", "spec.md"))
    seed = (run / "seed-head").read_text().strip()
    s["refused"] = int(same and not impl and git(run, "rev-parse", "HEAD").strip() == seed
                       and not (run / "diff.txt").read_text().strip())
    s["recommends_plan_phase"] = int(bool(re.search(r"crank-lite plan|plan phase", final_text(events))))


def score(run):
    scenario, model = (run / "arm").read_text().split()
    events = load_events(run)
    items = orchestrator_items(events)
    block, s = common(run, items, events)
    {"fresh": score_fresh, "stop-if": score_stop_if, "spec-path": score_spec_path}[scenario](run, items, events, block, s)
    s["seconds"] = int((run / "seconds").read_text()) if (run / "seconds").exists() else None
    s["turns"] = int((run / "turn-count").read_text()) if (run / "turn-count").exists() else None
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
                elif k in ("seconds", "turns", "commits_after_seed", "impl_dispatches"):
                    row.append(f"{sorted(vals)}" if vals else "n/a")
                else:
                    row.append(f"{sum(vals):g}/{len(vals)}" if vals else f"n/a ({n})")
            print(f"| {k} | " + " | ".join(row) + " |")


if __name__ == "__main__":
    main()
