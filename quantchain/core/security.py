"""Security module for API key management and credential handling."""

import logging
import os
import re
from pathlib import Path
from typing import Dict, List, Optional

# Exception classes defined below

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
    """Manages API credentials securely using environment variables and .env files."""

    def __init__(self, env_file: str = ".env") -> None:
        """Initialize security manager.

        Args:
            env_file: Path to .env file for local development
        """
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
            raise InvalidCredentialFormatError(
                f"Invalid credentials format for {service}"
            )

        if service not in self._credentials:
            self._credentials[service] = {}

        self._credentials[service]["key"] = key
        if secret:
            self._credentials[service]["secret"] = secret

        logger.info(f"Credentials set for service: {service}")

    def get_api_key(self, service: str) -> str:
        """Retrieve API key for a service.

        Args:
            service: Service identifier

        Returns:
            API key string

        Raises:
            CredentialNotFoundError: If credentials don't exist
        """
        if service not in self._credentials or "key" not in self._credentials[service]:
            raise CredentialNotFoundError(f"No API key found for service: {service}")

        return self._credentials[service]["key"]

    def get_api_secret(self, service: str) -> Optional[str]:
        """Retrieve API secret for a service.

        Args:
            service: Service identifier

        Returns:
            API secret string or None if not set
        """
        if service not in self._credentials:
            return None

        return self._credentials[service].get("secret")

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

        # Validate key
        if not test_key or not re.match(patterns["key_pattern"], test_key):
            return False

        # Validate secret if required
        if "secret_pattern" not in patterns:
            return True  # No secret required for this service

        # For services that require secrets, secret must be provided and valid
        if test_secret is None:
            return False  # Secret is required but not provided

        return bool(re.match(patterns["secret_pattern"], test_secret))

    def list_services(self) -> List[str]:
        """List all configured services.

        Returns:
            List of service names with stored credentials
        """
        return list(self._credentials.keys())

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


class CredentialNotFoundError(Exception):
    """Raised when requested credentials are not found."""

    pass


class InvalidCredentialFormatError(Exception):
    """Raised when credentials don't match expected format."""

    pass


class SecurityConfigurationError(Exception):
    """Raised when security configuration is invalid."""

    pass
