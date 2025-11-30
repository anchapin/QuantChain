#!/usr/bin/env python3
"""
Fix remaining unused imports.
"""

import os


def fix_import_in_file(file_path: str, old_line: str, new_line: str = None):
    """Fix a specific import line in a file."""
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return False

    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    fixed = False
    for i, line in enumerate(lines):
        if (
            old_line in line
            and line.strip().startswith("from ")
            or line.strip().startswith("import ")
        ):
            if new_line:
                lines[i] = line.replace(old_line, new_line)
                print(f"  Replaced: {line.strip()}")
                print(f"  With: {new_line}")
            else:
                # Remove the entire line
                lines[i] = ""
                print(f"  Removed: {line.strip()}")
            fixed = True
            break

    if fixed:
        with open(file_path, "w", encoding="utf-8") as f:
            f.writelines(lines)
        print(f"Fixed {file_path}")
        return True
    else:
        print(f"No fix needed for {file_path}")
        return False


def main():
    """Fix remaining unused imports."""
    print("Fixing remaining unused imports...")

    # Files that need patch removed
    patch_files = [
        "tests/unit/connectors/test_base_interface_quick.py",
        "tests/unit/core/test_llm_providers_quick.py",
        "tests/unit/core/test_security_quick.py",
        "tests/unit/tools/test_execution_real.py",
        "tests/unit/tools/test_tutorial_mode_comprehensive.py",
    ]

    for file_path in patch_files:
        fix_import_in_file(file_path, "from unittest.mock import patch", "")

    # Files with specific unused imports
    fix_import_in_file(
        "tests/unit/core/test_security_quick.py",
        "from quantchain.core.security import SecurityError",
        "",
    )

    # Trading execution comprehensive file
    fix_import_in_file(
        "tests/unit/tools/test_trading_execution_comprehensive.py",
        "from datetime import datetime, timedelta",
        "",
    )
    fix_import_in_file(
        "tests/unit/tools/test_trading_execution_comprehensive.py",
        "import pandas as pd",
        "",
    )
    fix_import_in_file(
        "tests/unit/tools/test_trading_execution_comprehensive.py",
        "from quantchain.core.exceptions import ExecutionError",
        "",
    )

    # Web dashboard comprehensive file
    fix_import_in_file(
        "tests/unit/tools/test_web_dashboard_comprehensive.py", "import json", ""
    )
    fix_import_in_file(
        "tests/unit/tools/test_web_dashboard_comprehensive.py",
        "from datetime import datetime, timedelta",
        "",
    )


if __name__ == "__main__":
    main()
