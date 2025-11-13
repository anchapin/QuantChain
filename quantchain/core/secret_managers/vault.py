"""HashiCorp Vault secret manager implementation."""

import json
import logging
import os
from typing import Any, Dict, Optional, Union

try:
    import hvac
    HVAC_AVAILABLE = True
except ImportError:
    HVAC_AVAILABLE = False

from .base import SecretManager

logger = logging.getLogger(__name__)


class VaultSecretManager(SecretManager):
    """HashiCorp Vault secret manager."""

    def __init__(
        self,
        url: Optional[str] = None,
        token: Optional[str] = None,
        namespace: Optional[str] = None,
        verify: bool = True,
        mount_point: str = "secret",
        **kwargs: Dict,
    ) -> None:
        """Initialize Vault secret manager.

        Args:
            url: Vault server URL (defaults to VAULT_ADDR env var)
            token: Vault token (defaults to VAULT_TOKEN env var)
            namespace: Vault namespace (optional)
            verify: Whether to verify SSL certificate
            mount_point: Vault mount point for secrets (default: 'secret')
            **kwargs: Additional hvac.Client parameters
        """
        if not HVAC_AVAILABLE:
            raise ImportError(
                "hvac library is required for Vault support. Install with: pip install hvac"
            )
        self.url = url or os.getenv("VAULT_ADDR")
        self.token = token or os.getenv("VAULT_TOKEN")
        self.namespace = namespace
        self.verify = verify
        self.mount_point = mount_point

        if not self.url:
            raise ValueError(
                "Vault URL must be provided or set in VAULT_ADDR environment variable"
            )

        if not self.token:
            raise ValueError(
                "Vault token must be provided or set in VAULT_TOKEN environment variable"
            )

        # Initialize Vault client
        self.client = hvac.Client(
            url=self.url,
            token=self.token,
            namespace=self.namespace,
            verify=self.verify,
            **kwargs,
        )

        # Verify connection
        if not self.client.is_authenticated():
            raise RuntimeError("Failed to authenticate with Vault")

        logger.info(f"Connected to Vault at {self.url}")

    def _build_secret_path(self, key: str) -> str:
        """Build the full path for a secret in Vault.

        Args:
            key: The secret key

        Returns:
            Full Vault path for the secret
        """
        # Strip leading slashes and build path
        key = key.lstrip("/")
        return f"{self.mount_point}/data/{key}"

    def get_secret(self, key: str) -> Optional[str]:
        """Retrieve a secret by key.

        Args:
            key: The secret key/identifier

        Returns:
            The secret value or None if not found
        """
        try:
            path = self._build_secret_path(key)
            response: Dict[str, Any] = self.client.secrets.kv.v2.read_secret_version(
                path=path
            )

            if response and "data" in response and "data" in response["data"]:
                # KV v2 stores the actual data under data.data
                secret_data: Dict[str, Union[str, Any]] = response["data"]["data"]
                # If we have a simple key-value pair, return the value
                # Otherwise, return the entire dict as JSON string
                if len(secret_data) == 1 and "value" in secret_data:
                    return str(secret_data["value"])
                elif len(secret_data) == 1:
                    # Return the single value
                    return str(next(iter(secret_data.values())))
                else:
                    # Multiple values, return as JSON string
                    return json.dumps(secret_data)

            return None
        except Exception as e:
            logger.error(f"Failed to retrieve secret {key} from Vault: {e}")
            return None

    def get_service_credentials(self, service: str) -> Dict[str, str]:
        """Retrieve all credentials for a service.

        Args:
            service: The service name (e.g., 'alpaca', 'ib_async')

        Returns:
            Dictionary containing the service's credentials
        """
        try:
            path = self._build_secret_path(f"services/{service}")
            response: Dict[str, Any] = self.client.secrets.kv.v2.read_secret_version(
                path=path
            )

            if response and "data" in response and "data" in response["data"]:
                # KV v2 stores the actual data under data.data
                secret_data: Dict[str, Any] = response["data"]["data"]
                # Convert all values to strings
                return (
                    {k: str(v) for k, v in secret_data.items()} if secret_data else {}
                )

            return {}
        except Exception as e:
            logger.error(
                f"Failed to retrieve credentials for {service} from Vault: {e}"
            )
            return {}

    def validate_service(self, service: str) -> bool:
        """Validate if credentials exist for a service.

        Args:
            service: The service name

        Returns:
            True if credentials are available, False otherwise
        """
        try:
            path = self._build_secret_path(f"services/{service}")
            response = self.client.secrets.kv.v2.read_secret_version(path=path)
            return (
                response is not None
                and "data" in response
                and "data" in response["data"]
            )
        except Exception as e:
            logger.debug(f"Service {service} validation failed: {e}")
            return False
