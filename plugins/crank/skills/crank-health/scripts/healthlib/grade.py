"""Letters from findings: the shapes, weights and bands `references/grading.md` states.

Grading reads what is on disk in the run dir, so a triage edit to a findings file (a row
flipped to `advisory: <reason>`) moves the letter the next time `grade` runs.
"""

from __future__ import annotations

from dataclasses import dataclass

from .runner import CATEGORIES, Finding, Row, number

WEIGHT = {"critical": 5.0, "error": 5.0, "warning": 1.0, "info": 0.2}
DENSITY = {"lint": (1, 5, 15, 40), "types": (0, 1, 5, 15), "dead code": (0.5, 2, 5, 10)}
RATIO = {"complexity": (2, 5, 10, 20), "duplication": (3, 5, 10, 20), "format": (1, 10, 30, 60)}
ROLLUP = "rollup"


@dataclass
class Grade:
    unit: str
    category: str
    letter: str  # A to F, or "" when not assessed
    basis: str

    @property
    def text(self) -> str:
        return f"{self.letter} ({self.basis})" if self.letter else f"not assessed ({self.basis})"


def band(value: float, bands) -> str:
    for letter, ceiling in zip("ABCD", bands):
        if value <= ceiling:
            return letter
    return "F"


def owner_of(path: str, project_dirs: list[str]) -> str:
    """The project whose directory is the longest prefix of `path`."""
    best = ""
    for d in project_dirs:
        if d != "." and (path == d or path.startswith(d + "/")) and len(d) > len(best):
            best = d
    return best or "."


def _why_not(rows: list[Row], category: str, profile_note: str) -> str:
    reasons = []
    for row in rows:
        if category in row.categories and (row.state != "ok" or row.unmeasured):
            reasons.append(f"{row.tool}: {row.unmeasured or row.detail or row.state}")
    reasons = list(dict.fromkeys(reasons))
    shown = "; ".join(reasons[:4]) + (f"; … {len(reasons) - 4} more" if len(reasons) > 4 else "")
    return shown or profile_note


def grade(projects: list[dict], rows: list[Row], only: set[str], deep: bool) -> list[Grade]:
    """One grade per (project, category), then the rollup over the selection."""
    scanned = [p for p in projects if p["lines"]]
    by_project = _by_project(projects, rows)
    units = [(p["dir"], [p]) for p in scanned]
    if len(scanned) != 1:
        units.append((ROLLUP, scanned))
    return [g for unit, members in units for g in _unit_grades(unit, members, rows, by_project, only, deep)]


def _unit_grades(unit, members, rows, by_project, only, deep) -> list[Grade]:
    member_dirs = {p["dir"] for p in members}
    unit_rows = [r for r in rows if r.project in member_dirs or r.project == "repo"]
    found = _unit_found(unit, member_dirs, by_project)
    return [
        _category(unit, category, members, rows, unit_rows, found, deep) if category in only else Grade(unit, category, "", "not selected")
        for category in CATEGORIES
    ]


def _by_project(projects: list[dict], rows: list[Row]) -> dict[str, list[tuple[Row, Finding]]]:
    """Every finding of a row that ran, under its project; a repo-wide row's under the file's owner."""
    dirs = [p["dir"] for p in projects]
    by_project: dict[str, list[tuple[Row, Finding]]] = {p["dir"]: [] for p in projects}
    for row in (r for r in rows if r.state == "ok"):
        for finding in row.findings:
            home = row.project if row.project != "repo" else owner_of(finding.file, dirs)
            by_project.setdefault(home, []).append((row, finding))
    return by_project


def _unit_found(unit: str, member_dirs: set[str], by_project: dict[str, list[tuple[Row, Finding]]]) -> list[tuple[Row, Finding]]:
    """The unit's members' findings; the rollup also takes those no scanned project owns."""
    found = [pair for d in member_dirs for pair in by_project.get(d, [])]
    if unit == ROLLUP:
        found += [pair for d, pairs in by_project.items() if d not in member_dirs for pair in pairs]
    return found


def _category(unit, category, members, rows, unit_rows, found, deep) -> Grade:
    if category == "security":
        return _security(unit, unit_rows, found)
    if category in DENSITY:
        return _density(unit, category, members, unit_rows, found)
    if category == "duplication":
        return _duplication(unit, rows, {p["dir"] for p in members})
    if category in RATIO:
        return _ratio(unit, category, unit_rows, found)
    note = "deep tools are run by the agent" if deep else "quick profile never executes repo code"
    return Grade(unit, category, "", _why_not(unit_rows, category, note))


