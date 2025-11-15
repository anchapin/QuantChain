"""Tests for GCP Secret Manager implementation."""





import pytest
from unittest.mock import MagicMock, patch
import json
import os
from quantchain.core.secret_managers.gcp import GCPSecretManager
from google.api_core import exceptions as gcp_exceptions
from google.api_core import exceptions as gcp_exceptions
from google.api_core import exceptions as gcp_exceptions
from google.api_core import exceptions as gcp_exceptions
from google.api_core import exceptions as gcp_exceptions
from google.api_core import exceptions as gcp_exceptions



class TestGCPSecretManagerFixed:
    """Test cases for GCPSecretManager with actual implementation."""



def setup_method(self):
        """Set up test fixtures."""
        self.project_id = "test-project-123"

    @patch("quantchain.core.secret_managers.gcp.GCP_AVAILABLE", True)
    @patch("quantchain.core.secret_managers.gcp.secretmanager")


def test_initialization_with_project_id(self, mock_secretmanager):
        """Test manager initialization with project ID."""
        mock_client = MagicMock()
        mock_secretmanager.SecretManagerServiceClient.return_value = mock_client

        # Mock successful connection
        mock_client.list_secrets.return_value = []

        manager = GCPSecretManager(project_id=self.project_id)

        assert manager.project_id == self.project_id
        assert manager.client == mock_client

    @patch("quantchain.core.secret_managers.gcp.GCP_AVAILABLE", True)
    @patch.dict(os.environ, {"GCP_PROJECT": "env-project-456"})
    @patch("quantchain.core.secret_managers.gcp.secretmanager")


def test_initialization_with_env_project_id(self, mock_secretmanager):
        """Test manager initialization using environment project ID."""
        mock_client = MagicMock()
        mock_secretmanager.SecretManagerServiceClient.return_value = mock_client

        # Mock successful connection
        mock_client.list_secrets.return_value = []

        manager = GCPSecretManager()

        assert manager.project_id == "env-project-456"
        assert manager.client == mock_client

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


def test_get_secret_success_json(self, mock_secretmanager):
        """Test successful JSON secret retrieval."""
        mock_client = MagicMock()
        mock_secretmanager.SecretManagerServiceClient.return_value = mock_client

        # Mock successful connection
        mock_client.list_secrets.return_value = []

        # Mock secret response
        secret_data = {"username": "testuser", "password": "testpass"}
        secret_value = json.dumps(secret_data).encode("utf-8")

        mock_response = MagicMock()
        mock_response.payload.data = secret_value
        mock_client.access_secret_version.return_value = mock_response

        manager = GCPSecretManager(project_id=self.project_id)
        result = manager.get_secret("test-secret")

        assert result == json.dumps(secret_data)

        # Verify correct secret name was built
        expected_name = (
            f"projects/{self.project_id}/secrets/quantchain/test-secret/versions/latest"
        )
        mock_client.access_secret_version.assert_called_once_with(
            request={"name": expected_name}
        )

    @patch("quantchain.core.secret_managers.gcp.GCP_AVAILABLE", True)
    @patch("quantchain.core.secret_managers.gcp.secretmanager")


def test_get_secret_success_single_value_json(self, mock_secretmanager):
        """Test successful single value JSON secret retrieval."""
        mock_client = MagicMock()
        mock_secretmanager.SecretManagerServiceClient.return_value = mock_client

        # Mock successful connection
        mock_client.list_secrets.return_value = []

        # Mock secret response with single value
        secret_data = {"api_key": "test-key-12345"}
        secret_value = json.dumps(secret_data).encode("utf-8")

        mock_response = MagicMock()
        mock_response.payload.data = secret_value
        mock_client.access_secret_version.return_value = mock_response

        manager = GCPSecretManager(project_id=self.project_id)
        result = manager.get_secret("test-secret")

        assert result == "test-key-12345"

    @patch("quantchain.core.secret_managers.gcp.GCP_AVAILABLE", True)
    @patch("quantchain.core.secret_managers.gcp.secretmanager")


