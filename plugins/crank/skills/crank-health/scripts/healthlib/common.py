"""Repo-wide analyzers: the commands and routing `references/common.md` states.

They run over the selected directories whatever languages those hold. gitleaks and aislop
read a mirror of the inventory rather than the working tree, so a gitignored build tree,
an old checkout under a hidden directory or a `.env` never enters the scan.
"""

from __future__ import annotations

import json
import os
import re
import shutil
from pathlib import Path

from . import inventory as inv
from .runner import Failed, Metric, Row, Run, Unavailable, parse_json, sarif_results

LANGUAGE = "repo-wide"
JSCPD_FORMATS = "javascript,jsx,typescript,tsx,python,csharp,go,c,c-header,cpp,cpp-header"
JSCPD_SKIP = ("node_modules", "vendor", "dist", "build", "bin", "obj")
OFFLINE = ("no such host", "dial tcp", "i/o timeout", "TLS handshake timeout")
OSV_MANIFESTS = (inv.LOCKFILES - {"go.sum", "bun.lockb"}) | {"go.mod", "pom.xml", "gradle.lockfile", "pubspec.lock", "mix.lock"}
NPM_LOCKS = {"package-lock.json", "npm-shrinkwrap.json", "pnpm-lock.yaml", "yarn.lock", "bun.lock"}
ZIZMOR_LEVEL = {"High": "error", "Medium": "warning", "Low": "info", "Informational": "info", "Unknown": "info"}
ZIZMOR_DEMOTED = {"unpinned-uses", "unpinned-images"}
AISLOP_OWN = ("ai-slop/", "security/")
AISLOP_ELSEWHERE = {
    "complexity/": "the complexity category measures it",
    "code-quality/duplicate-block": "jscpd measures duplication",
    "security/vulnerable-dependency": "duplicate of osv-scanner",
}


def plan(run: Run) -> list[Row]:
    ctx = _Context(run)
    rows = [ctx.gitleaks(), ctx.osv_scanner(), ctx.zizmor(), ctx.opengrep(), *ctx.jscpd(), ctx.aislop()]
    return [r for r in rows if r is not None]


def row(categories, tool: str, project: str = "repo", **kw) -> Row:
    categories = (categories,) if isinstance(categories, str) else tuple(categories)
    return Row(project=project, language=LANGUAGE, categories=categories, tool=tool, scope="selected project dirs", **kw)


