"""Go analyzers: the commands, gates and routing `references/go.md` states."""

from __future__ import annotations

import json
import os
import re
from pathlib import Path

from . import inventory as inv
from .runner import BUDGET_SLOW, Failed, Metric, Row, Run, Unavailable, batches, first_json_line, not_on_path, ok_findings, parse_json

LANGUAGE = "go"
CEILING = 15
OWNABLE = ("golangci-lint", "gremlins")
BROKEN_GRAPH = ("cannot find module providing package", "no required module provides", "import lookup disabled")
GOSEC_LEVEL = {"HIGH": "error", "MEDIUM": "warning", "LOW": "info"}
VULN_LABELS = {2: "symbol-reachable", 1: "imported-no-call", 0: "not-imported"}
MODULES = {
    "staticcheck": ("honnef.co/go/tools", "honnef.co/go/tools/cmd/staticcheck"),
    "golangci-lint": ("github.com/golangci/golangci-lint/v2", "github.com/golangci/golangci-lint/v2/cmd/golangci-lint"),
    "gocognit": ("github.com/uudashr/gocognit", "github.com/uudashr/gocognit/cmd/gocognit"),
    "gosec": ("github.com/securego/gosec/v2", "github.com/securego/gosec/v2/cmd/gosec"),
    "govulncheck": ("golang.org/x/vuln", "golang.org/x/vuln/cmd/govulncheck"),
}
OWNERSHIP = {
    "golangci-lint": (".golangci.yml", ".golangci.yaml", ".golangci.toml", ".golangci.json"),
    "gremlins": (".gremlins.yaml", ".gremlins.yml"),
}


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
    names = [
        (("types", "dead code", "lint"), "staticcheck"),
        ("lint", "go vet"),
        ("lint", "golangci-lint"),
        ("format", "gofmt"),
        ("complexity", "gocognit"),
        ("security", "gosec"),
        ("security", "govulncheck"),
        ("test quality", "gremlins"),
    ]
    rows = {tool: ctx.row(categories, tool) for categories, tool in names}
    if "golangci-lint" not in project.owned:
        rows["golangci-lint"].skip("not owned (never imposed)")
    rows["gremlins"].skip_deep("go.md", owned="gremlins" in project.owned, deep=run.deep)
    _wire(ctx, rows)
    if not (run.repo / project.dir / "go.mod").is_file():
        for tool in ("staticcheck", "go vet", "golangci-lint", "gocognit", "gosec", "govulncheck"):
            if rows[tool].job is not None:
                rows[tool].unavailable("no go.mod in the project directory")
    return list(rows.values())


def _wire(ctx: _Context, rows: dict[str, Row]) -> None:
    """Give every row not already skipped its job, or the reason the Go gate refused."""
    gate = ctx.gate()
    for tool, row in rows.items():
        if row.state == "skipped":
            continue
        if gate:
            row.unavailable(gate)
            continue
        row.budget = BUDGET_SLOW
        row.provenance = "default config, system binary" if tool in ("go vet", "gofmt") else "default config, ephemeral"
        row.job = getattr(ctx, tool.replace(" ", "_").replace("-", "_"))
    if rows["golangci-lint"].job is not None:
        rows["golangci-lint"].provenance = f"repo config ({ctx.project.owned['golangci-lint']}), ephemeral"
        if rows["staticcheck"].job is not None:
            rows["staticcheck"].stand_by("golangci-lint")


