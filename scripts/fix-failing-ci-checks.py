#!/usr/bin/env python3
"""
Fix failing CI checks script.

This script provides tools to fix common CI issues in the QuantChain project,
including formatting, linting, and test coverage problems.
"""

import argparse
import os
import shlex
import subprocess
import sys
from pathlib import Path


def run_command(cmd: list[str], capture: bool = True) -> subprocess.CompletedProcess:
    """Run a command safely with proper error handling and input validation."""
    # Validate command arguments to prevent command injection
    if not isinstance(cmd, list) or not cmd:
        raise ValueError("Command must be a non-empty list")

    # Sanitize each command argument
    sanitized_cmd = []
    for arg in cmd:
        if not isinstance(arg, str):
            raise ValueError(f"Command argument must be a string, got {type(arg)}")
        # Only allow alphanumeric characters, hyphens, underscores, dots, and common punctuation
        # This is a restrictive allowlist approach
        if not all(c.isalnum() or c in '-._/:' for c in arg):
            raise ValueError(f"Invalid characters in command argument: {arg}")
        sanitized_cmd.append(arg)

    try:
        if capture:
            result = subprocess.run(
                sanitized_cmd, capture_output=True, text=True, check=True, timeout=300
            )
        else:
            result = subprocess.run(sanitized_cmd, check=True, timeout=300)
        return result
    except subprocess.TimeoutExpired:
        print(f"Command timed out: {' '.join(sanitized_cmd)}")
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        print(f"Command failed: {' '.join(sanitized_cmd)}")
        print(f"Error: {e}")
        if capture and e.stdout:
            print(f"Output: {e.stdout}")
        if capture and e.stderr:
            print(f"Stderr: {e.stderr}")
        sys.exit(1)


def fix_formatting(repo_path: str) -> None:
    """Fix code formatting issues."""
    print("Fixing code formatting...")
    os.chdir(repo_path)

    # Run black to fix formatting
    run_command(["black", "."])

    # Run isort to fix import sorting
    run_command(["isort", "."])

    print("✅ Code formatting fixed!")


def run_linting(repo_path: str) -> None:
    """Run linting checks and report issues."""
    print("Running linting checks...")
    os.chdir(repo_path)

    # Run flake8 for syntax issues
    try:
        run_command(
            [
                "flake8",
                ".",
                "--count",
                "--select=E9,F63,F7,F82",
                "--show-source",
                "--statistics",
            ]
        )
        print("✅ No syntax errors found!")
    except subprocess.CalledProcessError:
        print("❌ Syntax errors found!")
        sys.exit(1)


def run_tests(repo_path: str, coverage: bool = True) -> None:
    """Run tests with optional coverage check."""
    print("Running tests...")
    os.chdir(repo_path)

    cmd = ["pytest", "tests/unit", "-v", "-m", "unit", "--tb=short"]

    if coverage:
        cmd.extend(
            ["--cov=quantchain", "--cov-report=term-missing", "--cov-fail-under=80"]
        )

    run_command(cmd, capture=False)
    print("✅ Tests passed!")


def check_dependencies(repo_path: str) -> None:
    """Check if required dependencies are installed."""
    print("Checking dependencies...")
    os.chdir(repo_path)

    required_packages = ["pytest", "pytest-cov", "black", "isort", "flake8", "mypy"]

    missing_packages = []

    for package in required_packages:
        try:
            run_command([sys.executable, "-c", f"import {package.replace('-', '_')}"])
            print(f"✅ {package} is installed")
        except subprocess.CalledProcessError:
            missing_packages.append(package)
            print(f"❌ {package} is missing")

    if missing_packages:
        print(f"\nInstalling missing packages: {', '.join(missing_packages)}")
        run_command([sys.executable, "-m", "pip", "install"] + missing_packages)
        print("✅ Dependencies installed!")
    else:
        print("✅ All dependencies are available!")


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Fix failing CI checks")
    parser.add_argument("--repo-path", type=str, default=".", help="Path to repository")
    parser.add_argument("--formatting", action="store_true", help="Fix code formatting")
    parser.add_argument("--lint", action="store_true", help="Run linting checks")
    parser.add_argument("--test", action="store_true", help="Run tests")
    parser.add_argument(
        "--coverage", action="store_true", default=True, help="Include coverage check"
    )
    parser.add_argument(
        "--deps", action="store_true", help="Check and install dependencies"
    )
    parser.add_argument("--all", action="store_true", help="Run all fixes")

    args = parser.parse_args()

    repo_path = os.path.abspath(args.repo_path)

    if not os.path.exists(repo_path):
        print(f"Error: Repository path {repo_path} does not exist")
        sys.exit(1)

    print(f"Working in repository: {repo_path}")

    if args.all:
        check_dependencies(repo_path)
        fix_formatting(repo_path)
        run_linting(repo_path)
        run_tests(repo_path, args.coverage)
    else:
        if args.deps:
            check_dependencies(repo_path)
        if args.formatting:
            fix_formatting(repo_path)
        if args.lint:
            run_linting(repo_path)
        if args.test:
            run_tests(repo_path, args.coverage)

    print("🎉 CI fixes completed successfully!")


if __name__ == "__main__":
    main()
