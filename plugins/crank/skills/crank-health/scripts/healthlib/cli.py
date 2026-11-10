"""crank-health's mechanical half: inventory a repo, choose its analyzers, run them, and
normalize what they print. Judgment (triage, the plan) stays with the agent.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import datetime
import fnmatch
import os
import re
import secrets
import shutil
import sys
import tempfile
import time
from collections import Counter
from pathlib import Path

from . import common, cpp, csharp, go, jsts, python, report, settle
from . import grade as grading
from . import inventory as inv
from .runner import CATEGORIES, Finding, Row, Run, execute

MODULES = {"js-ts": jsts, "python": python, "go": go, "csharp": csharp, "c-cpp": cpp}
PATH_PROBES = {
    "git": ["git", "--version"],
    "uv": ["uv", "--version"],
    "node": ["node", "--version"],
    "go": ["go", "version"],
    "dotnet": ["dotnet", "--version"],
    "cmake": ["cmake", "--version"],
    "meson": ["meson", "--version"],
    "gitleaks": ["gitleaks", "version"],
    "osv-scanner": ["osv-scanner", "--version"],
    "opengrep": ["opengrep", "--version"],
}
SECRET = re.compile(rb"AKIA[0-9A-Z]{16}|BEGIN [A-Z ]*PRIVATE KEY|ghp_[A-Za-z0-9]{36}|xox[baprs]-|sk-[A-Za-z0-9]{20,}")


def say(text: str) -> None:
    print(text, file=sys.stderr, flush=True)


def path_facts(run: Run) -> dict[str, str]:
    facts = {}
    for name, argv in PATH_PROBES.items():
        facts[name] = run.version("path:" + name, argv) if run.which(name) else ""
    return facts


def plan_rows(run: Run) -> list[Row]:
    rows: list[Row] = []
    for project in run.inv.scanned():
        real = [lang for lang in project.files if lang not in project.fixture_only]
        for language in report.LANGUAGE_ORDER:
            if language not in project.files:
                continue
            if language in project.fixture_only and real:
                continue  # one sample file per language under tests/fixtures is not a codebase
            rows += MODULES[language].plan(run, project)
    rows += common.plan(run)
    return [r for r in rows if set(r.categories) & run.only]


def run_rows(run: Run, rows: list[Row], jobs: int) -> None:
    pending = [r for r in rows if r.job is not None]
    with concurrent.futures.ThreadPoolExecutor(max_workers=jobs) as pool:
        futures = {pool.submit(execute, run, row): row for row in pending}
        for n, future in enumerate(concurrent.futures.as_completed(futures), 1):
            row = futures[future]
            future.result()
            tail = "" if row.state == "ok" else f": {row.detail}"
            say(f"[{n}/{len(pending)}] {row.state:<13} {row.tool} ({row.project}) {row.seconds:.1f}s{tail}")


def read_ownership(repo: Path, inventory: inv.Inventory, list_unowned: bool) -> None:
    for project in inventory.projects:
        for language in project.files:
            module = MODULES[language]
            project.owned.update(module.owned(repo, project))
            if list_unowned:
                project.unowned += [t for t in module.OWNABLE if t not in project.owned]


def run_meta(repo: Path, run_dir: Path, run: Run, deep: bool) -> dict:
    return {
        "run_dir": str(run_dir),
        "repo": str(repo),
        "head": run.inv.head,
        "head_full": inv.git(repo, "rev-parse", "HEAD").stdout.decode().strip(),
        "profile": "deep" if deep else "quick",
        "selected": run.inv.selected,
        "only": [c for c in CATEGORIES if c in run.only],
        "started": time.time(),
        "date": datetime.date.today().isoformat(),
        "pins": run.pins,
    }


def scan_tree(repo: Path, run_dir: Path, opts, pins: dict, extra: list[str], strict: bool = False) -> dict:
    """Inventory, plan and (unless `--plan`) run one working tree into `run_dir`; `strict` makes
    a `--project` that names no project raise `inv.InventoryError`."""
    inventory = inv.build(repo, opts.project, strict)
    for part in ("scratch", "raw", "findings", "summary"):
        (run_dir / part).mkdir(parents=True, exist_ok=True)
    read_ownership(repo, inventory, list_unowned=True)
    (run_dir / "footprint.txt").write_text(inv.footprint(repo))
    (run_dir / "scope.txt").write_text("".join(f + "\n" for f in inventory.files))

    run = Run(inventory, run_dir, deep=opts.deep, only=opts.only, pins=pins, budget_scale=opts.budget_scale)
    grades: list[grading.Grade] = []
    try:
        rows = plan_rows(run)
        facts = path_facts(run)
        meta = run_meta(repo, run_dir, run, opts.deep)
        projects = [p.record() for p in inventory.projects]
        (run_dir / "inventory.md").write_text(report.inventory_md(inventory, facts, extra))
        if opts.plan:
            (run_dir / "tools.md").write_text(report.tools_md(meta, rows))
            report.write_results(run_dir, meta, projects, rows)
        else:
            run_rows(run, rows, opts.jobs)
            settle.settle(inventory, rows)
            grades = write_all(run_dir, meta, projects, rows, "mechanical, before triage")
    finally:
        run.cleanup()
    return {"meta": meta, "projects": projects, "rows": rows, "inventory": inventory, "grades": grades}


def write_all(run_dir: Path, meta: dict, projects: list[inv.ProjectRecord], rows: list[Row], stage: str) -> list[grading.Grade]:
    report.write_findings(run_dir, rows)
    report.write_summaries(run_dir, projects, rows)
    (run_dir / "tools.md").write_text(report.tools_md(meta, rows))
    report.write_results(run_dir, meta, projects, rows)
    grades = grading.grade(projects, rows, set(meta["only"]), meta["profile"] == "deep")
    (run_dir / "grades.md").write_text(report.grades_md(grades, stage))
    return grades


def digest(run_dir: Path, rows: list[Row], grades: list[grading.Grade], stage: str) -> None:
    headline = grading.headline(grades)
    print(f"run dir: {run_dir}")
    if headline:
        print(f"grades ({stage}): {grading.line(grades, headline)}")
    states = Counter(r.state for r in rows)
    print("rows: " + ", ".join(f"{n} {state}" for state, n in sorted(states.items())))
    for row in rows:
        if row.state in ("error", "timeout", "not-available"):
            print(f"  {row.state}: {row.tool} ({row.project}): {row.detail}")
    checks: dict[str, list[str]] = {}
    for row in rows:
        for note in (n for n in row.notes if n.startswith("check:")):
            checks.setdefault(note, []).append(f"{row.tool} ({row.project})")
    for note, where in checks.items():
        print(f"  {note} [{', '.join(where)}]")
    print("read next: grades.md, inventory.md, tools.md, summary/*.md, findings/<project>/<tool>.tsv")


def new_run_dir(repo: Path, override: str | None) -> Path:
    if override:
        path = Path(override).resolve()
    else:
        home = repo / ".crank-health"
        home.mkdir(exist_ok=True)
        ignore = home / ".gitignore"
        if not ignore.exists():
            ignore.write_text("*\n")
        path = home / f"{datetime.date.today().isoformat()}-{secrets.token_hex(2)}"
    path.mkdir(parents=True, exist_ok=True)
    return path


def cmd_scan(opts) -> int:
    repo = Path(opts.path).resolve()
    if not repo.is_dir():
        say(f"not a directory: {repo}")
        return 2
    run_dir = new_run_dir(repo, opts.run_dir)
    extra = []
    base_sha = ""
    if opts.pr:
        found = inv.git(repo, "merge-base", opts.pr, "HEAD")
        base_sha = found.stdout.decode().strip()
        if found.returncode != 0 or not base_sha:
            say(f"--pr {opts.pr}: no merge-base with HEAD ({found.stderr.decode().strip()})")
            return 2
        extra.append(f"pr mode: base {opts.pr} · merge-base {base_sha[:10]}")
    try:
        head = scan_tree(repo, run_dir, opts, {}, extra, strict=True)
    except inv.InventoryError as err:
        say(str(err))
        return 2
    grades = head["grades"]
    if opts.plan:
        print(f"run dir: {run_dir}")
        print("planned only: read inventory.md and tools.md; nothing ran")
        return 0
    if opts.pr:
        pr_mode(repo, run_dir, opts, head, base_sha, grades)
    moved = inv.git(repo, "rev-parse", "HEAD").stdout.decode().strip()
    if moved != head["meta"]["head_full"]:
        print(f"check: HEAD moved during the scan ({head['meta']['head_full'][:10]} -> {moved[:10]}); findings describe a mix of both")
    digest(run_dir, head["rows"], grades, "mechanical, before triage")
    if opts.pr:
        print("pr mode: read pr.md, new-findings.tsv, resolved-findings.tsv")
    return 0


def finding_key(finding: Finding, renames: dict[str, str] | None = None) -> tuple:
    file = (renames or {}).get(finding.file, finding.file)
    return (finding.category, finding.rule, file, re.sub(r"\d+", "#", finding.message))


def changed_lines(repo: Path, base_sha: str) -> tuple[dict[str, str], dict[str, list[tuple[int, int]]]]:
    """Renames (old path -> new path) and, per file, the line ranges the diff added or changed."""
    renames, hunks = {}, {}
    status = inv.git(repo, "diff", "-M", "--name-status", base_sha).stdout.decode("utf-8", "replace")
    for line in status.splitlines():
        parts = line.split("\t")
        if parts[0].startswith("R") and len(parts) == 3:
            renames[parts[1]] = parts[2]
        if len(parts) >= 2:
            hunks.setdefault(parts[-1], [])
    current = None
    diff = inv.git(repo, "diff", "-U0", "-M", "--no-color", base_sha).stdout.decode("utf-8", "replace")
    for line in diff.splitlines():
        if line.startswith("+++ "):
            current = line[6:] if line.startswith("+++ b/") else None
        elif current and (span := hunk_span(line)):
            hunks.setdefault(current, []).append(span)
    return renames, hunks


def hunk_span(line: str) -> tuple[int, int] | None:
    """The first and last new-side line of a `@@` header that adds lines, else None."""
    m = re.match(r"@@ -\S+ \+(\d+)(?:,(\d+))? @@", line)
    if not m:
        return None
    start, count = int(m.group(1)), int(m.group(2) or 1)
    return (start, start + count - 1) if count else None


def link_dependencies(repo: Path, tree: Path, inventory: inv.Inventory) -> list[str]:
    """Installed dependencies are untracked, so the base tree borrows the head's."""
    linked = []
    for project in inventory.projects:
        for name in ("node_modules", ".venv", "venv"):
            source, target = repo / project.dir / name, tree / project.dir / name
            if source.is_dir() and target.parent.is_dir() and not target.exists():
                target.symlink_to(source, target_is_directory=True)
                linked.append(name if project.dir == "." else f"{project.dir}/{name}")
    return linked


