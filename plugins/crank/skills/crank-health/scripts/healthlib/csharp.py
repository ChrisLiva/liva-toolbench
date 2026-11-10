"""C# analyzers: the quick profile's one tool, and the rows `references/csharp.md` keeps
for `--deep`. Lint, types, complexity and dead code all need MSBuild, which runs the
project's own build logic."""

from __future__ import annotations

import functools
import json
import re
from pathlib import Path

from . import inventory as inv
from .runner import Failed, Metric, Row, Run, parse_json

LANGUAGE = "csharp"
OWNABLE = ("stryker.net",)
ENV = {
    "DOTNET_CLI_TELEMETRY_OPTOUT": "1",
    "DOTNET_NOLOGO": "1",
    "DOTNET_SKIP_FIRST_TIME_EXPERIENCE": "1",
    "DOTNET_CLI_UI_LANGUAGE": "en",
}


def owned(repo: Path, project: inv.Project) -> dict[str, str]:
    evidence = _stryker_tool(repo, project.dir) or _stryker_reference(repo, project.manifests)
    return {"stryker.net": evidence} if evidence else {}


def _stryker_tool(repo: Path, project_dir: str) -> str:
    """The nearest `.config/dotnet-tools.json` that declares dotnet-stryker."""
    for here in inv.ancestry(project_dir):
        tools = inv.read_json(str(repo / here / ".config" / "dotnet-tools.json")) or {}
        if "dotnet-stryker" in (tools.get("tools") or {}):
            return ".config/dotnet-tools.json" if here == "." else f"{here}/.config/dotnet-tools.json"
    return ""


def _stryker_reference(repo: Path, manifests: list[str]) -> str:
    """The last .csproj that references a Stryker package."""
    found = ""
    for manifest in manifests:
        if manifest.endswith(".csproj") and _references_stryker(repo / manifest):
            found = f"{manifest} PackageReference"
    return found


def _references_stryker(csproj: Path) -> bool:
    try:
        return bool(re.search(r'PackageReference\s+Include="(dotnet-)?stryker', csproj.read_text(errors="replace"), re.I))
    except OSError:
        return False


def plan(run: Run, project: inv.Project) -> list[Row]:
    files = project.files.get(LANGUAGE, [])
    if not files:
        return []
    cwd = run.repo / project.dir
    fmt = _row(project, "format", "dotnet format whitespace")
    build = _row(project, ("types", "lint", "complexity"), "dotnet build + NetAnalyzers")
    dead = _row(project, "dead code", "roslynator find-symbol")
    mutation = _row(project, "test quality", "stryker.net")
    deep = "deep tool: run it from references/csharp.md"
    build.skip(deep if run.deep else "needs --deep: MSBuild executes project build logic")
    dead.skip(deep if run.deep else "needs --deep: MSBuild executes project build logic")
    mutation.skip_deep("csharp.md", owned="stryker.net" in project.owned, deep=run.deep)
    rows = [fmt, build, dead, mutation]

    version, refused = _dotnet(run, cwd)
    if refused:
        fmt.unavailable(refused)
        return rows
    project.facts["dotnet"] = version
    fmt.version = version
    fmt.provenance = "repo config (.editorconfig), system binary"
    nested = [q.dir for q in run.inv.projects if q.dir != project.dir and inv.is_within(q.dir, project.dir)]
    fmt.job = functools.partial(_format, run, project, files, nested)
    return rows


def _row(project: inv.Project, categories, tool: str) -> Row:
    return Row(project=project.dir, language=LANGUAGE, categories=categories, tool=tool)


def _dotnet(run: Run, cwd: Path) -> tuple[str, str]:
    """The SDK version answering from `cwd`, and the reason dotnet format cannot run, if any."""
    if not run.which("dotnet"):
        return "", "dotnet not on PATH: https://dotnet.microsoft.com/download"
    version = run.version(f"dotnet:{cwd}", ["dotnet", "--version"], cwd=cwd, env=ENV)
    major = re.match(r"(\d+)", version)
    if not major or int(major.group(1)) < 10:
        return version, f"dotnet SDK {version or '?'} is below 10: https://dotnet.microsoft.com/download"
    return version, ""


def _format(run: Run, project: inv.Project, files: list[str], nested: list[str], fmt: Row) -> None:
    cwd = run.repo / project.dir
    out = run.scratch_dir("dotnet-format", project.slug)
    exclude = ["bin", "obj", *(str(Path(n).relative_to(project.dir)) if project.dir != "." else n for n in nested)]
    done = run.exec(
        fmt,
        ["dotnet", "format", "whitespace", cwd, "--folder", "--verify-no-changes", "--exclude", *exclude, "--report", out],
        cwd=cwd,
        env=ENV,
    )
    try:
        report = parse_json((out / "format-report.json").read_text(encoding="utf-8-sig"))
    except OSError:
        report = None
    if not isinstance(report, list):
        raise Failed(done.first_error)
    mine = set(project.every_file)
    failing = set()
    for entry in report:
        path = run.rel(entry.get("FilePath", ""), cwd)
        changes = entry.get("FileChanges") or []
        if path not in mine or not changes or path in failing:
            continue
        failing.add(path)
        first = changes[0]
        fmt.add(path, first.get("LineNumber", ""), "format", "whitespace", "warning", f"{len(changes)} whitespace change(s); first: {first.get('FormatDescription', '')}")
    fmt.metrics["format"] = Metric(len(failing), len(files), "files")
    run.save(fmt, "dotnet-format.json", json.dumps(report, indent=1))
