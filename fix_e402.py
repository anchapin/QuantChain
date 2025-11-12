#!/usr/bin/env python3
"""Fix E402 violations - module level imports not at top of file."""

from pathlib import Path


def find_e402_violations(directory):
    """Find E402 violations in Python files."""
    for file_path in Path(directory).rglob("*.py"):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            lines = content.split("\n")
            found_import = False
            code_started = False

            for i, line in enumerate(lines, 1):
                stripped = line.strip()

                # Skip comments and empty lines
                if not stripped or stripped.startswith("#"):
                    continue

                # Skip docstrings at the beginning
                if stripped.startswith('"""') or stripped.startswith("'''"):
                    if '"""' in stripped[3:] or "'''" in stripped[3:]:
                        continue
                    # Multiline docstring
                    in_docstring = True
                    j = i
                    while j < len(lines) and in_docstring:
                        if '"""' in lines[j - 1] or "'''" in lines[j - 1]:
                            in_docstring = False
                        j += 1
                    continue

                # Check if it's an import
                if stripped.startswith("import ") or stripped.startswith("from "):
                    if code_started:
                        print(f"{file_path}:{i}: Import not at top of file")
                        break
                    found_import = True
                elif (
                    found_import
                    and not stripped.startswith("import ")
                    and not stripped.startswith("from ")
                ):
                    code_started = True
        except Exception:
            pass


if __name__ == "__main__":
    find_e402_violations(".")
