#!/usr/bin/env python3
"""
Script to fix unused imports identified by flake8 F401 errors.
"""

import os
import re

# List of files and their unused imports based on flake8 output
UNUSED_IMPORTS = {
    "tests/unit/agents/test_memecoin_vibe_trader_coverage.py": [
        ("unittest.mock.MagicMock", "unittest.mock"),
        ("pandas as pd", "pandas"),
    ],
    "tests/unit/agents/test_smart_contract_auditor.py": [
        ("unittest.mock.MagicMock", "unittest.mock"),
        ("unittest.mock.PropertyMock", "unittest.mock"),
        (
            "quantchain.agents.smart_contract_auditor.Vulnerability",
            "quantchain.agents.smart_contract_auditor",
        ),
        (
            "quantchain.agents.smart_contract_auditor.VulnerabilitySeverity",
            "quantchain.agents.smart_contract_auditor",
        ),
    ],
    "tests/unit/backtesting/test_backtestingpy_engine.py": [
        (
            "quantchain.backtesting.backtestingpy_engine",
            "quantchain.backtesting.backtestingpy_engine",
        ),
    ],
    "tests/unit/backtesting/test_finrl_adapter.py": [
        (
            "quantchain.backtesting.finrl_adapter",
            "quantchain.backtesting.finrl_adapter",
        ),
    ],
    "tests/unit/backtesting/test_market_friction.py": [
        (
            "quantchain.backtesting.market_friction",
            "quantchain.backtesting.market_friction",
        ),
    ],
    "tests/unit/backtesting/test_performance_metrics.py": [
        (
            "quantchain.backtesting.performance_metrics",
            "quantchain.backtesting.performance_metrics",
        ),
    ],
    "tests/unit/backtesting/test_performance_metrics_corrected.py": [
        ("datetime.datetime", "datetime"),
        ("datetime.timedelta", "datetime"),
        ("unittest.mock.MagicMock", "unittest.mock"),
        ("unittest.mock.Mock", "unittest.mock"),
        ("unittest.mock.patch", "unittest.mock"),
        ("numpy as np", "numpy"),
    ],
    "tests/unit/backtesting/test_performance_metrics_coverage.py": [
        ("datetime.datetime", "datetime"),
        ("datetime.timedelta", "datetime"),
        ("unittest.mock.MagicMock", "unittest.mock"),
        ("numpy as np", "numpy"),
        ("pandas as pd", "pandas"),
    ],
    "tests/unit/backtesting/test_performance_metrics_working.py": [
        ("datetime.datetime", "datetime"),
        ("datetime.timedelta", "datetime"),
        ("unittest.mock.MagicMock", "unittest.mock"),
        ("unittest.mock.Mock", "unittest.mock"),
        ("unittest.mock.patch", "unittest.mock"),
    ],
    "tests/unit/connectors/test_alpaca_connector.py": [
        (
            "quantchain.connectors.alpaca_connector",
            "quantchain.connectors.alpaca_connector",
        ),
    ],
    "tests/unit/connectors/test_base_interface_quick.py": [
        ("unittest.mock.MagicMock", "unittest.mock"),
        ("unittest.mock.patch", "unittest.mock"),
    ],
    "tests/unit/connectors/test_dexscreener_connector.py": [
        (
            "quantchain.connectors.dexscreener_connector",
            "quantchain.connectors.dexscreener_connector",
        ),
    ],
    "tests/unit/core/test_agent_engine.py": [
        ("quantchain.core.agent_engine", "quantchain.core.agent_engine"),
    ],
    "tests/unit/core/test_config_comprehensive.py": [
        ("tempfile.NamedTemporaryFile", "tempfile"),
    ],
    "tests/unit/core/test_exceptions_comprehensive.py": [
        ("quantchain.core.exceptions.QuantChainError", "quantchain.core.exceptions"),
    ],
    "tests/unit/core/test_rag_system_comprehensive.py": [
        ("quantchain.core.rag_system.RAGSystem", "quantchain.core.rag_system"),
    ],
    "tests/unit/core/test_reflection_comprehensive.py": [
        ("quantchain.core.reflection.ReflectionEngine", "quantchain.core.reflection"),
    ],
    "tests/unit/tools/test_ci_fixer.py": [
        ("quantchain.tools.ci_fixer.CIFixer", "quantchain.tools.ci_fixer"),
    ],
    "tests/unit/tools/test_execution_coverage.py": [
        ("unittest.mock.MagicMock", "unittest.mock"),
    ],
    "tests/unit/tools/test_trading_execution_comprehensive.py": [
        ("unittest.mock.MagicMock", "unittest.mock"),
    ],
    "tests/unit/tools/test_tutorial_mode_comprehensive.py": [
        ("unittest.mock.MagicMock", "unittest.mock"),
    ],
    "tests/unit/tools/test_web_dashboard_comprehensive.py": [
        ("unittest.mock.MagicMock", "unittest.mock"),
    ],
}


def remove_unused_import(file_path: str, unused_imports: list):
    """Remove unused imports from a file."""
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return False

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    original_content = content
    removed_count = 0

    for import_statement, module_name in unused_imports:
        # Handle multi-line imports (from ... import ...)
        if " from " in import_statement or import_statement.startswith("from "):
            # Pattern to match "from module import name1, name2, name3"
            # and remove specific names while keeping the import if other names are still used
            pattern = rf"(from\s+{re.escape(module_name)}\s+import\s+)([^#\n]+)"
            matches = re.finditer(pattern, content)

            for match in matches:
                prefix = match.group(1)
                import_list = match.group(2)

                # Remove the unused import from the list
                names = [name.strip() for name in import_list.split(",")]
                filtered_names = [
                    name
                    for name in names
                    if name
                    and not any(
                        unused in name
                        for unused, _ in [(import_statement, module_name)]
                        if unused in import_statement
                    )
                ]

                if filtered_names:
                    # Replace with filtered list
                    new_import = prefix + ", ".join(filtered_names)
                    content = content.replace(match.group(0), new_import)
                else:
                    # Remove entire import line if no names left
                    content = content.replace(match.group(0), "")
                removed_count += 1

        # Handle simple imports
        else:
            # Remove the entire line containing the unused import
            lines = content.split("\n")
            new_lines = []
            for line in lines:
                if import_statement not in line:
                    new_lines.append(line)
                else:
                    removed_count += 1
            content = "\n".join(new_lines)

    # Clean up multiple blank lines and trailing whitespace
    lines = content.split("\n")
    cleaned_lines = []
    prev_blank = False
    for line in lines:
        line = line.rstrip()
        if line == "":
            if not prev_blank:
                cleaned_lines.append(line)
            prev_blank = True
        else:
            cleaned_lines.append(line)
            prev_blank = False

    content = "\n".join(cleaned_lines)

    if content != original_content:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"Fixed {file_path} - removed {removed_count} unused imports")
        return True
    else:
        print(f"No changes needed for {file_path}")
        return False


def main():
    """Main function to fix unused imports."""
    print("Fixing unused imports...")

    fixed_count = 0
    total_files = len(UNUSED_IMPORTS)

    for file_path, unused_imports in UNUSED_IMPORTS.items():
        full_path = os.path.abspath(file_path)
        if remove_unused_import(full_path, unused_imports):
            fixed_count += 1

    print(f"\nSummary: Fixed {fixed_count}/{total_files} files")


if __name__ == "__main__":
    main()
