#!/usr/bin/env python3
"""Gate the adversarial-review sites and the hand-synced reference copies.

Prints one line per failed check and exits 1 when any fails, 0 when all pass.
Run from the repository root: python3 scripts/check-reviewer-briefs.py
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# The eight adversarial-reviewer dispatch sites: six brief files, plus the two
# crank-lite skills that carry their reviewer instruction as dispatch prose.
SITES = [
    "plugins/crank/skills/crank/PLAN-REVIEW-BRIEF.md",
    "plugins/crank/skills/crank/SPEC-REVIEW-BRIEF.md",
    "plugins/crank/skills/crank-execute/PER-TASK-REVIEW-BRIEF.md",
    "plugins/crank/skills/crank-execute/FINAL-REVIEW-BRIEF.md",
    "plugins/crank/skills/crank-execute/RE-REVIEW-BRIEF.md",
    "plugins/crank/skills/crank-review/REVIEW-BRIEF.md",
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

# Brief prose states what the agent does, with no cost justification.
COST_PATTERN = re.compile(r"token|budget|cheaper|expensive|bloat|context window", re.I)

# Cross-harness prose carries no Claude-only preprocessing.
HARNESS_PATTERNS = [
    re.compile(r"\$\{CLAUDE_"),
    re.compile(r"\$ARGUMENTS"),
    re.compile(r"^!`", re.M),
]

CANONICAL_DIR = "plugins/crank/skills/crank"

# Reference files copied by hand into every skill that needs them, per
# CLAUDE.md -> Cross-harness plugins.
SYNC_GLOBS = [
    ("plugins/crank/skills", ["SUBAGENT-TIERS", "VOCABULARY", "GRILLING", "READBACK", "ARTIFACT-HOME"]),
    ("plugins/crank-lite/skills", ["VOCABULARY", "READBACK", "ARTIFACT-HOME"]),
]

SYNC_PAIRS = [
    ("plugins/crank-lite/skills/crank-lite/INTERVIEW.md", "plugins/crank-lite/skills/lite-deepen/INTERVIEW.md"),
]


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
        for literal in BATCH_LITERALS + READ_LITERALS.get(rel, []) + APPLY_LITERALS.get(rel, []):
            if literal not in text:
                failures.append(f"FAIL {rel}: missing literal {literal!r}")
        cost = COST_PATTERN.findall(text)
        if cost:
            failures.append(f"FAIL {rel}: cost vocabulary appears {len(cost)} time(s): {sorted(set(m.lower() for m in cost))}")
        for pattern in HARNESS_PATTERNS:
            hits = pattern.findall(text)
            if hits:
                failures.append(f"FAIL {rel}: Claude-only preprocessing {pattern.pattern!r} appears {len(hits)} time(s)")


def check_sync(failures):
    for skills_dir, names in SYNC_GLOBS:
        for name in names:
            canonical = read(f"{CANONICAL_DIR}/{name}.md")
            if canonical is None:
                failures.append(f"FAIL sync: canonical {CANONICAL_DIR}/{name}.md is missing")
                continue
            for skill in sorted((ROOT / skills_dir).iterdir()):
                copy = skill / f"{name}.md"
                if not copy.is_file():
                    continue
                if copy.read_text(encoding="utf-8") != canonical:
                    failures.append(f"FAIL sync {copy.relative_to(ROOT)}: differs from {CANONICAL_DIR}/{name}.md")
    for canonical_rel, copy_rel in SYNC_PAIRS:
        canonical, copy = read(canonical_rel), read(copy_rel)
        if canonical is None or copy is None:
            failures.append(f"FAIL sync {copy_rel}: missing beside {canonical_rel}")
        elif canonical != copy:
            failures.append(f"FAIL sync {copy_rel}: differs from {canonical_rel}")


def main():
    failures = []
    check_sites(failures)
    check_sync(failures)
    for line in failures:
        print(line)
    print(f"{len(failures)} failure(s)")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
