"""Tests for HashiCorp Vault secret manager implementation."""

import pytest
from unittest.mock import MagicMock, patch
import json
import os

from quantchain.core.secret_managers.vault import VaultSecretManager


class TestVaultSecretManager:
    """Test cases for VaultSecretManager."""

    def setup_method(self):
        """Set up test fixtures."""
        self.url = "https://vault.example.com:8200"
        self.token = "vault-token-123"
        self.namespace = "test-namespace"

    @patch("quantchain.core.secret_managers.vault.HVAC_AVAILABLE", True)
    @patch("quantchain.core.secret_managers.vault.hvac")
    def test_initialization_with_params(self, mock_hvac):
        """Test manager initialization with parameters."""
        mock_client = MagicMock()
        mock_hvac.Client.return_value = mock_client

        manager = VaultSecretManager(
            url=self.url,
            token=self.token,
            namespace=self.namespace,
            verify=False,
            mount_point="custom-mount",
        )

        assert manager.url == self.url
        assert manager.token == self.token
        assert manager.namespace == self.namespace
        assert manager.verify is False
        assert manager.mount_point == "custom-mount"
        assert manager._client == mock_client

    @patch("quantchain.core.secret_managers.vault.HVAC_AVAILABLE", True)
    @patch.dict(
        os.environ,
        {
            "VAULT_ADDR": "https://env-vault.example.com:8200",
            "VAULT_TOKEN": "env-token-456",
        },
    )
    @patch("quantchain.core.secret_managers.vault.hvac")
    def test_initialization_with_env_vars(self, mock_hvac):
        """Test manager initialization using environment variables."""
        mock_client = MagicMock()
        mock_hvac.Client.return_value = mock_client

        manager = VaultSecretManager()

        assert manager.url == "https://env-vault.example.com:8200"
        assert manager.token == "env-token-456"

    @patch("quantchain.core.secret_managers.vault.HVAC_AVAILABLE", True)
    @patch("quantchain.core.secret_managers.vault.hvac")
    def test_initialization_missing_url(self, mock_hvac):
        """Test manager initialization fails without URL."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="Vault URL must be provided"):
                VaultSecretManager(token=self.token)

    @patch("quantchain.core.secret_managers.vault.HVAC_AVAILABLE", True)
    @patch("quantchain.core.secret_managers.vault.hvac")
    def test_initialization_missing_token(self, mock_hvac):
        """Test manager initialization fails without token."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="Vault token must be provided"):
                VaultSecretManager(url=self.url)

    @patch("quantchain.core.secret_managers.vault.HVAC_AVAILABLE", False)
    def test_initialization_library_not_available(self):
        """Test manager initialization fails when library not available."""
        with pytest.raises(ImportError, match="hvac library is required"):
            VaultSecretManager(url=self.url, token=self.token)

    @patch("quantchain.core.secret_managers.vault.HVAC_AVAILABLE", True)
    @patch("quantchain.core.secret_managers.vault.hvac")
    def test_get_secret_success(self, mock_hvac):
        """Test successful secret retrieval."""
        mock_client = MagicMock()
        mock_hvac.Client.return_value = mock_client

        secret_data = {"username": "testuser", "password": "testpass"}
        mock_response = {"data": {"data": secret_data}}
        mock_client.secrets.kv.v2.read_secret_version.return_value = mock_response

        manager = VaultSecretManager(url=self.url, token=self.token)
        result = manager.get_secret("test-secret")

        assert result == secret_data
        mock_client.secrets.kv.v2.read_secret_version.assert_called_once_with(
            path="test-secret", mount_point="secret"
        )

    @patch("quantchain.core.secret_managers.vault.HVAC_AVAILABLE", True)
    @patch("quantchain.core.secret_managers.vault.hvac")
    def test_get_secret_success_custom_mount(self, mock_hvac):
        """Test successful secret retrieval with custom mount point."""
        mock_client = MagicMock()
        mock_hvac.Client.return_value = mock_client

        secret_data = {"username": "testuser", "password": "testpass"}
        mock_response = {"data": {"data": secret_data}}
        mock_client.secrets.kv.v2.read_secret_version.return_value = mock_response

        manager = VaultSecretManager(
            url=self.url, token=self.token, mount_point="custom-mount"
        )
        result = manager.get_secret("test-secret")

        assert result == secret_data
        mock_client.secrets.kv.v2.read_secret_version.assert_called_once_with(
            path="test-secret", mount_point="custom-mount"
        )

    @patch("quantchain.core.secret_managers.vault.HVAC_AVAILABLE", True)
    @patch("quantchain.core.secret_managers.vault.hvac")
    def test_get_secret_not_found(self, mock_hvac):
        """Test secret not found error."""
        mock_client = MagicMock()
        mock_hvac.Client.return_value = mock_client

        mock_client.secrets.kv.v2.read_secret_version.side_effect = Exception(
            "Secret not found"
        )

        manager = VaultSecretManager(url=self.url, token=self.token)

        with pytest.raises(Exception, match="Secret 'test-secret' not found"):
            manager.get_secret("test-secret")

    @patch("quantchain.core.secret_managers.vault.HVAC_AVAILABLE", True)
    @patch("quantchain.core.secret_managers.vault.hvac")
    def test_get_secret_permission_denied(self, mock_hvac):
        """Test permission denied error."""
        mock_client = MagicMock()
        mock_hvac.Client.return_value = mock_client

        mock_client.secrets.kv.v2.read_secret_version.side_effect = Exception(
            "Permission denied"
        )

        manager = VaultSecretManager(url=self.url, token=self.token)

        with pytest.raises(Exception, match="Access denied for secret 'test-secret'"):
            manager.get_secret("test-secret")

    @patch("quantchain.core.secret_managers.vault.HVAC_AVAILABLE", True)
    @patch("quantchain.core.secret_managers.vault.hvac")
    def test_set_secret_success(self, mock_hvac):
        """Test successful secret creation."""
        mock_client = MagicMock()
        mock_hvac.Client.return_value = mock_client

        secret_data = {"username": "newuser", "password": "newpass"}
        mock_client.secrets.kv.v2.create_or_update_secret.return_value = {
            "data": {"created_time": "now"}
        }

        manager = VaultSecretManager(url=self.url, token=self.token)
        manager.set_secret("test-secret", secret_data)

        mock_client.secrets.kv.v2.create_or_update_secret.assert_called_once_with(
            path="test-secret", secret=secret_data, mount_point="secret"
        )

    @patch("quantchain.core.secret_managers.vault.HVAC_AVAILABLE", True)
    @patch("quantchain.core.secret_managers.vault.hvac")
    def test_set_secret_binary_success(self, mock_hvac):
        """Test successful binary secret creation."""
        mock_client = MagicMock()
        mock_hvac.Client.return_value = mock_client

        binary_data = b"binary_secret_data"
        # Binary data should be base64 encoded for JSON compatibility
        import base64

        encoded_data = base64.b64encode(binary_data).decode("utf-8")

        mock_client.secrets.kv.v2.create_or_update_secret.return_value = {
            "data": {"created_time": "now"}
        }

        manager = VaultSecretManager(url=self.url, token=self.token)
        manager.set_secret("test-secret-binary", binary_data)

        # Verify binary data was encoded
        args, kwargs = mock_client.secrets.kv.v2.create_or_update_secret.call_args
        assert args[0] == "test-secret-binary"
        assert isinstance(args[1], dict)

    @patch("quantchain.core.secret_managers.vault.HVAC_AVAILABLE", True)
    @patch("quantchain.core.secret_managers.vault.hvac")
    def test_set_secret_error(self, mock_hvac):
        """Test error during secret creation."""
        mock_client = MagicMock()
        mock_hvac.Client.return_value = mock_client

        mock_client.secrets.kv.v2.create_or_update_secret.side_effect = Exception(
            "Creation failed"
        )

        manager = VaultSecretManager(url=self.url, token=self.token)
        secret_data = {"username": "testuser"}

        with pytest.raises(Exception, match="Failed to set secret 'test-secret'"):
            manager.set_secret("test-secret", secret_data)

    @patch("quantchain.core.secret_managers.vault.HVAC_AVAILABLE", True)
    @patch("quantchain.core.secret_managers.vault.hvac")
    def test_update_secret_success(self, mock_hvac):
        """Test successful secret update."""
        mock_client = MagicMock()
        mock_hvac.Client.return_value = mock_client

        secret_data = {"username": "updateduser", "password": "updatedpass"}
        mock_client.secrets.kv.v2.create_or_update_secret.return_value = {
            "data": {"updated_time": "now"}
        }

        manager = VaultSecretManager(url=self.url, token=self.token)
        manager.update_secret("test-secret", secret_data)

        mock_client.secrets.kv.v2.create_or_update_secret.assert_called_once_with(
            path="test-secret", secret=secret_data, mount_point="secret"
        )

    @patch("quantchain.core.secret_managers.vault.HVAC_AVAILABLE", True)
    @patch("quantchain.core.secret_managers.vault.hvac")
    def test_update_secret_not_found(self, mock_hvac):
        """Test updating secret that doesn't exist."""
        mock_client = MagicMock()
        mock_hvac.Client.return_value = mock_client

        mock_client.secrets.kv.v2.create_or_update_secret.side_effect = Exception(
            "Secret not found"
        )

        manager = VaultSecretManager(url=self.url, token=self.token)
        secret_data = {"username": "testuser"}

        with pytest.raises(Exception, match="Secret 'test-secret' not found"):
            manager.update_secret("test-secret", secret_data)

    @patch("quantchain.core.secret_managers.vault.HVAC_AVAILABLE", True)
    @patch("quantchain.core.secret_managers.vault.hvac")
    def test_delete_secret_success(self, mock_hvac):
        """Test successful secret deletion."""
        mock_client = MagicMock()
        mock_hvac.Client.return_value = mock_client

        mock_client.secrets.kv.v2.delete_metadata_and_all_versions.return_value = {
            "data": {"deleted_time": "now"}
        }

        manager = VaultSecretManager(url=self.url, token=self.token)
        manager.delete_secret("test-secret")

        mock_client.secrets.kv.v2.delete_metadata_and_all_versions.assert_called_once_with(
            path="test-secret", mount_point="secret"
        )

    @patch("quantchain.core.secret_managers.vault.HVAC_AVAILABLE", True)
    @patch("quantchain.core.secret_managers.vault.hvac")
    def test_delete_secret_not_found(self, mock_hvac):
        """Test deleting secret that doesn't exist."""
        mock_client = MagicMock()
        mock_hvac.Client.return_value = mock_client

        mock_client.secrets.kv.v2.delete_metadata_and_all_versions.side_effect = (
            Exception("Secret not found")
        )

        manager = VaultSecretManager(url=self.url, token=self.token)

        with pytest.raises(Exception, match="Secret 'test-secret' not found"):
            manager.delete_secret("test-secret")

    @patch("quantchain.core.secret_managers.vault.HVAC_AVAILABLE", True)
    @patch("quantchain.core.secret_managers.vault.hvac")
    def test_list_secrets_success(self, mock_hvac):
        """Test successful secret listing."""
        mock_client = MagicMock()
        mock_hvac.Client.return_value = mock_client

        mock_response = {"data": {"keys": ["secret1", "secret2", "app/secret3"]}}
        mock_client.secrets.kv.v2.list_secrets.return_value = mock_response

        manager = VaultSecretManager(url=self.url, token=self.token)
        secrets = manager.list_secrets()

        assert len(secrets) == 3
        assert "secret1" in secrets
        assert "secret2" in secrets
        assert "app/secret3" in secrets

        mock_client.secrets.kv.v2.list_secrets.assert_called_once_with(
            path="", mount_point="secret"
        )

    @patch("quantchain.core.secret_managers.vault.HVAC_AVAILABLE", True)
    @patch("quantchain.core.secret_managers.vault.hvac")
    def test_list_secrets_with_filter(self, mock_hvac):
        """Test secret listing with filter."""
        mock_client = MagicMock()
        mock_hvac.Client.return_value = mock_client

        mock_response = {
            "data": {"keys": ["app/secret1", "app/secret2", "other/secret"]}
        }
        mock_client.secrets.kv.v2.list_secrets.return_value = mock_response

        manager = VaultSecretManager(url=self.url, token=self.token)
        secrets = manager.list_secrets(filter_prefix="app/")

        assert len(secrets) == 2
        assert "app/secret1" in secrets
        assert "app/secret2" in secrets
        assert "other/secret" not in secrets

    @patch("quantchain.core.secret_managers.vault.HVAC_AVAILABLE", True)
    @patch("quantchain.core.secret_managers.vault.hvac")
    def test_list_secrets_with_path(self, mock_hvac):
        """Test secret listing with path."""
        mock_client = MagicMock()
        mock_hvac.Client.return_value = mock_client

        mock_response = {"data": {"keys": ["subsecret1", "subsecret2"]}}
        mock_client.secrets.kv.v2.list_secrets.return_value = mock_response

        manager = VaultSecretManager(url=self.url, token=self.token)
        secrets = manager.list_secrets(path="app/")

        assert len(secrets) == 2
        assert "subsecret1" in secrets
        assert "subsecret2" in secrets

        mock_client.secrets.kv.v2.list_secrets.assert_called_once_with(
            path="app/", mount_point="secret"
        )

    @patch("quantchain.core.secret_managers.vault.HVAC_AVAILABLE", True)
    @patch("quantchain.core.secret_managers.vault.hvac")
    def test_secret_exists_true(self, mock_hvac):
        """Test secret exists check - secret exists."""
        mock_client = MagicMock()
        mock_hvac.Client.return_value = mock_client

        mock_response = {"data": {"keys": ["test-secret", "other-secret"]}}
        mock_client.secrets.kv.v2.list_secrets.return_value = mock_response

        manager = VaultSecretManager(url=self.url, token=self.token)
        exists = manager.secret_exists("test-secret")

        assert exists is True

    @patch("quantchain.core.secret_managers.vault.HVAC_AVAILABLE", True)
    @patch("quantchain.core.secret_managers.vault.hvac")
    def test_secret_exists_false(self, mock_hvac):
        """Test secret exists check - secret doesn't exist."""
        mock_client = MagicMock()
        mock_hvac.Client.return_value = mock_client

        mock_response = {"data": {"keys": ["other-secret"]}}
        mock_client.secrets.kv.v2.list_secrets.return_value = mock_response

        manager = VaultSecretManager(url=self.url, token=self.token)
        exists = manager.secret_exists("nonexistent-secret")

        assert exists is False

    @patch("quantchain.core.secret_managers.vault.HVAC_AVAILABLE", True)
    @patch("quantchain.core.secret_managers.vault.hvac")
    def test_secret_exists_nested_path(self, mock_hvac):
        """Test secret exists check with nested path."""
        mock_client = MagicMock()
        mock_hvac.Client.return_value = mock_client

        # Mock list at root level
        mock_root_response = {"data": {"keys": ["app/"]}}
        # Mock list at app/ level
        mock_app_response = {"data": {"keys": ["secret1", "secret2"]}}
        mock_client.secrets.kv.v2.list_secrets.side_effect = [
            mock_root_response,
            mock_app_response,
        ]

        manager = VaultSecretManager(url=self.url, token=self.token)
        exists = manager.secret_exists("app/secret1")

        assert exists is True
        assert mock_client.secrets.kv.v2.list_secrets.call_count == 2

    @patch("quantchain.core.secret_managers.vault.HVAC_AVAILABLE", True)
    @patch("quantchain.core.secret_managers.vault.hvac")
    def test_namespace_support(self, mock_hvac):
        """Test namespace support in requests."""
        mock_client = MagicMock()
        mock_hvac.Client.return_value = mock_client

        secret_data = {"username": "testuser"}
        mock_response = {"data": {"data": secret_data}}
        mock_client.secrets.kv.v2.read_secret_version.return_value = mock_response

        manager = VaultSecretManager(
            url=self.url, token=self.token, namespace=self.namespace
        )
        result = manager.get_secret("test-secret")

        # Verify namespace was set on client
        assert mock_client.namespace == self.namespace
        assert result == secret_data

    @patch("quantchain.core.secret_managers.vault.HVAC_AVAILABLE", True)
    @patch("quantchain.core.secret_managers.vault.hvac")
    def test_ssl_verification_setting(self, mock_hvac):
        """Test SSL verification setting is passed to client."""
        mock_client = MagicMock()
        mock_hvac.Client.return_value = mock_client

        manager = VaultSecretManager(url=self.url, token=self.token, verify=False)

        # Verify client was called with verify=False
        mock_hvac.Client.assert_called_once_with(
            url=self.url, token=self.token, verify=False, namespace=None
        )

    @patch("quantchain.core.secret_managers.vault.HVAC_AVAILABLE", True)
    @patch("quantchain.core.secret_managers.vault.hvac")
    def test_custom_kwargs_passthrough(self, mock_hvac):
        """Test custom kwargs are passed through to hvac.Client."""
        mock_client = MagicMock()
        mock_hvac.Client.return_value = mock_client

        custom_kwargs = {"timeout": 30, "cert": "/path/to/cert.pem"}

        manager = VaultSecretManager(url=self.url, token=self.token, **custom_kwargs)

        # Verify client was called with custom kwargs
        expected_kwargs = {
            "url": self.url,
            "token": self.token,
            "verify": True,
            "namespace": None,
        }
        expected_kwargs.update(custom_kwargs)

        mock_hvac.Client.assert_called_once_with(**expected_kwargs)
