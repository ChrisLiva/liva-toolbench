#!/usr/bin/env python3
"""score.py [--json] <batch-dir>: mechanical checks per crank-lite phase run, then rates per arm.

A check scores 1 or 0, a count is averaged, and a check that does not apply to the run's
scenario scores n/a. Judgment checks (destination confirmed first, one round per turn, the
readback's shape) need a transcript reader: run.sh writes each run's transcript.md.
"""
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import extract  # noqa: E402

NEXT_PHASE = {"brainstorm": "SPEC.md", "spec": "PLAN.md", "plan": "lite-execute/SKILL.md"}
CATALOGUE = [r"absen", r"permission|EACCES|EPERM", r"stale", r"destr|delet", r"limit|large|size", r"interrupt|concurren|partial|crash", r"trust|valid|ownership"]


def turns_of(run):
    out = []
    for t in sorted(run.glob("turns/*.jsonl"), key=lambda p: int(p.stem)):
        lines = t.read_text(encoding="utf-8", errors="replace").splitlines()
        is_codex = any('"thread_id"' in l or '"item.completed"' in l for l in lines[:5])
        out.append((is_codex, list((extract.codex_events if is_codex else extract.claude_events)(lines))))
    return out


def plan_review_dispatches(run):
    """The inputs of a Claude stream's orchestrator Agent or Task calls naming the plan review or merge brief, in stream order."""
    out = []
    for t in sorted(run.glob("turns/*.jsonl"), key=lambda p: int(p.stem)):
        for line in t.read_text(encoding="utf-8", errors="replace").splitlines():
            try:
                ev = json.loads(line)
            except ValueError:
                continue
            if ev.get("type") != "assistant" or ev.get("parent_tool_use_id"):
                continue
            for part in ev.get("message", {}).get("content", []):
                if part.get("type") == "tool_use" and part.get("name") in ("Agent", "Task"):
                    inp = part.get("input") or {}
                    if re.search(r"PLAN-(REVIEW|MERGE)-BRIEF", json.dumps(inp)):
                        out.append(inp)
    return out


def reviewer_dispatched(dispatches):
    """Whether any plan review dispatch names the plan review brief."""
    return int(any("PLAN-REVIEW-BRIEF" in json.dumps(d) for d in dispatches))


def plan_stages(body):
    """The rows of the plan's Stages table whose first cell is a number, or 0 with no Stages table."""
    m = re.search(r"^## Stages\b.*?(?=^## |\Z)", body, re.M | re.S)
    return len(re.findall(r"^\|\s*\d+\s*\|", m.group(0), re.M)) if m else 0


def review_shape(dispatches, stages):
    """1 when the dispatches match the review shape the plan's stage count calls for, else 0."""
    prompts = [str(d.get("prompt", "")) for d in dispatches]
    shards = [(i, m.group(1)) for i, p in enumerate(prompts) for m in [re.search(r"^\s*Shard:\s*([ABX])\b", p, re.M)] if m]
    if stages < 2:
        return int(sum("PLAN-REVIEW-BRIEF" in p for p in prompts) == 1 and not any("Shard:" in p for p in prompts))
    merges = [i for i, p in enumerate(prompts) if "PLAN-MERGE-BRIEF" in p]
    return int(sorted(s for _, s in shards) == ["A", "B", "X"] and len(merges) == 1 and merges[0] > max(i for i, _ in shards))


def score(run):
    scenario = (run / "arm").read_text().split()[0]
    phase = scenario.split("-")[0]
    artifact_name = (run / "artifact").read_text().strip()
    turns = turns_of(run)
    is_codex = any(c for c, _ in turns)
    texts = ["\n".join(b for k, b in ev if k == "text") for _, ev in turns]
    tools = ["\n".join(b for k, b in ev if k == "tool") for _, ev in turns]
    after = run / "crank-after"
    artifact = next(iter(after.glob(f"*/{artifact_name}")), None) if after.exists() else None
    body = artifact.read_text() if artifact else ""
    written_at = next((i for i, tl in enumerate(tools) if artifact_name in tl and re.search(r"\[(Write|Edit)\]|file_change|cat >|tee |apply_patch", tl)), len(turns))
    before = range(min(written_at + 1, len(turns)))
    pre_text = "\n".join(texts[i] for i in before)
    status = [l for l in (run / "status.txt").read_text().splitlines() if l.strip()]
    s = {
        "turns": len(turns),
        "artifact_written": int(artifact is not None),
        "artifact_sections": len(re.findall(r"^#{2,3} ", body, re.M)),
        "artifact_grounding": int(bool(re.search(r"^#{2,3} .*Grounding", body, re.M))),
        "question_rounds": sum(1 for i in before if "❓" in texts[i]),
        "questions_asked": len(re.findall("❓", pre_text)),
        "recommend_lines": len(re.findall("➡️", pre_text)),
        "lookup_dispatches": sum(len(re.findall(r"\[(Agent|Task)\]|spawn_agent", tools[i])) for i in before),
        "prototype_mentions": len(re.findall(r"\b(prototype|mock|variants?)\b", pre_text, re.I)),
        "prototype_built": int(any(after.glob("*/prototype/*"))) if after.exists() else 0,
        "next_phase_loaded": int(any(NEXT_PHASE[phase] in tl for tl in tools)),
        "source_untouched": int(not status),
        "vocabulary_read": int(any("VOCABULARY.md" in tl for tl in tools)) if phase in ("spec", "plan") else None,
        "failure_catalogue": sum(bool(re.search(p, body, re.I)) for p in CATALOGUE) if phase == "spec" else None,
    }
    if phase == "plan":
        dispatches = [] if is_codex else plan_review_dispatches(run)
        stages = plan_stages(body)
        s["review_dispatched"] = None if is_codex else reviewer_dispatched(dispatches)
        s["plan_stages"] = stages
        s["review_shape"] = None if is_codex else review_shape(dispatches, stages)
        s["review_tiers"] = None if is_codex else [f"{d.get('model')}/{d.get('effort')}" for d in dispatches]
    else:
        s["review_dispatched"] = None
    return s


def main(args):
    as_json = "--json" in args
    batch = Path([a for a in args if a != "--json"][0])
    per = defaultdict(lambda: defaultdict(list))
    for arm_file in sorted(batch.glob("*/*/arm")):
        run = arm_file.parent
        s = score(run)
        s["run"] = f"{run.parent.name}/{run.name}"
        if as_json:
            print(json.dumps(s))
        scenario = (run / "arm").read_text().split()[0]
        per[scenario][run.parent.name].append(s)
    if as_json:
        return
    for scenario, arms in per.items():
        print(f"\n{scenario}")
        print("  check".ljust(26) + "".join(a.rjust(14) for a in arms))
        keys = [k for k in next(iter(arms.values()))[0] if k != "run"]
        for k in keys:
            row = f"  {k}".ljust(26)
            for runs in arms.values():
                vals = [r.get(k) for r in runs if r.get(k) is not None]
                if any(isinstance(v, list) for v in vals):
                    row += "--json".rjust(14)
                elif not vals:
                    row += "n/a".rjust(14)
                elif set(vals) <= {0, 1} and k not in ("turns", "question_rounds", "questions_asked", "recommend_lines", "lookup_dispatches", "prototype_mentions", "artifact_sections", "failure_catalogue", "plan_stages"):
                    row += f"{sum(vals)}/{len(vals)}".rjust(14)
                else:
                    row += f"{sum(vals) / len(vals):.1f}".rjust(14)
            print(row)


if __name__ == "__main__":
    main(sys.argv[1:])
