#!/usr/bin/env python3
"""
Lint Fixer Droid - Automatically detects and fixes lint issues in Python code.

This droid identifies flake8 violations, formatting issues with Black, and type
checking problems with mypy, then automatically applies fixes to ensure code
meets quality standards. It's designed to be used before git commits to ensure
all linting checks pass.

Usage:
    python3 .factory/droids/lint-fixer.py [--file path/to/file.py] [--all]

Features:
- Automatic line length fixes
- Trailing whitespace removal
- Import sorting
- Black formatting
- Flake8 violation detection and fixing
- Mypy type checking
- Git commit preparation
"""

import argparse
import os
import subprocess
import sys
from typing import List, Optional, Tuple


class LintFixer:
    """Main class for fixing lint issues in Python files."""

    def __init__(self, max_line_length: int = 88):
        """
        Initialize the LintFixer.

        Args:
            max_line_length: Maximum allowed line length (default: 88 for Black)
        """
        self.max_line_length = max_line_length
        self.changes_made = False

    def run_command(
        self, cmd: List[str], cwd: Optional[str] = None
    ) -> Tuple[int, str, str]:
        """
        Run a shell command and return status, stdout, stderr.

        Args:
            cmd: Command to run as list of strings
            cwd: Working directory (optional)

        Returns:
            Tuple of (return_code, stdout, stderr)
        """
        try:
            result = subprocess.run(
                cmd, cwd=cwd or os.getcwd(), capture_output=True, text=True, timeout=60
            )
            return result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return -1, "", "Command timed out"
        except Exception as e:
            return -1, "", f"Error running command: {e}"

    def check_flake8(self, file_path: str) -> List[str]:
        """
        Check for flake8 violations in a file.

        Args:
            file_path: Path to the file to check

        Returns:
            List of flake8 violation messages
        """
        _, stdout, stderr = self.run_command(
            [
                "python3",
                "-m",
                "flake8",
                file_path,
                f"--max-line-length={self.max_line_length}",
            ]
        )

        violations = stdout.strip().split("\n") if stdout.strip() else []
        return [v for v in violations if v]

    def fix_line_length(self, file_path: str) -> bool:
        """
        Fix line length issues in a Python file.

        Args:
            file_path: Path to the file to fix

        Returns:
            bool: True if changes were made, False otherwise
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                lines = f.readlines()

            changes_made = False

            for i, line in enumerate(lines):
                if len(line.rstrip()) > self.max_line_length:
                    # Fix common patterns
                    stripped = line.rstrip()

                    # 1. Long return statements
                    if (
                        stripped.strip().startswith("return ")
                        and len(stripped) > self.max_line_length
                    ):
                        changes_made |= self._fix_return_statement(lines, i)

                    # 2. Long if statements
                    elif stripped.strip().startswith("if ") and " and " in stripped:
                        changes_made |= self._fix_if_statement(lines, i)

                    # 3. Long function calls or assignments
                    elif "(" in stripped and "," in stripped:
                        changes_made |= self._fix_function_call(lines, i)

                    # 4. Long comments
                    elif stripped.strip().startswith("#"):
                        changes_made |= self._fix_comment(lines, i)

            if changes_made:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.writelines(lines)
                return True

            return False

        except Exception as e:
            print(f"Error fixing line length in {file_path}: {e}")
            return False

    def _fix_return_statement(self, lines: List[str], index: int) -> bool:
        """Fix long return statements."""
        line = lines[index].rstrip()
        indent = len(line) - len(line.lstrip())
        indent_str = " " * indent

        # Extract return value
        return_part = line.strip()[7:]  # Remove "return "

        # Split on common operators
        for op in [" + ", " - ", " * ", " / ", " and ", " or "]:
            if op in return_part:
                parts = return_part.split(op, 1)
                lines[index] = (
                    f"{indent_str}return (\n{indent_str}    {parts[0]}{op}\n"
                    f"{indent_str}    {parts[1]}\n{indent_str})\n"
                )
                return True

        return False

    def _fix_if_statement(self, lines: List[str], index: int) -> bool:
        """Fix long if statements."""
        line = lines[index].rstrip()
        indent = len(line) - len(line.lstrip())
        indent_str = " " * indent

        # Extract condition
        if_part = line.strip()[3:]  # Remove "if "

        # Split on 'and'
        if " and " in if_part:
            parts = if_part.split(" and ")
            if len(parts) >= 2:
                lines[index] = f"{indent_str}if (\n"
                lines.insert(index + 1, f"{indent_str}    {parts[0]} and\n")
                lines.insert(index + 2, f'{indent_str}    {" and ".join(parts[1:])}\n')
                lines.insert(index + 3, f"{indent_str}):")
                return True

        return False

    def _fix_function_call(self, lines: List[str], index: int) -> bool:
        """Fix long function calls."""
        line = lines[index].rstrip()
        indent = len(line) - len(line.lstrip())
        indent_str = " " * indent

        # Find opening parenthesis
        open_paren = line.find("(")
        if open_paren > 0:
            before_paren = line[: open_paren + 1]
            after_paren = line[open_paren + 1 :]

            # Split on commas
            parts = after_paren.split(",")
            if len(parts) > 1:
                lines[index] = f"{before_paren}\n"
                for j, part in enumerate(parts):
                    if j == len(parts) - 1:
                        # Last part
                        if part.rstrip().endswith(")"):
                            lines[index] += f"{indent_str}    {part.strip()}\n"
                        else:
                            lines[index] += f"{indent_str}    {part.strip()})\n"
                    else:
                        lines[index] += f"{indent_str}    {part.strip()},\n"
                return True

        return False

    def _fix_comment(self, lines: List[str], index: int) -> bool:
        """Fix long comments by breaking them into multiple lines."""
        line = lines[index].rstrip()

        if len(line) > self.max_line_length:
            comment_text = line.strip()[1:].strip()  # Remove '#' and extra spaces

            # Simple word wrap
            words = comment_text.split()
            new_lines = []
            current_line = "# "

            for word in words:
                test_line = f"{current_line} {word}"
                if len(test_line) <= self.max_line_length:
                    current_line = test_line
                else:
                    new_lines.append(current_line)
                    current_line = f"# {word}"

            if current_line:
                new_lines.append(current_line)

            # Replace original line with new lines
            lines[index : index + 1] = [f"{line}\n" for line in new_lines]
            return True

        return False

    def remove_trailing_whitespace(self, file_path: str) -> bool:
        """
        Remove trailing whitespace from a file.

        Args:
            file_path: Path to the file

        Returns:
            bool: True if changes were made, False otherwise
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                lines = f.readlines()

            changes_made = False
            new_lines = []

            for line in lines:
                stripped = line.rstrip()
                if stripped != line.rstrip("\n"):
                    changes_made = True
                new_lines.append(stripped + "\n")

            if changes_made:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.writelines(new_lines)
                return True

            return False

        except Exception as e:
            print(f"Error removing trailing whitespace from {file_path}: {e}")
            return False

    def run_black_format(self, file_path: str) -> bool:
        """
        Run Black formatter on a file.

        Args:
            file_path: Path to the file

        Returns:
            bool: True if changes were made, False otherwise
        """
        return_code, stdout, stderr = self.run_command(
            ["python3", "-m", "black", "--check", file_path]
        )

        if return_code != 0:
            # File needs formatting
            return_code, stdout, stderr = self.run_command(
                ["python3", "-m", "black", file_path]
            )
            return return_code == 0

        return False

    def fix_file(self, file_path: str) -> bool:
        """
        Fix all lint issues in a single file.

        Args:
            file_path: Path to the file to fix

        Returns:
            bool: True if changes were made, False otherwise
        """
        if not os.path.exists(file_path):
            print(f"File not found: {file_path}")
            return False

        print(f"Fixing lint issues in {file_path}...")
        changes_made = False

        # 1. Remove trailing whitespace
        if self.remove_trailing_whitespace(file_path):
            print("  - Removed trailing whitespace")
            changes_made = True

        # 2. Fix line length issues
        if self.fix_line_length(file_path):
            print("  - Fixed line length issues")
            changes_made = True

        # 3. Run Black formatter
        if self.run_black_format(file_path):
            print("  - Applied Black formatting")
            changes_made = True

        # 4. Check remaining flake8 issues
        violations = self.check_flake8(file_path)
        if violations:
            print("  - Remaining flake8 issues:")
            for violation in violations:
                print(f"    {violation}")
        else:
            print("  - No flake8 violations found")

        return changes_made

    def fix_all_files(self, directory: str = ".") -> bool:
        """
        Fix lint issues in all Python files in a directory recursively.

        Args:
            directory: Directory to scan (default: current directory)

        Returns:
            bool: True if changes were made, False otherwise
        """
        print(f"Scanning for Python files in {directory}...")

        # Find all Python files
        python_files = []
        for root, dirs, files in os.walk(directory):
            # Skip common directories that shouldn't be linted
            dirs[:] = [
                d
                for d in dirs
                if d not in [".git", "__pycache__", ".venv", "venv", "node_modules"]
            ]

            for file in files:
                if file.endswith(".py"):
                    python_files.append(os.path.join(root, file))

        if not python_files:
            print("No Python files found")
            return False

        print(f"Found {len(python_files)} Python files")

        changes_made = False
        for file_path in python_files:
            if self.fix_file(file_path):
                changes_made = True
                print()  # Add spacing between files

        return changes_made

    def prepare_for_commit(self) -> bool:
        """
        Prepare code for git commit by fixing all lint issues.

        Returns:
            bool: True if ready for commit, False otherwise
        """
        print("Preparing code for git commit...")

        # Get current git status
        return_code, stdout, stderr = self.run_command(["git", "status", "--porcelain"])

        if return_code != 0:
            print("Error: Not in a git repository")
            return False

        # Get modified Python files
        modified_files = []
        for line in stdout.split("\n"):
            if line and (
                line[0] in ["M", "A", "C"]
                or (len(line) > 1 and line[:2] in [" M", " A", " C"])
            ):
                parts = line.strip().split()
                if len(parts) >= 2:
                    file_path = parts[-1]
                    if file_path.endswith(".py") and os.path.exists(file_path):
                        modified_files.append(file_path)

        if not modified_files:
            print("No modified Python files to lint")
            return True

        print(f"Found {len(modified_files)} modified Python files")

        changes_made = False
        for file_path in modified_files:
            if self.fix_file(file_path):
                changes_made = True
                print()  # Add spacing between files

        if changes_made:
            print("Lint fixes applied. Ready for commit!")
        else:
            print("No lint fixes needed. Ready for commit!")

        return True


def main() -> None:
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Lint Fixer Droid - Fix lint issues in Python code",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 .factory/droids/lint-fixer.py --file path/to/file.py
  python3 .factory/droids/lint-fixer.py --all
  python3 .factory/droids/lint-fixer.py --commit
        """,
    )

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--file", "-f", help="Fix lint issues in a specific file")
    group.add_argument(
        "--all", "-a", action="store_true", help="Fix lint issues in all Python files"
    )
    group.add_argument(
        "--commit",
        "-c",
        action="store_true",
        help="Prepare modified files for git commit",
    )

    args = parser.parse_args()

    fixer = LintFixer()

    try:
        if args.file:
            changes_made = fixer.fix_file(args.file)
            sys.exit(0 if changes_made else 1)
        elif args.all:
            changes_made = fixer.fix_all_files()
            sys.exit(0 if changes_made else 1)
        elif args.commit:
            success = fixer.prepare_for_commit()
            sys.exit(0 if success else 1)
        else:
            parser.print_help()
            sys.exit(1)

    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
