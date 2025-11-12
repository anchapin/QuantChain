# Auto-generated test file for vault.py
# Generated using Z.AI GLM-4.6 API

import json
import os
import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch

# Add the parent directory to the path to import the module
sys.path.insert(0, str(Path(__file__).parent.parent))

"""Test cases for VaultSecretManager."""

from vault import VaultSecretManager


class TestVaultSecretManagerInit:
    """Test cases for VaultSecretManager initialization."""

    @patch("vault.hvac.Client")
    @patch.dict(
        os.environ,
        {"VAULT_ADDR": "https://vault.example.com", "VAULT_TOKEN": "test-token"},
    )
    def test_init_with_env_vars(self, mock_client_class):
        """Test initialization using environment variables."""
        mock_client = Mock()
        mock_client.is_authenticated.return_value = True
        mock_client_class.return_value = mock_client

        manager = VaultSecretManager()

        assert manager.url == "https://vault.example.com"
        assert manager.token == "test-token"
        assert manager.namespace is None
        assert manager.verify is True
        assert manager.mount_point == "secret"
        mock_client_class.assert_called_once_with(
            url="https://vault.example.com",
            token="test-token",
            namespace=None,
            verify=True,
        )

    @patch("vault.hvac.Client")
    def test_init_with_parameters(self, mock_client_class):
        """Test initialization with explicit parameters."""
        mock_client = Mock()
        mock_client.is_authenticated.return_value = True
        mock_client_class.return_value = mock_client

        manager = VaultSecretManager(
            url="https://custom.vault.com",
            token="custom-token",
            namespace="test-ns",
            verify=False,
            mount_point="custom-mount",
            timeout=30,
        )

        assert manager.url == "https://custom.vault.com"
        assert manager.token == "custom-token"
        assert manager.namespace == "test-ns"
        assert manager.verify is False
        assert manager.mount_point == "custom-mount"
        mock_client_class.assert_called_once_with(
            url="https://custom.vault.com",
            token="custom-token",
            namespace="test-ns",
            verify=False,
            timeout=30,
        )

    @patch("vault.hvac.Client")
    @patch.dict(os.environ, {}, clear=True)
    def test_init_missing_url(self, mock_client_class):
        """Test initialization failure when URL is missing."""
        with pytest.raises(ValueError, match="Vault URL must be provided"):
            VaultSecretManager(token="token")

    @patch("vault.hvac.Client")
    @patch.dict(os.environ, {"VAULT_ADDR": "https://vault.example.com"}, clear=True)
    def test_init_missing_token(self, mock_client_class):
        """Test initialization failure when token is missing."""
        with pytest.raises(ValueError, match="Vault token must be provided"):
            VaultSecretManager()

    @patch("vault.hvac.Client")
    def test_init_authentication_failure(self, mock_client_class):
        """Test initialization failure when authentication fails."""
        mock_client = Mock()
        mock_client.is_authenticated.return_value = False
        mock_client_class.return_value = mock_client

        with pytest.raises(RuntimeError, match="Failed to authenticate with Vault"):
            VaultSecretManager(url="https://vault.com", token="token")

    @patch("vault.hvac.Client")
    def test_init_with_kwargs(self, mock_client_class):
        """Test initialization with additional hvac.Client parameters."""
        mock_client = Mock()
        mock_client.is_authenticated.return_value = True
        mock_client_class.return_value = mock_client

        VaultSecretManager(
            url="https://vault.com",
            token="token",
            cert=("client.crt", "client.key"),
            timeout=60,
        )

        mock_client_class.assert_called_once_with(
            url="https://vault.com",
            token="token",
            namespace=None,
            verify=True,
            cert=("client.crt", "client.key"),
            timeout=60,
        )


