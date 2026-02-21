"""Load all CSV data files into DataFrames for use by the routine agent."""
import ast
import os
import pandas as pd

CSV_DIR = os.path.join(os.path.dirname(__file__), "..", "csv_files")


def _csv(name: str) -> str:
    return os.path.join(CSV_DIR, name)


def load_all() -> dict:
    """Return a dict of named DataFrames loaded from the csv_files directory."""
    class_dt = pd.read_csv(_csv("classes.csv"))
    class_dt = class_dt[["id", "name", "code"]]

    section_dt = pd.read_csv(_csv("sections.csv"))
    section_dt = section_dt[["id", "classes_id", "name", "code", "grp_code"]]

    class_room_dt = pd.read_csv(_csv("class_rooms.csv"))
    class_room_dt = class_room_dt[
        ["id", "room_no", "number_of_row", "number_of_column", "each_brench_capacity"]
    ]
    class_room_dt["total_capacity"] = (
        class_room_dt["number_of_row"]
        * class_room_dt["number_of_column"]
        * class_room_dt["each_brench_capacity"]
    )
    class_room_dt = class_room_dt.sort_values("room_no")

    shift_log_dt = pd.read_csv(_csv("shift_management_logs.csv"))
    shift_log_dt = shift_log_dt[["id", "weekends", "start", "end"]]

    sub_dt = pd.read_csv(_csv("subjects.csv"))
    sub_dt = sub_dt[["id", "name", "code", "department"]]

    sub_grp_dt = pd.read_csv(_csv("subject_groups.csv"))
    sub_grp_dt = sub_grp_dt[["id", "name", "grp_code", "has_subjects"]]
    sub_grp_dt = sub_grp_dt.rename(columns={"id": "grp_id"})
    sub_grp_dt["has_subjects"] = sub_grp_dt["has_subjects"].apply(ast.literal_eval)

    teacher_dt = pd.read_csv(_csv("teachers.csv"))
    teacher_dt = teacher_dt[["id", "name", "code", "department", "designation"]]

    return {
        "classes": class_dt,
        "sections": section_dt,
        "rooms": class_room_dt,
        "shift_logs": shift_log_dt,
        "subjects": sub_dt,
        "subject_groups": sub_grp_dt,
        "teachers": teacher_dt,
    }
