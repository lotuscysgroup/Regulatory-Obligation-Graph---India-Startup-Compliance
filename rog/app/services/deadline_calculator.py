from __future__ import annotations

import re
from datetime import date, timedelta

_WITHIN_DAYS_RE = re.compile(r"\bwithin\s+(\d+)\s+days?\b", re.IGNORECASE)
_BEFORE_NUMERIC_RE = re.compile(r"\bbefore\s+(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})\b", re.IGNORECASE)
_BEFORE_TEXTUAL_RE = re.compile(r"\bbefore\s+([A-Za-z]+)\s+(\d{1,2}),?\s+(\d{4})\b", re.IGNORECASE)

_MONTHS = {
    "jan": 1,
    "january": 1,
    "feb": 2,
    "february": 2,
    "mar": 3,
    "march": 3,
    "apr": 4,
    "april": 4,
    "may": 5,
    "jun": 6,
    "june": 6,
    "jul": 7,
    "july": 7,
    "aug": 8,
    "august": 8,
    "sep": 9,
    "sept": 9,
    "september": 9,
    "oct": 10,
    "october": 10,
    "nov": 11,
    "november": 11,
    "dec": 12,
    "december": 12,
}


class DeadlineCalculator:
    @staticmethod
    def calculate_due_date(deadline_text: str | None, *, reference_date: date | None = None) -> date | None:
        if not deadline_text:
            return None
        ref = reference_date or date.today()
        text = deadline_text.strip()
        lowered = text.lower()

        m = _WITHIN_DAYS_RE.search(text)
        if m:
            return ref + timedelta(days=int(m.group(1)))

        m = _BEFORE_NUMERIC_RE.search(text)
        if m:
            day = int(m.group(1))
            month = int(m.group(2))
            year = int(m.group(3))
            if year < 100:
                year += 2000
            return date(year, month, day)

        m = _BEFORE_TEXTUAL_RE.search(text)
        if m:
            month = _MONTHS.get(m.group(1).lower())
            if month:
                return date(int(m.group(3)), month, int(m.group(2)))

        if "annually" in lowered:
            return ref + timedelta(days=365)
        if "quarterly" in lowered:
            return ref + timedelta(days=90)
        if "monthly" in lowered:
            return ref + timedelta(days=30)
        return None

