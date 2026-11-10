"""Running one analyzer: a budget, a recorded command, a state, and findings in one schema.

Every tool module builds `Row`s and hands each a `job`. A job that raises, times out or
cannot find its binary records a state on its row; it never stops the run.
"""

from __future__ import annotations

import json
import os
import re
import shlex
import shutil
import signal
import subprocess
import tempfile
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from collections.abc import Callable

from . import inventory as inv

CATEGORIES = ("security", "types", "dead code", "complexity", "duplication", "lint", "format", "test quality")
STATES = ("ok", "error", "not-available", "skipped", "timeout")
BUDGET = 120
BUDGET_SLOW = 300
BATCH = 200
SECRET = "<redacted>"

INSTALL_HINTS = {
    "uv": "brew install uv",
    "node": "brew install node",
    "go": "https://go.dev/dl (1.25+)",
    "dotnet": "https://dotnet.microsoft.com/download (SDK 10+)",
    "gitleaks": "brew install gitleaks",
    "opengrep": "brew install opengrep",
    "osv-scanner": "brew install osv-scanner",
    "cmake": "brew install cmake",
    "meson": "brew install meson",
}


class Unavailable(Exception):
    """The tool cannot run here; the message is the reason and the install hint."""


class Failed(Exception):
    """The tool ran and produced nothing usable; the message is stderr's first line."""


@dataclass
class Finding:
    """One row of a findings file:
    file  line  category  tool/rule  severity  verdict  message  flags

    `verdict` is `graded`, `advisory: <reason>` or `dropped: <reason>`. The scan writes the
    first two; triage rewrites the column, and `dropped` takes a row out of every count.
    `line` is empty for a finding about a whole file. `flags` carries what triage sorts on:
    path classes (`test`, `snapshot`, `generated`) and the numbers behind a message
    (`score=24`, `confidence=60`).
    """

    file: str
    line: int | str
    category: str
    rule: str
    severity: str
    status: str
    message: str
    reason: str = ""
    data: dict = field(default_factory=dict)
    flags: list[str] = field(default_factory=list)

    @property
    def graded(self) -> bool:
        return self.status == "graded"

    @property
    def dropped(self) -> bool:
        return self.status == "dropped"

    def demote(self, reason: str, status: str = "advisory") -> None:
        self.status, self.reason = status, reason

    def tsv(self) -> str:
        verdict = self.status + (": " + self.reason if self.reason and self.status != "graded" else "")
        notes = [*self.flags, *(f"{k}={v}" for k, v in self.data.items() if v != "")]
        cells = (self.file, str(self.line or ""), self.category, self.rule, self.severity, verdict, self.message)
        return "\t".join([*(one_line(c) for c in cells), " ".join(notes)])

    @classmethod
    def parse(cls, text: str) -> Finding | None:
        cells = text.rstrip("\n").split("\t")
        if len(cells) < 7:
            return None
        file, lineno, category, rule, severity, verdict, message = cells[:7]
        status, _, reason = verdict.partition(":")
        status = status.strip().lower()
        if status not in ("graded", "advisory", "dropped"):
            status, reason = "advisory", verdict
        flags = cells[7].split() if len(cells) > 7 else []
        return cls(file, lineno, category, rule, severity, status, message, reason.strip(), flags=flags)


def number(value: float) -> str:
    return str(int(value)) if float(value).is_integer() else f"{value:.1f}"


def one_line(text: str) -> str:
    return re.sub(r"\s+", " ", str(text)).strip()


@dataclass
class Metric:
    """A ratio a category grades on: files failing a formatter, functions over the ceiling."""

    numerator: float
    denominator: float
    unit: str

    @property
    def percent(self) -> float:
        return 100 * self.numerator / self.denominator if self.denominator else 0.0

    def text(self) -> str:
        return f"{number(self.numerator)} / {number(self.denominator)} {self.unit} ({self.percent:.2f}%)"


