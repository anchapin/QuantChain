"""Environment variable secret manager for development (NON-PRODUCTION)."""

import logging
import os
import re
from pathlib import Path
from typing import Dict, Optional

from .base import SecretManager


class InvalidCredentialFormatError(Exception):
    """Raised when credentials don't match expected format."""
    pass


class SecurityConfigurationError(Exception):
    """Raised when security configuration is invalid."""
    pass


logger = logging.getLogger(__name__)


# Service-specific validation patterns (copied from original security.py)
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


class EnvSecretManager(SecretManager):
    """Environment variable secret manager for development ONLY.

    WARNING: This implementation reads secrets from environment variables and .env files.
    DO NOT use in production environments. For production, use VaultSecretManager,
    AWSSecretsManager, or GCPSecretManager instead.
    """

    def __init__(
        self, env_file: str = ".env", allow_production_warning: bool = True
    ) -> None:
        """Initialize environment variable secret manager.

        Args:
            env_file: Path to .env file for local development
            allow_production_warning: Whether to show production warnings
        """
        if allow_production_warning:
            logger.warning(
                "Using EnvSecretManager - FOR DEVELOPMENT ONLY. "
                "DO NOT use in production environments."
            )

        self.env_file = Path(env_file)
        self._credentials: Dict[str, Dict[str, str]] = {}
        self._load_credentials()

    def _load_credentials(self) -> None:
        """Load credentials from environment variables and .env file."""
        # Load from .env file first (lower priority)
        if self.env_file.exists():
            try:
                with open(self.env_file, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#") and "=" in line:
                            key, value = line.split("=", 1)
                            key = key.strip()
                            value = value.strip().strip('"').strip("'")

                            # Parse service and type from key
                            if key.endswith("_API_KEY"):
                                service = key[:-8].lower()  # Remove _API_KEY
                                if service not in self._credentials:
                                    self._credentials[service] = {}
                                self._credentials[service]["key"] = value
                            elif key.endswith("_API_SECRET"):
                                service = key[:-11].lower()  # Remove _API_SECRET
                                if service not in self._credentials:
                                    self._credentials[service] = {}
                                self._credentials[service]["secret"] = value
            except Exception as e:
                logger.warning(f"Failed to load .env file {self.env_file}: {e}")

        # Load from environment variables last (highest priority)
        for service in API_KEY_PATTERNS.keys():
            key_env = f"{service.upper()}_API_KEY"
            secret_env = f"{service.upper()}_API_SECRET"

            if key_env in os.environ:
                if service not in self._credentials:
                    self._credentials[service] = {}
                self._credentials[service]["key"] = os.environ[key_env]
                if secret_env in os.environ:
                    self._credentials[service]["secret"] = os.environ[secret_env]

    def get_secret(self, key: str) -> Optional[str]:
        """Retrieve a secret by key.

        Args:
            key: The secret key/identifier

        Returns:
            The secret value or None if not found
        """
        # Try to parse service from key
        if "_" in key:
            parts = key.split("_")
            if len(parts) >= 3 and parts[-2] == "API":
                service = "_".join(parts[:-2]).lower()
                if parts[-1] == "KEY":
                    return self._credentials.get(service, {}).get("key")
                elif parts[-1] == "SECRET":
                    return self._credentials.get(service, {}).get("secret")

        # Try direct environment variable lookup
        value = os.getenv(key)
        if value:
            return value

        return None

    def get_service_credentials(self, service: str) -> Dict[str, str]:
        """Retrieve all credentials for a service.

        Args:
            service: The service name (e.g., 'alpaca', 'ib_async')

        Returns:
            Dictionary containing the service's credentials
        """
        return self._credentials.get(service.lower(), {})

    def validate_service(self, service: str) -> bool:
        """Validate if credentials exist for a service.

        Args:
            service: The service name

        Returns:
            True if credentials are available, False otherwise
        """
        service = service.lower()
        return service in self._credentials and bool(self._credentials[service])

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
        test_key = (
            key if key is not None else self._credentials.get(service, {}).get("key")
        )
        test_secret = (
            secret
            if secret is not None
            else self._credentials.get(service, {}).get("secret")
        )

        # If no credentials are stored and none are provided, return False
        if test_key is None and test_secret is None and key is None and secret is None:
            return False

        # If key is explicitly None (but secret is provided), only validate secret
        if key is None and secret is not None:
            # Empty string should be treated as not provided for services w/o secrets
            if "secret_pattern" not in patterns:
                return True  # No secret required for this service

            # For services that require secrets, secret must be provided and valid
            if test_secret is None:
                return False  # Secret is required but not provided

            return bool(re.match(patterns["secret_pattern"], test_secret))

        # Normal case: validate both key and secret
        if not test_key or not re.match(patterns["key_pattern"], test_key):
            return False

        # For services that don't require secrets, just key validation is enough
        if "secret_pattern" not in patterns:
            return True

        # For services that require secrets, secret must be provided and valid
        if test_secret is None:
            return False

        return bool(re.match(patterns["secret_pattern"], test_secret))

    def set_api_key(self, service: str, key: str, secret: Optional[str] = None) -> None:
        """Store API key for a service.

        Args:
            service: Service identifier (e.g., 'alpaca', 'polygon')
            key: API key
            secret: Optional API secret
        """
        if service not in API_KEY_PATTERNS:
            raise SecurityConfigurationError(f"Unsupported service: {service}")

        if not self.validate_credentials(service, key, secret):
            raise InvalidCredentialFormatError(f"Invalid credentials format for {service}")

        if service not in self._credentials:
            self._credentials[service] = {}

        self._credentials[service]["key"] = key
        if secret:
            self._credentials[service]["secret"] = secret

        logger.info(f"Credentials set for service: {service}")

    def remove_service(self, service: str) -> None:
        """Remove stored credentials for a service.

        Args:
            service: Service identifier
        """
        if service in self._credentials:
            del self._credentials[service]
            logger.info(f"Credentials removed for service: {service}")

    def save_to_env_file(self) -> None:
        """Save current credentials to .env file (development only)."""
        if not self.env_file.exists():
            self.env_file.touch()

        env_lines = []
        if self.env_file.exists():
            with open(self.env_file, "r", encoding="utf-8") as f:
                env_lines = f.readlines()

        filtered_lines = [
            line
            for line in env_lines
            if all(
                f"{service.upper()}_API" not in line
                for service in self._credentials.keys()
            )
        ]
        # Add current credentials
        for service, creds in self._credentials.items():
            filtered_lines.append(f'{service.upper()}_API_KEY="{creds["key"]}"\n')
            if "secret" in creds:
                filtered_lines.append(
                    f'{service.upper()}_API_SECRET="{creds["secret"]}"\n'
                )

        with open(self.env_file, "w", encoding="utf-8") as f:
            f.writelines(filtered_lines)

        logger.info(f"Credentials saved to {self.env_file}")
