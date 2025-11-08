# Fix Failing CI Checks

This custom command automates the process of identifying, diagnosing, and fixing failing CI checks for the current pull request.

## Command Name
`fix-failing-ci-checks`

## Description
When CI checks fail for a pull request, this command will:
1. Detect the current PR on GitHub
2. Identify which CI jobs are failing
3. Download logs from failing jobs
4. Analyze the failure patterns
5. Create and implement a plan to fix the issues
6. Verify the fixes by running local tests

## Usage
```
droid fix-failing-ci-checks
```

## Prerequisites
- Must be in a git repository with a GitHub remote
- Must have the GitHub CLI (`gh`) installed and authenticated
- Must have local test environment set up (pytest, etc.)

## Implementation Steps

### 1. Detect Current PR
```bash
# Get current branch name
git rev-parse --abbrev-ref HEAD

# Find associated PR
gh pr list --head $(git rev-parse --abbrev-ref HEAD) --json number,title,state
```

### 2. Identify Failing Jobs
```bash
# Get PR checks status
gh pr checks --json name,conclusion,detailsUrl

# Filter for failed checks
```

### 3. Download Failure Logs
```bash
# For each failing job, download logs
gh api $(detailsUrl) > logs/{job-name}.log
```

### 4. Analyze Failure Patterns
- Parse log files to identify common failure types:
  - Test failures
  - Linting errors
  - Type checking errors
  - Build errors
  - Dependency issues

### 5. Create Fix Plan
Based on failure analysis:
- **Test failures**: Identify failing tests, analyze code changes
- **Linting errors**: Apply automatic fixes where possible
- **Type errors**: Update type annotations
- **Dependency issues**: Update requirements/fix version conflicts

### 6. Implement Fixes
- Apply automated fixes (black, isort, mypy)
- Fix specific test failures
- Update configuration files
- Add missing dependencies

### 7. Verify Fixes
```bash
# Run full test suite
pytest --cov=quantchain tests/

# Run linting
flake8 quantchain tests/
mypy quantchain/

# Check formatting
black --check quantchain tests/
```

## Configuration
The command respects the following configuration files:
- `pyproject.toml` - Test and linting configuration
- `requirements*.txt` - Python dependencies
- `.github/workflows/` - CI job definitions

## Example Output
```
Detected PR #123: "Add new feature"
Found 3 failing jobs:
- test (pytest): 2 tests failing
- lint (flake8): 5 linting errors
- type-check (mypy): 3 type errors

Analyzing failures...
Creating fix plan...

✅ Fixed 2 failing tests in test_new_feature.py
✅ Fixed 5 linting errors using auto-formatters
✅ Fixed 3 type errors by adding type annotations

Running verification tests...
All tests passed! ✓
```

## Error Handling
- If no PR is found, prompts user to create one
- If `gh` CLI is not installed, provides installation instructions
- If fixes cannot be applied automatically, provides manual fix instructions
- Maintains backup of original files before making changes

## Notes
- The command creates a backup branch before applying fixes
- All changes are committed with descriptive commit messages
- If verification fails, rolls back to the backup branch
- Progress is logged throughout the process
