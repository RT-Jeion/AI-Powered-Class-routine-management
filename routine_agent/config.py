"""RoutineRules – static configuration for the routine management system."""
from pydantic import BaseModel
from typing import List


class RoutineRules(BaseModel):
    days: List[str] = ["Sun", "Mon", "Tue", "Wed", "Thu"]
    periods: List[int] = [1, 2, 3, 4, 5, 6]
    break_after_period: int = 3
    break_label: str = "Break"
    break_duration_min: int = 30