class _Context:
    def __init__(self, run: Run, project: inv.Project, files: list[str]):
        self.run, self.project, self.files = run, project, files
        self.dir = run.repo / project.dir
        self.mine = set(project.every_file)
        self.env = {"GOFLAGS": "-mod=readonly", "GOMODCACHE": os.path.expanduser("~/go/pkg/mod")}

    def row(self, categories, tool: str) -> Row:
        return Row(project=self.project.dir, language=LANGUAGE, categories=categories, tool=tool)

    def gate(self) -> str:
        """Empty when Go 1.25+ answers from this directory; otherwise the reason."""
        if not self.run.which("go"):
            return not_on_path("go")
        version = self.run.version(f"go:{self.dir}", ["go", "version"], cwd=self.dir, pattern=r"go(\d+\.\d+(?:\.\d+)?)")
        found = re.search(r"(\d+)\.(\d+)", version)
        if not found or (int(found.group(1)), int(found.group(2))) < (1, 25):
            return f"go {version or '?'} is below 1.25: https://go.dev/dl"
        self.project.facts["go"] = version.removeprefix("go")
        return ""

    def tool(self, row: Row, name: str) -> list[str]:
        """`go run <import path>@<version>`, with `latest` resolved once per run."""
        module, package = MODULES[name]
        if module not in self.run.pins:
            with self.run.lock("gomod:" + module):
                if module not in self.run.pins:
                    done = self.run.exec(
                        None, ["go", "list", "-m", "-f", "{{.Version}}", f"{module}@latest"], cwd=self.run.scratch_dir(), env={"GOFLAGS": ""}
                    )
                    version = done.stdout.strip()
                    if done.code != 0 or not version.startswith("v"):
                        raise Unavailable(f"go could not resolve {module}: {done.first_error}")
                    self.run.pins[module] = version
        row.version = self.run.pins[module].lstrip("v")
        return ["go", "run", f"{package}@{self.run.pins[module]}"]

    def go(self, row: Row, argv: list[str]):
        return self.run.exec(row, argv, cwd=self.dir, env=self.env)

    def staticcheck(self, row: Row) -> None:
        done = self.go(row, [*self.tool(row, "staticcheck"), "-f", "json", "./..."])
        records = [r for r in map(parse_json, done.stdout.splitlines()) if isinstance(r, dict)]
        if not records and done.code != 0 and _real_stderr(done.stderr):
            raise Failed(_real_stderr(done.stderr))
        for record in records:
            code, message = record.get("code", ""), record.get("message", "")
            if code == "compile" and any(marker in message for marker in BROKEN_GRAPH):
                raise Failed(f"module graph is broken, refusing a partial run: {message[:200]}")
            location = record.get("location") or {}
            path = self.run.rel(location.get("file", ""), self.dir)
            if re.fullmatch(r"U\d+", code):
                row.add(path, location.get("line", 0), "dead code", code, "warning", message)
            elif code == "compile":
                row.add(path, location.get("line", 0), "types", code, "error", message)
            else:
                row.add(path, location.get("line", 0), "lint", code, "warning", message)
        self.run.save(row, "staticcheck.jsonl", done.stdout)

    def go_vet(self, row: Row) -> None:
        row.version = self.project.facts.get("go", "")
        done = self.go(row, ["go", "vet", "-json", "./..."])
        text = done.stderr + "\n" + done.stdout
        documents = _json_documents(text)
        if done.code != 0 and not any(documents):
            raise Failed(_real_stderr(done.stderr) or f"exit {done.code}")
        for analyzer, item in _vet_diagnostics(documents):
            path, _, rest = str(item.get("posn", "")).partition(":")
            row.add(self.run.rel(path, self.dir), rest.split(":")[0] if rest else "", "lint", analyzer, "warning", item.get("message", ""))
        self.run.save(row, "go-vet.json", json.dumps(documents, indent=1))

    def golangci_lint(self, row: Row) -> None:
        done = self.go(row, [*self.tool(row, "golangci-lint"), "run", "--output.json.path", "stdout"])
        doc = first_json_line(done.stdout, "Issues")
        if doc is None:
            raise Failed(_real_stderr(done.stderr) or f"exit {done.code}, no JSON line carrying Issues")
        for issue in doc.get("Issues") or []:
            position = issue.get("Pos") or {}
            issue.pop("SourceLines", None)
            row.add(self.run.rel(position.get("Filename", ""), self.dir), position.get("Line", 0), "lint", issue.get("FromLinter", ""), "warning", issue.get("Text", ""))
        self.run.save(row, "golangci-lint.json", json.dumps(doc.get("Issues") or [], indent=1))

    def gofmt(self, row: Row) -> None:
        row.version = self.project.facts.get("go", "")
        failing = []
        for batch in batches([self.project.rel(f) for f in self.files]):  # files, never a directory
            done = self.go(row, ["gofmt", "-l", *batch])
            if done.code != 0 and not done.stdout.strip():
                raise Failed(done.first_error)
            failing += [line.strip() for line in done.stdout.splitlines() if line.strip()]
        for path in failing:
            row.add(self.run.rel(path, self.dir), "", "format", "unformatted", "warning", "File would be reformatted")
        row.metrics["format"] = Metric(len(failing), len(self.files), "files")
        self.run.save(row, "gofmt.txt", "".join(p + "\n" for p in failing))

    def gocognit(self, row: Row) -> None:
        # -over -1 keeps zero-scored functions in the output, which is the denominator
        done = self.go(row, [*self.tool(row, "gocognit"), "-json", "-over", "-1", "."])
        records = parse_json(done.stdout)
        if not isinstance(records, list):
            raise Failed(_real_stderr(done.stderr) or f"exit {done.code}")
        counted = over = 0
        for record in records:
            position = record.get("Pos") or {}
            path = self.run.rel(position.get("Filename", ""), self.dir)
            if path not in self.mine:
                continue
            counted += 1
            score = record.get("Complexity", 0)
            if score > CEILING:
                over += 1
                finding = row.add(
                    path, position.get("Line", 0), "complexity", "cognitive-complexity", "warning",
                    f"{record.get('FuncName', '?')} has cognitive complexity {score} (ceiling {CEILING})",
                )
                finding.data["score"] = score
        row.metrics["complexity"] = Metric(over, counted, f"functions over {CEILING}")
        self.run.save(row, "gocognit.json", done.stdout)

    def gosec(self, row: Row) -> None:
        done = self.go(row, [*self.tool(row, "gosec"), "-fmt=json", "./..."])
        doc = parse_json(done.stdout)
        if not isinstance(doc, dict) or "Issues" not in doc:
            raise Failed(_real_stderr(done.stderr) or f"exit {done.code}")
        issues = doc.get("Issues") or []
        if not issues and doc.get("Golang errors"):
            raise Failed("gosec could not load the packages: " + str(next(iter(doc["Golang errors"])))[:200])
        row.version = str(doc.get("GosecVersion") or row.version).lstrip("v") if doc.get("GosecVersion") not in (None, "dev") else row.version
        for issue in issues:
            issue.pop("code", None)  # the source window: G101's is the credential
            rule = issue.get("rule_id", "")
            finding = row.add(
                self.run.rel(issue.get("file", ""), self.dir),
                int(str(issue.get("line", "0")).split("-")[0] or 0),
                "security",
                rule,
                "critical" if rule == "G101" else GOSEC_LEVEL.get(issue.get("severity", ""), "info"),
                "hardcoded credential; value redacted" if rule == "G101" else issue.get("details", ""),
            )
            finding.data.update(severity=issue.get("severity", ""), confidence=issue.get("confidence", ""))
        self.run.save(row, "gosec.json", json.dumps(doc, indent=1))

    def govulncheck(self, row: Row) -> None:
        done = self.go(row, [*self.tool(row, "govulncheck"), "-json", "./..."])
        documents = _json_documents(done.stdout)
        if not documents:
            raise Failed(_real_stderr(done.stderr) or f"exit {done.code}")
        aliases, verdicts = _vuln_verdicts(documents)
        for osv_id, (rank, frame) in sorted(verdicts.items()):
            self._vulnerability(row, osv_id, rank, frame, aliases.get(osv_id, []))
        slim = [d for d in documents if "finding" in d or "config" in d]
        self.run.save(row, "govulncheck.json", json.dumps(slim, indent=1))

    def _vulnerability(self, row: Row, osv_id: str, rank: int, frame: dict, aliases: list[str]) -> None:
        label = VULN_LABELS[rank]
        reachable = rank == 2
        position = frame.get("position") or {}
        module = f"{frame.get('module', '?')}@{frame.get('version', '?')}"
        if position.get("filename"):
            path, line = self.run.rel(position.get("filename", ""), self.dir), position.get("line", "")
        else:
            path, line = ("go.mod" if self.project.dir == "." else f"{self.project.dir}/go.mod"), ""
        finding = row.add(
            path,
            line,
            "security",
            label,
            "error" if reachable else "info",
            f"{osv_id} in {module}: {label}" + (f"; fixed in {frame['fixed']}" if frame.get("fixed") else "; no fixed version"),
            graded=reachable,
            reason="the vulnerable symbol is never called",
        )
        finding.data.update(ids=",".join([osv_id, *aliases]), verdict=label)


