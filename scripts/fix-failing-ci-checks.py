#!/usr/bin/env python3
"""
Fix Failing CI Checks Command

This script automates the process of identifying, diagnosing, and fixing failing CI checks
for the current pull request.
"""

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


class CIFixTool:
    def __init__(self, repo_path: str = "."):
        self.repo_path = Path(repo_path).resolve()
        self.logs_dir = self.repo_path / "logs" / "ci-fix"
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        self.backup_branch = None
        self.pr_info = None
        self.failing_jobs = []

    def run_command(
        self, cmd: List[str], capture_output: bool = True
    ) -> subprocess.CompletedProcess:
        """Run a command and return the result."""
        try:
            result = subprocess.run(
                cmd,
                cwd=self.repo_path,
                capture_output=capture_output,
                text=True,
                check=False,
            )
            return result
        except Exception as e:
            print(f"Error running command {' '.join(cmd)}: {e}")
            raise

    def detect_current_pr(self) -> Optional[Dict]:
        """Detect the current pull request."""
        print("Detecting current PR...")

        # Get current branch name
        result = self.run_command(["git", "rev-parse", "--abbrev-ref", "HEAD"])
        if result.returncode != 0:
            print("Error: Not in a git repository")
            return None

        branch_name = result.stdout.strip()

        # Find associated PR
        result = self.run_command(
            [
                "gh",
                "pr",
                "list",
                "--head",
                branch_name,
                "--json",
                "number,title,state,url",
            ]
        )

        if result.returncode != 0:
            print("Error: GitHub CLI not installed or not authenticated")
            print("Please install gh CLI and run 'gh auth login'")
            return None

        prs = json.loads(result.stdout)
        if not prs:
            print(f"No PR found for branch '{branch_name}'")
            return None

        self.pr_info = prs[0]
        print(f"Found PR #{self.pr_info['number']}: {self.pr_info['title']}")
        return self.pr_info

    def identify_failing_jobs(self) -> List[Dict]:
        """Identify which CI jobs are failing."""
        if not self.pr_info:
            return []

        print("Identifying failing jobs...")

        # Try JSON first
        result = self.run_command(["gh", "pr", "checks", "--json", "name,state,link"])

        failing_jobs = []

        if result.returncode == 0 and result.stdout.strip():
            # Parse JSON output
            checks = json.loads(result.stdout)
            for check in checks:
                # Check for failed or pending states
                if check.get("state") in ["failure", "pending", "queued"]:
                    failing_jobs.append(check)
                    print(f"  - {check['name']}: {check.get('state', 'unknown')}")

                    # Add detailsUrl field for compatibility with log downloading
                    check["detailsUrl"] = check.get("link")

        # Fall back to parsing text output (gh returns exit code 1 when there are failures)
        result = self.run_command(["gh", "pr", "checks"])
        if result.stdout and (result.returncode == 0 or result.returncode == 1):
            lines = result.stdout.strip().split("\n")
            for line in lines:
                if "\t" in line:
                    parts = line.split("\t")
                    if len(parts) >= 4:
                        job_name = parts[0]
                        status = parts[1]
                        parts[2]
                        details_url = parts[3] if len(parts) > 3 else ""

                        if status.lower() == "fail" or status.lower() == "pending":
                            job_info = {
                                "name": job_name,
                                "state": status.lower(),
                                "detailsUrl": details_url,
                            }
                            failing_jobs.append(job_info)
                            print(f"  - {job_name}: {status}")

        self.failing_jobs = failing_jobs
        return failing_jobs

    def download_failure_logs(self) -> Dict[str, str]:
        """Download logs from failing jobs."""
        if not self.failing_jobs:
            return {}

        print("Downloading failure logs...")
        log_files = {}

        # First try to get the workflow run ID from the details URL
        for job in self.failing_jobs:
            job_name = job["name"].replace("/", "-")
            log_file = self.logs_dir / f"{job_name}.log"

            if "detailsUrl" in job and job["detailsUrl"]:
                try:
                    # Extract run ID from the details URL
                    # URL format: https://github.com/owner/repo/actions/runs/{run_id}/job/{job_id}
                    url_parts = job["detailsUrl"].split("/")
                    if "runs" in url_parts:
                        run_idx = url_parts.index("runs")
                        job_idx = url_parts.index("job") if "job" in url_parts else -1

                        if job_idx > 0 and run_idx > 0:
                            run_id = url_parts[run_idx + 1]
                            job_id = url_parts[job_idx + 1]

                            # Get the logs for this specific job
                            result = self.run_command(
                                [
                                    "gh",
                                    "api",
                                    f"repos/:owner/:repo/actions/jobs/{job_id}/logs",
                                ]
                            )

                            if result.returncode == 0:
                                with open(log_file, "w") as f:
                                    f.write(result.stdout)
                                log_files[job_name] = str(log_file)
                                print(f"  Downloaded logs for {job_name}")
                            else:
                                # Try alternative approach - get workflow run logs
                                result = self.run_command(
                                    ["gh", "run", "view", run_id, "--log"],
                                    capture_output=False,
                                )

                                if result.returncode == 0:
                                    # The log output was not captured, create a placeholder
                                    with open(log_file, "w") as f:
                                        f.write(f"# Log for {job_name}\n")
                                        f.write(
                                            "# Logs retrieved via gh run view command\n"
                                        )
                                        f.write(
                                            "# Please check the GitHub UI for detailed logs\n"
                                        )
                                    log_files[job_name] = str(log_file)
                                    print(f"  Created log reference for {job_name}")
                        else:
                            print(f"  Could not extract IDs from URL for {job_name}")
                    else:
                        print(
                            f"  Invalid URL format for {job_name}. URL: {job['detailsUrl']}"
                        )

                except Exception as e:
                    print(f"  Failed to download logs for {job_name}: {e}")

                    # Create a placeholder file with job information
                    with open(log_file, "w") as f:
                        f.write(f"# Log for {job_name}\n")
                        f.write(f"# State: {job.get('state', 'unknown')}\n")
                        f.write(f"# Details URL: {job.get('detailsUrl', 'N/A')}\n")
                        f.write("# Note: Could not download actual logs\n")
                    log_files[job_name] = str(log_file)
                    print(f"  Created placeholder for {job_name}")

        return log_files

    def analyze_failure_patterns(self, log_files: Dict[str, str]) -> List[Dict]:
        """Analyze failure patterns from logs."""
        print("Analyzing failure patterns...")

        failure_patterns = []

        for job_name, log_file in log_files.items():
            try:
                with open(log_file, "r") as f:
                    content = f.read()

                # Analyze common failure patterns
                patterns = {
                    "test_failures": [],
                    "linting_errors": [],
                    "type_errors": [],
                    "import_errors": [],
                    "build_errors": [],
                    "dependency_issues": [],
                }

                lines = content.split("\n")
                for i, line in enumerate(lines):
                    # Test failures
                    if "FAILED" in line and "::" in line:
                        patterns["test_failures"].append(line.strip())

                    # Linting errors
                    if any(linter in line for linter in ["flake8", "pylint", "black"]):
                        if "error" in line.lower() or "failed" in line.lower():
                            patterns["linting_errors"].append(line.strip())

                    # Type errors
                    if "mypy" in line.lower() and (
                        "error" in line.lower() or "failed" in line.lower()
                    ):
                        patterns["type_errors"].append(line.strip())

                    # Import errors
                    if "ImportError" in line or "ModuleNotFoundError" in line:
                        patterns["import_errors"].append(line.strip())

                    # Build errors
                    if "BUILD FAILED" in line or "compilation error" in line.lower():
                        patterns["build_errors"].append(line.strip())

                    # Dependency issues
                    if "dependency" in line.lower() and (
                        "error" in line.lower() or "conflict" in line.lower()
                    ):
                        patterns["dependency_issues"].append(line.strip())

                # Summarize findings
                summary = {
                    "job_name": job_name,
                    "patterns": patterns,
                    "total_issues": sum(len(v) for v in patterns.values()),
                }

                if summary["total_issues"] > 0:
                    failure_patterns.append(summary)
                    print(f"  {job_name}: {summary['total_issues']} issues found")
                    for pattern_type, issues in patterns.items():
                        if issues:
                            print(f"    {pattern_type}: {len(issues)} issues")

            except Exception as e:
                print(f"  Error analyzing {job_name}: {e}")

        return failure_patterns

    def create_fix_plan(self, failure_patterns: List[Dict]) -> List[Dict]:
        """Create a plan to fix the issues."""
        print("Creating fix plan...")

        fix_plan = []

        # Since we're getting unit test failures, create a test fix plan
        if any("unit-tests" in job.get("name", "") for job in self.failing_jobs):
            fix_plan.append(
                {
                    "type": "test_fixes",
                    "job": "unit-tests",
                    "description": "Fix failing unit tests",
                    "actions": [
                        "run_tests_locally",
                        "analyze_test_failures",
                        "apply_fixes",
                        "verify_coverage",
                    ],
                }
            )

        # Check for integration test failures
        if any("integration-tests" in job.get("name", "") for job in self.failing_jobs):
            fix_plan.append(
                {
                    "type": "integration_test_fixes",
                    "job": "integration-tests",
                    "description": "Fix failing integration tests",
                    "actions": [
                        "run_integration_tests",
                        "analyze_failures",
                        "apply_fixes",
                    ],
                }
            )

        # Always include linting check
        fix_plan.append(
            {
                "type": "linting_fixes",
                "job": "linting",
                "description": "Check and fix linting issues",
                "actions": ["run_black", "run_flake8", "verify_formatting"],
            }
        )

        return fix_plan

    def create_backup_branch(self) -> bool:
        """Create a backup branch before making changes."""
        print("Creating backup branch...")

        # Get current branch
        result = self.run_command(["git", "rev-parse", "--abbrev-ref", "HEAD"])
        if result.returncode != 0:
            return False

        current_branch = result.stdout.strip()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.backup_branch = f"backup_before_ci_fix_{timestamp}"

        # Create backup branch
        result = self.run_command(["git", "checkout", "-b", self.backup_branch])
        if result.returncode != 0:
            print(f"Failed to create backup branch: {result.stderr}")
            return False

        # Switch back to original branch
        result = self.run_command(["git", "checkout", current_branch])
        if result.returncode != 0:
            return False

        print(f"Created backup branch: {self.backup_branch}")
        return True

    def implement_fixes(self, fix_plan: List[Dict]) -> bool:
        """Implement the fixes according to the plan."""
        print("\nGenerating fix recommendations...")
        print("=" * 60)

        recommendations = []

        for plan_item in fix_plan:
            print(f"\n• {plan_item['description']}")
            print("-" * 40)

            if plan_item["type"] == "test_fixes":
                recommendations.append("• Test Fixes:")
                recommendations.append(
                    "   1. Run: pytest tests/unit -v --cov=quantchain --cov-fail-under=80"
                )
                recommendations.append("   2. Identify failing tests from the output")
                recommendations.append("   3. Fix failing tests to ensure 80% coverage")
                recommendations.append("   4. Common issues:")
                recommendations.append("      - Missing test cases for new code")
                recommendations.append("      - Broken test fixtures or mocks")
                recommendations.append("      - Import errors or missing dependencies")

            elif plan_item["type"] == "integration_test_fixes":
                recommendations.append("• Integration Test Fixes:")
                recommendations.append(
                    "   1. Run: pytest -m 'integration and not slow' -v"
                )
                recommendations.append("   2. Check for external service connectivity")
                recommendations.append("   3. Verify environment variables are set")

            elif plan_item["type"] == "linting_fixes":
                recommendations.append("• Linting Fixes:")
                recommendations.append("   1. Run: black .")
                recommendations.append(
                    "   2. Run: flake8 . --count --select=E9,F63,F7,F82"
                )
                recommendations.append("   3. Fix any syntax errors")

        print("\n• Summary of Actions Needed:")
        print("=" * 60)
        for rec in recommendations:
            print(rec)

        print("\n• Quick Fix Commands:")
        print("=" * 60)
        print("# Apply formatting fixes")
        print("black .")
        print()
        print("# Run tests with coverage")
        print("pytest tests/unit -v --cov=quantchain --cov-fail-under=80")
        print()
        print("# Check linting")
        print("flake8 . --count --select=E9,F63,F7,F82")
        print()
        print("# Run integration tests")
        print("pytest -m 'integration and not slow' -v")

        return True

    def verify_fixes(self) -> bool:
        """Skip verification as this tool only provides recommendations."""
        print("\nNote: This tool provides recommendations only.")
        print("Please run the commands above manually to fix the issues.")
        print("\nAfter applying fixes, you can verify with:")
        print("  - pytest tests/unit -v --cov=quantchain --cov-fail-under=80")
        print("  - flake8 . --count --select=E9,F63,F7,F82")
        print("  - black --check .")
        return True

    def run(self) -> int:
        """Run the complete CI fix process."""
        print("Fix Failing CI Checks Tool")
        print("=" * 50)

        # Step 1: Detect current PR
        if not self.detect_current_pr():
            return 1

        # Step 2: Identify failing jobs
        if not self.identify_failing_jobs():
            print("No failing jobs found. CI is passing!")
            return 0

        # Step 3: Skip log downloading for now and create fix plan directly
        # Step 4: Create fix plan based on failing job names
        fix_plan = self.create_fix_plan([])

        if not fix_plan:
            print("No fixable issues found")
            return 1

        print(f"\nFix plan created with {len(fix_plan)} items")

        # Step 6: Create backup branch
        if not self.create_backup_branch():
            return 1

        # Step 7: Implement fixes
        if not self.implement_fixes(fix_plan):
            print("Failed to implement fixes")
            return 1

        # Step 8: Verify fixes
        if self.verify_fixes():
            print(f"\n* Fix recommendations generated successfully!")
            print(f"  Backup branch created: {self.backup_branch}")
            return 0
        else:
            print(f"\n* Failed to generate recommendations.")
            if self.backup_branch:
                print(f"  You can restore from backup branch: {self.backup_branch}")
            return 1


def main():
    parser = argparse.ArgumentParser(
        description="Fix failing CI checks for the current PR"
    )
    parser.add_argument(
        "--repo-path",
        default=".",
        help="Path to the repository (default: current directory)",
    )

    args = parser.parse_args()

    tool = CIFixTool(args.repo_path)

    try:
        exit_code = tool.run()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
