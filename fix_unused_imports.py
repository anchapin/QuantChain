#!/usr/bin/env python3
"""
Script to fix linting issues identified by flake8:
- F401: unused imports
- E712: comparison to True/False
- no-untyped-def: missing type annotations
"""

import re
import subprocess
from typing import List, Tuple


def get_flake8_errors(error_codes: List[str]) -> List[Tuple[str, int, str]]:
    """
    Run flake8 and return a list of errors for specified error codes.

    Args:
        error_codes: List of error codes to collect (e.g., ["F401", "E712"])

    Returns:
        List of tuples containing (file_path, line_number, message)
    """
    errors = []

    try:
        # Build flake8 command with specified error codes
        cmd = ["flake8", "--select=" + ",".join(error_codes), "quantchain/", "tests/"]
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False
        )

        for line in result.stdout.strip().split('\n'):
            if line and any(code in line for code in error_codes):
                # Parse the flake8 output format: file:line:column: code message
                parts = line.split(':')
                if len(parts) >= 4:
                    file_path = parts[0]
                    line_num = int(parts[1])
                    message = ':'.join(parts[3:]).strip()
                    errors.append((file_path, line_num, message))
    except Exception as e:
        print(f"Error running flake8: {e}")

    return errors


def fix_unused_imports(errors: List[Tuple[str, int, str]]) -> None:
    """
    Fix unused imports by removing them from their files.

    Args:
        errors: List of tuples containing (file_path, line_number, message)
    """
    # Group errors by file
    files_to_fix = {}
    for file_path, line_num, message in errors:
        if "F401" in message:
            if file_path not in files_to_fix:
                files_to_fix[file_path] = []
            files_to_fix[file_path].append((line_num, message))

    for file_path, line_errors in files_to_fix.items():
        try:
            with open(file_path, 'r') as f:
                lines = f.readlines()

            # Sort by line number in reverse order to avoid shifting indices
            line_errors.sort(key=lambda x: x[0], reverse=True)

            for line_num, message in line_errors:
                # Adjust for 0-based indexing
                idx = line_num - 1

                if idx < len(lines):
                    line = lines[idx].strip()

                    # Extract the import name from the message
                    import_match = re.search(r"'(.+)' imported but unused", message)
                    if import_match:
                        import_name = import_match.group(1)

                        # Check if this is the unused import we need to remove
                        if import_name in line:
                            # Remove the line
                            del lines[idx]
                        else:
                            # Try to match module parts (e.g., "module.submodule" in "from module import submodule")
                            module_parts = import_name.split('.')
                            if len(module_parts) > 1:
                                base_module = module_parts[0]
                                if line.startswith(f"from {base_module} ") and module_parts[1] in line:
                                    # This is a more complex case, need to modify the import line
                                    import_parts = line[len(f"from {base_module} "):].split(' import ')
                                    if len(import_parts) == 2:
                                        imports = import_parts[1].strip()
                                        if imports.startswith('(') and imports.endswith(')'):
                                            # Multi-line import with parentheses
                                            imports = imports[1:-1].strip()

                                        import_list = [imp.strip() for imp in imports.split(',')]
                                        # Remove the unused import
                                        import_list = [imp for imp in import_list if module_parts[1] not in imp]

                                        if import_list:
                                            new_imports = ', '.join(import_list)
                                            lines[idx] = f"from {base_module} import {new_imports}\n"
                                        else:
                                            # No imports left, remove the line
                                            del lines[idx]

            # Write the fixed content back
            with open(file_path, 'w') as f:
                f.writelines(lines)

            print(f"Fixed unused imports in {file_path}")
        except Exception as e:
            print(f"Error fixing {file_path}: {e}")