def test_get_secret_success_binary(self, mock_secretmanager):
        """Test successful binary secret retrieval."""
        mock_client = MagicMock()
        mock_secretmanager.SecretManagerServiceClient.return_value = mock_client

        # Mock successful connection
        mock_client.list_secrets.return_value = []

        # Mock binary secret response
        binary_data = b"binary_secret_data"

        mock_response = MagicMock()
        mock_response.payload.data = binary_data
        mock_client.access_secret_version.return_value = mock_response

        manager = GCPSecretManager(project_id=self.project_id)
        result = manager.get_secret("test-secret-binary")

        assert result == "binary_secret_data"

    @patch("quantchain.core.secret_managers.gcp.GCP_AVAILABLE", True)
    @patch("quantchain.core.secret_managers.gcp.secretmanager")


def test_get_secret_success_string(self, mock_secretmanager):
        """Test successful string secret retrieval (non-JSON)."""
        mock_client = MagicMock()
        mock_secretmanager.SecretManagerServiceClient.return_value = mock_client

        # Mock successful connection
        mock_client.list_secrets.return_value = []

        # Mock string secret response
        secret_string = "simple-secret-value"
        secret_value = secret_string.encode("utf-8")

        mock_response = MagicMock()
        mock_response.payload.data = secret_value
        mock_client.access_secret_version.return_value = mock_response

        manager = GCPSecretManager(project_id=self.project_id)
        result = manager.get_secret("test-secret")

        assert result == secret_string

    @patch("quantchain.core.secret_managers.gcp.GCP_AVAILABLE", True)
    @patch("quantchain.core.secret_managers.gcp.secretmanager")


def test_get_secret_not_found(self, mock_secretmanager):
        """Test secret not found error."""
        mock_client = MagicMock()
        mock_secretmanager.SecretManagerServiceClient.return_value = mock_client

        # Mock successful connection
        mock_client.list_secrets.return_value = []


        mock_client.access_secret_version.side_effect = gcp_exceptions.NotFound(
            "Secret not found"
        )

        manager = GCPSecretManager(project_id=self.project_id)
        result = manager.get_secret("test-secret")

        assert result is None

    @patch("quantchain.core.secret_managers.gcp.GCP_AVAILABLE", True)
    @patch("quantchain.core.secret_managers.gcp.secretmanager")


def test_get_secret_permission_denied(self, mock_secretmanager):
        """Test permission denied error."""
        mock_client = MagicMock()
        mock_secretmanager.SecretManagerServiceClient.return_value = mock_client

        # Mock successful connection
        mock_client.list_secrets.return_value = []


        mock_client.access_secret_version.side_effect = gcp_exceptions.PermissionDenied(
            "Access denied"
        )

        manager = GCPSecretManager(project_id=self.project_id)
        result = manager.get_secret("test-secret")

        assert result is None

    @patch("quantchain.core.secret_managers.gcp.GCP_AVAILABLE", True)
    @patch("quantchain.core.secret_managers.gcp.secretmanager")


def test_get_secret_already_quantchain_prefix(self, mock_secretmanager):
        """Test get_secret with quantchain/ prefix."""
        mock_client = MagicMock()
        mock_secretmanager.SecretManagerServiceClient.return_value = mock_client

        # Mock successful connection
        mock_client.list_secrets.return_value = []

        # Mock secret response
        secret_value = b"test-value"
        mock_response = MagicMock()
        mock_response.payload.data = secret_value
        mock_client.access_secret_version.return_value = mock_response

        manager = GCPSecretManager(project_id=self.project_id)
        result = manager.get_secret("quantchain/existing-secret")

        assert result == "test-value"

        # Should not add quantchain/ prefix again
        expected_name = f"projects/{self.project_id}/secrets/quantchain/existing-secret/versions/latest"
        mock_client.access_secret_version.assert_called_once_with(
            request={"name": expected_name}
        )

    @patch("quantchain.core.secret_managers.gcp.GCP_AVAILABLE", True)
    @patch("quantchain.core.secret_managers.gcp.secretmanager")


