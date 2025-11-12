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
