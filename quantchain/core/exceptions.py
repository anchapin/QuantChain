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


class SecurityError(QuantChainError):
    """Base exception for security module."""

    pass


class KeyNotFoundError(SecurityError):
    """Raised when required API key is missing."""

    def __init__(self, key_name: str):
        self.key_name = key_name
        super().__init__(
            f"Required API key '{key_name}' not found in environment variables"
        )


class InvalidKeyError(SecurityError):
    """Raised when API key fails validation."""

    def __init__(self, key_name: str, reason: str):
        self.key_name = key_name
        self.reason = reason
        super().__init__(f"API key '{key_name}' validation failed: {reason}")
