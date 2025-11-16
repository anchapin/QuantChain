#!/usr/bin/env python3
"""
Fix Linting Issues Script

This script fixes non-critical linting issues in Python files, specifically:
1. Formatting issues like line length, whitespace, and import organization
2. Style issues like blank lines, trailing whitespace, etc.
"""

import os
import re
from pathlib import Path
from typing import List, Set, Tuple

# Base directory for the project
BASE_DIR = Path(__file__).parent.parent

# Directories to scan for Python files
DIRECTORIES = [
    "quantchain/agents",
    "quantchain/backtesting",
    "quantchain/connectors",
    "quantchain/core",
    "quantchain/tools",
    "scripts",
]


def fix_line_length(file_path: str) -> None:
    """Fix line length issues by wrapping long lines."""
    full_path = BASE_DIR / file_path

    if not full_path.exists():
        print(f"File not found: {full_path}")
        return

    with open(full_path, "r", encoding="utf-8") as f:
        content = f.read()

    lines = content.split("\n")
    modified_lines = []

    for line in lines:
        # Skip comment lines that exceed line length
        if line.strip().startswith("#") and len(line) > 88:
            # For now, we'll just note this but not modify
            modified_lines.append(line)
            continue

        # Split long lines at common break points
        if len(line) > 88 and not line.strip().startswith("#"):
            # Try to break at common patterns
            if " and " in line and not line.strip().startswith("#"):
                parts = line.split(" and ")
                if len(parts) > 1:
                    indent = len(line) - len(line.lstrip())
                    modified_lines.append(parts[0] + " and")
                    modified_lines.append(" " * (indent + 4) + " and ".join(parts[1:]))
                    continue
            elif " or " in line and not line.strip().startswith("#"):
                parts = line.split(" or ")
                if len(parts) > 1:
                    indent = len(line) - len(line.lstrip())
                    modified_lines.append(parts[0] + " or")
                    modified_lines.append(" " * (indent + 4) + " or ".join(parts[1:]))
                    continue

        modified_lines.append(line)

    # Write back the file
    with open(full_path, "w", encoding="utf-8") as f:
        f.write("\n".join(modified_lines))

    print(f"Fixed line length issues in {file_path}")


def fix_whitespace_issues(file_path: str) -> None:
    """Fix whitespace issues like trailing whitespace and extra blank lines."""
    full_path = BASE_DIR / file_path

    if not full_path.exists():
        print(f"File not found: {full_path}")
        return

    with open(full_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Fix trailing whitespace
    content = re.sub(r"[ \t]+$", "", content, flags=re.MULTILINE)

    # Fix excessive blank lines at end of file
    content = re.sub(r"\n{3,}$", "\n\n", content)

    # Fix excessive blank lines in the middle (max 2 consecutive blank lines)
    content = re.sub(r"\n{4,}", "\n\n\n", content)

    # Write back the file
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"Fixed whitespace issues in {file_path}")


def fix_import_organization(file_path: str) -> None:
    """Fix import organization issues."""
    full_path = BASE_DIR / file_path

    if not full_path.exists():
        print(f"File not found: {full_path}")
        return

    with open(full_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    # Separate imports from non-import lines
    import_lines = []
    other_lines = []
    in_imports = True

    for line in lines:
        if in_imports:
            if line.startswith("import ") or line.startswith("from "):
                import_lines.append(line)
            elif line.strip() == "":
                import_lines.append(line)
            else:
                in_imports = False
                other_lines.append(line)
        else:
            other_lines.append(line)

    # Sort imports by type and then alphabetically
    standard_lib_imports = []
    third_party_imports = []
    local_imports = []

    for line in import_lines:
        if line.strip() == "":
            continue
        if line.startswith("from ..") or line.startswith("from ."):
            local_imports.append(line)
        elif line.startswith("import ") and not ("." in line):
            standard_lib_imports.append(line)
        elif line.startswith("from ") and not ("." in line):
            standard_lib_imports.append(line)
        else:
            third_party_imports.append(line)

    # Sort each category alphabetically
    standard_lib_imports.sort()
    third_party_imports.sort()
    local_imports.sort()

    # Rebuild file with organized imports
    new_lines = []
    new_lines.extend(standard_lib_imports)
    if standard_lib_imports and third_party_imports:
        new_lines.append("\n")
    new_lines.extend(third_party_imports)
    if (standard_lib_imports or third_party_imports) and local_imports:
        new_lines.append("\n")
    new_lines.extend(local_imports)
    if import_lines and other_lines:
        new_lines.append("\n")
    new_lines.extend(other_lines)

    # Write back the file
    with open(full_path, "w", encoding="utf-8") as f:
        f.writelines(new_lines)

    print(f"Fixed import organization in {file_path}")


def fix_blank_lines_after_decorators(file_path: str) -> None:
    """Fix blank lines after function decorators."""
    full_path = BASE_DIR / file_path

    if not full_path.exists():
        print(f"File not found: {full_path}")
        return

    with open(full_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Fix blank lines after decorators (should not have blank lines)
    content = re.sub(r"(@\w+.*\n)\n+", r"\1", content)

    # Write back the file
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"Fixed blank lines after decorators in {file_path}")


def get_python_files() -> List[str]:
    """Get all Python files in the specified directories."""
    python_files = []

    for directory in DIRECTORIES:
        dir_path = BASE_DIR / directory
        if dir_path.exists():
            for file_path in dir_path.rglob("*.py"):
                # Convert to relative path
                rel_path = str(file_path.relative_to(BASE_DIR))
                python_files.append(rel_path)

    return python_files


def main() -> None:
    """Main function to fix all linting issues."""
    print("Fixing linting issues in QuantChain project...")

    # Get all Python files
    python_files = get_python_files()

    for file_path in python_files:
        print(f"\nProcessing: {file_path}")

        # Fix various linting issues
        fix_line_length(file_path)
        fix_whitespace_issues(file_path)
        fix_import_organization(file_path)
        fix_blank_lines_after_decorators(file_path)

    print("\nLinting issue fixes complete!")

    # Run flake8 again to see the remaining issues
    print("\nRunning flake8 to see remaining linting issues...")
    os.system(
        f"cd {BASE_DIR} && python -m flake8 --count --statistics quantchain/agents/ quantchain/backtesting/ quantchain/connectors/ quantchain/core/ quantchain/tools/ scripts/"
    )


if __name__ == "__main__":
    main()