def fix_true_false_comparisons(errors: List[Tuple[str, int, str]]) -> None:
    """
    Fix E712 errors: comparison to True/False should use 'is' or 'not'.

    Args:
        errors: List of tuples containing (file_path, line_number, message)
    """
    # Group errors by file
    files_to_fix = {}
    for file_path, line_num, message in errors:
        if "E712" in message:
            if file_path not in files_to_fix:
                files_to_fix[file_path] = []
            files_to_fix[file_path].append((line_num, message))

    for file_path, line_errors in files_to_fix.items():
        try:
            with open(file_path, 'r') as f:
                content = f.read()

            # Common patterns to fix
            content = re.sub(r'([^\s]+)\s+==\s+True', r'\1 is True', content)
            content = re.sub(r'([^\s]+)\s+==\s+False', r'\1 is False', content)
            content = re.sub(r'([^\s]+)\s+!=\s+True', r'\1 is not True', content)
            content = re.sub(r'([^\s]+)\s+!=\s+False', r'\1 is not False', content)

            # Also replace with simpler forms where appropriate
            content = re.sub(r'([^\s]+)\s+is\s+True', r'\1', content)
            content = re.sub(r'([^\s]+)\s+is not\s+True', r'not \1', content)
            content = re.sub(r'([^\s]+)\s+is\s+False', r'not \1', content)
            content = re.sub(r'([^\s]+)\s+is not\s+False', r'\1', content)

            with open(file_path, 'w') as f:
                f.write(content)

            print(f"Fixed True/False comparisons in {file_path}")
        except Exception as e:
            print(f"Error fixing {file_path}: {e}")


def add_type_annotations(errors: List[Tuple[str, int, str]]) -> None:
    """
    Add type annotations for functions missing them (no-untyped-def).

    Args:
        errors: List of tuples containing (file_path, line_number, message)
    """
    # Group errors by file
    files_to_fix = {}
    for file_path, line_num, message in errors:
        if "no-untyped-def" in message:
            if file_path not in files_to_fix:
                files_to_fix[file_path] = []
            files_to_fix[file_path].append((line_num, message))

    for file_path, line_errors in files_to_fix.items():
        try:
            with open(file_path, 'r') as f:
                lines = f.readlines()

            # Process each error
            for line_num, message in sorted(line_errors, key=lambda x: x[0], reverse=True):
                idx = line_num - 1
                if idx < len(lines):
                    line = lines[idx].strip()

                    # Check if it's a function definition
                    match = re.match(r'^(\s*)def\s+(\w+)\s*\((.*)\)\s*[:]', line)
                    if match:
                        indent, func_name, params = match.groups()

                        # Skip if already has a return type annotation
                        if '->' in line:
                            continue

                        # Add "-> None" for functions that don't return a value
                        if "Use \"-> None\"" in message:
                            new_line = f"{indent}def {func_name}({params}) -> None:\n"
                            lines[idx] = new_line

            with open(file_path, 'w') as f:
                f.writelines(lines)

            print(f"Added type annotations in {file_path}")
        except Exception as e:
            print(f"Error fixing {file_path}: {e}")


def main():
    print("Fixing linting issues...")

    # Fix unused imports (F401)
    print("\n1. Fixing unused imports (F401)...")
    f401_errors = get_flake8_errors(["F401"])
    if not f401_errors:
        print("No F401 errors found.")
    else:
        print(f"Found {len(f401_errors)} unused import errors.")
        fix_unused_imports(f401_errors)

    # Fix True/False comparisons (E712)
    print("\n2. Fixing True/False comparisons (E712)...")
    e712_errors = get_flake8_errors(["E712"])
    if not e712_errors:
        print("No E712 errors found.")
    else:
        print(f"Found {len(e712_errors)} comparison errors.")
        fix_true_false_comparisons(e712_errors)

    # Add type annotations (no-untyped-def)
    print("\n3. Adding type annotations for functions...")
    type_errors = get_flake8_errors(["no-untyped-def"])
    if not type_errors:
        print("No type annotation errors found.")
    else:
        print(f"Found {len(type_errors)} type annotation errors.")
        add_type_annotations(type_errors)

    print("\nDone fixing linting issues!")


if __name__ == "__main__":
    main()