@dataclass
class Done:
    argv: list[str]
    cwd: str
    code: int | None
    seconds: float
    stdout: str
    stderr: str

    @property
    def first_error(self) -> str:
        for line in self.stderr.splitlines():
            if line.strip() and not line.startswith(("go: downloading", "go: extracting", "go: finding", "npm warn")):
                return one_line(line)[:300]
        return f"exit {self.code}, nothing on stderr"


@dataclass
class Row:
    """One (project x tool) line of `tools.md`, and everything its run produced."""

    project: str  # a project directory, or "repo" for the repo-wide tools
    language: str
    categories: tuple[str, ...]
    tool: str
    version: str = ""
    provenance: str = ""
    scope: str = "project"
    state: str = "pending"
    detail: str = ""
    budget: int = BUDGET
    metrics: dict[str, Metric] = field(default_factory=dict)
    findings: list[Finding] = field(default_factory=list)
    commands: list[dict] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    raw: list[str] = field(default_factory=list)
    standby_behind: str = ""
    stood_down: bool = False
    reads_assets: bool = False
    seconds: float = 0.0
    job: Callable[[Row], None] | None = None

    @property
    def category(self) -> str:
        return ", ".join(self.categories)

    @property
    def key(self) -> str:
        return f"{self.project}::{self.tool}"

    @property
    def slug(self) -> str:
        return re.sub(r"[^A-Za-z0-9._-]+", "-", self.tool)

    @property
    def folder(self) -> str:
        return "repo" if self.project == "repo" else ("root" if self.project == "." else self.project.replace("/", "-"))

    def skip(self, reason: str) -> Row:
        self.state, self.detail, self.provenance, self.job = "skipped", reason, f"skipped: {reason}", None
        return self

    def unavailable(self, reason: str) -> Row:
        self.state, self.detail, self.provenance, self.job = "not-available", reason, f"not available: {reason}", None
        return self

    def add(self, file, line, category, rule, severity, message, *, graded=True, reason="") -> Finding:
        finding = Finding(
            file,
            line if line else "",
            category,
            f"{self.tool.replace(' ', '-')}/{rule}",
            severity,
            "graded" if graded else "advisory",
            one_line(message)[:500],
            "" if graded else reason,
        )
        self.findings.append(finding)
        return finding


