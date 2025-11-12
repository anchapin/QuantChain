#!/usr/bin/env python3
"""Fix all E402 violations - module level imports not at top of file."""

from pathlib import Path


def fix_e402_violations(file_path):
    """Fix E402 violations in a single file."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        # Extract all imports
        imports = []
        other_lines = []
        in_docstring = False
        docstring_char = None

        for line in lines:
            stripped = line.strip()

            # Skip empty lines and comments for now
            if not stripped or stripped.startswith("#"):
                other_lines.append(line)
                continue

            # Handle docstrings
            if not in_docstring and (
                stripped.startswith('"""') or stripped.startswith("'''")
            ):
                in_docstring = True
                docstring_char = '"""' if stripped.startswith('"""') else "'''"
                other_lines.append(line)
                if stripped.count(docstring_char) >= 2:
                    in_docstring = False
                continue
            elif in_docstring:
                other_lines.append(line)
                if docstring_char in stripped:
                    in_docstring = False
                continue

            # Handle imports
            if stripped.startswith("import ") or stripped.startswith("from "):
                # Check if it's a multi-line import
                if stripped.endswith("\\"):
                    # Collect the entire multi-line import
                    import_lines = [line]
                    for next_line in lines[lines.index(line) + 1 :]:
                        import_lines.append(next_line)
                        if not next_line.strip().endswith("\\"):
                            break
                    imports.extend(import_lines)
                    # Skip these lines in the main loop
                    lines = [l for l in lines if l not in import_lines[1:]]
                else:
                    imports.append(line)
                continue

            # Any other code
            other_lines.append(line)

        # Reconstruct the file
        # Find the end of initial docstring/comments
        new_lines = []
        i = 0
        while i < len(other_lines):
            line = other_lines[i]
            stripped = line.strip()

            # Skip initial blank lines and comments
            if not stripped or stripped.startswith("#"):
                new_lines.append(line)
                i += 1
                continue

            # Skip initial docstring
            if stripped.startswith('"""') or stripped.startswith("'''"):
                new_lines.append(line)
                i += 1
                # Find end of docstring
                while i < len(other_lines) and (
                    stripped.count('"""') < 2 and stripped.count("'''") < 2
                ):
                    new_lines.append(other_lines[i])
                    i += 1
                    if i < len(other_lines):
                        stripped = other_lines[i - 1].strip()
                continue

            break

        # Add imports
        if imports:
            new_lines.extend(imports)
            # Add a blank line if there aren't any imports yet and code exists
            if i < len(other_lines):
                new_lines.append("\n")

        # Add the rest of the file
        new_lines.extend(other_lines[i:])

        # Write back
        with open(file_path, "w", encoding="utf-8") as f:
            f.writelines(new_lines)

        return True
    except Exception as e:
        print(f"Error fixing {file_path}: {e}")
        return False


def fix_all_e402(directory):
    """Fix all E402 violations in directory recursively."""
    fixed = 0
    for file_path in Path(directory).rglob("*.py"):
        # Skip the fix scripts themselves
        if "fix_e402" in file_path.name or "fix_all_e402" in file_path.name:
            continue

        # Try to fix the file
        if fix_e402_violations(file_path):
            fixed += 1
            print(f"Fixed: {file_path}")

    print(f"\nFixed {fixed} files with E402 violations")


if __name__ == "__main__":
    fix_all_e402(".")
