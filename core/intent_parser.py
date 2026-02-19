"""Parse natural-language prompts into structured intent dicts.

Preferred path: Groq LLM via LangChain (requires GROQ_API_KEY in env).
Fallback:       keyword / regex heuristic parser (no API key needed).

Returned dict always contains at least {"intent": <str>}.
Possible intents: create_routine, reschedule, show_routine, unknown.
"""

import json
import os
import re
from typing import Dict, Any


# ── Day name → abbreviation ─────────────────────────────────────────────────
_DAY_MAP: Dict[str, str] = {
    "monday": "Mon", "tuesday": "Tue", "wednesday": "Wed",
    "thursday": "Thu", "friday": "Fri", "saturday": "Sat", "sunday": "Sun",
}

# ── Stream keyword → grp_code ────────────────────────────────────────────────
_STREAM_MAP: Dict[str, str] = {
    "science": "hsc-sci",
    "commerce": "hsc-commerces",
    "arts": "hsc-arts",
    "humanities": "hsc-arts",
}


def _heuristic(prompt: str) -> Dict[str, Any]:
    """Simple keyword/regex intent parser — works without any API key."""
    pl = prompt.lower()

    if any(kw in pl for kw in ("regenerate", "recreate", "overwrite", "replace")):
        intent: Dict[str, Any] = {"intent": "regenerate_routine"}
        m = re.search(r"class\s*(\d+)", pl)
        if m:
            intent["class_name"] = f"Class {m.group(1)}"
        m = re.search(r"\b(1[12][a-e])\b", pl, re.IGNORECASE)
        if m:
            intent["section_code"] = m.group(1).upper()
        for stream_kw, grp in _STREAM_MAP.items():
            if stream_kw in pl:
                intent["grp_code"] = grp
                break
        return intent

    if any(kw in pl for kw in ("create", "generate", "make", "build")):
        intent: Dict[str, Any] = {"intent": "create_routine"}
        m = re.search(r"class\s*(\d+)", pl)
        if m:
            intent["class_name"] = f"Class {m.group(1)}"
        m = re.search(r"\b(1[12][a-e])\b", pl, re.IGNORECASE)
        if m:
            intent["section_code"] = m.group(1).upper()
        for stream_kw, grp in _STREAM_MAP.items():
            if stream_kw in pl:
                intent["grp_code"] = grp
                break
        return intent

    if any(kw in pl for kw in ("reschedule", "move", "avoid", "shift")):
        intent = {"intent": "reschedule"}
        for day_kw, day_code in _DAY_MAP.items():
            if day_kw in pl:
                intent["avoid_day"] = day_code
                break
        for subj in (
            "higher mathematics", "mathematics", "math",
            "english", "bangla", "geography", "accounting",
        ):
            if subj in pl:
                intent["subject"] = subj.title()
                break
        m = re.search(r"\b(1[12][a-e])\b", pl, re.IGNORECASE)
        if m:
            intent["section_code"] = m.group(1).upper()
        return intent

    if any(kw in pl for kw in ("save", "export", "write", "output")):
        return {"intent": "save_routine"}

    if any(kw in pl for kw in ("show", "display", "view", "print", "list")):
        intent = {"intent": "show_routine"}
        m = re.search(r"\b(1[12][a-e])\b", pl, re.IGNORECASE)
        if m:
            intent["section_code"] = m.group(1).upper()
        return intent

    return {"intent": "unknown"}


_LLM_SYSTEM = """\
You are a class-routine management assistant.
Parse the user's request and return ONLY a JSON object with these fields:

For creating a routine:
  {"intent": "create_routine", "class_name": "Class 11", "section_code": "11A", "grp_code": "hsc-sci"}

For rescheduling:
  {"intent": "reschedule", "subject": "Math", "avoid_day": "Fri", "section_code": "11A"}

For showing a routine:
  {"intent": "show_routine", "section_code": "11A"}

For saving/exporting to file:
  {"intent": "save_routine"}

Omit optional fields that are not mentioned. Use 3-letter day codes (Mon/Tue/Wed/Thu/Fri/Sat/Sun).
Respond with valid JSON only — no extra text.
"""


def _llm(prompt: str) -> Dict[str, Any]:
    """Use Groq via LangChain to parse intent; falls back to heuristic on error."""
    api_key = os.environ.get("GROQ_API_KEY", "").strip()
    if not api_key:
        return _heuristic(prompt)
    try:
        from langchain_groq import ChatGroq
        from langchain.schema import HumanMessage, SystemMessage

        # Attach class_routine.md as structural context for the LLM
        from . import md_parser
        context = md_parser.get_context_text()
        system_content = _LLM_SYSTEM
        if context:
            system_content = (
                _LLM_SYSTEM
                + "\n\nExisting class_routine.md (use as structural context):\n"
                + context
            )

        llm = ChatGroq(model="llama3-8b-8192", api_key=api_key, temperature=0)
        messages = [SystemMessage(content=system_content), HumanMessage(content=prompt)]
        response = llm.invoke(messages)
        text = response.content.strip()
        m = re.search(r"\{.*\}", text, re.DOTALL)
        if m:
            return json.loads(m.group())
    except Exception:
        pass
    return _heuristic(prompt)


def parse_intent(prompt: str) -> Dict[str, Any]:
    """Parse *prompt* into a structured intent dict."""
    return _llm(prompt)
