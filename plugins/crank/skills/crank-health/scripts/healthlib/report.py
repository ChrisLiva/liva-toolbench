"""What a scan leaves in the run dir: inventory.md, tools.md, findings, summaries, grades.

`results.json` is the machine copy every later command reloads; the markdown files are
what the agent reads.
"""

from __future__ import annotations

import json
from pathlib import Path

from . import grade as grading
from . import inventory as inv
from .runner import CATEGORIES, Finding, Metric, Row

LANGUAGE_ORDER = ("js-ts", "python", "go", "csharp", "c-cpp")


def _cell(text) -> str:
    return str(text).replace("|", "\\|").replace("\n", " ")


def _table(header: list[str], rows: list[list]) -> list[str]:
    out = ["| " + " | ".join(header) + " |", "| " + " | ".join("---" for _ in header) + " |"]
    out += ["| " + " | ".join(_cell(c) for c in row) + " |" for row in rows]
    return out


# --- inventory.md ------------------------------------------------------------------------


def inventory_md(inventory: inv.Inventory, path_facts: dict, extra: list[str]) -> str:
    out = [f"repo: {inventory.repo} · head: {inventory.head} · dirty: {inventory.dirty} paths", *extra, ""]
    for project in inventory.projects:
        out += _project_md(project)
    out.append("## repo-wide")
    present = [f"{name} {version}" for name, version in path_facts.items() if version]
    missing = [name for name, version in path_facts.items() if not version]
    out.append("  on PATH: " + (", ".join(present) or "none"))
    out.append("  missing: " + (", ".join(missing) or "none"))
    out.append(f"  workflows: {len(inventory.workflows)} files" + _listing(inventory.workflows))
    out.append("  snapshots: " + (", ".join(inventory.snapshots) or "none by name"))
    out.append(f"  generated: {len(inventory.generated)} files by name or header" + _listing(inventory.generated))
    out.append("  lockfiles: " + (", ".join(inventory.lockfiles) or "none"))
    rest = sorted(inventory.unassessed.items(), key=lambda kv: (-kv[1], kv[0]))
    out.append("  unassessed: " + (" ".join(f"{ext}:{n}" for ext, n in rest[:16]) or "none"))
    out.append(f"  file list: scope.txt ({len(inventory.files)} files)")
    return "\n".join(out) + "\n"


def _project_md(project: inv.Project) -> list[str]:
    out = [f"## project {project.dir}"]
    if project.manifests:
        out.append("  manifests: " + ", ".join(project.manifests))
    if project.shell:
        return out + ["  workspace shell: no source of its own", ""]
    out += [_language_md(project, language) for language in LANGUAGE_ORDER if language in project.files]
    if project.assets:
        parts = [
            f"{kind} {len(paths)} files {project.asset_lines[kind]} lines ({project.asset_lines[kind] / 1000:.1f} KLOC)"
            for kind, paths in sorted(project.assets.items())
        ]
        out.append("  lint assets  " + "; ".join(parts))
    owned = ", ".join(f"{tool} ({why})" for tool, why in sorted(project.owned.items()))
    out.append("  owned: " + (owned or "none"))
    out.append("  unowned: " + (", ".join(sorted(project.unowned)) or "none"))
    out += [f"  {name}: {value}" for name, value in sorted(project.facts.items())]
    out.append("")
    return out


def _language_md(project: inv.Project, language: str) -> str:
    count, lines = len(project.files[language]), project.lines[language]
    line = f"  {language:<8} {count:>5} files {lines:>8} lines ({lines / 1000:.1f} KLOC)"
    if language in project.fixture_only:
        line += f"   every file under {project.fixture_only[language]}/: likely fixtures"
    return line


def _listing(paths: list[str], limit: int = 6) -> str:
    if not paths:
        return ""
    more = f", … {len(paths) - limit} more" if len(paths) > limit else ""
    return " (" + ", ".join(paths[:limit]) + more + ")"


# --- tools.md ----------------------------------------------------------------------------


