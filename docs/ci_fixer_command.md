# Fix Failing CI Checks Command

This document describes the `fix-failing-ci-checks` command that automates the process of identifying, diagnosing, and fixing failing CI checks for the current pull request.

## Usage

```bash
# Using the CLI module
python -m quantchain.tools fix-failing-ci-checks

# Using the installed script (after pip install)
quantchain fix-failing-ci-checks

# Show help
python -m quantchain.tools help
```

## Prerequisites

- Must be in a git repository with a GitHub remote
- Must have the GitHub CLI (`gh`) installed and authenticated
- Must have local test environment set up with the following tools:
  - `pytest` for running tests
  - `flake8` for linting
  - `black` for code formatting
  - `mypy` for type checking
  - `autopep8` (optional) for automatic code fixes

## Implementation Details

### 1. Detect Current PR

The command uses the GitHub CLI to:
1. Get the current branch name using `git rev-parse --abbrev-ref HEAD`
2. Find the associated PR using `gh pr list --head <branch> --json number,title,state,headRepository,headRefName`

### 2. Identify Failing Jobs

Uses `gh pr checks --json name,conclusion,detailsUrl,startedAt,completedAt` to get the status of all CI jobs and filters for failed ones.

### 3. Download Failure Logs

For each failing job:
1. Extracts the job ID from the details URL
2. Downloads logs using `gh api repos/{owner}/{repo}/actions/jobs/{job_id}/logs`
3. Saves logs to `logs/{job_name}_{job_id}.log`

### 4. Analyze Failure Patterns

Parses log files to identify common failure types:

#### Test Failures
- Pytest failures: `FAILED <test_path> -`
- Assertion errors: `AssertionError: <error_message>`

#### Linting Errors
- Flake8 errors: `<file>:<line>:<column>: <code> <message>`
- Black formatting issues: `would reformat <file>`

#### Type Checking Errors
- MyPy errors: `<file>:<line>: error: <message>`

#### Build Errors
- ModuleNotFoundError: `No module named <module>`
- ImportError: `ImportError: <message>`

#### Dependency Issues
- Version conflicts: `Could not find a version that satisfies the requirement`
- General dependency conflicts

### 5. Create Fix Plan

Based on the analysis, creates a prioritized fix plan:

- **High Priority**: Test failures, build errors, dependency issues
- **Medium Priority**: Linting errors, type checking errors

Each fix item includes:
- Type of fix
- Description
- Priority level
- Specific actions to take

### 6. Implement Fixes

Automatically applies fixes where possible:

#### Automated Fixes
- **Black formatting**: Runs `black quantchain tests/`
- **Autopep8 fixes**: Runs `autopep8 --in-place --aggressive quantchain tests/`

#### Manual Fixes Required
- **Test failures**: Requires code changes and test debugging
- **Type errors**: Requires adding type annotations
- **Build errors**: Requires fixing imports and dependencies
- **Dependency issues**: Requires updating requirements files

### 7. Verify Fixes

Runs local verification tests:
1. **Tests**: `pytest --cov=quantchain tests/` (with 5-minute timeout)
2. **Linting**: `flake8 quantchain tests/`
3. **Formatting**: `black --check quantchain tests/`

## Example Output

```
🚀 Starting CI fix process...
📋 Detected PR #123: "Add new feature"
❌ Found 3 failing jobs
🔍 Analyzed failure patterns: 5 categories
📝 Created fix plan with 2 items

🔧 Implementing linting_fixes: Fix 5 linting errors
✅ Applied black formatting
⚠️ Linting issues:
quantchain/tools/example.py:10:1: E302 expected 2 blank lines, not 1

🔧 Implementing type_fixes: Fix 3 type errors
ℹ️ Type fixes would require manual intervention

🧪 Running verification tests...
✅ All tests passed!
✅ Linting passed!
✅ Formatting check passed!

✅ All fixes implemented and verified!
```

## Error Handling

The command includes comprehensive error handling:

- **No PR detected**: Prompts user to ensure they're on a feature branch
- **GitHub CLI not available**: Provides installation instructions
- **Log download failures**: Continues with available logs
- **Fix implementation failures**: Logs errors and continues
- **Verification timeouts**: Handles long-running tests gracefully
- **User interruption**: Cleanly handles Ctrl+C

## Security Considerations

- Only reads log files, doesn't execute arbitrary code from logs
- Uses subprocess with explicit command arrays (not shell=True)
- Validates and sanitizes file paths
- Respects existing git and GitHub authentication

## Configuration

The command respects existing project configuration:
- `pyproject.toml` for test and linting settings
- `requirements*.txt` for dependencies
- `.github/workflows/` for CI job definitions
- `.flake8`, `mypy.ini` for tool-specific settings

## Future Enhancements

Potential improvements that could be added:

1. **More Automated Fixes**:
   - Automatic import fixing with `isort`
   - Type annotation suggestions with AI assistance
   - Dependency conflict resolution

2. **Better Analysis**:
   - Pattern recognition for common failure modes
   - Historical failure analysis
   - Performance regression detection

3. **Integration**:
   - Direct integration with CI systems
   - Automatic PR comments with fix suggestions
   - Web dashboard for CI monitoring

4. **Reporting**:
   - Detailed fix reports
   - Success/failure metrics
   - Time tracking for fix process