def scan_base(repo: Path, run_dir: Path, opts, head: dict, base_sha: str) -> tuple[dict, list[str]] | None:
    """Scan the merge-base in a throwaway worktree; None when git cannot check it out."""
    holder = Path(tempfile.mkdtemp(prefix="crank-health-base-"))
    tree = holder / "base"
    added = inv.git(repo, "worktree", "add", "--detach", str(tree), base_sha)
    if added.returncode != 0:
        say("pr mode: git worktree add failed: " + added.stderr.decode().strip())
        shutil.rmtree(holder, ignore_errors=True)
        return None
    try:
        linked = link_dependencies(repo, tree, head["inventory"])
        say(f"pr mode: scanning merge-base {base_sha[:10]} with the head's tool versions")
        extra = [f"base tree of {repo} at {base_sha[:10]}; borrowed from head: {', '.join(linked) or 'nothing'}"]
        base = scan_tree(tree, run_dir / "base", opts, dict(head["meta"]["pins"]), extra)
    finally:
        inv.git(repo, "worktree", "remove", "--force", str(tree))
        inv.git(repo, "worktree", "prune")
        shutil.rmtree(holder, ignore_errors=True)
    return base, linked


def ok_findings(rows: list[Row]) -> list[Finding]:
    return [f for r in rows if r.state == "ok" for f in r.findings]


