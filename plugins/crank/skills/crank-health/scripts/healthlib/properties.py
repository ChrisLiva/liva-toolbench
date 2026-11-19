"""Property tests as context: the row and the offer `references/properties.md` states.

The row reads a project's test files and executes nothing, so it runs in the quick profile.
"""

from __future__ import annotations

import re
from functools import partial

from . import inventory as inv
from .runner import Row, Run

TOOL = "property tests"
# language: (the library the scan offers, how to install it, {library: what a test that uses it contains})
LIBRARIES: dict[str, tuple[str, str, dict[str, bytes]]] = {
    "js-ts": (
        "fast-check",
        "npm install --save-dev fast-check",
        {"fast-check": rb"""['"](?:fast-check|@fast-check/[\w-]+)['"]"""},
    ),
    "python": ("hypothesis", "uv add --dev hypothesis", {"hypothesis": rb"^\s*(?:from|import)\s+hypothesis\b"}),
    "go": (
        "rapid",
        "go get pgregory.net/rapid",
        {
            "rapid": rb'"pgregory\.net/rapid"',
            "gopter": rb'"github\.com/leanovate/gopter',
            "testing/quick": rb'"testing/quick"',
            "go fuzz": rb"^func Fuzz\w*\(\w+ \*testing\.F\)",
        },
    ),
    "csharp": (
        "CsCheck",
        "dotnet add <test project> package CsCheck",
        {name: rb"^\s*using\s+" + name.encode() + rb"\b" for name in ("FsCheck", "CsCheck", "Hedgehog")},
    ),
    "c-cpp": (
        "RapidCheck",
        "CMake FetchContent of https://github.com/emil-e/rapidcheck",
        {"RapidCheck": rb"""#\s*include\s*[<"]rapidcheck"""},
    ),
}


def plan(run: Run, project: inv.Project, language: str) -> Row:
    row = Row(project=project.dir, language=language, categories="test quality", tool=TOOL)
    row.provenance = "reads the test files, runs nothing"
    row.job = partial(_count, run, project, language)
    return row


def _count(run: Run, project: inv.Project, language: str, row: Row) -> None:
    offer, install, patterns = LIBRARIES[language]
    tests = [f for f in project.files[language] if inv.is_test_path(f) and not inv.under_snapshot(f)]
    used = {library: sum(1 for f in tests if _uses(run, f, pattern)) for library, pattern in patterns.items()}
    found = ", ".join(f"{library} in {n}" for library, n in used.items() if n)
    if found:
        row.unmeasured = f"{found} of {len(tests)} test files"
        return
    none = f"no property test in {len(tests)} test files"
    row.unmeasured = none
    scope = set(run.inv.files)
    anchor = next((m for m in project.manifests if m in scope), "")
    message = f"{none}; {offer} is the library to offer: {install}"
    row.add(anchor, "", "test quality", "none", "info", message, graded=False, reason="an offer, never graded")


def _uses(run: Run, rel: str, pattern: bytes) -> bool:
    try:
        return bool(re.search(pattern, (run.repo / rel).read_bytes(), re.M))
    except OSError:
        return False
