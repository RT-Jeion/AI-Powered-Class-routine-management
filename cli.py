#!/usr/bin/env python3
"""CLI entrypoint for the AI-Powered Class Routine Management System.

Usage
-----
Interactive mode:
    python cli.py

Single-prompt mode:
    python cli.py "Create a routine for Class 11 Science"
    python cli.py "Reschedule all Math classes to avoid Friday"
    python cli.py "Show routine for 11A"
"""

import os
import sys

from dotenv import load_dotenv

# Load .env before anything else so GROQ_API_KEY is available
load_dotenv()

# Ensure the project root is on sys.path when running as a script
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core import agent, data_loader  # noqa: E402 — import after path fix

_BANNER = "🎓  AI-Powered Class Routine Management"
_SEPARATOR = "─" * 50
_EXAMPLES = (
    '  -- "Create a routine for Class 11 Science"',
    '  -- "Create a routine for Class 12"',
    '  -- "Reschedule all Math classes to avoid Friday"',
    '  -- "Show routine for 11A"',
    '  -- "show all routines"',
    '  -- "Save routine to file"',
)


def _warn_no_key() -> None:
    if not os.environ.get("GROQ_API_KEY", "").strip():
        print(
            "⚠️  GROQ_API_KEY not set — using built-in keyword parser.\n"
            "   Add GROQ_API_KEY=<key> to a .env file for LLM-powered parsing.\n"
        )


def main() -> None:
    print(_BANNER)
    print(_SEPARATOR)

    # Load all CSV data once
    try:
        data = data_loader.load_all()
    except FileNotFoundError as exc:
        print(f"❌ Could not load CSV data: {exc}")
        print("   Make sure csv_files/ exists and contains the required CSVs.")
        sys.exit(1)

    print(
        f"✅ Data loaded: {len(data['classes'])} classes, "
        f"{len(data['sections'])} sections, "
        f"{len(data['teachers'])} teachers, "
        f"{len(data['subjects'])} subjects"
    )
    print("ℹ️  Generated routines are saved to: generated_class_routine.md")
    print()
    _warn_no_key()

    # ── Single-prompt mode ────────────────────────────────────────────────────
    if len(sys.argv) > 1:
        prompt = " ".join(sys.argv[1:])
        print(f"Prompt: {prompt}\n")
        print(agent.run(prompt, data))
        return

    # ── Interactive mode ──────────────────────────────────────────────────────
    print("Enter prompts in natural language (type 'quit' to exit).")
    print("Examples:")
    for ex in _EXAMPLES:
        print(ex)
    print()

    while True:
        try:
            prompt = input(">>> ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nGoodbye!")
            break

        if not prompt:
            continue
        if prompt.lower() in {"quit", "exit", "q"}:
            print("Goodbye!")
            break

        print()
        print(agent.run(prompt, data))
        print()


if __name__ == "__main__":
    main()
