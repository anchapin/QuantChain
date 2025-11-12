"""Command-line interface for QuantChain tools."""

import sys

from quantchain.tools.ci_fixer import CIFixer


def main():
    """Main CLI entry point."""
    if len(sys.argv) < 2:
        print("Usage: python -m quantchain.tools <command>")
        print("\nAvailable commands:")
        print("  fix-failing-ci-checks  - Fix failing CI checks")
        print("  help                 - Show this help message")
        sys.exit(1)

    command = sys.argv[1]

    if command == "help":
        print("Usage: python -m quantchain.tools <command>")
        print("\nAvailable commands:")
        print("  fix-failing-ci-checks  - Fix failing CI checks")
        print("                         Automates fixing failing CI checks by:")
        print("                         1. Detecting current PR")
        print("                         2. Identifying failing jobs")
        print("                         3. Downloading and analyzing logs")
        print("                         4. Creating and implementing fix plans")
        print("                         5. Verifying fixes locally")
        print("\nPrerequisites:")
        print("  - GitHub CLI (gh) installed and authenticated")
        print("  - pytest, flake8, black, mypy installed")
        print("  - Running from a git repository with GitHub remote")

    elif command == "fix-failing-ci-checks":
        try:
            fixer = CIFixer()
            success = fixer.run_fix_process()
            sys.exit(0 if success else 1)
        except KeyboardInterrupt:
            print("\nProcess interrupted by user")
            sys.exit(1)
        except Exception as e:
            print(f"Error: {e}")
            sys.exit(1)

    else:
        print(f"Unknown command: {command}")
        print("Use 'help' to see available commands")
        sys.exit(1)


if __name__ == "__main__":
    main()
