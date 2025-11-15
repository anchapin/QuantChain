#!/usr/bin/env python3
"""
Script to fix TimeFrame imports in test files.
"""

import os
import re
from pathlib import Path

def fix_timeframe_import(file_path):
    """Add TimeFrame import to test file if it's missing."""
    try:
        with open(file_path, 'r') as f:
            content = f.read()

        # Check if TimeFrame is referenced but not imported
        if 'TimeFrame' in content and 'from alpaca.data import TimeFrame' not in content:
            # Find the last import line to add after it
            import_lines = []
            other_lines = []
            time_to_add_import = False

            lines = content.split('\n')
            for line in lines:
                # Track imports
                if line.strip().startswith('from ') or line.strip().startswith('import '):
                    import_lines.append(line)
                    # Check if this is the alpaca import block
                    if 'alpaca' in line:
                        time_to_add_import = True
                else:
                    other_lines.append(line)

            # If we found TimeFrame usage but no import, add the import
            if time_to_add_import:
                # Find where to insert the import (after other alpaca imports)
                new_content = []
                import_added = False

                for line in lines:
                    if not import_added and line.strip().startswith('from alpaca'):
                        # Add our import right after alpaca imports
                        new_content.append(line)
                        # Check if the next line is also an alpaca import or a continuation
                        if 'TimeFrame' not in line:
                            new_content.append('from alpaca.data import TimeFrame')
                            import_added = True
                    else:
                        new_content.append(line)

                # If we still haven't added the import, add it before the first test class
                if not import_added:
                    for i, line in enumerate(new_content):
                        if line.strip().startswith('class ') and 'Test' in line:
                            new_content.insert(i, 'from alpaca.data import TimeFrame')
                            new_content.insert(i, '')
                            break
                    else:
                        # Add at the end of imports if no test class found
                        new_content.append('from alpaca.data import TimeFrame')

                with open(file_path, 'w') as f:
                    f.write('\n'.join(new_content))

                print(f"Fixed TimeFrame import in {file_path}")
                return True
    except Exception as e:
        print(f"Error processing {file_path}: {e}")

    return False

def main():
    """Process all test files to fix TimeFrame imports."""
    test_dir = Path("tests/unit")
    fixed_files = 0

    for test_file in test_dir.rglob("*.py"):
        if fix_timeframe_import(test_file):
            fixed_files += 1

    print(f"Fixed TimeFrame imports in {fixed_files} files")

if __name__ == "__main__":
    main()
