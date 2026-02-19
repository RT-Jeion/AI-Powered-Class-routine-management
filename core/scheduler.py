"""Heuristic routine generation and rescheduling.

A schedule is a list of entry dicts:
    {section, day, period, subject_id, subject, teacher_id, teacher, room_id, room}

The generator works in two passes:
1. For each subject in the section's group, find (day, period) slots where
   neither the teacher nor the room is already taken, then assign.
2. A shared availability tracker (teacher_avail, room_avail) can be passed
   in so that cross-section conflicts are avoided when generating multiple
   sections in one call.
"""

from typing import Dict, List, Optional, Set, Tuple

# Days used when scheduling (Mon–Fri; Fri can be rescheduled away via CLI)
DAYS: List[str] = ["Mon", "Tue", "Wed", "Thu", "Fri"]
PERIODS: List[int] = [1, 2, 3, 4, 5, 6]  # 6 periods per day
PERIODS_PER_SUBJECT: int = 4  # weekly periods per subject (adjust as needed)


def _all_slots() -> List[Tuple[str, int]]:
    # Interleave days so subjects spread across the week rather than bunching.
    # Order: Mon P1, Tue P1, Wed P1, Thu P1, Fri P1, Mon P2, Tue P2, …
    return [(d, p) for p in PERIODS for d in DAYS]


def generate_routine(
    section_code: str,
    data: dict,
    shared_avail: Optional[Dict] = None,
) -> Tuple[Optional[List[Dict]], Optional[str]]:
    """Generate a weekly routine for *section_code*.

    Args:
        section_code: e.g. "11A"
        data: dict returned by data_loader.load_all()
        shared_avail: optional {"teacher": {(day,period)->set}, "room": {...}}
                      updated in-place so multiple sections share state.

    Returns:
        (schedule, error_message) — schedule is None when an error occurs.
    """
    if shared_avail is None:
        shared_avail = {"teacher": {}, "room": {}}

    sections = data["sections"]
    row = sections[sections["code"].str.upper() == section_code.upper()]
    if row.empty:
        return None, f"Section '{section_code}' not found."

    section = row.iloc[0]
    grp_code = section["grp_code"]

    sub_groups = data["subject_groups"]
    grp = sub_groups[sub_groups["grp_code"] == grp_code]
    if grp.empty:
        return None, f"No subject group found for grp_code '{grp_code}'."

    subject_ids: List[int] = grp.iloc[0]["has_subjects"]
    subjects = data["subjects"][data["subjects"]["id"].isin(subject_ids)]
    teachers = data["teachers"]
    rooms = data["rooms"]

    schedule: List[Dict] = []
    slots = _all_slots()
    slot_idx = 0  # rotating start position to spread load

    for _, subj in subjects.iterrows():
        dept = subj["department"]
        dept_teachers = teachers[teachers["department"] == dept]
        assigned = 0

        for i in range(len(slots)):
            if assigned >= PERIODS_PER_SUBJECT:
                break
            day, period = slots[(slot_idx + i) % len(slots)]
            key = (day, period)

            t_busy: Set = shared_avail["teacher"].get(key, set())
            r_busy: Set = shared_avail["room"].get(key, set())
            # Section must not already have a class in this slot
            if any(e["section"] == section_code and e["day"] == day and e["period"] == period
                   for e in schedule):
                continue

            # Pick first available teacher in this department
            teacher = None
            for _, t in dept_teachers.iterrows():
                if t["id"] not in t_busy:
                    teacher = t
                    break
            if teacher is None:
                continue

            # Pick first available room
            room = None
            for _, r in rooms.iterrows():
                if r["id"] not in r_busy:
                    room = r
                    break
            if room is None:
                continue

            entry = {
                "section": section_code,
                "day": day,
                "period": period,
                "subject_id": int(subj["id"]),
                "subject": subj["name"],
                "teacher_id": int(teacher["id"]),
                "teacher": teacher["name"],
                "room_id": int(room["id"]),
                "room": str(room["room_no"]),
            }
            schedule.append(entry)
            shared_avail["teacher"].setdefault(key, set()).add(int(teacher["id"]))
            shared_avail["room"].setdefault(key, set()).add(int(room["id"]))
            assigned += 1

        slot_idx = (slot_idx + PERIODS_PER_SUBJECT) % len(slots)

    return schedule, None


def reschedule_subject(
    schedule: List[Dict],
    subject_name: str,
    avoid_day: str,
    data: dict,
) -> Tuple[List[Dict], Optional[str]]:
    """Move all entries whose subject matches *subject_name* off *avoid_day*.

    Returns the updated schedule and an optional warning message.
    """
    match_fn = lambda e: subject_name.lower() in e["subject"].lower()
    to_move = [e for e in schedule if match_fn(e) and e["day"] == avoid_day]
    keep = [e for e in schedule if not (match_fn(e) and e["day"] == avoid_day)]

    if not to_move:
        return schedule, f"No '{subject_name}' classes found on {avoid_day}."

    # Rebuild availability from kept entries
    t_avail: Dict[tuple, Set] = {}
    r_avail: Dict[tuple, Set] = {}
    sec_slots: set = set()
    for e in keep:
        k = (e["day"], e["period"])
        t_avail.setdefault(k, set()).add(e["teacher_id"])
        r_avail.setdefault(k, set()).add(e["room_id"])
        sec_slots.add((e["section"], e["day"], e["period"]))

    available_days = [d for d in DAYS if d != avoid_day]
    slots = [(d, p) for d in available_days for p in PERIODS]

    new_schedule = list(keep)
    for entry in to_move:
        placed = False
        for day, period in slots:
            k = (day, period)
            sec_key = (entry["section"], day, period)
            if sec_key in sec_slots:
                continue
            if entry["teacher_id"] in t_avail.get(k, set()):
                continue
            if entry["room_id"] in r_avail.get(k, set()):
                continue

            new_entry = dict(entry, day=day, period=period)
            new_schedule.append(new_entry)
            t_avail.setdefault(k, set()).add(entry["teacher_id"])
            r_avail.setdefault(k, set()).add(entry["room_id"])
            sec_slots.add(sec_key)
            placed = True
            break

        if not placed:
            # Keep original if no alternative slot found
            new_schedule.append(entry)

    return new_schedule, None
