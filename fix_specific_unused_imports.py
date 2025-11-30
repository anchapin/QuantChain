#!/usr/bin/env python3
"""
Quick script to fix specific unused imports identified by flake8.
"""

import os

# Files and unused imports based on flake8 output
UNUSED_IMPORTS_FIXES = {
    "tests/unit/backtesting/test_performance_metrics_corrected.py": [
        (
            "from datetime import datetime, timedelta",
            "from datetime import ",
        ),  # Remove both
        (
            "from unittest.mock import MagicMock, Mock, patch",
            "from unittest.mock import patch",
        ),  # Remove MagicMock, Mock
    ],
    "tests/unit/backtesting/test_performance_metrics_coverage.py": [
        (
            "from datetime import datetime, timedelta",
            "from datetime import ",
        ),  # Remove both
        (
            "from unittest.mock import MagicMock, Mock, patch",
            "from unittest.mock import patch",
        ),  # Remove MagicMock, Mock
    ],
    "tests/unit/backtesting/test_performance_metrics_working.py": [
        (
            "from datetime import datetime, timedelta",
            "from datetime import ",
        ),  # Remove both
        (
            "from unittest.mock import MagicMock, Mock, patch",
            "from unittest.mock import patch",
        ),  # Remove MagicMock, Mock
    ],
    "tests/unit/connectors/test_base_interface_quick.py": [
        (
            "from unittest.mock import MagicMock, Mock, patch",
            "from unittest.mock import patch",
        ),
    ],
    "tests/unit/core/test_exceptions_comprehensive.py": [
        (
            "from unittest.mock import MagicMock, Mock, patch",
            "from unittest.mock import patch",
        ),
    ],
    "tests/unit/core/test_llm_providers_quick.py": [
        (
            "from unittest.mock import MagicMock, Mock, patch",
            "from unittest.mock import patch",
        ),
    ],
    "tests/unit/core/test_security_quick.py": [
        (
            "from unittest.mock import MagicMock, Mock, patch",
            "from unittest.mock import patch",
        ),
        (
            "from quantchain.core.security import SecurityError",
            "from quantchain.core.security import ",
        ),  # Remove SecurityError
    ],
    "tests/unit/tools/test_execution_coverage.py": [
        (
            "from unittest.mock import MagicMock, Mock, patch",
            "from unittest.mock import patch",
        ),
    ],
    "tests/unit/tools/test_execution_real.py": [
        (
            "from unittest.mock import MagicMock, Mock, patch",
            "from unittest.mock import patch",
        ),
    ],
    "tests/unit/tools/test_trading_execution_comprehensive.py": [
        (
            "from unittest.mock import MagicMock, Mock, patch",
            "from unittest.mock import patch",
        ),
    ],
    "tests/unit/tools/test_tutorial_mode_comprehensive.py": [
        (
            "from unittest.mock import MagicMock, Mock, patch",
            "from unittest.mock import patch",
        ),
    ],
    "tests/unit/tools/test_web_dashboard_comprehensive.py": [
        (
            "from unittest.mock import MagicMock, Mock, patch",
            "from unittest.mock import patch",
        ),
    ],
}


def fix_file_imports(file_path: str, fixes: list):
    """Fix imports in a file."""
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return False

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    original_content = content
    fixes_applied = 0

    for old_import, new_import in fixes:
        if old_import in content:
            content = content.replace(old_import, new_import)
            fixes_applied += 1
            print(f"  Fixed: {old_import} -> {new_import}")

    if content != original_content:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"Fixed {file_path} - applied {fixes_applied} fixes")
        return True
    else:
        print(f"No fixes needed for {file_path}")
        return False


def main():
    """Fix all unused imports."""
    print("Fixing unused imports...")
    fixed_count = 0

    for file_path, fixes in UNUSED_IMPORTS_FIXES.items():
        if fix_file_imports(file_path, fixes):
            fixed_count += 1

    print(f"\nSummary: Fixed {fixed_count}/{len(UNUSED_IMPORTS_FIXES)} files")


if __name__ == "__main__":
    main()
