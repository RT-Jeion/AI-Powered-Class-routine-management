#!/usr/bin/env python3
"""run_agent.py – CLI entrypoint for the agentic class routine management system."""
import argparse
import sys

from routine_agent.agent import run_agent
from routine_agent.data_context import load_context
from routine_agent.markdown_renderer import render_markdown
from routine_agent.routine_store import save_routine
from routine_agent.validator import validate_routine


def main() -> None:
    parser = argparse.ArgumentParser(
        description="AI-powered class routine management agent (LangChain + Groq)."
    )
    parser.add_argument(
        "--prompt",
        required=True,
        help="Natural-language instruction for the routine agent.",
    )
    args = parser.parse_args()

    print("Loading reference data from csv_files/ …")
    context = load_context()

    print("Running agent …")
    response, df = run_agent(args.prompt, context=context)

    if df is not None and not df.empty:
        print("Validating routine …")
        errors = validate_routine(df)
        if errors:
            print("Validation warnings:")
            for err in errors:
                print(f"  ⚠  {err}")
        else:
            print("Routine is valid (no conflicts).")

        print("Saving output/routine_table.csv …")
        save_routine(df)

        print("Generating output/class_routine_generated.md …")
        render_markdown(df)
        print("Done. See output/ directory for results.")
    else:
        print("No routine changes made.")

    print("\nAgent response:")
    print(response)


if __name__ == "__main__":
    main()
