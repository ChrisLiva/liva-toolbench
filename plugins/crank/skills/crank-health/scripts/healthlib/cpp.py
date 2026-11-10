"""C and C++ analyzers: the commands, ownership rule and routing `references/cpp.md` states."""

from __future__ import annotations

import csv
import io
import re
import xml.etree.ElementTree as ET
from pathlib import Path

from . import inventory as inv
from .runner import BUDGET_SLOW, Failed, Metric, Row, Run, batches

LANGUAGE = "c-cpp"
CEILING = 15
OWNABLE = ("clang-format", "clang-tidy", "mull")
OWNERSHIP = {"clang-format": (".clang-format", "_clang-format"), "clang-tidy": (".clang-tidy",), "mull": ("mull.yml",)}
CPPCHECK_LINT = {"style", "performance", "portability"}
CPPCHECK_ABORT = {"unknownMacro", "syntaxError", "preprocessorErrorDirective", "internalAstError", "cppcheckError"}
FORMAT_LINE = re.compile(r"^(.+?):\d+:\d+: (?:error|warning): .*\[-Wclang-format-violations\]")


def owned(repo: Path, project: inv.Project) -> dict[str, str]:
    found = {}
    for tool, patterns in OWNERSHIP.items():
        if evidence := inv.find_config(repo, project.dir, patterns):
            found[tool] = evidence
    return found


def plan(run: Run, project: inv.Project) -> list[Row]:
    files = project.files.get(LANGUAGE, [])
    if not files:
        return []
    ctx = _Context(run, project, files)
    cppcheck = ctx.row(("security", "lint", "dead code"), "cppcheck", budget=BUDGET_SLOW)
    lizard = ctx.row("complexity", "lizard")
    fmt = ctx.row("format", "clang-format")
    tidy = ctx.row(("types", "lint", "complexity"), "clang-tidy")
    mull = ctx.row("test quality", "mull")
    if run.which("uv"):
        cppcheck.provenance = lizard.provenance = "default config, ephemeral"
        cppcheck.job, lizard.job = ctx.cppcheck, ctx.lizard
        if not ctx.sources:
            cppcheck.skip("nothing to scan (headers only)")
    else:
        for row in (cppcheck, lizard):
            row.unavailable("uv not on PATH: brew install uv")
    _wire_format(ctx, fmt)
    if run.deep:
        tidy.skip("deep tool: run it from references/cpp.md")
    else:
        tidy.skip("needs --deep: a compile database comes from the repo's build configure")
    mull.skip_deep("cpp.md", owned="mull" in project.owned, deep=run.deep)
    return [cppcheck, lizard, fmt, tidy, mull]


def _wire_format(ctx: _Context, fmt: Row) -> None:
    run, project = ctx.run, ctx.project
    if "clang-format" not in project.owned:
        fmt.skip("not owned (never imposed)")
    elif run.which("xcrun"):
        fmt.provenance, fmt.job = f"repo config ({project.owned['clang-format']}), system binary", ctx.clang_format
    elif run.which("uv"):
        fmt.provenance, fmt.job = f"repo config ({project.owned['clang-format']}), ephemeral", ctx.clang_format
    else:
        fmt.unavailable("uv not on PATH: brew install uv")


def _route(rule: str, severity: str) -> tuple[str, str] | None:
    """The category and level a cppcheck result files under, or None for one the row drops."""
    if rule == "unusedFunction":
        return "dead code", "warning"
    if severity in ("error", "warning"):
        return "security", severity
    if severity in CPPCHECK_LINT:
        return "lint", "warning"
    return None


