#!/usr/bin/env python3
"""
Script to fix unmatched parentheses in Python files.
"""

import os
import re
import ast
import sys


def fix_parentheses(file_path: str) -> bool:
    """
    Fix unmatched parentheses in a Python file.

    Returns True if changes were made, False otherwise.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        original_content = content

        # Check if the file has syntax errors
        try:
            ast.parse(content)
            return False  # No syntax errors
        except SyntaxError:
            pass  # Continue to fix issues

        # Count opening and closing parentheses
        open_count = content.count('(')
        close_count = content.count(')')

        # Add missing closing parentheses
        if open_count > close_count:
            content += ')' * (open_count - close_count)

        # If we have too many closing parentheses, remove the excess
        if close_count > open_count:
            # This is harder to fix correctly, but we'll try a simple approach
            # Find the last extra closing parenthesis and remove it
            lines = content.split('\n')
            excess = close_count - open_count

            for i in range(len(lines) - 1, -1, -1):
                if excess <= 0:
                    break

                line = lines[i]
                # Count closing parentheses in this line
                line_close = line.count(')')
                line_open = line.count('(')
                line_diff = line_close - line_open

                if line_diff > 0:
                    # Remove some closing parentheses from this line
                    to_remove = min(line_diff, excess)
                    # Find the positions of closing parentheses
                    positions = [pos for pos, char in enumerate(line) if char == ')']

                    # Remove the last 'to_remove' closing parentheses
                    for pos in positions[-to_remove:]:
                        line = line[:pos] + line[pos+1:]

                    lines[i] = line
                    excess -= to_remove

            content = '\n'.join(lines)

        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True

        return False
    except Exception as e:
        print(f"  Error fixing parentheses in {file_path}: {e}")
        return False


def fix_brackets_and_braces(file_path: str) -> bool:
    """
    Fix unmatched brackets and braces in a Python file.

    Returns True if changes were made, False otherwise.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        original_content = content

        # Check if the file has syntax errors
        try:
            ast.parse(content)
            return False  # No syntax errors
        except SyntaxError:
            pass  # Continue to fix issues

        # Fix square brackets
        open_count = content.count('[')
        close_count = content.count(']')
        if open_count > close_count:
            content += ']' * (open_count - close_count)

        # Fix curly braces
        open_count = content.count('{')
        close_count = content.count('}')
        if open_count > close_count:
            content += '}' * (open_count - close_count)

        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True

        return False
    except Exception as e:
        print(f"  Error fixing brackets and braces in {file_path}: {e}")
        return False


def fix_empty_blocks(file_path: str) -> bool:
    """
    Fix empty blocks in Python files.

    Returns True if changes were made, False otherwise.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        original_content = content

        # Check if the file has syntax errors
        try:
            ast.parse(content)
            return False  # No syntax errors
        except SyntaxError:
            pass  # Continue to fix issues

        # Fix empty class definitions
        pattern = r'class\s+(\w+)(?:\([^)]+\))?\s*:\s*$'
        content = re.sub(pattern, r'class \1:\n    pass', content, flags=re.MULTILINE)

        # Fix empty function definitions
        pattern = r'def\s+(\w+)\s*\([^)]*\)\s*(?:->\s*[^:]+)?\s*:\s*$'
        content = re.sub(pattern, r'def \1():\n    pass', content, flags=re.MULTILINE)

        # Fix empty try blocks
        pattern = r'try\s*:\s*$'
        content = re.sub(pattern, 'try:\n    pass', content, flags=re.MULTILINE)

        # Fix empty except blocks
        pattern = r'except(\s+\w+)?\s*:\s*$'
        content = re.sub(pattern, r'except\1:\n    pass', content, flags=re.MULTILINE)

        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True

        return False
    except Exception as e:
        print(f"  Error fixing empty blocks in {file_path}: {e}")
        return False


def fix_unmatched_indentation(file_path: str) -> bool:
    """
    Fix unmatched indentation in Python files.

    Returns True if changes were made, False otherwise.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        # Check if the file has syntax errors
        try:
            ast.parse(''.join(lines))
            return False  # No syntax errors
        except SyntaxError:
            pass  # Continue to fix issues

        new_lines = []
        changes_made = False

        for i, line in enumerate(lines):
            stripped = line.strip()

            # Skip empty lines and comments
            if not stripped or stripped.startswith('#'):
                new_lines.append(line)
                continue

            # Check for unexpected indentation
            if i > 0:
                prev_line = lines[i-1]
                prev_stripped = prev_line.strip()

                # If the previous line was not a block starter, this line should not be indented
                if (not prev_stripped.endswith(':') and
                    len(line) - len(stripped) > 0 and
                    not (stripped.startswith('def') or
                         stripped.startswith('class') or
                         stripped.startswith('if') or
                         stripped.startswith('for') or
                         stripped.startswith('while') or
                         stripped.startswith('with') or
                         stripped.startswith('try') or
                         stripped.startswith('except') or
                         stripped.startswith('finally'))):

                    # Fix the indentation
                    new_line = stripped + '\n'
                    new_lines.append(new_line)
                    changes_made = True
                    continue

            new_lines.append(line)

        if changes_made:
            with open(file_path, 'w', encoding='utf-8') as f:
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

    # Fix parentheses
    if fix_parentheses(file_path):
        print(f"  Fixed parentheses")
        changes_made = True

    # Fix brackets and braces
    if fix_brackets_and_braces(file_path):
        print(f"  Fixed brackets and braces")
        changes_made = True

    # Fix empty blocks
    if fix_empty_blocks(file_path):
        print(f"  Fixed empty blocks")
        changes_made = True

    # Fix indentation
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