def test_get_service_credentials_success(self, mock_secretmanager):
        """Test successful service credentials retrieval."""
        mock_client = MagicMock()
        mock_secretmanager.SecretManagerServiceClient.return_value = mock_client

        # Mock successful connection
        mock_client.list_secrets.return_value = []

        # Mock service credentials response
        service_credentials = {
            "api_key": "test-key-123",
            "api_secret": "test-secret-456",
            "base_url": "https://api.example.com",
        }
        secret_value = json.dumps(service_credentials).encode("utf-8")

        mock_response = MagicMock()
        mock_response.payload.data = secret_value
        mock_client.access_secret_version.return_value = mock_response

        manager = GCPSecretManager(project_id=self.project_id)
        result = manager.get_service_credentials("test-service")

        # Should return string values only
        expected_result = {k: str(v) for k, v in service_credentials.items()}
        assert result == expected_result

        # Verify correct secret name was built
        expected_name = f"projects/{self.project_id}/secrets/quantchain/test-service/versions/latest"
        mock_client.access_secret_version.assert_called_once_with(
            request={"name": expected_name}
        )

    @patch("quantchain.core.secret_managers.gcp.GCP_AVAILABLE", True)
    @patch("quantchain.core.secret_managers.gcp.secretmanager")


def test_get_service_credentials_not_found(self, mock_secretmanager):
        """Test service credentials not found."""
        mock_client = MagicMock()
        mock_secretmanager.SecretManagerServiceClient.return_value = mock_client

        # Mock successful connection
        mock_client.list_secrets.return_value = []


        mock_client.access_secret_version.side_effect = gcp_exceptions.NotFound(
            "Secret not found"
        )

        manager = GCPSecretManager(project_id=self.project_id)
        result = manager.get_service_credentials("test-service")

        assert result == {}

    @patch("quantchain.core.secret_managers.gcp.GCP_AVAILABLE", True)
    @patch("quantchain.core.secret_managers.gcp.secretmanager")


def test_get_service_credentials_invalid_json(self, mock_secretmanager):
        """Test service credentials with invalid JSON."""
        mock_client = MagicMock()
        mock_secretmanager.SecretManagerServiceClient.return_value = mock_client

        # Mock successful connection
        mock_client.list_secrets.return_value = []

        # Mock invalid JSON response
        invalid_json = b"invalid-json-string"

        mock_response = MagicMock()
        mock_response.payload.data = invalid_json
        mock_client.access_secret_version.return_value = mock_response

        manager = GCPSecretManager(project_id=self.project_id)
        result = manager.get_service_credentials("test-service")

        assert result == {"value": "invalid-json-string"}

    @patch("quantchain.core.secret_managers.gcp.GCP_AVAILABLE", True)
    @patch("quantchain.core.secret_managers.gcp.secretmanager")


def test_validate_service_success(self, mock_secretmanager):
        """Test successful service validation."""
        mock_client = MagicMock()
        mock_secretmanager.SecretManagerServiceClient.return_value = mock_client

        # Mock successful connection
        mock_client.list_secrets.return_value = []

        # Mock successful secret access
        secret_value = json.dumps({"api_key": "test-key"}).encode("utf-8")
        mock_response = MagicMock()
        mock_response.payload.data = secret_value
        mock_client.get_secret.return_value = mock_response

        manager = GCPSecretManager(project_id=self.project_id)
        result = manager.validate_service("test-service")

        assert result is True

        # Verify correct secret name was built (not version)
        expected_name = f"projects/{self.project_id}/secrets/quantchain/test-service"
        mock_client.get_secret.assert_called_once_with(request={"name": expected_name})

    @patch("quantchain.core.secret_managers.gcp.GCP_AVAILABLE", True)
    @patch("quantchain.core.secret_managers.gcp.secretmanager")


def test_validate_service_not_found(self, mock_secretmanager):
        """Test service validation when secret not found."""
        mock_client = MagicMock()
        mock_secretmanager.SecretManagerServiceClient.return_value = mock_client

        # Mock successful connection
        mock_client.list_secrets.return_value = []


        mock_client.get_secret.side_effect = gcp_exceptions.NotFound("Secret not found")

        manager = GCPSecretManager(project_id=self.project_id)
        result = manager.validate_service("test-service")

        assert result is False

    @patch("quantchain.core.secret_managers.gcp.GCP_AVAILABLE", True)
    @patch("quantchain.core.secret_managers.gcp.secretmanager")