class TestVaultSecretManagerBuildSecretPath:
    """Test cases for _build_secret_path method."""

    def test_build_secret_path_simple(self):
        """Test building path with simple key."""
        manager = VaultSecretManager(url="https://vault.com", token="token")
        manager.client = Mock(is_authenticated=lambda: True)

        path = manager._build_secret_path("mysecret")
        assert path == "secret/data/mysecret"

    def test_build_secret_path_with_leading_slash(self):
        """Test building path with key that has leading slash."""
        manager = VaultSecretManager(url="https://vault.com", token="token")
        manager.client = Mock(is_authenticated=lambda: True)

        path = manager._build_secret_path("/mysecret")
        assert path == "secret/data/mysecret"

    def test_build_secret_path_with_nested_key(self):
        """Test building path with nested key."""
        manager = VaultSecretManager(url="https://vault.com", token="token")
        manager.client = Mock(is_authenticated=lambda: True)

        path = manager._build_secret_path("path/to/secret")
        assert path == "secret/data/path/to/secret"

    def test_build_secret_path_custom_mount(self):
        """Test building path with custom mount point."""
        manager = VaultSecretManager(
            url="https://vault.com", token="token", mount_point="custom-mount"
        )
        manager.client = Mock(is_authenticated=lambda: True)

        path = manager._build_secret_path("mysecret")
        assert path == "custom-mount/data/mysecret"

    def test_build_secret_path_multiple_leading_slashes(self):
        """Test building path with multiple leading slashes."""
        manager = VaultSecretManager(url="https://vault.com", token="token")
        manager.client = Mock(is_authenticated=lambda: True)

        path = manager._build_secret_path("///mysecret")
        assert path == "secret/data/mysecret"


class TestVaultSecretManagerGetSecret:
    """Test cases for get_secret method."""

    @patch("vault.hvac.Client")
    def test_get_secret_single_value(self, mock_client_class):
        """Test retrieving a secret with single 'value' key."""
        mock_client = Mock()
        mock_client.is_authenticated.return_value = True
        mock_client_class.return_value = mock_client

        mock_client.secrets.kv.v2.read_secret_version.return_value = {
            "data": {"data": {"value": "secret-value"}}
        }

        manager = VaultSecretManager(url="https://vault.com", token="token")
        result = manager.get_secret("mysecret")

        assert result == "secret-value"
        mock_client.secrets.kv.v2.read_secret_version.assert_called_once_with(
            path="secret/data/mysecret"
        )

    @patch("vault.hvac.Client")
    def test_get_secret_single_non_value_key(self, mock_client_class):
        """Test retrieving a secret with single non-'value' key."""
        mock_client = Mock()
        mock_client.is_authenticated.return_value = True
        mock_client_class.return_value = mock_client

        mock_client.secrets.kv.v2.read_secret_version.return_value = {
            "data": {"data": {"password": "secret-password"}}
        }

        manager = VaultSecretManager(url="https://vault.com", token="token")
        result = manager.get_secret("mysecret")

        assert result == "secret-password"

    @patch("vault.hvac.Client")
    def test_get_secret_multiple_values(self, mock_client_class):
        """Test retrieving a secret with multiple key-value pairs."""
        mock_client = Mock()
        mock_client.is_authenticated.return_value = True
        mock_client_class.return_value = mock_client

        secret_data = {"username": "user1", "password": "pass1", "host": "example.com"}
        mock_client.secrets.kv.v2.read_secret_version.return_value = {
            "data": {"data": secret_data}
        }

        manager = VaultSecretManager(url="https://vault.com", token="token")
        result = manager.get_secret("mysecret")

        assert result == json.dumps(secret_data)

    @patch("vault.hvac.Client")
    def test_get_secret_not_found(self, mock_client_class):
        """Test retrieving a non-existent secret."""
        mock_client = Mock()
        mock_client.is_authenticated.return_value = True
        mock_client_class.return_value = mock_client

        mock_client.secrets.kv.v2.read_secret_version.return_value = None

        manager = VaultSecretManager(url="https://vault.com", token="token")
        result = manager.get_secret("nonexistent")

        assert result is None

    @patch("vault.hvac.Client")
    def test_get_secret_empty_response(self, mock_client_class):
        """Test retrieving a secret with empty response."""
        mock_client = Mock()
        mock_client.is_authenticated.return_value = True
        mock_client_class.return_value = mock_client

        mock_client.secrets.kv.v2.read_secret_version.return_value = {}

        manager = VaultSecretManager(url="https://vault.com", token="token")
        result = manager.get_secret("empty")

        assert result is None

    @patch("vault.hvac.Client")
    def test_get_secret_exception(self, mock_client_class):
        """Test retrieving a secret when an exception occurs."""
        mock_client = Mock()
        mock_client.is_authenticated.return_value = True
        mock_client_class.return_value = mock_client

        mock_client.secrets.kv.v2.read_secret_version.side_effect = Exception(
            "Vault error"
        )

        manager = VaultSecretManager(url="https://vault.com", token="token")
        result = manager.get_secret("error-secret")

        assert result is None

    @patch("vault.hvac.Client")
    def test_get_secret_with_custom_mount(self, mock_client_class):
        """Test retrieving a secret with custom mount point."""
        mock_client = Mock()
        mock_client.is_authenticated.return_value = True
        mock_client_class.return_value = mock_client

        mock_client.secrets.kv.v2.read_secret_version.return_value = {
            "data": {"data": {"value": "custom-value"}}
        }

        manager = VaultSecretManager(
            url="https://vault.com", token="token", mount_point="custom"
        )
        result = manager.get_secret("mysecret")

        assert result == "custom-value"
        mock_client.secrets.kv.v2.read_secret_version.assert_called_once_with(
            path="custom/data/mysecret"
        )


