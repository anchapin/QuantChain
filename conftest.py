"""
Root pytest configuration for QuantChain.
"""

import json
import os
from datetime import datetime
from typing import Any

import psutil

# Pytest configuration
pytest_plugins: list[str] = []


# Test markers


def pytest_configure(config: Any) -> None:
    config.addinivalue_line("markers", "unit: mark test as a unit test")
    config.addinivalue_line("markers", "integration: mark test as an integration test")
    config.addinivalue_line("markers", "slow: mark test as slow running")
    config.addinivalue_line(
        "markers", "requires_backtestingpy: mark test that requires Backtesting.py"
    )
    config.addinivalue_line(
        "markers", "requires_ml: mark test that requires ML dependencies"
    )


def pytest_sessionstart(session: Any) -> None:
    """Log resources at the start of the test session."""
    import os

    if os.getenv("CI") or os.getenv("MONITOR_RESOURCES"):
        log_resources("session_start")


def pytest_sessionfinish(session: Any) -> None:
    """Log resources at the end of the test session."""
    if os.getenv("CI") or os.getenv("MONITOR_RESOURCES"):
        log_resources("session_end")


def pytest_runtest_makereport(item: Any, call: Any) -> None:
    """Log resources after each test if CI is enabled or monitoring is on."""
    if (os.getenv("CI") or os.getenv("MONITOR_RESOURCES")) and call.when == "call":
        log_resources(f"test_{item.name}_after")


def log_resources(context: str) -> None:
    """Log system resources to a JSON file."""
    try:
        # Create logs directory if it doesn't exist
        os.makedirs("logs", exist_ok=True)

        # Get resource statistics
        timestamp = datetime.now().isoformat()
        disk = psutil.disk_usage("/")
        memory = psutil.virtual_memory()

        stats = {
            "context": context,
            "timestamp": timestamp,
            "disk": {
                "total_gb": round(disk.total / (1024**3), 2),
                "used_gb": round(disk.used / (1024**3), 2),
                "free_gb": round(disk.free / (1024**3), 2),
                "percent": disk.percent,
            },
            "memory": {
                "total_gb": round(memory.total / (1024**3), 2),
                "available_gb": round(memory.available / (1024**3), 2),
                "used_gb": round(memory.used / (1024**3), 2),
                "percent": memory.percent,
            },
            "cpu": {
                "percent": psutil.cpu_percent(interval=0.1),
                "count": psutil.cpu_count(),
            },
        }

        # Write to log file
        log_file = "logs/test_resources.jsonl"
        with open(log_file, "a") as f:
            json.dump(stats, f)
            f.write("\n")

    except Exception:
        # Silently ignore errors to not interfere with tests
        pass