def _security(unit, rows, found) -> Grade:
    ran = [r for r in rows if "security" in r.categories and r.state == "ok"]
    if not ran:
        return Grade(unit, "security", "", _why_not(rows, "security", "no security tool ran"))
    mine = [f for _, f in found if f.category == "security" and not f.dropped]
    counts = {level: sum(1 for f in mine if f.graded and f.severity == level) for level in WEIGHT}
    advisory = sum(1 for f in mine if f.status == "advisory")
    return Grade(unit, "security", _security_letter(counts, bool(mine)), _security_basis(counts, advisory))


def _security_basis(counts: dict[str, int], advisory: int) -> str:
    basis = ", ".join(f"{n} {level}" for level, n in counts.items() if n) or "0 findings"
    basis += " (graded)" if any(counts.values()) else ""
    basis += f"; {advisory} advisory" if advisory else ""
    return basis


def _security_letter(counts: dict[str, int], any_kept: bool) -> str:
    if counts["critical"]:
        return "F"
    if counts["error"]:
        return "D"
    if counts["warning"] > 2 or counts["info"] > 10:
        return "C"
    return "B" if any_kept else "A"


def _graders(rows, project_dir: str, language: str, category: str) -> list[Row]:
    return [
        r
        for r in rows
        if r.project == project_dir and r.language == language and category in r.categories and r.state == "ok" and not r.stood_down and not r.unmeasured
    ]


def _measured_lines(category, members, rows) -> tuple[int, bool]:
    """Lines of the languages some tool graded `category` in, and whether there were any."""
    lines = 0
    assessed = False
    for project in members:
        for language, count in project["lines"].items():
            graders = _graders(rows, project["dir"], language, category)
            if not graders:
                continue
            lines += count
            assessed = True
            if category == "lint" and any(r.reads_assets for r in graders):
                lines += sum(project.get("asset_lines", {}).values())
    return lines, assessed


def _density(unit, category, members, rows, found) -> Grade:
    lines, assessed = _measured_lines(category, members, rows)
    if not assessed:
        return Grade(unit, category, "", _why_not(rows, category, "no tool measures it here"))
    weighted = sum(WEIGHT.get(f.severity, 0) for _, f in found if f.category == category and f.graded)
    kloc = lines / 1000
    if weighted == 0:
        return Grade(unit, category, "A", f"0 weighted / {_kloc(kloc)} KLOC = 0.0")
    if kloc == 0:
        return Grade(unit, category, "F", f"{number(weighted)} weighted / 0 KLOC")
    value = weighted / kloc
    return Grade(unit, category, band(value, DENSITY[category]), f"{number(weighted)} weighted / {_kloc(kloc)} KLOC = {value:.2f}")


def _kloc(kloc: float) -> str:
    return f"{kloc:.1f}" if kloc >= 1 else f"{kloc:.3f}"


def _ratio(unit, category, rows, found) -> Grade:
    graders = [r for r in rows if r.state == "ok" and category in r.metrics and not r.stood_down and not r.unmeasured]
    if not graders:
        return Grade(unit, category, "", _why_not(rows, category, "no tool measures it here"))
    keys = {r.key for r in graders}
    numerator = sum(1 for row, f in found if row.key in keys and f.category == category and f.graded)
    denominator = sum(r.metrics[category].denominator for r in graders)
    unit_name = graders[0].metrics[category].unit
    if denominator == 0:
        return Grade(unit, category, "", f"0 {unit_name.split(' ')[0]} measured")
    percent = 100 * numerator / denominator
    return Grade(
        unit, category, band(percent, RATIO[category]), f"{numerator} / {number(denominator)} {unit_name} = {percent:.2f}%"
    )


def _duplication(unit, rows, member_dirs) -> Grade:
    want = "repo" if unit == ROLLUP else unit
    passes = [r for r in rows if "duplication" in r.categories and r.project == want]
    row = next((r for r in passes if r.state == "ok" and "duplication" in r.metrics), None)
    if row is None:
        return Grade(unit, "duplication", "", _why_not(passes, "duplication", "no duplication pass covers it"))
    metric = row.metrics["duplication"]
    if metric.denominator == 0:
        return Grade(unit, "duplication", "", "no file reached jscpd")
    return Grade(
        unit,
        "duplication",
        band(metric.percent, RATIO["duplication"]),
        f"{number(metric.numerator)} / {number(metric.denominator)} tokens = {metric.percent:.2f}%",
    )


def line(grades: list[Grade], unit: str) -> str:
    mine = {g.category: g for g in grades if g.unit == unit}
    return " · ".join(f"{c} {mine[c].letter or 'not assessed'}" for c in CATEGORIES if c in mine)
