#!/usr/bin/env python3
"""
Simple script to fix linting issues identified by black, flake8, and mypy.
"""


import subprocess
from typing import List


def run_command(cmd: List[str]) -> str:
    """Run a command and return the output."""
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        return result.stdout
    except Exception as e:
        print(f"Error running command: {' '.join(cmd)}")
        print(str(e))
        return ""


def main():
    """Main function."""
    print("Running code formatting and linting tools...")

    # 1. Run black to format code
    print("\n1. Running black...")
    output = run_command(["black", "--check", "quantchain/", "tests/"])
    if "would reformat" in output:
        print("Code formatting issues found. Running black to fix them...")
        run_command(["black", "quantchain/", "tests/"])
        print("Code formatting fixed.")
    else:
        print("Code is already formatted with black.")

    # 2. Run flake8 and fix common issues
    print("\n2. Running flake8...")
    output = run_command(["flake8", "quantchain/", "tests/"])

    # Check for unused imports
    f401_lines = [line for line in output.split("\n") if "F401" in line]
    if f401_lines:
        print(f"Found {len(f401_lines)} unused import issues (F401).")
        print("These should be fixed manually by removing unused imports.")
        print("Some examples:")
        for i, line in enumerate(f401_lines[:5]):
            print(f"  {i + 1}. {line}")
        if len(f401_lines) > 5:
            print(f"  ... and {len(f401_lines) - 5} more.")

    # Check for comparison to True/False
    e712_lines = [line for line in output.split("\n") if "E712" in line]
    if e712_lines:
        print(f"Found {len(e712_lines)} comparison to True/False issues (E712).")
        print("These should be fixed manually by using 'is' or 'not' instead of ==/!=.")
        print("Some examples:")
        for i, line in enumerate(e712_lines[:5]):
            print(f"  {i + 1}. {line}")
        if len(e712_lines) > 5:
            print(f"  ... and {len(e712_lines) - 5} more.")

    # 3. Run mypy
    print("\n3. Running mypy...")
    output = run_command(["mypy", "quantchain/"])

    if output and "error:" in output:
        print("Type checking issues found.")
        print("These should be fixed manually by adding proper type annotations.")
        # Print first 10 lines of mypy output
        lines = output.split("\n")
        for i, line in enumerate(lines[:10]):
            if line:
                print(f"  {i + 1}. {line}")
        if len(lines) > 10:
            print("  ... and more.")

    print("\nLinting complete. Please fix the remaining issues manually.")


if __name__ == "__main__":
    main()
