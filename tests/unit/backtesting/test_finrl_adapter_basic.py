"""Basic tests for FinRL adapter imports and exception classes."""

import pytest

try:
    from quantchain.backtesting.finrl_adapter import (
        FinRLAdapterError,
        FinRLConnectionError,
        FinRLDataError,
        GYMNASIUM_AVAILABLE,
        get_connector,
    )
    FINRL_ADAPTER_AVAILABLE = True
except ImportError as e:
    FINRL_ADAPTER_AVAILABLE = False
    print(f"Import error: {e}")

pytestmark = pytest.mark.skipif(
    not FINRL_ADAPTER_AVAILABLE, reason="FinRL adapter not available"
)


@pytest.mark.unit
class TestFinRLAdapterBasic:
    """Basic tests for FinRL adapter imports and constants."""

    def test_gymnasium_availability_constant(self):
        """Test GYMNASIUM_AVAILABLE constant is defined."""
        assert isinstance(GYMNASIUM_AVAILABLE, bool)

    def test_finrl_adapter_error_creation(self):
        """Test FinRLAdapterError creation."""
        error = FinRLAdapterError("Test error")
        assert str(error) == "Test error"

    def test_finrl_connection_error_creation(self):
        """Test FinRLConnectionError creation."""
        error = FinRLConnectionError("Connection failed")
        assert str(error) == "Connection failed"

    def test_finrl_data_error_creation(self):
        """Test FinRLDataError creation."""
        error = FinRLDataError("Data error")
        assert str(error) == "Data error"

    def test_error_inheritance(self):
        """Test error inheritance."""
        assert issubclass(FinRLConnectionError, FinRLAdapterError)
        assert issubclass(FinRLDataError, FinRLAdapterError)

    def test_get_connector_function_exists(self):
        """Test get_connector function exists."""
        assert callable(get_connector)

    def test_module_metadata(self):
        """Test module has required exports."""
        from quantchain.backtesting import finrl_adapter
        # Check that key classes are available
        assert hasattr(finrl_adapter, 'FinRLAdapter')
        assert hasattr(finrl_adapter, 'get_connector')
        assert hasattr(finrl_adapter, 'GYMNASIUM_AVAILABLE')
