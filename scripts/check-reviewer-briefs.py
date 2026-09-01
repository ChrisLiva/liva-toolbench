#!/usr/bin/env python3
"""Gate the adversarial-review sites, the orchestrator skills' promised
literals, and the hand-synced reference copies.

Prints one line per failed check and exits 1 when any fails, 0 when all pass.
Run from the repository root: python3 scripts/check-reviewer-briefs.py
"""

import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# The nine adversarial-reviewer dispatch sites: seven brief files, plus the two
# crank-lite skills that carry their reviewer instruction as dispatch prose.
SITES = [
    "plugins/crank/skills/crank/PLAN-REVIEW-BRIEF.md",
    "plugins/crank/skills/crank/SPEC-REVIEW-BRIEF.md",
    "plugins/crank/skills/crank-execute/PER-TASK-REVIEW-BRIEF.md",
    "plugins/crank/skills/crank-execute/FINAL-REVIEW-BRIEF.md",
    "plugins/crank/skills/crank-execute/RE-REVIEW-BRIEF.md",
    "plugins/crank/skills/crank-review/REVIEW-BRIEF.md",
    "plugins/crank/skills/crank-deslop/DESLOP-BRIEF.md",
    "plugins/crank-lite/skills/lite-execute/SKILL.md",
    "plugins/crank-lite/skills/lite-review/SKILL.md",
]

# Every site sends its whole frontier as one batch per turn.
BATCH_LITERALS = ["as one batch", "frontier"]

# Each site that names what it reads names it in its own words.
READ_LITERALS = {
    "plugins/crank/skills/crank/PLAN-REVIEW-BRIEF.md": ["the plan's frame"],
    "plugins/crank/skills/crank/SPEC-REVIEW-BRIEF.md": ["Read the spec at"],
    "plugins/crank/skills/crank-execute/FINAL-REVIEW-BRIEF.md": ["read the spec in full"],
}

# The two sites whose reviewer edits the artifact under review land their
# findings through one uniqueness-asserting edit script.
APPLY_LITERALS = {
    "plugins/crank/skills/crank/PLAN-REVIEW-BRIEF.md": ["plan-review-edits.py", "MISS"],
    "plugins/crank/skills/crank/SPEC-REVIEW-BRIEF.md": ["spec-review-edits.py", "MISS"],
}

# Flags a site's reviewer must carry, each named in that site's own words.
FLAG_LITERALS = {
    "plugins/crank/skills/crank/PLAN-REVIEW-BRIEF.md": [
        "unprobed oracle",
        "self-invalidating citation",
        "unclaimed file",
    ],
    "plugins/crank/skills/crank-execute/FINAL-REVIEW-BRIEF.md": ["prose the diff falsified"],
    "plugins/crank/skills/crank-review/REVIEW-BRIEF.md": ["made untrue"],
    "plugins/crank-lite/skills/lite-execute/SKILL.md": ["outlives the effort"],
}

# Files outside SITES that must carry a literal their own prose promises.
# Presence only: these are orchestrator skills, not reviewer dispatch sites, so
# the site vocabulary and preprocessing rules below do not reach them.
PRESENCE_LITERALS = {
    "plugins/crank/skills/crank-execute/SKILL.md": [
        "**Promote it.**",
        "- **Promoted** —",
        "Standing defect rules",
    ],
    "plugins/crank/skills/crank-execute/IMPLEMENTER-BRIEF.md": ["## Standing defect rules"],
}

# Brief prose states what the agent does, with no cost justification.
COST_PATTERN = re.compile(r"token|budget|cheaper|expensive|bloat|context window", re.I)

# Cross-harness prose carries no Claude-only preprocessing.
HARNESS_PATTERNS = [
    re.compile(r"\$\{CLAUDE_"),
    re.compile(r"\$ARGUMENTS"),
    re.compile(r"^!`", re.M),
]

# Reference files copied by hand into every skill that needs them, per
# CLAUDE.md -> Cross-harness plugins: name -> the directory holding the canonical.
CANONICAL = {
    "SUBAGENT-TIERS": "plugins/crank/skills/crank",
    "VOCABULARY": "plugins/crank/skills/crank",
    "GRILLING": "plugins/crank/skills/crank",
    "READBACK": "plugins/crank/skills/crank",
    "ARTIFACT-HOME": "plugins/crank/skills/crank",
    "INTERVIEW": "plugins/crank-lite/skills/crank-lite",
}

