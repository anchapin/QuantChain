
<tool_call>create_file
<arg_key>path</arg_key>
<arg_value>QuantChain\fix_linting_issues\fix_final_issues.py</arg_value>
<arg_key>mode</arg_key>
<arg_value>create</arg_value>
<arg_key>display_description</arg_key>
<arg_value>Create a script to fix final remaining linting issues</arg_value>
<arg_key>content</arg_key>
<arg_value>#!/usr/bin/env python3
"""
Script to fix final remaining linting issues in QuantChain project.

This script will focus on:
1. Fixing undefined names (missing imports)
2. Fixing indentation and formatting issues
3. Fixing empty f-strings
"""

import os
import re
import ast
import sys


def fix_missing_imports(file_path: str) -> bool:
    """
    Fix missing imports for undefined names.

    Returns True if changes were made, False otherwise.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        original_content = content

        # Check for common undefined names and add appropriate imports
        if 'sys.' in content and 'import sys' not in content:
            # Add import sys at the top
            lines = content.split('\n')

            # Find the first non-comment line after docstring
            insert_pos = 0
            in_docstring = False

            for i, line in enumerate(lines):
                stripped = line.strip()

                # Skip empty lines
                if not stripped:
                    insert_pos = i + 1
                    continue

                # Skip docstring
                if stripped.startswith('"""') or stripped.startswith("'''"):
                    if in_docstring and (stripped.endswith('"""') or stripped.endswith("'''")):
                        in_docstring = False
                        insert_pos = i + 1
                    else:
                        in_docstring = True
                    continue

                if in_docstring:
                    if stripped.endswith('"""') or stripped.endswith("'''"):
                        in_docstring = False
                        insert_pos = i + 1
                    continue

                # Skip comments and shebang
                if stripped.startswith('#') or stripped.startswith('#!'):
                    insert_pos = i + 1
                    continue

                # We've found the first line of code
                break

            # Insert import sys
            lines.insert(insert_pos, 'import sys')
            content = '\n'.join(lines)

        if 'os.' in content and 'import os' not in content:
            # Add import os at the top
            lines = content.split('\n')

            # Find the position to insert the import
            insert_pos = 0

            # Try to insert after import sys if it exists
            for i, line in enumerate(lines):
                if 'import sys' in line:
                    insert_pos = i + 1
                    break

            # Insert import os
            lines.insert(insert_pos, 'import os')
            content = '\n'.join(lines)

        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True

        return False
    except Exception as e:
        print(f"  Error fixing missing imports in {file_path}: {e}")
        return False


def fix_indentation(file_path: str) -> bool:
    """
    Fix indentation issues.

    Returns True if changes were made, False otherwise.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        new_lines = []
        changes_made = False

        for i, line in enumerate(lines):
            # Fix E122: continuation line missing indentation or outdented
            if i > 0:
                prev_line = lines[i-1].rstrip()

                # If previous line ends with a backslash, this is a continuation line
                if prev_line.endswith('\\'):
                    # This line should be indented more
                    prev_indent = len(prev_line) - len(prev_line.lstrip())
                    curr_indent = len(line) - len(line.lstrip())

                    if curr_indent <= prev_indent:
                        # Fix indentation
                        new_line = ' ' * (prev_indent + 4) + line.lstrip()
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
        print(f"  Error fixing indentation in {file_path}: {e}")
        return False


def fix_empty_fstrings(file_path: str) -> bool:
    """
    Fix empty f-strings.

    Returns True if changes were made, False otherwise.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        original_content = content

        # Replace empty f-strings with regular strings
        content = re.sub(r'f["\']{1,2}["\']{1,2}', '""', content)

        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True

        return False
    except Exception as e:
        print(f"  Error fixing empty f-strings in {file_path}: {e}")
        return False


def fix_blank_lines(file_path: str) -> bool:
    """
    Fix blank line issues.

    Returns True if changes were made, False otherwise.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        new_lines = []
        changes_made = False
        prev_line_type = None  # 'class', 'def', or 'other'

        for i, line in enumerate(lines):
            stripped = line.strip()

            # Skip empty lines
            if not stripped:
                new_lines.append(line)
                continue

            # Check if this is a class or function definition
            if stripped.startswith('class '):
                line_type = 'class'
            elif stripped.startswith('def '):
                line_type = 'def'
            else:
                line_type = 'other'

            # Fix E305: expected 2 blank lines after class or function definition
            if prev_line_type in ['class', 'def'] and line_type != 'other':
                # Check if we have enough blank lines
                blank_count = 0
                for j in range(i-1, -1, -1):
                    if not lines[j].strip():
                        blank_count += 1
                    else:
                        break

                if blank_count < 2:
                    # Add missing blank lines
                    for _ in range(2 - blank_count):
                        new_lines.append('\n')

            new_lines.append(line)
            prev_line_type = line_type

        if changes_made:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.writelines(new_lines)
            return True

        return False
    except Exception as e:
        print(f"  Error fixing blank lines in {file_path}: {e}")
        return False


def process_file(file_path: str) -> bool:
    """
    Process a single file for linting issues.

    Returns True if changes were made, False otherwise.
    """
    changes_made = False

    print(f"Processing {file_path}")

    # Fix missing imports
    if fix_missing_imports(file_path):
        print(f"  Fixed missing imports")
        changes_made = True

    # Fix indentation
    if fix_indentation(file_path):
        print(f"  Fixed indentation")
        changes_made = True

    # Fix empty f-strings
    if fix_empty_fstrings(file_path):
        print(f"  Fixed empty f-strings")
        changes_made = True

    # Fix blank lines
    if fix_blank_lines(file_path):
        print(f"  Fixed blank lines")
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
    os.system("flake8 --count quantchain/ scripts/")

    return total_changes


if __name__ == "__main__":
    sys.exit(main())</arg_value>
</tool_call>
