"""Constraint validation for generated class routines.

Each schedule is a list of dicts with at minimum the keys:
    section, day, period, teacher_id, room_id
"""

from typing import List, Dict, Any


def check_teacher_double_booking(schedule: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Return conflicts where the same teacher is assigned two slots at once."""
    conflicts: List[Dict[str, Any]] = []
    occupied: Dict[tuple, Dict] = {}
    for entry in schedule:
        teacher_id = entry.get("teacher_id")
        if teacher_id is None:
            continue
        key = (entry["day"], entry["period"], teacher_id)
        if key in occupied:
            conflicts.append(
                {
                    "type": "teacher_double_booking",
                    "teacher_id": teacher_id,
                    "teacher": entry.get("teacher"),
                    "day": entry["day"],
                    "period": entry["period"],
                    "sections": [occupied[key]["section"], entry["section"]],
                }
            )
        else:
            occupied[key] = entry
    return conflicts


def check_room_double_booking(schedule: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Return conflicts where the same room is used by two sections at once."""
    conflicts: List[Dict[str, Any]] = []
    occupied: Dict[tuple, Dict] = {}
    for entry in schedule:
        room_id = entry.get("room_id")
        if room_id is None:
            continue
        key = (entry["day"], entry["period"], room_id)
        if key in occupied:
            conflicts.append(
                {
                    "type": "room_double_booking",
                    "room_id": room_id,
                    "room": entry.get("room"),
                    "day": entry["day"],
                    "period": entry["period"],
                    "sections": [occupied[key]["section"], entry["section"]],
                }
            )
        else:
            occupied[key] = entry
    return conflicts


def check_timeslot_collisions(schedule: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Return conflicts where a section is scheduled twice in the same slot."""
    conflicts: List[Dict[str, Any]] = []
    seen: set = set()
    for entry in schedule:
        key = (entry["section"], entry["day"], entry["period"])
        if key in seen:
            conflicts.append(
                {
                    "type": "timeslot_collision",
                    "section": entry["section"],
                    "day": entry["day"],
                    "period": entry["period"],
                    "subject": entry.get("subject"),
                }
            )
        else:
            seen.add(key)
    return conflicts


def validate(schedule: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Run all constraint checks and return a combined list of violations."""
    violations: List[Dict[str, Any]] = []
    violations.extend(check_teacher_double_booking(schedule))
    violations.extend(check_room_double_booking(schedule))
    violations.extend(check_timeslot_collisions(schedule))
    return violations
