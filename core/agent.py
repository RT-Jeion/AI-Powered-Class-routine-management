"""Agentic loop: parse intent → load data → plan → apply → validate → respond.

The in-memory routine store (_routines) maps section_code → schedule list.
This module is intentionally free of I/O so it can be imported by a future
REST API layer without modification.

Generated routines are automatically saved to ``generated_class_routine.md``
(never overwrites the source template ``class_routine.md``).
"""

from __future__ import annotations

import os
from typing import Dict, List, Optional

import pandas as pd

from . import constraints, data_loader, formatter, intent_parser, md_parser, scheduler

# In-memory store: section_code -> list[entry_dict]
_routines: Dict[str, List[Dict]] = {}

# Output file path — always written here, never to class_routine.md
_OUTPUT_MD = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "generated_class_routine.md")
)


def run(prompt: str, data: Optional[dict] = None) -> str:
    """Main entry point.  Returns a human-readable response string."""
    if data is None:
        data = data_loader.load_all()

    intent = intent_parser.parse_intent(prompt)
    action = intent.get("intent", "unknown")

    if action == "create_routine":
        return _create_routine(intent, data)
    if action == "reschedule":
        return _reschedule(intent, data)
    if action == "show_routine":
        return _show_routine(intent)
    if action == "save_routine":
        return _save_to_file(data)
    return (
        "I couldn't understand your request. Try:\n"
        "  \"Create a routine for Class 11 Science\"\n"
        "  \"Reschedule all Math classes to avoid Friday\"\n"
        "  \"Show routine for 11A\"\n"
        "  \"Save routine to file\""
    )


# ── helpers ──────────────────────────────────────────────────────────────────

def _resolve_sections(intent: dict, data: dict) -> List[str]:
    """Return section codes that match the intent."""
    sections = data["sections"]
    section_code: Optional[str] = intent.get("section_code")
    class_name: Optional[str] = intent.get("class_name")
    grp_code: Optional[str] = intent.get("grp_code")

    if section_code:
        row = sections[sections["code"].str.upper() == section_code.upper()]
        if not row.empty:
            return [row.iloc[0]["code"]]

    if class_name:
        classes = data["classes"]
        cl = classes[classes["name"].str.lower() == class_name.lower()]
        if not cl.empty:
            class_code = str(cl.iloc[0]["code"])
            filtered = sections[sections["classes_id"].astype(str) == class_code]
            if grp_code:
                filtered = filtered[filtered["grp_code"] == grp_code]
            if not filtered.empty:
                return filtered["code"].tolist()

    # Fall back to an empty list when nothing matched so the caller can
    # report that no sections were found rather than silently touching all.
    return []


def _format_schedule(schedule: List[Dict], section_code: str) -> str:
    if not schedule:
        return f"  (no entries for {section_code})"
    df = pd.DataFrame(schedule)
    df = df.sort_values(["day", "period"])
    ordered_days = [d for d in scheduler.DAYS if d in df["day"].values]
    rows = []
    for day in ordered_days:
        day_df = df[df["day"] == day].sort_values("period")
        for _, row in day_df.iterrows():
            rows.append(
                f"  {day} P{int(row['period'])}: {row['subject']}"
                f" | {row['teacher']} | Room {row['room']}"
            )
    return "\n".join(rows)


# ── action handlers ───────────────────────────────────────────────────────────

def _create_routine(intent: dict, data: dict) -> str:
    target_sections = _resolve_sections(intent, data)
    results: List[str] = []
    all_schedule: List[Dict] = []
    shared_avail: dict = {"teacher": {}, "room": {}}

    for sec_code in target_sections:
        sched, err = scheduler.generate_routine(sec_code, data, shared_avail)
        if err:
            results.append(f"Error for {sec_code}: {err}")
            continue
        _routines[sec_code] = sched
        all_schedule.extend(sched)
        results.append(f"✅ Generated routine for {sec_code} ({len(sched)} entries).")

    if not all_schedule:
        if not results:
            return (
                "No matching sections found. "
                "Try specifying a class or section, e.g. 'Create a routine for Class 11'."
            )
        return "\n".join(results)

    violations = constraints.validate(all_schedule)
    if violations:
        results.append(f"\n⚠️  {len(violations)} constraint violation(s):")
        for v in violations[:5]:
            results.append(f"   • {v['type']}: {v}")
        if len(violations) > 5:
            results.append(f"   … and {len(violations) - 5} more.")
    else:
        results.append("✅ No constraint violations.")

    # Auto-save to generated_class_routine.md
    save_msg = _save_to_file(data)
    results.append(save_msg)

    # Preview table
    results.append("\n── Routine Preview ──")
    for sec_code in target_sections:
        if sec_code in _routines:
            results.append(f"\n[{sec_code}]")
            results.append(_format_schedule(_routines[sec_code], sec_code))

    return "\n".join(results)


def _reschedule(intent: dict, data: dict) -> str:
    subject: Optional[str] = intent.get("subject")
    avoid_day: Optional[str] = intent.get("avoid_day")

    if not subject:
        return "Please specify which subject to reschedule (e.g. 'Math')."
    if not avoid_day:
        return "Please specify which day to avoid (e.g. 'Friday')."

    section_code: Optional[str] = intent.get("section_code")
    target_sections = (
        [section_code] if section_code and section_code in _routines
        else list(_routines.keys())
    )

    if not target_sections:
        return "No routines found. Please create a routine first."

    results: List[str] = []
    for sec_code in target_sections:
        if sec_code not in _routines:
            continue
        new_sched, warn = scheduler.reschedule_subject(
            _routines[sec_code], subject, avoid_day, data
        )
        if warn:
            results.append(f"{sec_code}: {warn}")
        else:
            _routines[sec_code] = new_sched
            results.append(
                f"✅ {sec_code}: '{subject}' classes moved away from {avoid_day}."
            )

    all_schedule = [e for s in _routines.values() for e in s]
    violations = constraints.validate(all_schedule)
    if violations:
        results.append(f"\n⚠️  {len(violations)} constraint violation(s) after rescheduling.")
    else:
        results.append("✅ No constraint violations after rescheduling.")

    # Auto-save updated routines
    results.append(_save_to_file(data))

    return "\n".join(results) if results else "Nothing to reschedule."


def _show_routine(intent: dict) -> str:
    section_code: Optional[str] = intent.get("section_code")
    if section_code:
        sec_upper = section_code.upper()
        match = next(
            (k for k in _routines if k.upper() == sec_upper), None
        )
        if match:
            return f"Routine for {match}:\n{_format_schedule(_routines[match], match)}"
        return f"No routine found for '{section_code}'. Create one first."

    if not _routines:
        return "No routines generated yet. Use 'create routine' first."

    parts: List[str] = []
    for sec, sched in _routines.items():
        parts.append(f"\n[{sec}]")
        parts.append(_format_schedule(sched, sec))
    return "\n".join(parts)


def _save_to_file(data: dict) -> str:
    """Write all in-memory routines to generated_class_routine.md.

    This never touches class_routine.md.  Returns a status message.
    """
    if not _routines:
        return "ℹ️  No routines to save. Generate a routine first."
    try:
        md = formatter.format_routines(_routines, data)
        with open(_OUTPUT_MD, "w", encoding="utf-8") as fh:
            fh.write(md)
        filename = os.path.basename(_OUTPUT_MD)
        return f"💾 Saved to {filename}"
    except Exception as exc:
        return f"❌ Could not save file: {exc}"


def reset() -> None:
    """Clear in-memory routines (useful for testing)."""
    _routines.clear()
