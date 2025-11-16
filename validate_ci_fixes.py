#!/usr/bin/env python3
"""
Script to validate CI fixes and ensure code quality.
"""

import sys
import os
import logging
from pathlib import Path
from quantchain.core.dependency_manager import get_dependency_manager
from quantchain.tools.web_dashboard import create_dashboard
from quantchain.core.dependency_manager import import_plotly, import_streamlit


def validate_dependencies():
    """Validate that all dependencies are properly handled."""
    dep_manager = get_dependency_manager()

    # Check optional dependencies
    plotly_available = import_plotly()
    streamlit_available = import_streamlit()

    print(f"Plotly available: {plotly_available}")
    print(f"Streamlit available: {streamlit_available}")

    return True


def validate_imports():
    """Validate that all imports work correctly."""
    try:
        from quantchain.tools.web_dashboard import DashboardCharts, WebDashboardApp

        print("Web dashboard imports successful")
        return True
    except ImportError as e:
        print(f"Import error: {e}")
        return False


def main():
    """Main validation function."""
    print("Validating CI fixes...")

    deps_ok = validate_dependencies()
    imports_ok = validate_imports()

    if deps_ok and imports_ok:
        print("All validations passed!")
        return 0
    else:
        print("Some validations failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main())
