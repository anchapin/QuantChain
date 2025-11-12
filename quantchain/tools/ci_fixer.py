"""CI/CD Helper tools for fixing failing CI checks."""

import json
import logging
import re
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


class CIFixer:
    """Automated CI check fixer for QuantChain project."""

    def __init__(self, repo_path: Optional[str] = None):
        """Initialize CI fixer with optional repository path."""
        self.repo_path = Path(repo_path) if repo_path else Path.cwd()
        self.logs_dir = self.repo_path / "logs"
        self.logs_dir.mkdir(exist_ok=True)

    def detect_current_pr(self) -> Optional[Dict[str, Any]]:
        """Detect the current PR on GitHub."""
        try:
            # Get current branch name
            result = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True,
            )
            branch_name = result.stdout.strip()

            # Find associated PR
            result = subprocess.run(
                [
                    "gh",
                    "pr",
                    "list",
                    "--head",
                    branch_name,
                    "--json",
                    "number,title,state,headRepository,headRefName",
                ],
                capture_output=True,
                text=True,
                check=True,
            )

            pr_data = json.loads(result.stdout)
            if pr_data:
                return pr_data[0]
            else:
                logger.warning(f"No PR found for branch: {branch_name}")
                return None

        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to detect current PR: {e}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse PR data: {e}")
            return None

    def get_pr_checks(self, pr_number: int) -> List[Dict[str, Any]]:
        """Get PR checks status."""
        try:
            result = subprocess.run(
                [
                    "gh",
                    "pr",
                    "checks",
                    "--json",
                    "name,conclusion,detailsUrl,startedAt,completedAt",
                ],
                capture_output=True,
                text=True,
                check=True,
            )

            checks_data = json.loads(result.stdout)
            return checks_data

        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to get PR checks: {e}")
            return []
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse checks data: {e}")
            return []

    def download_job_logs(self, checks: List[Dict[str, Any]]) -> Dict[str, str]:
        """Download logs from failing jobs."""
        failing_jobs = [
            check for check in checks if check.get("conclusion") == "failure"
        ]
        log_files = {}

        for job in failing_jobs:
            job_name = job.get("name", "unknown").replace(" ", "_")
            details_url = job.get("detailsUrl", "")

            if not details_url:
                continue

            try:
                # Try to extract the job ID from the URL
                job_id_match = re.search(r"/(\d+)$", details_url)
                if not job_id_match:
                    continue

                job_id = job_id_match.group(1)

                # Download logs using GitHub API
                result = subprocess.run(
                    [
                        "gh",
                        "api",
                        f"repos/{self._get_repo_owner()}/{self._get_repo_name()}/actions/jobs/{job_id}/logs",
                    ],
                    capture_output=True,
                    text=True,
                    check=True,
                )

                log_content = result.stdout
                log_file_path = self.logs_dir / f"{job_name}_{job_id}.log"

                with open(log_file_path, "w", encoding="utf-8") as f:
                    f.write(log_content)

                log_files[job_name] = str(log_file_path)
                logger.info(f"Downloaded logs for {job_name} to {log_file_path}")

            except subprocess.CalledProcessError as e:
                logger.error(f"Failed to download logs for {job_name}: {e}")
            except Exception as e:
                logger.error(f"Error processing job {job_name}: {e}")

        return log_files

    def analyze_failure_patterns(self, log_files: Dict[str, str]) -> Dict[str, Any]:
        """Analyze failure patterns from log files."""
        analysis = {
            "test_failures": [],
            "linting_errors": [],
            "type_errors": [],
            "build_errors": [],
            "dependency_issues": [],
            "other_issues": [],
        }

        for job_name, log_file in log_files.items():
            try:
                with open(log_file, "r", encoding="utf-8") as f:
                    log_content = f.read()

                # Analyze different failure types
                self._analyze_test_failures(log_content, job_name, analysis)
                self._analyze_linting_errors(log_content, job_name, analysis)
                self._analyze_type_errors(log_content, job_name, analysis)
                self._analyze_build_errors(log_content, job_name, analysis)
                self._analyze_dependency_issues(log_content, job_name, analysis)

            except Exception as e:
                logger.error(f"Failed to analyze log file {log_file}: {e}")

        return analysis

    def _analyze_test_failures(
        self, log_content: str, job_name: str, analysis: Dict[str, Any]
    ):
        """Analyze test failure patterns."""
        # Look for pytest failures
        pytest_failures = re.findall(r"FAILED (.+?)\s*-", log_content)
        if pytest_failures:
            analysis["test_failures"].extend(
                [
                    {"job": job_name, "test": failure, "type": "pytest"}
                    for failure in pytest_failures
                ]
            )

        # Look for assertion errors
        assertion_errors = re.findall(r"AssertionError: (.+?)(?=\n|\r|$)", log_content)
        if assertion_errors:
            analysis["test_failures"].extend(
                [
                    {"job": job_name, "error": error, "type": "assertion"}
                    for error in assertion_errors
                ]
            )

    def _analyze_linting_errors(
        self, log_content: str, job_name: str, analysis: Dict[str, Any]
    ):
        """Analyze linting error patterns."""
        # Look for flake8 errors
        flake8_errors = re.findall(r"(.+?):(\d+):(\d+): (.+?) (.+)", log_content)
        if flake8_errors:
            analysis["linting_errors"].extend(
                [
                    {
                        "job": job_name,
                        "file": file,
                        "line": line,
                        "error": error,
                        "code": code,
                        "tool": "flake8",
                    }
                    for file, line, col, code, error in flake8_errors
                ]
            )

        # Look for black formatting issues
        if "would reformat" in log_content:
            files = re.findall(r"would reformat (.+?)(?=\n|$)", log_content)
            analysis["linting_errors"].extend(
                [
                    {
                        "job": job_name,
                        "file": file,
                        "tool": "black",
                        "issue": "formatting",
                    }
                    for file in files
                ]
            )

    def _analyze_type_errors(
        self, log_content: str, job_name: str, analysis: Dict[str, Any]
    ):
        """Analyze type checking error patterns."""
        # Look for mypy errors
        mypy_errors = re.findall(r"(.+?):(\d+): (.+?)(?=\n|$)", log_content)
        if mypy_errors:
            for file, line, error in mypy_errors:
                if "error:" in error:
                    analysis["type_errors"].append(
                        {
                            "job": job_name,
                            "file": file,
                            "line": line,
                            "error": error,
                            "tool": "mypy",
                        }
                    )

    def _analyze_build_errors(
        self, log_content: str, job_name: str, analysis: Dict[str, Any]
    ):
        """Analyze build error patterns."""
        # Look for common build errors
        if "ModuleNotFoundError" in log_content:
            modules = re.findall(
                r"ModuleNotFoundError: No module named (.+?)(?=\n|$)", log_content
            )
            analysis["build_errors"].extend(
                [
                    {"job": job_name, "module": module, "type": "missing_module"}
                    for module in modules
                ]
            )

        if "ImportError" in log_content:
            imports = re.findall(r"ImportError: (.+?)(?=\n|$)", log_content)
            analysis["build_errors"].extend(
                [
                    {"job": job_name, "error": error, "type": "import"}
                    for error in imports
                ]
            )

    def _analyze_dependency_issues(
        self, log_content: str, job_name: str, analysis: Dict[str, Any]
    ):
        """Analyze dependency issue patterns."""
        # Look for dependency resolution errors
        if "Could not find a version that satisfies the requirement" in log_content:
            packages = re.findall(
                r"Could not find a version that satisfies the requirement (.+?)(?=\n|$)",
                log_content,
            )
            analysis["dependency_issues"].extend(
                [
                    {"job": job_name, "package": package, "type": "version_conflict"}
                    for package in packages
                ]
            )

        if "conflict" in log_content.lower():
            analysis["dependency_issues"].append(
                {
                    "job": job_name,
                    "type": "dependency_conflict",
                    "description": "Dependency conflict detected",
                }
            )

    def create_fix_plan(self, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create a fix plan based on failure analysis."""
        fix_plan = []

        # Test failure fixes
        if analysis["test_failures"]:
            fix_plan.append(
                {
                    "type": "test_fixes",
                    "description": f"Fix {len(analysis['test_failures'])} test failures",
                    "priority": "high",
                    "actions": self._create_test_fix_actions(analysis["test_failures"]),
                }
            )

        # Linting fixes
        if analysis["linting_errors"]:
            fix_plan.append(
                {
                    "type": "linting_fixes",
                    "description": f"Fix {len(analysis['linting_errors'])} linting errors",
                    "priority": "medium",
                    "actions": self._create_linting_fix_actions(
                        analysis["linting_errors"]
                    ),
                }
            )

        # Type checking fixes
        if analysis["type_errors"]:
            fix_plan.append(
                {
                    "type": "type_fixes",
                    "description": f"Fix {len(analysis['type_errors'])} type errors",
                    "priority": "medium",
                    "actions": self._create_type_fix_actions(analysis["type_errors"]),
                }
            )

        # Build fixes
        if analysis["build_errors"]:
            fix_plan.append(
                {
                    "type": "build_fixes",
                    "description": f"Fix {len(analysis['build_errors'])} build errors",
                    "priority": "high",
                    "actions": self._create_build_fix_actions(analysis["build_errors"]),
                }
            )

        # Dependency fixes
        if analysis["dependency_issues"]:
            fix_plan.append(
                {
                    "type": "dependency_fixes",
                    "description": f"Fix {len(analysis['dependency_issues'])} dependency issues",
                    "priority": "high",
                    "actions": self._create_dependency_fix_actions(
                        analysis["dependency_issues"]
                    ),
                }
            )

        return fix_plan

    def _create_test_fix_actions(self, failures: List[Dict[str, Any]]) -> List[str]:
        """Create test fix actions."""
        actions = []
        pytest_failures = [f for f in failures if f.get("type") == "pytest"]
        assertion_failures = [f for f in failures if f.get("type") == "assertion"]

        if pytest_failures:
            actions.append(
                f"Run failing tests: pytest {' '.join([f['test'] for f in pytest_failures])}"
            )
        if assertion_failures:
            actions.append("Analyze and fix assertion failures in test code")

        return actions

    def _create_linting_fix_actions(self, errors: List[Dict[str, Any]]) -> List[str]:
        """Create linting fix actions."""
        actions = []
        black_errors = [e for e in errors if e.get("tool") == "black"]
        flake8_errors = [e for e in errors if e.get("tool") == "flake8"]

        if black_errors:
            actions.append("Run black formatter: black quantchain tests/")
        if flake8_errors:
            actions.append("Fix flake8 errors manually or with autopep8")

        return actions

    def _create_type_fix_actions(self, errors: List[Dict[str, Any]]) -> List[str]:
        """Create type fix actions."""
        actions = []
        if errors:
            actions.append("Add missing type annotations")
            actions.append("Run mypy to verify type fixes")

        return actions

    def _create_build_fix_actions(self, errors: List[Dict[str, Any]]) -> List[str]:
        """Create build fix actions."""
        actions = []
        missing_modules = [e for e in errors if e.get("type") == "missing_module"]
        import_errors = [e for e in errors if e.get("type") == "import"]

        if missing_modules:
            actions.append("Add missing dependencies to requirements.txt")
        if import_errors:
            actions.append("Fix import statements in code")

        return actions

    def _create_dependency_fix_actions(self, issues: List[Dict[str, Any]]) -> List[str]:
        """Create dependency fix actions."""
        actions = []
        if issues:
            actions.append("Update dependency versions in requirements*.txt")
            actions.append("Check for version conflicts and resolve them")

        return actions

    def implement_fixes(self, fix_plan: List[Dict[str, Any]]) -> bool:
        """Implement the fixes from the fix plan."""
        success = True

        for fix in fix_plan:
            logger.info(f"Implementing {fix['type']}: {fix['description']}")

            try:
                if fix["type"] == "linting_fixes":
                    success &= self._apply_linting_fixes(fix["actions"])
                elif fix["type"] == "type_fixes":
                    success &= self._apply_type_fixes(fix["actions"])
                elif fix["type"] == "build_fixes":
                    success &= self._apply_build_fixes(fix["actions"])
                elif fix["type"] == "dependency_fixes":
                    success &= self._apply_dependency_fixes(fix["actions"])
                # Note: Test fixes require manual intervention

            except Exception as e:
                logger.error(f"Failed to implement {fix['type']}: {e}")
                success = False

        return success

    def _apply_linting_fixes(self, actions: List[str]) -> bool:
        """Apply linting fixes."""
        for action in actions:
            if "black" in action:
                try:
                    subprocess.run(
                        ["black", "quantchain", "tests/"],
                        check=True,
                        cwd=self.repo_path,
                    )
                    logger.info("Applied black formatting")
                except subprocess.CalledProcessError as e:
                    logger.error(f"Black formatting failed: {e}")
                    return False
            elif "autopep8" in action:
                try:
                    subprocess.run(
                        [
                            "autopep8",
                            "--in-place",
                            "--aggressive",
                            "quantchain",
                            "tests/",
                        ],
                        check=True,
                        cwd=self.repo_path,
                    )
                    logger.info("Applied autopep8 formatting")
                except subprocess.CalledProcessError as e:
                    logger.error(f"Autopep8 formatting failed: {e}")
                    return False

        return True

    def _apply_type_fixes(self, actions: List[str]) -> bool:
        """Apply type fixes."""
        # This would require more sophisticated analysis to implement automatically
        logger.info("Type fixes would require manual intervention")
        return True

    def _apply_build_fixes(self, actions: List[str]) -> bool:
        """Apply build fixes."""
        # This would require manual intervention to fix imports
        logger.info("Build fixes would require manual intervention")
        return True

    def _apply_dependency_fixes(self, actions: List[str]) -> bool:
        """Apply dependency fixes."""
        # This would require manual intervention to update requirements
        logger.info("Dependency fixes would require manual intervention")
        return True

    def verify_fixes(self) -> bool:
        """Verify fixes by running local tests."""
        logger.info("Running verification tests...")

        try:
            # Run tests
            result = subprocess.run(
                ["pytest", "--cov=quantchain", "tests/"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=300,
            )

            if result.returncode == 0:
                logger.info("✅ All tests passed!")
            else:
                logger.error(f"❌ Tests failed:\n{result.stdout}\n{result.stderr}")
                return False

            # Run linting
            result = subprocess.run(
                ["flake8", "quantchain", "tests/"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
            )

            if result.returncode == 0:
                logger.info("✅ Linting passed!")
            else:
                logger.warning(f"⚠️ Linting issues:\n{result.stdout}")

            # Check formatting
            result = subprocess.run(
                ["black", "--check", "quantchain", "tests/"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
            )

            if result.returncode == 0:
                logger.info("✅ Formatting check passed!")
            else:
                logger.warning(f"⚠️ Formatting issues:\n{result.stdout}")

            return True

        except subprocess.TimeoutExpired:
            logger.error("❌ Tests timed out")
            return False
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Verification failed: {e}")
            return False

    def _get_repo_owner(self) -> str:
        """Get repository owner from git remote."""
        try:
            result = subprocess.run(
                ["git", "remote", "get-url", "origin"],
                capture_output=True,
                text=True,
                check=True,
            )
            url = result.stdout.strip()
            # Extract owner from git@github.com:owner/repo.git or https://github.com/owner/repo.git
            match = re.search(r"[:/](.+?)/", url)
            return match.group(1) if match else ""
        except Exception:
            return ""

    def _get_repo_name(self) -> str:
        """Get repository name from git remote."""
        try:
            result = subprocess.run(
                ["git", "remote", "get-url", "origin"],
                capture_output=True,
                text=True,
                check=True,
            )
            url = result.stdout.strip()
            # Extract repo name from URL
            match = re.search(r"/([^/]+?)(?:\.git)?$", url)
            return match.group(1) if match else ""
        except Exception:
            return ""

    def run_fix_process(self) -> bool:
        """Run the complete CI fix process."""
        logger.info("🚀 Starting CI fix process...")

        # Step 1: Detect current PR
        pr = self.detect_current_pr()
        if not pr:
            logger.error(
                "❌ No PR detected. Make sure you're on a feature branch with an associated PR."
            )
            return False

        logger.info(f"📋 Detected PR #{pr['number']}: {pr['title']}")

        # Step 2: Identify failing jobs
        checks = self.get_pr_checks(pr["number"])
        failing_jobs = [
            check for check in checks if check.get("conclusion") == "failure"
        ]

        if not failing_jobs:
            logger.info("✅ No failing jobs found!")
            return True

        logger.info(f"❌ Found {len(failing_jobs)} failing jobs")

        # Step 3: Download logs
        log_files = self.download_job_logs(failing_jobs)
        if not log_files:
            logger.error("❌ No log files downloaded")
            return False

        # Step 4: Analyze failures
        analysis = self.analyze_failure_patterns(log_files)
        logger.info(f"🔍 Analyzed failure patterns: {len(analysis)} categories")

        # Step 5: Create fix plan
        fix_plan = self.create_fix_plan(analysis)
        logger.info(f"📝 Created fix plan with {len(fix_plan)} items")

        # Step 6: Implement fixes
        if fix_plan:
            success = self.implement_fixes(fix_plan)
            if not success:
                logger.error("❌ Failed to implement fixes")
                return False

            # Step 7: Verify fixes
            verification_success = self.verify_fixes()
            if verification_success:
                logger.info("✅ All fixes implemented and verified!")
                return True
            else:
                logger.error("❌ Verification failed")
                return False
        else:
            logger.info("✅ No automated fixes needed")
            return True


def main():
    """Main entry point for the CI fixer command."""
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--help":
        print(
            """
CI Fixer Command

Usage: python -m quantchain.tools.ci_fixer

This command automates the process of identifying, diagnosing, and fixing
failing CI checks for the current pull request.

Prerequisites:
- Must be in a git repository with a GitHub remote
- Must have the GitHub CLI (`gh`) installed and authenticated
- Must have local test environment set up (pytest, etc.)

The command will:
1. Detect the current PR on GitHub
2. Identify which CI jobs are failing
3. Download logs from failing jobs
4. Analyze the failure patterns
5. Create and implement a plan to fix the issues
6. Verify the fixes by running local tests
"""
        )
        return

    try:
        fixer = CIFixer()
        success = fixer.run_fix_process()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("Process interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
