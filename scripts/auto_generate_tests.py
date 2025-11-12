#!/usr/bin/env python3
"""
Automated test generation script to achieve 80% coverage.
Generates tests for the lowest coverage files first.
"""

import json
import os
import subprocess
import sys
from pathlib import Path


def get_coverage_report():
    """Run coverage test and return coverage data."""
    try:
        # Run coverage tests
        result = subprocess.run(
            ["pytest", "tests/unit", "-v", "--cov=quantchain", "--cov-report=json", "--cov-fail-under=0"],
            capture_output=True,
            text=True,
            check=False  # Don't fail if coverage is low
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
            if file_path.startswith("quantchain\\") or file_path.startswith("quantchain/"):
                source_path = file_path.replace("\\", "/")
                low_coverage.append({
                    "path": source_path,
                    "coverage": coverage_percent,
                    "missing_lines": file_data["summary"]["missing_lines"]
                })
    
    # Sort by coverage (lowest first)
    low_coverage.sort(key=lambda x: x["coverage"])
    return low_coverage


def generate_tests_for_file(file_path):
    """Generate tests for a specific file."""
    print(f"\nGenerating tests for: {file_path}")
    print("="*50)
    
    # Use custom generator
    cmd = ["python", "scripts/generate_tests.py", file_path]
    
    try:
        subprocess.run(cmd, check=True)
        print(f"Tests generated successfully for {file_path}")
    except subprocess.CalledProcessError as e:
        print(f"Error generating tests: {e}")


def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate tests to improve coverage")
    parser.add_argument("--top", type=int, default=5, help="Generate tests for top N low-coverage files")
    parser.add_argument("--all", action="store_true", help="Generate tests for all low-coverage files")
    parser.add_argument("--threshold", type=float, default=80.0, help="Coverage threshold (default: 80.0)")
    
    args = parser.parse_args()
    
    print("Analyzing test coverage...")
    
    # Get coverage data
    coverage_data = get_coverage_report()
    if not coverage_data:
        print("Failed to get coverage data")
        sys.exit(1)
    
    # Find low coverage files
    low_coverage = find_low_coverage_files(coverage_data, args.threshold)
    
    if not low_coverage:
        print(f"All files have coverage >= {args.threshold}%!")
        sys.exit(0)
    
    print(f"\nFound {len(low_coverage)} files with coverage < {args.threshold}%:")
    print("\nRank | Coverage | File Path")
    print("-" * 60)
    
    for i, file_info in enumerate(low_coverage[:args.top] if not args.all else low_coverage, 1):
        print(f"{i:4d} | {file_info['coverage']:7.1f}% | {file_info['path']}")
    
    # Determine which files to process
    files_to_process = low_coverage if args.all else low_coverage[:args.top]
    
    print(f"\nGenerating tests for {len(files_to_process)} files...")
    
    for file_info in files_to_process:
        generate_tests_for_file(file_info["path"])
    
    # Run coverage again to check improvement
    print("\nRunning coverage check after generating tests...")
    subprocess.run(
        ["pytest", "tests/unit", "-v", "--cov=quantchain", "--cov-report=term-missing"],
        check=False
    )


if __name__ == "__main__":
    main()