def test_validate_service_permission_denied(self, mock_secretmanager):
        """Test service validation when access denied."""
        mock_client = MagicMock()
        mock_secretmanager.SecretManagerServiceClient.return_value = mock_client

        # Mock successful connection
        mock_client.list_secrets.return_value = []


        mock_client.get_secret.side_effect = gcp_exceptions.PermissionDenied(
            "Access denied"
        )

        manager = GCPSecretManager(project_id=self.project_id)
        result = manager.validate_service("test-service")

        assert result is False

    @patch("quantchain.core.secret_managers.gcp.GCP_AVAILABLE", True)
    @patch("quantchain.core.secret_managers.gcp.secretmanager")


def test_get_api_key_convenience(self, mock_secretmanager):
        """Test get_api_key convenience method."""
        mock_client = MagicMock()
        mock_secretmanager.SecretManagerServiceClient.return_value = mock_client

        # Mock successful connection
        mock_client.list_secrets.return_value = []

        # Mock service credentials with key field
        service_credentials = {
            "key": "test-api-key-123",  # Base class uses "key" field
            "secret": "test-api-secret",
        }
        secret_value = json.dumps(service_credentials).encode("utf-8")

        mock_response = MagicMock()
        mock_response.payload.data = secret_value
        mock_client.access_secret_version.return_value = mock_response

        manager = GCPSecretManager(project_id=self.project_id)
        result = manager.get_api_key("test-service")

        assert result == "test-api-key-123"

    @patch("quantchain.core.secret_managers.gcp.GCP_AVAILABLE", True)
    @patch("quantchain.core.secret_managers.gcp.secretmanager")


def test_get_api_secret_convenience(self, mock_secretmanager):
        """Test get_api_secret convenience method."""
        mock_client = MagicMock()
        mock_secretmanager.SecretManagerServiceClient.return_value = mock_client

        # Mock successful connection
        mock_client.list_secrets.return_value = []

        # Mock service credentials with secret field
        service_credentials = {
            "key": "test-api-key-123",
            "secret": "test-api-secret-456",  # Base class uses "secret" field
        }
        secret_value = json.dumps(service_credentials).encode("utf-8")

        mock_response = MagicMock()
        mock_response.payload.data = secret_value
        mock_client.access_secret_version.return_value = mock_response

        manager = GCPSecretManager(project_id=self.project_id)
        result = manager.get_api_secret("test-service")

        assert result == "test-api-secret-456"

    @patch("quantchain.core.secret_managers.gcp.GCP_AVAILABLE", True)
    @patch("quantchain.core.secret_managers.gcp.secretmanager")


def test_has_credentials_convenience(self, mock_secretmanager):
        """Test has_credentials convenience method."""
        mock_client = MagicMock()
        mock_secretmanager.SecretManagerServiceClient.return_value = mock_client

        # Mock successful connection
        mock_client.list_secrets.return_value = []

        # Mock service credentials
        service_credentials = {"key": "test-api-key-123", "secret": "test-api-secret"}
        secret_value = json.dumps(service_credentials).encode("utf-8")

        mock_response = MagicMock()
        mock_response.payload.data = secret_value
        mock_client.access_secret_version.return_value = mock_response

        manager = GCPSecretManager(project_id=self.project_id)
        result = manager.has_credentials("test-service")

        assert result is True

    @patch("quantchain.core.secret_managers.gcp.GCP_AVAILABLE", True)
    @patch("quantchain.core.secret_managers.gcp.secretmanager")


def test_has_credentials_empty(self, mock_secretmanager):
        """Test has_credentials convenience method with no credentials."""
        mock_client = MagicMock()
        mock_secretmanager.SecretManagerServiceClient.return_value = mock_client

        # Mock successful connection
        mock_client.list_secrets.return_value = []


        mock_client.access_secret_version.side_effect = gcp_exceptions.NotFound(
            "Secret not found"
        )

        manager = GCPSecretManager(project_id=self.project_id)
        result = manager.has_credentials("test-service")

        assert result is False