class Run:
    """One scan: where things are written, what is on PATH, and how commands run."""

    def __init__(self, inventory: inv.Inventory, run_dir: Path, *, deep=False, only=None, pins=None, budget_scale=1.0):
        self.inv = inventory
        self.repo = inventory.repo
        self.run_dir = run_dir
        self.scratch = run_dir / "scratch"
        self.raw = run_dir / "raw"
        self.temp: Path | None = None
        self.budget_scale = budget_scale
        self.deep = deep
        self.only = set(only or CATEGORIES)
        self.pins: dict[str, str] = dict(pins or {})
        self.rows: list[Row] = []
        self._locks: dict[str, threading.Lock] = {}
        self._guard = threading.Lock()
        self._which: dict[str, str | None] = {}
        self._versions: dict[str, str] = {}
        self._shared: dict[str, tuple[bool, object]] = {}

    # --- paths -------------------------------------------------------------------------

    def temp_dir(self, *parts: str) -> Path:
        """A directory outside the repo for mirrors and worktrees: a tool that honours
        `.gitignore` sees nothing under the run dir, which `.crank-health/.gitignore` hides."""
        with self._guard:
            if self.temp is None:
                self.temp = Path(tempfile.mkdtemp(prefix="crank-health-"))
        path = self.temp.joinpath(*parts)
        path.mkdir(parents=True, exist_ok=True)
        return path

    def cleanup(self) -> None:
        if self.temp is not None:
            shutil.rmtree(self.temp, ignore_errors=True)
            self.temp = None

    def scratch_dir(self, *parts: str) -> Path:
        path = self.scratch.joinpath(*parts)
        path.mkdir(parents=True, exist_ok=True)
        return path

    def config_dir(self, *parts: str) -> Path:
        """Where the skill's own default configs are written. They outlive scratch, so a
        command copied out of tools.md still runs after the report."""
        path = self.run_dir.joinpath("config", *parts)
        path.mkdir(parents=True, exist_ok=True)
        return path

    def raw_path(self, row: Row, name: str) -> Path:
        base = self.raw / row.folder
        base.mkdir(parents=True, exist_ok=True)
        return base / name

    def save(self, row: Row, name: str, text: str) -> Path:
        path = self.raw_path(row, name)
        path.write_text(text, encoding="utf-8", errors="replace")
        row.raw.append(str(path.relative_to(self.run_dir)))
        return path

    def abs(self, rel: str) -> str:
        return str(self.repo / rel)

    def rel(self, path: str, base: Path | str | None = None, root: Path | str | None = None) -> str:
        """Any path a tool printed, as a repo-relative one. `base` is what a relative path is
        relative to (the tool's cwd); `root` replaces the repo when the tool read a mirror."""
        if not path:
            return ""
        path = path.removeprefix("file://")
        root = root or self.repo
        full = Path(path) if os.path.isabs(path) else Path(base or root) / path
        try:
            return os.path.relpath(os.path.realpath(full), os.path.realpath(root)).replace(os.sep, "/")
        except ValueError:
            return path

    # --- PATH --------------------------------------------------------------------------

    def which(self, name: str) -> str | None:
        if name not in self._which:
            self._which[name] = shutil.which(name)
        return self._which[name]

    def need(self, name: str) -> str:
        found = self.which(name)
        if not found:
            raise Unavailable(f"{name} not on PATH: {INSTALL_HINTS.get(name, 'install ' + name)}")
        return found

    def lock(self, name: str) -> threading.Lock:
        with self._guard:
            return self._locks.setdefault(name, threading.Lock())

    def once(self, key: str, compute):
        """One run of a tool whose unit is a whole workspace, shared by every project in it."""
        with self.lock("once:" + key):
            if key not in self._shared:
                try:
                    self._shared[key] = (True, compute())
                except Exception as exc:
                    self._shared[key] = (False, exc)
            ok, value = self._shared[key]
        if not ok:
            raise value
        return value

    def extra(self, tool: str, project: str = "") -> list[str]:
        """Arguments the agent added for one tool in `<run-dir>/overrides.json`, a map of
        tool name to argument list: a knip `--config`, a cppcheck `--library=`. A
        `<tool>@<project dir>` key reaches one project and wins over the bare tool name."""
        doc = parse_json(_read_text(self.run_dir / "overrides.json")) or {}
        args = doc.get(f"{tool}@{project}", doc.get(tool)) or []
        return [str(a).replace("<run-dir>", str(self.run_dir)) for a in args] if isinstance(args, list) else []

    # --- commands ----------------------------------------------------------------------

    def env(self, extra: dict | None = None) -> dict:
        env = dict(os.environ)
        env.update(
            NO_COLOR="1",
            FORCE_COLOR="0",
            npm_config_update_notifier="false",
            npm_config_fund="false",
            npm_config_audit="false",
            PYTHONDONTWRITEBYTECODE="1",
        )
        if not env.get("UV_CACHE_DIR"):
            env.pop("UV_CACHE_DIR", None)  # uv rejects an empty value
        env.update(extra or {})
        return env

    def exec(self, row: Row | None, argv, *, cwd=None, env=None, budget=None, stdin=None, record=True) -> Done:
        argv = [str(a) for a in argv]
        cwd = str(cwd or self.scratch_dir())
        budget = int((budget or (row.budget if row else BUDGET)) * self.budget_scale)
        started = time.monotonic()
        try:
            proc = subprocess.Popen(
                argv,
                cwd=cwd,
                env=self.env(env),
                stdin=subprocess.PIPE if stdin is not None else subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                start_new_session=True,
            )
        except FileNotFoundError as exc:
            raise Unavailable(f"{argv[0]} not found") from exc
        try:
            out, err = proc.communicate(stdin.encode() if stdin is not None else None, timeout=budget)
        except subprocess.TimeoutExpired:
            try:
                os.killpg(proc.pid, signal.SIGKILL)
            except (ProcessLookupError, PermissionError):
                proc.kill()
            proc.communicate()
            if row is not None and record:
                self._record(row, argv, cwd, env, None, time.monotonic() - started)
            raise TimeoutError(f"killed after {budget} s") from None
        done = Done(
            argv,
            cwd,
            proc.returncode,
            time.monotonic() - started,
            out.decode("utf-8", "replace"),
            err.decode("utf-8", "replace"),
        )
        if row is not None and record:
            self._record(row, argv, cwd, env, done.code, done.seconds)
        return done

    def _record(self, row: Row, argv: list[str], cwd: str, env, code, seconds: float) -> None:
        """Keep the command as it ran. A long trailing file list goes to `lists/` and the
        record reads it back through xargs, so a batched tool is one runnable line."""
        head = list(argv)
        files = []
        while head and os.path.isfile(os.path.join(cwd, head[-1])):
            files.append(head.pop())
        prefix = "".join(f"{k}={shlex.quote(str(v))} " for k, v in (env or {}).items())
        if len(files) < 4:
            command = prefix + shlex.join(argv)
        else:
            listing = self.run_dir / "lists" / f"{row.folder}--{row.slug}.txt"
            listing.parent.mkdir(parents=True, exist_ok=True)
            known = listing.read_text().splitlines() if listing.exists() else []
            listing.write_text("".join(f + "\n" for f in dict.fromkeys([*known, *reversed(files)])))
            command = f"tr '\\n' '\\0' < {shlex.quote(str(listing))} | {prefix}xargs -0 {shlex.join(head)}"
        for earlier in row.commands:
            if earlier["command"] == command and earlier["cwd"] == cwd:
                earlier["seconds"] = round(earlier["seconds"] + seconds, 1)
                if code is None or (earlier["exit"] is not None and code > earlier["exit"]):
                    earlier["exit"] = code
                earlier["runs"] = earlier.get("runs", 1) + 1
                return
        row.commands.append({"cwd": cwd, "command": command, "exit": code, "seconds": round(seconds, 1)})

    def version(self, key: str, argv, *, cwd=None, env=None, pattern=r"\d+\.\d+(?:\.\d+)?(?:[-+.][0-9A-Za-z.]+)?") -> str:
        """The version a tool prints, probed once per run."""
        with self.lock("version:" + key):
            if key not in self._versions:
                try:
                    done = self.exec(None, argv, cwd=cwd, env=env, budget=BUDGET)
                    found = re.search(pattern, done.stdout + "\n" + done.stderr)
                    self._versions[key] = found.group(0) if found else ""
                except (Unavailable, TimeoutError):
                    self._versions[key] = ""
            return self._versions[key]

    # --- ephemeral runners -------------------------------------------------------------

    def npm_version(self, package: str, declared: str = "") -> str:
        """Pin `latest` to the number it means now, so every call in a run agrees. A version
        the repo's manifest declares wins over `latest`."""
        key = f"{package}@{declared}" if declared else package
        if key in self.pins:
            return self.pins[key]
        if declared:
            self.pins[key] = declared
            return declared
        self.need("node")
        with self.lock("npm:" + package):
            if package not in self.pins:
                done = self.exec(None, ["npm", "view", package, "version"], budget=60)
                version = done.stdout.strip().splitlines()[-1].strip() if done.stdout.strip() else ""
                if done.code != 0 or not re.fullmatch(r"[0-9][0-9A-Za-z.+-]*", version):
                    raise Unavailable(f"npm could not resolve {package}: {done.first_error}")
                self.pins[package] = version
        return self.pins[package]

    def npx(self, package: str, binary: str | None = None, declared: str = "") -> tuple[list[str], str]:
        """argv prefix for an ephemeral npm tool at a pinned version, and that version."""
        self.need("node")
        version = self.npm_version(package, declared)
        spec = f"{package}@{version}"
        if binary and binary != package:
            return ["npx", "--yes", "--package", spec, "--", binary], version
        return ["npx", "--yes", spec], version

    def uvx(self, dist: str, binary: str | None = None) -> list[str]:
        """argv prefix for an ephemeral PyPI tool, at the version an earlier scan pinned."""
        self.need("uv")
        pinned = self.pins.get("uv:" + dist)
        if pinned or (binary and binary != dist):
            return ["uvx", "--quiet", "--from", f"{dist}=={pinned}" if pinned else dist, binary or dist]
        return ["uvx", "--quiet", dist]

    def pin_uvx(self, dist: str, version: str) -> None:
        """Remember the version `latest` meant, for the base side of a PR scan and for reruns."""
        if re.fullmatch(r"\d+(\.\d+)+", version or ""):
            self.pins.setdefault("uv:" + dist, version)

    def warm(self, key: str, argv, *, cwd=None, env=None, budget=BUDGET_SLOW) -> None:
        """Install an ephemeral tool once, serially: two cold `npx` or `uvx` calls for the
        same package race on the shared cache."""
        with self.lock("warm:" + key):
            if key in self._versions:
                return
            self._versions[key] = ""
            self.exec(None, argv, cwd=cwd, env=env, budget=budget)


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def batches(items: list[str], size: int = BATCH):
    for start in range(0, len(items), size):
        yield items[start : start + size]