def unmatched(findings: list[Finding], counts: Counter, key) -> list[Finding]:
    """The findings left once each one consumes a match from `counts`, in the order given."""
    left = []
    for finding in findings:
        k = key(finding)
        if counts[k] > 0:
            counts[k] -= 1
        else:
            left.append(finding)
    return left


def mark_touched(finding: Finding, hunks: dict[str, list[tuple[int, int]]]) -> None:
    ranges = hunks.get(finding.file)
    line = finding.line
    if ranges is not None and (not line or any(a <= line <= b for a, b in ranges)):
        finding.flags = ["touched", *finding.flags]


def delta_row(g: grading.Grade, was: grading.Grade | None, new: list[Finding], resolved: list[Finding]) -> list:
    fresh = [f for f in new if f.category == g.category]
    graded = [f for f in fresh if f.graded]
    return [
        g.category,
        (was.letter or "not assessed") if was else "absent",
        g.letter or "not assessed",
        len(graded),
        sum(1 for f in graded if "touched" in f.flags),
        len(fresh) - len(graded),
        sum(1 for f in resolved if f.category == g.category and f.graded),
    ]


def delta_table(head_grades, base_grades, new: list[Finding], resolved: list[Finding]) -> list[str]:
    unit = grading.headline(head_grades)
    before = {g.category: g for g in base_grades if g.unit == unit}
    if not before and base_grades:
        first = base_grades[0].unit
        before = {g.category: g for g in base_grades if g.unit == first}
    body = [delta_row(g, before.get(g.category), new, resolved) for g in head_grades if g.unit == unit]
    return report._table(["category", "base", "head", "new graded", "of which touched", "new advisory", "resolved graded"], body)


