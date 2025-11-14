"""
Script to run new test files and improve test coverage
"""
import os
import sys
import subprocess
import json
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def run_command(cmd, cwd=None):
    """Run a command and return the result"""
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    print(f"Exit code: {result.returncode}")
    if result.stdout:
        print(f"Output:\n{result.stdout}")
    if result.stderr:
        print(f"Error:\n{result.stderr}")
    return result

def run_coverage_tests():
    """Run tests with coverage"""
    print("=" * 80)
    print("RUNNING TESTS WITH COVERAGE")
    print("=" * 80)

    # Change to project directory
    os.chdir(project_root)

    # Run pytest with coverage
    result = run_command([
        sys.executable, "-m", "pytest",
        "test_coverage_improvements/web_dashboard_tests.py",
        "test_coverage_improvements/security_tests.py",
        "test_coverage_improvements/ib_async_execution_tests.py",
        "--cov=quantchain",
        "--cov-report=term-missing",
        "--cov-report=html",
        "--cov-report=json",
        "-v"
    ])

    return result.returncode == 0

def show_coverage_report():
    """Display the coverage report"""
    print("\n" + "=" * 80)
    print("COVERAGE REPORT")
    print("=" * 80)

    # Read coverage JSON
    with open("coverage.json", "r") as f:
        data = json.load(f)

    # Display overall coverage
    totals = data["totals"]
    print(f"Overall coverage: {totals['percent_covered']:.2f}%")
    print(f"Lines: {totals['covered_lines']}/{totals['num_statements']}")
    print(f"Missing: {totals['missing_lines']}")

    # Display files with lowest coverage
    low_coverage = []
    for filename, file_data in data["files"].items():
        if filename.startswith("quantchain") and file_data["summary"]["num_statements"] > 0:
            percent = file_data["summary"]["percent_covered"]
            if percent < 80:
                low_coverage.append((filename, percent, file_data["summary"]["missing_lines"]))

    low_coverage.sort(key=lambda x: x[1])

    print("\nFiles with lowest coverage (< 80%):")
    print("-" * 80)
    for filename, percent, missing in low_coverage[:10]:
        print(f"{percent:5.1f}% {filename}")
        print(f"       Missing: {missing} lines")
        print()

def copy_new_test_files():
    """Copy new test files to the appropriate test directories"""
    print("\n" + "=" * 80)
    print("COPYING NEW TEST FILES")
    print("=" * 80)

    # Source directory
    src_dir = project_root / "test_coverage_improvements"

    # Copy web dashboard tests
    web_tests_src = src_dir / "web_dashboard_tests.py"
    web_tests_dst = project_root / "tests" / "unit" / "tools" / "test_web_dashboard_comprehensive.py"
    if web_tests_src.exists():
        os.makedirs(os.path.dirname(web_tests_dst), exist_ok=True)
        run_command(["cp", str(web_tests_src), str(web_tests_dst)])
        print(f"Copied web dashboard tests to {web_tests_dst}")

    # Copy security tests
    security_tests_src = src_dir / "security_tests.py"
    security_tests_dst = project_root / "tests" / "unit" / "core" / "test_security_comprehensive.py"
    if security_tests_src.exists():
        os.makedirs(os.path.dirname(security_tests_dst), exist_ok=True)
        run_command(["cp", str(security_tests_src), str(security_tests_dst)])
        print(f"Copied security tests to {security_tests_dst}")

    # Copy IB async execution tests
    ib_tests_src = src_dir / "ib_async_execution_tests.py"
    ib_tests_dst = project_root / "tests" / "unit" / "connectors" / "test_ib_async_execution_comprehensive.py"
    if ib_tests_src.exists():
        os.makedirs(os.path.dirname(ib_tests_dst), exist_ok=True)
        run_command(["cp", str(ib_tests_src), str(ib_tests_dst)])
        print(f"Copied IB async execution tests to {ib_tests_dst}")

def run_all_tests():
    """Run all tests with coverage"""
    print("\n" + "=" * 80)
    print("RUNNING ALL TESTS WITH COVERAGE")
    print("=" * 80)

    # Change to project directory
    os.chdir(project_root)

    # Run pytest with coverage
    result = run_command([
        sys.executable, "-m", "pytest",
        "tests/",
        "--cov=quantchain",
        "--cov-report=term-missing",
        "--cov-report=html",
        "--cov-report=json",
        "-v"
    ])

    return result.returncode == 0

def main():
    """Main function"""
    print("QuantChain Test Coverage Improvement Script")

    # Copy new test files
    copy_new_test_files()

    # Run new tests with coverage
    if run_coverage_tests():
        print("New tests passed successfully!")
    else:
        print("Some new tests failed. Check the output above.")

    # Show coverage report
    show_coverage_report()

    # Ask if user wants to run all tests
    response = input("\nDo you want to run all tests with coverage? (y/n): ")
    if response.lower() == 'y':
        run_all_tests()
        show_coverage_report()

    print("\nCoverage report is available at:")
    print(f"- HTML: {project_root / 'htmlcov' / 'index.html'}")
    print(f"- JSON: {project_root / 'coverage.json'}")

if __name__ == "__main__":
    main()
