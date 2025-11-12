#!/usr/bin/env python3
"""Test script to verify all key dependencies are working."""


def test_dependencies():
    """Test that all required dependencies can be imported."""
    dependencies = [
        "yaml",
        "pandas",
        "requests",
        "gymnasium",
        "alpaca",
        "ccxt",
        "polygon",
        "langgraph",
        "openai",
        "anthropic",
        "pytest",
        "pytest_cov",
    ]

    missing = []
    for dep in dependencies:
        try:
            __import__(dep)
            print(f"OK {dep}")
        except ImportError as e:
            print(f"FAIL {dep}: {e}")
            missing.append(dep)

    if missing:
        print(f"\nFAIL Missing dependencies: {missing}")
        return False
    else:
        print("\nOK All key dependencies installed successfully!")
        return True


if __name__ == "__main__":
    test_dependencies()
