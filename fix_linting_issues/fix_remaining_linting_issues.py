#!/usr/bin/env python3
"""
Script to fix the remaining linting issues in QuantChain.

This script will focus on:
1. Removing unused imports (F401)
2. Fixing module level imports not at top of file (E402)
3. Removing empty f-strings (F541)
4. Fixing indentation issues (E117)
5. Fixing excessive blank lines (E303)
"""

import os
import re
import ast
import sys
from typing import List, Dict, Set


def fix_unused_imports(file_path: str) -> bool:
    """
    Remove unused imports from a Python file.

    Returns True if changes were made, False otherwise.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Parse the AST to find used names
        try:
            tree = ast.parse(content)
        except SyntaxError:
            print(f"  Syntax error in {file_path}, skipping...")
            return False

        # Collect all defined names in the AST
        used_names = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Name):
                used_names.add(node.id)
            elif isinstance(node, ast.Attribute):
                # Add attribute names for cases like module.name
                used_names.add(node.attr)

        # Extract all imports
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    name = alias.asname if alias.asname else alias.name
                    imports.append((name, node))
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                for alias in node.names:
                    name = alias.asname if alias.asname else alias.name
                    imports.append((name, node))

        # Find unused imports
        unused_imports = []
        for name, node in imports:
            if name not in used_names and name != "__future__":
                unused_imports.append(node)

        if not unused_imports:
            return False

        # Remove unused imports
        lines = content.split('\n')
        nodes_by_lineno = {}

        # Map nodes to line numbers (handling multi-line imports)
        for node in unused_imports:
            start_line = node.lineno - 1  # Convert to 0-based
            end_line = node.end_lineno - 1 if hasattr(node, 'end_lineno') else start_line
            nodes_by_lineno[start_line] = (start_line, end_line)

        # Remove lines (in reverse order to maintain line numbers)
        for start, end in sorted(nodes_by_lineno.values(), reverse=True):
            # Check if the import has a comment on the same line
            if '"""' in lines[end] or "'''" in lines[end]:
                continue  # Don't remove lines with docstrings

            del lines[start:end+1]

        # Write back the modified content
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))

        return True
    except Exception as e:
        print(f"  Error fixing unused imports in {file_path}: {e}")
        return False


def fix_e402_imports(file_path: str) -> bool:
    """
    Fix module level imports not at top of file (E402).

    Returns True if changes were made, False otherwise.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        # Find the first non-import line after docstring
        first_code_line = 0
        docstring_end = 0
        in_docstring = False

        for i, line in enumerate(lines):
            stripped = line.strip()
            if not stripped:
                continue

            # Check for docstring
            if stripped.startswith('"""') or stripped.startswith("'''"):
                if in_docstring and (stripped.endswith('"""') or stripped.endswith("'''")):
                    in_docstring = False
                    docstring_end = i
                else:
                    in_docstring = True
                continue

            if in_docstring:
                if stripped.endswith('"""') or stripped.endswith("'''"):
                    in_docstring = False
                    docstring_end = i
                continue

            # Skip shebang and encoding
            if i == 0 and (stripped.startswith('#!') or stripped.startswith('# -*- coding:')):
                docstring_end = i
                continue

            # Skip comments
            if stripped.startswith('#'):
                continue

            # If we reach here and haven't found imports yet, this is the first code line
            if not (stripped.startswith('import ') or stripped.startswith('from ')):
                first_code_line = i
                break

        # Find any import statements after the first code line
        late_imports = []
        for i in range(first_code_line, len(lines)):
            stripped = lines[i].strip()
            if stripped.startswith('import ') or stripped.startswith('from '):
                late_imports.append(i)

        if not late_imports:
            return False

        # Move late imports to the top
        new_lines = lines[:docstring_end+1].copy()

        # Add imports
        for i in sorted(late_imports):
            new_lines.append(lines[i])

        # Add the rest of the lines, skipping the moved imports
        late_imports_set = set(late_imports)
        for i in range(first_code_line, len(lines)):
            if i not in late_imports_set:
                new_lines.append(lines[i])

        # Write back the modified content
        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)

        return True
    except Exception as e:
        print(f"  Error fixing E402 imports in {file_path}: {e}")
        return False


def fix_empty_fstrings(file_path: str) -> bool:
    """
    Fix empty f-strings (F541).

    Returns True if changes were made, False otherwise.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Find all f-strings
        original_content = content

        # Pattern to match f-strings (simplified)
        pattern = r'f["\']{1,2}["\']{1,2}'

        # Replace empty f-strings with regular strings
        content = re.sub(pattern, '""', content)

        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True

        return False
    except Exception as e:
        print(f"  Error fixing empty f-strings in {file_path}: {e}")
        return False


def fix_indentation_issues(file_path: str) -> bool:
    """
    Fix over-indented lines (E117).

    Returns True if changes were made, False otherwise.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        changes_made = False
        new_lines = lines.copy()

        for i, line in enumerate(lines):
            stripped = line.lstrip()
            if not stripped:  # Skip empty lines
                continue

            # Check for over-indented lines
            if stripped and not line.startswith(stripped):
                # Calculate current indentation
                leading_spaces = len(line) - len(stripped)

                # Skip if this is a comment
                if stripped.startswith('#'):
                    continue

                # Special case: lines that follow a dedent
                if i > 0:
                    prev_line = lines[i-1]
                    prev_stripped = prev_line.lstrip()

                    # If previous line had less indentation and this line starts a new block
                    if prev_stripped and len(prev_line) - len(prev_stripped) < leading_spaces:
                        # This might be incorrectly indented
                        new_line = ' ' * (leading_spaces - 4) + stripped
                        if new_line != line:
                            new_lines[i] = new_line
                            changes_made = True

        if changes_made:
            with open(file_path, 'w', encoding='utf-8') as fl:
                fl.writelines(new_lines)
            return True

        return False
    except Exception as e:
        print(f"  Error fixing indentation in {file_path}: {e}")
        return False


def fix_excess_blank_lines(file_path: str) -> bool:
    """
    Fix excessive blank lines (E303).

    Returns True if changes were made, False otherwise.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        new_lines = []
        consecutive_blank = 0

        for line in lines:
            if line.strip() == "":
                consecutive_blank += 1
                # Only allow 2 consecutive blank lines maximum
                if consecutive_blank <= 2:
                    new_lines.append(line)
            else:
                consecutive_blank = 0
                new_lines.append(line)

        if new_lines != lines:
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

    # Fix various linting issues
    if fix_unused_imports(file_path):
        print(f"  Fixed unused imports")
        changes_made = True

    if fix_e402_imports(file_path):
        print(f"  Fixed module level imports")
        changes_made = True

    if fix_empty_fstrings(file_path):
        print(f"  Fixed empty f-strings")
        changes_made = True

    if fix_indentation_issues(file_path):
        print(f"  Fixed indentation issues")
        changes_made = True

    if fix_excess_blank_lines(file_path):
        print(f"  Fixed excessive blank lines")
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
    os.system("flake8 --count quantchain/ scripts/")

    return total_changes


if __name__ == "__main__":
    sys.exit(main())