class _Context:
    def __init__(self, run: Run):
        self.run = run
        self.inv = run.inv
        self.repo = run.repo
        self.files = [f for f in self.inv.files if self.inv.in_selection(f)]

    def mirror(self, name: str) -> Path:
        """A copy of the in-scope files, outside the repo and deleted with the run's temp dir."""
        root = self.run.temp_dir(name)
        for rel in self.files:
            target = root / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(self.repo / rel, target)
        return root

    # --- secrets -----------------------------------------------------------------------

    def gitleaks(self) -> Row:
        r = row("security", "gitleaks")
        if not self.run.which("gitleaks"):
            return r.unavailable("brew install gitleaks")
        config = inv.find_config(self.repo, ".", (".gitleaks.toml",), local=True)
        r.provenance = (f"repo config ({config})" if config else "default config") + ", system binary"

        def job(r: Row) -> None:
            r.version = self.run.version("gitleaks", ["gitleaks", "version"])
            mirror = self.mirror("gitleaks")
            report = self.run.scratch_dir() / "gitleaks.json"
            ignore = ["--gitleaks-ignore-path", mirror] if (mirror / ".gitleaksignore").is_file() else []
            done = self.run.exec(
                r,
                ["gitleaks", "dir", "--no-banner", "--redact=100", "--report-format", "json", "--report-path", report, "--exit-code", "0", *ignore, mirror],
            )
            hits = parse_json(_read(report))
            report.unlink(missing_ok=True)
            if not isinstance(hits, list):
                raise Failed(done.first_error)
            grouped: dict[tuple[str, str], list[int]] = {}
            kept = []
            for hit in hits:
                rel = self.run.rel(hit.get("File", ""), mirror, mirror)
                grouped.setdefault((rel, hit.get("RuleID", "")), []).append(hit.get("StartLine") or 0)
                # the report's Match and Line fields hold the code around the secret
                kept.append({"File": rel, "RuleID": hit.get("RuleID"), "StartLine": hit.get("StartLine"), "Description": hit.get("Description")})
            for (rel, rule), lines in sorted(grouped.items()):
                lines.sort()
                finding = r.add(
                    rel,
                    lines[0],
                    "security",
                    rule,
                    "critical",
                    f"{len(lines)} hit(s) of rule {rule}; first at line {lines[0]}; values redacted",
                )
                finding.data["hits"] = len(lines)
            r.notes.append(f"scanned a mirror of the {len(self.files)} in-scope files; {len(hits)} hits")
            self.run.save(r, "gitleaks.json", json.dumps(kept, indent=1))

        r.job = job
        return r

    # --- vulnerable dependencies -------------------------------------------------------

    def osv_scanner(self) -> Row:
        r = row("security", "osv-scanner")
        if not self.run.which("osv-scanner"):
            return r.unavailable("brew install osv-scanner")
        locks = [f for f in self.files if _is_osv_manifest(f)]
        config = inv.find_config(self.repo, ".", ("osv-scanner.toml",), local=True)
        r.provenance = (f"repo config ({config})" if config else "default config") + ", system binary"
        if not locks:
            return r.skip("nothing to scan (no lockfile or manifest in scope)")

        def job(r: Row) -> None:
            r.version = self.run.version("osv-scanner", ["osv-scanner", "--version"])
            saved, failed = [], []
            for lock in locks:
                out = self.run.scratch_dir("osv") / (lock.replace("/", "__") + ".json")
                argv = ["osv-scanner", "scan", "source", "--format", "json", "--output-file", out, "--verbosity", "error"]
                argv += ["--config", self.repo / config] if config else []
                done = self.run.exec(r, [*argv, "--lockfile", self.repo / lock])
                if any(marker in done.stderr for marker in OFFLINE):
                    raise Unavailable("offline: " + done.first_error)
                doc = parse_json(_read(out))
                if not isinstance(doc, dict) or "results" not in doc:
                    failed.append(f"{lock}: {done.first_error}")
                    continue
                saved.append({"lockfile": lock, "results": doc["results"]})
                self._osv_findings(r, lock, doc)
            if failed and not saved:
                raise Failed("; ".join(failed))
            r.notes += [f"could not read {f}" for f in failed]
            r.notes.append(f"lockfiles read: {', '.join(s['lockfile'] for s in saved)}")
            self.run.save(r, "osv-scanner.json", json.dumps(saved, indent=1))

        r.job = job
        return r

    def _osv_findings(self, r: Row, lock: str, doc: dict) -> None:
        reach = _Reachability(self.repo / lock)
        text = _read(self.repo / lock)
        for result in doc.get("results") or []:
            for package in result.get("packages") or []:
                info = package.get("package") or {}
                name, version, ecosystem = info.get("name", ""), info.get("version", ""), info.get("ecosystem", "")
                vulns = package.get("vulnerabilities") or []
                if not vulns:
                    continue
                groups = package.get("groups") or []
                ids = sorted({i for g in groups for i in [*(g.get("ids") or []), *(g.get("aliases") or [])]} or {v.get("id", "") for v in vulns})
                scores = [_score(g.get("max_severity")) for g in groups]
                labels = {str((v.get("database_specific") or {}).get("severity", "")).upper() for v in vulns}
                high = any(s >= 7.0 for s in scores) or bool(labels & {"HIGH", "CRITICAL"})
                fixes = [_fixed_version(v, name, version) for v in vulns]
                target = max((f for f in fixes if f), key=_version_key, default="")
                count = len(groups) or len(vulns)
                message = f"{name}@{version} ({ecosystem}): {count} advisor{'y' if count == 1 else 'ies'}"
                message += f"; fix: upgrade to >={target}" if target else "; no fixed version"
                missing = sum(1 for f in fixes if not f)
                if target and missing:
                    message += f" ({missing} without a fix)"
                reason = ""
                if not target:
                    reason = "no fixed version exists"
                elif lock.rsplit("/", 1)[-1] in NPM_LOCKS and (where := reach.verdict(name, version)) != "prod":
                    reason = "reached only from devDependencies" if where == "dev" else ""
                    message += "" if where == "dev" else f"; reachability unknown ({reach.why})"
                finding = r.add(
                    lock,
                    _line_of(text, name, version),
                    "security",
                    "vulnerable-dependency",
                    "error" if high else "warning",
                    message,
                    graded=not reason,
                    reason=reason,
                )
                finding.data.update(package=f"{name}@{version}", ids=",".join(ids), cvss=max(scores, default=0) or "")

    # --- workflows ---------------------------------------------------------------------

    def zizmor(self) -> Row:
        r = row("security", "zizmor")
        workflows = [f for f in self.inv.workflows if self.inv.in_selection(f) or f.startswith(inv.WORKFLOW_ROOTS)]
        if not workflows:
            return r.skip("nothing to scan (no workflow files)")
        if not self.run.which("uv"):
            return r.unavailable("uv not on PATH: brew install uv")
        config = inv.find_config(self.repo, ".", ("zizmor.yml", "zizmor.yaml"), local=True) or (
            ".github/zizmor.yml" if (self.repo / ".github/zizmor.yml").exists() else None
        )
        r.provenance = (f"repo config ({config})" if config else "default config") + ", ephemeral"

        def job(r: Row) -> None:
            argv = self.run.uvx("zizmor")
            r.version = self.run.version("zizmor", [*argv, "--version"])
            self.run.pin_uvx("zizmor", r.version)
            done = self.run.exec(
                r,
                [*argv, "--format", "json-v1", "--offline", "--no-exit-codes", "--no-progress", "--", *(self.repo / w for w in workflows)],
            )
            found = parse_json(done.stdout)
            if not isinstance(found, list):
                raise Failed(done.first_error)
            waived = 0
            for item in found:
                if item.get("ignored"):
                    waived += 1
                    continue
                ident = item.get("ident", "")
                marks = item.get("determinations") or {}
                locations = item.get("locations") or [{}]
                primary = next((l for l in locations if (l.get("symbolic") or {}).get("kind") == "Primary"), locations[0])
                symbolic = primary.get("symbolic") or {}
                local = ((symbolic.get("key") or {}).get("Local") or {}) if isinstance(symbolic.get("key"), dict) else {}
                path = next((v for v in local.values() if isinstance(v, str)), "")
                start = (((primary.get("concrete") or {}).get("location") or {}).get("start_point") or {}).get("row")
                route = ".".join(str(next(iter(step.values()))) for step in ((symbolic.get("route") or {}).get("route") or []))
                level = ZIZMOR_LEVEL.get(marks.get("severity", ""), "info")
                if ident in ZIZMOR_DEMOTED and level == "error":
                    level = "warning"
                note = symbolic.get("annotation") or ""
                finding = r.add(
                    self.run.rel(path),
                    start + 1 if isinstance(start, int) else "",
                    "security",
                    ident,
                    level,
                    f"{item.get('desc', '')}: {note} (at {route})" if route else f"{item.get('desc', '')}: {note}",
                )
                finding.data.update(confidence=marks.get("confidence", ""), severity=marks.get("severity", ""))
            if waived:
                r.notes.append(f"{waived} waived by {config or 'inline ignores'}")
            r.notes.append(f"{len(workflows)} workflow file(s): {', '.join(workflows[:8])}")
            self.run.save(r, "zizmor.json", done.stdout)

        r.job = job
        return r

    # --- SAST --------------------------------------------------------------------------

    def opengrep(self) -> Row:
        r = row("security", "opengrep")
        if not self.run.which("opengrep"):
            return r.unavailable("brew install opengrep")
        rules = next((d for d in (".opengrep", ".semgrep") if (self.repo / d).is_dir()), None)
        if rules is None:
            return r.skip("no local ruleset")
        targets = [self.run.abs(f) for f in self.files if inv.language_of(f) in ("js-ts", "python", "c-cpp")]
        if not targets:
            return r.skip("nothing to scan")
        r.provenance = f"repo config ({rules}/), system binary"

        def job(r: Row) -> None:
            r.version = self.run.version("opengrep", ["opengrep", "--version"])
            results = []
            for start in range(0, len(targets), 200):
                done = self.run.exec(
                    r,
                    ["opengrep", "scan", "--config", self.repo / rules, "--json", "--disable-version-check", "--quiet", *targets[start : start + 200]],
                )
                doc = parse_json(done.stdout)
                if not isinstance(doc, dict) or "results" not in doc:
                    raise Failed(done.first_error)
                results += doc["results"]
            for item in results:
                extra = item.get("extra") or {}
                extra.pop("lines", None)  # the matched source
                level = {"ERROR": "error", "WARNING": "warning"}.get(str(extra.get("severity", "")).upper(), "info")
                r.add(
                    self.run.rel(item.get("path", "")),
                    (item.get("start") or {}).get("line", 0),
                    "security",
                    str(item.get("check_id", "")).rsplit(".", 1)[-1],
                    level,
                    extra.get("message", ""),
                )
            self.run.save(r, "opengrep.json", json.dumps(results, indent=1))

        r.job = job
        return r

    # --- duplication -------------------------------------------------------------------

    def jscpd(self) -> list[Row]:
        scanned = self.inv.scanned()
        passes = [(p.dir, [p.dir], [q.dir for q in self.inv.projects if q.dir != p.dir and inv.is_within(q.dir, p.dir)]) for p in scanned]
        if len(scanned) != 1:
            passes.append(("repo", self.inv.scan_dirs(), []))
        rows = []
        for project, dirs, nested in passes:
            r = row("duplication", "jscpd", project=project)
            r.scope = "project" if project != "repo" else "selected project dirs"
            if not self.run.which("node"):
                rows.append(r.unavailable("node not on PATH: brew install node"))
                continue
            r.provenance = "skill config, ephemeral"
            r.job = self._jscpd_job(project, dirs, nested)
            rows.append(r)
        return rows

    def _jscpd_job(self, project: str, dirs: list[str], nested: list[str]):
        def job(r: Row) -> None:
            argv, r.version = self.run.npx("jscpd")
            self.run.warm("jscpd", [*argv, "--version"])
            name = r.folder
            out = self.run.scratch_dir("jscpd", name)
            ignore = []
            for d in dirs:
                root = str(self.repo / d) if d != "." else str(self.repo)
                ignore += [f"{root}/**/{skip}/**" for skip in JSCPD_SKIP] + [f"{root}/**/.*/**"]
            ignore += [f"{self.repo / child}/**" for child in nested]
            ignore += self._repo_excludes()
            generated = [g for g in self.inv.generated if any(inv.is_within(g, d) for d in dirs)]
            ignore += [str(self.repo / g) for g in generated]
            if generated:
                r.notes.append(f"{len(generated)} generated files left out (inventory.md lists them)")
            config = self.run.config_dir() / f"jscpd-{name}.json"
            config.write_text(json.dumps({"minTokens": 50, "minLines": 5, "ignore": ignore}, indent=1))
            done = self.run.exec(
                r,
                [*argv, "--reporters", "json", "--output", out, "--format", JSCPD_FORMATS, "--config", config, "--absolute", "--no-colors", *(self.repo / d for d in dirs)],
            )
            doc = parse_json(_read(out / "jscpd-report.json"))
            if not isinstance(doc, dict) or "statistics" not in doc:
                raise Failed(done.first_error)
            total = (doc.get("statistics") or {}).get("total") or {}
            r.metrics["duplication"] = Metric(total.get("duplicatedTokens", 0), total.get("tokens", 0), "tokens")
            if not total.get("sources"):
                r.notes.append("jscpd analyzed no files: duplication is not assessed, not clean")
            in_tests = 0
            for clone in doc.get("duplicates") or []:
                clone.pop("fragment", None)  # the duplicated source
                first, second = clone.get("firstFile") or {}, clone.get("secondFile") or {}
                a, b = self.run.rel(first.get("name", "")), self.run.rel(second.get("name", ""))
                in_tests += int(inv.is_test_path(a) and inv.is_test_path(b))
                finding = r.add(
                    a,
                    first.get("start", 0),
                    "duplication",
                    "clone",
                    "info",
                    f"{clone.get('lines', 0)} lines, {clone.get('tokens', 0)} tokens duplicated with {b}:{second.get('start', '')}-{second.get('end', '')}",
                    graded=False,
                    reason="evidence: the letter is the token percentage",
                )
                finding.data.update(tokens=clone.get("tokens", ""), other=b)
            clones = len(doc.get("duplicates") or [])
            r.notes.append(f"{clones} clones over {total.get('sources', 0)} files; {in_tests} sit between two test files")
            self.run.save(r, "jscpd.json", json.dumps(doc, indent=1))

        return job

    def _repo_excludes(self) -> list[str]:
        """Globs the repo's own Biome or fallow config excludes, anchored to that config's
        directory."""
        globs = []
        for rel in self.inv.files:
            name = rel.rsplit("/", 1)[-1]
            base = self.repo / inv.parent(rel)
            if name in ("biome.json", "biome.jsonc"):
                doc = inv.read_jsonc(str(self.repo / rel)) or {}
                entries = ((doc.get("files") or {}).get("includes")) or []
                globs += [g for e in entries if isinstance(e, str) and e.startswith("!") for g in _both(f"{base}/{e[1:].lstrip('/')}")]
            elif name in (".fallowrc.json", ".fallowrc.jsonc"):
                doc = inv.read_jsonc(str(self.repo / rel)) or {}
                globs += [g for e in (doc.get("ignorePatterns") or []) if isinstance(e, str) for g in _both(f"{base}/{e.lstrip('/')}")]
        return globs

    # --- aislop ------------------------------------------------------------------------

    def aislop(self) -> Row:
        r = row(("lint", "security"), "aislop")
        if not self.run.which("node"):
            return r.unavailable("node not on PATH: brew install node")
        config = ".aislop" if (self.repo / ".aislop").is_dir() else None
        r.provenance = (f"repo config ({config}/)" if config else "default config") + ", ephemeral"

        def job(r: Row) -> None:
            argv, r.version = self.run.npx("aislop")
            mirror = self.mirror("aislop")
            if config:
                shutil.copytree(self.repo / config, mirror / config, dirs_exist_ok=True)
            # aislop walks files through git: a mirror without a commit scans 0 files at exit 0
            identity = ["-c", "user.name=scan", "-c", "user.email=scan@localhost", "-c", "commit.gpgsign=false"]
            for step in (["init", "-q"], ["add", "-A", "-f"], [*identity, "commit", "-qm", "scan"]):
                done = self.run.exec(None, ["git", "-C", mirror, *step])
                if done.code != 0:
                    raise Failed("mirror: " + done.first_error)
            done = self.run.exec(r, [*argv, "scan", "--sarif", mirror], env={"AISLOP_NO_TELEMETRY": "1"})
            doc = parse_json(done.stdout)
            if not isinstance(doc, dict) or not doc.get("runs"):
                raise Failed(done.first_error)
            driver = ((doc["runs"][0].get("tool") or {}).get("driver")) or {}
            r.version = driver.get("version") or r.version
            for rule, level, message, uri, line in sarif_results(doc):
                if rule.endswith("/skipped"):  # an engine aislop could not run, not a finding
                    r.notes.append(f"{rule}: {message}"[:200])
                    continue
                reason = next((why for prefix, why in AISLOP_ELSEWHERE.items() if rule.startswith(prefix)), "")
                if not reason and not config and not rule.startswith(AISLOP_OWN):
                    # eslint, knip, react and jsx-a11y rules run inside aislop: engines the repo never chose
                    reason = "default config: a bundled engine's rule, never imposed"
                graded = not reason or (bool(config) and "duplicate" not in reason)
                finding = r.add(
                    self.run.rel(uri, mirror, mirror),
                    line,
                    "security" if rule.startswith("security/") else "lint",
                    rule,
                    "warning",
                    message,
                    graded=graded,
                    reason=reason,
                )
                finding.data["level"] = level
            self.run.save(r, "aislop.sarif", done.stdout)

        r.job = job
        return r


