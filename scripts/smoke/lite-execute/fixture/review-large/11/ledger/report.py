"""Each month's spending against the budget for each category."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ledger.money import format_cents
from ledger.store import Entry


@dataclass(frozen=True)
class BudgetLine:
    category: str
    spent_cents: int
    limit_cents: int

    @property
    def over(self) -> bool:
        return self.spent_cents > self.limit_cents


def load_budgets(path: Path | str) -> dict[str, int]:
    """Read one category<TAB>limit line per budget, limits in currency units ("400", "120.50"), as cents."""
    limits = {}
    for n, line in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip() or line.startswith("#"):
            continue
        category, sep, limit = line.partition("\t")
        if not sep or not category.strip():
            raise ValueError(f"{path}:{n}: expected a category and a limit separated by a tab")
        limits[category.strip()] = int(float(limit) * 100)
    return limits


def monthly_report(entries: list[Entry], limits: dict[str, int], month: str) -> list[BudgetLine]:
    """One line per budgeted category, in budget file order: the month's spending in it against its limit."""
    in_month = [e for e in entries if e.date.startswith(month + "-")]
    return [BudgetLine(category, sum(e.amount_cents for e in in_month if e.category == category), limit)
            for category, limit in limits.items()]


def render(lines: list[BudgetLine]) -> str:
    """The report as text: one line per category, its spending, its limit, and OVER past the limit."""
    width = max((len(l.category) for l in lines), default=0)
    return "".join(f"{l.category:<{width}}  {format_cents(l.spent_cents):>12} of {format_cents(l.limit_cents):>12}"
                   f"{'  OVER' if l.over else ''}\n" for l in lines)
