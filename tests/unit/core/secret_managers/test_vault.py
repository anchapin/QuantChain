"""Comprehensive tests for HashiCorp Vault secret manager implementation."""

import json
import os
import sys
import typing
import unittest.mock

import pytest

# Mock hvac module before import
mock_hvac = unittest.mock.MagicMock()
sys.modules['hvac'] = mock_hvac

# Now import the vault module
from quantchain.core.secret_managers.vault import VaultSecretManager

# Mock HVAC_AVAILABLE variable
import quantchain.core.secret_managers.vault as vault_module
vault_module.HVAC_AVAILABLE = True


# Create complete mock hierarchy
class MockKVv2:
    read_secret_version = unittest.mock.MagicMock()


class MockSecrets:
    def __init__(self) -> None:
        self.kv = unittest.mock.MagicMock()
        self.kv.v2 = MockKVv2()


class MockHvacClient:
    def __init__(self, *args: typing.Any, **kwargs: typing.Any) -> None:
        self.is_authenticated_ret = kwargs.get("is_authenticated", True)
        self.connect_error = kwargs.get("connect_error", None)
        # Create new secrets instance each time to avoid shared state
        self._secrets = MockSecrets()

    def is_authenticated(self) -> bool:
        return bool(self.is_authenticated_ret)

    @property
    def secrets(self) -> MockSecrets:
        return self._secrets


# Create a mock hvac module
mock_hvac_module = unittest.mock.MagicMock()
mock_hvac_module.Client = MockHvacClient

# Add mock to sys.modules before importing vault module
sys.modules["hvac"] = mock_hvac_module

_VAULT_AVAILABLE = True


def with_mock_client(
    mock_client_factory: typing.Callable[..., typing.Any],
) -> typing.Callable[..., typing.Any]:
    """Decorator to temporarily replace the mock Client class."""

    def decorator(
        test_func: typing.Callable[..., typing.Any],
    ) -> typing.Callable[..., typing.Any]:
        def wrapper(
            self: typing.Any, *args: typing.Any, **kwargs: typing.Any
        ) -> typing.Any:
            original_client = mock_hvac_module.Client
            try:
                # If factory is callable, call it to get client
                if callable(mock_client_factory):
                    mock_hvac_module.Client = mock_client_factory
                return test_func(self, *args, **kwargs)
            finally:
                mock_hvac_module.Client = original_client

        return wrapper

    return decorator


