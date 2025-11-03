"""Common exceptions for QuantChain."""


class QuantChainError(Exception):
    """Base exception for QuantChain."""

    pass


class DataSourceError(QuantChainError):
    """Raised when data cannot be fetched from the source."""

    pass


class AuthenticationError(DataSourceError):
    """Raised when API authentication fails."""

    pass


class RateLimitError(DataSourceError):
    """Raised when API rate limits are exceeded."""

    pass


class SymbolNotFoundError(ValueError):
    """Raised when a requested symbol is not found."""

    pass


class ConfigurationError(QuantChainError):
    """Raised when configuration is invalid."""

    pass


class ValidationError(QuantChainError):
    """Raised when input validation fails."""

    pass
