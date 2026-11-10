"""The table-lookup calls made once every tool has run: a standby stands down, a hit
outside the inventory leaves, one defect seen by two tools is counted once.

Everything here is a rule `references/grading.md` or `references/run-dir.md` states as a lookup.
Whether a finding is a false positive, a fixture or a public API stays with the agent.
"""

from __future__ import annotations

from . import go
from . import inventory as inv
from .runner import Row


def settle(inventory: inv.Inventory, rows: list[Row]) -> None:
    stand_down(rows)
    for row in rows:
        if row.state == "ok":
            drop_out_of_scope(inventory, row)
            flag(inventory, row)
    for row in rows:
        row.findings.sort(key=order)  # tools print in the order their workers finish
    go.join_vulnerabilities(rows)
    one_defect_one_finding(rows)


def order(finding) -> tuple:
    return (finding.file, finding.line, finding.category, finding.rule, finding.message)


def stand_down(rows: list[Row]) -> None:
    """A default tool running behind an owner keeps its findings only when the owner failed."""
    for row in rows:
        if not row.standby_behind or row.state != "ok":
            continue
        owner = next((r for r in rows if r.project == row.project and r.tool == row.standby_behind), None)
        if owner is not None:
            _settle_standby(row, owner)


def _settle_standby(row: Row, owner: Row) -> None:
    shared = [c for c in row.categories if c in owner.categories]
    excluded = owner.state == "skipped" and owner.detail.startswith("nothing to scan")
    if owner.state != "ok" and not excluded:
        graded = sum(1 for f in row.findings if f.graded and f.category in shared)
        row.notes.append(
            f"{row.tool} graded {', '.join(shared)} on its default config because {owner.tool} reported {owner.state}"
            f" ({graded} graded, {sum(1 for f in row.findings if f.category in shared) - graded} advisory)"
        )
        return
    row.findings = [f for f in row.findings if f.category not in shared]
    for category in shared:
        row.metrics.pop(category, None)
    row.stood_down = set(shared) == set(row.categories)
    if excluded:
        # the repo's own config skips these files, so no default tool grades them instead
        row.notes.append(f"standby stood down: {owner.tool}'s config excludes every file here, so {', '.join(shared)} is not assessed")
    else:
        row.notes.append(f"standby stood down: {owner.tool} graded {', '.join(shared)}")


def drop_out_of_scope(inventory: inv.Inventory, row: Row) -> None:
    scope = set(inventory.files)
    outside = [f for f in row.findings if f.file and f.file not in scope]
    if not outside:
        return
    row.findings = [f for f in row.findings if not (f.file and f.file not in scope)]
    tops: dict[str, int] = {}
    for finding in outside:
        top = finding.file.split("/", 1)[0]
        tops[top] = tops.get(top, 0) + 1
    where = ", ".join(f"{top} {n}" for top, n in sorted(tops.items(), key=lambda kv: -kv[1])[:6])
    row.notes.append(f"{len(outside)} findings outside the inventory dropped, count only ({where})")


def flag(inventory: inv.Inventory, row: Row) -> None:
    generated = set(inventory.generated)
    for finding in row.findings:
        marks = []
        if inv.is_test_path(finding.file):
            marks.append("test")
        if inv.under_snapshot(finding.file):
            marks.append("snapshot")
        if finding.file in generated:
            marks.append("generated")
        finding.flags = marks


def one_defect_one_finding(rows: list[Row]) -> None:
    """Two tools naming the same place in the same category is one defect: the row from the
    earlier tool in `tools.md` stays graded and the others cite it."""
    seen: dict[tuple, str] = {}
    secret_files = {f.file: f.rule for f in _ok_findings(rows, "gitleaks")}
    dead_imports = {
        (f.file, f.line): f.rule for f in _ok_findings(rows, "vulture") if f.rule.endswith("/unused-import") and f.graded
    }
    for row in (r for r in rows if r.state == "ok"):
        for finding in (f for f in row.findings if f.graded):
            original = _original_of(row, finding, secret_files, dead_imports, seen)
            if original is not None:
                finding.demote(f"duplicate of {original}")


def _ok_findings(rows: list[Row], tool: str) -> list:
    return [f for row in rows if row.state == "ok" and row.tool == tool for f in row.findings]


def _original_of(row: Row, finding, secret_files: dict[str, str], dead_imports: dict[tuple, str], seen: dict[tuple, str]) -> str | None:
    """The rule an earlier finding of the same defect carries, or None when this one is the first.
    Records the finding's place in `seen` once the specific duplicates rule it out."""
    if row.tool != "gitleaks" and finding.severity == "critical" and finding.file in secret_files:
        return secret_files[finding.file]
    if finding.rule == "ruff-check/F401" and (finding.file, finding.line) in dead_imports:
        return dead_imports[(finding.file, finding.line)]
    if not finding.line:
        return None
    first = seen.setdefault((finding.category, finding.file, finding.line), finding.rule)
    if first != finding.rule and first.split("/", 1)[0] != finding.rule.split("/", 1)[0]:
        return first
    return None
