"""Load, save, and mutate the routine CSV (output/routine_table.csv)."""
import os
import pandas as pd

ROUTINE_COLUMNS = [
    "section_code",
    "day",
    "period",
    "subject_id",
    "teacher_id",
    "room_id",
    "shift_log_id",
]

DEFAULT_PATH = os.path.join(
    os.path.dirname(__file__), "..", "output", "routine_table.csv"
)


def load(path: str = DEFAULT_PATH) -> pd.DataFrame:
    """Load routine CSV; return empty DataFrame with correct columns if file is empty."""
    df = pd.read_csv(path)
    for col in ROUTINE_COLUMNS:
        if col not in df.columns:
            df[col] = None
    return df[ROUTINE_COLUMNS]


def save(df: pd.DataFrame, path: str = DEFAULT_PATH) -> None:
    """Save routine DataFrame to CSV."""
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    df[ROUTINE_COLUMNS].to_csv(path, index=False)


def upsert(
    df: pd.DataFrame,
    section_code: str,
    day: str,
    period: int,
    subject_id,
    teacher_id,
    room_id,
    shift_log_id,
) -> pd.DataFrame:
    """Insert or update a single slot. Returns the modified DataFrame."""
    mask = (
        (df["section_code"] == section_code)
        & (df["day"] == day)
        & (df["period"] == period)
    )
    row = {
        "section_code": section_code,
        "day": day,
        "period": int(period),
        "subject_id": subject_id,
        "teacher_id": teacher_id,
        "room_id": room_id,
        "shift_log_id": shift_log_id,
    }
    if mask.any():
        for key, val in row.items():
            df.loc[mask, key] = val
    else:
        df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
    return df


def move(
    df: pd.DataFrame,
    section_code: str,
    from_day: str,
    from_period: int,
    to_day: str,
    to_period: int,
) -> pd.DataFrame:
    """Move a slot from one (day, period) to another. Raises if source not found."""
    mask = (
        (df["section_code"] == section_code)
        & (df["day"] == from_day)
        & (df["period"] == from_period)
    )
    if not mask.any():
        raise ValueError(
            f"No slot found for section={section_code} day={from_day} period={from_period}"
        )
    df.loc[mask, "day"] = to_day
    df.loc[mask, "period"] = to_period
    return df


def swap(
    df: pd.DataFrame,
    section_code: str,
    day1: str,
    period1: int,
    day2: str,
    period2: int,
) -> pd.DataFrame:
    """Swap two slots within the same section."""
    mask1 = (
        (df["section_code"] == section_code)
        & (df["day"] == day1)
        & (df["period"] == period1)
    )
    mask2 = (
        (df["section_code"] == section_code)
        & (df["day"] == day2)
        & (df["period"] == period2)
    )
    if not mask1.any() or not mask2.any():
        raise ValueError("One or both slots not found for swap.")
    idx1 = df.index[mask1][0]
    idx2 = df.index[mask2][0]
    df.loc[idx1, "day"], df.loc[idx2, "day"] = day2, day1
    df.loc[idx1, "period"], df.loc[idx2, "period"] = period2, period1
    return df
