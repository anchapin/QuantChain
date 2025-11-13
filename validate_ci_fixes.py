#!/usr/bin/env python3
"""
Validation script for QuantChain CI fixes
Tests dependency handling, optional imports, and basic functionality.
"""

import sys
import os
import logging
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def test_dependency_manager():
    """Test dependency manager functionality."""
    logger.info("=== Testing Dependency Manager ===")

    try:
        from quantchain.core.dependency_manager import get_dependency_manager

        manager = get_dependency_manager()
        status = manager.get_status()

        logger.info(f"Dependency status: {status}")

        # Test availability checks
        has_plotly = manager.is_available("plotly")
        has_streamlit = manager.is_available("streamlit")
        has_torch = manager.is_available("torch")

        logger.info(f"Plotly available: {has_plotly}")
        logger.info(f"Streamlit available: {has_streamlit}")
        logger.info(f"Torch available: {has_torch}")

        return True

    except Exception as e:
        logger.error(f"Dependency manager test failed: {e}")
        return False


def test_core_imports():
    """Test core module imports."""
    logger.info("=== Testing Core Imports ===")

    try:
        from quantchain.core import (
            Config,
            QuantChainError,
            get_dependency_manager,
            has_plotly,
            has_streamlit,
            has_torch,
        )

        logger.info("✓ Core imports successful")

        # Test basic functionality
        config = Config()
        logger.info(f"✓ Config created: {config}")

        # Test dependency status
        dep_status = get_dependency_manager().get_status()
        logger.info(f"✓ Dependency status retrieved")

        return True

    except Exception as e:
        logger.error(f"Core imports test failed: {e}")
        return False


def test_optional_imports():
    """Test optional import handling."""
    logger.info("=== Testing Optional Imports ===")

    try:
        # Test web dashboard imports
        try:
            from quantchain.tools.web_dashboard import create_dashboard

            logger.info("✓ Web dashboard import successful")
        except ImportError as e:
            logger.warning(f"Web dashboard import failed (expected): {e}")

        # Test dependency handling
        from quantchain.core.dependency_manager import import_plotly, import_streamlit

        go, px, make_subplots = import_plotly()
        st, html = import_streamlit()

        if go is not None:
            logger.info("✓ Plotly import successful")
        else:
            logger.warning("✗ Plotly not available (expected in CI)")

        if st is not None:
            logger.info("✓ Streamlit import successful")
        else:
            logger.warning("✗ Streamlit not available (expected in CI)")

        return True

    except Exception as e:
        logger.error(f"Optional imports test failed: {e}")
        return False


def test_setup_py():
    """Test setup.py configuration."""
    logger.info("=== Testing Setup Configuration ===")

    try:
        import setup

        logger.info("✓ Setup module import successful")

        # Test that setup defines required variables
        if hasattr(setup, "VERSION"):
            logger.info(f"✓ Version defined: {setup.VERSION}")
        else:
            logger.warning("✗ Version not defined in setup")

        if hasattr(setup, "CORE_REQUIREMENTS"):
            logger.info(
                f"✓ Core requirements defined ({len(setup.CORE_REQUIREMENTS)} packages)"
            )
        else:
            logger.warning("✗ Core requirements not defined")

        return True

    except Exception as e:
        logger.error(f"Setup.py test failed: {e}")
        return False


def test_requirements_files():
    """Test that requirements files exist and are valid."""
    logger.info("=== Testing Requirements Files ===")

    requirements_files = [
        "requirements.txt",
        "requirements-dev.txt",
        "requirements-ci.txt",
        "requirements-ml.txt",
    ]

    success = True
    for req_file in requirements_files:
        file_path = Path(req_file)
        if file_path.exists():
            try:
                with open(file_path, "r") as f:
                    content = f.read()
                lines = [
                    line.strip()
                    for line in content.split("\n")
                    if line.strip() and not line.strip().startswith("#")
                ]
                logger.info(f"✓ {req_file}: {len(lines)} dependencies")
            except Exception as e:
                logger.error(f"✗ {req_file}: Failed to read - {e}")
                success = False
        else:
            logger.warning(f"✗ {req_file}: File not found")
            success = False

    return success


def test_pytest_configuration():
    """Test pytest configuration."""
    logger.info("=== Testing Pytest Configuration ===")

    pytest_config = Path("pytest.ini")
    if pytest_config.exists():
        try:
            with open(pytest_config, "r") as f:
                content = f.read()
            logger.info("✓ pytest.ini exists")

            # Check for custom markers
            if "requires_plotly" in content:
                logger.info("✓ Custom markers found")
            else:
                logger.warning("✗ Custom markers not found")

            return True
        except Exception as e:
            logger.error(f"✗ Failed to read pytest.ini: {e}")
            return False
    else:
        logger.warning("✗ pytest.ini not found")
        return False


def run_all_tests():
    """Run all validation tests."""
    logger.info("Starting QuantChain CI validation tests...")

    tests = [
        ("Dependency Manager", test_dependency_manager),
        ("Core Imports", test_core_imports),
        ("Optional Imports", test_optional_imports),
        ("Setup Configuration", test_setup_py),
        ("Requirements Files", test_requirements_files),
        ("Pytest Configuration", test_pytest_configuration),
    ]

    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            logger.error(f"Test {test_name} crashed: {e}")
            results.append((test_name, False))

    # Print summary
    logger.info("=== Test Summary ===")
    passed = 0
    total = len(results)

    for test_name, result in results:
        status = "✓ PASSED" if result else "✗ FAILED"
        logger.info(f"{test_name}: {status}")
        if result:
            passed += 1

    logger.info(f"Overall: {passed}/{total} tests passed")

    if passed == total:
        logger.info("🎉 All validation tests passed!")
        return True
    else:
        logger.warning(f"⚠️ {total - passed} tests failed")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
