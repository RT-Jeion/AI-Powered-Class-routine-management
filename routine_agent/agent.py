"""LangChain tool-calling agent wired to Groq for managing class routines."""
import json
import os

import pandas as pd
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from langchain_core.tools import tool
from langchain_groq import ChatGroq

from . import data_context, markdown_renderer, routine_store, validator

GROQ_MODEL = "openai/gpt-oss-120b"

# Module-level mutable state (populated by build_agent)
_routine: pd.DataFrame = pd.DataFrame(columns=routine_store.ROUTINE_COLUMNS)
_context: dict = {}
_routine_path: str = routine_store.DEFAULT_PATH


# ---------------------------------------------------------------------------
# Tools exposed to the LLM
# ---------------------------------------------------------------------------


@tool
def list_sections() -> str:
    """Return a JSON list of available sections with their codes and group codes."""
    sections = _context.get("sections", pd.DataFrame())
    if sections.empty:
        return "[]"
    return sections[["id", "code", "grp_code"]].to_json(orient="records")


@tool
def list_subjects() -> str:
    """Return a JSON list of subjects (id, name, code, department)."""
    subjects = _context.get("subjects", pd.DataFrame())
    if subjects.empty:
        return "[]"
    return subjects.to_json(orient="records")


@tool
def list_teachers() -> str:
    """Return a JSON list of teachers (id, name, code, department, designation)."""
    teachers = _context.get("teachers", pd.DataFrame())
    if teachers.empty:
        return "[]"
    return teachers.to_json(orient="records")


@tool
def list_rooms() -> str:
    """Return a JSON list of class rooms (id, room_no, total_capacity)."""
    rooms = _context.get("rooms", pd.DataFrame())
    if rooms.empty:
        return "[]"
    return rooms[["id", "room_no", "total_capacity"]].to_json(orient="records")


@tool
def get_routine() -> str:
    """Return the current routine as a JSON array of slot records."""
    return _routine.to_json(orient="records")


@tool
def upsert_slot(
    section_code: str,
    day: str,
    period: int,
    subject_id: int,
    teacher_id: int,
    room_id: int,
    shift_log_id: int,
) -> str:
    """
    Insert or update a single routine slot.

    Args:
        section_code: e.g. '11A'
        day: one of Sun, Mon, Tue, Wed, Thu
        period: integer 1-6
        subject_id: integer subject id
        teacher_id: integer teacher id
        room_id: integer room id
        shift_log_id: integer shift log id

    Returns:
        'ok' or an error message string.
    """
    global _routine
    try:
        _routine = routine_store.upsert(
            _routine,
            section_code,
            day,
            int(period),
            int(subject_id),
            int(teacher_id),
            int(room_id),
            int(shift_log_id),
        )
        return "ok"
    except Exception as exc:  # noqa: BLE001
        return f"error: {exc}"


@tool
def move_slot(
    section_code: str,
    from_day: str,
    from_period: int,
    to_day: str,
    to_period: int,
) -> str:
    """
    Move a slot from one (day, period) to another within the same section.

    Returns:
        'ok' or an error message string.
    """
    global _routine
    try:
        _routine = routine_store.move(
            _routine, section_code, from_day, int(from_period), to_day, int(to_period)
        )
        return "ok"
    except Exception as exc:  # noqa: BLE001
        return f"error: {exc}"


@tool
def swap_slots(
    section_code: str,
    day1: str,
    period1: int,
    day2: str,
    period2: int,
) -> str:
    """
    Swap two slots within the same section.

    Returns:
        'ok' or an error message string.
    """
    global _routine
    try:
        _routine = routine_store.swap(
            _routine, section_code, day1, int(period1), day2, int(period2)
        )
        return "ok"
    except Exception as exc:  # noqa: BLE001
        return f"error: {exc}"


@tool
def validate_routine() -> str:
    """
    Validate the current routine for conflicts and constraint violations.

    Returns:
        'valid' if no errors, otherwise a JSON array of error strings.
    """
    errors = validator.validate(_routine)
    if not errors:
        return "valid"
    return json.dumps(errors)


# ---------------------------------------------------------------------------
# Agent builder
# ---------------------------------------------------------------------------

TOOLS = [
    list_sections,
    list_subjects,
    list_teachers,
    list_rooms,
    get_routine,
    upsert_slot,
    move_slot,
    swap_slots,
    validate_routine,
]

SYSTEM_PROMPT = """You are an AI assistant that manages a class routine (timetable) for a college.
You have access to tools to read context data (sections, subjects, teachers, rooms) and to
upsert/move/swap routine slots. After making changes always call validate_routine to ensure
there are no conflicts. Only use days Sun, Mon, Tue, Wed, Thu and periods 1-6.
"""


def build_agent(
    context: dict,
    routine: pd.DataFrame,
    routine_path: str = routine_store.DEFAULT_PATH,
):
    """
    Build and return a callable agent function.

    Args:
        context: dict from data_context.load_all()
        routine: DataFrame from routine_store.load()
        routine_path: path to save updated routine CSV

    Returns:
        A function run(prompt: str) -> str that runs the agent and returns its final reply.
    """
    global _routine, _context, _routine_path
    _routine = routine.copy()
    _context = context
    _routine_path = routine_path

    api_key = os.environ.get("GROQ_API_KEY", "")
    llm = ChatGroq(model=GROQ_MODEL, api_key=api_key, temperature=0)
    llm_with_tools = llm.bind_tools(TOOLS)

    tool_map = {t.name: t for t in TOOLS}

    def run(prompt: str) -> str:
        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=prompt),
        ]
        while True:
            response = llm_with_tools.invoke(messages)
            messages.append(response)

            if not response.tool_calls:
                break

            for tc in response.tool_calls:
                tool_fn = tool_map[tc["name"]]
                result = tool_fn.invoke(tc["args"])
                messages.append(
                    ToolMessage(content=str(result), tool_call_id=tc["id"])
                )

        return response.content

    return run


def get_updated_routine() -> pd.DataFrame:
    """Return the current in-memory routine DataFrame after agent modifications."""
    return _routine
