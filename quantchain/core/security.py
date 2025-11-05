"""
Security module for secure API key management and validation.

Provides SecureKeyManager class and utilities for secure handling of
sensitive credentials in the QuantChain framework.
"""

import os
import re
import stat
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Any

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

from .exceptions import SecurityError, KeyNotFoundError


@dataclass
class SecurityConfig:
    """Configuration for security module."""

    env_file: Optional[str] = None
    require_encryption: bool = False
    audit_on_load: bool = True
    allowed_key_patterns: Dict[str, str] = field(default_factory=dict)


class SecureKeyManager:
    """Secure API key management with validation and auditing."""

    # Default validation patterns for common API keys
    DEFAULT_PATTERNS = {
        "ALPACA_API_KEY": r"^[A-Za-z0-9]{16,32}$",
        "ALPACA_SECRET_KEY": r"^[A-Za-z0-9]{16,32}$",
        "POLYGON_API_KEY": r"^[A-Za-z0-9_-]{20,50}$",
        "DEXSCREENER_API_KEY": r"^[A-Za-z0-9_-]{10,40}$",
    }

    # List of all required keys for the framework
    REQUIRED_KEYS = [
        "ALPACA_API_KEY",
        "ALPACA_SECRET_KEY",
    ]

    # Optional keys that are commonly used
    OPTIONAL_KEYS = [
        "POLYGON_API_KEY",
        "DEXSCREENER_API_KEY",
        "IB_HOST",
        "IB_PORT",
        "IB_CLIENT_ID",
    ]

    # Sensitive patterns to identify sensitive data
    SENSITIVE_PATTERNS = [
        r".*SECRET.*",
        r".*KEY.*",
        r".*TOKEN.*",
        r".*PASSWORD.*",
        r".*CREDENTIAL.*",
    ]

    def __init__(
        self,
        config: Optional[SecurityConfig] = None,
        *,
        env_file: Optional[str] = None,
        audit_on_load: Optional[bool] = None,
    ):
        """Initialize SecureKeyManager with optional configuration."""
        # Handle legacy env_file parameter for backward compatibility
        if config is None:
            config = SecurityConfig()

        # Override config with direct parameters if provided
        if env_file is not None:
            config.env_file = env_file
        if audit_on_load is not None:
            config.audit_on_load = audit_on_load

        self.config = config
        self._cached_keys: Dict[str, Optional[str]] = {}
        self._load_environment()

        if self.config.audit_on_load:
            audit_result = self.audit_security()
            if audit_result["missing_keys"] or audit_result["weak_keys"]:
                print("Security Audit Warning:")
                if audit_result["missing_keys"]:
                    print(f"  Missing required keys: {audit_result['missing_keys']}")
                if audit_result["weak_keys"]:
                    print(f"  Weak keys detected: {audit_result['weak_keys']}")

    def _load_environment(self) -> None:
        """Load environment variables from file if specified."""
        if self.config.env_file and load_dotenv:
            # Only attempt to load if the file exists
            if Path(self.config.env_file).exists():
                if not load_dotenv(self.config.env_file):
                    raise SecurityError(
                        f"Failed to load environment file: {self.config.env_file}"
                    )

    def get_key(self, key_name: str, required: bool = True) -> Optional[str]:
        """
        Retrieve API key from environment variables with caching.

        Args:
            key_name: Name of the environment variable
            required: Whether to raise exception if key is missing

        Returns:
            API key value or None if not found and not required

        Raises:
            KeyNotFoundError: If required key is missing
        """
        # Check cache first
        if key_name in self._cached_keys:
            return self._cached_keys[key_name]

        # Get from environment
        key_value = os.getenv(key_name)

        # Cache the result (even None)
        self._cached_keys[key_name] = key_value

        if required and key_value is None:
            raise KeyNotFoundError(key_name)

        return key_value

    def validate_key(self, key_name: str, key_value: str) -> bool:
        """
        Validate API key format and requirements.

        Args:
            key_name: Name of the key for validation rules
            key_value: The actual key value to validate

        Returns:
            True if key is valid, False otherwise
        """
        if not key_value:
            return False

        # Use custom pattern if provided, otherwise use default
        patterns = {**self.DEFAULT_PATTERNS, **self.config.allowed_key_patterns}
        pattern = patterns.get(key_name)

        if pattern:
            return bool(re.match(pattern, key_value))

        # Generic validation for unknown keys
        return self._validate_generic_key(key_value)

    def _validate_generic_key(self, key_value: str) -> bool:
        """Validate a generic API key with basic security rules."""
        # Minimum length check
        if len(key_value) < 8:
            return False

        # Check for common weak patterns
        weak_patterns = [
            r"^test.*",
            r"^demo.*",
            r"^sample.*",
            r"^123.*",
            r".*password.*",
            r".*secret.*",
        ]

        for pattern in weak_patterns:
            if re.match(pattern, key_value.lower()):
                return False

        # Should contain at least some alphanumeric characters
        if not re.search(r"[a-zA-Z0-9]", key_value):
            return False

        return True

    def list_required_keys(self) -> List[str]:
        """Return list of all required API keys for the framework."""
        return self.REQUIRED_KEYS.copy()

    def list_optional_keys(self) -> List[str]:
        """Return list of optional API keys."""
        return self.OPTIONAL_KEYS.copy()

    def audit_security(self) -> Dict[str, Any]:
        """
        Perform security audit of current configuration.

        Returns:
            Dictionary containing audit results with missing_keys,
            weak_keys, environment_security, and recommendations
        """
        audit_result: Dict[str, Any] = {
            "missing_keys": [],
            "weak_keys": [],
            "environment_security": "unknown",
            "recommendations": [],
        }

        # Check for missing required keys
        for key in self.REQUIRED_KEYS:
            key_value = self.get_key(key, required=False)
            if key_value is None:
                audit_result["missing_keys"].append(key)

        # Check for weak keys in known keys
        all_keys = self.REQUIRED_KEYS + self.OPTIONAL_KEYS
        for key in all_keys:
            key_value = self.get_key(key, required=False)
            if key_value and not self.validate_key(key, key_value):
                audit_result["weak_keys"].append(key)

        # Check for weak keys in other environment variables
        for key in os.environ.keys():
            if key not in all_keys and is_sensitive_key(key):
                key_value = os.environ[key]
                if key_value and not self.validate_key(key, key_value):
                    audit_result["weak_keys"].append(key)

        # Check environment file security if specified
        if self.config.env_file:
            env_path = Path(self.config.env_file)
            if env_path.exists():
                audit_result["environment_security"] = (
                    "secure" if validate_env_permissions(str(env_path)) else "insecure"
                )
            else:
                audit_result["environment_security"] = "missing"

        # Generate recommendations
        if audit_result["missing_keys"]:
            audit_result["recommendations"].append(
                "Set missing required API keys in environment variables"
            )

        if audit_result["weak_keys"]:
            audit_result["recommendations"].append(
                "Replace weak API keys with strong, unique values"
            )

        if audit_result["environment_security"] == "insecure":
            audit_result["recommendations"].append(
                f"Set secure file permissions (600) on {self.config.env_file}"
            )

        if not audit_result["recommendations"]:
            audit_result["recommendations"].append("Security configuration looks good!")

        return audit_result


