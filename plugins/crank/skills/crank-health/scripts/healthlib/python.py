"""Python analyzers: the commands, ownership rule and routing `references/python.md` states."""

from __future__ import annotations

import json
import os
import re
from pathlib import Path

from . import inventory as inv
from .runner import Failed, Metric, Row, Run, Unavailable, batches, parse_json, sarif_results

LANGUAGE = "python"
CEILING = 15
RUFF_DEFAULT = '[lint]\nselect = ["E4", "E7", "E9", "F"]\n'
TY_ADVISORY = {"unresolved-import", "import-not-found", "missing-typeshed-stub"}
PYRIGHT_ADVISORY = {
    "reportMissingImports",
    "reportMissingModuleSource",
    "reportMissingTypeStubs",
    "reportAttributeAccessIssue",
}
BANDIT_SECRETS = {"B105", "B106", "B107"}
BANDIT_LEVEL = {"HIGH": "error", "MEDIUM": "warning", "LOW": "info"}
VULTURE_LINE = re.compile(r"^(.*?):(\d+): (.*) \((\d+)% confidence(?:, \d+ lines?)?\)\s*$")

OWNABLE = ("ruff", "ty", "pyright", "mypy", "vulture", "complexipy", "bandit", "cosmic-ray")

# tool -> (dedicated config files, [tool.<name>] table, distribution)
OWNERSHIP = {
    "ruff": (("ruff.toml", ".ruff.toml"), "ruff", "ruff"),
    "ty": (("ty.toml",), "ty", "ty"),
    "pyright": (("pyrightconfig.json",), "pyright", "pyright"),
    "mypy": (("mypy.ini", ".mypy.ini"), "mypy", "mypy"),
    "vulture": ((), "vulture", "vulture"),
    "complexipy": (("complexipy.toml", ".complexipy.toml"), "complexipy", "complexipy"),
    "bandit": ((".bandit", "bandit.yaml", "bandit.yml"), "bandit", "bandit"),
    "cosmic-ray": (("cosmic-ray.toml",), "cosmic-ray", "cosmic-ray"),
}


def owned(repo: Path, project: inv.Project) -> dict[str, str]:
    """Ownership = a `[tool.<name>]` table, a dedicated config file, or the package in a
    declared dependency list, ancestors included."""
    found = {}
    for tool, (configs, table, dist) in OWNERSHIP.items():
        evidence = (
            inv.python_tool_table(repo, project.dir, table)
            or (configs and inv.find_config(repo, project.dir, configs))
            or inv.python_dependency(repo, project.dir, dist)
        )
        if evidence:
            found[tool] = evidence
    return found


def has_config(repo: Path, project: inv.Project, tool: str) -> str | None:
    """A config the tool will read, as opposed to a bare dependency entry."""
    configs, table, _ = OWNERSHIP[tool]
    return inv.python_tool_table(repo, project.dir, table) or (
        inv.find_config(repo, project.dir, configs) if configs else None
    )


def find_venv(repo: Path, project: inv.Project) -> Path | None:
    for here in inv.ancestry(project.dir):
        for name in (".venv", "venv", "env"):
            candidate = repo / here / name
            if (candidate / "bin" / "python").exists():
                return candidate
    active = os.environ.get("VIRTUAL_ENV")
    if active and (Path(active) / "bin" / "python").exists():
        return Path(active)
    return None


def plan(run: Run, project: inv.Project) -> list[Row]:
    files = [run.abs(f) for f in project.files.get(LANGUAGE, [])]
    if not files:
        return []
    venv = find_venv(run.repo, project)
    project.facts["virtualenv"] = str(venv) if venv else "none"
    ctx = _Context(run, project, files, venv)
    rows = [
        ctx.ruff_check(),
        ctx.ruff_format(),
        *ctx.types(),
        ctx.vulture(),
        ctx.complexipy(),
        ctx.bandit(),
        ctx.deep("test quality", "cosmic-ray", owned_only=True),
    ]
    return [r for r in rows if r is not None]