def _both(glob: str) -> list[str]:
    """A config's exclude names a file or a directory; cover both readings."""
    return [glob] if glob.endswith("/**") else [glob, glob.rstrip("/") + "/**"]


# --- osv helpers ---------------------------------------------------------------------------


def _is_osv_manifest(rel: str) -> bool:
    name = rel.rsplit("/", 1)[-1]
    return name in OSV_MANIFESTS or bool(re.fullmatch(r"requirements.*\.txt", name))


def _score(value) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _version_key(version: str) -> tuple:
    return tuple(int(n) for n in re.findall(r"\d+", version.split("+")[0])[:6])


def _fixed_version(vuln: dict, name: str, installed: str) -> str:
    """The smallest fixed version above the installed one, walked out of the affected ranges."""
    have = _version_key(installed)
    candidates = []
    for affected in vuln.get("affected") or []:
        package = (affected.get("package") or {}).get("name")
        if package and package != name:
            continue
        for rng in affected.get("ranges") or []:
            for event in rng.get("events") or []:
                fixed = event.get("fixed")
                if fixed and _version_key(str(fixed)) > have:
                    candidates.append(str(fixed))
    return min(candidates, key=_version_key, default="")


def _line_of(text: str, name: str, version: str) -> int | str:
    needles = (f"{name}@{version}", f'"node_modules/{name}"', f'name = "{name}"', f"{name} v{version}", f"{name} {version}")
    for needle in needles:
        at = text.find(needle)
        if at >= 0:
            return text.count("\n", 0, at) + 1
    return ""


