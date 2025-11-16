#!/usr/bin/env python3
"""
Script to fix specific issues in the codebase.

This script will focus on:
1. Fixing incorrectly indented imports
2. Fixing empty try-except blocks
3. Fixing malformed syntax
"""

import os
import re
import ast
import sys


def fix_import_indentation(file_path: str) -> bool:
    """
    Fix incorrectly indented import statements.

    Returns True if changes were made, False otherwise.
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        new_lines = []
        changes_made = False

        for line in lines:
            stripped = line.strip()

            # Check if this is an import statement with incorrect indentation
            if (
                stripped.startswith("import ") or stripped.startswith("from ")
            ) and line != stripped:
                # Fix the indentation
                new_line = stripped + "\n"
                new_lines.append(new_line)
                changes_made = True
            else:
                new_lines.append(line)

        if changes_made:
            with open(file_path, "w", encoding="utf-8") as f:
                f.writelines(new_lines)
            return True

        return False
    except Exception as e:
        print(f"  Error fixing import indentation in {file_path}: {e}")
        return False


def fix_empty_try_blocks(file_path: str) -> bool:
    """
    Fix empty try blocks by adding pass statements.

    Returns True if changes were made, False otherwise.
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        original_content = content

        # Pattern to match empty try blocks
        pattern = r"try:\s*\n(\s*?)(?=\n|\S)"

        def replace_empty_try(match):
            indent = match.group(1)
            return f"try:\n{indent}    pass\n"

        content = re.sub(pattern, replace_empty_try, content)

        if content != original_content:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            return True

        return False
    except Exception as e:
        print(f"  Error fixing empty try blocks in {file_path}: {e}")
        return False


def fix_empty_except_blocks(file_path: str) -> bool:
    """
    Fix empty except blocks by adding pass statements.

    Returns True if changes were made, False otherwise.
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        original_content = content

        # Pattern to match empty except blocks
        pattern = r"except(\s+\w+)?\s*:\s*\n(\s*?)(?=\n|\S)"

        def replace_empty_except(match):
            exception = match.group(1) if match.group(1) else ""
            indent = match.group(2)
            return f"except{exception}:\n{indent}    pass\n"

        content = re.sub(pattern, replace_empty_except, content)

        if content != original_content:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            return True

        return False
    except Exception as e:
        print(f"  Error fixing empty except blocks in {file_path}: {e}")
        return False


def fix_malformed_syntax(file_path: str) -> bool:
    """
    Fix malformed syntax like unmatched parentheses and unterminated strings.

    Returns True if changes were made, False otherwise.
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        # First, try to parse the file to check for syntax errors
        try:
            ast.parse("".join(lines))
            return False  # No syntax errors
        except SyntaxError:
            pass  # Continue to fix the issues

        new_content = ""
        in_string = False
        string_char = None
        paren_count = 0
        changes_made = False

        for line in lines:
            line_content = line.rstrip("\n")

            # Fix unmatched parentheses
            open_count = line_content.count("(")
            close_count = line_content.count(")")
            paren_diff = open_count - close_count

            if paren_diff > 0:
                line_content += ")" * paren_diff
                changes_made = True

            new_content += line_content + "\n"

        if changes_made:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(new_content)
            return True

        return False
    except Exception as e:
        print(f"  Error fixing malformed syntax in {file_path}: {e}")
        return False