class _Context:
    def __init__(self, run: Run, project: inv.Project, files: list[str], venv: Path | None):
        self.run, self.project, self.files, self.venv = run, project, files, venv
        self.cwd = run.repo / project.dir

    def row(self, category: str, tool: str, **kw) -> Row:
        categories = (category,) if isinstance(category, str) else tuple(category)
        return Row(project=self.project.dir, language=LANGUAGE, categories=categories, tool=tool, **kw)

    def binary(self, row: Row, tool: str, dist: str | None = None, *, config: str | None) -> list[str]:
        """argv prefix for a tool, and the provenance that goes with it."""
        dist = dist or tool
        how = f"repo config ({config})" if config else "default config"
        local = self.venv / "bin" / tool if self.venv else None
        if tool in self.project.owned and local and local.exists():
            row.provenance = f"{how}, repo binary"
            argv = [str(local)]
        else:
            self.run.need("uv")
            row.provenance = f"{how}, ephemeral"
            argv = self.run.uvx(dist, tool)
        return argv

    def resolve(self, row: Row, tool: str, dist: str | None = None, *, config: str | None) -> list[str] | None:
        try:
            argv = self.binary(row, tool, dist, config=config)
        except Unavailable as exc:
            row.unavailable(str(exc))
            return None
        return argv

    def stamp(self, row: Row, argv: list[str], flag: str = "--version") -> None:
        row.version = self.run.version(" ".join(argv), [*argv, flag], cwd=self.run.scratch_dir())
        if argv[0] == "uvx":
            self.run.pin_uvx(argv[-1], row.version)

    # --- lint and format ---------------------------------------------------------------

    def ruff_check(self) -> Row:
        row = self.row(("lint", "security"), "ruff check")
        config = has_config(self.run.repo, self.project, "ruff")
        argv = self.resolve(row, "ruff", config=config)
        if argv is None:
            return row

        def job(row: Row) -> None:
            self.stamp(row, argv)
            extra = []
            if not config:
                default = self.run.config_dir() / "ruff.toml"
                default.write_text(RUFF_DEFAULT)
                extra = ["--config", str(default)]
            records = []
            for batch in batches(self.files):
                done = self.run.exec(
                    row, [*argv, "check", "--output-format", "json", "--no-cache", "--exit-zero", *extra, *batch], cwd=self.cwd
                )
                part = parse_json(done.stdout)
                if not isinstance(part, list):
                    raise Failed(done.first_error)
                records += part
            for record in records:
                record.pop("fix", None)
                code = record.get("code") or record.get("name") or "invalid-syntax"
                syntax = code == "invalid-syntax" or code.startswith("E9")
                security = bool(re.fullmatch(r"S\d+", code))
                graded = bool(config) or syntax or code.startswith("F")
                row.add(
                    self.run.rel(record.get("filename", "")),
                    (record.get("location") or {}).get("row", 0),
                    "security" if security else "lint",
                    code,
                    "error" if syntax else "warning",
                    record.get("message", ""),
                    graded=graded,
                    reason="" if graded else "default config: style rule",
                )
            self.run.save(row, "ruff-check.json", _dump(records))

        row.job = job
        return row

    def ruff_format(self) -> Row:
        row = self.row("format", "ruff format")
        config = has_config(self.run.repo, self.project, "ruff")
        argv = self.resolve(row, "ruff", config=config)
        if argv is None:
            return row

        def job(row: Row) -> None:
            self.stamp(row, argv)
            records, missing = [], 0
            for batch in batches(self.files):
                done = self.run.exec(row, [*argv, "format", "--check", "--no-cache", "--output-format", "json", *batch], cwd=self.cwd)
                part = parse_json(done.stdout)
                if not isinstance(part, list):
                    raise Failed(done.first_error)
                records += part
            failing = set()
            for record in records:
                record.pop("fix", None)  # the reformatted source: megabytes, and every secret in it
                path = self.run.rel(record.get("filename", ""))
                if record.get("code") == "io":
                    missing += 1
                elif record.get("code") == "unformatted":
                    if path not in failing:
                        row.add(path, (record.get("location") or {}).get("row", 1), "format", "unformatted", "warning", "File would be reformatted")
                    failing.add(path)
                else:
                    row.notes.append(f"{path}: {record.get('code')}: {record.get('message', '')}"[:200])
            row.metrics["format"] = Metric(len(failing), len(self.files) - missing, "files")
            self.run.save(row, "ruff-format.json", _dump(records))

        row.job = job
        return row

    # --- types -------------------------------------------------------------------------

    def types(self) -> list[Row]:
        mypy = self.mypy()
        default = self.pyright() if self.venv else self.ty()
        if mypy.job is not None and default.job is not None:
            default.standby_behind = "mypy"
            default.provenance += ", standby behind mypy"
        return [default, mypy]

    def ty(self) -> Row:
        row = self.row("types", "ty")
        config = has_config(self.run.repo, self.project, "ty")
        argv = self.resolve(row, "ty", config=config)
        if argv is None:
            return row

        def job(row: Row) -> None:
            self.stamp(row, argv)
            records = []
            for batch in batches(self.files):
                done = self.run.exec(
                    row,
                    [*argv, "check", "--output-format", "gitlab", "--exit-zero", "--no-progress", "--color", "never", *batch],
                    cwd=self.cwd,
                )
                part = parse_json(done.stdout)
                if not isinstance(part, list):
                    raise Failed(done.first_error)
                records += part
            for record in records:
                rule = record.get("check_name", "")
                location = record.get("location") or {}
                begin = (location.get("positions") or {}).get("begin") or location.get("lines") or {}
                error = record.get("severity") in ("major", "critical", "blocker")
                advisory = not config and rule in TY_ADVISORY
                row.add(
                    self.run.rel(location.get("path", ""), self.cwd),
                    begin.get("line") or begin.get("begin") or 0,
                    "types",
                    rule,
                    "error" if error else "info",
                    record.get("description", "").removeprefix(rule + ": "),
                    graded=error and not advisory,
                    reason="default config: import resolution, no virtualenv" if advisory else ("" if error else "warning"),
                )
            self.run.save(row, "ty.json", _dump(records))

        row.job = job
        return row

    def pyright(self) -> Row:
        row = self.row("types", "pyright")
        config = has_config(self.run.repo, self.project, "pyright")
        how = f"repo config ({config})" if config else "default config"
        local = self.venv / "bin" / "pyright"
        if local.exists():
            argv, row.provenance = [str(local)], f"{how}, repo binary"
        elif self.run.which("pyright"):
            argv, row.provenance = [self.run.which("pyright")], f"{how}, system binary"
        elif self.run.which("uv"):
            argv, row.provenance = self.run.uvx("pyright"), f"{how}, ephemeral"
        else:
            return row.unavailable("uv not on PATH: brew install uv")

        def job(row: Row) -> None:
            self.stamp(row, argv)
            diagnostics, analyzed = [], 0
            for batch in batches(self.files):
                done = self.run.exec(row, [*argv, "--outputjson", "--pythonpath", str(self.venv / "bin" / "python"), *batch], cwd=self.cwd)
                doc = parse_json(done.stdout)
                if not isinstance(doc, dict) or "generalDiagnostics" not in doc:
                    raise Failed(done.first_error)
                diagnostics += doc["generalDiagnostics"]
                analyzed += (doc.get("summary") or {}).get("filesAnalyzed", 0)
            for record in diagnostics:
                rule = record.get("rule") or "error"
                error = record.get("severity") == "error"
                advisory = not config and rule in PYRIGHT_ADVISORY
                start = ((record.get("range") or {}).get("start") or {}).get("line")
                row.add(
                    self.run.rel(record.get("file", "")),
                    start + 1 if isinstance(start, int) else 0,  # pyright counts from 0
                    "types",
                    rule,
                    "error" if error else "info",
                    record.get("message", ""),
                    graded=error and not advisory,
                    reason="default config: import resolution" if advisory else ("" if error else record.get("severity", "")),
                )
            row.notes.append(f"{analyzed} files analyzed")
            self.run.save(row, "pyright.json", _dump(diagnostics))

        row.job = job
        return row

    def mypy(self) -> Row:
        row = self.row("types", "mypy")
        if "mypy" not in self.project.owned:
            return row.skip("not owned (never imposed)")
        config = has_config(self.run.repo, self.project, "mypy") or _setup_cfg_section(self.run.repo, self.project, "mypy")
        local = self.venv / "bin" / "mypy" if self.venv else None
        if local and local.exists():
            argv, row.provenance = [str(local)], f"repo config ({config or 'none'}), repo binary"
        elif self.venv is None:
            return row.unavailable("mypy is not installed and the project has no virtualenv")
        elif self.run.which("uv"):
            argv, row.provenance = self.run.uvx("mypy"), f"repo config ({config or 'none'}), ephemeral"
        else:
            return row.unavailable("uv not on PATH: brew install uv")

        def job(row: Row) -> None:
            self.stamp(row, argv)
            config_file = str(self.run.repo / config.split(" ")[0]) if config else ""
            command = [*argv, "--output=json", "--cache-dir", str(self.run.scratch_dir("mypy-cache", self.project.slug))]
            command += [f"--config-file={config_file}"]
            if self.venv:
                command += ["--python-executable", str(self.venv / "bin" / "python")]
            done = self.run.exec(row, [*command, *self.files], cwd=self.cwd)
            records = [r for r in map(parse_json, done.stdout.splitlines()) if isinstance(r, dict)]
            if not records and done.code not in (0, 1):
                raise Failed(done.first_error)
            for record in records:
                if record.get("severity") == "note":
                    continue
                row.add(
                    self.run.rel(record.get("file", ""), self.cwd),
                    record.get("line", 0),
                    "types",
                    record.get("code") or "error",
                    "error",
                    record.get("message", ""),
                )
            self.run.save(row, "mypy.jsonl", done.stdout)

        row.job = job
        return row

    # --- dead code, complexity, security -----------------------------------------------

    def vulture(self) -> Row:
        row = self.row("dead code", "vulture")
        config = has_config(self.run.repo, self.project, "vulture")
        argv = self.resolve(row, "vulture", config=config)
        if argv is None:
            return row

        def job(row: Row) -> None:
            self.stamp(row, argv)
            # one invocation: splitting the list invents dead code at the seams
            done = self.run.exec(row, [*argv, "--min-confidence", "60", *self.files], cwd=self.cwd)
            if done.code not in (0, 3):
                raise Failed(done.first_error)
            for line in done.stdout.splitlines():
                if not (m := VULTURE_LINE.match(line)):
                    continue
                path, lineno, message, confidence = m.group(1), int(m.group(2)), m.group(3), int(m.group(4))
                kind = re.sub(r"\s+", "-", re.split(r" '", message)[0].strip())
                graded = confidence >= 90
                finding = row.add(
                    self.run.rel(path, self.cwd),
                    lineno,
                    "dead code",
                    kind,
                    "warning" if graded else "info",
                    f"{message} ({confidence}% confidence)",
                    graded=graded,
                    reason="" if graded else "confidence below 90%",
                )
                finding.data["confidence"] = confidence
            self.run.save(row, "vulture.txt", done.stdout)

        row.job = job
        return row

    def complexipy(self) -> Row:
        row = self.row("complexity", "complexipy")
        config = has_config(self.run.repo, self.project, "complexipy")
        argv = self.resolve(row, "complexipy", config=config)
        if argv is None:
            return row

        def job(row: Row) -> None:
            self.stamp(row, argv)
            # .complexipy_cache/ lands beside the cwd and cannot be disabled
            cwd = self.run.scratch_dir("complexipy", self.project.slug)
            functions, results = [], []
            for n, batch in enumerate(batches(self.files)):
                out = cwd / f"out{n}"
                done = self.run.exec(
                    row,
                    [*argv, "--quiet", "--max-complexity-allowed", str(CEILING), "--output", f"{out}/", "--output-format", "json,sarif", *batch],
                    cwd=cwd,
                )
                listed = parse_json(_read(out / "complexipy-results.json"))
                if not isinstance(listed, list):
                    raise Failed(done.first_error)
                functions += listed
                results += list(sarif_results(parse_json(_read(out / "complexipy-results.sarif"))))
            over = 0
            for rule, _level, message, uri, line in results:
                score = re.search(r"cognitive complexity of (\d+)", message)
                finding = row.add(self.run.rel(uri), line, "complexity", rule or "CC001", "warning", message)
                finding.data["score"] = int(score.group(1)) if score else ""
                over += 1
            row.metrics["complexity"] = Metric(over, len(functions), f"functions over {CEILING}")
            slim = [{k: f.get(k) for k in ("path", "function_name", "complexity")} for f in functions]
            self.run.save(row, "complexipy.json", _dump(slim))

        row.job = job
        return row

    def bandit(self) -> Row:
        row = self.row("security", "bandit")
        config = has_config(self.run.repo, self.project, "bandit")
        argv = self.resolve(row, "bandit", config=config)
        if argv is None:
            return row

        def job(row: Row) -> None:
            self.stamp(row, argv)
            results = []
            for batch in batches(self.files):
                done = self.run.exec(row, [*argv, "--format", "json", "-q", *batch], cwd=self.run.scratch_dir())
                doc = parse_json(done.stdout)
                if not isinstance(doc, dict) or "results" not in doc:
                    raise Failed(done.first_error)
                results += doc["results"]
            for record in results:
                record.pop("code", None)  # the source window: B105's is the credential
                rule = record.get("test_id", "")
                severity, confidence = record.get("issue_severity", ""), record.get("issue_confidence", "")
                message = record.get("issue_text", "")
                if rule in BANDIT_SECRETS:
                    message = record["issue_text"] = re.sub(r"'.*'|\".*\"", "'<redacted>'", message)
                secret = rule in BANDIT_SECRETS and confidence == "HIGH"
                graded = bool(config) or secret or "HIGH" in (severity, confidence)
                finding = row.add(
                    self.run.rel(record.get("filename", "")),
                    record.get("line_number", 0),
                    "security",
                    rule,
                    "critical" if secret else BANDIT_LEVEL.get(severity, "info"),
                    message,
                    graded=graded,
                    reason="" if graded else "default config: below HIGH severity and HIGH confidence",
                )
                finding.data.update(severity=severity, confidence=confidence)
            self.run.save(row, "bandit.json", _dump(results))

        row.job = job
        return row

    def deep(self, category: str, tool: str, *, owned_only: bool) -> Row | None:
        row = self.row(category, tool)
        if owned_only and tool not in self.project.owned:
            return row.skip("not owned (never imposed)")
        if not self.run.deep:
            return row.skip("needs --deep")
        return row.skip("deep tool: run it from references/python.md")


def _setup_cfg_section(repo: Path, project: inv.Project, section: str) -> str | None:
    for here in inv.ancestry(project.dir):
        path = repo / here / "setup.cfg"
        try:
            if re.search(rf"^\[{section}\]", path.read_text(errors="replace"), re.M):
                return "setup.cfg" if here == "." else f"{here}/setup.cfg"
        except OSError:
            continue
    return None


def _read(path: Path) -> str:
    try:
        return path.read_text(errors="replace")
    except OSError:
        return ""


def _dump(value) -> str:
    return json.dumps(value, indent=1)
