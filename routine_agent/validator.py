"""validator.py – check teacher conflicts, room conflicts and slot bounds."""
from typing import List, Tuple
import pandas as pd
from .config import RoutineRules


def validate_routine(
    df: pd.DataFrame, rules: RoutineRules | None = None
) -> List[str]:
    """Return a list of validation error strings (empty means valid)."""
    if rules is None:
        rules = RoutineRules()
    errors: List[str] = []

    errors.extend(_teacher_conflicts(df))
    errors.extend(_room_conflicts(df))
    errors.extend(_bounds_check(df, rules))
    return errors


def _teacher_conflicts(df: pd.DataFrame) -> List[str]:
    errors: List[str] = []
    if df.empty or "teacher_id" not in df.columns:
        return errors
    grp = df.groupby(["day", "period", "teacher_id"])
    for (day, period, teacher_id), group in grp:
        if len(group) > 1:
            sections = group["section_code"].tolist()
            errors.append(
                f"Teacher conflict: teacher {teacher_id} assigned to multiple sections "
                f"{sections} on {day} period {period}."
            )
    return errors


def _room_conflicts(df: pd.DataFrame) -> List[str]:
    errors: List[str] = []
    if df.empty or "room_id" not in df.columns:
        return errors
    grp = df.groupby(["day", "period", "room_id"])
    for (day, period, room_id), group in grp:
        if len(group) > 1:
            sections = group["section_code"].tolist()
            errors.append(
                f"Room conflict: room {room_id} used by multiple sections "
                f"{sections} on {day} period {period}."
            )
    return errors


def _bounds_check(df: pd.DataFrame, rules: RoutineRules) -> List[str]:
    errors: List[str] = []
    for _, row in df.iterrows():
        if row["day"] not in rules.days:
            errors.append(
                f"Invalid day '{row['day']}' for section {row['section_code']}. "
                f"Allowed: {rules.days}."
            )
        if int(row["period"]) not in rules.periods:
            errors.append(
                f"Invalid period {row['period']} for section {row['section_code']}. "
                f"Allowed: {rules.periods}."
            )
    return errors
