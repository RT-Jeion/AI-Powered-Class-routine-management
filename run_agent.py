#!/usr/bin/env python3
"""CLI entrypoint for the agentic class routine management system.

Usage:
    python run_agent.py --prompt "Schedule Math (id=5) for 11A on Mon period 1, teacher 6, room 1, shift_log 1"
    python run_agent.py --prompt "..." --routine output/routine_table.csv
"""
import argparse
import os
import sys

from routine_agent import agent as agent_module
from routine_agent import data_context, markdown_renderer, routine_store, validator


def main() -> int:
    parser = argparse.ArgumentParser(
        description="AI-powered class routine management agent"
    )
    parser.add_argument("--prompt", required=True, help="Natural language instruction for the agent")
    parser.add_argument(
        "--routine",
        default=routine_store.DEFAULT_PATH,
        help="Path to the routine CSV file (default: output/routine_table.csv)",
    )
    parser.add_argument(
        "--output-md",
        default=markdown_renderer.OUTPUT_PATH,
        help="Path to write the generated Markdown file",
    )
    args = parser.parse_args()

    # Load context and routine
    context = data_context.load_all()
    routine = routine_store.load(args.routine)

    # Build and run agent
    run = agent_module.build_agent(context, routine, args.routine)
    print(f"Running agent with prompt: {args.prompt!r}\n")
    reply = run(args.prompt)
    print(f"Agent reply:\n{reply}\n")

    # Retrieve updated routine from agent module state and save
    updated_routine = agent_module.get_updated_routine()
    errors = validator.validate(updated_routine)
    if errors:
        print("Validation warnings:")
        for err in errors:
            print(f"  - {err}")

    routine_store.save(updated_routine, args.routine)
    print(f"Routine saved to {args.routine}")

    # Regenerate Markdown
    markdown_renderer.render(updated_routine, context, args.output_md)
    print(f"Markdown visualization saved to {args.output_md}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