def pr_mode(repo: Path, run_dir: Path, opts, head: dict, base_sha: str, head_grades) -> None:
    scanned = scan_base(repo, run_dir, opts, head, base_sha)
    if scanned is None:
        return
    base, linked = scanned
    renames, hunks = changed_lines(repo, base_sha)
    base_grades = grading.grade(base["projects"], base["rows"], set(base["meta"]["only"]), opts.deep)

    head_found, base_found = ok_findings(head["rows"]), ok_findings(base["rows"])
    base_counts = Counter(finding_key(f, renames) for f in base_found)
    head_counts = Counter(finding_key(f) for f in head_found)
    new = unmatched(sorted(head_found, key=lambda f: (f.file, f.line)), base_counts, finding_key)
    for finding in new:
        mark_touched(finding, hunks)
    resolved = unmatched(base_found, head_counts, lambda f: finding_key(f, renames))
    rank = {category: n for n, category in enumerate(CATEGORIES)}
    new.sort(key=lambda f: ("touched" not in f.flags, not f.graded, rank.get(f.category, 9), settle.order(f)))
    resolved.sort(key=lambda f: (rank.get(f.category, 9), settle.order(f)))
    (run_dir / "new-findings.tsv").write_text("".join(f.tsv() + "\n" for f in new))
    (run_dir / "resolved-findings.tsv").write_text("".join(f.tsv() + "\n" for f in resolved))

    out = [
        "# PR delta",
        "",
        f"base `{opts.pr}` · merge-base `{base_sha[:10]}` · {len(hunks)} files changed · {len(renames)} renamed",
        f"base tree borrowed from head: {', '.join(linked) or 'nothing'}",
        "",
    ]
    out += delta_table(head_grades, base_grades, new, resolved)
    out += [
        "",
        "Finding sets are keyed on (category, tool/rule, file after rename mapping, message with numbers masked).",
        "`new-findings.tsv` lists head minus base, touched lines first; `resolved-findings.tsv` lists base minus head.",
        "Base evidence: `base/` holds its own inventory.md, tools.md, grades.md, summary/ and findings/.",
    ]
    (run_dir / "pr.md").write_text("\n".join(out) + "\n")