class TestVaultSecretManagerGetServiceCredentials:
    """Test cases for get_service_credentials method."""

    @patch("vault.hvac.Client")
    def test_get_service_credentials_success(self, mock_client_class):
        """Test retrieving service credentials successfully."""
        mock_client = Mock()
        mock_client.is_authenticated.return_value = True
        mock_client_class.return_value = mock_client

        credentials = {
            "api_key": "key123",
            "api_secret": "secret456",
            "endpoint": "https://api.example.com",
        }
        mock_client.secrets.kv.v2.read_secret_version.return_value = {
            "data": {"data": credentials}
        }

        manager = VaultSecretManager(url="https://vault.com", token="token")
        result = manager.get_service_credentials("alpaca")

        assert result == {
            "api_key": "key123",
            "api_secret": "secret456",
            "endpoint": "https://api.example.com",
        }
        mock_client.secrets.kv.v2.read_secret_version.assert_called_once_with(
            path="secret/data/services/alpaca"
        )

    @patch("vault.hvac.Client")
    def test_get_service_credentials_empty(self, mock_client_class):
        """Test retrieving service credentials when none exist."""
        mock_client = Mock()
        mock_client.is_authenticated.return_value = True
        mock_client_class.return_value = mock_client

        mock_client.secrets.kv.v2.read_secret_version.return_value = {
            "data": {"data": {}}
        }

        manager = VaultSecretManager(url="https://vault.com", token="token")
        result = manager.get_service_credentials("nonexistent")

        assert result == {}

    @patch("vault.hvac.Client")
    def test_get_service_credentials_not_found(self, mock_client_class):
        """Test retrieving credentials for non-existent service."""
        mock_client = Mock()
        mock_client.is_authenticated.return_value = True
        mock_client_class.return_value = mock_client

        mock_client.secrets.kv.v2.read_secret_version.return_value = None

        manager = VaultSecretManager(url="https://vault.com", token="token")
        result = manager.get_service_credentials("nonexistent")

        assert result == {}

    @patch("vault.hvac.Client")
    def test_get_service_credentials_type_conversion(self, mock_client_class):
        """Test that all credential values are converted to strings."""
        mock_client = Mock()
        mock_client.is_authenticated.return_value = True
        mock_client_class.return_value = mock_client

        credentials = {
            "port": 8080,
            "timeout": 30.5,
            "enabled": True,
            "name": "service",
        }
        mock_client.secrets.kv.v2.read_secret_version.return_value = {
            "data": {"data": credentials}
        }

        manager = VaultSecretManager(url="https://vault.com", token="token")
        result = manager.get_service_credentials("service")

        assert result == {
            "port": "8080",
            "timeout": "30.5",
            "enabled": "True",
            "name": "service",
        }

    @patch("vault.hvac.Client")
    def test_get_service_credentials_exception(self, mock_client_class):
        """Test retrieving service credentials when an exception occurs."""
        mock_client = Mock()
        mock_client.is_authenticated.return_value = True
        mock_client_class.return_value = mock_client

        mock_client.secrets.kv.v2.read_secret_version.side_effect = Exception(
            "Connection error"
        )

        manager = VaultSecretManager(url="https://vault.com", token="token")
        result = manager.get_service_credentials("error-service")

        assert result == {}

    @patch("vault.hvac.Client")
    def test_get_service_credentials_with_custom_mount(self, mock_client_class):
        """Test retrieving service credentials with custom mount point."""
        mock_client = Mock()
        mock_client.is_authenticated.return_value = True
        mock_client_class.return_value = mock_client

        mock_client.secrets.kv.v2.read_secret_version.return_value = {
            "data": {"data": {"key": "value"}}
        }

        manager = VaultSecretManager(
            url="https://vault.com", token="token", mount_point="secrets"
        )
        manager.get_service_credentials("service")

        mock_client.secrets.kv.v2.read_secret_version.assert_called_once_with(
            path="secrets/data/services/service"
        )


