#!/usr/bin/env python
"""
Simple test runner to execute our new test files directly
"""

import subprocess
import sys
import os
from pathlib import Path

def run_test_file(test_file_path):
    """Run a single test file directly"""
    print(f"Running: {test_file_path}")
    result = subprocess.run([
        sys.executable, "-m", "pytest",
        test_file_path,
        "-v",
        "--tb=short"
    ], capture_output=True, text=True)

    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr)

    return result.returncode == 0

def main():
    """Main function"""
    print("QuantChain Test Coverage Improvement - Simple Test Runner")
    print("=" * 60)

    # Directory containing our test files
    test_dir = Path("test_coverage_improvements")

    # Test files to run
    test_files = [
        "web_dashboard_tests.py",
        "security_tests.py",
        "ib_async_execution_tests.py",
        "../tests/unit/backtesting/test_performance_metrics.py",
        "../tests/unit/backtesting/test_market_friction.py"
    ]

    success_count = 0
    total_count = len(test_files)

    for test_file in test_files:
        test_path = test_dir / test_file
        if test_path.exists():
            if run_test_file(str(test_path)):
                success_count += 1
                print(f"✅ {test_file} PASSED")
            else:
                print(f"❌ {test_file} FAILED")
        else:
            print(f"⚠️  {test_file} NOT FOUND")

    print("=" * 60)
    print(f"Results: {success_count}/{total_count} test files passed")

    if success_count == total_count:
        print("\nAll test files passed! ✅")
        return 0
    else:
        print(f"\n{total_count - success_count} test files failed! ❌")
        return 1

if __name__ == "__main__":
    sys.exit(main())