def cmd_rerun(opts) -> int:
    run_dir = Path(opts.run_dir).resolve()
    meta, projects, old_rows = report.read_results(run_dir)
    repo = Path(meta["repo"])
    inventory = inv.build(repo, meta["selected"])
    read_ownership(repo, inventory, list_unowned=False)
    run = Run(inventory, run_dir, deep=meta["profile"] == "deep", only=meta["only"], pins=meta["pins"], budget_scale=opts.budget_scale)
    for key in run.unread_overrides():
        say(f"overrides.json: no tool reads the key `{key}`; only {' and '.join(Run.OVERRIDABLE)} take overrides")
    try:
        fresh = [r for r in plan_rows(run) if rerun_wanted(r, opts)]
        if not fresh:
            say("no row matches; tools.md lists the tool and project names")
            return 2
        run_rows(run, fresh, opts.jobs)
    finally:
        run.cleanup()
    rows, kept = merge_rerun(old_rows, fresh)
    verdicts = verdicts_of(old_rows)  # before settle, which changes old findings in place
    settle.settle(inventory, rows)
    keep_verdicts(verdicts, rows)
    grades = write_all(run_dir, meta, projects, rows, "after a rerun")
    print_rerun(fresh, kept)
    digest(run_dir, rows, grades, "after a rerun")
    return 0


def merge_rerun(old_rows: list[Row], fresh: list[Row]) -> tuple[list[Row], list[tuple[Row, Row]]]:
    """The run's rows with each fresh row in its old row's place, except that an old `ok` row
    stays when its fresh row is not `ok`; also returns those (old, fresh) pairs."""
    by_key = {r.key: r for r in fresh}
    rows, kept = [], []
    for old in old_rows:
        new = by_key.pop(old.key, old)
        if old.state == "ok" and new.state != "ok":
            kept.append((old, new))
            new = old
        rows.append(new)
    return rows + list(by_key.values()), kept


def print_rerun(fresh: list[Row], kept: list[tuple[Row, Row]]) -> None:
    kept_old = {new.key: old for old, new in kept}
    for row in fresh:
        if (old := kept_old.get(row.key)) is not None:
            print(f"{row.tool} ({row.project}): rerun ended {row.state}: {row.detail}; kept the previous ok row and its {len(old.findings)} findings")
            continue
        graded = sum(1 for f in row.findings if f.graded)
        print(f"{row.tool} ({row.project}): {row.state}, {graded} graded, {len(row.findings) - graded} advisory or dropped")


def rerun_wanted(row: Row, opts) -> bool:
    wanted_tools = {t.replace("-", " ") for t in opts.tool}
    wanted_projects = {inv.project_dir(p) for p in opts.project}
    return (not wanted_tools or row.tool.replace("-", " ") in wanted_tools) and (not wanted_projects or row.project in wanted_projects)


def verdicts_of(rows: list[Row]) -> dict[tuple, tuple[str, str, bool]]:
    """Each finding's (status, reason, touched), under its line-qualified key and its bare
    `finding_key`. Two findings of one rule and message in one file share the bare key."""
    verdicts = {}
    for finding in (f for r in rows for f in r.findings):
        kept = (finding.status, finding.reason, "touched" in finding.flags)
        verdicts[finding_key(finding)] = kept
        verdicts[(*finding_key(finding), finding.line)] = kept
    return verdicts


def keep_verdicts(verdicts: dict[tuple, tuple[str, str, bool]], rows: list[Row]) -> None:
    """A finding that survives a rerun keeps the verdict triage gave it; the bare key serves a
    finding whose line moved."""
    for finding in (f for r in rows for f in r.findings):
        if (kept := verdicts.get((*finding_key(finding), finding.line)) or verdicts.get(finding_key(finding))) is not None:
            finding.status, finding.reason = kept[:2]


def rule_matches(rule: str, pattern: str) -> bool:
    return fnmatch.fnmatchcase(rule.split("/", 1)[-1], pattern) or fnmatch.fnmatchcase(rule, pattern)


def verdict_row_matches(row: Row, opts) -> bool:
    if opts.tool and row.tool.replace("-", " ") != opts.tool.replace("-", " "):
        return False
    return not opts.project or row.project == inv.project_dir(opts.project)


