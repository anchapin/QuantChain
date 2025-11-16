"""
Comprehensive tests for quantchain.core.exceptions module.
These tests are designed to achieve high test coverage for the exceptions module.
"""

import pytest

from quantchain.core.exceptions import (
    AgentError,
    APIError,
    AuthenticationError,
    BacktestError,
    ConfigurationError,
    ConnectorError,
    DataSourceError,
    InsufficientFundsError,
    NetworkError,
    OrderNotFoundError,
    PortfolioError,
    QuantChainError,
    RateLimitError,
    RiskManagementError,
    SymbolNotFoundError,
    TradingError,
    ValidationError,
)


class TestQuantChainExceptions:
    """Test QuantChain base exception and all derived exceptions."""

    def test_quant_chain_error_base(self) -> None:
        """Test base QuantChainError exception."""
        error = QuantChainError("Test message")
        assert str(error) == "Test message"
        assert isinstance(error, Exception)
        assert isinstance(error, QuantChainError)

    def test_quant_chain_error_with_no_message(self) -> None:
        """Test QuantChainError without message."""
        error = QuantChainError()
        assert str(error) == ""

    def test_quant_chain_error_inheritance(self) -> None:
        """Test that all custom exceptions inherit from QuantChainError."""
        exceptions_to_test = [
            ConfigurationError,
            AuthenticationError,
            DataSourceError,
            SymbolNotFoundError,
            ValidationError,
            InsufficientFundsError,
            OrderNotFoundError,
            TradingError,
            ConnectorError,
            AgentError,
            BacktestError,
            RiskManagementError,
            PortfolioError,
            APIError,
            RateLimitError,
            NetworkError,
        ]

        for exc_class in exceptions_to_test:
            # Test that they inherit from QuantChainError
            assert issubclass(
                exc_class, QuantChainError
            ), f"{exc_class.__name__} should inherit from QuantChainError"

            # Test that they inherit from Exception
            assert issubclass(
                exc_class, Exception
            ), f"{exc_class.__name__} should inherit from Exception"

    def test_configuration_error(self) -> None:
        """Test ConfigurationError exception."""
        error = ConfigurationError("Invalid configuration")
        assert str(error) == "Invalid configuration"
        assert isinstance(error, QuantChainError)

    def test_authentication_error(self) -> None:
        """Test AuthenticationError exception."""
        error = AuthenticationError("Authentication failed")
        assert str(error) == "Authentication failed"
        assert isinstance(error, QuantChainError)

    def test_data_source_error(self) -> None:
        """Test DataSourceError exception."""
        error = DataSourceError("Data source error")
        assert str(error) == "Data source error"
        assert isinstance(error, QuantChainError)

    def test_symbol_not_found_error(self) -> None:
        """Test SymbolNotFoundError exception."""
        error = SymbolNotFoundError("Symbol not found")
        assert str(error) == "Symbol not found"
        assert isinstance(error, QuantChainError)

    def test_validation_error(self) -> None:
        """Test ValidationError exception."""
        error = ValidationError("Validation failed")
        assert str(error) == "Validation failed"
        assert isinstance(error, QuantChainError)

    def test_insufficient_funds_error(self) -> None:
        """Test InsufficientFundsError exception."""
        error = InsufficientFundsError("Insufficient funds")
        assert str(error) == "Insufficient funds"
        assert isinstance(error, QuantChainError)

    def test_order_not_found_error(self) -> None:
        """Test OrderNotFoundError exception."""
        error = OrderNotFoundError("Order not found")
        assert str(error) == "Order not found"
        assert isinstance(error, QuantChainError)

    def test_trading_error(self) -> None:
        """Test TradingError exception."""
        error = TradingError("Trading operation failed")
        assert str(error) == "Trading operation failed"
        assert isinstance(error, QuantChainError)

    def test_connector_error(self) -> None:
        """Test ConnectorError exception."""
        error = ConnectorError("Connector error")
        assert str(error) == "Connector error"
        assert isinstance(error, QuantChainError)

    def test_agent_error(self) -> None:
        """Test AgentError exception."""
        error = AgentError("Agent error")
        assert str(error) == "Agent error"
        assert isinstance(error, QuantChainError)

    def test_backtest_error(self) -> None:
        """Test BacktestError exception."""
        error = BacktestError("Backtest failed")
        assert str(error) == "Backtest failed"
        assert isinstance(error, QuantChainError)

    def test_risk_management_error(self) -> None:
        """Test RiskManagementError exception."""
        error = RiskManagementError("Risk management error")
        assert str(error) == "Risk management error"
        assert isinstance(error, QuantChainError)

    def test_portfolio_error(self) -> None:
        """Test PortfolioError exception."""
        error = PortfolioError("Portfolio error")
        assert str(error) == "Portfolio error"
        assert isinstance(error, QuantChainError)

    def test_api_error(self) -> None:
        """Test APIError exception."""
        error = APIError("API error")
        assert str(error) == "API error"
        assert isinstance(error, QuantChainError)

    def test_rate_limit_error(self) -> None:
        """Test RateLimitError exception."""
        error = RateLimitError("Rate limit exceeded")
        assert str(error) == "Rate limit exceeded"
        assert isinstance(error, APIError)
        assert isinstance(error, QuantChainError)

    def test_network_error(self) -> None:
        """Test NetworkError exception."""
        error = NetworkError("Network error")
        assert str(error) == "Network error"
        assert isinstance(error, QuantChainError)


