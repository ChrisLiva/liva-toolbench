"""C# analyzers: the quick profile's one tool, and the rows `references/csharp.md` keeps
for `--deep`. Lint, types, complexity and dead code all need MSBuild, which runs the
project's own build logic."""

from __future__ import annotations

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
    found = {}
    for here in inv.ancestry(project.dir):
        tools = inv.read_json(str(repo / here / ".config" / "dotnet-tools.json")) or {}
        if "dotnet-stryker" in (tools.get("tools") or {}):
            found["stryker.net"] = ".config/dotnet-tools.json" if here == "." else f"{here}/.config/dotnet-tools.json"
            break
    if "stryker.net" not in found:
        for manifest in project.manifests:
            try:
                if manifest.endswith(".csproj") and re.search(r'PackageReference\s+Include="(dotnet-)?stryker', (repo / manifest).read_text(errors="replace"), re.I):
                    found["stryker.net"] = f"{manifest} PackageReference"
            except OSError:
                continue
    return found


def plan(run: Run, project: inv.Project) -> list[Row]:
    files = project.files.get(LANGUAGE, [])
    if not files:
        return []

    def row(categories, tool: str) -> Row:
        categories = (categories,) if isinstance(categories, str) else tuple(categories)
        return Row(project=project.dir, language=LANGUAGE, categories=categories, tool=tool)

    cwd = run.repo / project.dir
    fmt = row("format", "dotnet format whitespace")
    build = row(("types", "lint", "complexity"), "dotnet build + NetAnalyzers")
    dead = row("dead code", "roslynator find-symbol")
    mutation = row("test quality", "stryker.net")
    deep = "deep tool: run it from references/csharp.md"
    build.skip(deep if run.deep else "needs --deep: MSBuild executes project build logic")
    dead.skip(deep if run.deep else "needs --deep: MSBuild executes project build logic")
    if "stryker.net" not in project.owned:
        mutation.skip("not owned (never imposed)")
    else:
        mutation.skip(deep if run.deep else "needs --deep")

    if not run.which("dotnet"):
        fmt.unavailable("dotnet not on PATH: https://dotnet.microsoft.com/download")
        return [fmt, build, dead, mutation]
    version = run.version(f"dotnet:{cwd}", ["dotnet", "--version"], cwd=cwd, env=ENV)
    major = re.match(r"(\d+)", version)
    if not major or int(major.group(1)) < 10:
        fmt.unavailable(f"dotnet SDK {version or '?'} is below 10: https://dotnet.microsoft.com/download")
        return [fmt, build, dead, mutation]
    project.facts["dotnet"] = version
    fmt.version = version
    fmt.provenance = "repo config (.editorconfig), system binary"
    nested = [q.dir for q in run.inv.projects if q.dir != project.dir and inv.is_within(q.dir, project.dir)]

    def job(fmt: Row) -> None:
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

    fmt.job = job
    return [fmt, build, dead, mutation]
