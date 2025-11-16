#!/usr/bin/env python3
"""
Script to fix remaining linting issues in the QuantChain project.
"""

import os
import re
import sys
from pathlib import Path


def fix_function_spacing(file_path):
    """Fix spacing issues between function definitions."""
    with open(file_path, "r") as f:
        content = f.read()

    original_content = content
    lines = content.split("\n")
    fixed_lines = []
    i = 0
    while i < len(lines):
        line = lines[i]
        fixed_lines.append(line)
        i += 1

        # Check if current line is a function or class definition
        if re.match(r"^\s*(def|class)\s+", line):
            # Check if there are enough blank lines before this function
            blank_lines = 0
            j = i - 2  # Start checking from the line before the current one
            while j >= 0 and not lines[j].strip():
                blank_lines += 1
                j -= 1

            # If we need more blank lines, add them
            if blank_lines < 2:
                # Replace the existing line with properly spaced lines
                fixed_lines.pop()  # Remove the last added line
                # Add blank lines
                for _ in range(2):
                    fixed_lines.append("")
                # Add the function line
                fixed_lines.append(line)

    content = "\n".join(fixed_lines)

    if content != original_content:
        with open(file_path, "w") as f:
            f.write(content)
        return True
    return False


def fix_example_imports(file_path):
    """Fix module level imports not at top of file in examples."""
    with open(file_path, "r") as f:
        content = f.read()

    original_content = content
    lines = content.split("\n")

    # Find all imports
    imports = []
    non_import_lines = []
    after_imports = []
    found_non_import = False

    for line in lines:
        if re.match(r"^(from|import)\s+", line.strip()) and not found_non_import:
            imports.append(line)
        elif line.strip():
            if (
                imports
            ):  # If we've already collected imports, everything else goes after
                found_non_import = True
                after_imports.append(line)
            else:
                non_import_lines.append(line)
        else:
            if not found_non_import and imports:
                imports.append(line)  # Keep blank lines with imports
            elif found_non_import:
                after_imports.append(line)
            else:
                non_import_lines.append(line)

    # Reconstruct with proper order
    fixed_content = "\n".join(non_imports + [""] * 2 + imports + after_imports)

    if fixed_content != original_content:
        with open(file_path, "w") as f:
            f.write(fixed_content)
        return True
    return False


def main():
    """Fix all remaining linting issues."""
    fixed_count = 0

    # Process all Python files in the project
    for file_path in Path(".").rglob("*.py"):
        if file_path.is_file():
            try:
                # Fix function/class spacing issues
                if fix_function_spacing(file_path):
                    fixed_count += 1
                    print(f"Fixed spacing in {file_path}")

                # Fix import issues in example files
                if "examples" in str(file_path):
                    if fix_example_imports(file_path):
                        fixed_count += 1
                        print(f"Fixed imports in {file_path}")
            except Exception as e:
                print(f"Error processing {file_path}: {e}")

    print(f"\nFixed {fixed_count} files")
    return 0


if __name__ == "__main__":
    sys.exit(main())