class _Reachability:
    """Whether a locked package is reached from production dependencies.

    `prod` and `unknown` both grade: only a package the lockfile proves dev-only is advisory.
    """

    def __init__(self, lockfile: Path):
        self.why = f"{lockfile.name} does not say"
        self.prod: set[str] | None = None
        self.dev: set[str] = set()
        name = lockfile.name
        try:
            if name in ("package-lock.json", "npm-shrinkwrap.json"):
                self._npm(json.loads(lockfile.read_text(encoding="utf-8")))
            elif name == "pnpm-lock.yaml":
                self._pnpm(parse_yaml_maps(lockfile.read_text(encoding="utf-8")))
        except (OSError, ValueError, AttributeError, TypeError) as exc:
            self.prod, self.why = None, f"{name} unreadable: {type(exc).__name__}"

    def verdict(self, name: str, version: str) -> str:
        if self.prod is None:
            return "unknown"
        key = f"{name}@{version}"
        if key in self.prod:
            return "prod"
        if key in self.dev:
            return "dev"
        self.why = "the lockfile never mentions it"
        return "unknown"

    def _npm(self, doc: dict) -> None:
        self.prod = set()
        for path, entry in (doc.get("packages") or {}).items():
            if "node_modules/" not in path or not isinstance(entry, dict):
                continue
            key = f"{path.rsplit('node_modules/', 1)[1]}@{entry.get('version', '')}"
            (self.dev if entry.get("dev") else self.prod).add(key)
        self.dev -= self.prod

    def _pnpm(self, doc: dict) -> None:
        importers = doc.get("importers") or {}
        snapshots = doc.get("snapshots") or doc.get("packages") or {}
        graph = {_pnpm_key(k): v for k, v in snapshots.items() if isinstance(v, dict)}
        queue, seen_importers = [], set()

        def enter(importer: str) -> None:
            if importer in seen_importers or importer not in importers:
                return
            seen_importers.add(importer)
            for block in ("dependencies", "optionalDependencies"):
                for dep, spec in (importers[importer].get(block) or {}).items():
                    version = spec.get("version", "") if isinstance(spec, dict) else str(spec)
                    if version.startswith("link:"):
                        enter(os.path.normpath(os.path.join(importer, version[5:])).replace(os.sep, "/"))
                    else:
                        queue.append(_pnpm_key(f"{dep}@{version}"))

        for importer in list(importers):
            enter(importer)
        self.prod = set()
        while queue:
            key = queue.pop()
            if key in self.prod:
                continue
            self.prod.add(key)
            entry = graph.get(key) or {}
            for block in ("dependencies", "optionalDependencies"):
                for dep, version in (entry.get(block) or {}).items():
                    if isinstance(version, str):
                        queue.append(_pnpm_key(f"{dep}@{version}"))
        self.dev = set(graph) - self.prod


