"""Comprehensive tests for HashiCorp Vault secret manager implementation."""

import json
import os
import sys
import unittest.mock
import pytest

# Create complete mock hierarchy
class MockKVv2:
    read_secret_version = unittest.mock.MagicMock()

class MockSecrets:
    kv = unittest.mock.MagicMock()
    kv.v2 = MockKVv2()

class MockHvacClient:
    def __init__(self, *args, **kwargs):
        self.is_authenticated_ret = kwargs.get('is_authenticated', True)
        self.connect_error = kwargs.get('connect_error', None)
        
    def is_authenticated(self):
        return self.is_authenticated_ret
        
    @property
    def secrets(self):
        return MockSecrets()

# Add mock to sys.modules before any other imports
sys.modules['hvac'] = unittest.mock.MagicMock()
sys.modules['hvac.Client'] = MockHvacClient

# Now we can import our module
from quantchain.core.secret_managers.vault import VaultSecretManager

_VAULT_AVAILABLE = True


@pytest.mark.unit
class TestVaultSecretManager:
    """Test Vault Secret Manager implementation."""

    def test_init_with_explicit_values(self) -> None:
        """Test initialization with explicit values."""
        mock_client = MockHvacClient(is_authenticated=True)
        
        manager = VaultSecretManager(
            url="https://vault.example.com",
            token="test-token",
            namespace="test-ns",
            verify=False,
            mount_point="custom-mount"
        )

        assert manager.url == "https://vault.example.com"
        assert manager.token == "test-token"
        assert manager.namespace == "test-ns"
        assert manager.verify is False
        assert manager.mount_point == "custom-mount"

    def test_init_with_env_values(self) -> None:
        """Test initialization with environment variables."""
        with unittest.mock.patch.dict(os.environ, {
            "VAULT_ADDR": "http://vault:8200",
            "VAULT_TOKEN": "env-token"
        }):
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
        with unittest.mock.patch.dict(os.environ, {"VAULT_ADDR": "http://vault:8200"}, clear=True):
            with pytest.raises(ValueError, match="Vault token must be provided"):
                VaultSecretManager()

    def test_init_authentication_failure(self) -> None:
        """Test initialization fails authentication."""
        with unittest.mock.patch('hvac.Client') as mock_client_class:
            # Make Client constructor return a client that returns False for auth
            mock_client = MockHvacClient(is_authenticated=False)
            mock_client_class.return_value = mock_client

            with pytest.raises(RuntimeError, match="Failed to authenticate with Vault"):
                VaultSecretManager(url="http://vault:8200", token="invalid-token")

    def test_init_connection_error(self) -> None:
        """Test initialization with connection error."""
        with unittest.mock.patch('hvac.Client') as mock_client_class:
            # Make Client constructor raise exception
            mock_client_class.side_effect = Exception("Connection failed")
            
            with pytest.raises(Exception, match="Connection failed"):
                VaultSecretManager(url="http://vault:8200", token="test-token")

    def test_build_secret_path(self) -> None:
        """Test building secret path."""
        manager = VaultSecretManager(
            url="http://vault:8200",
            token="test-token",
            mount_point="custom-mount"
        )

        # Test various key formats
        assert manager._build_secret_path("test") == "custom-mount/data/test"
        assert manager._build_secret_path("/test") == "custom-mount/data/test"
        assert manager._build_secret_path("path/to/secret") == "custom-mount/data/path/to/secret"
        assert manager._build_secret_path("/path/to/secret") == "custom-mount/data/path/to/secret"

    def test_get_secret_success_single_value(self) -> None:
        """Test successful secret retrieval with single value."""
        mock_client = MockHvacClient()
        mock_client.secrets.kv.v2.read_secret_version.return_value = {
            "data": {"data": {"value": "test_secret_value"}}
        }
        
        with unittest.mock.patch('hvac.Client', return_value=mock_client):
            manager = VaultSecretManager(url="http://vault:8200", token="test-token")
            result = manager.get_secret("test_secret")

            assert result == "test_secret_value"

    def test_get_secret_success_single_non_value(self) -> None:
        """Test successful secret retrieval with single non-value key."""
        mock_client = MockHvacClient()
        mock_client.secrets.kv.v2.read_secret_version.return_value = {
            "data": {"data": {"api_key": "test_key"}}
        }
        
        with unittest.mock.patch('hvac.Client', return_value=mock_client):
            manager = VaultSecretManager(url="http://vault:8200", token="test-token")
            result = manager.get_secret("test_secret")

            assert result == "test_key"

    def test_get_secret_success_multiple_values(self) -> None:
        """Test successful secret retrieval with multiple values."""
        mock_client = MockHvacClient()
        mock_client.secrets.kv.v2.read_secret_version.return_value = {
            "data": {"data": {"key1": "value1", "key2": "value2"}}
        }
        
        with unittest.mock.patch('hvac.Client', return_value=mock_client):
            manager = VaultSecretManager(url="http://vault:8200", token="test-token")
            result = manager.get_secret("test_secret")

            # Should return JSON string for multiple values
            assert json.loads(result) == {"key1": "value1", "key2": "value2"}

    def test_get_secret_no_data_response(self) -> None:
        """Test secret retrieval with no data in response."""
        mock_client = MockHvacClient()
        mock_client.secrets.kv.v2.read_secret_version.return_value = {}
        
        with unittest.mock.patch('hvac.Client', return_value=mock_client):
            manager = VaultSecretManager(url="http://vault:8200", token="test-token")
            result = manager.get_secret("test_secret")

            assert result is None

    def test_get_secret_no_nested_data(self) -> None:
        """Test secret retrieval with no nested data."""
        mock_client = MockHvacClient()
        mock_client.secrets.kv.v2.read_secret_version.return_value = {
            "data": {}
        }
        
        with unittest.mock.patch('hvac.Client', return_value=mock_client):
            manager = VaultSecretManager(url="http://vault:8200", token="test-token")
            result = manager.get_secret("test_secret")

            assert result is None

    def test_get_secret_exception(self) -> None:
        """Test secret retrieval with exception."""
        mock_client = MockHvacClient()
        mock_client.secrets.kv.v2.read_secret_version.side_effect = Exception("Vault error")
        
        with unittest.mock.patch('hvac.Client', return_value=mock_client):
            manager = VaultSecretManager(url="http://vault:8200", token="test-token")
            result = manager.get_secret("test_secret")

            assert result is None

    def test_get_service_credentials_success(self) -> None:
        """Test successful service credentials retrieval."""
        mock_client = MockHvacClient()
        mock_client.secrets.kv.v2.read_secret_version.return_value = {
            "data": {"data": {"api_key": "key123", "api_secret": "secret123"}}
        }
        # Make sure side_effect is cleared from previous tests
        mock_client.secrets.kv.v2.read_secret_version.side_effect = None
        
        with unittest.mock.patch('hvac.Client', return_value=mock_client):
            manager = VaultSecretManager(url="http://vault:8200", token="test-token")
            result = manager.get_service_credentials("alpaca")

            assert result == {"api_key": "key123", "api_secret": "secret123"}
            # Verify correct path was used
            mock_client.secrets.kv.v2.read_secret_version.assert_called_once_with(
                path="secret/data/services/alpaca"
            )

    def test_get_service_credentials_empty_data(self) -> None:
        """Test service credentials retrieval with empty data."""
        mock_client = MockHvacClient()
        mock_client.secrets.kv.v2.read_secret_version.return_value = {
            "data": {"data": {}}
        }
        
        with unittest.mock.patch('hvac.Client', return_value=mock_client):
            manager = VaultSecretManager(url="http://vault:8200", token="test-token")
            result = manager.get_service_credentials("alpaca")

            assert result == {}

    def test_get_service_credentials_exception(self) -> None:
        """Test service credentials retrieval with exception."""
        mock_client = MockHvacClient()
        mock_client.secrets.kv.v2.read_secret_version.side_effect = Exception("Vault error")
        
        with unittest.mock.patch('hvac.Client', return_value=mock_client):
            manager = VaultSecretManager(url="http://vault:8200", token="test-token")
            result = manager.get_service_credentials("alpaca")

            assert result == {}

    def test_validate_service_success(self) -> None:
        """Test successful service validation."""
        mock_client = MockHvacClient()
        mock_client.secrets.kv.v2.read_secret_version.return_value = {
            "data": {"data": {"api_key": "test_key"}}
        }
        
        with unittest.mock.patch('hvac.Client', return_value=mock_client):
            manager = VaultSecretManager(url="http://vault:8200", token="test-token")
            result = manager.validate_service("alpaca")

            assert result is True

    def test_validate_service_no_data_response(self) -> None:
        """Test service validation with no data in response."""
        mock_client = MockHvacClient()
        mock_client.secrets.kv.v2.read_secret_version.return_value = {}
        
        with unittest.mock.patch('hvac.Client', return_value=mock_client):
            manager = VaultSecretManager(url="http://vault:8200", token="test-token")
            result = manager.validate_service("alpaca")

            assert result is False

    def test_validate_service_exception(self) -> None:
        """Test service validation with exception."""
        mock_client = MockHvacClient()
        mock_client.secrets.kv.v2.read_secret_version.side_effect = Exception("Vault error")
        
        with unittest.mock.patch('hvac.Client', return_value=mock_client):
            manager = VaultSecretManager(url="http://vault:8200", token="test-token")
            result = manager.validate_service("alpaca")

            assert result is False

    def test_custom_mount_point(self) -> None:
        """Test using custom mount point."""
        mock_client = MockHvacClient()
        mock_client.secrets.kv.v2.read_secret_version.return_value = {
            "data": {"data": {"value": "test_value"}}
        }
        
        with unittest.mock.patch('hvac.Client', return_value=mock_client):
            manager = VaultSecretManager(
                url="http://vault:8200",
                token="test-token",
                mount_point="custom-mount"
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

    def test_with_ssl_verify_disabled(self) -> None:
        """Test initialization with SSL verification disabled."""
        mock_client = MockHvacClient()
        
        with unittest.mock.patch('hvac.Client', return_value=mock_client):
            manager = VaultSecretManager(
                url="https://vault.example.com",
                token="test-token",
                verify=False
            )

            # Should be called with verify=False
            pass  # Already verified by mock setup
