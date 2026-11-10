"""JS/TS analyzers: the commands, ownership rule and routing `references/jsts.md` states."""

from __future__ import annotations

import json
import re
from functools import partial
from pathlib import Path

from . import inventory as inv
from .runner import Failed, Metric, Row, Run, Rung, batches, first_json_line, not_on_path, parse_json, pick_binary, sarif_results

LANGUAGE = "js-ts"
CEILING = 15
OWNABLE = ("tsc", "eslint", "biome", "oxlint", "prettier", "oxfmt", "knip", "fallow", "stryker")
TS_EXTENSIONS = (".ts", ".tsx", ".mts", ".cts")
FORMAT_EXTRA = (".css", ".scss", ".less", ".json", ".jsonc", ".graphql", ".gql", ".md", ".mdx", ".yaml", ".yml", ".html", ".vue")
LINT_EXTRA = (".css", ".graphql", ".gql")
OXLINT_DEFAULT = {"plugins": ["typescript", "unicorn", "oxc"], "categories": {"correctness": "error", "suspicious": "warn", "perf": "warn"}}
SCRATCH_TSCONFIG = {
    "strict": True,
    "noEmit": True,
    "skipLibCheck": True,
    "module": "esnext",
    "moduleResolution": "bundler",
    "target": "es2022",
    "jsx": "preserve",
}
TSC_LINE = re.compile(r"^(?:(.+?)\((\d+),\d+\): )?(error|warning) (TS\d+): (.*)$")
TSC_NEEDS_INSTALL = {"TS2307", "TS2503", "TS2580", "TS2591", "TS2593", "TS2688", "TS2792", "TS7016"}
NO_CACHE = {"JITI_CACHE": "false", "JITI_FS_CACHE": "false"}
KNIP_ENTRIES = (
    'name the entries in <run-dir>/knip.json, add {"knip": ["--config", "<run-dir>/knip.json"]} '
    "to <run-dir>/overrides.json and rerun --tool knip"
)
KNIP_GRADED = {
    "files": "unused-file",
    "exports": "unused-export",
    "types": "unused-type",
    "enumMembers": "unused-member",
    "classMembers": "unused-member",
    "namespaceMembers": "unused-member",
    "duplicates": "duplicate-export",
}
KNIP_INFO = {
    "dependencies": "unused-dependency",
    "devDependencies": "unused-dependency",
    "optionalPeerDependencies": "unused-dependency",
    "unlisted": "unlisted-dependency",
    "binaries": "unlisted-binary",
    "unresolved": "unresolved-import",
    "catalog": "unused-catalog-entry",
}
FALLOW_GRADED = {
    "unused_files": "unused-file",
    "unused_exports": "unused-export",
    "unused_types": "unused-type",
    "unused_enum_members": "unused-member",
    "unused_class_members": "unused-member",
    "duplicate_exports": "duplicate-export",
}
FALLOW_INFO = {
    "unused_dependencies": "unused-dependency",
    "unused_dev_dependencies": "unused-dependency",
    "unused_optional_dependencies": "unused-dependency",
    "unlisted_dependencies": "unlisted-dependency",
    "unresolved_imports": "unresolved-import",
}

# tool -> (config file patterns, package names, package.json key)
OWNERSHIP = {
    "eslint": (("eslint.config.*", ".eslintrc", ".eslintrc.*"), ("eslint",), None),
    "biome": (("biome.json", "biome.jsonc"), ("@biomejs/biome",), None),
    "oxlint": ((".oxlintrc.json", "oxlint.config.*"), ("oxlint",), None),
    "prettier": ((".prettierrc", ".prettierrc.*", "prettier.config.*"), ("prettier",), "prettier"),
    "oxfmt": ((".oxfmtrc.json", ".oxfmtrc.jsonc", "oxfmt.config.ts"), ("oxfmt",), None),
    "knip": (("knip.json", "knip.jsonc", ".knip.json", ".knip.jsonc", "knip.ts", "knip.js", "knip.config.*"), ("knip",), "knip"),
    "fallow": ((".fallowrc.json", ".fallowrc.jsonc", "fallow.toml", ".fallow.toml", "fallow.config.*"), ("fallow",), None),
    "stryker": (("stryker.config.*", "stryker.conf.*", ".strykerrc*"), ("@stryker-mutator/core",), None),
}


def config_of(repo: Path, project: inv.Project, tool: str) -> str | None:
    patterns, _packages, key = OWNERSHIP[tool]
    return inv.find_config(repo, project.dir, patterns) or (inv.npm_manifest_key(repo, project.dir, key) if key else None)


