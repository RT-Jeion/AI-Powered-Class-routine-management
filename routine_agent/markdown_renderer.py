"""markdown_renderer.py – generate output/class_routine_generated.md from routine_table.csv."""
import os
import pandas as pd
from .config import RoutineRules
from .data_context import load_context

_OUTPUT_PATH = os.path.join(
    os.path.dirname(__file__), "..", "output", "class_routine_generated.md"
)


def render_markdown(
    routine_df: pd.DataFrame,
    output_path: str = _OUTPUT_PATH,
    rules: RoutineRules | None = None,
) -> str:
    """Generate a Markdown timetable for every section and write to output_path.

    Returns the rendered Markdown string.
    """
    if rules is None:
        rules = RoutineRules()

    ctx = load_context()
    sections_df = ctx["sections"]
    subjects_df = ctx["subjects"]
    teachers_df = ctx["teachers"]
    rooms_df = ctx["rooms"]

    lines: list[str] = []

    # Build lookup dicts for fast access
    subj_name = dict(zip(subjects_df["id"].astype(str), subjects_df["name"]))
    teacher_code = dict(zip(teachers_df["id"].astype(str), teachers_df["code"]))
    room_no = dict(zip(rooms_df["id"].astype(str), rooms_df["room_no"].astype(str)))

    days = rules.days

    # Determine section codes from routine or from sections table
    if not routine_df.empty:
        section_codes = routine_df["section_code"].unique().tolist()
    else:
        section_codes = sections_df["code"].tolist() if "code" in sections_df.columns else []

    for sec_code in section_codes:
        # Metadata
        sec_row = sections_df[sections_df["code"] == sec_code]
        room_label = ""
        grp_label = ""
        if not sec_row.empty:
            r = sec_row.iloc[0]
            if "room_id" in r.index and not pd.isna(r.get("room_id", None)):
                room_label = f" — Room {room_no.get(str(int(r['room_id'])), str(r.get('room_id', '')))}"
            grp_label = str(r.get("grp_code", ""))

        lines.append(f"# Class {sec_code}{room_label}\n")
        if grp_label:
            lines.append(f"**Group:** {grp_label}  ")
        lines.append("")

        # Table header
        header = "| Period | " + " | ".join(days) + " |"
        separator = "|--------|" + "|".join(["------------------------"] * len(days)) + "|"
        lines.append(header)
        lines.append(separator)

        sec_df = routine_df[routine_df["section_code"] == sec_code] if not routine_df.empty else pd.DataFrame()

        for period in rules.periods:
            row_cells = [str(period)]
            for day in days:
                slot = (
                    sec_df[(sec_df["day"] == day) & (sec_df["period"] == period)]
                    if not sec_df.empty
                    else pd.DataFrame()
                )
                if slot.empty:
                    row_cells.append("—")
                else:
                    s = slot.iloc[0]
                    sub = subj_name.get(str(s.get("subject_id", "")), str(s.get("subject_id", "—")))
                    tcode = teacher_code.get(str(s.get("teacher_id", "")), str(s.get("teacher_id", "")))
                    cell = f"{sub} ({tcode})" if tcode else sub
                    row_cells.append(cell)

            lines.append("| " + " | ".join(row_cells) + " |")

            # Insert break row after break_after_period
            if period == rules.break_after_period:
                break_cells = [rules.break_label] + [f"{rules.break_duration_min} Min"] * len(days)
                lines.append("| " + " | ".join(break_cells) + " |")

        lines.append("")

    content = "\n".join(lines)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as fh:
        fh.write(content)
    return content