def verdict_finding_matches(finding: Finding, opts) -> bool:
    checks = (
        (opts.category, lambda: finding.category == opts.category),
        (opts.rule, lambda: rule_matches(finding.rule, opts.rule)),
        (opts.path, lambda: fnmatch.fnmatchcase(finding.file, opts.path)),
        (opts.flag, lambda: opts.flag in finding.flags),
        (opts.line is not None, lambda: str(finding.line or "") == opts.line),
        (opts.message, lambda: opts.message in finding.message),
    )
    return all(test() for given, test in checks if given)


def verdict_problem(opts, rows: list[Row]) -> str | None:
    """Why the verdict's filters cannot run: none given, or a `--project` no row belongs to."""
    filters = (opts.tool, opts.project, opts.category, opts.rule, opts.path, opts.flag, opts.line, opts.message)
    if not any(f is not None for f in filters):
        return "give at least one filter, so a verdict never lands on every finding by accident"
    if opts.project is not None and not any(r.project == inv.project_dir(opts.project) for r in rows):
        return f"--project {opts.project}: no row has that project; projects: {', '.join(sorted({r.project for r in rows}))}"
    return None


def cmd_verdict(opts) -> int:
    run_dir = Path(opts.run_dir).resolve()
    meta, projects, rows = report.read_results(run_dir)
    if (problem := verdict_problem(opts, rows)) is not None:
        say(problem)
        return 2
    status, reason = ("graded", "") if opts.graded else ("advisory", opts.advisory) if opts.advisory else ("dropped", opts.dropped)
    changed = 0
    for finding in (f for r in rows if verdict_row_matches(r, opts) for f in r.findings if verdict_finding_matches(f, opts)):
        if (finding.status, finding.reason) != (status, reason):
            finding.status, finding.reason = status, reason
            changed += 1
    grades = write_all(run_dir, meta, projects, rows, "after triage")
    unit = grading.headline(grades)
    print(f"{changed} findings now read `{status}{': ' + reason if reason else ''}`")
    print(f"grades (after triage): {grading.line(grades, unit)}")
    return 0


def cmd_grade(opts) -> int:
    run_dir = Path(opts.run_dir).resolve()
    meta, projects, rows = report.read_results(run_dir)
    grades = grading.grade(projects, rows, set(meta["only"]), meta["profile"] == "deep")
    report.write_summaries(run_dir, projects, rows)
    (run_dir / "grades.md").write_text(report.grades_md(grades, "after triage"))
    print(report.grades_md(grades, "after triage"))
    return 0


def cmd_finish(opts) -> int:
    run_dir = Path(opts.run_dir).resolve()
    meta, _projects, _rows = report.read_results(run_dir)
    repo = Path(meta["repo"])
    for scratch in (run_dir / "scratch", run_dir / "base" / "scratch"):
        shutil.rmtree(scratch, ignore_errors=True)
    leaks = secret_leaks(run_dir)
    before = set((run_dir / "footprint.txt").read_text().splitlines())
    left = [line for line in inv.footprint(repo).splitlines() if line not in before]
    touched = written_since(repo, run_dir, meta["started"])
    moved = inv.git(repo, "rev-parse", "HEAD").stdout.decode().strip()
    print("scratch: removed")
    print_listing("secret patterns in the run dir: ", leaks)
    print_listing("footprint (paths git status shows now and not before the scan): ", left)
    print_listing("written since the scan started, outside the run dir: ", touched[:40])
    if len(touched) > 40:
        print(f"  … {len(touched) - 40} more")
    if moved != meta["head_full"]:
        print(f"HEAD moved since the scan: {meta['head_full'][:10]} -> {moved[:10]}")
    return 1 if leaks or left else 0


def secret_leaks(run_dir: Path) -> list[str]:
    leaks = []
    for base, _dirs, files in os.walk(run_dir):
        for name in files:
            path = Path(base) / name
            try:
                if SECRET.search(path.read_bytes()):
                    leaks.append(str(path))
            except OSError:
                continue
    return leaks


def print_listing(heading: str, items: list[str]) -> None:
    print(heading + ("none" if not items else ""))
    for item in items:
        print(f"  {item}")


