"""Custom exceptions for QuantChain."""


class QuantChainError(Exception):
    """Base exception for all QuantChain errors."""

    pass


class AuthenticationError(QuantChainError):
    """Exception raised when authentication fails."""

    pass


class DataSourceError(QuantChainError):
    """Exception raised when data source operations fail."""

    pass


class SymbolNotFoundError(QuantChainError):
    """Exception raised when a symbol is not found."""

    pass


class ConfigurationError(QuantChainError):
    """Exception raised for configuration issues."""

    pass


class ValidationError(QuantChainError):
    """Exception raised for validation errors."""

    pass


class InsufficientFundsError(QuantChainError):
    """Exception raised when there are insufficient funds for an operation."""

    pass


class OrderNotFoundError(QuantChainError):
    """Exception raised when an order is not found."""

    pass


class TradingError(QuantChainError):
    """Exception raised for general trading errors."""

    pass


class ConnectorError(QuantChainError):
    """Base exception for connector errors."""

    pass


class AgentError(QuantChainError):
    """Base exception for agent errors."""

    pass


class BacktestError(QuantChainError):
    """Base exception for backtesting errors."""

    pass


class RiskManagementError(QuantChainError):
    """Exception raised for risk management issues."""

    pass


class PortfolioError(QuantChainError):
    """Exception raised for portfolio management issues."""

    pass


class APIError(QuantChainError):
    """Exception raised for API-related errors."""

    pass


class RateLimitError(APIError):
    """Exception raised when API rate limits are exceeded."""

    pass


class NetworkError(QuantChainError):
    """Exception raised for network-related errors."""

    pass
