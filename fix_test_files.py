#!/usr/bin/env python3
"""
Script to fix all test files with syntax errors
"""

import os
import re
import sys
from pathlib import Path


def fix_syntax_errors(file_path):
    """Fix common syntax errors in test files."""
    with open(file_path, "r") as f:
        content = f.read()

    original_content = content

    # Fix unexpected indent errors
    lines = content.split("\n")
    fixed_lines = []
    in_function = False
    in_class = False

    for line in lines:
        # Skip empty lines
        if not line.strip():
            fixed_lines.append(line)
            continue

        # Check for indentation errors
        if re.match(r"^(\s+)(import|from)\s+", line):
            # Remove incorrect indentation from imports
            fixed_line = re.sub(r"^(\s+)(import|from)", r"\2", line)
            fixed_lines.append(fixed_line)
            continue

        # Check for class/function definitions with incorrect indentation
        if re.match(r"^(\s+)def\s+\w+", line):
            fixed_line = re.sub(r"^(\s+)(def\s+)", r"\2", line)
            fixed_lines.append(fixed_line)
            in_function = True
            continue

        if re.match(r"^(\s+)class\s+\w+", line):
            fixed_line = re.sub(r"^(\s+)(class\s+)", r"\2", line)
            fixed_lines.append(fixed_line)
            in_class = True
            continue

        # Fix type annotations with list[float]
        line = line.replace("list[float]", "list")
        line = line.replace("list[float] =", "list =")
        line = line.replace(": list[float]", ": list")

        fixed_lines.append(line)

    content = "\n".join(fixed_lines)

    # Write back if changed
    if content != original_content:
        with open(file_path, "w") as f:
            f.write(content)
        print(f"Fixed {file_path}")
        return True

    return False


def main():
    """Main function to fix all test files."""
    # Find all test files
    test_dir = Path("tests")
    if not test_dir.exists():
        print("Tests directory not found")
        return 1

    fixed_count = 0

    # Recursively find all Python test files
    for file_path in test_dir.rglob("*.py"):
        if file_path.is_file():
            try:
                if fix_syntax_errors(file_path):
                    fixed_count += 1
            except Exception as e:
                print(f"Error fixing {file_path}: {e}")

    print(f"\nFixed {fixed_count} test files")
    return 0


if __name__ == "__main__":
    sys.exit(main())
