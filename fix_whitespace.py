#!/usr/bin/env python3
"""
Script to fix trailing whitespace issues (W293 errors).
"""

import os


def fix_trailing_whitespace(file_path: str):
    """Remove trailing whitespace from all lines in a file."""
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return False

    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    # Remove trailing whitespace from each line
    fixed_lines = [line.rstrip() for line in lines]

    # Join back with newlines (ensuring file ends with newline)
    content = "\n".join(fixed_lines)
    if content and not content.endswith("\n"):
        content += "\n"

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"Fixed trailing whitespace in {file_path}")
    return True


def main():
    """Fix trailing whitespace in files that had W293 errors."""
    # List of files that had W293 errors based on flake8 output
    files_to_fix = ["tests/unit/agents/test_smart_contract_auditor.py"]

    print("Fixing trailing whitespace issues...")
    fixed_count = 0

    for file_path in files_to_fix:
        full_path = os.path.abspath(file_path)
        if fix_trailing_whitespace(full_path):
            fixed_count += 1

    print(f"\nSummary: Fixed {fixed_count}/{len(files_to_fix)} files")


if __name__ == "__main__":
    main()
