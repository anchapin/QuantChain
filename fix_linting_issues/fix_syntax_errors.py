#!/usr/bin/env python3
"""
Script to fix syntax errors caused by the previous linting fix script.

This script will focus on:
1. Fixing empty try-except blocks
2. Fixing empty class definitions
3. Fixing empty function definitions
4. Fixing indentation issues
5. Fixing syntax errors like unmatched parentheses
"""

import os
import re
import ast
import sys
from typing import List, Dict, Set


def fix_empty_blocks(file_path: str) -> bool:
    """
    Fix empty blocks in Python code (try-except, class, function definitions).

    Returns True if changes were made, False otherwise.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        original_content = content
        changes_made = False

        # Fix empty try blocks
        content = re.sub(
            r'try:\s*\n(\s*?)(?=\n|\S|$)',
            lambda m: f"{m.group(0)}{m.group(1)}pass\n",
            content
        )

        # Fix empty except blocks
        content = re.sub(
            r'except(\s+\w+)?\s*:\s*\n(\s*?)(?=\n|\S|$)',
            lambda m: f"except{m.group(1) if m.group(1) else ''}:\n{m.group(2)}pass\n",
            content
        )

        # Fix empty class definitions
        content = re.sub(
            r'class\s+(\w+)(?:\([^)]+\))?\s*:\s*\n(\s*?)(?=\n|\S|$)',
            lambda m: f"class {m.group(1)}:\n{m.group(2)}pass\n",
            content
        )

        # Fix empty function definitions
        content = re.sub(
            r'def\s+(\w+)\s*\([^)]*\)\s*(?:->\s*[^:]+)?\s*:\s*\n(\s*?)(?=\n|\S|$)',
            lambda m: f"def {m.group(1)}():\n{m.group(2)}pass\n",
            content
        )

        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True

        return False
    except Exception as e:
        print(f"  Error fixing empty blocks in {file_path}: {e}")
        return False


def fix_indentation_errors(file_path: str) -> bool:
    """
    Fix indentation errors in Python code.

    Returns True if changes were made, False otherwise.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        # Try to parse the file to identify syntax errors
        try:
            ast.parse(''.join(lines))
            return False  # No syntax errors, no changes needed
        except SyntaxError as e:
            if 'unexpected indent' in str(e) or 'expected an indented block' in str(e):
                # We need to fix indentation
                pass
            elif 'unterminated' in str(e) or 'unmatched' in str(e):
                # This is not an indentation issue
                return False
            else:
                # Other syntax errors we can't fix
                return False

        new_lines = []
        i = 0

        while i < len(lines):
            line = lines[i]
            stripped = line.strip()

            # Skip empty lines and comments
            if not stripped or stripped.startswith('#'):
                new_lines.append(line)
                i += 1
                continue

            # Check for try, except, class, def lines
            if (stripped.startswith('try') or stripped.startswith('except') or
                stripped.startswith('class') or stripped.startswith('def') or
                stripped.startswith('if') or stripped.startswith('elif') or
                stripped.startswith('else') or stripped.startswith('for') or
                stripped.startswith('while') or stripped.startswith('with')):

                new_lines.append(line)
                i += 1

                # Check if the next line is properly indented
                if i < len(lines):
                    next_line = lines[i]
                    next_stripped = next_line.strip()

                    # If the next line is empty or a comment, continue
                    if not next_stripped or next_stripped.startswith('#'):
                        new_lines.append(next_line)
                        i += 1
                    # If the next line doesn't have proper indentation, fix it
                    elif (len(next_line) - len(next_line.lstrip()) <= len(line) - len(line.lstrip())):
                        # Add proper indentation
                        indent_level = len(line) - len(line.lstrip()) + 4
                        indented_line = ' ' * indent_level + next_stripped + '\n'
                        new_lines.append(indented_line)
                        i += 1
                    else:
                        new_lines.append(next_line)
                        i += 1
            else:
                new_lines.append(line)
                i += 1

        # Write the fixed content
        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)

        return True
    except Exception as e:
        print(f"  Error fixing indentation in {file_path}: {e}")
        return False


def fix_syntax_errors(file_path: str) -> bool:
    """
    Fix specific syntax errors like unmatched parentheses and unterminated strings.

    Returns True if changes were made, False otherwise.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        original_content = content

        # Fix unmatched parentheses
        # Count open and close parentheses
        open_count = content.count('(') - content.count(')')
        if open_count > 0:
            content += ')' * open_count

        # Fix unterminated triple-quoted strings
        # Count opening and closing triple quotes
        triple_single = content.count("'''")
        triple_double = content.count('"""')

        if triple_single % 2 != 0:
            content += "'''"

        if triple_double % 2 != 0:
            content += '"""'

        # Fix unterminated regular strings (simple cases)
        single_quotes = content.count("'")
        double_quotes = content.count('"')

        # This is a naive approach and might not work for all cases
        if single_quotes % 2 != 0:
            content += "'"

        if double_quotes % 2 != 0:
            content += '"'

        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True

        return False
    except Exception as e:
        print(f"  Error fixing syntax errors in {file_path}: {e}")
        return False


def process_file(file_path: str) -> bool:
    """
    Process a single file for syntax errors.

    Returns True if changes were made, False otherwise.
    """
    changes_made = False

    print(f"Processing {file_path}")

    # Fix various syntax issues
    if fix_empty_blocks(file_path):
        print(f"  Fixed empty blocks")
        changes_made = True

    if fix_syntax_errors(file_path):
        print(f"  Fixed syntax errors")
        changes_made = True

    if fix_indentation_errors(file_path):
        print(f"  Fixed indentation errors")
        changes_made = True

    return changes_made


def find_python_files(directory: str) -> List[str]:
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
