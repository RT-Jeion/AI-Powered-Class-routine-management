"""routine_store.py – load, save, upsert, move and swap routine slots."""
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

_DEFAULT_PATH = os.path.join(
    os.path.dirname(__file__), "..", "output", "routine_table.csv"
)


def load_routine(path: str = _DEFAULT_PATH) -> pd.DataFrame:
    """Load routine CSV, returning an empty DataFrame if the file does not exist."""
    if os.path.exists(path):
        df = pd.read_csv(path)
        # Ensure all expected columns present
        for col in ROUTINE_COLUMNS:
            if col not in df.columns:
                df[col] = None
        return df[ROUTINE_COLUMNS]
    return pd.DataFrame(columns=ROUTINE_COLUMNS)


def save_routine(df: pd.DataFrame, path: str = _DEFAULT_PATH) -> None:
    """Persist the routine DataFrame to CSV."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    df[ROUTINE_COLUMNS].to_csv(path, index=False)


def _match(df: pd.DataFrame, section_code: str, day: str, period: int) -> pd.Series:
    """Boolean mask for a specific slot."""
    return (
        (df["section_code"] == section_code)
        & (df["day"] == day)
        & (df["period"] == int(period))
    )


def upsert_slot(
    df: pd.DataFrame,
    section_code: str,
    day: str,
    period: int,
    subject_id,
    teacher_id,
    room_id,
    shift_log_id,
) -> pd.DataFrame:
    """Insert or update a single routine slot."""
    mask = _match(df, section_code, day, period)
    new_row = {
        "section_code": section_code,
        "day": day,
        "period": int(period),
        "subject_id": subject_id,
        "teacher_id": teacher_id,
        "room_id": room_id,
        "shift_log_id": shift_log_id,
    }
    if mask.any():
        df.loc[mask, list(new_row.keys())] = list(new_row.values())
    else:
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    return df


def remove_slot(
    df: pd.DataFrame, section_code: str, day: str, period: int
) -> pd.DataFrame:
    """Remove a slot identified by section_code, day, period."""
    mask = _match(df, section_code, day, period)
    return df[~mask].reset_index(drop=True)


def move_slot(
    df: pd.DataFrame,
    section_code: str,
    from_day: str,
    from_period: int,
    to_day: str,
    to_period: int,
) -> pd.DataFrame:
    """Move a slot to a new day/period (fails silently if source not found)."""
    mask = _match(df, section_code, from_day, from_period)
    if not mask.any():
        return df
    df.loc[mask, "day"] = to_day
    df.loc[mask, "period"] = int(to_period)
    return df


def swap_slots(
    df: pd.DataFrame,
    section_code_a: str,
    day_a: str,
    period_a: int,
    section_code_b: str,
    day_b: str,
    period_b: int,
) -> pd.DataFrame:
    """Swap two slots (identified by section/day/period pairs)."""
    mask_a = _match(df, section_code_a, day_a, period_a)
    mask_b = _match(df, section_code_b, day_b, period_b)
    if not mask_a.any() or not mask_b.any():
        return df

    cols = ["section_code", "day", "period", "subject_id", "teacher_id", "room_id", "shift_log_id"]
    tmp = df.loc[mask_a, cols].copy()
    df.loc[mask_a, cols] = df.loc[mask_b, cols].values
    df.loc[mask_b, cols] = tmp.values
    return df
