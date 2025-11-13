"""Tests for IB async execution constants and basic imports."""

import pytest

try:
    from quantchain.connectors.ib_async_execution import (
        IBExecutionConnector,
        IB_ASYNC_AVAILABLE,
    )
    IB_EXECUTION_AVAILABLE = True
except ImportError as e:
    IB_EXECUTION_AVAILABLE = False
    print(f"Import error: {e}")

pytestmark = pytest.mark.skipif(
    not IB_EXECUTION_AVAILABLE, reason="IB execution connector not available"
)


@pytest.mark.unit
class TestIBAsyncExecutionConstants:
    """Test constants and basic imports for IB async execution."""

    def test_ib_async_availability_constant(self):
        """Test IB_ASYNC_AVAILABLE constant is defined."""
        assert isinstance(IB_ASYNC_AVAILABLE, bool)

    def test_class_import(self):
        """Test IBExecutionConnector class can be imported."""
        assert IBExecutionConnector is not None

    def test_module_has_required_exports(self):
        """Test module exports required components."""
        from quantchain.connectors import ib_async_execution
        # Check that main class is available
        assert hasattr(ib_async_execution, 'IBExecutionConnector')
        assert hasattr(ib_async_execution, 'IB_ASYNC_AVAILABLE')