def _vet_diagnostics(documents: list[dict]):
    """(analyzer, diagnostic) from `go vet -json`: package -> analyzer -> list of diagnostics."""
    packages = [analyzers for document in documents for analyzers in document.values() if isinstance(analyzers, dict)]
    for analyzers in packages:
        for analyzer, items in analyzers.items():
            if isinstance(items, list):
                yield from ((analyzer, item) for item in items)


def _vuln_verdicts(documents: list[dict]) -> tuple[dict[str, list[str]], dict[str, tuple[int, dict]]]:
    """Each advisory's aliases, and the deepest trace govulncheck reached for it as
    (rank, frame): 2 a called symbol, 1 an imported package, 0 the module only."""
    entries = [document["osv"] for document in documents if isinstance(document.get("osv"), dict)]
    aliases = {entry.get("id", ""): entry.get("aliases") or [] for entry in entries}
    verdicts: dict[str, tuple[int, dict]] = {}
    for finding in (document["finding"] for document in documents if isinstance(document.get("finding"), dict)):
        frame = (finding.get("trace") or [{}])[0]
        rank = 2 if frame.get("function") else 1 if frame.get("package") else 0
        if rank >= verdicts.get(finding.get("osv", ""), (-1, {}))[0]:
            verdicts[finding.get("osv", "")] = (rank, {**frame, "fixed": finding.get("fixed_version", "")})
    return aliases, verdicts


