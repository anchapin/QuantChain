#!/usr/bin/env python3
"""
Script to check for syntax errors in all Python files.
"""

import os
import ast
import sys

def check_file_syntax(file_path):
    """Check if a Python file has valid syntax."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        ast.parse(content)
        return True, None
    except SyntaxError as e:
        return False, str(e)
    except Exception as e:
        return False, f"Error reading file: {str(e)}"

def find_python_files(directory):
    """Find all Python files in a directory recursively."""
    python_files = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(".py"):
                python_files.append(os.path.join(root, file))
    return python_files

def main():
    """Main function."""
    directories = ["quantchain", "scripts"]
    error_count = 0
    total_files = 0

    for directory in directories:
        if not os.path.exists(directory):
            print(f"Directory {directory} does not exist, skipping...")
            continue

        python_files = find_python_files(directory)

        for file_path in python_files:
            total_files += 1
            is_valid, error = check_file_syntax(file_path)

            if not is_valid:
                print(f"Syntax error in {file_path}: {error}")
                error_count += 1

    print(f"\nProcessed {total_files} Python files")
    print(f"Found {error_count} files with syntax errors")

    return error_count

if __name__ == "__main__":
    sys.exit(main())
