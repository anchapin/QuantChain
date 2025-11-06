"""Tests for QuantChain exceptions."""

import pytest

from quantchain.core.exceptions import (
    QuantChainError,
    DataSourceError,
    AuthenticationError,
    RateLimitError,
    SymbolNotFoundError,
    ConfigurationError,
    ValidationError,
)


@pytest.mark.unit
class TestQuantChainExceptions:
    """Test suite for QuantChain exceptions."""

    def test_quant_chain_error_basic(self) -> None:
        """Test basic QuantChainError functionality."""
        error = QuantChainError("Test error")
        assert str(error) == "Test error"
        assert isinstance(error, Exception)

    def test_data_source_error_inheritance(self) -> None:
        """Test DataSourceError inherits from QuantChainError."""
        error = DataSourceError("Data source error")
        assert isinstance(error, QuantChainError)
        assert str(error) == "Data source error"

    def test_authentication_error_inheritance(self) -> None:
        """Test AuthenticationError inheritance chain."""
        error = AuthenticationError("Auth failed")
        assert isinstance(error, DataSourceError)
        assert isinstance(error, QuantChainError)
        assert str(error) == "Auth failed"

    def test_rate_limit_error_inheritance(self) -> None:
        """Test RateLimitError inheritance chain."""
        error = RateLimitError("Rate limit exceeded")
        assert isinstance(error, DataSourceError)
        assert isinstance(error, QuantChainError)
        assert str(error) == "Rate limit exceeded"

    def test_symbol_not_found_error_inheritance(self) -> None:
        """Test SymbolNotFoundError inherits from ValueError."""
        error = SymbolNotFoundError("Symbol not found")
        assert isinstance(error, ValueError)
        assert str(error) == "Symbol not found"

    def test_configuration_error_inheritance(self) -> None:
        """Test ConfigurationError inherits from QuantChainError."""
        error = ConfigurationError("Invalid config")
        assert isinstance(error, QuantChainError)
        assert str(error) == "Invalid config"

    def test_validation_error_inheritance(self) -> None:
        """Test ValidationError inherits from QuantChainError."""
        error = ValidationError("Validation failed")
        assert isinstance(error, QuantChainError)
        assert str(error) == "Validation failed"

    def test_exception_with_cause(self) -> None:
        """Test exception chaining."""
        original_error = ValueError("Original")
        wrapped_error = DataSourceError("Wrapped")
        wrapped_error.__cause__ = original_error

        assert str(wrapped_error) == "Wrapped"
        assert wrapped_error.__cause__ == original_error

    def test_all_exceptions_are_differentiable(self) -> None:
        """Test that all exception types are differentiable."""
        exceptions = [
            QuantChainError("test"),
            DataSourceError("test"),
            AuthenticationError("test"),
            RateLimitError("test"),
            SymbolNotFoundError("test"),
            ConfigurationError("test"),
            ValidationError("test"),
        ]

        # Each should have a unique type
        types = [type(exc) for exc in exceptions]
        assert len(types) == len(set(types))

    def test_exception_inheritance_chain_completeness(self) -> None:
        """Test the complete inheritance chain for all exceptions."""
        # QuantChainError should only inherit from Exception
        assert issubclass(QuantChainError, Exception)

        # DataSource-based errors should inherit correctly
        assert issubclass(DataSourceError, QuantChainError)
        assert issubclass(AuthenticationError, DataSourceError)
        assert issubclass(RateLimitError, DataSourceError)

        # Other exceptions should inherit from QuantChainError
        assert issubclass(ConfigurationError, QuantChainError)
        assert issubclass(ValidationError, QuantChainError)

        # SymbolNotFoundError should inherit from ValueError
        assert issubclass(SymbolNotFoundError, ValueError)
