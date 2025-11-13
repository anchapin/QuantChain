"""Common exceptions for QuantChain."""


class QuantChainError(Exception):
    """Base exception for QuantChain."""


class DataSourceError(QuantChainError):
    """Raised when data cannot be fetched from the source."""


class AuthenticationError(DataSourceError):
    """Raised when API authentication fails."""


class RateLimitError(DataSourceError):
    """Raised when API rate limits are exceeded."""


class SymbolNotFoundError(ValueError):
    """Raised when a requested symbol is not found."""


class ConfigurationError(QuantChainError):
    """Raised when configuration is invalid."""


class ValidationError(QuantChainError):
    """Raised when input validation fails."""


# Add missing exception classes for compatibility
class DataError(QuantChainError):
    """Raised when data processing fails."""

    pass


class ModelError(QuantChainError):
    """Raised when ML model operations fail."""

    pass


class ConnectorError(QuantChainError):
    """Raised when trading connector operations fail."""

    pass


class SecurityError(QuantChainError):
    """Raised when security operations fail."""

    pass


class BacktestError(QuantChainError):
    """Raised when backtesting operations fail."""

    pass


class APIError(QuantChainError):
    """Raised when API operations fail."""

    pass


class TradingError(QuantChainError):
    """Raised when trading operations fail."""

    pass