class TestExceptionHierarchy:
    """Test the exception hierarchy structure."""

    def test_api_error_hierarchy(self) -> None:
        """Test that API errors inherit correctly."""
        base_error = APIError("Base API error")
        rate_limit_error = RateLimitError("Rate limit error")

        assert isinstance(rate_limit_error, APIError)
        assert isinstance(rate_limit_error, QuantChainError)
        assert isinstance(base_error, QuantChainError)

    def test_exception_catching(self) -> None:
        """Test that exceptions can be caught properly."""
        try:
            raise ConfigurationError("Test config error")
        except QuantChainError as e:
            assert str(e) == "Test config error"
        except Exception:
            pytest.fail("Should have been caught by QuantChainError")

        try:
            raise RateLimitError("Rate limit error")
        except APIError as e:
            assert str(e) == "Rate limit error"
        except Exception:
            pytest.fail("Should have been caught by APIError")

    def test_exception_type_hierarchy(self) -> None:
        """Test the type hierarchy of exceptions."""
        # API hierarchy
        assert issubclass(RateLimitError, APIError)
        assert issubclass(APIError, QuantChainError)

        # Direct QuantChainError inheritance
        assert issubclass(ConfigurationError, QuantChainError)
        assert issubclass(TradingError, QuantChainError)
        assert issubclass(BacktestError, QuantChainError)


class TestExceptionWithComplexMessages:
    """Test exceptions with complex message scenarios."""

    def test_exception_with_none_message(self) -> None:
        """Test exceptions with None message."""
        error = ConfigurationError(None)
        assert str(error) == "None"

    def test_exception_with_empty_message(self) -> None:
        """Test exceptions with empty string message."""
        error = ValidationError("")
        assert str(error) == ""

    def test_exception_with_special_characters(self) -> None:
        """Test exceptions with special characters in message."""
        message = "Error with special chars: \n\t\r\"'"
        error = TradingError(message)
        assert str(error) == message

    def test_exception_with_unicode_characters(self) -> None:
        """Test exceptions with unicode characters in message."""
        message = "Error with unicode: ñáéíóú 🚀"
        error = BacktestError(message)
        assert str(error) == message

    def test_exception_with_long_message(self) -> None:
        """Test exceptions with very long messages."""
        message = "x" * 1000
        error = PortfolioError(message)
        assert str(error) == message
        assert len(str(error)) == 1000


class TestExceptionEdgeCases:
    """Test edge cases and unusual scenarios."""

    def test_exception_equality(self) -> None:
        """Test exception equality comparisons."""
        error1 = ConfigurationError("same message")
        error2 = ConfigurationError("same message")
        error3 = ConfigurationError("different message")

        # Same message should be equal
        assert error1.args == error2.args
        assert error1.args != error3.args

        # Different types should not be equal even with same message
        other_error = TradingError("same message")
        assert error1.args == other_error.args  # args are the same
        assert type(error1) != type(other_error)  # but types are different

    def test_exception_repr(self) -> None:
        """Test exception representation."""
        error = ValidationError("Test message")
        repr_str = repr(error)
        assert "ValidationError" in repr_str
        assert "Test message" in repr_str

    def test_exception_with_kwargs(self) -> None:
        """Test creating exceptions with additional keyword arguments."""
        # Standard exceptions don't typically accept kwargs, but let's test that they don't break
        try:
            error = QuantChainError("message", extra_info="test")
            # Some exception classes might accept kwargs, others might not
            # The important thing is that they don't crash
            assert isinstance(error, QuantChainError)
        except TypeError:
            # It's acceptable if kwargs are not accepted
            pass

    def test_exception_iteration(self) -> None:
        """Test that exception args can be iterated."""
        message = "test message"
        error = NetworkError(message, "additional_info")

        # Should be able to iterate over args
        args_tuple = tuple(error.args)
        assert len(args_tuple) == 2
        assert args_tuple[0] == message
        assert args_tuple[1] == "additional_info"
