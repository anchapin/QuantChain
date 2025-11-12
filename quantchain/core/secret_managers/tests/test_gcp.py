# Auto-generated test file for gcp.py
# Generated using Z.AI GLM-4.6 API

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Add the parent directory to the path to import the module
sys.path.insert(0, str(Path(__file__).parent.parent))


```python
"""Test cases for GCP Secret Manager implementation."""

import json
import os
from unittest.mock import MagicMock, Mock, patch

import pytest
from google.api_core import exceptions as gcp_exceptions

from gcp import GCPSecretManager


class TestGCPSecretManagerInit:
    """Test GCPSecretManager initialization."""

    @patch("gcp.secretmanager.SecretManagerServiceClient")
    @patch.dict(os.environ, {"GCP_PROJECT": "test-project"})
    def test_init_with_env_project_id(self, mock_client):
        """Test initialization with project ID from environment."""
        mock_client_instance = Mock()
        mock_client_instance.list_secrets.return_value = Mock()
        mock_client.return_value = mock_client_instance

        manager = GCPSecretManager()

        assert manager.project_id == "test-project"
        mock_client.assert_called_once()
        mock_client_instance.list_secrets.assert_called_once()

    @patch("gcp.secretmanager.SecretManagerServiceClient")
    def test_init_with_explicit_project_id(self, mock_client):
        """Test initialization with explicit project ID."""
        mock_client_instance = Mock()
        mock_client_instance.list_secrets.return_value = Mock()
        mock_client.return_value = mock_client_instance

        manager = GCPSecretManager(project_id="explicit-project")

        assert manager.project_id == "explicit-project"
        mock_client.assert_called_once()

    @patch("gcp.secretmanager.SecretManagerServiceClient")
    @patch.dict(os.environ, {}, clear=True)
    def test_init_without_project_id_raises_error(self, mock_client):
        """Test initialization fails without project ID."""
        with pytest.raises(ValueError, match="GCP project ID must be provided"):
            GCPSecretManager()

    @patch("gcp.secretmanager.SecretManagerServiceClient")
    @patch("gcp.service_account")
    def test_init_with_service_account_key(self, mock_service_account, mock_client):
        """Test initialization with service account key dict."""
        mock_credentials = Mock()
        mock_service_account.Credentials.from_service_account_info.return_value = mock_credentials
        mock_client_instance = Mock()
        mock_client_instance.list_secrets.return_value = Mock()
        mock_client.return_value = mock_client_instance

        service_key = {"type": "service_account", "project_id": "test"}
        manager = GCPSecretManager(project_id="test", service_account_key=service_key)

        mock_service_account.Credentials.from_service_account_info.assert_called_once_with(service_key)
        mock_client.assert_called_once_with(credentials=mock_credentials)

    @patch("gcp.secretmanager.SecretManagerServiceClient")
    @patch("gcp.service_account")
    def test_init_with_credentials_path(self, mock_service_account, mock_client):
        """Test initialization with credentials file path."""
        mock_credentials = Mock()
        mock_service_account.Credentials.from_service_account_file.return_value = mock_credentials
        mock_client_instance = Mock()
        mock_client_instance.list_secrets.return_value = Mock()
        mock_client.return_value = mock_client_instance

        manager = GCPSecretManager(
            project_id="test",
            credentials_path="/path/to/credentials.json"
        )

        mock_service_account.Credentials.from_service_account_file.assert_called_once_with(
            "/path/to/credentials.json"
        )
        mock_client.assert_called_once_with(credentials=mock_credentials)

    @patch("gcp.secretmanager.SecretManagerServiceClient")
    @patch.dict(os.environ, {"GOOGLE_APPLICATION_CREDENTIALS": "/default/path.json"})
    def test_init_with_default_adc(self, mock_client):
        """Test initialization with default ADC from environment."""
        mock_client_instance = Mock()
        mock_client_instance.list_secrets.return_value = Mock()
        mock_client.return_value = mock_client_instance

        manager = GCPSecretManager(project_id="test")

        mock_client.assert_called_once_with()

    @patch("gcp.secretmanager.SecretManagerServiceClient")
    def test_init_connection_failure_raises_error(self, mock_client):
        """Test initialization raises error on connection failure."""
        mock_client.side_effect = Exception("Connection failed")

        with pytest.raises(RuntimeError, match="Failed to connect to GCP Secret Manager"):
            GCPSecretManager(project_id="test")

    @patch("gcp.secretmanager.SecretManagerServiceClient")
    def test_init_with_additional_kwargs(self, mock_client):
        """Test initialization with additional client parameters."""
        mock_client_instance = Mock()
        mock_client_instance.list_secrets.return_value = Mock()
        mock_client.return_value = mock_client_instance

        manager = GCPSecretManager(
            project_id="test",
            client_options={"api_endpoint": "custom.endpoint.com"}
        )

        mock_client.assert_called_once_with(
            client_options={"api_endpoint": "custom.endpoint.com"}
        )


class TestGCPSecretManagerBuildSecretName:
    """Test secret name building methods."""

    def setup_method(self):
        """Set up test instance."""
        with patch("gcp.secretmanager.SecretManagerServiceClient"):
            self.manager = GCPSecretManager(project_id="test-project")

    def test_build_secret_name_with_quantchain_prefix(self):
        """Test building secret name with quantchain prefix."""
        result = self.manager._build_secret_name("quantchain/mysecret")
        expected = "projects/test-project/secrets/quantchain/mysecret"
        assert result == expected

    def test_build_secret_name_without_quantchain_prefix(self):
        """Test building secret name adds quantchain prefix."""
        result = self.manager._build_secret_name("mysecret")
        expected = "projects/test-project/secrets/quantchain/mysecret"
        assert result == expected

    def test_build_secret_name_with_leading_slash(self):
        """Test building secret name strips leading slashes."""
        result = self.manager._build_secret_name("/mysecret")
        expected = "projects/test-project/secrets/quantchain/mysecret"
        assert result == expected

    def test_build_secret_name_with_multiple_leading_slashes(self):
        """Test building secret name strips multiple leading slashes."""
        result = self.manager._build_secret_name("///mysecret")
        expected = "projects/test-project/secrets/quantchain/mysecret"
        assert result == expected

    def test_build_secret_version_name_default_version(self):
        """Test building secret version name with default version."""
        result = self.manager._build_secret_version_name("mysecret")
        expected = "projects/test-project/secrets/quantchain/mysecret/versions/latest"
        assert result == expected

    def test_build_secret_version_name_custom_version(self):
        """Test building secret version name with custom version."""
        result = self.manager._build_secret_version_name("mysecret", "v2")
        expected = "projects/test-project/secrets/quantchain/mysecret/versions/v2"
        assert result == expected

    def test_build_secret_version_name_with_quantchain_prefix(self):
        """Test building secret version name with quantchain prefix."""
        result = self.manager._build_secret_version_name("quantchain/mysecret", "v1")
        expected = "projects/test-project/secrets/quantchain/mysecret/versions/v1"
        assert result == expected


class TestGCPSecretManagerGetSecret:
    """Test secret retrieval methods."""

    def setup_method(self):
        """Set up test instance."""
        with patch("gcp.secretmanager.SecretManagerServiceClient"):
            self.manager = GCPSecretManager(project_id="test-project")
            self.manager.client = Mock()

    def test_get_secret_simple_value(self):
        """Test retrieving a simple string secret."""
        mock_response = Mock()
        mock_response.payload.data = b"simple_secret_value"
        self.manager.client.access_secret_version.return_value = mock_response

        result = self.manager.get_secret("mysecret")

        assert result == "simple_secret_value"
        self.manager.client.access_secret_version.assert_called_once()

    def test_get_secret_json_single_key(self):
        """Test retrieving JSON secret with single key returns value."""
        json_data = {"password": "secret123"}
        mock_response = Mock()
        mock_response.payload.data = json.dumps(json_data).encode()
        self.manager.client.access_secret_version.return_value = mock_response

        result = self.manager.get_secret("mysecret")

        assert result == "secret123"

    def test_get_secret_json_multiple_keys(self):
        """Test retrieving JSON secret with multiple keys returns JSON string."""
        json_data = {"username": "user", "password": "pass"}
        mock_response = Mock()
        mock_response.payload.data = json.dumps(json_data).encode()
        self.manager.client.access_secret_version.return_value = mock_response

        result = self.manager.get_secret("mysecret")

        assert result == json.dumps(json_data)

    def test_get_secret_with_quantchain_prefix(self):
        """Test retrieving secret with quantchain prefix."""
        mock_response = Mock()
        mock_response.payload.data = b"secret_value"
        self.manager.client.access_secret_version.return_value = mock_response

        result = self.manager.get_secret("quantchain/mysecret")

        assert result == "secret_value"
        expected_name = "projects/test-project/secrets/quantchain/mysecret/versions/latest"
        self.manager.client.access_secret_version.assert_called_once_with(
            request={"name": expected_name}
        )

    def test_get_secret_not_found(self):
        """Test retrieving non-existent secret returns None."""
        self.manager.client.access_secret_version.side_effect = gcp_exceptions.NotFound("Not found")

        result = self.manager.get_secret("nonexistent")

        assert result is None

    def test_get_secret_empty_payload(self):
        """Test retrieving secret with empty payload returns None."""
        mock_response = Mock()
        mock_response.payload = None
        self.manager.client.access_secret_version.return_value = mock_response

        result = self.manager.get_secret("empty_secret")

        assert result is None

    def test_get_secret_no_payload_data(self):
        """Test retrieving secret with no payload data returns None."""
        mock_response = Mock()
        mock_response.payload.data = None
        self.manager.client.access_secret_version.return_value = mock_response

        result = self.manager.get_secret("no_data_secret")

        assert result is None

    def test_get_secret_invalid_json(self):
        """Test retrieving secret with invalid JSON returns raw string."""
        mock_response = Mock()
        mock_response.payload.data = b"invalid_json{"
        self.manager.client.access_secret_version.return_value = mock_response

        result = self.manager.get_secret("invalid_json_secret")

        assert result == "invalid_json{"

    def test_get_secret_api_error(self):
        """Test retrieving secret with API error returns None."""
        self.manager.client.access_secret_version.side_effect = Exception("API Error")

        result = self.manager.get_secret("error_secret")

        assert result is None

    def test_get_secret_with_custom_version(self):
        """Test retrieving specific version of secret."""
        mock_response = Mock()
        mock_response.payload.data = b"versioned_secret"
        self.manager.client.access_secret_version.return_value = mock_response

        result = self.manager.get_secret("mysecret")

        assert result == "versioned_secret"


class TestGCPSecretManagerGetServiceCredentials:
    """Test service credentials retrieval."""

    def setup_method(self):
        """Set up test instance."""
        with patch("gcp.secretmanager.SecretManagerServiceClient"):
            self.manager = GCPSecretManager(project_id="test-project")
            self.manager.client = Mock()

    def test_get_service_credentials_json(self):
        """Test retrieving service credentials as JSON."""
        json_data = {"api_key": "key123", "secret": "secret456"}
        mock_response = Mock()
        mock_response.payload.data = json.dumps(json_data).encode()
        self.manager.client.access_secret_version.return_value = mock_response

        result = self.manager.get_service_credentials("myservice")

        expected = {"api_key": "key123", "secret": "secret456"}
        assert result == expected

    def test_get_service_credentials_plain_text(self):
        """Test retrieving service credentials as plain text."""
        mock_response = Mock()
        mock_response.payload.data = b"plain_text_credential"
        self.manager.client.access_secret_version.return_value = mock_response

        result = self.manager.get_service_credentials("myservice")

        expected = {"value": "plain_text_credential"}
        assert result == expected

    def test_get_service_credentials_not_found(self):
        """Test retrieving non-existent service credentials returns empty dict."""
        self.manager.client.access_secret_version.side_effect = gcp_exceptions.NotFound("Not found")

        result = self.manager.get_service_credentials("nonexistent")

        assert result == {}

    def test_get_service_credentials_empty_payload(self):
        """Test retrieving service credentials with empty payload returns empty dict."""
        mock_response = Mock()
        mock_response.payload = None
        self.manager.client.access_secret_version.return_value = mock_response

        result = self.manager.get_service_credentials("empty_service")

        assert result == {}

    def test_get_service_credentials_no_payload_data(self):
        """Test retrieving service credentials with no payload data returns empty dict."""
        mock_response = Mock()
        mock_response.payload.data = None
        self.manager.client.access_secret_version.return_value = mock_response

        result = self.manager.get_service_credentials("no_data_service")

        assert result == {}

    def test_get_service_credentials_invalid_json(self):
        """Test retrieving service credentials with invalid JSON returns value dict."""
        mock_response = Mock()
        mock_response.payload.data = b"invalid_json{"
        self.manager.client.access_secret_version.return_value = mock_response

        result = self.manager.get_service_credentials("invalid_service")

        expected = {"value": "invalid_json{"}
        assert result == expected

    def test_get_service_credentials_api_error(self):
        """Test retrieving service credentials with API error returns empty dict."""
        self.manager.client.access_secret_version.side_effect = Exception("API Error")

        result = self.manager.get_service_credentials("error_service")

        assert result == {}

    def test_get_service_credentials_converts_values_to_strings(self):
        """Test service credentials values are converted to strings."""
        json_data = {"number": 123, "boolean": True, "string": "text"}
        mock_response = Mock()
        mock_response.payload.data = json.dumps(json_data).encode()
        self.manager.client.access_secret_version.return_value = mock_response

        result = self.manager.get_service_credentials("typed_service")

        expected = {"number": "123", "boolean": "True", "string": "text"}
        assert result == expected


class TestGCPSecretManagerValidateService:
    """Test service validation methods."""

    def setup_method(self):
        """Set up test instance."""
        with patch("gcp.secretmanager.SecretManagerServiceClient"):
            self.manager = GCPSecretManager(project_id="test-project")
            self.manager.client = Mock()

    def test_validate_service_exists(self):
        """Test validating existing service returns True."""
        mock_response = Mock()
        mock_response.state.name = "ENABLED"
        self.manager.client.get_secret.return_value = mock_response

        result = self.manager.validate_service("myservice")

        assert result is True
        expected_name = "projects/test-project/secrets/quantchain/myservice"
        self.manager.client.get_secret.assert_called_once_with(request={"name": expected_name})

    def test_validate_service_destroyed(self):
        """Test validating destroyed service returns False."""
        mock_response = Mock()
        mock_response.state.name = "DESTROYED"
        self.manager.client.get_secret.return_value = mock_response

        result = self.manager.validate_service("destroyed_service")

        assert result is False

    def test_validate_service_not_found(self):
        """Test validating non-existent service returns False."""
        self.manager.client.get_secret.side_effect = gcp_exceptions.NotFound("Not found")

        result = self.manager.validate_service("nonexistent")

        assert result is False

    def test_validate_service_api_error(self):
        """Test validating service with API error returns False."""
        self.manager.client.get_secret.side_effect = Exception("API Error")

        result = self.manager.validate_service("error_service")

        assert result is False

    def test_validate_service_none_response(self):
        """Test validating service with None response returns False."""
        self.manager.client.get_secret.return_value = None

        result = self.manager.validate_service("null_service")

        assert result is False

    def test_validate_service_disabled_state(self):
        """Test validating disabled service returns True (not destroyed)."""
        mock_response = Mock()
        mock_response.state.name = "DISABLED"
        self.manager.client.get_secret.return_value = mock_response

        result = self.manager.validate_service("disabled_service")

        assert result is True


class TestGCPSecretManagerIntegration:
    """Integration tests for GCPSecretManager."""

    @patch("gcp.secretmanager.SecretManagerServiceClient")
    def test_full_workflow(self, mock_client):
        """Test complete workflow from initialization to secret retrieval."""
        # Setup mock client
        mock_client_instance = Mock()
        mock_client_instance.list_secrets.return_value = Mock()
        
        # Mock secret retrieval
        mock_secret_response = Mock()
        mock_secret_response.payload.data = b'{"api_key": "test123"}'
        mock_client_instance.access_secret_version.return_value = mock_secret_response
        
        # Mock service validation
        mock_validate_response = Mock()
        mock_validate_response.state.name = "ENABLED"
        mock_client_instance.get_secret.return_value = mock_validate_response
        
        mock_client.return_value = mock_client_instance

        # Initialize manager
        manager = GCPSecretManager(project_id="integration-test")
        
        # Test secret name building
        secret_name = manager._build_secret_name("test_secret")
        assert "integration-test" in secret_name
        assert "quantchain/test_secret" in secret_name
        
        # Test version name building
        version_name = manager._build_secret_version_name("test_secret", "v1")
        assert version_name.endswith("/versions/v1")
        
        # Test secret retrieval
        secret = manager.get_secret("test_secret")
        assert secret == '{"api_key": "test123"}'
        
        # Test service credentials
        creds = manager.get_service_credentials("test_service")
        assert creds == {"api_key": "test123"}
        
        # Test service validation
        is_valid = manager.validate_service("test_service")
        assert is_valid is True

    def test_import_error_handling(self):
        """Test ImportError is raised when google-cloud-secret-manager is not available."""
        with patch.dict("sys.modules", {"google.cloud.secretmanager": None}):
            with pytest.raises(ImportError, match="google-cloud-secret-manager library
