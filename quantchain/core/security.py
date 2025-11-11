"""Security module for API key management and credential handling."""

import logging
import re
from typing import Dict, List, Optional

from .secret_managers import (
    create_secret_manager,
    get_default_secret_manager,
    InvalidCredentialFormatError,
    SecurityConfigurationError,
)

logger = logging.getLogger(__name__)

# Service-specific validation patterns
API_KEY_PATTERNS = {
    "alpaca": {
        "key_pattern": r"^A[A-Z0-9]{16,20}$",  # Alpaca keys start with 'A'
        "secret_pattern": r"^[A-Za-z0-9+/]{40,50}$",  # Base64-like secret
    },
    "polygon": {
        "key_pattern": r"^[A-Za-z0-9_-]{20,50}$",  # Polygon API keys
    },
    "alpha_vantage": {
        "key_pattern": r"^[A-Z0-9]{16}$",  # Alpha Vantage 16-char keys
    },
    "anthropic": {
        "key_pattern": r"^sk-ant-[A-Za-z0-9_-]{95,110}$",  # Anthropic API keys
    },
    "openai": {
        "key_pattern": r"^sk-[A-Za-z0-9_-]{20,200}$",  # OpenAI API keys
    },
}


class APISecurityManager:
    """Manages API credentials securely using production-grade secret managers.

    This class provides a unified interface for accessing API credentials from
    various secret management backends including HashiCorp Vault, AWS Secrets Manager,
    Google Cloud Secret Manager, and environment variables (development only).

    For production use, configure QUANTCHAIN_SECRET_BACKEND environment variable
    to one of: 'vault', 'aws', 'gcp'. For development, 'env' can be used.
    """

    def __init__(
        self,
        backend: Optional[str] = None,
        config: Optional[Dict] = None,
        **kwargs,
    ) -> None:
        """Initialize security manager.

        Args:
            backend: Secret backend to use ('vault', 'aws', 'gcp', 'env').
                     If None, checks QUANTCHAIN_SECRET_BACKEND env var.
                     For backward compatibility, if this is a file path ending in .env,
                     will use 'env' backend with that file.
            config: Configuration dictionary for the secret manager
            **kwargs: Additional configuration parameters passed to secret manager
        """
        # Initialize the appropriate secret manager
        # Handle backward compatibility: if backend looks like a file path, use env backend
        if backend and isinstance(backend, str) and backend.endswith('.env'):
            # Old API: passing env file path as first argument
            kwargs['env_file'] = backend
            backend = 'env'
        
        if backend or config or kwargs:
            # Use custom configuration
            self._secret_manager = create_secret_manager(backend, config, **kwargs)
        else:
            # Use default configuration from environment
            self._secret_manager = get_default_secret_manager()

        # Store validation patterns for compatibility
        self.api_key_patterns = API_KEY_PATTERNS

    def get_api_key(self, service: str) -> str:
        """Retrieve API key for a service.

        Args:
            service: Service identifier

        Returns:
            API key string

        Raises:
            CredentialNotFoundError: If credentials don't exist
        """
        key = self._secret_manager.get_api_key(service)
        if not key:
            raise CredentialNotFoundError(f"No API key found for service: {service}")
        return key

    def get_api_secret(self, service: str) -> Optional[str]:
        """Retrieve API secret for a service.

        Args:
            service: Service identifier

        Returns:
            API secret string or None if not set
        """
        return self._secret_manager.get_api_secret(service)

    def set_api_key(self, service: str, key: str, secret: Optional[str] = None) -> None:
        """Store API key for a service.

        Note: This method is deprecated and only works with EnvSecretManager.
        Production secret managers don't support writing credentials.

        Args:
            service: Service identifier (e.g., 'alpaca', 'polygon')
            key: API key
            secret: Optional API secret
        """
        logger.warning(
            "set_api_key() is deprecated and only works with EnvSecretManager. "
            "Store secrets directly in your production secret management system."
        )

        # Only implement for EnvSecretManager
        if hasattr(self._secret_manager, "set_api_key"):
            self._secret_manager.set_api_key(service, key, secret)
            logger.info(f"Credentials set for service: {service}")
        else:
            raise SecurityConfigurationError(
                "Cannot set credentials in production secret managers. "
                "Configure secrets directly in your secret management system."
            )

    def validate_credentials(
        self, service: str, key: Optional[str] = None, secret: Optional[str] = None
    ) -> bool:
        """Validate credentials format for a service.

        Args:
            service: Service identifier
            key: API key to validate (uses stored key if None)
            secret: API secret to validate (uses stored secret if None)

        Returns:
            True if valid, False otherwise
        """
        if service not in API_KEY_PATTERNS:
            return False

        patterns = API_KEY_PATTERNS[service]

        # Use provided values or stored values
        if key is None:
            key = self._secret_manager.get_api_key(service)
        if secret is None:
            secret = self._secret_manager.get_api_secret(service)

        # If no credentials are stored and none are provided, return False
        if key is None and secret is None:
            return False

        # If key is explicitly None (but secret is provided), only validate secret
        if key is None and secret is not None:
            # Empty string should be treated as not provided for services w/o secrets
            if "secret_pattern" not in patterns:
                return True  # No secret required for this service

            # For services that require secrets, secret must be provided and valid
            if secret is None:
                return False  # Secret is required but not provided

            return bool(re.match(patterns["secret_pattern"], secret))

        # Validate key
        if not key or not re.match(patterns["key_pattern"], key):
            return False

        # Validate secret if required
        if "secret_pattern" not in patterns:
            return True  # No secret required for this service

        # For services that require secrets, secret must be provided and valid
        if secret is None:
            return False  # Secret is required but not provided

        return bool(re.match(patterns["secret_pattern"], secret))

    def validate_service(self, service: str) -> bool:
        """Validate if credentials exist for a service.

        Args:
            service: Service name

        Returns:
            True if credentials are available, False otherwise
        """
        return self._secret_manager.validate_service(service)

    def list_services(self) -> List[str]:
        """List all configured services.

        Returns:
            List of service names with stored credentials
        """
        # Note: This is a best-effort implementation as some secret managers
        # don't support listing all services directly
        services = []
        for service in API_KEY_PATTERNS.keys():
            if self.validate_service(service):
                services.append(service)
        return services

    def remove_service(self, service: str) -> None:
        """Remove stored credentials for a service.

        Note: This method is not supported for most production secret managers.
        It's kept for backward compatibility with the EnvSecretManager.

        Args:
            service: Service identifier
        """
        logger.warning(
            "remove_service() is deprecated and not supported for production secret managers. "
            "Remove secrets directly from your secret management system."
        )

        # Only implement for EnvSecretManager
        if hasattr(self._secret_manager, "remove_service"):
            self._secret_manager.remove_service(service)
            logger.info(f"Credentials removed for service: {service}")

    def save_to_env_file(self) -> None:
        """Save current credentials to .env file (development only).

        Note: This method is deprecated and only works with EnvSecretManager.
        """
        logger.warning(
            "save_to_env_file() is deprecated and only works with EnvSecretManager. "
            "Use your secret management system's export/import features instead."
        )

        # Only implement for EnvSecretManager
        if hasattr(self._secret_manager, "save_to_env_file"):
            self._secret_manager.save_to_env_file()
            logger.info(
                f"Credentials saved to {getattr(self._secret_manager, 'env_file', '.env')}"
            )

    def get_service_credentials(self, service: str) -> Dict[str, str]:
        """Retrieve all credentials for a service.

        Args:
            service: Service identifier

        Returns:
            Dictionary containing the service's credentials
        """
        return self._secret_manager.get_service_credentials(service)


class CredentialNotFoundError(Exception):
    """Raised when requested credentials are not found."""

    pass



