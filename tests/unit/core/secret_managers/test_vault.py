"""Comprehensive tests for HashiCorp Vault secret manager implementation."""

import json
import os
import unittest.mock

import pytest

from quantchain.core.secret_managers.vault import VaultSecretManager


@pytest.fixture


def mock_hvac():
    """Mock hvac module."""
    mock = unittest.mock.MagicMock()
    return mock


@pytest.fixture


def mock_client():
    """Mock hvac client."""
    client = unittest.mock.MagicMock()
    client.is_authenticated.return_value = True
    client.secrets.kv.v2.read_secret_version.return_value = {
        "data": {"data": {"value": "test_secret_value"}}
    }
    return client


@pytest.mark.unit


class TestVaultSecretManager:
    """Test Vault Secret Manager implementation."""

    @unittest.mock.patch("quantchain.core.secret_managers.vault.hvac.Client")


def test_init_with_explicit_values(self, mock_client_class) -> None:
        """Test initialization with explicit values."""
        mock_client = unittest.mock.MagicMock()
        mock_client.is_authenticated.return_value = True
        mock_client_class.return_value = mock_client

        manager = VaultSecretManager(
            url="https://vault.example.com",
            token="test-token",
            namespace="test-ns",
            verify=False,
            mount_point="custom-mount",
        )

        assert manager.url == "https://vault.example.com"
        assert manager.token == "test-token"
        assert manager.namespace == "test-ns"
        assert manager.verify is False
        assert manager.mount_point == "custom-mount"



def test_init_with_env_values(self) -> None:
        """Test initialization with environment variables."""
        with unittest.mock.patch.dict(
            os.environ, {"VAULT_ADDR": "http://vault:8200", "VAULT_TOKEN": "env-token"}
        ), unittest.mock.patch(
            "quantchain.core.secret_managers.vault.hvac.Client"
        ) as mock_client_class:
            mock_client = unittest.mock.MagicMock()
            mock_client.is_authenticated.return_value = True
            mock_client_class.return_value = mock_client

            manager = VaultSecretManager()

            assert manager.url == "http://vault:8200"
            assert manager.token == "env-token"



def test_init_missing_url(self) -> None:
        """Test initialization fails without URL."""
        with unittest.mock.patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="Vault URL must be provided"):
                VaultSecretManager(token="test-token")



def test_init_missing_token(self) -> None:
        """Test initialization fails without token."""
        with unittest.mock.patch.dict(
            os.environ, {"VAULT_ADDR": "http://vault:8200"}, clear=True
        ), pytest.raises(ValueError, match="Vault token must be provided"):
            VaultSecretManager()

    @unittest.mock.patch("quantchain.core.secret_managers.vault.hvac.Client")


def test_init_authentication_failure(self, mock_client_class) -> None:
        """Test initialization fails authentication."""
        mock_client = unittest.mock.MagicMock()
        mock_client.is_authenticated.return_value = False
        mock_client_class.return_value = mock_client

        with pytest.raises(RuntimeError, match="Failed to authenticate with Vault"):
            VaultSecretManager(url="http://vault:8200", token="invalid-token")

    @unittest.mock.patch("quantchain.core.secret_managers.vault.hvac.Client")


def test_init_connection_error(self, mock_client_class) -> None:
        """Test initialization with connection error."""
        mock_client_class.side_effect = Exception("Connection failed")

        with pytest.raises(Exception, match="Connection failed"):
            VaultSecretManager(url="http://vault:8200", token="test-token")



def test_build_secret_path(self) -> None:
        """Test building secret path."""
        with unittest.mock.patch(
            "quantchain.core.secret_managers.vault.hvac.Client"
        ) as mock_client_class:
            mock_client = unittest.mock.MagicMock()
            mock_client.is_authenticated.return_value = True
            mock_client_class.return_value = mock_client

            manager = VaultSecretManager(
                url="http://vault:8200", token="test-token", mount_point="custom-mount"
            )

            # Test various key formats
            assert manager._build_secret_path("test") == "custom-mount/data/test"
            assert manager._build_secret_path("/test") == "custom-mount/data/test"
            assert (
                manager._build_secret_path("path/to/secret")
                == "custom-mount/data/path/to/secret"
            )
            assert (
                manager._build_secret_path("/path/to/secret")
                == "custom-mount/data/path/to/secret"
            )

    @unittest.mock.patch("quantchain.core.secret_managers.vault.hvac.Client")