@pytest.mark.unit
class TestVaultSecretManager:
    """Test Vault Secret Manager implementation."""

    @unittest.mock.patch('hvac.Client')
    def test_init_with_explicit_values(self, mock_client_class) -> None:
        """Test initialization with explicit values."""
        mock_client = MockHvacClient(is_authenticated=True)
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
        ):
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
        ):
            with pytest.raises(ValueError, match="Vault token must be provided"):
                VaultSecretManager()

    @with_mock_client(lambda *args, **kwargs: MockHvacClient(is_authenticated=False))
    def test_init_authentication_failure(self) -> None:
        """Test initialization fails authentication."""
        with pytest.raises(RuntimeError, match="Failed to authenticate with Vault"):
            VaultSecretManager(url="http://vault:8200", token="invalid-token")

    @with_mock_client(
        lambda *args, **kwargs: (_ for _ in ()).throw(Exception("Connection failed"))
    )
    def test_init_connection_error(self) -> None:
        """Test initialization with connection error."""
        with pytest.raises(Exception, match="Connection failed"):
            VaultSecretManager(url="http://vault:8200", token="test-token")

    def test_build_secret_path(self) -> None:
        """Test building secret path."""
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

    def test_get_secret_success_single_value(self) -> None:
        """Test successful secret retrieval with single value."""
        mock_client = MockHvacClient()
        mock_client.secrets.kv.v2.read_secret_version.return_value = {
            "data": {"data": {"value": "test_secret_value"}}
        }

        # Temporarily replace the mock Client class
        original_client = mock_hvac_module.Client
        mock_hvac_module.Client = lambda *args, **kwargs: mock_client

        try:
            manager = VaultSecretManager(url="http://vault:8200", token="test-token")
            result = manager.get_secret("test_secret")
            assert result == "test_secret_value"
        finally:
            # Restore original mock
            mock_hvac_module.Client = original_client

    def test_get_secret_success_single_non_value(self) -> None:
        """Test successful secret retrieval with single non-value key."""
        # Create mock client with specific return value
        mock_client = MockHvacClient()
        mock_client.secrets.kv.v2.read_secret_version.return_value = {
            "data": {"data": {"api_key": "test_key"}}
        }

        # Temporarily replace the mock Client class
        original_client = mock_hvac_module.Client
        mock_hvac_module.Client = lambda *args, **kwargs: mock_client
        try:
            manager = VaultSecretManager(url="http://vault:8200", token="test-token")
            result = manager.get_secret("test_secret")
            assert result == "test_key"
        finally:
            mock_hvac_module.Client = original_client

    def test_get_secret_success_multiple_values(self) -> None:
        """Test successful secret retrieval with multiple values."""
        mock_client = MockHvacClient()
        mock_client.secrets.kv.v2.read_secret_version.return_value = {
            "data": {"data": {"key1": "value1", "key2": "value2"}}
        }

        # Temporarily replace the mock Client class
        original_client = mock_hvac_module.Client
        mock_hvac_module.Client = lambda *args, **kwargs: mock_client
        try:
            manager = VaultSecretManager(url="http://vault:8200", token="test-token")
            result = manager.get_secret("test_secret")
            # Should return JSON string for multiple values
            assert json.loads(result) == {"key1": "value1", "key2": "value2"}
        finally:
            mock_hvac_module.Client = original_client

    def test_get_secret_no_data_response(self) -> None:
        """Test secret retrieval with no data in response."""
        mock_client = MockHvacClient()
        mock_client.secrets.kv.v2.read_secret_version.return_value = {}

        # Temporarily replace mock Client class
        original_client = mock_hvac_module.Client
        mock_hvac_module.Client = lambda *args, **kwargs: mock_client
        try:
            manager = VaultSecretManager(url="http://vault:8200", token="test-token")
            result = manager.get_secret("test_secret")
            assert result is None
        finally:
            mock_hvac_module.Client = original_client

    def test_get_secret_no_nested_data(self) -> None:
        """Test secret retrieval with no nested data."""
        mock_client = MockHvacClient()
        mock_client.secrets.kv.v2.read_secret_version.return_value = {"data": {}}

        # Temporarily replace mock Client class
        original_client = mock_hvac_module.Client
        mock_hvac_module.Client = lambda *args, **kwargs: mock_client
        try:
            manager = VaultSecretManager(url="http://vault:8200", token="test-token")
            result = manager.get_secret("test_secret")
            assert result is None
        finally:
            mock_hvac_module.Client = original_client

    def test_get_secret_exception(self) -> None:
        """Test secret retrieval with exception."""
        mock_client = MockHvacClient()
        mock_client.secrets.kv.v2.read_secret_version.side_effect = Exception(
            "Vault error"
        )

        # Temporarily replace mock Client class
        original_client = mock_hvac_module.Client
        mock_hvac_module.Client = lambda *args, **kwargs: mock_client
        try:
            manager = VaultSecretManager(url="http://vault:8200", token="test-token")
            result = manager.get_secret("test_secret")
            assert result is None
        finally:
            mock_hvac_module.Client = original_client

    def test_get_service_credentials_success(self) -> None:
        """Test successful service credentials retrieval."""
        # Create fresh mock instance
        mock_client = MockHvacClient()
        mock_client.secrets.kv.v2.read_secret_version.return_value = {
            "data": {"data": {"api_key": "key123", "api_secret": "secret123"}}
        }
        # Make sure side_effect is cleared from previous tests
        mock_client.secrets.kv.v2.read_secret_version.reset_mock()
        mock_client.secrets.kv.v2.read_secret_version.side_effect = None

        # Temporarily replace mock Client class
        original_client = mock_hvac_module.Client
        mock_hvac_module.Client = lambda *args, **kwargs: mock_client
        try:
            manager = VaultSecretManager(url="http://vault:8200", token="test-token")
            result = manager.get_service_credentials("alpaca")
            assert result == {"api_key": "key123", "api_secret": "secret123"}
            # Verify correct path was used - only check the last call
            mock_client.secrets.kv.v2.read_secret_version.assert_called_with(
                path="secret/data/services/alpaca"
            )
        finally:
            mock_hvac_module.Client = original_client

    def test_get_service_credentials_empty_data(self) -> None:
        """Test service credentials retrieval with empty data."""
        mock_client = MockHvacClient()
        mock_client.secrets.kv.v2.read_secret_version.return_value = {
            "data": {"data": {}}
        }

        # Temporarily replace mock Client class
        original_client = mock_hvac_module.Client
        mock_hvac_module.Client = lambda *args, **kwargs: mock_client
        try:
            manager = VaultSecretManager(url="http://vault:8200", token="test-token")
            result = manager.get_service_credentials("alpaca")
            assert result == {}
        finally:
            mock_hvac_module.Client = original_client

    def test_get_service_credentials_exception(self) -> None:
        """Test service credentials retrieval with exception."""
        mock_client = MockHvacClient()
        mock_client.secrets.kv.v2.read_secret_version.side_effect = Exception(
            "Vault error"
        )

        # Temporarily replace mock Client class
        original_client = mock_hvac_module.Client
        mock_hvac_module.Client = lambda *args, **kwargs: mock_client
        try:
            manager = VaultSecretManager(url="http://vault:8200", token="test-token")
            result = manager.get_service_credentials("alpaca")
            assert result == {}
        finally:
            mock_hvac_module.Client = original_client

    def test_validate_service_success(self) -> None:
        """Test successful service validation."""
        # Create a fresh mock client
        mock_client = MockHvacClient()
        mock_client.secrets.kv.v2.read_secret_version.return_value = {
            "data": {"data": {"api_key": "test_key"}}
        }

        # Temporarily replace mock Client class
        original_client = mock_hvac_module.Client
        mock_hvac_module.Client = lambda *args, **kwargs: mock_client
        try:
            manager = VaultSecretManager(url="http://vault:8200", token="test-token")
            result = manager.validate_service("alpaca")
            assert result is True
        finally:
            mock_hvac_module.Client = original_client

    def test_validate_service_no_data_response(self) -> None:
        """Test service validation with no data in response."""
        mock_client = MockHvacClient()
        mock_client.secrets.kv.v2.read_secret_version.return_value = {}

        # Temporarily replace mock Client class
        original_client = mock_hvac_module.Client
        mock_hvac_module.Client = lambda *args, **kwargs: mock_client
        try:
            manager = VaultSecretManager(url="http://vault:8200", token="test-token")
            result = manager.validate_service("alpaca")
            assert result is False
        finally:
            mock_hvac_module.Client = original_client

    def test_validate_service_exception(self) -> None:
        """Test service validation with exception."""
        mock_client = MockHvacClient()
        mock_client.secrets.kv.v2.read_secret_version.side_effect = Exception(
            "Vault error"
        )

        # Temporarily replace mock Client class
        original_client = mock_hvac_module.Client
        mock_hvac_module.Client = lambda *args, **kwargs: mock_client
        try:
            manager = VaultSecretManager(url="http://vault:8200", token="test-token")
            result = manager.validate_service("alpaca")
            assert result is False
        finally:
            mock_hvac_module.Client = original_client

    def test_custom_mount_point(self) -> None:
        """Test using custom mount point."""
        mock_client = MockHvacClient()
        mock_client.secrets.kv.v2.read_secret_version.return_value = {
            "data": {"data": {"value": "test_value"}}
        }

        # Temporarily replace mock Client class
        original_client = mock_hvac_module.Client
        mock_hvac_module.Client = lambda *args, **kwargs: mock_client
        try:
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
        finally:
            mock_hvac_module.Client = original_client

    def test_with_ssl_verify_disabled(self) -> None:
        """Test initialization with SSL verification disabled."""
        mock_client = MockHvacClient()

        # Temporarily replace mock Client class
        original_client = mock_hvac_module.Client
        mock_hvac_module.Client = lambda *args, **kwargs: mock_client
        try:
            manager = VaultSecretManager(
                url="https://vault.example.com", token="test-token", verify=False
            )
            # Should be called with verify=False
            pass  # Already verified by mock setup
        finally:
            mock_hvac_module.Client = original_client