class _Context:
    def __init__(self, run: Run, project: inv.Project, files: list[str]):
        self.run, self.project = run, project
        self.dir = run.repo / project.dir
        self.mine = set(project.every_file)
        self.sources = [f for f in files if inv.ext_of(f) in inv.C_SOURCES]
        self.headers = [f for f in files if inv.ext_of(f) in inv.C_HEADERS]

    def row(self, categories, tool: str, **kw) -> Row:
        return Row(project=self.project.dir, language=LANGUAGE, categories=categories, tool=tool, **kw)

    def listing(self, name: str, files: list[str]) -> Path:
        path = self.run.scratch_dir("lists") / f"{self.project.slug}-{name}.txt"
        path.write_text("".join(self.run.abs(f) + "\n" for f in files))
        return path

    def cppcheck(self, row: Row) -> None:
        argv = self.run.uvx("cppcheck-py", "cppcheck")
        row.version = self.run.version("cppcheck", [*argv, "--version"])
        report = self.run.raw_path(row, "cppcheck.xml")
        include = []
        for header_dir in sorted({inv.parent(h) for h in self.headers}):
            include += ["-I", self.run.repo / header_dir]
        extra = self.run.extra("cppcheck", self.project.dir)
        done = self.run.exec(
            row,
            [
                *argv, "-q", "--enable=all", "--xml", f"--output-file={report}",
                f"--cppcheck-build-dir={self.run.scratch_dir('cppcheck', self.project.slug)}", "-j", "4",
                "--suppress=missingIncludeSystem", *extra, *include, f"--file-list={self.listing('sources', self.sources)}",
            ],
            cwd=self.dir,
        )
        try:
            root = ET.parse(report).getroot()
        except (OSError, ET.ParseError):
            raise Failed(done.first_error) from None
        row.raw.append(str(report.relative_to(self.run.run_dir)))
        if extra:
            row.provenance += f" + {' '.join(extra)}"
        unresolved, aborted = self._cppcheck_results(row, root)
        row.notes.append(f"{unresolved} unresolved (information rows: missing includes, configurations cppcheck gave up on)")
        if aborted:
            sample = ", ".join(f"{path} ({rule})" for path, rule in sorted(aborted.items())[:5])
            row.notes.append(
                f"check: cppcheck aborted in {len(aborted)} files and measured nothing in the translation units past them: {sample}. "
                'Name the macros\' library in <run-dir>/overrides.json ({"cppcheck": ["--library=boost"]}) and rerun --tool cppcheck'
            )

    def _cppcheck_results(self, row: Row, root: ET.Element) -> tuple[int, dict[str, str]]:
        """File the report's results on the row; return the count of unresolved
        information rows and the first aborting rule per file."""
        unresolved, aborted = 0, {}
        for error in root.iter("error"):
            rule, severity = error.get("id", ""), error.get("severity", "")
            location = error.find("location")
            path = self.run.rel(location.get("file", ""), self.dir) if location is not None else ""
            line = int(location.get("line", "0") or 0) if location is not None else 0
            if rule in CPPCHECK_ABORT:
                aborted.setdefault(path, rule)
            if path and path not in self.mine:
                continue
            if severity == "information":
                unresolved += rule != "checkersReport"
                continue
            if routed := _route(rule, severity):
                category, level = routed
                row.add(path, line, category, rule, level, error.get("msg", ""))
        return unresolved, aborted

    def lizard(self, row: Row) -> None:
        argv = self.run.uvx("lizard")
        row.version = self.run.version("lizard", [*argv, "--version"])
        self.run.pin_uvx("lizard", row.version)
        done = self.run.exec(row, [*argv, "--csv", "-l", "cpp", "--input_file", self.listing("all", self.sources + self.headers)], cwd=self.dir)
        if not done.stdout.strip() and (done.code != 0 or not (self.sources or self.headers)):
            raise Failed(done.first_error)
        counted = over = 0
        for record in csv.reader(io.StringIO(done.stdout)):
            # NLOC,CCN,token,PARAM,length,location,file,function,long_name,start,end
            if len(record) < 10 or not record[1].isdigit():
                continue
            counted += 1
            ccn = int(record[1])
            if ccn > CEILING:
                over += 1
                finding = row.add(
                    self.run.rel(record[6], self.dir), int(record[9] or 0), "complexity", "ccn", "warning",
                    f"{record[7]} has cyclomatic complexity {ccn} (ceiling {CEILING})",
                )
                finding.data["score"] = ccn
        row.metrics["complexity"] = Metric(over, counted, f"functions over {CEILING} (cyclomatic)")
        row.notes.append("lizard measures cyclomatic complexity, not cognitive")
        self.run.save(row, "lizard.csv", done.stdout)

    def clang_format(self, row: Row) -> None:
        argv = ["xcrun", "clang-format"] if self.run.which("xcrun") else self.run.uvx("clang-format")
        row.version = self.run.version("clang-format", [*argv, "--version"])
        targets = self.sources + self.headers
        failing, output = set(), []
        for batch in batches([self.run.abs(f) for f in targets], 100):
            done = self.run.exec(
                row, [*argv, "--style=file", "--fallback-style=none", "--dry-run", "-Werror", "--ferror-limit=1", *batch], cwd=self.dir
            )
            output.append(done.stderr)
            matched = [m.group(1) for line in done.stderr.splitlines() if (m := FORMAT_LINE.match(line))]
            if done.code != 0 and not matched:  # exit 1 names a file; without one it crashed
                raise Failed(done.first_error)
            failing.update(self.run.rel(path, self.dir) for path in matched)
        for path in sorted(failing):
            row.add(path, "", "format", "unformatted", "warning", "File would be reformatted")
        row.metrics["format"] = Metric(len(failing), len(targets), "files")
        self.run.save(row, "clang-format.txt", "".join(p + "\n" for p in sorted(failing)))
