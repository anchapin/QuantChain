"""Google Cloud Secret Manager secret manager implementation."""

import json
import logging
import os
from typing import Any, Dict, Optional, Union

try:
    from google.api_core import exceptions as gcp_exceptions
    from google.cloud import secretmanager

    GCP_AVAILABLE = True
except ImportError:
    GCP_AVAILABLE = False

from .base import SecretManager

logger = logging.getLogger(__name__)


class GCPSecretManager(SecretManager):
    """Google Cloud Secret Manager secret manager."""

    def __init__(
        self,
        project_id: Optional[str] = None,
        credentials_path: Optional[str] = None,
        service_account_key: Optional[Dict] = None,
        **kwargs: Dict,
    ) -> None:
        """Initialize GCP Secret Manager.

        Args:
            project_id: GCP project ID (defaults to GCP_PROJECT env var)
            credentials_path: Path to service account JSON file (defaults to GOOGLE_APPLICATION_CREDENTIALS env var)
            service_account_key: Service account key as dict (overrides credentials_path)
            **kwargs: Additional SecretManagerServiceClient parameters
        """
        if not GCP_AVAILABLE:
            raise ImportError(
                "google-cloud-secret-manager library is required for GCP Secret Manager support. "
                "Install with: pip install google-cloud-secret-manager"
            )

        self.project_id = project_id or os.getenv("GCP_PROJECT")

        if not self.project_id:
            raise ValueError(
                "GCP project ID must be provided or set in GCP_PROJECT environment variable"
            )

        # Initialize client
        client_kwargs = {}
        if service_account_key:
            from google.oauth2 import service_account

            credentials = service_account.Credentials.from_service_account_info(
                service_account_key
            )
            client_kwargs["credentials"] = credentials
        elif credentials_path:
            from google.oauth2 import service_account

            credentials = service_account.Credentials.from_service_account_file(
                credentials_path
            )
            client_kwargs["credentials"] = credentials
        elif os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
            # Use the default ADC path
            pass

        client_kwargs.update(kwargs)

        try:
            self.client = secretmanager.SecretManagerServiceClient(**client_kwargs)
            # Test connection by listing a single secret
            parent = f"projects/{self.project_id}"
            self.client.list_secrets(request={"parent": parent, "page_size": 1})
            logger.info(
                f"Connected to GCP Secret Manager for project {self.project_id}"
            )
        except Exception as e:
            raise RuntimeError(f"Failed to connect to GCP Secret Manager: {e}") from e

    def _build_secret_name(self, key: str) -> str:
        """Build the full resource name for a secret.

        Args:
            key: The secret key

        Returns:
            Full GCP secret resource name
        """
        # Strip leading slashes and build resource name
        key = key.lstrip("/")
        # Ensure key starts with "quantchain/" for organization
        if not key.startswith("quantchain/"):
            key = f"quantchain/{key}"
        return f"projects/{self.project_id}/secrets/{key}"

    def _build_secret_version_name(self, key: str, version: str = "latest") -> str:
        """Build the full resource name for a secret version.

        Args:
            key: The secret key
            version: Secret version (default: "latest")

        Returns:
            Full GCP secret version resource name
        """
        secret_name = self._build_secret_name(key)
        return f"{secret_name}/versions/{version}"

    def get_secret(self, key: str) -> Optional[str]:
        """Retrieve a secret by key.

        Args:
            key: The secret key/identifier

        Returns:
            The secret value or None if not found
        """
        try:
            # Ensure key starts with quantchain/ for organization
            if not key.startswith("quantchain/"):
                full_key = f"quantchain/{key}"
            else:
                full_key = key

            name = self._build_secret_version_name(full_key)
            response: Any = self.client.access_secret_version(request={"name": name})

            if response.payload and response.payload.data:
                secret_value: str = response.payload.data.decode("UTF-8")

                # Try to parse as JSON first
                try:
                    secret_data: Dict[str, Union[str, Any]] = json.loads(secret_value)
                    # If it's a simple key-value pair with a single key, return the value
                    if len(secret_data) == 1:
                        return str(next(iter(secret_data.values())))
                    # Otherwise return the entire JSON string
                    return secret_value
                except json.JSONDecodeError:
                    # Not JSON, return as is
                    return secret_value

            return None
        except gcp_exceptions.NotFound:
            logger.debug(f"Secret {key} not found in GCP Secret Manager")
            return None
        except Exception as e:
            logger.error(
                f"Failed to retrieve secret {key} from GCP Secret Manager: {e}"
            )
            return None

    def get_service_credentials(self, service: str) -> Dict[str, str]:
        """Retrieve all credentials for a service.

        Args:
            service: The service name (e.g., 'alpaca', 'ib_async')

        Returns:
            Dictionary containing the service's credentials
        """
        try:
            secret_key = f"quantchain/{service}"
            name = self._build_secret_version_name(secret_key)
            response: Any = self.client.access_secret_version(request={"name": name})

            if response.payload and response.payload.data:
                secret_value: str = response.payload.data.decode("UTF-8")
                try:
                    # Parse as JSON and convert all values to strings
                    secret_data: Dict[str, Union[str, Any]] = json.loads(secret_value)
                    return {k: str(v) for k, v in secret_data.items()}
                except json.JSONDecodeError:
                    # Not JSON, treat entire string as a single credential
                    return {"value": secret_value}

            return {}
        except gcp_exceptions.NotFound:
            logger.debug(f"Credentials for {service} not found in GCP Secret Manager")
            return {}
        except Exception as e:
            logger.error(
                f"Failed to retrieve credentials for {service} from GCP Secret Manager: {e}"
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
            secret_key = f"quantchain/{service}"
            name = self._build_secret_name(secret_key)
            # Try to get the secret metadata (without retrieving the actual value)
            response = self.client.get_secret(request={"name": name})
            return response is not None and not response.state.name == "DESTROYED"
        except gcp_exceptions.NotFound:
            return False
        except Exception as e:
            logger.debug(f"Service {service} validation failed: {e}")
            return False
