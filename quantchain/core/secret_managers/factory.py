"""Factory for creating secret managers based on configuration."""

import logging
import os
from typing import Any, Dict, Optional, Type

from .base import SecretManager
from .env import EnvSecretManager

# Optional dependencies - only import if available
try:
    from .aws import AWSSecretsManager
except ImportError:
    AWSSecretsManager = None

try:
    from .gcp import GCPSecretManager
except ImportError:
    GCPSecretManager = None

try:
    from .vault import VaultSecretManager
except ImportError:
    VaultSecretManager = None

logger = logging.getLogger(__name__)

# Registry of available secret managers
SECRET_MANAGERS: Dict[str, Type[SecretManager]] = {
    "env": EnvSecretManager,  # For development only
}

# Add optional managers if available
if VaultSecretManager:
    SECRET_MANAGERS["vault"] = VaultSecretManager

if AWSSecretsManager:
    SECRET_MANAGERS["aws"] = AWSSecretsManager

if GCPSecretManager:
    SECRET_MANAGERS["gcp"] = GCPSecretManager


def create_secret_manager(
    backend: Optional[str] = None,
    config: Optional[Dict[str, Any]] = None,
    **kwargs: Any,
) -> SecretManager:
    """Create a secret manager instance.

    Args:
        backend: The backend to use ('vault', 'aws', 'gcp', 'env')
                 If None, will check QUANTCHAIN_SECRET_BACKEND env var,
                 then default to 'env' for development.
        config: Configuration dictionary for the secret manager
        **kwargs: Additional configuration parameters

    Returns:
        SecretManager instance

    Raises:
        ValueError: If backend is not supported
        RuntimeError: If required configuration is missing
    """
    # Determine backend
    if backend is None:
        backend = os.getenv("QUANTCHAIN_SECRET_BACKEND", "env")
    
    backend = backend.lower()
    
    if backend not in SECRET_MANAGERS:
        available_backends = list(SECRET_MANAGERS.keys())
        
        # Suggest installing missing dependencies
        if backend in ["vault", "aws", "gcp"] and backend not in available_backends:
            install_msg = {
                "vault": "pip install hvac",
                "aws": "pip install boto3",
                "gcp": "pip install google-cloud-secret-manager"
            }
            
            raise ValueError(
                f"Backend '{backend}' is not available. "
                f"To enable it, install the required package: {install_msg.get(backend)}. "
                f"Currently available backends: {available_backends}"
            )
        
        raise ValueError(
            f"Unsupported secret backend: {backend}. "
            f"Supported backends: {available_backends}"
        )
    
    # Show warning for production use of env backend
    if backend == "env" and not os.getenv("QUANTCHAIN_DEV_MODE"):
        logger.warning(
            "Using environment variables for secret management. "
            "This is NOT recommended for production. "
            "Set QUANTCHAIN_SECRET_BACKEND to 'vault', 'aws', or 'gcp' for production use."
        )
    
    # Get the secret manager class
    manager_class = SECRET_MANAGERS[backend]
    
    # Merge config with kwargs
    final_config = config or {}
    final_config.update(kwargs)
    
    try:
        # Create and return the secret manager
        return manager_class(**final_config)
    except Exception as e:
        raise RuntimeError(f"Failed to create {backend} secret manager: {e}") from e


def get_default_secret_manager() -> SecretManager:
    """Get the default secret manager based on environment configuration.

    Returns:
        SecretManager instance
    """
    return create_secret_manager()


def register_secret_manager(name: str, manager_class: Type[SecretManager]) -> None:
    """Register a custom secret manager.

    Args:
        name: Name for the secret manager
        manager_class: SecretManager implementation class
    """
    SECRET_MANAGERS[name.lower()] = manager_class
    logger.info(f"Registered custom secret manager: {name}")


def list_secret_managers() -> list:
    """List all available secret managers.

    Returns:
        List of secret manager names
    """
    return list(SECRET_MANAGERS.keys())