def parse_json(text: str):
    try:
        return json.loads(text)
    except ValueError:
        return None


def first_json_line(text: str, key: str):
    """The first line that parses as a JSON object carrying `key`: several tools print
    prose around one JSON line."""
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("{"):
            doc = parse_json(line)
            if isinstance(doc, dict) and key in doc:
                return doc
    doc = parse_json(text)
    return doc if isinstance(doc, dict) and key in doc else None


def sarif_results(doc):
    """(rule id, level, message, file uri, line) for every result in a SARIF document."""
    for run in (doc or {}).get("runs") or []:
        rules = {}
        driver = ((run.get("tool") or {}).get("driver")) or {}
        for rule in driver.get("rules") or []:
            rules[rule.get("id")] = rule
        for result in run.get("results") or []:
            rule_id = result.get("ruleId") or (result.get("rule") or {}).get("id") or ""
            level = result.get("level") or ((rules.get(rule_id) or {}).get("defaultConfiguration") or {}).get("level") or "warning"
            message = (result.get("message") or {}).get("text") or ""
            uri, line = "", 0
            for location in result.get("locations") or []:
                physical = location.get("physicalLocation") or {}
                uri = (physical.get("artifactLocation") or {}).get("uri") or ""
                line = (physical.get("region") or {}).get("startLine") or 0
                break
            yield rule_id, level, message, uri, line


def execute(run: Run, row: Row) -> None:
    """Run one row's job and settle its state, whatever the job does."""
    if row.job is None:
        return
    started = time.monotonic()
    try:
        row.job(row)
        if row.state == "pending":
            row.state = "ok"
    except Unavailable as exc:
        row.state, row.detail = "not-available", str(exc)
    except TimeoutError as exc:
        row.state, row.detail = "timeout", str(exc)
    except Failed as exc:
        row.state, row.detail = "error", str(exc)
    except Exception as exc:  # one tool never aborts the run
        row.state, row.detail = "error", f"{type(exc).__name__}: {one_line(exc)[:300]}"
    row.seconds = time.monotonic() - started
    if row.state != "ok":
        row.findings.clear()
        row.metrics.clear()
