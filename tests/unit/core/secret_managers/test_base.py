"""Tests for secret manager base class."""

import pytest

from quantchain.core.secret_managers.base import SecretManager


@pytest.mark.unit
class TestSecretManager:
    """Test abstract base class methods."""

    def test_abstract_methods(self):
        """Test that SecretManager cannot be instantiated directly."""
        with pytest.raises(TypeError):
            SecretManager()

    def test_concrete_methods(self):
        """Test concrete methods with a concrete implementation."""
        # Create a concrete implementation for testing
        class ConcreteSecretManager(SecretManager):
            def __init__(self):
                self._credentials = {}

            def get_secret(self, key: str):
                return self._credentials.get(key)

            def get_service_credentials(self, service: str):
                return self._credentials.get(service, {})

            def validate_service(self, service: str):
                return service in self._credentials

        manager = ConcreteSecretManager()
        
        # Test with no credentials
        assert manager.get_api_key("nonexistent") is None
        assert manager.get_api_secret("nonexistent") is None
        assert manager.has_credentials("nonexistent") is False
        
        # Add credentials
        manager._credentials["test_service"] = {"key": "test_key", "secret": "test_secret"}
        
        # Test with credentials
        assert manager.get_api_key("test_service") == "test_key"
        assert manager.get_api_secret("test_service") == "test_secret"
        assert manager.has_credentials("test_service") is True

    def test_get_api_key_none_when_missing(self):
        """Test get_api_key returns None when key is missing."""
        class ConcreteSecretManager(SecretManager):
            def get_secret(self, key: str):
                return None
            def get_service_credentials(self, service: str):
                return {"secret": "test_secret"}
            def validate_service(self, service: str):
                return True

        manager = ConcreteSecretManager()
        assert manager.get_api_key("test_service") is None

    def test_get_api_secret_none_when_missing(self):
        """Test get_api_secret returns None when secret is missing."""
        class ConcreteSecretManager(SecretManager):
            def get_secret(self, key: str):
                return None
            def get_service_credentials(self, service: str):
                return {"key": "test_key"}
            def validate_service(self, service: str):
                return True

        manager = ConcreteSecretManager()
        assert manager.get_api_secret("test_service") is None

    def test_get_api_key_empty_credentials(self):
        """Test get_api_key returns None with empty credentials."""
        class ConcreteSecretManager(SecretManager):
            def get_secret(self, key: str):
                return None
            def get_service_credentials(self, service: str):
                return {}
            def validate_service(self, service: str):
                return False

        manager = ConcreteSecretManager()
        assert manager.get_api_key("test_service") is None

    def test_get_api_secret_empty_credentials(self):
        """Test get_api_secret returns None with empty credentials."""
        class ConcreteSecretManager(SecretManager):
            def get_secret(self, key: str):
                return None
            def get_service_credentials(self, service: str):
                return {}
            def validate_service(self, service: str):
                return False

        manager = ConcreteSecretManager()
        assert manager.get_api_secret("test_service") is None
