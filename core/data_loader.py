"""Load all CSV data into pandas DataFrames.

Mirrors the data wrangling from class1.py and main.py so the core
engine has a single, clean place to get its inputs.
"""

import ast
import os

import pandas as pd

_CSV_DIR = os.path.join(os.path.dirname(__file__), "..", "csv_files")


def _csv(name: str) -> str:
    return os.path.join(_CSV_DIR, name)


def load_classes() -> pd.DataFrame:
    df = pd.read_csv(_csv("classes.csv"))
    return df[["id", "name", "code"]].copy()


def load_sections() -> pd.DataFrame:
    df = pd.read_csv(_csv("sections.csv"))
    return df[["id", "classes_id", "name", "code", "grp_code"]].copy()


def load_rooms() -> pd.DataFrame:
    df = pd.read_csv(_csv("class_rooms.csv"))
    df = df[["id", "room_no", "number_of_row", "number_of_column", "each_brench_capacity"]].copy()
    df["total_capacity"] = (
        df["number_of_row"] * df["number_of_column"] * df["each_brench_capacity"]
    )
    return df.sort_values("room_no").reset_index(drop=True)


def load_teachers() -> pd.DataFrame:
    df = pd.read_csv(_csv("teachers.csv"))
    return df[["id", "name", "code", "department", "designation"]].copy()


def load_subjects() -> pd.DataFrame:
    df = pd.read_csv(_csv("subjects.csv"))
    return df[["id", "name", "code", "department"]].copy()


def load_subject_groups() -> pd.DataFrame:
    df = pd.read_csv(_csv("subject_groups.csv"))
    df = df[["id", "name", "grp_code", "has_subjects"]].copy()
    df = df.rename(columns={"id": "grp_id"})
    df["has_subjects"] = df["has_subjects"].apply(ast.literal_eval)
    return df


def load_shifts() -> pd.DataFrame:
    df = pd.read_csv(_csv("shift_management_logs.csv"))
    df = df[["id", "weekends", "start", "end"]].copy()
    df["weekends"] = df["weekends"].apply(ast.literal_eval)
    return df


def load_all() -> dict:
    """Return a dict of all DataFrames keyed by table name."""
    return {
        "classes": load_classes(),
        "sections": load_sections(),
        "rooms": load_rooms(),
        "teachers": load_teachers(),
        "subjects": load_subjects(),
        "subject_groups": load_subject_groups(),
        "shifts": load_shifts(),
    }