def written_since(repo: Path, run_dir: Path, started: float) -> list[str]:
    """Files created or changed after the scan began, ignored ones included: a cache a tool
    left under `node_modules/.cache` never shows in `git status`."""
    found = []
    skip = {str(repo / ".git"), str(run_dir), str(repo / ".crank-health")}
    stack = [str(repo)]
    while stack:
        here = stack.pop()
        try:
            entries = list(os.scandir(here))
        except OSError:
            continue
        for entry in entries:
            if entry.path in skip:
                continue
            try:
                if entry.is_dir(follow_symlinks=False):
                    stack.append(entry.path)
                elif entry.stat(follow_symlinks=False).st_mtime > started:
                    found.append(os.path.relpath(entry.path, repo))
            except OSError:
                continue
    return sorted(found)


def categories(text: str) -> list[str]:
    wanted = [c.strip().lower().replace("-", " ").replace("_", " ") for c in text.split(",") if c.strip()]
    unknown = [c for c in wanted if c not in CATEGORIES]
    if unknown:
        raise argparse.ArgumentTypeError(f"unknown categories: {', '.join(unknown)}; choose from {', '.join(CATEGORIES)}")
    return wanted


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="health.py", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)

    scan = sub.add_parser("scan", help="inventory, choose tools, run them, write the run dir")
    scan.add_argument("path", nargs="?", default=".")
    scan.add_argument("--pr", metavar="BASE", help="also scan the merge-base and diff the finding sets")
    scan.add_argument("--deep", action="store_true", help="list the deep tools the agent runs from the references")
    scan.add_argument("--only", type=categories, default=list(CATEGORIES), metavar="CATEGORY,…")
    scan.add_argument("--project", action="append", default=[], metavar="DIR", help="repeatable; the selection is the union")
    scan.add_argument("--plan", action="store_true", help="write inventory.md and tools.md, run nothing")
    scan.add_argument("--run-dir", help="default: <path>/.crank-health/<date>-<4 hex>")
    scan.set_defaults(run=cmd_scan)

    rerun = sub.add_parser("rerun", help="run some rows again with the run's pinned versions, keep triage verdicts, re-grade")
    rerun.add_argument("run_dir")
    rerun.add_argument("--tool", action="append", default=[], metavar="NAME", help="as tools.md names it; repeatable")
    rerun.add_argument("--project", action="append", default=[], metavar="DIR")
    rerun.set_defaults(run=cmd_rerun)

    for command in (scan, rerun):
        command.add_argument("--jobs", type=int, default=4, help="tools run in parallel (default 4)")
        command.add_argument("--budget-scale", type=float, default=1.0, metavar="N", help="multiply every tool budget, for a large repo")

    verdict = sub.add_parser("verdict", help="triage in bulk: set the verdict of the findings the filters select, then re-grade")
    verdict.add_argument("run_dir")
    how = verdict.add_mutually_exclusive_group(required=True)
    how.add_argument("--advisory", metavar="REASON", help="keep the row, take it out of the grade")
    how.add_argument("--dropped", metavar="REASON", help="take the row out of every count: a false positive, a fixture")
    how.add_argument("--graded", action="store_true", help="count the row toward its grade")
    verdict.add_argument("--tool", help="as tools.md names it")
    verdict.add_argument("--project", metavar="DIR")
    verdict.add_argument("--category")
    verdict.add_argument("--rule", metavar="GLOB", help="matched against the rule with or without its tool prefix")
    verdict.add_argument("--path", metavar="GLOB", help="matched against the repo-relative file")
    verdict.add_argument("--flag", help="test, snapshot, generated or touched")
    verdict.add_argument("--line")
    verdict.add_argument("--message", metavar="TEXT", help="a substring of the message")
    verdict.set_defaults(run=cmd_verdict)

    grade = sub.add_parser("grade", help="letters and summaries from the findings files as they stand")
    grade.add_argument("run_dir")
    grade.set_defaults(run=cmd_grade)

    finish = sub.add_parser("finish", help="delete scratch, grep the run dir for secrets, compare the footprint")
    finish.add_argument("run_dir")
    finish.set_defaults(run=cmd_finish)

    opts = parser.parse_args(argv)
    return opts.run(opts)