def _pnpm_key(key: str) -> str:
    """`/name@1.0.0(peer@2)` and `name@1.0.0(peer@2)` both name `name@1.0.0`."""
    return key.lstrip("/").split("(", 1)[0]


YAML_KEY = re.compile(r"""^(\s*)(?:'((?:[^']|'')*)'|"([^"]*)"|([^\s#'"\-][^:]*?)):(?:\s+(.*))?$""")


def parse_yaml_maps(text: str) -> dict:
    """The nested maps of a machine-written YAML lockfile. Scalars keep their text; lists and
    flow collections are skipped, which is all a dependency walk needs."""
    root: dict = {}
    stack: list[tuple[int, dict]] = [(-1, root)]
    for raw in text.splitlines():
        if not raw.strip() or raw.lstrip().startswith(("#", "- ")):
            continue
        match = YAML_KEY.match(raw)
        if not match:
            continue
        indent = len(match.group(1))
        key = next(g for g in match.groups()[1:4] if g is not None).replace("''", "'")
        value = (match.group(5) or "").strip()
        while stack[-1][0] >= indent:
            stack.pop()
        parent = stack[-1][1]
        if value == "" or value.startswith("#"):
            child: dict = {}
            parent[key] = child
            stack.append((indent, child))
        elif value.startswith("{"):
            parent[key] = {}  # a flow mapping: the key exists, its content is not walked
        elif not value.startswith(("[", "|", ">")):
            parent[key] = value.strip("'\"")
    return root


def _read(path) -> str:
    try:
        return Path(path).read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""
