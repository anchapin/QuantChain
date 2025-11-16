"""
Test runner script to check test coverage for QuantChain
"""

import os
import sys
import json
from pathlib import Path


def run_test_file(test_file_path):
    """Run a single test file and check if it passes"""
    print(f"Running: {test_file_path}")
    try:
        # Import the test module
        module_name = (
            test_file_path.replace("/", ".").replace("\\", ".").replace(".py", "")
        )

        # Add the project root to the path
        project_root = Path(__file__).parent
        sys.path.insert(0, str(project_root))

        # Import the module
        test_module = __import__(module_name, fromlist=[""])

        # Find test classes
        test_classes = [
            getattr(test_module, name)
            for name in dir(test_module)
            if name.startswith("Test")
            and hasattr(getattr(test_module, name), "__bases__")
        ]

        # Run test methods
        passed = 0
        total = 0

        for test_class in test_classes:
            # Create an instance
            test_instance = test_class()

            # Find test methods
            test_methods = [
                name for name in dir(test_instance) if name.startswith("test_")
            ]

            for method_name in test_methods:
                total += 1
                try:
                    method = getattr(test_instance, method_name)
                    method()
                    passed += 1
                    print(f"  ✅ {method_name} PASSED")
                except Exception as e:
                    print(f"  ❌ {method_name} FAILED: {e}")

        print(f"Results: {passed}/{total} tests passed")
        return passed == total

    except Exception as e:
        print(f"Error running {test_file_path}: {e}")
        return False


def check_coverage():
    """Check current test coverage"""
    print("Checking test coverage for QuantChain modules with low coverage...")

    # List of modules to check
    modules = [
        "tests/unit/backtesting/test_performance_metrics.py",
        "tests/unit/backtesting/test_market_friction.py",
        "tests/unit/backtesting/test_finrl_adapter_comprehensive.py",
        "tests/unit/tools/test_web_dashboard.py",
        "tests/unit/core/test_security.py",
    ]

    all_passed = True

    for module in modules:
        print(f"\n{'='*60}")
        if not run_test_file(module):
            all_passed = False

    print(f"\n{'='*60}")
    if all_passed:
        print("All tests passed! ✅")
    else:
        print("Some tests failed! ❌")

    return all_passed


if __name__ == "__main__":
    success = check_coverage()
    sys.exit(0 if success else 1)