def tools_md(meta: dict, rows: list[Row]) -> str:
    scope = "all projects" if not meta["selected"] else "--project " + " ".join(meta["selected"])
    only = "all" if len(meta["only"]) == len(CATEGORIES) else "--only " + ",".join(meta["only"])
    out = [
        "# Tools of record",
        "",
        f"Run dir `{meta['run_dir']}` · `{meta['repo']}` @ `{meta['head']}` · {meta['profile']} · scope: {scope} · categories: {only}",
        "",
    ]
    body = [
        [r.project, r.category, r.tool, r.version, r.provenance, r.scope if r.job or r.state == "ok" else "", _state(r)]
        for r in rows
    ]
    out += _table(["project", "category", "tool", "version", "provenance", "scope", "state"], body)
    out += ["", "## Commands", "", "Each row's commands as they ran: versions pinned, exit code and seconds beside them.", ""]
    for row in (r for r in rows if r.commands):
        out += [f"### {row.project} · {row.tool}", ""]
        for command in row.commands:
            out += _command_md(command)
    return "\n".join(out) + "\n"


def _command_md(command: dict) -> list[str]:
    code = "killed" if command["exit"] is None else f"exit {command['exit']}"
    runs = f" · {command['runs']} batches" if command.get("runs") else ""
    return ["```sh", f"cd {command['cwd']} && {command['command']}", "```", f"{code} · {command['seconds']} s{runs}", ""]


def _state(row: Row) -> str:
    if row.state in ("error", "timeout") and row.detail:
        return f"{row.state}: {row.detail}"
    return row.state


# --- findings ------------------------------------------------------------------------------


def findings_path(run_dir: Path, row: Row) -> Path:
    return run_dir / "findings" / row.folder / f"{row.slug}.tsv"


def write_findings(run_dir: Path, rows: list[Row]) -> None:
    for row in rows:
        path = findings_path(run_dir, row)
        if row.state != "ok":
            path.unlink(missing_ok=True)
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("".join(f.tsv() + "\n" for f in row.findings), encoding="utf-8")


def read_findings(run_dir: Path, row: Row) -> list[Finding]:
    try:
        lines = findings_path(run_dir, row).read_text(encoding="utf-8").splitlines()
    except OSError:
        return []
    return [f for f in map(Finding.parse, lines) if f is not None]


# --- summaries -----------------------------------------------------------------------------


def _counts(findings: list[Finding], status: str) -> str:
    mine = [f for f in findings if f.status == status]
    if not mine:
        return "0"
    by_level = {}
    for finding in mine:
        by_level[finding.severity] = by_level.get(finding.severity, 0) + 1
    order = ("critical", "error", "warning", "info")
    return ", ".join(f"{by_level[level]} {level}" for level in order if level in by_level) or str(len(mine))


def _metric(row: Row) -> str:
    if row.state != "ok":
        return row.detail
    if row.unmeasured:
        return "unmeasured: " + row.unmeasured
    parts = [f"{category}: {metric.text()}" if len(row.metrics) > 1 else metric.text() for category, metric in row.metrics.items()]
    return "; ".join(parts)


def summary_md(title: str, inventory_line: str, rows: list[Row]) -> str:
    out = [f"# Scan summary: {title}", "", inventory_line, "", "## Tools", ""]
    out += _table(["tool", "version", "provenance", "state", "graded", "advisory", "metric"], [_tool_cells(row) for row in rows])
    out += ["", "## Top rules (graded)", ""]
    rule_rows = _top_rules(rows)
    out += _table(["category", "tool/rule", "count", "files", "sample"], rule_rows) if rule_rows else ["none"]
    out += ["", "## Notes", ""]
    notes = [f"- {_tool_name(row)}: {note}" for row in rows for note in row.notes]
    out += notes or ["- none"]
    return "\n".join(out) + "\n"


def _tool_name(row: Row) -> str:
    """A repo-wide tool that ran per project carries the project beside its name."""
    return row.tool if row.language != "repo-wide" or row.project == "repo" else f"{row.tool} ({row.project})"


def _tool_cells(row: Row) -> list:
    provenance = row.provenance + (f" (stood down: {row.standby_behind} graded {row.category})" if row.stood_down else "")
    if row.state != "ok":
        return [_tool_name(row), row.version, provenance, row.state, "", "", _metric(row)]
    dropped = sum(1 for f in row.findings if f.dropped)
    advisory = _counts(row.findings, "advisory") + (f"; {dropped} dropped" if dropped else "")
    return [_tool_name(row), row.version, provenance, row.state, _counts(row.findings, "graded"), advisory, _metric(row)]


def _top_rules(rows: list[Row]) -> list[list]:
    tally: dict[tuple[str, str], list[Finding]] = {}
    for finding in (f for row in rows for f in row.findings if f.graded):
        tally.setdefault((finding.category, finding.rule), []).append(finding)
    top = sorted(tally.items(), key=lambda kv: (-len(kv[1]), kv[0]))[:15]
    return [
        [category, rule, len(found), len({f.file for f in found}), f"{found[0].file}:{found[0].line}" if found[0].line else found[0].file]
        for (category, rule), found in top
    ]