def join_vulnerabilities(rows: list[Row]) -> None:
    """govulncheck's reachability decides an osv-scanner Go advisory; the two never both grade."""
    verdicts = _reachability(rows)
    if not verdicts:
        return
    covered = set()
    for finding in ok_findings(rows, "osv-scanner"):
        ids = [i for i in _ids(finding) if i in verdicts]
        if not ids:
            continue
        covered.update(ids)
        if finding.graded and not any(verdicts[i] for i in ids):
            finding.demote("govulncheck: the vulnerable symbol is never called")
    for finding in ok_findings(rows, "govulncheck"):
        if finding.graded and set(_ids(finding)) & covered:
            finding.demote("duplicate of osv-scanner/vulnerable-dependency")


def _reachability(rows: list[Row]) -> dict[str, bool]:
    """Per advisory id or alias, whether govulncheck found a vulnerable symbol called."""
    verdicts: dict[str, bool] = {}
    for finding in ok_findings(rows, "govulncheck"):
        for osv_id in _ids(finding):
            verdicts[osv_id] = verdicts.get(osv_id, False) or finding.rule.endswith("/symbol-reachable")
    return verdicts


def _ids(finding) -> list[str]:
    return str(finding.data.get("ids", "")).split(",")


def _real_stderr(stderr: str) -> str:
    skip = ("go: downloading", "go: extracting", "go: finding", "exit status")
    lines = [l.strip() for l in stderr.splitlines() if l.strip() and not l.startswith(skip)]
    return lines[0][:300] if lines else ""


def _json_documents(text: str) -> list[dict]:
    """Several JSON documents printed one after another, with other lines between them."""
    decoder, found, at = json.JSONDecoder(), [], 0
    while (start := text.find("{", at)) >= 0:
        try:
            value, end = decoder.raw_decode(text, start)
        except ValueError:
            at = start + 1
            continue
        if isinstance(value, dict):
            found.append(value)
        at = end
    return found
