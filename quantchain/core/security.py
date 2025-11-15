"""Security module for QuantChain - API key management and credential handling."""

import os
import re
import json
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass
from pathlib import Path

from quantchain.core.secret_managers import get_default_secret_manager, create_secret_manager
from quantchain.core.secret_managers.base import SecretManager


class CredentialNotFoundError(Exception):
    """Raised when requested credentials don't exist."""
    pass


class SecurityConfigurationError(Exception):
    """Raised when security setup is invalid."""
    pass


class InvalidCredentialFormatError(Exception):
    """Raised when credentials don't match expected format."""
    pass


# API key patterns for validation
API_KEY_PATTERNS = {
    "alpaca": {
        "key_pattern": r"^[A-Z0-9]{16,32}$",
        "secret_pattern": r"^[A-Za-z0-9+/]{32,64}$"
    },
    "polygon": {
        "key_pattern": r"^[a-zA-Z0-9_]{20,40}$"
    },
    "alpha_vantage": {
        "key_pattern": r"^[A-Z0-9]{16}$"
    },
    "anthropic": {
        "key_pattern": r"^sk-ant-api03-[A-Za-z0-9_-]{95}$"
    },
    "openai": {
        "key_pattern": r"^sk-[A-Za-z0-9]{48}$"
    }
}