def test_get_secret_success_single_value(self, mock_client_class) -> None:
        """Test successful secret retrieval with single value."""
        mock_client = unittest.mock.MagicMock()
        mock_client.is_authenticated.return_value = True
        mock_client.secrets.kv.v2.read_secret_version.return_value = {
            "data": {"data": {"value": "test_secret_value"}}
        }
        mock_client_class.return_value = mock_client

        manager = VaultSecretManager(url="http://vault:8200", token="test-token")
        result = manager.get_secret("test_secret")
        assert result == "test_secret_value"

    @unittest.mock.patch("quantchain.core.secret_managers.vault.hvac.Client")


def test_get_secret_success_single_non_value(self, mock_client_class) -> None:
        """Test successful secret retrieval with single non-value key."""
        mock_client = unittest.mock.MagicMock()
        mock_client.is_authenticated.return_value = True
        mock_client.secrets.kv.v2.read_secret_version.return_value = {
            "data": {"data": {"api_key": "test_key"}}
        }
        mock_client_class.return_value = mock_client

        manager = VaultSecretManager(url="http://vault:8200", token="test-token")
        result = manager.get_secret("test_secret")
        assert result == "test_key"

    @unittest.mock.patch("quantchain.core.secret_managers.vault.hvac.Client")


def test_get_secret_success_multiple_values(self, mock_client_class) -> None:
        """Test successful secret retrieval with multiple values."""
        mock_client = unittest.mock.MagicMock()
        mock_client.is_authenticated.return_value = True
        mock_client.secrets.kv.v2.read_secret_version.return_value = {
            "data": {"data": {"key1": "value1", "key2": "value2"}}
        }
        mock_client_class.return_value = mock_client

        manager = VaultSecretManager(url="http://vault:8200", token="test-token")
        result = manager.get_secret("test_secret")
        # Should return JSON string for multiple values
        assert json.loads(result) == {"key1": "value1", "key2": "value2"}

    @unittest.mock.patch("quantchain.core.secret_managers.vault.hvac.Client")


def test_get_secret_no_data_response(self, mock_client_class) -> None:
        """Test secret retrieval with no data in response."""
        mock_client = unittest.mock.MagicMock()
        mock_client.is_authenticated.return_value = True
        mock_client.secrets.kv.v2.read_secret_version.return_value = {}
        mock_client_class.return_value = mock_client

        manager = VaultSecretManager(url="http://vault:8200", token="test-token")
        result = manager.get_secret("test_secret")
        assert result is None

    @unittest.mock.patch("quantchain.core.secret_managers.vault.hvac.Client")


def test_get_secret_no_nested_data(self, mock_client_class) -> None:
        """Test secret retrieval with no nested data."""
        mock_client = unittest.mock.MagicMock()
        mock_client.is_authenticated.return_value = True
        mock_client.secrets.kv.v2.read_secret_version.return_value = {"data": {}}
        mock_client_class.return_value = mock_client

        manager = VaultSecretManager(url="http://vault:8200", token="test-token")
        result = manager.get_secret("test_secret")
        assert result is None

    @unittest.mock.patch("quantchain.core.secret_managers.vault.hvac.Client")


def test_get_secret_exception(self, mock_client_class) -> None:
        """Test secret retrieval with exception."""
        mock_client = unittest.mock.MagicMock()
        mock_client.is_authenticated.return_value = True
        mock_client.secrets.kv.v2.read_secret_version.side_effect = Exception(
            "Vault error"
        )
        mock_client_class.return_value = mock_client

        manager = VaultSecretManager(url="http://vault:8200", token="test-token")
        result = manager.get_secret("test_secret")
        assert result is None

    @unittest.mock.patch("quantchain.core.secret_managers.vault.hvac.Client")


def test_get_service_credentials_success(self, mock_client_class) -> None:
        """Test successful service credentials retrieval."""
        mock_client = unittest.mock.MagicMock()
        mock_client.is_authenticated.return_value = True
        mock_client.secrets.kv.v2.read_secret_version.return_value = {
            "data": {"data": {"api_key": "key123", "api_secret": "secret123"}}
        }
        mock_client_class.return_value = mock_client

        manager = VaultSecretManager(url="http://vault:8200", token="test-token")
        result = manager.get_service_credentials("alpaca")
        assert result == {"api_key": "key123", "api_secret": "secret123"}
        # Verify correct path was used
        mock_client.secrets.kv.v2.read_secret_version.assert_called_with(
            path="secret/data/services/alpaca"
        )

    @unittest.mock.patch("quantchain.core.secret_managers.vault.hvac.Client")


