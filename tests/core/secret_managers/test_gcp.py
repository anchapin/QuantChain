"""Tests for GCP Secret Manager implementation."""

import pytest
from unittest.mock import MagicMock, patch, mock_open
import json
import os

from quantchain.core.secret_managers.gcp import GCPSecretManager


class TestGCPSecretManager:
    """Test cases for GCPSecretManager."""

    def setup_method(self):
        """Set up test fixtures."""
        self.project_id = "test-project-123"
        self.credentials_path = "/path/to/credentials.json"

    @patch("quantchain.core.secret_managers.gcp.GCP_AVAILABLE", True)
    @patch("quantchain.core.secret_managers.gcp.secretmanager")
    def test_initialization_with_project_id(self, mock_secretmanager):
        """Test manager initialization with project ID."""
        mock_client = MagicMock()
        mock_secretmanager.SecretManagerServiceClient.return_value = mock_client

        manager = GCPSecretManager(project_id=self.project_id)

        assert manager.project_id == self.project_id
        assert manager._client == mock_client

    @patch("quantchain.core.secret_managers.gcp.GCP_AVAILABLE", True)
    @patch.dict(os.environ, {"GCP_PROJECT": "env-project-456"})
    @patch("quantchain.core.secret_managers.gcp.secretmanager")
    def test_initialization_with_env_project_id(self, mock_secretmanager):
        """Test manager initialization using environment project ID."""
        mock_client = MagicMock()
        mock_secretmanager.SecretManagerServiceClient.return_value = mock_client

        manager = GCPSecretManager()

        assert manager.project_id == "env-project-456"
        assert manager._client == mock_client

    @patch("quantchain.core.secret_managers.gcp.GCP_AVAILABLE", True)
    @patch("quantchain.core.secret_managers.gcp.secretmanager")
    def test_initialization_no_project_id(self, mock_secretmanager):
        """Test manager initialization fails without project ID."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="GCP project ID must be provided"):
                GCPSecretManager()

    @patch("quantchain.core.secret_managers.gcp.GCP_AVAILABLE", False)
    def test_initialization_library_not_available(self):
        """Test manager initialization fails when library not available."""
        with pytest.raises(
            ImportError, match="google-cloud-secret-manager library is required"
        ):
            GCPSecretManager(project_id=self.project_id)

    @patch("quantchain.core.secret_managers.gcp.GCP_AVAILABLE", True)
    @patch("quantchain.core.secret_managers.gcp.secretmanager")
    def test_get_secret_success(self, mock_secretmanager):
        """Test successful secret retrieval."""
        mock_client = MagicMock()
        mock_secretmanager.SecretManagerServiceClient.return_value = mock_client

        secret_data = {"username": "testuser", "password": "testpass"}
        secret_payload = json.dumps(secret_data).encode("utf-8")

        mock_response = MagicMock()
        mock_response.payload.data = secret_payload
        mock_client.access_secret_version.return_value = mock_response

        manager = GCPSecretManager(project_id=self.project_id)
        result = manager.get_secret("test-secret")

        assert result == secret_data

        # Verify the correct path was built
        expected_name = (
            f"projects/{self.project_id}/secrets/test-secret/versions/latest"
        )
        mock_client.access_secret_version.assert_called_once_with(
            {"name": expected_name}
        )

    @patch("quantchain.core.secret_managers.gcp.GCP_AVAILABLE", True)
    @patch("quantchain.core.secret_managers.gcp.secretmanager")
    def test_get_secret_binary_success(self, mock_secretmanager):
        """Test successful binary secret retrieval."""
        mock_client = MagicMock()
        mock_secretmanager.SecretManagerServiceClient.return_value = mock_client

        binary_data = b"binary_secret_data"

        mock_response = MagicMock()
        mock_response.payload.data = binary_data
        mock_client.access_secret_version.return_value = mock_response

        manager = GCPSecretManager(project_id=self.project_id)
        result = manager.get_secret("test-secret-binary")

        assert result == binary_data

    @patch("quantchain.core.secret_managers.gcp.GCP_AVAILABLE", True)
    @patch("quantchain.core.secret_managers.gcp.secretmanager")
    def test_get_secret_not_found(self, mock_secretmanager):
        """Test secret not found error."""
        mock_client = MagicMock()
        mock_secretmanager.SecretManagerServiceClient.return_value = mock_client

        from google.api_core import exceptions as gcp_exceptions

        mock_client.access_secret_version.side_effect = gcp_exceptions.NotFound(
            "Secret not found"
        )

        manager = GCPSecretManager(project_id=self.project_id)

        with pytest.raises(Exception, match="Secret 'test-secret' not found"):
            manager.get_secret("test-secret")

    @patch("quantchain.core.secret_managers.gcp.GCP_AVAILABLE", True)
    @patch("quantchain.core.secret_managers.gcp.secretmanager")
    def test_get_secret_permission_denied(self, mock_secretmanager):
        """Test permission denied error."""
        mock_client = MagicMock()
        mock_secretmanager.SecretManagerServiceClient.return_value = mock_client

        from google.api_core import exceptions as gcp_exceptions

        mock_client.access_secret_version.side_effect = gcp_exceptions.PermissionDenied(
            "Access denied"
        )

        manager = GCPSecretManager(project_id=self.project_id)

        with pytest.raises(Exception, match="Access denied for secret 'test-secret'"):
            manager.get_secret("test-secret")

    @patch("quantchain.core.secret_managers.gcp.GCP_AVAILABLE", True)
    @patch("quantchain.core.secret_managers.gcp.secretmanager")
    def test_set_secret_success(self, mock_secretmanager):
        """Test successful secret creation."""
        mock_client = MagicMock()
        mock_secretmanager.SecretManagerServiceClient.return_value = mock_client

        secret_data = {"username": "newuser", "password": "newpass"}
        secret_payload = json.dumps(secret_data).encode("utf-8")

        # Mock create_secret response
        mock_create_response = MagicMock()
        mock_create_response.name = f"projects/{self.project_id}/secrets/test-secret"
        mock_client.create_secret.return_value = mock_create_response

        # Mock add_secret_version response
        mock_version_response = MagicMock()
        mock_version_response.name = (
            f"projects/{self.project_id}/secrets/test-secret/versions/1"
        )
        mock_client.add_secret_version.return_value = mock_version_response

        manager = GCPSecretManager(project_id=self.project_id)
        manager.set_secret("test-secret", secret_data)

        # Verify secret creation
        secret_path = f"projects/{self.project_id}"
        mock_client.create_secret.assert_called_once()

        # Verify version addition
        expected_secret_name = f"projects/{self.project_id}/secrets/test-secret"
        mock_client.add_secret_version.assert_called_once_with(
            {"parent": expected_secret_name, "payload": {"data": secret_payload}}
        )

    @patch("quantchain.core.secret_managers.gcp.GCP_AVAILABLE", True)
    @patch("quantchain.core.secret_managers.gcp.secretmanager")
    def test_set_secret_binary_success(self, mock_secretmanager):
        """Test successful binary secret creation."""
        mock_client = MagicMock()
        mock_secretmanager.SecretManagerServiceClient.return_value = mock_client

        binary_data = b"binary_secret_data"

        # Mock create_secret response
        mock_create_response = MagicMock()
        mock_create_response.name = (
            f"projects/{self.project_id}/secrets/test-secret-binary"
        )
        mock_client.create_secret.return_value = mock_create_response

        # Mock add_secret_version response
        mock_version_response = MagicMock()
        mock_client.add_secret_version.return_value = mock_version_response

        manager = GCPSecretManager(project_id=self.project_id)
        manager.set_secret("test-secret-binary", binary_data)

        expected_secret_name = f"projects/{self.project_id}/secrets/test-secret-binary"
        mock_client.add_secret_version.assert_called_once_with(
            {"parent": expected_secret_name, "payload": {"data": binary_data}}
        )

    @patch("quantchain.core.secret_managers.gcp.GCP_AVAILABLE", True)
    @patch("quantchain.core.secret_managers.gcp.secretmanager")
    def test_set_secret_already_exists(self, mock_secretmanager):
        """Test setting secret that already exists."""
        mock_client = MagicMock()
        mock_secretmanager.SecretManagerServiceClient.return_value = mock_client

        from google.api_core import exceptions as gcp_exceptions

        mock_client.create_secret.side_effect = gcp_exceptions.AlreadyExists(
            "Secret already exists"
        )

        manager = GCPSecretManager(project_id=self.project_id)
        secret_data = {"username": "testuser"}

        with pytest.raises(Exception, match="Secret 'test-secret' already exists"):
            manager.set_secret("test-secret", secret_data)

    @patch("quantchain.core.secret_managers.gcp.GCP_AVAILABLE", True)
    @patch("quantchain.core.secret_managers.gcp.secretmanager")
    def test_update_secret_success(self, mock_secretmanager):
        """Test successful secret update."""
        mock_client = MagicMock()
        mock_secretmanager.SecretManagerServiceClient.return_value = mock_client

        secret_data = {"username": "updateduser", "password": "updatedpass"}
        secret_payload = json.dumps(secret_data).encode("utf-8")

        mock_response = MagicMock()
        mock_response.name = (
            f"projects/{self.project_id}/secrets/test-secret/versions/2"
        )
        mock_client.add_secret_version.return_value = mock_response

        manager = GCPSecretManager(project_id=self.project_id)
        manager.update_secret("test-secret", secret_data)

        expected_secret_name = f"projects/{self.project_id}/secrets/test-secret"
        mock_client.add_secret_version.assert_called_once_with(
            {"parent": expected_secret_name, "payload": {"data": secret_payload}}
        )

    @patch("quantchain.core.secret_managers.gcp.GCP_AVAILABLE", True)
    @patch("quantchain.core.secret_managers.gcp.secretmanager")
    def test_update_secret_not_found(self, mock_secretmanager):
        """Test updating secret that doesn't exist."""
        mock_client = MagicMock()
        mock_secretmanager.SecretManagerServiceClient.return_value = mock_client

        from google.api_core import exceptions as gcp_exceptions

        mock_client.add_secret_version.side_effect = gcp_exceptions.NotFound(
            "Secret not found"
        )

        manager = GCPSecretManager(project_id=self.project_id)
        secret_data = {"username": "testuser"}

        with pytest.raises(Exception, match="Secret 'test-secret' not found"):
            manager.update_secret("test-secret", secret_data)

    @patch("quantchain.core.secret_managers.gcp.GCP_AVAILABLE", True)
    @patch("quantchain.core.secret_managers.gcp.secretmanager")
    def test_delete_secret_success(self, mock_secretmanager):
        """Test successful secret deletion."""
        mock_client = MagicMock()
        mock_secretmanager.SecretManagerServiceClient.return_value = mock_client

        mock_client.delete_secret.return_value = MagicMock()

        manager = GCPSecretManager(project_id=self.project_id)
        manager.delete_secret("test-secret")

        expected_name = f"projects/{self.project_id}/secrets/test-secret"
        mock_client.delete_secret.assert_called_once_with({"name": expected_name})

    @patch("quantchain.core.secret_managers.gcp.GCP_AVAILABLE", True)
    @patch("quantchain.core.secret_managers.gcp.secretmanager")
    def test_delete_secret_not_found(self, mock_secretmanager):
        """Test deleting secret that doesn't exist."""
        mock_client = MagicMock()
        mock_secretmanager.SecretManagerServiceClient.return_value = mock_client

        from google.api_core import exceptions as gcp_exceptions

        mock_client.delete_secret.side_effect = gcp_exceptions.NotFound(
            "Secret not found"
        )

        manager = GCPSecretManager(project_id=self.project_id)

        with pytest.raises(Exception, match="Secret 'test-secret' not found"):
            manager.delete_secret("test-secret")

    @patch("quantchain.core.secret_managers.gcp.GCP_AVAILABLE", True)
    @patch("quantchain.core.secret_managers.gcp.secretmanager")
    def test_list_secrets_success(self, mock_secretmanager):
        """Test successful secret listing."""
        mock_client = MagicMock()
        mock_secretmanager.SecretManagerServiceClient.return_value = mock_client

        mock_secret1 = MagicMock()
        mock_secret1.name = f"projects/{self.project_id}/secrets/secret1"

        mock_secret2 = MagicMock()
        mock_secret2.name = f"projects/{self.project_id}/secrets/secret2"

        mock_response = [mock_secret1, mock_secret2]
        mock_client.list_secrets.return_value = mock_response

        manager = GCPSecretManager(project_id=self.project_id)
        secrets = manager.list_secrets()

        assert len(secrets) == 2
        assert "secret1" in secrets
        assert "secret2" in secrets

        expected_parent = f"projects/{self.project_id}"
        mock_client.list_secrets.assert_called_once_with({"parent": expected_parent})

    @patch("quantchain.core.secret_managers.gcp.GCP_AVAILABLE", True)
    @patch("quantchain.core.secret_managers.gcp.secretmanager")
    def test_list_secrets_with_filter(self, mock_secretmanager):
        """Test secret listing with filter."""
        mock_client = MagicMock()
        mock_secretmanager.SecretManagerServiceClient.return_value = mock_client

        mock_secret = MagicMock()
        mock_secret.name = f"projects/{self.project_id}/secrets/app/secret1"

        mock_response = [mock_secret]
        mock_client.list_secrets.return_value = mock_response

        manager = GCPSecretManager(project_id=self.project_id)
        secrets = manager.list_secrets(filter_prefix="app/")

        assert len(secrets) == 1
        assert "app/secret1" in secrets

    @patch("quantchain.core.secret_managers.gcp.GCP_AVAILABLE", True)
    @patch("quantchain.core.secret_managers.gcp.secretmanager")
    def test_secret_exists_true(self, mock_secretmanager):
        """Test secret exists check - secret exists."""
        mock_client = MagicMock()
        mock_secretmanager.SecretManagerServiceClient.return_value = mock_client

        mock_secret = MagicMock()
        mock_secret.name = f"projects/{self.project_id}/secrets/test-secret"
        mock_client.list_secrets.return_value = [mock_secret]

        manager = GCPSecretManager(project_id=self.project_id)
        exists = manager.secret_exists("test-secret")

        assert exists is True

    @patch("quantchain.core.secret_managers.gcp.GCP_AVAILABLE", True)
    @patch("quantchain.core.secret_managers.gcp.secretmanager")
    def test_secret_exists_false(self, mock_secretmanager):
        """Test secret exists check - secret doesn't exist."""
        mock_client = MagicMock()
        mock_secretmanager.SecretManagerServiceClient.return_value = mock_client

        mock_client.list_secrets.return_value = []

        manager = GCPSecretManager(project_id=self.project_id)
        exists = manager.secret_exists("nonexistent-secret")

        assert exists is False

    @patch("quantchain.core.secret_managers.gcp.GCP_AVAILABLE", True)
    @patch("quantchain.core.secret_managers.gcp.secretmanager")
    def test_secret_name_parsing(self, mock_secretmanager):
        """Test parsing secret names from GCP resource names."""
        mock_client = MagicMock()
        mock_secretmanager.SecretManagerServiceClient.return_value = mock_client

        manager = GCPSecretManager(project_id=self.project_id)

        # Test various secret name formats
        test_cases = [
            ("test-secret", "test-secret"),
            ("app/secret1", "app/secret1"),
            ("namespace/app/database-url", "namespace/app/database-url"),
        ]

        for secret_id, expected_name in test_cases:
            result = manager._format_secret_name(secret_id)
            assert result == expected_name

    @patch("quantchain.core.secret_managers.gcp.GCP_AVAILABLE", True)
    @patch("quantchain.core.secret_managers.gcp.secretmanager")
    def test_version_number_handling(self, mock_secretmanager):
        """Test handling specific secret versions."""
        mock_client = MagicMock()
        mock_secretmanager.SecretManagerServiceClient.return_value = mock_client

        secret_data = {"key": "value"}
        secret_payload = json.dumps(secret_data).encode("utf-8")

        mock_response = MagicMock()
        mock_response.payload.data = secret_payload
        mock_client.access_secret_version.return_value = mock_response

        manager = GCPSecretManager(project_id=self.project_id)

        # Test getting specific version
        result = manager.get_secret("test-secret", version="5")

        expected_name = f"projects/{self.project_id}/secrets/test-secret/versions/5"
        mock_client.access_secret_version.assert_called_once_with(
            {"name": expected_name}
        )
        assert result == secret_data