def write_summaries(run_dir: Path, projects: list[inv.ProjectRecord], rows: list[Row]) -> None:
    folder = run_dir / "summary"
    folder.mkdir(parents=True, exist_ok=True)
    for stale in folder.glob("*.md"):
        stale.unlink()
    for project in projects:
        _write_project_summaries(folder, project, rows)
    wide = [r for r in rows if r.language == "repo-wide"]
    if wide:
        total = sum(sum(p.lines.values()) for p in projects)
        files = sum(sum(p.files.values()) for p in projects)
        line = f"Inventory: {files} source files, {total} lines ({total / 1000:.1f} KLOC) across {len(projects)} project(s)"
        (folder / "repo-wide.md").write_text(summary_md("repo-wide · .", line, wide), encoding="utf-8")


def _write_project_summaries(folder: Path, project: inv.ProjectRecord, rows: list[Row]) -> None:
    for language, lines in project.lines.items():
        mine = [r for r in rows if r.project == project.dir and r.language == language]
        if not mine:
            continue
        count = project.files[language]
        line = f"Inventory: {count} files, {lines} lines ({lines / 1000:.1f} KLOC)"
        text = summary_md(f"{language} · {project.dir}", line, mine)
        (folder / f"{language}--{project.slug}.md").write_text(text, encoding="utf-8")


# --- grades.md -----------------------------------------------------------------------------


def grades_md(grades: list[grading.Grade], stage: str) -> str:
    units = list(dict.fromkeys(g.unit for g in grades))
    headline = grading.headline(grades)
    out = [f"# Grades ({stage})", ""]
    if headline:
        out += [f"Grades{' (rollup)' if headline == grading.ROLLUP else ''}: " + grading.line(grades, headline), ""]
    for unit in [headline, *[u for u in units if u != headline]]:
        if not unit:
            continue
        out += [f"## {'rollup' if unit == grading.ROLLUP else 'project ' + unit}", ""]
        mine = {g.category: g for g in grades if g.unit == unit}
        body = [[c, mine[c].letter or "not assessed", mine[c].basis] for c in CATEGORIES if c in mine]
        out += _table(["category", "grade", "basis"], body) + [""]
    return "\n".join(out)


# --- results.json --------------------------------------------------------------------------


def row_record(row: Row) -> dict:
    return {
        "project": row.project,
        "language": row.language,
        "categories": list(row.categories),
        "tool": row.tool,
        "version": row.version,
        "provenance": row.provenance,
        "scope": row.scope,
        "state": row.state,
        "detail": row.detail,
        "budget": row.budget,
        "seconds": round(row.seconds, 1),
        "metrics": {c: [m.numerator, m.denominator, m.unit] for c, m in row.metrics.items()},
        "commands": row.commands,
        "notes": row.notes,
        "raw": row.raw,
        "standby_behind": row.standby_behind,
        "stood_down": row.stood_down,
        "unmeasured": row.unmeasured,
        "reads_assets": row.reads_assets,
    }


def row_from(record: dict) -> Row:
    row = Row(
        project=record["project"],
        language=record["language"],
        categories=tuple(record["categories"]),
        tool=record["tool"],
    )
    for name in ("version", "provenance", "scope", "state", "detail", "budget", "seconds", "commands", "notes", "raw"):
        setattr(row, name, record[name])
    row.standby_behind, row.stood_down, row.reads_assets = record["standby_behind"], record["stood_down"], record["reads_assets"]
    row.unmeasured = record.get("unmeasured", "")
    row.metrics = {c: Metric(*m) for c, m in record["metrics"].items()}
    return row


def write_results(run_dir: Path, meta: dict, projects: list[inv.ProjectRecord], rows: list[Row]) -> None:
    doc = {"meta": meta, "projects": [p.to_json() for p in projects], "rows": [row_record(r) for r in rows]}
    (run_dir / "results.json").write_text(json.dumps(doc, indent=1), encoding="utf-8")


def read_results(run_dir: Path) -> tuple[dict, list[inv.ProjectRecord], list[Row]]:
    doc = json.loads((run_dir / "results.json").read_text(encoding="utf-8"))
    rows = [row_from(r) for r in doc["rows"]]
    for row in rows:
        row.findings = read_findings(run_dir, row)
    return doc["meta"], [inv.ProjectRecord.from_json(p) for p in doc["projects"]], rows
