"""Categorize ledger entries by payee with the rules in a rules file."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


class RulesError(ValueError):
    """A line of the rules file is not a payee pattern and a category separated by a tab."""


@dataclass(frozen=True)
class Rule:
    pattern: str
    category: str

    def matches(self, payee: str) -> bool:
        return self.pattern.casefold() in payee.casefold()


def load_rules(path: Path | str) -> list[Rule]:
    """Read one pattern<TAB>category rule per line, skipping blank lines and # comments."""
    rules = []
    for n, line in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        pattern, sep, category = line.partition("\t")
        if not sep or not pattern.strip() or not category.strip():
            raise RulesError(f"{path}:{n}: expected a payee pattern and a category separated by a tab")
        rules.append(Rule(pattern.strip(), category.strip()))
    # A longer pattern is the more specific one, so try it first: "amazon prime" before "amazon".
    rules.sort(key=lambda r: len(r.pattern), reverse=True)
    return rules


def category_for(rules: list[Rule], payee: str) -> str:
    """Return the category of the first rule whose pattern appears in payee, or "" when none does."""
    return next((r.category for r in rules if r.matches(payee)), "")
