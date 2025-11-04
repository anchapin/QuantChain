"""
Root pytest configuration for QuantChain.
"""

from typing import Any

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
