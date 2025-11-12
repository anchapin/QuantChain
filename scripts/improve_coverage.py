#!/usr/bin/env python3
"""
Script to identify files with low test coverage and generate tests for them.
"""

import json
import subprocess
import sys
from pathlib import Path


def get_coverage_report():
    """Run coverage test and return coverage data."""
    try:
        # Run coverage tests
        result = subprocess.run(
            [
                "pytest",
                "tests/unit",
                "-v",
                "--cov=quantchain",
                "--cov-report=json",
                "--cov-fail-under=0",
            ],
            capture_output=True,
            text=True,
            check=False,  # Don't fail if coverage is low
        )

        # Load coverage data
        try:
            with open("coverage.json") as f:
                return json.load(f)
        except FileNotFoundError:
            print("coverage.json not found after running tests")
            print(f"pytest output: {result.stdout}")
            if result.stderr:
                print(f"pytest stderr: {result.stderr}")
            return None
    except Exception as e:
        print(f"Error running coverage: {e}")
        return None


def find_low_coverage_files(coverage_data, threshold=80):
    """Find files with coverage below threshold."""
    low_coverage = []

    for file_path, file_data in coverage_data["files"].items():
        coverage_percent = file_data["summary"]["percent_covered"]
        if coverage_percent < threshold:
            # Convert to source file path
            if file_path.startswith("quantchain\\") or file_path.startswith(
                "quantchain/"
            ):
                source_path = file_path.replace("\\", "/")
                low_coverage.append(
                    {
                        "path": source_path,
                        "coverage": coverage_percent,
                        "missing_lines": file_data["summary"]["missing_lines"],
                    }
                )

    # Sort by coverage (lowest first)
    low_coverage.sort(key=lambda x: x["coverage"])
    return low_coverage


def generate_tests_for_file(file_path):
    """Generate tests for a specific file."""
    print("=" * 50)
    print(f"Generating tests for: {file_path}")
    print("=" * 50)

    # Check if test file already exists
    test_dir = Path("tests/unit") / Path(file_path).relative_to("quantchain").parent
    test_file = test_dir / f"test_{Path(file_path).name}"

    if test_file.exists():
        print(f"Warning: Test file already exists: {test_file}")
        response = input("Overwrite? (y/N): ").strip().lower()
        if response != "y":
            return

    # Use custom generator
    cmd = ["python", "scripts/generate_tests.py", file_path]

    try:
        subprocess.run(cmd, check=True)
        print(f"Tests generated: {test_file}")
        print(f"Run with: pytest {test_file}")
    except subprocess.CalledProcessError as e:
        print(f"Error generating tests: {e}")


def main():
    """Main function."""
    # Parse arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == "--file":
            if len(sys.argv) < 3:
                print("Usage: python improve_coverage.py --file <path/to/file.py>")
                sys.exit(1)
            # Generate tests for specific file
            generate_tests_for_file(sys.argv[2])
            return

    print("Analyzing test coverage...")

    # Get coverage data
    coverage_data = get_coverage_report()
    if not coverage_data:
        print("❌ Failed to get coverage data")
        sys.exit(1)

    # Find low coverage files
    low_coverage = find_low_coverage_files(coverage_data)

    if not low_coverage:
        print("All files have coverage >= 80%!")
        sys.exit(0)

    print(f"\nFound {len(low_coverage)} files with coverage < 80%:")
    print("\nRank | Coverage | File Path")
    print("-" * 60)

    for i, file_info in enumerate(low_coverage, 1):
        print(f"{i:4d} | {file_info['coverage']:7.1f}% | {file_info['path']}")

    # Ask user to select files
    print("\nOptions:")
    print("1. Generate tests for top N files")
    print("2. Generate tests for all low-coverage files")
    print("3. Generate tests for specific file")
    print("4. Exit")

    choice = input("\nSelect option (1-4): ").strip()

    if choice == "1":
        try:
            n = int(input("How many files? "))
            for file_info in low_coverage[:n]:
                generate_tests_for_file(file_info["path"])
        except ValueError:
            print("Invalid number")
    elif choice == "2":
        for file_info in low_coverage:
            generate_tests_for_file(file_info["path"])
    elif choice == "3":
        file_num = int(input("Enter file number: "))
        if 1 <= file_num <= len(low_coverage):
            generate_tests_for_file(low_coverage[file_num - 1]["path"])
        else:
            print("Invalid file number")
    elif choice == "4":
        print("Goodbye!")
    else:
        print("Invalid option")


if __name__ == "__main__":
    main()