SKILL_DIRS = ["plugins/crank/skills", "plugins/crank-lite/skills", "plugins/crank-wizard/skills"]

# The crank-wizard skill ships a compilable Go template; a wizard generator
# whose own template does not compile is the failure this gate exists to catch.
TEMPLATE_DIR = "plugins/crank-wizard/skills/crank-wizard/template"


def read(rel):
    path = ROOT / rel
    if not path.is_file():
        return None
    return path.read_text(encoding="utf-8")


def check_sites(failures):
    for rel in SITES:
        text = read(rel)
        if text is None:
            failures.append(f"FAIL {rel}: file is missing")
            continue
        for literal in (
            BATCH_LITERALS
            + READ_LITERALS.get(rel, [])
            + APPLY_LITERALS.get(rel, [])
            + FLAG_LITERALS.get(rel, [])
        ):
            if literal not in text:
                failures.append(f"FAIL {rel}: missing literal {literal!r}")
        cost = COST_PATTERN.findall(text)
        if cost:
            failures.append(f"FAIL {rel}: cost vocabulary appears {len(cost)} time(s): {sorted(set(m.lower() for m in cost))}")
        for pattern in HARNESS_PATTERNS:
            hits = pattern.findall(text)
            if hits:
                failures.append(f"FAIL {rel}: Claude-only preprocessing {pattern.pattern!r} appears {len(hits)} time(s)")


def check_presence(failures):
    for rel, literals in PRESENCE_LITERALS.items():
        text = read(rel)
        if text is None:
            failures.append(f"FAIL {rel}: file is missing")
            continue
        for literal in literals:
            if literal not in text:
                failures.append(f"FAIL {rel}: missing literal {literal!r}")


def check_sync(failures):
    """Every reference a skill links must be present and byte-identical to its canonical.

    A skill owes a copy of every reference any of its own markdown files links.
    Expectation comes from the link, not from the file being there, so deleting a
    copy fails the gate instead of silently dropping its check.
    """
    for skills_dir in SKILL_DIRS:
        for skill in sorted((ROOT / skills_dir).iterdir()):
            if not skill.is_dir():
                continue
            body = "".join(
                f.read_text(encoding="utf-8", errors="replace")
                for f in sorted(skill.glob("*.md"))
            )
            for name, canonical_dir in CANONICAL.items():
                copy_rel = f"{skills_dir}/{skill.name}/{name}.md"
                if copy_rel == f"{canonical_dir}/{name}.md":
                    continue
                copy = read(copy_rel)
                linked = f"]({name}.md)" in body
                if copy is None:
                    if linked:
                        failures.append(f"FAIL sync {copy_rel}: a skill file links it, but the copy is missing")
                    continue
                if not linked:
                    failures.append(f"FAIL sync {copy_rel}: a copy no link in this skill reaches")
                canonical = read(f"{canonical_dir}/{name}.md")
                if canonical is None:
                    failures.append(f"FAIL sync: canonical {canonical_dir}/{name}.md is missing")
                elif copy != canonical:
                    failures.append(f"FAIL sync {copy_rel}: differs from {canonical_dir}/{name}.md")


def check_template(failures):
    """The wizard template must pass vet and compile for both shipped OSes."""
    tdir = ROOT / TEMPLATE_DIR
    if not tdir.is_dir():
        failures.append(f"FAIL {TEMPLATE_DIR}: directory is missing")
        return
    runs = [
        (["go", "vet", "./..."], {}),
        (["go", "build", "-o", os.devnull, "."], {}),
        (["go", "build", "-o", os.devnull, "."], {"GOOS": "windows"}),
    ]
    for cmd, extra_env in runs:
        label = " ".join([f"{k}={v}" for k, v in extra_env.items()] + cmd)
        try:
            proc = subprocess.run(
                cmd, cwd=tdir, env={**os.environ, **extra_env},
                capture_output=True, text=True,
            )
        except FileNotFoundError:
            failures.append(f"FAIL {TEMPLATE_DIR}: go toolchain not found, template unverified")
            return
        if proc.returncode != 0:
            tail = (proc.stderr or proc.stdout).strip().splitlines()[-5:]
            failures.append(f"FAIL {TEMPLATE_DIR}: {label}: " + " | ".join(tail))


def main():
    failures = []
    check_sites(failures)
    check_presence(failures)
    check_sync(failures)
    check_template(failures)
    for line in failures:
        print(line)
    print(f"{len(failures)} failure(s)")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
