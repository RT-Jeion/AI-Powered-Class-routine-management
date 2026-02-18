#!/usr/bin/env python3
"""
Script to run main.py and save its console output to output.txt

This script:
1. Executes main.py using subprocess
2. Captures all stdout output
3. Saves the captured output to output.txt
4. Handles errors gracefully
5. Prints a success message when complete
"""

import subprocess
import sys
from pathlib import Path


def run_and_save_output():
    """
    Run main.py and save its output to output.txt
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Get the directory where this script is located
        script_dir = Path(__file__).parent.absolute()
        main_py_path = script_dir / "main.py"
        output_file_path = script_dir / "output.txt"
        
        # Check if main.py exists
        if not main_py_path.exists():
            print(f"Error: main.py not found at {main_py_path}", file=sys.stderr)
            return False
        
        print(f"Running main.py...")
        
        # Run main.py and capture output
        result = subprocess.run(
            [sys.executable, str(main_py_path)],
            cwd=str(script_dir),
            capture_output=True,
            text=True,
            timeout=30  # 30 second timeout to prevent hanging
        )
        
        # Combine stdout and stderr
        output = result.stdout
        if result.stderr:
            output += f"\n--- STDERR ---\n{result.stderr}"
        
        # Save output to file
        with open(output_file_path, 'w', encoding='utf-8') as f:
            f.write(output)
        
        # Check if the execution was successful
        if result.returncode != 0:
            print(f"Warning: main.py exited with return code {result.returncode}", file=sys.stderr)
            print(f"Output has been saved to {output_file_path}")
            return False
        
        # Success message
        print(f"✓ Successfully executed main.py")
        print(f"✓ Output saved to {output_file_path}")
        print(f"✓ Total output size: {len(output)} characters")
        
        return True
        
    except subprocess.TimeoutExpired:
        print("Error: main.py execution timed out after 30 seconds", file=sys.stderr)
        return False
    except FileNotFoundError as e:
        print(f"Error: File not found - {e}", file=sys.stderr)
        return False
    except PermissionError as e:
        print(f"Error: Permission denied - {e}", file=sys.stderr)
        return False
    except Exception as e:
        print(f"Error: An unexpected error occurred - {e}", file=sys.stderr)
        return False


if __name__ == "__main__":
    success = run_and_save_output()
    sys.exit(0 if success else 1)
