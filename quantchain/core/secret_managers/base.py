"""Abstract base class for secret managers."""

from abc import ABC, abstractmethod
from typing import Dict, Optional


class SecretManager(ABC):
    """Abstract base class for secret management implementations."""

    @abstractmethod
    def get_secret(self, key: str) -> Optional[str]:
        """Retrieve a secret by key.

        Args:
            key: The secret key/identifier

        Returns:
            The secret value or None if not found
        """

    @abstractmethod
    def get_service_credentials(self, service: str) -> Dict[str, str]:
        """Retrieve all credentials for a service.

        Args:
            service: The service name (e.g., 'alpaca', 'ib_async')

        Returns:
            Dictionary containing the service's credentials
        """

    @abstractmethod
    def validate_service(self, service: str) -> bool:
        """Validate if credentials exist for a service.

        Args:
            service: The service name

        Returns:
            True if credentials are available, False otherwise
        """

    def get_api_key(self, service: str) -> Optional[str]:
        """Convenience method to get API key for a service.

        Args:
            service: The service name

        Returns:
            The API key or None if not found
        """
        creds = self.get_service_credentials(service)
        return creds.get("key")

    def get_api_secret(self, service: str) -> Optional[str]:
        """Convenience method to get API secret for a service.

        Args:
            service: The service name

        Returns:
            The API secret or None if not found
        """
        creds = self.get_service_credentials(service)
        return creds.get("secret")

    def has_credentials(self, service: str) -> bool:
        """Check if any credentials exist for a service.

        Args:
            service: The service name

        Returns:
            True if at least one credential exists
        """
        creds = self.get_service_credentials(service)
        return bool(creds)
