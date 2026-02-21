"""Generate a Markdown timetable visualization from the routine CSV + context DataFrames."""
import os
import pandas as pd

DAYS = ["Sun", "Mon", "Tue", "Wed", "Thu"]
PERIODS = [1, 2, 3, 4, 5, 6]

OUTPUT_PATH = os.path.join(
    os.path.dirname(__file__), "..", "output", "class_routine_generated.md"
)


def render(
    routine: pd.DataFrame,
    context: dict,
    output_path: str = OUTPUT_PATH,
) -> str:
    """
    Generate per-section timetable Markdown tables with a Break row after period 3.

    Args:
        routine: DataFrame from routine_store.load()
        context: dict from data_context.load_all()
        output_path: where to write the .md file

    Returns:
        The generated Markdown string.
    """
    sections = context["sections"]
    subjects = context["subjects"]
    teachers = context["teachers"]
    rooms = context["rooms"]

    # Build lookup dicts for quick access
    subj_map = dict(zip(subjects["id"].astype(str), subjects["name"]))
    teacher_map = dict(zip(teachers["id"].astype(str), teachers["code"]))
    room_map = dict(zip(rooms["id"].astype(str), rooms["room_no"].astype(str)))

    lines: list[str] = ["# Generated Class Routine\n"]

    for _, sec in sections.iterrows():
        sec_code = str(sec["code"])
        grp_code = str(sec.get("grp_code", ""))
        sec_rows = routine[routine["section_code"] == sec_code]

        # Determine room (use most common room_id if multiple exist)
        room_label = ""
        if not sec_rows.empty and sec_rows["room_id"].notna().any():
            common_room = sec_rows["room_id"].dropna().mode()
            if not common_room.empty:
                rid = str(int(common_room.iloc[0]))
                room_no = room_map.get(rid, rid)
                room_label = f" — Room {room_no}"

        lines.append(f"# Section {sec_code}{room_label}\n")
        if grp_code:
            lines.append(f"**Group:** {grp_code}  \n")
        lines.append("")

        # Table header
        day_headers = " | ".join(DAYS)
        lines.append(f"| Period | {day_headers} |")
        sep = " | ".join(["----------"] * len(DAYS))
        lines.append(f"|--------|{sep}|")

        for period in PERIODS:
            cells = []
            for day in DAYS:
                slot = sec_rows[
                    (sec_rows["day"] == day) & (sec_rows["period"] == period)
                ]
                if slot.empty:
                    cells.append("—")
                else:
                    row = slot.iloc[0]
                    subj = subj_map.get(str(int(row["subject_id"])) if pd.notna(row["subject_id"]) else "", "")
                    tcode = teacher_map.get(str(int(row["teacher_id"])) if pd.notna(row["teacher_id"]) else "", "")
                    cells.append(f"{subj} ({tcode})" if subj else "—")
            lines.append(f"| {period} | " + " | ".join(cells) + " |")

            if period == 3:
                break_cells = " | ".join(["**Break** (30 Min)"] * len(DAYS))
                lines.append(f"| Break | {break_cells} |")

        lines.append("")

    md = "\n".join(lines)
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as fh:
        fh.write(md)
    return md
