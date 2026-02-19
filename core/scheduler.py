"""Heuristic routine generation and rescheduling.

A schedule is a list of entry dicts:
    {section, day, period, subject_id, subject, teacher_id, teacher, room_id, room}

The generator assigns each subject to exactly ONE period and repeats it
across ALL working days, matching the pattern in class_routine.md:
    Period 1 → Subject A  (Sun, Mon, Tue, Wed, Thu)
    Period 2 → Subject B  (Sun, Mon, Tue, Wed, Thu)
    …
    Period 6 → Subject F  (Sun, Mon, Tue, Wed, Thu)

This yields 6 × 5 = 30 entries with no empty slots and perfect consistency.
"""

from typing import Dict, List, Optional, Set, Tuple

# Days used when scheduling — matches class_routine.md (Sun–Thu, Islamic week)
DAYS: List[str] = ["Sun", "Mon", "Tue", "Wed", "Thu"]
PERIODS: List[int] = [1, 2, 3, 4, 5, 6]  # 6 periods per day

# Short display names for subjects (CSV names → display names)
_SHORT_NAMES: Dict[str, str] = {
    "Bangla 1st paper": "Bangla 1st",
    "Bangla 2nd paper": "Bangla 2nd",
    "English 1st paper": "English 1st",
    "English 2nd paper": "English 2nd",
    "Mathematics": "Math",
    "Higher Mathematics": "Higher Math",
}


def _short_name(name: str) -> str:
    return _SHORT_NAMES.get(name, name)


def generate_routine(
    section_code: str,
    data: dict,
    shared_avail: Optional[Dict] = None,
) -> Tuple[Optional[List[Dict]], Optional[str]]:
    """Generate a weekly routine for *section_code*.

    Each subject is assigned to exactly one period and appears on ALL 5 days,
    ensuring consistent, gap-free timetables.

    Args:
        section_code: e.g. "11A"
        data: dict returned by data_loader.load_all()
        shared_avail: optional {"teacher": {(day,period)->set}, "room": {(day,period)->set}}
                      updated in-place so multiple sections share room availability state.

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
    # "11" → prefer Junior teachers; "12" → prefer Senior teachers
    prefer_senior: bool = str(section["classes_id"]) == "12"

    sub_groups = data["subject_groups"]
    grp = sub_groups[sub_groups["grp_code"] == grp_code]
    if grp.empty:
        return None, f"No subject group found for grp_code '{grp_code}'."

    subject_ids: List[int] = grp.iloc[0]["has_subjects"]
    # Sort by id so the period assignment is deterministic
    subjects = (
        data["subjects"][data["subjects"]["id"].isin(subject_ids)]
        .sort_values("id")
        .reset_index(drop=True)
    )
    teachers = data["teachers"]
    rooms = data["rooms"]

    # ── Assign one dedicated room to this section ─────────────────────────────
    # A room is "taken" if it appears in shared_avail["room"] for ANY slot that
    # this section will occupy (all 30 day×period combinations).
    all_section_slots = [(d, p) for d in DAYS for p in PERIODS]

    def _room_is_available(room_id: int) -> bool:
        return not any(
            room_id in shared_avail["room"].get(slot, set())
            for slot in all_section_slots
        )

    room = None
    for _, r in rooms.iterrows():
        if _room_is_available(int(r["id"])):
            room = r
            break
    if room is None:
        return None, "No available room found for section."

    # Mark every slot in this section's room as taken
    for slot in all_section_slots:
        shared_avail["room"].setdefault(slot, set()).add(int(room["id"]))

    # ── Assign subjects to periods 1–6 ────────────────────────────────────────
    schedule: List[Dict] = []
    for period, (_, subj) in enumerate(subjects.iterrows(), start=1):
        dept = subj["department"]
        dept_teachers = teachers[teachers["department"] == dept].copy()

        # Sort by designation: "Senior Teacher" > "Junior Teacher" alphabetically;
        # reverse the sort direction based on the seniority preference.
        dept_teachers = dept_teachers.sort_values(
            "designation", ascending=not prefer_senior
        )

        # Pick the preferred teacher (first after sorting)
        if dept_teachers.empty:
            continue
        teacher = dept_teachers.iloc[0]

        # Create one entry per day for this (period, subject, teacher, room)
        for day in DAYS:
            schedule.append({
                "section": section_code,
                "day": day,
                "period": period,
                "subject_id": int(subj["id"]),
                "subject": _short_name(subj["name"]),
                "teacher_id": int(teacher["id"]),
                "teacher": teacher["name"],
                "room_id": int(room["id"]),
                "room": str(room["room_no"]),
            })

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