def load_env_file(env_file: Optional[str] = None) -> bool:
    """
    Load environment variables from .env file.

    Args:
        env_file: Path to .env file

    Returns:
        True if loaded successfully, False otherwise
    """
    if not load_dotenv:
        print("Warning: python-dotenv not installed. Cannot load .env file.")
        return False

    if env_file and not Path(env_file).exists():
        return False

    try:
        return bool(load_dotenv(env_file))
    except Exception:
        return False


def validate_env_permissions(env_file: str) -> bool:
    """
    Validate that .env file has appropriate permissions.

    Args:
        env_file: Path to .env file

    Returns:
        True if permissions are secure, False otherwise
    """
    try:
        file_path = Path(env_file)
        file_stat = file_path.stat()
        file_mode = file_stat.st_mode

        # Check that file exists and is readable by owner
        if not file_path.exists():
            return False

        # Check that file is not readable by others (no o+r permission)
        if file_mode & stat.S_IROTH:
            return False

        # Check that file is not readable by group (no g+r permission)
        if file_mode & stat.S_IRGRP:
            return False

        # Allow owner read/write (600) or more restrictive
        return bool(file_mode & stat.S_IRUSR)

    except (OSError, FileNotFoundError):
        return False


def sanitize_env_vars() -> None:
    """Remove any hardcoded credentials from process environment."""
    sensitive_keys = []

    for key in os.environ.keys():
        # Check if key matches sensitive patterns
        for pattern in SecureKeyManager.SENSITIVE_PATTERNS:
            if re.match(pattern, key, re.IGNORECASE):
                sensitive_keys.append(key)
                break

    # Remove sensitive environment variables
    for key in sensitive_keys:
        os.environ.pop(key, None)

    if sensitive_keys:
        print(f"Sanitized {len(sensitive_keys)} sensitive environment variables")


def is_sensitive_key(key_name: str) -> bool:
    """
    Check if a key name suggests it contains sensitive information.

    Args:
        key_name: Name of the environment variable

    Returns:
        True if key appears to be sensitive, False otherwise
    """
    for pattern in SecureKeyManager.SENSITIVE_PATTERNS:
        if re.match(pattern, key_name, re.IGNORECASE):
            return True
    return False


def create_env_template(output_path: str = ".env.example") -> None:
    """
    Create a template .env.example file with all required keys.

    Args:
        output_path: Path where to create the template file
    """
    template_content = """# QuantChain Environment Variables Template
# Copy this file to .env and fill in your actual API keys

# Required - Alpaca Trading API Keys
ALPACA_API_KEY=your_alpaca_api_key_here
ALPACA_SECRET_KEY=your_alpaca_secret_key_here

# Optional - Polygon.io API Key (for equities data)
POLYGON_API_KEY=your_polygon_api_key_here

# Optional - Dexscreener API Key (for enhanced crypto data)
DEXSCREENER_API_KEY=your_dexscreener_api_key_here

# Optional - Interactive Brokers Configuration
IB_HOST=localhost
IB_PORT=7497
IB_CLIENT_ID=1

# Optional - LLM Provider Configuration
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Security Notes:
# 1. Never commit this file with real keys to version control
# 2. Set file permissions to 600 (chmod 600 .env)
# 3. Use strong, unique API keys
# 4. Consider using a secret manager in production
"""

    with open(output_path, "w") as f:
        f.write(template_content)

    # Set appropriate permissions
    os.chmod(output_path, 0o644)
    print(f"Created environment template: {output_path}")
