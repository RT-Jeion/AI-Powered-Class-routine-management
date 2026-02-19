"""Format a generated schedule as Markdown, matching the structure of class_routine.md.

Output sections:
1. Weekly Shift Distribution Matrix (one row per section)
2. Per-section timetables with periods 1-6 and a 30-minute break after period 3

The shift start-times are taken from shift_management_logs.csv:
  Shift 1 → 09:00, Shift 3 → 08:00, Shift 6 → 10:00
"""

from typing import Dict, List

from . import scheduler
from .md_parser import get_break_rule, get_shift_distribution

_DAYS: List[str] = ["Sun", "Mon", "Tue", "Wed", "Thu"]

# shift_id -> start time (derived from shift_management_logs.csv)
_SHIFT_START: Dict[int, str] = {1: "09:00", 3: "08:00", 6: "10:00"}

# grp_code -> (short label, full label, teacher allocation note)
_GROUP_META: Dict[str, tuple] = {
    "hsc-sci": ("Science", "HSC Science", "Junior (T2, T4, T6)"),
    "hsc-commerces": ("Commerce", "HSC Commerce", "Mix (T2, T4, T6, T8)"),
    "hsc-arts": ("Arts", "HSC Humanities", "Mix (T2, T4, T6, T7)"),
}


def format_routines(routines: Dict[str, List[Dict]], data: dict) -> str:
    """Convert an in-memory routines dict to class_routine.md-compatible Markdown.

    Args:
        routines: section_code → list of schedule entry dicts
        data:     dict returned by data_loader.load_all()

    Returns:
        A multi-line Markdown string ready to be written to generated_class_routine.md.
    """
    shift_dist = get_shift_distribution()
    break_rule = get_break_rule()
    break_after = break_rule["after_period"]

    lines: List[str] = []

    # ── 1. Weekly Shift Distribution Matrix ───────────────────────────────────
    lines.append("# Weekly Shift Distribution Matrix\n")
    lines.append(
        "Each section follows the requested count: "
        "Shift 1 (2x), Shift 6 (2x), Shift 3 (1x).\n"
    )

    day_header = " | ".join(_DAYS)
    sep = "|".join(["---------"] + ["----------"] * len(_DAYS))
    lines.append(f"| Section | {day_header} |")
    lines.append(f"|{sep}|")

    for sec_code in routines:
        dist = shift_dist.get(sec_code, {d: 1 for d in _DAYS})
        cells = " | ".join(f"Shift {dist.get(d, 1):<8}" for d in _DAYS)
        lines.append(f"| {sec_code:<7} | {cells} |")

    lines.append("")

    # ── 2. Per-section timetables ──────────────────────────────────────────────
    sections_df = data["sections"]

    for sec_code, schedule in routines.items():
        if not schedule:
            continue

        # Section metadata
        sec_row = sections_df[sections_df["code"].str.upper() == sec_code.upper()]
        grp_code = sec_row.iloc[0]["grp_code"] if not sec_row.empty else ""
        short_lbl, full_lbl, teacher_alloc = _GROUP_META.get(
            grp_code, (grp_code, grp_code, "Mix")
        )

        # Room: use the first room that appears in this section's schedule
        room_no = next((e["room"] for e in schedule if e.get("room")), "?")

        # Build (day, period) → entry lookup
        lookup: Dict[tuple, Dict] = {}
        for e in schedule:
            lookup[(e["day"], e["period"])] = e

        # Shift distribution for this section
        dist = shift_dist.get(sec_code, {d: 1 for d in _DAYS})

        # Section heading
        lines.append(f"# Class {sec_code} ({short_lbl}) — Room {room_no}\n")
        lines.append(f"**Group:** {full_lbl}  ")
        lines.append(f"**Teacher Allocation:** {teacher_alloc}\n")

        # Table header row:  | Period | Sun (S1: 09:00) | Mon (S1: 09:00) | … |
        col_headers = []
        for day in _DAYS:
            sid = dist.get(day, 1)
            col_headers.append(f"{day} (S{sid}: {_SHIFT_START.get(sid, '?')})")

        hdr = "| Period | " + " | ".join(f"{h:<24}" for h in col_headers) + " |"
        sep_row = "|--------|" + "|".join(["-" * 26] * len(_DAYS)) + "|"
        lines.append(hdr)
        lines.append(sep_row)

        # Period rows (with break inserted after break_after)
        for period in scheduler.PERIODS:
            cells = []
            for day in _DAYS:
                e = lookup.get((day, period))
                if e:
                    t_code = _teacher_code(e, data)
                    cells.append(f"{e['subject']} ({t_code})")
                else:
                    cells.append("")
            row = f"| {period:<6} | " + " | ".join(f"{c:<24}" for c in cells) + " |"
            lines.append(row)

            if period == break_after:
                break_cells = " | ".join(f"{'30 Min':<24}" for _ in _DAYS)
                lines.append(f"| {'Break':<6} | {break_cells} |")

        lines.append("")

    return "\n".join(lines)


# ── helpers ───────────────────────────────────────────────────────────────────

def _teacher_code(entry: Dict, data: dict) -> str:
    """Return the teacher code string for a schedule entry."""
    teacher_id = entry.get("teacher_id")
    if teacher_id is None:
        return "?"
    teachers = data["teachers"]
    row = teachers[teachers["id"] == teacher_id]
    if not row.empty:
        return str(row.iloc[0]["code"])
    return "?"