def fix_try_except_syntax(file_path: str) -> bool:
    """
    Fix try-except syntax issues.

    Returns True if changes were made, False otherwise.
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        # First, try to parse the file to check for syntax errors
        try:
            ast.parse("".join(lines))
            return False  # No syntax errors
        except SyntaxError:
            pass  # Continue to fix the issues

        # Look for try blocks without except or finally
        new_lines = []
        i = 0
        changes_made = False
        in_try = False
        try_indent = 0

        while i < len(lines):
            line = lines[i]
            stripped = line.strip()

            if stripped.startswith("try:"):
                in_try = True
                try_indent = len(line) - len(stripped)
                new_lines.append(line)
                i += 1
                continue
            elif in_try and (
                stripped.startswith("except") or stripped.startswith("finally")
            ):
                in_try = False
                new_lines.append(line)
                i += 1
                continue
            elif in_try and (len(line) - len(stripped) <= try_indent):
                # We've reached a line at the same or lower indentation as the try
                # without finding an except or finally, add one
                except_line = " " * try_indent + "except:\n"
                except_line += " " * (try_indent + 4) + "pass\n"
                new_lines.append(except_line)
                in_try = False
                changes_made = True
                new_lines.append(line)
                i += 1
                continue
            else:
                new_lines.append(line)
                i += 1

        # If we ended with an unclosed try, add an except block
        if in_try:
            except_line = " " * try_indent + "except:\n"
            except_line += " " * (try_indent + 4) + "pass\n"
            new_lines.append(except_line)
            changes_made = True

        if changes_made:
            with open(file_path, "w", encoding="utf-8") as f:
                f.writelines(new_lines)
            return True

        return False
    except Exception as e:
        print(f"  Error fixing try-except syntax in {file_path}: {e}")
        return False


def fix_unmatched_indentation(file_path: str) -> bool:
    """
    Fix unmatched indentation issues.

    Returns True if changes were made, False otherwise.
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        # First, try to parse the file to check for syntax errors
        try:
            ast.parse("".join(lines))
            return False  # No syntax errors
        except SyntaxError:
            pass  # Continue to fix the issues

        new_lines = []
        i = 0
        changes_made = False

        while i < len(lines):
            line = lines[i]
            stripped = line.strip()

            # Skip empty lines and comments
            if not stripped or stripped.startswith("#"):
                new_lines.append(line)
                i += 1
                continue

            # Check for unexpected indent
            if i > 0:
                prev_line = lines[i - 1]
                prev_stripped = prev_line.strip()

                # If the previous line was not a block starter, this line should not be indented
                if (
                    not prev_stripped.endswith(":")
                    and not prev_stripped.startswith("try")
                    and not prev_stripped.startswith("except")
                    and not prev_stripped.startswith("finally")
                    and len(line) - len(stripped) > 0
                ):

                    # This might be incorrectly indented
                    # Check if it's a regular line that shouldn't be indented
                    if not (
                        stripped.startswith("def")
                        or stripped.startswith("class")
                        or stripped.startswith("if")
                        or stripped.startswith("for")
                        or stripped.startswith("while")
                        or stripped.startswith("with")
                    ):

                        # Fix the indentation
                        new_line = stripped + "\n"
                        new_lines.append(new_line)
                        changes_made = True
                        i += 1
                        continue

            new_lines.append(line)
            i += 1

        if changes_made:
            with open(file_path, "w", encoding="utf-8") as f:
                f.writelines(new_lines)
            return True

        return False
    except Exception as e:
        print(f"  Error fixing unmatched indentation in {file_path}: {e}")
        return False


def process_file(file_path: str) -> bool:
    """
    Process a single file for syntax errors.

    Returns True if changes were made, False otherwise.
    """
    changes_made = False

    print(f"Processing {file_path}")

    # Fix various syntax issues
    if fix_import_indentation(file_path):
        print(f"  Fixed import indentation")
        changes_made = True

    if fix_empty_try_blocks(file_path):
        print(f"  Fixed empty try blocks")
        changes_made = True

    if fix_empty_except_blocks(file_path):
        print(f"  Fixed empty except blocks")
        changes_made = True

    if fix_try_except_syntax(file_path):
        print(f"  Fixed try-except syntax")
        changes_made = True

    if fix_malformed_syntax(file_path):
        print(f"  Fixed malformed syntax")
        changes_made = True

    if fix_unmatched_indentation(file_path):
        print(f"  Fixed unmatched indentation")
        changes_made = True

    return changes_made


def find_python_files(directory: str) -> list:
    """
    Find all Python files in a directory recursively.
    """
    python_files = []

    for root, dirs, files in os.walk(directory):
        # Skip __pycache__ directories
        if "__pycache__" in dirs:
            dirs.remove("__pycache__")

        for file in files:
            if file.endswith(".py"):
                python_files.append(os.path.join(root, file))

    return python_files


def main():
    """Main function."""
    directories = ["quantchain", "scripts"]

    total_changes = 0
    total_files = 0

    for directory in directories:
        if not os.path.exists(directory):
            print(f"Directory {directory} does not exist, skipping...")
            continue

        python_files = find_python_files(directory)

        for file_path in python_files:
            total_files += 1
            if process_file(file_path):
                total_changes += 1

    print(f"\nProcessed {total_files} Python files")
    print(f"Modified {total_changes} files")

    # Run flake8 to check remaining issues
    print("\nRunning flake8 to check remaining issues...")
    os.system("flake8 --count --select=E999 quantchain/ scripts/")

    return total_changes


if __name__ == "__main__":
    sys.exit(main())
