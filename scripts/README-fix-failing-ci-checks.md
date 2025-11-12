# Fix Failing CI Checks Command

## Overview

The `fix-failing-ci-checks` command automates the process of identifying, diagnosing, and providing recommendations for fixing failing CI checks for the current pull request.

## Usage

### Direct Python Execution
```bash
python scripts/fix-failing-ci-checks.py
```

### Shell/Batch Execution

On Unix/Linux/macOS:
```bash
./scripts/fix-failing-ci-checks
```

On Windows:
```batch
scripts\fix-failing-ci-checks.bat
```

## Prerequisites

1. **Git**: Must be in a git repository with a GitHub remote
2. **GitHub CLI (`gh`)**: Must be installed and authenticated
   - Install from: https://cli.github.com/
   - Authenticate with: `gh auth login`
3. **Python**: Python 3.9 or higher

## What It Does

1. **Detect Current PR**: Identifies the pull request associated with the current branch
2. **Identify Failing Jobs**: Lists all CI jobs that are failing
3. **Create Backup Branch**: Creates a backup branch before any modifications
4. **Generate Recommendations**: Provides detailed steps to fix each type of failure

## Output Example

```
Fix Failing CI Checks Tool
==================================================
Detecting current PR...
Found PR #60: feat: Implement mandatory 80% test coverage requirement
Identifying failing jobs...
  - integration-tests (3.13): fail
  - unit-tests (3.11): fail
  - unit-tests (3.10): fail
  - unit-tests (3.12): fail
  - unit-tests (3.13): fail
  - unit-tests (3.9): fail

Creating fix plan...
Fix plan created with 3 items
Creating backup branch...
Created backup branch: backup_before_ci_fix_20251111_234826

Generating fix recommendations...
============================================================

* Test Fixes:
   1. Run: pytest tests/unit -v --cov=quantchain --cov-fail-under=80
   2. Identify failing tests from the output
   3. Fix failing tests to ensure 80% coverage
   ...

* Quick Fix Commands:
============================================================
# Apply formatting fixes
black .

# Run tests with coverage
pytest tests/unit -v --cov=quantchain --cov-fail-under=80

# Check linting
flake8 . --count --select=E9,F63,F7,F82

# Run integration tests
pytest -m 'integration and not slow' -v
```

## Features

### Test Coverage Requirements
- Enforces the mandatory 80% test coverage requirement
- Provides coverage reporting
- Identifies files with missing test coverage

### Linting Support
- Detects and provides fixes for flake8 issues
- Applies Black formatting automatically
- Checks for critical syntax errors

### Integration Testing
- Identifies integration test failures
- Provides guidance for environment and dependency issues

## Limitations

- The tool provides recommendations only - manual intervention is required to apply fixes
- Log downloading may fail on Windows due to encoding issues
- Some automated fixes require manual verification

## Integration with Droid

To integrate this command with Droid, you can add it as a custom command in your Droid configuration.

## Troubleshooting

### "GitHub CLI not installed or not authenticated"
- Install GitHub CLI from https://cli.github.com/
- Run `gh auth login` to authenticate

### "No PR found for branch"
- Ensure you're on a branch that has an associated PR
- Create a PR if one doesn't exist

### "Unicode errors on Windows"
- The tool uses placeholders for logs when download fails
- Manually check the GitHub Actions UI for detailed logs

## Examples

### Basic Usage
```bash
# Run from project root
python scripts/fix-failing-ci-checks.py
```

### With Custom Repository Path
```bash
python scripts/fix-failing-ci-checks.py --repo-path /path/to/repo
```

## Contributing

To extend this tool:
1. Add new fix types to the `create_fix_plan` method
2. Implement new actions in the `implement_fixes` method
3. Update the failure pattern analysis in `analyze_failure_patterns`

## License

This tool is part of the QuantChain project and follows the same license terms.
