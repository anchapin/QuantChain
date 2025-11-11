"""Secret management module for QuantChain."""

from .base import SecretManager
from .env import EnvSecretManager
from .factory import (
    create_secret_manager,
    get_default_secret_manager,
    list_secret_managers,
    register_secret_manager,
)

# Optional imports - only expose if available
try:
    from .aws import AWSSecretsManager
    _AWS_AVAILABLE = True
except ImportError:
    _AWS_AVAILABLE = False

try:
    from .gcp import GCPSecretManager
    _GCP_AVAILABLE = True
except ImportError:
    _GCP_AVAILABLE = False

try:
    from .vault import VaultSecretManager
    _VAULT_AVAILABLE = True
except ImportError:
    _VAULT_AVAILABLE = False

__all__ = [
    "SecretManager",
    "EnvSecretManager",
    "create_secret_manager",
    "get_default_secret_manager",
    "list_secret_managers",
    "register_secret_manager",
]

# Only add optional managers if available
if _AWS_AVAILABLE:
    __all__.append("AWSSecretsManager")
if _GCP_AVAILABLE:
    __all__.append("GCPSecretManager")
if _VAULT_AVAILABLE:
    __all__.append("VaultSecretManager")