def test_get_service_credentials_empty_data(self, mock_client_class) -> None:
        """Test service credentials retrieval with empty data."""
        mock_client = unittest.mock.MagicMock()
        mock_client.is_authenticated.return_value = True
        mock_client.secrets.kv.v2.read_secret_version.return_value = {
            "data": {"data": {}}
        }
        mock_client_class.return_value = mock_client

        manager = VaultSecretManager(url="http://vault:8200", token="test-token")
        result = manager.get_service_credentials("alpaca")
        assert result == {}

    @unittest.mock.patch("quantchain.core.secret_managers.vault.hvac.Client")


def test_get_service_credentials_exception(self, mock_client_class) -> None:
        """Test service credentials retrieval with exception."""
        mock_client = unittest.mock.MagicMock()
        mock_client.is_authenticated.return_value = True
        mock_client.secrets.kv.v2.read_secret_version.side_effect = Exception(
            "Vault error"
        )
        mock_client_class.return_value = mock_client

        manager = VaultSecretManager(url="http://vault:8200", token="test-token")
        result = manager.get_service_credentials("alpaca")
        assert result == {}

    @unittest.mock.patch("quantchain.core.secret_managers.vault.hvac.Client")


def test_validate_service_success(self, mock_client_class) -> None:
        """Test successful service validation."""
        mock_client = unittest.mock.MagicMock()
        mock_client.is_authenticated.return_value = True
        mock_client.secrets.kv.v2.read_secret_version.return_value = {
            "data": {"data": {"api_key": "test_key"}}
        }
        mock_client_class.return_value = mock_client

        manager = VaultSecretManager(url="http://vault:8200", token="test-token")
        result = manager.validate_service("alpaca")
        assert result is True

    @unittest.mock.patch("quantchain.core.secret_managers.vault.hvac.Client")


def test_validate_service_no_data_response(self, mock_client_class) -> None:
        """Test service validation with no data in response."""
        mock_client = unittest.mock.MagicMock()
        mock_client.is_authenticated.return_value = True
        mock_client.secrets.kv.v2.read_secret_version.return_value = {}
        mock_client_class.return_value = mock_client

        manager = VaultSecretManager(url="http://vault:8200", token="test-token")
        result = manager.validate_service("alpaca")
        assert result is False

    @unittest.mock.patch("quantchain.core.secret_managers.vault.hvac.Client")


def test_validate_service_exception(self, mock_client_class) -> None:
        """Test service validation with exception."""
        mock_client = unittest.mock.MagicMock()
        mock_client.is_authenticated.return_value = True
        mock_client.secrets.kv.v2.read_secret_version.side_effect = Exception(
            "Vault error"
        )
        mock_client_class.return_value = mock_client

        manager = VaultSecretManager(url="http://vault:8200", token="test-token")
        result = manager.validate_service("alpaca")
        assert result is False

    @unittest.mock.patch("quantchain.core.secret_managers.vault.hvac.Client")


def test_custom_mount_point(self, mock_client_class) -> None:
        """Test using custom mount point."""
        mock_client = unittest.mock.MagicMock()
        mock_client.is_authenticated.return_value = True
        mock_client.secrets.kv.v2.read_secret_version.return_value = {
            "data": {"data": {"value": "test_value"}}
        }
        mock_client_class.return_value = mock_client

        manager = VaultSecretManager(
            url="http://vault:8200", token="test-token", mount_point="custom-mount"
        )

        # Test get_secret
        manager.get_secret("test_secret")
        mock_client.secrets.kv.v2.read_secret_version.assert_called_with(
            path="custom-mount/data/test_secret"
        )

        # Test get_service_credentials
        manager.get_service_credentials("alpaca")
        mock_client.secrets.kv.v2.read_secret_version.assert_called_with(
            path="custom-mount/data/services/alpaca"
        )

        # Test validate_service
        manager.validate_service("alpaca")
        mock_client.secrets.kv.v2.read_secret_version.assert_called_with(
            path="custom-mount/data/services/alpaca"
        )

    @unittest.mock.patch("quantchain.core.secret_managers.vault.hvac.Client")


def test_with_ssl_verify_disabled(self, mock_client_class) -> None:
        """Test initialization with SSL verification disabled."""
        mock_client = unittest.mock.MagicMock()
        mock_client.is_authenticated.return_value = True
        mock_client_class.return_value = mock_client

        manager = VaultSecretManager(
            url="https://vault.example.com", token="test-token", verify=False
        )
        # Verify hvac.Client was called with verify=False
        mock_client_class.assert_called_with(
            url="https://vault.example.com",
            token="test-token",
            namespace=None,
            verify=False,
        )
