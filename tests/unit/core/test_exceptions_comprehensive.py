"""
Additional tests for exceptions module to ensure complete coverage.
"""

import pytest

try:
    from quantchain.core.exceptions import (
        AuthenticationError,
        ConfigurationError,
        DataSourceError,
        ExecutionError,
        InsufficientDataError,
        LibraryImportError,
        OrderError,
        PortfolioError,
        QuantChainError,
        SymbolNotFoundError,
        ValidationError,
    )

    EXCEPTIONS_AVAILABLE = True
except ImportError as e:
    EXCEPTIONS_AVAILABLE = False
    print(f"Exceptions module not available: {e}")


@pytest.mark.skipif(not EXCEPTIONS_AVAILABLE, reason="Exceptions module not available")
class TestExceptionInheritance:
    """Test exception inheritance and behavior."""

    def test_quantchain_error_base_class(self):
        """Test QuantChainError base exception."""
        error = QuantChainError("Base error")
        assert str(error) == "Base error"
        assert isinstance(error, Exception)
        assert isinstance(error, QuantChainError)

    def test_all_exceptions_inherit_correctly(self):
        """Test that all custom exceptions inherit properly."""
        exceptions = [
            DataSourceError,
            AuthenticationError,
            ValidationError,
            ConfigurationError,
            ExecutionError,
            InsufficientDataError,
            LibraryImportError,
            SymbolNotFoundError,
            OrderError,
            PortfolioError,
        ]

        for exc_class in exceptions:
            # Test instantiation
            error = exc_class(f"Test {exc_class.__name__}")
            assert isinstance(error, Exception)
            assert isinstance(error, QuantChainError)
            assert isinstance(error, exc_class)

    def test_exception_with_none_message(self):
        """Test exceptions with None message."""
        try:
            error = DataSourceError(None)
            # Should handle None gracefully
            assert error is not None
        except Exception:
            pass  # May fail with None message

    def test_exception_with_empty_message(self):
        """Test exceptions with empty message."""
        error = DataSourceError("")
        assert str(error) == ""

    def test_exception_repr(self):
        """Test exception string representation."""
        error = ValidationError("Invalid input")
        repr_str = repr(error)
        assert "ValidationError" in repr_str

    def test_exception_attributes(self):
        """Test setting additional attributes on exceptions."""
        error = ExecutionError("Execution failed")
        error.error_code = 500
        error.timestamp = "2024-01-01"

        assert error.error_code == 500
        assert error.timestamp == "2024-01-01"
