"""Validate routine constraints: teacher conflicts, room conflicts, period/day bounds."""
import pandas as pd

VALID_DAYS = ["Sun", "Mon", "Tue", "Wed", "Thu"]
VALID_PERIODS = list(range(1, 7))  # 1..6


def check_period_bounds(df: pd.DataFrame) -> list[str]:
    """Return list of error messages for out-of-bounds periods."""
    errors = []
    bad = df[~df["period"].isin(VALID_PERIODS)]
    for _, row in bad.iterrows():
        errors.append(
            f"Invalid period {row['period']} for section={row['section_code']} day={row['day']}"
        )
    return errors


def check_day_bounds(df: pd.DataFrame) -> list[str]:
    """Return list of error messages for invalid days."""
    errors = []
    bad = df[~df["day"].isin(VALID_DAYS)]
    for _, row in bad.iterrows():
        errors.append(
            f"Invalid day '{row['day']}' for section={row['section_code']} period={row['period']}"
        )
    return errors


def check_teacher_conflicts(df: pd.DataFrame) -> list[str]:
    """Return list of error messages where the same teacher is scheduled in two sections at the same time."""
    errors = []
    subset = df.dropna(subset=["teacher_id"])
    dupes = subset[subset.duplicated(subset=["day", "period", "teacher_id"], keep=False)]
    for (day, period, teacher_id), group in dupes.groupby(["day", "period", "teacher_id"]):
        sections = group["section_code"].tolist()
        errors.append(
            f"Teacher conflict: teacher_id={teacher_id} on {day} period={period} "
            f"assigned to sections {sections}"
        )
    return errors


def check_room_conflicts(df: pd.DataFrame) -> list[str]:
    """Return list of error messages where the same room is booked for two sections at the same time."""
    errors = []
    subset = df.dropna(subset=["room_id"])
    dupes = subset[subset.duplicated(subset=["day", "period", "room_id"], keep=False)]
    for (day, period, room_id), group in dupes.groupby(["day", "period", "room_id"]):
        sections = group["section_code"].tolist()
        errors.append(
            f"Room conflict: room_id={room_id} on {day} period={period} "
            f"used by sections {sections}"
        )
    return errors


def validate(df: pd.DataFrame) -> list[str]:
    """Run all checks and return combined list of error strings (empty = valid)."""
    errors = []
    errors.extend(check_period_bounds(df))
    errors.extend(check_day_bounds(df))
    errors.extend(check_teacher_conflicts(df))
    errors.extend(check_room_conflicts(df))
    return errors
