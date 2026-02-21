"""data_context.py – load all reference data from csv_files/ using pandas."""
import os
import pandas as pd

_BASE = os.path.join(os.path.dirname(__file__), "..", "csv_files")


def _path(name: str) -> str:
    return os.path.join(_BASE, name)


def load_context() -> dict:
    """Return a dict of DataFrames keyed by logical name."""
    ctx: dict = {}

    ctx["classes"] = pd.read_csv(_path("classes.csv"))
    ctx["sections"] = pd.read_csv(_path("sections.csv"))
    ctx["teachers"] = pd.read_csv(_path("teachers.csv"))
    ctx["subjects"] = pd.read_csv(_path("subjects.csv"))
    ctx["rooms"] = pd.read_csv(_path("class_rooms.csv"))
    ctx["shifts"] = pd.read_csv(_path("shifts.csv"))
    ctx["shift_logs"] = pd.read_csv(_path("shift_management_logs.csv"))
    ctx["subject_groups"] = pd.read_csv(_path("subject_groups.csv"))
    ctx["time_tables"] = pd.read_csv(_path("time_tables.csv"))

    # Normalise column names to lowercase strip
    for key, df in ctx.items():
        df.columns = [c.strip().lower() for c in df.columns]
        ctx[key] = df

    return ctx
