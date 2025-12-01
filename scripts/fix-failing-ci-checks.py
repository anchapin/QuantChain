#!/usr/bin/env python3
"""
Fix failing CI checks script.

This script provides tools to fix common CI issues in the QuantChain project,
including formatting, linting, and test coverage problems.
"""

import argparse
import os
import subprocess
import sys


def _is_valid_char(char: str) -> bool:
    """Check if a character is allowed in command arguments."""
    return char.isalnum() or char in "-._/"


def _validate_argument(arg: str) -> str:
    """Validate a single command argument."""
    if not isinstance(arg, str):
        raise ValueError(f"Command argument must be a string, got {type(arg)}")

    # Only allow alphanumeric characters, hyphens, underscores, dots, and forward slashes
    # This is a restrictive allowlist approach - exclude colons and other dangerous chars
    if not all(_is_valid_char(c) for c in arg):
        raise ValueError(f"Invalid characters in command argument: {arg}")

    return arg


def _validate_command(cmd: list[str]) -> list[str]:
    """Validate and sanitize command arguments."""
    if not isinstance(cmd, list) or not cmd:
        raise ValueError("Command must be a non-empty list")

    return [_validate_argument(arg) for arg in cmd]


def _run_subprocess(
    sanitized_cmd: list[str], capture: bool
) -> subprocess.CompletedProcess:
    """Execute the subprocess with the given parameters."""
    if capture:
        return subprocess.run(
            sanitized_cmd, capture_output=True, text=True, check=True, timeout=300
        )
    else:
        return subprocess.run(sanitized_cmd, check=True, timeout=300)


def _handle_command_error(
    error: Exception, sanitized_cmd: list[str], capture: bool
) -> None:
    """Handle command execution errors."""
    cmd_str = " ".join(sanitized_cmd)

    if isinstance(error, subprocess.TimeoutExpired):
        print(f"Command timed out: {cmd_str}")
    elif isinstance(error, subprocess.CalledProcessError):
        print(f"Command failed: {cmd_str}")
        print(f"Error: {error}")
        if capture and hasattr(error, "stdout") and error.stdout:
            print(f"Output: {error.stdout}")
        if capture and hasattr(error, "stderr") and error.stderr:
            print(f"Stderr: {error.stderr}")
    else:
        print(f"Unexpected error running command: {cmd_str}")
        print(f"Error: {error}")

    sys.exit(1)


def run_command(cmd: list[str], capture: bool = True) -> subprocess.CompletedProcess:
    """Run a command safely with proper error handling and input validation."""
    sanitized_cmd = _validate_command(cmd)

    try:
        return _run_subprocess(sanitized_cmd, capture)
    except (subprocess.TimeoutExpired, subprocess.CalledProcessError) as error:
        _handle_command_error(error, sanitized_cmd, capture)


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