def owned(repo: Path, project: inv.Project) -> dict[str, str]:
    """Ownership = a config file in the project or an ancestor, or the package in a
    dependency block. `tsc` alone needs its `tsconfig.json` in the project itself."""
    found = {}
    if (repo / project.dir / "tsconfig.json").is_file():
        found["tsc"] = "tsconfig.json" if project.dir == "." else f"{project.dir}/tsconfig.json"
    for tool, (_patterns, packages, _key) in OWNERSHIP.items():
        evidence = config_of(repo, project, tool) or inv.npm_dependency(repo, project.dir, *packages)
        if evidence:
            found[tool] = evidence
    return found


def plan(run: Run, project: inv.Project) -> list[Row]:
    files = project.files.get(LANGUAGE, [])
    if not files:
        return []
    ctx = _Context(run, project, files)
    project.facts["node_modules"] = "present" if ctx.modules else "absent"
    lint = [ctx.eslint(), ctx.biome("lint"), ctx.oxlint()]
    fmt = [ctx.biome("format"), ctx.oxfmt(), ctx.prettier()]
    dead = [ctx.fallow_dead_code(), ctx.knip()]
    _standby(lint)
    _standby(fmt)
    _standby(dead)
    rows = [*lint, ctx.react_doctor(), ctx.tsc(), *dead, ctx.fallow_health(), *fmt, ctx.stryker()]
    return [r for r in rows if r is not None]


def _standby(rows: list[Row]) -> None:
    """The last row is the default tool; it stands by behind the first owner that will run."""
    default = rows[-1]
    owner = next((r for r in rows[:-1] if r.job is not None), None)
    if default.job is None or owner is None or not default.provenance.startswith("default config"):
        return
    default.stand_by(owner.tool)


