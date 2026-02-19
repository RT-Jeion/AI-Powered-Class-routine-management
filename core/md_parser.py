"""Parse class_routine.md to extract structural context for the scheduler.

This module reads the existing class_routine.md template and surfaces:
- The weekly shift distribution matrix (section → day → shift_id)
- Break rules (break after period N, duration in minutes)
- The full file text (for use as LLM context)
"""

import os
import re
from typing import Dict

_MD_PATH = os.path.join(os.path.dirname(__file__), "..", "class_routine.md")

# Break rule constants reflected from class_routine.md
BREAK_AFTER_PERIOD: int = 3
BREAK_DURATION_MINUTES: int = 30

# Fallback shift distribution taken directly from class_routine.md.
# Mapping: section_code -> {day_abbrev -> shift_id (int)}
_DEFAULT_SHIFT_DIST: Dict[str, Dict[str, int]] = {
    "11A": {"Sun": 1, "Mon": 1, "Tue": 6, "Wed": 6, "Thu": 3},
    "11B": {"Sun": 6, "Mon": 3, "Tue": 1, "Wed": 1, "Thu": 6},
    "11C": {"Sun": 6, "Mon": 6, "Tue": 3, "Wed": 1, "Thu": 1},
    "12A": {"Sun": 3, "Mon": 1, "Tue": 1, "Wed": 6, "Thu": 6},
    "12B": {"Sun": 1, "Mon": 6, "Tue": 6, "Wed": 3, "Thu": 1},
}


def get_shift_distribution() -> Dict[str, Dict[str, int]]:
    """Return section→day→shift_id mapping parsed from class_routine.md.

    Falls back to the hardcoded defaults when parsing fails or the file is absent.
    """
    try:
        return _parse_shift_distribution()
    except Exception:
        return {k: dict(v) for k, v in _DEFAULT_SHIFT_DIST.items()}


def _parse_shift_distribution() -> Dict[str, Dict[str, int]]:
    """Extract the shift distribution matrix table from class_routine.md."""
    with open(_MD_PATH, encoding="utf-8") as fh:
        text = fh.read()

    # Locate the separator line that follows the header row, then read data rows.
    # Pattern: lines that look like "| 11A | Shift 1 | Shift 1 | … |"
    row_re = re.compile(
        r"^\|\s*(\w+)\s*\|"  # section code
        r"\s*(Shift\s*\d+)\s*\|"  # Sun
        r"\s*(Shift\s*\d+)\s*\|"  # Mon
        r"\s*(Shift\s*\d+)\s*\|"  # Tue
        r"\s*(Shift\s*\d+)\s*\|"  # Wed
        r"\s*(Shift\s*\d+)\s*\|",  # Thu
        re.MULTILINE,
    )

    dist: Dict[str, Dict[str, int]] = {}
    days = ["Sun", "Mon", "Tue", "Wed", "Thu"]
    for m in row_re.finditer(text):
        sec = m.group(1).strip()
        # group(1) = section code; shift groups start at group(2)
        _SHIFT_GROUP_OFFSET = 2
        for i, day in enumerate(days):
            shift_text = m.group(_SHIFT_GROUP_OFFSET + i)
            num = re.search(r"\d+", shift_text)
            if num:
                dist.setdefault(sec, {})[day] = int(num.group())

    return dist if dist else {k: dict(v) for k, v in _DEFAULT_SHIFT_DIST.items()}


def get_break_rule() -> Dict[str, int]:
    """Return the break rule reflected from class_routine.md."""
    return {
        "after_period": BREAK_AFTER_PERIOD,
        "duration_minutes": BREAK_DURATION_MINUTES,
    }


def get_context_text() -> str:
    """Return the full contents of class_routine.md for use as LLM context."""
    try:
        with open(_MD_PATH, encoding="utf-8") as fh:
            return fh.read()
    except FileNotFoundError:
        return ""