class TestVaultSecretManagerValidateService:
    """Test cases for validate_service method."""

    @patch("vault.hvac.Client")
    def test_validate_service_exists(self, mock_client_class):
        """Test validating a service that exists."""
        mock_client = Mock()
        mock_client.is_authenticated.return_value = True
        mock_client_class.return_value = mock_client

        mock_client.secrets.kv.v2.read_secret_version.return_value = {
            "data": {"data": {"key": "value"}}
        }

        manager = VaultSecretManager(url="https://vault.com", token="token")
        result = manager.validate_service("alpaca")

        assert result is True
        mock_client.secrets.kv.v2.read_secret_version.assert_called_once_with(
            path="secret/data/services/alpaca"
        )

    @patch("vault.hvac.Client")
    def test_validate_service_not_exists(self, mock_client_class):
        """Test validating a service that doesn't exist."""
        mock_client = Mock()
        mock_client.is_authenticated.return_value = True
        mock_client_class.return_value = mock_client

        mock_client.secrets.kv.v2.read_secret_version.return_value = None

        manager = VaultSecretManager(url="https://vault.com", token="token")
        result = manager.validate_service("nonexistent")

        assert result is False

    @patch("vault.hvac.Client")
    def test_validate_service_empty_response(self, mock_client_class):
        """Test validating a service with empty response."""
        mock_client = Mock()
        mock_client.is_authenticated.return_value = True
        mock_client_class.return_value = mock_client

        mock_client.secrets.kv.v2.read_secret_version.return_value = {}

        manager = VaultSecretManager(url="https://vault.com", token="token")
        result = manager.validate_service("empty")

        assert result is False

    @patch("vault.hvac.Client")
    def test_validate_service_malformed_response(self, mock_client_class):
        """Test validating a service with malformed response."""
        mock_client = Mock()
        mock_client.is_authenticated.return_value = True
        mock_client_class.return_value = mock_client

        mock_client.secrets.kv.v2.read_secret_version.return_value = {
            "data": {}  # Missing 'data' key
        }

        manager = VaultSecretManager(url="https://vault.com", token="token")
        result = manager.validate_service("malformed")

        assert result is False

    @patch("vault.hvac.Client")
    def test_validate_service_exception(self, mock_client_class):
        """Test validating a service when an exception occurs."""
        mock_client = Mock()
        mock_client.is_authenticated.return_value = True
        mock_client_class.return_value = mock_client

        mock_client.secrets.kv.v2.read_secret_version.side_effect = Exception(
            "Vault error"
        )

        manager = VaultSecretManager(url="https://vault.com", token="token")
        result = manager.validate_service("error-service")

        assert result is False

    @patch("vault.hvac.Client")
    def test_validate_service_with_custom_mount(self, mock_client_class):
        """Test validating a service with custom mount point."""
        mock_client = Mock()
        mock_client.is_authenticated.return_value = True
        mock_client_class.return_value = mock_client