class APISecurityManager:
    """Manages secure API key storage and validation for QuantChain."""

    def __init__(self, env_file: str = ".env", backend: Optional[str] = None, **kwargs):
        """Initialize security manager with optional env file path or backend."""
        self.env_file = env_file
        self._services = {}
        self._secret_manager: Optional[SecretManager] = None

        # Initialize secret manager
        if backend:
            self._secret_manager = create_secret_manager(backend, **kwargs)
        else:
            self._secret_manager = get_default_secret_manager()

        # Load credentials from environment
        self._load_from_environment()

        # Load credentials from .env file if it exists
        if os.path.exists(env_file):
            self._load_from_env_file()

    def _load_from_environment(self) -> None:
        """Load credentials from environment variables."""
        # Load Alpaca credentials
        alpaca_key = os.getenv("ALPACA_API_KEY")
        alpaca_secret = os.getenv("ALPACA_API_SECRET")
        if alpaca_key:
            self._services["alpaca"] = {"key": alpaca_key}
            if alpaca_secret:
                self._services["alpaca"]["secret"] = alpaca_secret

        # Load Polygon credentials
        polygon_key = os.getenv("POLYGON_API_KEY")
        if polygon_key:
            self._services["polygon"] = {"key": polygon_key}

        # Load Alpha Vantage credentials
        alpha_vantage_key = os.getenv("ALPHA_VANTAGE_API_KEY")
        if alpha_vantage_key:
            self._services["alpha_vantage"] = {"key": alpha_vantage_key}

        # Load Anthropic credentials
        anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        if anthropic_key:
            self._services["anthropic"] = {"key": anthropic_key}

        # Load OpenAI credentials
        openai_key = os.getenv("OPENAI_API_KEY")
        if openai_key:
            self._services["openai"] = {"key": openai_key}

    def _load_from_env_file(self) -> None:
        """Load credentials from .env file."""
        try:
            with open(self.env_file, 'r') as f:
                for line in f:
                    line = line.strip()

                    # Skip comments and empty lines
                    if line.startswith('#') or '=' not in line:
                        continue

                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip().strip('"\'')

                    # Parse environment variable
                    if key == "ALPACA_API_KEY":
                        if "alpaca" not in self._services:
                            self._services["alpaca"] = {}
                        self._services["alpaca"]["key"] = value
                    elif key == "ALPACA_API_SECRET":
                        if "alpaca" not in self._services:
                            self._services["alpaca"] = {}
                        self._services["alpaca"]["secret"] = value
                    elif key == "POLYGON_API_KEY":
                        if "polygon" not in self._services:
                            self._services["polygon"] = {}
                        self._services["polygon"]["key"] = value
                    elif key == "ALPHA_VANTAGE_API_KEY":
                        if "alpha_vantage" not in self._services:
                            self._services["alpha_vantage"] = {}
                        self._services["alpha_vantage"]["key"] = value
                    elif key == "ANTHROPIC_API_KEY":
                        if "anthropic" not in self._services:
                            self._services["anthropic"] = {}
                        self._services["anthropic"]["key"] = value
                    elif key == "OPENAI_API_KEY":
                        if "openai" not in self._services:
                            self._services["openai"] = {}
                        self._services["openai"]["key"] = value
        except Exception as e:
            # If loading fails, just continue with what we have
            pass

    def set_api_key(self, service: str, key: str, secret: Optional[str] = None) -> None:
        """Securely store API key for a service."""
        if not key:
            raise SecurityConfigurationError(f"API key for {service} cannot be empty")

        # Validate key format
        if service in API_KEY_PATTERNS:
            patterns = API_KEY_PATTERNS[service]
            if not re.match(patterns["key_pattern"], key):
                raise InvalidCredentialFormatError(f"API key format for {service} is invalid")

        # Store in memory
        if service not in self._services:
            self._services[service] = {}
        self._services[service]["key"] = key

        if secret:
            # Validate secret format if applicable
            if service in API_KEY_PATTERNS and "secret_pattern" in patterns:
                if not re.match(patterns["secret_pattern"], secret):
                    raise InvalidCredentialFormatError(f"API secret format for {service} is invalid")
            self._services[service]["secret"] = secret

        # Store in secret manager if available
        if self._secret_manager:
            try:
                self._secret_manager.set_secret(f"{service}_api_key", key)
                if secret:
                    self._secret_manager.set_secret(f"{service}_api_secret", secret)
            except Exception:
                # Fall back to memory storage if secret manager fails
                pass

    def get_api_key(self, service: str) -> str:
        """Retrieve API key for a service."""
        if service not in self._services or "key" not in self._services[service]:
            # Try to get from secret manager
            if self._secret_manager:
                try:
                    key = self._secret_manager.get_secret(f"{service}_api_key")
                    if key:
                        # Cache in memory
                        if service not in self._services:
                            self._services[service] = {}
                        self._services[service]["key"] = key
                        return key
                except Exception:
                    pass
            raise CredentialNotFoundError(f"API key for {service} not found")

        return self._services[service]["key"]

    def get_api_secret(self, service: str) -> Optional[str]:
        """Retrieve API secret for a service."""
        if service not in self._services or "secret" not in self._services[service]:
            # Try to get from secret manager
            if self._secret_manager:
                try:
                    secret = self._secret_manager.get_secret(f"{service}_api_secret")
                    if secret:
                        # Cache in memory
                        if service not in self._services:
                            self._services[service] = {}
                        self._services[service]["secret"] = secret
                        return secret
                except Exception:
                    pass
            return None

        return self._services[service]["secret"]

    def validate_credentials(self, service: str, key: Optional[str] = None, secret: Optional[str] = None) -> bool:
        """Validate that stored credentials are properly formatted."""
        try:
            # Use provided key/secret or get from storage
            api_key = key if key is not None else self.get_api_key(service)
            api_secret = secret if secret is not None else self.get_api_secret(service)

            # Check if service has validation patterns
            if service not in API_KEY_PATTERNS:
                return True  # No validation available, assume valid

            patterns = API_KEY_PATTERNS[service]

            # Validate key pattern
            if not re.match(patterns["key_pattern"], api_key):
                return False

            # Validate secret pattern if required and provided
            if "secret_pattern" in patterns and api_secret:
                if not re.match(patterns["secret_pattern"], api_secret):
                    return False

            return True
        except (CredentialNotFoundError, InvalidCredentialFormatError):
            return False

    def list_services(self) -> List[str]:
        """List all configured services."""
        return list(self._services.keys())

    def remove_service(self, service: str) -> None:
        """Remove stored credentials for a service."""
        if service in self._services:
            del self._services[service]

        # Also remove from secret manager
        if self._secret_manager:
            try:
                self._secret_manager.delete_secret(f"{service}_api_key")
                self._secret_manager.delete_secret(f"{service}_api_secret")
            except Exception:
                pass

    def save_to_env_file(self, env_file: Optional[str] = None) -> None:
        """Save credentials to .env file."""
        file_path = env_file if env_file else self.env_file

        # Read existing content
        existing_content = ""
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                existing_content = f.read()

        # Parse existing lines to preserve non-credential content
        existing_lines = existing_content.split('\n')
        non_credential_lines = []
        credential_keys = set()

        for line in existing_lines:
            line = line.strip()
            if not line or line.startswith('#') or '=' not in line:
                non_credential_lines.append(line)
            else:
                key = line.split('=', 1)[0].strip()
                # Skip if it's a credential we're replacing
                if not any(key.endswith(suffix) for suffix in [
                    "ALPACA_API_KEY", "ALPACA_API_SECRET",
                    "POLYGON_API_KEY", "ALPHA_VANTAGE_API_KEY",
                    "ANTHROPIC_API_KEY", "OPENAI_API_KEY"
                ]):
                    non_credential_lines.append(line)
                credential_keys.add(key)

        # Write new content
        with open(file_path, 'w') as f:
            # Write non-credential content first
            for line in non_credential_lines:
                f.write(line + '\n')

            # Write credentials
            for service, credentials in self._services.items():
                if "key" in credentials:
                    if service == "alpaca":
                        f.write(f"ALPACA_API_KEY={credentials['key']}\n")
                    elif service == "polygon":
                        f.write(f"POLYGON_API_KEY={credentials['key']}\n")
                    elif service == "alpha_vantage":
                        f.write(f"ALPHA_VANTAGE_API_KEY={credentials['key']}\n")
                    elif service == "anthropic":
                        f.write(f"ANTHROPIC_API_KEY={credentials['key']}\n")
                    elif service == "openai":
                        f.write(f"OPENAI_API_KEY={credentials['key']}\n")

                if "secret" in credentials:
                    if service == "alpaca":
                        f.write(f"ALPACA_API_SECRET={credentials['secret']}\n")

    def get_service_info(self, service: str) -> Dict[str, Any]:
        """Get information about a service configuration."""
        if service not in self._services:
            return {}

        info = self._services[service].copy()
        # Remove sensitive information from return value
        if "key" in info:
            info["key"] = "***" + info["key"][-4:] if len(info["key"]) > 4 else "****"
        if "secret" in info:
            info["secret"] = "***" + info["secret"][-4:] if len(info["secret"]) > 4 else "****"

        return info

    def refresh_from_env(self) -> None:
        """Refresh credentials from environment and .env file."""
        self._services.clear()
        self._load_from_environment()
        if os.path.exists(self.env_file):
            self._load_from_env_file()