class _Context:
    def __init__(self, run: Run, project: inv.Project, files: list[str]):
        self.run, self.project, self.repo = run, project, run.repo
        self.dir = run.repo / project.dir
        self.files = files
        self.mine = set(project.every_file)
        self.lint_files = files + [f for f in project.every_file if inv.ext_of(f) in LINT_EXTRA]
        locks = inv.LOCKFILES
        self.format_files = files + [
            f for f in project.every_file if inv.ext_of(f) in FORMAT_EXTRA and f.rsplit("/", 1)[-1] not in locks
        ]
        self.modules = next((self.repo / d / "node_modules" for d in inv.ancestry(project.dir) if (self.repo / d / "node_modules").is_dir()), None)

    def row(self, categories, tool: str, **kw) -> Row:
        return Row(project=self.project.dir, language=LANGUAGE, categories=categories, tool=tool, **kw)

    # --- resolving a binary ------------------------------------------------------------

    def local_bin(self, name: str) -> Path | None:
        for here in inv.ancestry(self.project.dir):
            candidate = self.repo / here / "node_modules" / ".bin" / name
            if candidate.exists():
                return candidate
        return None

    def declared(self, package: str) -> str:
        """The exact version a manifest's range starts at: `^2.4.14` runs as 2.4.14."""
        for here in inv.ancestry(self.project.dir):
            manifest = inv.read_json(str(self.repo / here / "package.json")) or {}
            for block in inv.DEP_BLOCKS:
                spec = (manifest.get(block) or {}).get(package) if isinstance(manifest.get(block), dict) else None
                if isinstance(spec, str) and (m := re.fullmatch(r"[~^=v]*(\d+\.\d+\.\d+(?:-[0-9A-Za-z.]+)?)", spec.strip())):
                    return m.group(1)
        return ""

    def resolve(self, row: Row, tool: str, package: str, binary: str, config: str | None):
        """A deferred argv prefix, with the row's provenance set now. An owned tool runs its
        installed binary; owned but not installed runs the declared version ephemerally."""
        how = f"repo config ({config})" if config else "default config"
        is_owned = tool in self.project.owned
        local = self.local_bin(binary) if is_owned else None
        declared = self.declared(package) if is_owned else ""

        def local_argv() -> list[str]:
            row.version = self.run.version(str(local), [str(local), "--version"], cwd=self.dir)
            return [str(local)]

        def npx_argv() -> list[str]:
            prefix, row.version = self.run.npx(package, binary, declared)
            self.run.warm(f"{package}@{row.version}", [*prefix, "--version"])
            return prefix

        rungs = [
            Rung("repo binary", is_owned and local is not None, lambda: local_argv),
            Rung("ephemeral", bool(self.run.which("node")), lambda: npx_argv),
        ]
        return pick_binary(row, how, rungs, not_on_path("node"))

    # --- lint --------------------------------------------------------------------------

    def oxlint(self) -> Row:
        row = self.row("lint", "oxlint")
        config = config_of(self.repo, self.project, "oxlint")
        argv = self.resolve(row, "oxlint", "oxlint", "oxlint", config)
        if argv is None:
            return row
        row.job = partial(self._oxlint_job, argv, config)
        return row

    def _oxlint_job(self, argv, config: str | None, row: Row) -> None:
        prefix = argv()
        extra = []
        if not config:
            default = self.run.config_dir() / "oxlintrc.json"
            default.write_text(json.dumps(OXLINT_DEFAULT))
            extra = ["--config", str(default), "--disable-nested-config"]
        results = self._oxlint_results(row, [*prefix, "--format", "sarif", "--no-error-on-unmatched-pattern", *extra])
        for rule, level, message, uri, line in results:
            error = level == "error"
            graded = bool(config) or error
            row.add(
                self.run.rel(uri, self.repo),
                line,
                "lint",
                re.sub(r"^([^()]+)\((.+)\)$", r"\1/\2", rule),
                "error" if error else "warning",
                message,
                graded=graded,
                reason="default config: only correctness rules grade",
            )
        self.run.save(row, "oxlint.json", json.dumps([list(r) for r in results], indent=1))

    def _oxlint_results(self, row: Row, command: list[str]) -> list:
        results = []
        for batch in batches([self.run.abs(f) for f in self.files]):
            done = self.run.exec(row, [*command, *batch], cwd=self.repo)
            doc = parse_json(done.stdout)
            if not isinstance(doc, dict) or not doc.get("runs"):
                # exit 0 with nothing on stdout is a file list oxlint could not read, not a clean tree
                raise Failed(f"exit {done.code} and no SARIF on stdout: {done.first_error}")
            results += list(sarif_results(doc))
        return results

    def eslint(self) -> Row:
        row = self.row("lint", "eslint")
        if "eslint" not in self.project.owned:
            return row.skip("not owned (never imposed)")
        config = config_of(self.repo, self.project, "eslint")
        flat = config and config.rsplit("/", 1)[-1].startswith("eslint.config.")
        if config and not flat and self.local_bin("eslint") is None:
            return row.unavailable("only a legacy .eslintrc and no install: ESLint 9+ no longer reads it")
        argv = self.resolve(row, "eslint", "eslint", "eslint", config)
        if argv is None:
            return row
        cwd = self.repo / inv.parent(config) if config else self.dir
        row.job = partial(self._eslint_job, argv, cwd)
        return row

    def _eslint_job(self, argv, cwd: Path, row: Row) -> None:
        prefix = argv()
        reports = self._eslint_reports(row, prefix, cwd)
        for entry in reports:
            self._eslint_entry(row, entry, cwd)
        row.notes.append(f"eslint reported on {len(reports)} of {len(self.files)} files; its config ignores the rest")
        self.run.save(row, "eslint.json", json.dumps(reports, indent=1))

    def _eslint_reports(self, row: Row, prefix: list[str], cwd: Path) -> list:
        reports = []
        for batch in batches([self.run.abs(f) for f in self.files]):
            flags = ["--format", "json", "--no-color", "--no-warn-ignored"]
            done = self.run.exec(row, [*prefix, *flags, *batch], cwd=cwd)
            if done.code == 2 and "no-warn-ignored" in done.stderr:
                done = self.run.exec(row, [*prefix, "--format", "json", "--no-color", *batch], cwd=cwd)
            part = parse_json(done.stdout)
            if not isinstance(part, list):
                raise Failed(done.first_error)
            reports += part
        return reports

    def _eslint_entry(self, row: Row, entry: dict, cwd: Path) -> None:
        """Add one file's messages, then slim the entry to what the saved report keeps."""
        entry.pop("source", None)
        path = self.run.rel(entry.get("filePath", ""), cwd)
        for message in entry.get("messages") or []:
            row.add(
                path,
                message.get("line", 0),
                "lint",
                message.get("ruleId") or "parse-error",
                "error" if message.get("severity") == 2 else "warning",
                message.get("message", ""),
            )
        entry["messages"] = [{k: m.get(k) for k in ("ruleId", "severity", "message", "line", "column")} for m in entry.get("messages") or []]

    def biome(self, mode: str) -> Row:
        row = self.row(mode, f"biome {mode}")
        if "biome" not in self.project.owned:
            return row.skip("not owned (never imposed)")
        config = None
        for here in inv.ancestry(self.project.dir):  # the highest config: Biome refuses one below its cwd
            config = inv.find_config(self.repo, here, OWNERSHIP["biome"][0], local=True) or config
        argv = self.resolve(row, "biome", "@biomejs/biome", "biome", config)
        if argv is None:
            return row
        cwd = self.repo / inv.parent(config) if config else self.dir
        targets = self.lint_files if mode == "lint" else self.format_files
        row.reads_assets = mode == "lint"
        row.job = partial(self._biome_job, argv, mode, cwd, targets)
        return row

    def _biome_job(self, argv, mode: str, cwd: Path, targets: list[str], row: Row) -> None:
        prefix = argv()
        flags = ["--reporter=json", "--max-diagnostics=none", "--colors=off", "--no-errors-on-unmatched"]
        if self.run.inv.is_git and (self.repo / ".gitignore").is_file():  # Biome errors without an ignore file
            flags += ["--vcs-enabled=true", "--vcs-client-kind=git", "--vcs-use-ignore-file=true", f"--vcs-root={self.repo}"]
        diagnostics, parsed = self._biome_diagnostics(row, [*prefix, mode, *flags], targets, cwd)
        if parsed == 0:
            row.skip(f"nothing to scan (the Biome config includes none of this project's {len(targets)} files)")
            return
        failing = self._biome_findings(row, mode, diagnostics, cwd)
        if mode == "format":
            row.metrics["format"] = Metric(len(failing), parsed, "files")
        row.notes.append(f"Biome read {parsed} of the {len(targets)} files passed")
        self.run.save(row, f"biome-{mode}.json", json.dumps(diagnostics, indent=1))

    def _biome_diagnostics(self, row: Row, command: list[str], targets: list[str], cwd: Path) -> tuple[list, int]:
        """Every diagnostic over the batches, and how many files Biome read."""
        diagnostics, parsed = [], 0
        for batch in batches([self.run.abs(f) for f in targets]):
            done = self.run.exec(row, [*command, *batch], cwd=cwd)
            doc = first_json_line(done.stdout, "diagnostics")
            if doc is None:
                raise Failed(done.first_error)
            diagnostics += doc["diagnostics"]
            parsed += (doc.get("summary") or {}).get("unchanged", 0) + (doc.get("summary") or {}).get("changed", 0)
        return diagnostics, parsed

    def _biome_findings(self, row: Row, mode: str, diagnostics: list, cwd: Path) -> set[str]:
        """Add the diagnostics this mode reports; return the files that fail the formatter."""
        failing = set()
        for item in diagnostics:
            category = item.get("category", "")
            location = item.get("location") or {}
            path = location.get("path")
            path = self.run.rel(path.get("file", "") if isinstance(path, dict) else (path or ""), cwd)
            line = (location.get("start") or {}).get("line", 0)
            if category == "parse" or category.startswith("parse"):
                row.notes.append(f"{path}: Biome could not parse it")
            elif mode == "format" and category == "format":
                if path not in failing:
                    row.add(path, "", "format", "unformatted", "warning", "File would be reformatted")
                failing.add(path)
            elif mode == "lint" and category.startswith("lint/"):
                severity = {"error": "error", "fatal": "error", "warning": "warning"}.get(item.get("severity"), "info")
                row.add(path, line, "lint", category[5:], severity, item.get("message", ""), graded=severity != "info", reason="information")
        return failing

    def react_doctor(self) -> Row | None:
        react = inv.npm_dependency(self.repo, self.project.dir, "react")
        if not react:
            return None
        self.project.facts["react"] = react
        row = self.row("lint", "react-doctor")
        if not self.run.which("node"):
            return row.unavailable(not_on_path("node"))
        row.provenance = "default config, ephemeral"
        row.job = self._react_doctor_job
        return row

    def _react_doctor_job(self, row: Row) -> None:
        prefix, row.version = self.run.npx("react-doctor")
        out = self.run.scratch_dir("react-doctor", self.project.slug)
        env = {**NO_CACHE, "REACT_DOCTOR_CACHE_DIR": str(out / "cache"), "REACT_DOCTOR_NO_CACHE": "1"}
        done = self.run.exec(
            row,
            [*prefix, self.dir, "--json", "--no-telemetry", "--no-supply-chain", "--no-dead-code", "--blocking", "none", "--output-dir", out],
            cwd=self.run.scratch_dir(),
            env=env,
        )
        doc = parse_json(done.stdout)
        if not isinstance(doc, dict) or "diagnostics" not in doc:
            raise Failed(done.first_error)
        slim = []
        for item in doc["diagnostics"]:
            path = self.run.rel(item.get("filePath", ""), self.dir)
            if path not in self.mine:
                continue
            row.add(
                path,
                item.get("line", 0),
                "lint",
                item.get("rule", ""),
                "error" if item.get("severity") == "error" else "warning",
                item.get("message", ""),
                graded=False,
                reason="complementary tool",
            )
            slim.append({k: item.get(k) for k in ("filePath", "line", "rule", "severity", "message", "category")})
        self.run.save(row, "react-doctor.json", json.dumps(slim, indent=1))

    # --- format ------------------------------------------------------------------------

    def prettier(self) -> Row:
        row = self.row("format", "prettier")
        is_owned = "prettier" in self.project.owned
        config = config_of(self.repo, self.project, "prettier") if is_owned else None
        argv = self.resolve(row, "prettier", "prettier", "prettier", config)
        if argv is None:
            return row
        ignore = inv.find_config(self.repo, self.project.dir, (".prettierignore",))
        cwd = self.repo / inv.parent(ignore) if ignore else self.dir
        row.job = partial(self._prettier_job, argv, is_owned, ignore, cwd)
        return row

    def _prettier_job(self, argv, is_owned: bool, ignore: str | None, cwd: Path, row: Row) -> None:
        prefix = argv()
        flags = ["--list-different", "--ignore-unknown"] + ([] if is_owned else ["--no-config", "--no-editorconfig"])
        skipped = set(ignored_by(self.run, self.repo / ignore, cwd, self.format_files)) if ignore else set()
        targets = [f for f in self.format_files if f not in skipped]
        listed, errors = self._prettier_listed(row, [*prefix, *flags], targets, cwd)
        if errors and not listed:
            raise Failed(errors[0])
        row.notes += [f"check: prettier failed on a batch, whose files count as clean: {e}" for e in errors[:3]]
        failing = sorted({self.run.rel(path, cwd) for path in listed})
        for path in failing:
            row.add(path, "", "format", "unformatted", "warning", "File would be reformatted")
        row.metrics["format"] = Metric(len(failing), len(targets), "files")
        if skipped:
            row.notes.append(f"{len(skipped)} files skipped by {ignore}")
        self.run.save(row, "prettier.txt", "".join(p + "\n" for p in failing))

    def _prettier_listed(self, row: Row, command: list[str], targets: list[str], cwd: Path) -> tuple[list[str], list[str]]:
        """The paths prettier lists as different, and the first error of each failed batch."""
        listed, errors = [], []
        for batch in batches([self.run.abs(f) for f in targets]):
            done = self.run.exec(row, [*command, *batch], cwd=cwd)
            # exit 1 means it listed a file; exit 1 with nothing listed is a crash, a missing plugin
            if done.code not in (0, 1) or (done.code == 1 and not done.stdout.strip()):
                errors.append(done.first_error)
            listed += [line.strip() for line in done.stdout.splitlines() if line.strip()]
        return listed, errors

    def oxfmt(self) -> Row:
        row = self.row("format", "oxfmt")
        if "oxfmt" not in self.project.owned:
            return row.skip("not owned (never imposed)")
        config = config_of(self.repo, self.project, "oxfmt")
        argv = self.resolve(row, "oxfmt", "oxfmt", "oxfmt", config)
        if argv is None:
            return row
        row.job = partial(self._oxfmt_job, argv)
        return row

    def _oxfmt_job(self, argv, row: Row) -> None:
        prefix = argv()
        failing, counted, unparsed = self._oxfmt_listed(row, prefix)
        for path in sorted(failing):
            row.add(path, "", "format", "unformatted", "warning", "File would be reformatted")
        row.metrics["format"] = Metric(len(failing), counted or len(self.format_files), "files")
        row.notes += [f"oxfmt could not parse a file: {e}" for e in unparsed[:3]]
        self.run.save(row, "oxfmt.txt", "".join(p + "\n" for p in sorted(failing)))

    def _oxfmt_listed(self, row: Row, prefix: list[str]) -> tuple[set[str], int, list[str]]:
        """The files oxfmt would change, how many it checked, and its parse errors."""
        failing, counted, unparsed = set(), 0, []
        # oxfmt refuses a path containing `..` and reads .prettierignore from cwd alone
        for batch in batches([self.project.rel(f) for f in self.format_files]):
            done = self.run.exec(row, [*prefix, "--list-different", "--no-error-on-unmatched-pattern", *batch], cwd=self.dir)
            if done.code not in (0, 1, 2) or (done.code == 1 and not done.stdout.strip()):
                raise Failed(done.first_error)
            if done.code == 2:
                unparsed.append(done.first_error)
            failing.update(self.run.rel(line.strip(), self.dir) for line in done.stdout.splitlines() if line.strip())
            check = self.run.exec(row, [*prefix, "--check", "--no-error-on-unmatched-pattern", *batch], cwd=self.dir)
            if m := re.search(r"on (\d+) files?", check.stdout + check.stderr):
                counted += int(m.group(1))
        return failing, counted, unparsed

    # --- types -------------------------------------------------------------------------

    def tsc(self) -> Row:
        row = self.row("types", "tsc")
        own = "tsc" in self.project.owned
        typed = [f for f in self.files if inv.ext_of(f) in TS_EXTENSIONS]
        if not own and not typed:
            return row.skip("nothing to scan (no tsconfig.json and no TypeScript file: plain JavaScript is not type-checked)")
        config = self.project.owned.get("tsc")
        declared = self.declared("typescript")
        local = self.local_bin("tsc")
        how = f"repo config ({config})" if own else "default config"
        rungs = [
            Rung("repo binary", local is not None and bool(own or declared), lambda: local),
            Rung("ephemeral", bool(self.run.which("node")), lambda: None),
        ]
        picked = pick_binary(row, how, rungs, not_on_path("node"))
        if row.state == "not-available":
            return row
        row.job = partial(self._tsc_job, own, typed, declared, picked)
        return row

    def _tsc_prefix(self, row: Row, local: Path | None, declared: str) -> list[str]:
        if local is not None:
            prefix = [str(local)]
            row.version = self.run.version(str(local), [*prefix, "--version"], cwd=self.dir)
        else:
            prefix, row.version = self.run.npx("typescript", "tsc", declared)
            self.run.warm(f"typescript@{row.version}", [*prefix, "--version"])
        return prefix

    def _tsc_job(self, own: bool, typed: list[str], declared: str, local: Path | None, row: Row) -> None:
        prefix = self._tsc_prefix(row, local, declared)
        target = self.dir
        if not own:
            target = self.run.config_dir("tsc-" + self.project.slug) / "tsconfig.json"
            target.write_text(json.dumps({"compilerOptions": SCRATCH_TSCONFIG, "files": [self.run.abs(f) for f in typed]}))
        flags = ["--noEmit", "--pretty", "false", "--incremental", "false"]
        done = self.run.exec(row, [*prefix, *flags, "--project", target], cwd=self.repo)
        if "TS6379" in done.stdout:  # a composite project may not disable incremental compilation
            info = self.run.scratch_dir("tsc") / f"{self.project.slug}.tsbuildinfo"
            done = self.run.exec(row, [*prefix, "--noEmit", "--pretty", "false", "--tsBuildInfoFile", info, "--project", target], cwd=self.repo)
        parsed = 0
        for line in done.stdout.splitlines():
            if m := TSC_LINE.match(line):
                parsed += 1
                self._tsc_add(row, m)
        if done.code != 0 and parsed == 0:
            raise Failed(f"exit {done.code}, no diagnostics: {(done.stdout.strip().splitlines() or [done.first_error])[0][:200]}")
        if self.modules is None:
            row.notes.append("no node_modules: module-resolution diagnostics are advisory and imported types are unchecked")
        others = sorted(n for n in inv._listdir(str(self.dir)) if re.fullmatch(r"tsconfig\..+\.json", n))
        if own and others:
            row.notes.append(f"other tsconfig files here were not checked: {', '.join(others)}")
        self.run.save(row, "tsc.txt", done.stdout)

    def _tsc_add(self, row: Row, match: re.Match) -> None:
        path, lineno, kind, code, message = match.groups()
        needs_install = self.modules is None and (code in TSC_NEEDS_INSTALL or "npm i --save-dev @types/" in message)
        error = kind == "error"
        row.add(
            self.run.rel(path, self.repo) if path else "",
            int(lineno) if lineno else "",
            "types",
            code,
            "error" if error else "info",
            message,
            graded=error and not needs_install,
            reason="no node_modules: an install that never ran" if needs_install else kind,
        )

    # --- dead code ---------------------------------------------------------------------

    def knip_cwd(self) -> str | None:
        """The highest ancestor with workspaces or a knip config; else the nearest package.json."""
        best = nearest = None
        for here in inv.ancestry(self.project.dir):
            manifest = inv.read_json(str(self.repo / here / "package.json"))
            if isinstance(manifest, dict):
                nearest = nearest or here
                if "workspaces" in manifest:
                    best = here
            if (self.repo / here / "pnpm-workspace.yaml").is_file() or inv.find_config(self.repo, here, OWNERSHIP["knip"][0], local=True):
                best = here
        return best or nearest

    def knip(self) -> Row:
        row = self.row("dead code", "knip")
        cwd = self.knip_cwd()
        if cwd is None:
            return row.unavailable("no package.json in ancestry")
        config = config_of(self.repo, self.project, "knip")
        argv = self.resolve(row, "knip", "knip", "knip", config)
        if argv is None:
            return row
        row.scope = "project" if cwd == self.project.dir else f"workspace {cwd}, filtered to the project"
        row.job = partial(self._knip_job, argv, cwd)
        return row

    def _knip_compute(self, argv, cwd: str, row: Row):
        prefix = argv()
        extra = self.run.extra("knip", cwd)
        done = self.run.exec(
            row, [*prefix, "--reporter", "json", "--no-config-hints", "--no-progress", "--no-exit-code", *extra], cwd=self.repo / cwd, env=NO_CACHE
        )
        doc = first_json_line(done.stdout, "issues")
        if doc is None:
            raise Failed(done.first_error)
        return doc, row.version, list(row.commands), extra

    def _knip_job(self, argv, cwd: str, row: Row) -> None:
        doc, row.version, commands, extra = self.run.once(f"knip:{cwd}", partial(self._knip_compute, argv, cwd, row))
        row.notes.clear()
        row.commands = row.commands or commands
        if extra:
            row.provenance += f" + {' '.join(extra)}"
        dead_files = 0
        for issue in doc.get("issues") or []:
            path = self.run.rel(issue.get("file", ""), self.repo / cwd)
            if path in self.mine:
                dead_files += _knip_issue(row, path, issue)
        if extra:
            pass  # the agent named the entry points
        elif self.modules is None:
            self._knip_unmeasured(row, "no node_modules: knip cannot load the configs that name entry points")
        elif dead_files >= max(5, len(self.files) // 5):
            self._knip_unreached(row, dead_files)
        self.run.save(row, "knip.json", json.dumps(doc, indent=1))

    def _knip_unmeasured(self, row: Row, why: str) -> None:
        """knip ran and its rows cannot be believed: dead code reads not assessed, not A."""
        row.unmeasured = why
        for finding in row.findings:
            if finding.graded:
                finding.demote(why.split(":")[0])
        row.notes.append(f"check: {why}, so dead code is not assessed here; {KNIP_ENTRIES}")

    def _knip_unreached(self, row: Row, dead_files: int) -> None:
        # half the project unreached is no entry point at all; a fifth is worth a look
        if dead_files >= max(5, len(self.files) // 2):
            self._knip_unmeasured(row, f"no entry point reaches this project: knip calls {dead_files} of {len(self.files)} files unused")
            return
        row.notes.append(
            f"check: knip calls {dead_files} of {len(self.files)} files unused, so an entry point is probably missing; {KNIP_ENTRIES}"
        )

    def fallow(self, row: Row, config: str | None):
        if not self.run.which("node"):
            row.unavailable(not_on_path("node"))
            return None
        return self.resolve(row, "fallow", "fallow", "fallow", config)

    def fallow_dead_code(self) -> Row:
        row = self.row("dead code", "fallow dead-code")
        if "fallow" not in self.project.owned:
            return row.skip("not owned (never imposed)")
        argv = self.fallow(row, config_of(self.repo, self.project, "fallow"))
        if argv is None:
            return row
        row.scope = "repo, filtered to the project"
        row.job = partial(self._fallow_dead_code_job, argv)
        return row

    def _fallow_dead_code_compute(self, argv, row: Row):
        prefix = argv()
        done = self.run.exec(row, [*prefix, "dead-code", "--format", "json", "--no-cache", "-q"], cwd=self.repo)
        doc = parse_json(done.stdout)
        if not isinstance(doc, dict):
            raise Failed(done.first_error)
        return doc, row.version, list(row.commands)

    def _fallow_dead_code_job(self, argv, row: Row) -> None:
        doc, row.version, commands = self.run.once("fallow-dead-code", partial(self._fallow_dead_code_compute, argv, row))
        row.commands = row.commands or commands
        for key, rule in {**FALLOW_GRADED, **FALLOW_INFO}.items():
            for item in doc.get(key) or []:
                for path, line, name in _fallow_places(item):
                    path = self.run.rel(path, self.repo)
                    if path in self.mine:
                        _add_dead(row, path, line, rule, name, graded=key in FALLOW_GRADED)
        self.run.save(row, "fallow-dead-code.json", json.dumps({k: doc.get(k) for k in [*FALLOW_GRADED, *FALLOW_INFO, "summary"]}, indent=1))

    def fallow_health(self) -> Row:
        row = self.row("complexity", "fallow health")
        config = config_of(self.repo, self.project, "fallow") if "fallow" in self.project.owned else None
        argv = self.fallow(row, config)
        if argv is None:
            return row
        row.job = partial(self._fallow_health_job, argv)
        return row

    def _fallow_health_job(self, argv, row: Row) -> None:
        prefix = argv()
        done = self.run.exec(
            row,
            [*prefix, "health", "--format", "json", "--no-cache", "-q", "--root", self.dir, "--complexity", "--file-scores", "--max-cognitive", str(CEILING)],
            cwd=self.repo,
        )
        doc = parse_json(done.stdout)
        if not isinstance(doc, dict) or "findings" not in doc:
            raise Failed(done.first_error)
        over = self._fallow_health_findings(row, doc)
        scores = doc.get("file_scores") or []
        mine = [s for s in scores if self.run.rel(s.get("path", ""), self.dir) in self.mine]
        functions = sum(s.get("function_count", 0) for s in mine) if scores else (doc.get("summary") or {}).get("functions_analyzed", 0)
        row.metrics["complexity"] = Metric(over, functions, f"functions over {CEILING}")
        if not scores:
            row.notes.append("no file_scores in fallow's output: the function count is its own total, not filtered to the inventory")
        slim = {"summary": doc.get("summary"), "findings": [{k: f.get(k) for k in ("path", "name", "line", "cognitive", "cyclomatic", "exceeded")} for f in doc.get("findings") or []]}
        self.run.save(row, "fallow-health.json", json.dumps(slim, indent=1))

    def _fallow_health_findings(self, row: Row, doc: dict) -> int:
        """Add this project's findings; return how many functions are over the ceiling."""
        over = 0
        for item in doc.get("findings") or []:
            path = self.run.rel(item.get("path", ""), self.dir)  # fallow prints paths relative to --root
            if path in self.mine:
                over += _fallow_health_add(row, path, item)
        return over

    def stryker(self) -> Row:
        row = self.row("test quality", "stryker")
        return row.skip_deep("jsts.md", owned="stryker" in self.project.owned, deep=self.run.deep)


def _knip_symbols(value):
    """(name, line) for each entry of one knip issue list, whatever its nesting."""
    if isinstance(value, dict):
        for members in value.values():
            yield from _knip_symbols(members)
    elif isinstance(value, list):
        for item in value:
            yield from _knip_entry(item)


def _knip_entry(item):
    if isinstance(item, list):
        symbols = [i for i in item if isinstance(i, dict)]
        yield " = ".join(i.get("name", "") for i in symbols), next((i.get("line", 0) for i in symbols), 0)
    elif isinstance(item, dict):
        yield item.get("name", ""), item.get("line", 0)


def _knip_issue(row: Row, path: str, issue: dict) -> int:
    """Add one knip issue's findings; return how many unused files it names."""
    dead_files = 0
    for key, rule in {**KNIP_GRADED, **KNIP_INFO}.items():
        for name, line in _knip_symbols(issue.get(key)):
            if key == "files":
                dead_files += 1
            _add_dead(row, path, line, rule, name, graded=key in KNIP_GRADED)
    return dead_files


def _add_dead(row: Row, path: str, line, rule: str, name: str, *, graded: bool) -> None:
    row.add(
        path,
        line,
        "dead code",
        rule,
        "warning" if graded else "info",
        f"{rule.replace('-', ' ')}: {name}" if name else rule.replace("-", " "),
        graded=graded,
        reason="never grades",
    )


def _fallow_places(item):
    """(path, line, name) for one fallow dead-code entry; a duplicate export names several."""
    if not isinstance(item, dict):
        return
    name = item.get("export_name") or item.get("member_name") or item.get("name") or item.get("package_name") or ""
    if isinstance(item.get("locations"), list):
        for place in item["locations"]:
            if isinstance(place, dict) and place.get("path"):
                yield place["path"], place.get("line", 0), name
    elif item.get("path"):
        yield item["path"], item.get("line", 0), name


def _fallow_health_add(row: Row, path: str, item: dict) -> bool:
    """Add one fallow health finding; return whether it is over the ceiling."""
    cognitive = item.get("cognitive") or 0
    if cognitive > CEILING:
        finding = row.add(
            path, item.get("line", 0), "complexity", "cognitive-complexity", "warning",
            f"{item.get('name', '?')} has cognitive complexity {cognitive} (ceiling {CEILING})",
        )
    else:
        finding = row.add(
            path, item.get("line", 0), "complexity", str(item.get("exceeded", "threshold")).replace("_", "-"), "info",
            f"{item.get('name', '?')} exceeds fallow's {item.get('exceeded', '')} threshold (cyclomatic {item.get('cyclomatic', '?')}, cognitive {cognitive})",
            graded=False, reason="CRAP, cyclomatic and unit-size rows are advisory",
        )
    finding.data.update(score=cognitive, cyclomatic=item.get("cyclomatic", ""))
    return cognitive > CEILING


def ignored_by(run: Run, ignore_file: Path, cwd: Path, files: list[str]) -> list[str]:
    """The files a gitignore-syntax ignore file excludes, decided by git's own matcher."""
    probe = run.scratch_dir("ignore-probe", re.sub(r"[^A-Za-z0-9]+", "-", str(ignore_file)))
    try:
        (probe / ".gitignore").write_text(ignore_file.read_text(errors="replace"))
    except OSError:
        return []
    run.exec(None, ["git", "init", "-q", probe])
    relative = {str(Path(run.abs(f)).relative_to(cwd)): f for f in files if Path(run.abs(f)).is_relative_to(cwd)}
    done = run.exec(None, ["git", "-C", probe, "check-ignore", "--no-index", "--stdin"], stdin="".join(r + "\n" for r in relative))
    return [relative[line] for line in done.stdout.splitlines() if line in relative]
