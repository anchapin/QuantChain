#!/usr/bin/env python3
"""
Test runner with resource monitoring for QuantChain.
This script runs tests while monitoring system resources.
"""

import os
import sys
import subprocess
import json
from datetime import datetime
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from scripts.monitor_resources import monitor_resources


def run_command_with_monitoring(command, output_file=None):
    """Run a command while monitoring resources."""
    print(f"Running command: {' '.join(command)}")
    
    # Monitor before execution
    print("\n=== BEFORE EXECUTION ===")
    before_stats = monitor_resources(output_file)
    
    # Run the command
    start_time = datetime.now()
    try:
        result = subprocess.run(command, check=True)
        success = True
        return_code = result.returncode
    except subprocess.CalledProcessError as e:
        success = False
        return_code = e.returncode
    end_time = datetime.now()
    
    # Monitor after execution
    print("\n=== AFTER EXECUTION ===")
    after_stats = monitor_resources(output_file)
    
    # Calculate resource changes
    disk_change = after_stats['disk']['used_gb'] - before_stats['disk']['used_gb']
    memory_peak = after_stats['memory']['percent']
    
    # Print summary
    duration = (end_time - start_time).total_seconds()
    print(f"\n=== EXECUTION SUMMARY ===")
    print(f"Duration: {duration:.2f} seconds")
    print(f"Exit Code: {return_code}")
    print(f"Disk Change: {disk_change:+.2f} GB")
    print(f"Peak Memory Usage: {memory_peak}%")
    if before_stats['pip_cache_mb'] and after_stats['pip_cache_mb']:
        cache_change = after_stats['pip_cache_mb'] - before_stats['pip_cache_mb']
        print(f"Pip Cache Change: {cache_change:+.2f} MB")
    
    return success, return_code


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Run tests with resource monitoring"
    )
    parser.add_argument(
        "--type",
        choices=["unit", "ml", "integration", "all"],
        default="unit",
        help="Type of tests to run"
    )
    parser.add_argument(
        "--python-version",
        default="python3",
        help="Python executable to use"
    )
    parser.add_argument(
        "--coverage",
        action="store_true",
        help="Enable coverage reporting"
    )
    parser.add_argument(
        "--output",
        help="Output file for resource monitoring logs",
        default="logs/resource_monitor.jsonl"
    )
    
    args = parser.parse_args()
    
    # Create logs directory if it doesn't exist
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    
    # Prepare test command based on type
    base_cmd = [
        args.python_version, "-m", "pytest", "tests/unit", "-v"
    ]
    
    if args.coverage:
        base_cmd.extend([
            "--cov=quantchain",
            "--cov-report=term-missing",
            "--cov-report=html",
            "--cov-report=xml",
            "--cov-fail-under=80"
        ])
    
    if args.type == "unit":
        # Run non-ML, non-slow tests
        test_cmd = base_cmd + ["-m", "not requires_ml and not slow"]
        test_name = "Unit Tests (Non-ML)"
    elif args.type == "ml":
        # Run ML-dependent and slow tests
        test_cmd = base_cmd + ["-m", "requires_ml or slow"]
        test_name = "ML Tests"
    elif args.type == "integration":
        # Run integration tests
        test_cmd = [
            args.python_version, "-m", "pytest", "-m",
            "integration and not slow", "-v"
        ]
        if args.coverage:
            test_cmd.extend([
                "--cov=quantchain",
                "--cov-report=term-missing",
                "--cov-report=html",
                "--cov-report=xml",
                "--cov-fail-under=80"
            ])
        test_name = "Integration Tests"
    else:  # all
        # Run all tests
        test_cmd = base_cmd
        test_name = "All Tests"
    
    # Create a timestamped output file for this run
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"logs/resource_monitor_{test_name.lower().replace(' ', '_')}_{timestamp}.jsonl"
    
    print(f"=== {test_name.upper()} WITH RESOURCE MONITORING ===")
    
    # Run tests with monitoring
    success, return_code = run_command_with_monitoring(test_cmd, output_file)
    
    # Exit with appropriate code
    sys.exit(return_code if not success else 0)


if __name__ == "__main__":
    main()
