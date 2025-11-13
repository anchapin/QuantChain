#!/usr/bin/env python3
"""
Utility script to add import guards for optional dependencies across the codebase.
This helps with Python 3.9 compatibility and graceful degradation when dependencies are missing.
"""

import os
import re
from pathlib import Path
from typing import Dict, List, Set

# Mapping of problematic imports to their guard patterns
IMPORT_GUARDS = {
    "from alpaca": """
# Alpaca compatibility guard
ALPACA_AVAILABLE = False
try:
    from alpaca.data import (
        HistoricalCryptoData,
        StockDataStream,
        StockTradeApi,
    )
    from alpaca.trading.client import Client as AlpacaTradingClient
    from alpaca import TradingStream
    ALPACA_AVAILABLE = True
except ImportError:
    pass

""",
    "from langgraph": """
# LangGraph compatibility guard
LANGGRAPH_AVAILABLE = False
try:
    from langgraph.graph import StateGraph, END
    LANGGRAPH_AVAILABLE = True
except ImportError:
    StateGraph = None
    END = None
    LANGGRAPH_AVAILABLE = False

""",
    "import gymnasium": """
# Gymnasium compatibility guard
GYMNASIUM_AVAILABLE = False
try:
    import gymnasium as gym
    GYMNASIUM_AVAILABLE = True
except ImportError:
    gym = None
    GYMNASIUM_AVAILABLE = False

""",
    "import ib_async": """
# IB Async compatibility guard
IB_ASYNC_AVAILABLE = False
try:
    import ib_async
    IB_ASYNC_AVAILABLE = True
except ImportError:
    pass

""",
    "from ib_async": """
# IB Async compatibility guard
IB_ASYNC_AVAILABLE = False
try:
    from ib_async.client import IB
    from ib_async.contract import Contract
    IB_ASYNC_AVAILABLE = True
except ImportError:
    IB = None
    Contract = None
    IB_ASYNC_AVAILABLE = False

""",
}

def find_files_with_imports(root_dir: Path) -> Dict[str, List[Path]]:
    """Find Python files that contain problematic imports."""
    files_with_imports = {}
    
    for import_pattern in IMPORT_GUARDS.keys():
        matching_files = []
        for py_file in root_dir.rglob("*.py"):
            # Skip __pycache__ and .git directories
            if "__pycache__" in str(py_file) or ".git" in str(py_file):
                continue
                
            try:
                content = py_file.read_text(encoding='utf-8')
                if import_pattern in content:
                    matching_files.append(py_file)
            except (UnicodeDecodeError, PermissionError):
                continue
                
        if matching_files:
            files_with_imports[import_pattern] = matching_files
    
    return files_with_imports

def has_guard_already(file_path: Path, guard_pattern: str) -> bool:
    """Check if a file already has the import guard."""
    try:
        content = file_path.read_text(encoding='utf-8')
        # Check for key indicators that the guard is already present
        if "ALPACA_AVAILABLE" in guard_pattern and "ALPACA_AVAILABLE" in content:
            return True
        if "LANGGRAPH_AVAILABLE" in guard_pattern and "LANGGRAPH_AVAILABLE" in content:
            return True
        if "GYMNASIUM_AVAILABLE" in guard_pattern and "GYMNASIUM_AVAILABLE" in content:
            return True
        if "IB_ASYNC_AVAILABLE" in guard_pattern and "IB_ASYNC_AVAILABLE" in content:
            return True
    except (UnicodeDecodeError, PermissionError):
        pass
    return False

def add_guard_to_file(file_path: Path, import_pattern: str, guard_code: str) -> bool:
    """Add import guard to a Python file."""
    try:
        content = file_path.read_text(encoding='utf-8')
        lines = content.splitlines()
        
        # Find the docstring end to insert guards after it
        insert_index = 0
        docstring_end = False
        
        for i, line in enumerate(lines):
            insert_index = i + 1
            if line.strip().startswith('"""') or line.strip().startswith("'''"):
                # Found docstring start, look for end
                if line.count('"""') == 2 or line.count("'''") == 2:
                    # Single line docstring
                    break
                else:
                    # Multi-line docstring, find the end
                    quote_type = '"""' if '"""' in line else "'''"
                    for j in range(i + 1, len(lines)):
                        if quote_type in lines[j]:
                            insert_index = j + 1
                            break
                    break
            elif line.strip() and not line.strip().startswith('#'):
                # First non-comment, non-empty line after docstring
                break
        
        # Insert the guard code
        new_lines = lines[:insert_index] + [guard_code] + lines[insert_index:]
        new_content = '\n'.join(new_lines)
        
        # Write back to file
        file_path.write_text(new_content, encoding='utf-8')
        print(f"Added guard to {file_path}")
        return True
        
    except (UnicodeDecodeError, PermissionError) as e:
        print(f"Error processing {file_path}: {e}")
        return False

def main():
    """Main function to add import guards to all necessary files."""
    root_dir = Path(__file__).parent
    
    print("Scanning for files with problematic imports...")
    files_with_imports = find_files_with_imports(root_dir)
    
    total_files_modified = 0
    
    for import_pattern, files in files_with_imports.items():
        print(f"\nProcessing import pattern: {import_pattern}")
        guard_code = IMPORT_GUARDS[import_pattern]
        
        for file_path in files:
            # Skip if guard is already present
            if has_guard_already(file_path, guard_code):
                print(f"Skipping {file_path} (guard already present)")
                continue
            
            # Skip certain directories that are already handled
            if "__pycache__" in str(file_path) or ".git" in str(file_path):
                continue
                
            # Skip test files for now (they have different handling)
            if "test_" in file_path.name:
                print(f"Skipping test file {file_path}")
                continue
                
            if add_guard_to_file(file_path, import_pattern, guard_code):
                total_files_modified += 1
    
    print(f"\nSummary: Added guards to {total_files_modified} files")

if __name__ == "__main__":
    main()