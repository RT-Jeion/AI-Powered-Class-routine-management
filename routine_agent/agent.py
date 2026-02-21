"""agent.py – LangChain tool-calling agent wired to the Groq model openai/gpt-oss-120b."""
import json
import os
from typing import Any

import pandas as pd
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.tools import tool
from langchain_groq import ChatGroq

from .config import RoutineRules
from .routine_store import (
    load_routine,
    move_slot,
    remove_slot,
    save_routine,
    swap_slots,
    upsert_slot,
)
from .validator import validate_routine
from .markdown_renderer import render_markdown

_ROUTINE_PATH = os.path.join(
    os.path.dirname(__file__), "..", "output", "routine_table.csv"
)

# Module-level mutable state shared by tools within a single agent run
_state: dict[str, Any] = {"df": None, "rules": None}


# ---------------------------------------------------------------------------
# Tool definitions
# ---------------------------------------------------------------------------


@tool
def add_slot(
    section_code: str,
    day: str,
    period: int,
    subject_id: str,
    teacher_id: str,
    room_id: str,
    shift_log_id: str = "",
) -> str:
    """Add or update a class slot in the routine.

    Args:
        section_code: Section code, e.g. '11A'.
        day: Day abbreviation, e.g. 'Sun', 'Mon'.
        period: Period number (1-6).
        subject_id: Subject ID from subjects.csv.
        teacher_id: Teacher ID from teachers.csv.
        room_id: Room ID from class_rooms.csv.
        shift_log_id: Optional shift management log ID.
    """
    df = _state["df"]
    df = upsert_slot(df, section_code, day, int(period), subject_id, teacher_id, room_id, shift_log_id)
    _state["df"] = df
    return f"Slot added/updated: {section_code} {day} P{period}."


@tool
def remove_slot_tool(section_code: str, day: str, period: int) -> str:
    """Remove a class slot from the routine.

    Args:
        section_code: Section code, e.g. '11A'.
        day: Day abbreviation.
        period: Period number (1-6).
    """
    _state["df"] = remove_slot(_state["df"], section_code, day, int(period))
    return f"Slot removed: {section_code} {day} P{period}."


@tool
def move_slot_tool(
    section_code: str,
    from_day: str,
    from_period: int,
    to_day: str,
    to_period: int,
) -> str:
    """Move a slot to a different day/period.

    Args:
        section_code: Section code.
        from_day: Source day.
        from_period: Source period.
        to_day: Destination day.
        to_period: Destination period.
    """
    _state["df"] = move_slot(_state["df"], section_code, from_day, int(from_period), to_day, int(to_period))
    return f"Slot moved: {section_code} {from_day} P{from_period} → {to_day} P{to_period}."


@tool
def swap_slots_tool(
    section_code_a: str,
    day_a: str,
    period_a: int,
    section_code_b: str,
    day_b: str,
    period_b: int,
) -> str:
    """Swap two slots between sections or days/periods.

    Args:
        section_code_a: First section code.
        day_a: First slot day.
        period_a: First slot period.
        section_code_b: Second section code.
        day_b: Second slot day.
        period_b: Second slot period.
    """
    _state["df"] = swap_slots(
        _state["df"],
        section_code_a, day_a, int(period_a),
        section_code_b, day_b, int(period_b),
    )
    return f"Slots swapped: ({section_code_a},{day_a},P{period_a}) ↔ ({section_code_b},{day_b},P{period_b})."


@tool
def list_slots(section_code: str = "") -> str:
    """List current routine slots, optionally filtered by section.

    Args:
        section_code: Optional section code filter; empty string returns all slots.
    """
    df = _state["df"]
    if df.empty:
        return "Routine is currently empty."
    if section_code:
        df = df[df["section_code"] == section_code]
    return df.to_string(index=False)


@tool
def validate_routine_tool() -> str:
    """Validate the current routine and return a list of conflicts or 'OK'."""
    errors = validate_routine(_state["df"], _state["rules"])
    if errors:
        return "\n".join(errors)
    return "Routine is valid (no conflicts)."


# ---------------------------------------------------------------------------
# Agent runner
# ---------------------------------------------------------------------------

_TOOLS = [add_slot, remove_slot_tool, move_slot_tool, swap_slots_tool, list_slots, validate_routine_tool]

MAX_AGENT_ITERATIONS = 20

_SYSTEM_PROMPT = """You are an intelligent class routine management assistant.
You help schedule and manage class timetables for an HSC college using the provided tools.

Available days: Sun, Mon, Tue, Wed, Thu
Available periods: 1, 2, 3, 4, 5 (break after period 3), 6

Always validate the routine after making changes.
When the user asks to schedule classes, use add_slot for each slot.
When finished, call validate_routine_tool to confirm there are no conflicts."""


def run_agent(prompt: str, context: dict | None = None) -> str:
    """Run the LangChain + Groq agent with the given user prompt.

    Modifies the shared _state in-place; caller should save/render afterwards.

    Args:
        prompt: Natural-language instruction from the user.
        context: Optional dict of DataFrames from load_context().

    Returns:
        The final assistant response text.
    """
    groq_api_key = os.environ.get("GROQ_API_KEY")
    if not groq_api_key:
        raise EnvironmentError("GROQ_API_KEY environment variable is not set.")

    # Initialise shared state
    _state["df"] = load_routine(_ROUTINE_PATH)
    _state["rules"] = RoutineRules()

    # Build context summary for the system message
    ctx_summary = ""
    if context:
        for name, df in context.items():
            if isinstance(df, pd.DataFrame) and not df.empty:
                ctx_summary += f"\n### {name}\n{df.to_string(index=False)}\n"

    system_content = _SYSTEM_PROMPT
    if ctx_summary:
        system_content += f"\n\n## Reference Data\n{ctx_summary}"

    llm = ChatGroq(
        model="openai/gpt-oss-120b",
        api_key=groq_api_key,
    )
    llm_with_tools = llm.bind_tools(_TOOLS)

    messages = [
        SystemMessage(content=system_content),
        HumanMessage(content=prompt),
    ]

    tool_map = {t.name: t for t in _TOOLS}

    # Agentic loop: run until no more tool calls
    final_text = ""
    for _ in range(MAX_AGENT_ITERATIONS):  # max iterations safety guard
        response = llm_with_tools.invoke(messages)
        messages.append(response)

        if not response.tool_calls:
            final_text = response.content
            break

        # Execute tool calls and append results
        for tc in response.tool_calls:
            t = tool_map.get(tc["name"])
            if t is None:
                result = f"Unknown tool: {tc['name']}"
            else:
                try:
                    result = t.invoke(tc["args"])
                except Exception as exc:
                    result = f"Tool error: {exc}"
            from langchain_core.messages import ToolMessage
            messages.append(
                ToolMessage(content=str(result), tool_call_id=tc["id"])
            )

    return final_text, _state["df"]
