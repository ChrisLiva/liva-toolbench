"""Read and print money amounts as integer cents."""
from __future__ import annotations

import re

CURRENCY_SIGNS = "$£€"
_AMOUNT = re.compile(r"(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d{1,2})?")


def parse_amount(text: str) -> int:
    """Return the amount text holds as integer cents.

    Accepts a leading minus or surrounding parentheses for a negative amount, a currency sign,
    thousands separators, and one or two decimal places: "-1,234.56", "(12.50)", "£0.99".
    """
    s = text.strip()
    negative = False
    if s.startswith("(") and s.endswith(")"):
        negative, s = True, s[1:-1].strip()
    elif s.startswith("-"):
        negative, s = True, s[1:].strip()
    if s[:1] and s[0] in CURRENCY_SIGNS:
        s = s[1:].strip()
    if not _AMOUNT.fullmatch(s):
        raise ValueError(f"not an amount: {text!r}")
    whole, _, frac = s.replace(",", "").partition(".")
    cents = int(whole) * 100 + int(frac or 0)
    return -cents if negative else cents


def format_cents(cents: int) -> str:
    """Print integer cents with a sign, thousands separators, and two decimal places: -123456 -> "-1,234.56"."""
    sign = "-" if cents < 0 else ""
    whole, frac = divmod(abs(cents), 100)
    return f"{sign}{whole:,}.{frac:02d}"
