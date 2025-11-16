#!/usr/bin/env python3
"""
Add @pytest.mark.integration markers to key test files to fix CI collection.
"""

import os
from pathlib import Path

def add_integration_marker(test_file):
    """Add integration marker to test file."""

    if not os.path.exists(test_file):
        return False

    try:
        with open(test_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # Check if already has integration marker
        if '@pytest.mark.integration' in content:
            return False

        # Add integration marker to first test function
        lines = content.split('\n')
        new_lines = []
        added_marker = False

        for i, line in enumerate(lines):
            if line.strip().startswith('def test_') and not added_marker:
                # Add marker before this function
                new_lines.append('@pytest.mark.integration')
                new_lines.append('')
                added_marker = True
            new_lines.append(line)

        # Write back to file
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(new_lines))

        return added_marker

    except:
        return False


def main():
    """Add integration markers to key test files."""

    # Focus on high-impact test files
    key_test_files = [
        'tests/unit/core/test_config_massive.py',
        'tests/unit/core/test_security_massive.py',
        'tests/unit/tools/test_execution_massive.py',
        'tests/unit/tools/test_web_dashboard_massive.py',
        'tests/unit/tools/test_social_media_scraper_massive.py',
        'tests/unit/agents/test_smart_contract_auditor_massive.py',
        'tests/unit/agents/test_chart_reader_agent_massive.py',
        'tests/unit/backtesting/test_engine_massive.py',
        'tests/unit/backtesting/test_performance_metrics_massive.py',
        'tests/unit/connectors/test_alpaca_connector_massive.py',
        'tests/unit/core/test_secret_managers_integration.py',  # Update existing one
    ]

    updated_count = 0
    for test_file in key_test_files:
        if add_integration_marker(test_file):
            print(f"Added integration marker to: {test_file}")
            updated_count += 1

    print(f"Updated {updated_count} test files with integration markers!")

if __name__ == "__main__":
    main()