"""Comprehensive tests for Google Cloud Secret Manager implementation."""

import json
import os
import pytest
from unittest.mock import Mock, patch, MagicMock

# Import the module under test
try:
    from quantchain.core.secret_managers.gcp import GCPSecretManager
    try:
        from google.api_core import exceptions as gcp_exceptions
    except ImportError:
        # Mock exceptions for testing when google-cloud-secret-manager is not available
        class gcp_exceptions:
            class NotFound(Exception):
                pass
        
    _GCP_AVAILABLE = True
except ImportError:
    _GCP_AVAILABLE = False
    # Mock exceptions for when google-cloud-secret-manager is not available
    class gcp_exceptions:
        class NotFound(Exception):
            pass


@pytest.mark.skipif(not _GCP_AVAILABLE, reason="google-cloud-secret-manager not installed")
@pytest.mark.unit
class TestGCPSecretManager:
    """Test GCP Secret Manager implementation."""

    def test_init_with_explicit_project_id(self) -> None:
        """Test initialization with explicit project ID."""
        with patch("google.cloud.secretmanager.SecretManagerServiceClient") as mock_client:
            mock_instance = Mock()
            mock_instance.list_secrets.return_value = Mock()
            mock_client.return_value = mock_instance

            manager = GCPSecretManager(project_id="test-project")

            assert manager.project_id == "test-project"
            mock_instance.list_secrets.assert_called_once()

    def test_init_with_env_project_id(self) -> None:
        """Test initialization with environment variable project ID."""
        with patch.dict(os.environ, {"GCP_PROJECT": "env-project"}):
            with patch("google.cloud.secretmanager.SecretManagerServiceClient") as mock_client:
                mock_instance = Mock()
                mock_instance.list_secrets.return_value = Mock()
                mock_client.return_value = mock_instance

                manager = GCPSecretManager()

                assert manager.project_id == "env-project"

    def test_init_missing_project_id(self) -> None:
        """Test initialization fails without project ID."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="GCP project ID must be provided"):
                GCPSecretManager()

    def test_init_with_service_account_dict(self) -> None:
        """Test initialization with service account key dictionary."""
        service_account_key = {
            "type": "service_account", 
            "project_id": "test-project",
            "private_key_id": "test-key-id",
            "private_key": "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n",
            "client_email": "test@test-project.iam.gserviceaccount.com",
            "client_id": "123456789",
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token"
        }
        
        with patch("google.cloud.secretmanager.SecretManagerServiceClient") as mock_client:
            with patch("google.oauth2.service_account.Credentials") as mock_credentials:
                mock_instance = Mock()
                mock_instance.list_secrets.return_value = Mock()
                mock_client.return_value = mock_instance
                
                mock_creds = Mock()
                mock_credentials.from_service_account_info.return_value = mock_creds

                manager = GCPSecretManager(
                    project_id="test-project",
                    service_account_key=service_account_key
                )

                assert manager.project_id == "test-project"
                mock_credentials.from_service_account_info.assert_called_once_with(service_account_key)

    def test_init_with_credentials_path(self) -> None:
        """Test initialization with credentials file path."""
        # Create a temporary service account file
        import tempfile
        service_account_key = {
            "type": "service_account",
            "project_id": "test-project",
            "private_key_id": "test-key-id",
            "private_key": "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n",
            "client_email": "test@test-project.iam.gserviceaccount.com",
            "client_id": "123456789",
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token"
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            import json
            json.dump(service_account_key, f)
            temp_path = f.name
        
        try:
            with patch("google.cloud.secretmanager.SecretManagerServiceClient") as mock_client:
                with patch("google.oauth2.service_account.Credentials") as mock_credentials:
                    mock_instance = Mock()
                    mock_instance.list_secrets.return_value = Mock()
                    mock_client.return_value = mock_instance
                    
                    mock_creds = Mock()
                    mock_credentials.from_service_account_file.return_value = mock_creds

                    manager = GCPSecretManager(
                        project_id="test-project",
                        credentials_path=temp_path
                    )

                    assert manager.project_id == "test-project"
                    mock_credentials.from_service_account_file.assert_called_once_with(temp_path)
        finally:
            import os
            os.unlink(temp_path)

    def test_init_with_env_credentials(self) -> None:
        """Test initialization with environment variable credentials."""
        with patch.dict(os.environ, {"GOOGLE_APPLICATION_CREDENTIALS": "/path/to/creds.json"}):
            with patch("google.cloud.secretmanager.SecretManagerServiceClient") as mock_client:
                mock_instance = Mock()
                mock_instance.list_secrets.return_value = Mock()
                mock_client.return_value = mock_instance

                manager = GCPSecretManager(project_id="test-project")

                assert manager.project_id == "test-project"

    def test_init_connection_failure(self) -> None:
        """Test initialization with connection failure."""
        with patch("google.cloud.secretmanager.SecretManagerServiceClient") as mock_client:
            mock_client.side_effect = Exception("Connection failed")

            with pytest.raises(RuntimeError, match="Failed to connect to GCP Secret Manager"):
                GCPSecretManager(project_id="test-project")

    def test_build_secret_name(self) -> None:
        """Test building secret name."""
        with patch("google.cloud.secretmanager.SecretManagerServiceClient") as mock_client:
            mock_instance = Mock()
            mock_instance.list_secrets.return_value = Mock()
            mock_client.return_value = mock_instance

            manager = GCPSecretManager(project_id="test-project")

            # Test various key formats
            assert manager._build_secret_name("test") == "projects/test-project/secrets/quantchain/test"
            assert manager._build_secret_name("quantchain/test") == "projects/test-project/secrets/quantchain/test"
            assert manager._build_secret_name("/test") == "projects/test-project/secrets/quantchain/test"
            assert manager._build_secret_name("/quantchain/test") == "projects/test-project/secrets/quantchain/test"

    def test_build_secret_version_name(self) -> None:
        """Test building secret version name."""
        with patch("google.cloud.secretmanager.SecretManagerServiceClient") as mock_client:
            mock_instance = Mock()
            mock_instance.list_secrets.return_value = Mock()
            mock_client.return_value = mock_instance

            manager = GCPSecretManager(project_id="test-project")

            # Test default version
            assert manager._build_secret_version_name("test") == "projects/test-project/secrets/quantchain/test/versions/latest"
            
            # Test specific version
            assert manager._build_secret_version_name("test", "2") == "projects/test-project/secrets/quantchain/test/versions/2"

    def test_get_secret_success_string(self) -> None:
        """Test successful secret retrieval as string."""
        with patch("google.cloud.secretmanager.SecretManagerServiceClient") as mock_client:
            mock_instance = Mock()
            mock_instance.list_secrets.return_value = Mock()
            
            # Mock successful response
            mock_payload = Mock()
            mock_payload.data = b"test_secret_value"
            mock_response = Mock()
            mock_response.payload = mock_payload
            mock_instance.access_secret_version.return_value = mock_response
            mock_client.return_value = mock_instance

            manager = GCPSecretManager(project_id="test-project")
            result = manager.get_secret("test_secret")

            assert result == "test_secret_value"

    def test_get_secret_success_json_single_value(self) -> None:
        """Test successful secret retrieval as JSON with single value."""
        with patch("google.cloud.secretmanager.SecretManagerServiceClient") as mock_client:
            mock_instance = Mock()
            mock_instance.list_secrets.return_value = Mock()
            
            # Mock successful response with JSON
            mock_payload = Mock()
            mock_payload.data = b'{"key": "value"}'
            mock_response = Mock()
            mock_response.payload = mock_payload
            mock_instance.access_secret_version.return_value = mock_response
            mock_client.return_value = mock_instance

            manager = GCPSecretManager(project_id="test-project")
            result = manager.get_secret("test_secret")

            assert result == "value"

    def test_get_secret_success_json_multiple_values(self) -> None:
        """Test successful secret retrieval as JSON with multiple values."""
        with patch("google.cloud.secretmanager.SecretManagerServiceClient") as mock_client:
            mock_instance = Mock()
            mock_instance.list_secrets.return_value = Mock()
            
            # Mock successful response with JSON
            mock_payload = Mock()
            mock_payload.data = b'{"key1": "value1", "key2": "value2"}'
            mock_response = Mock()
            mock_response.payload = mock_payload
            mock_instance.access_secret_version.return_value = mock_response
            mock_client.return_value = mock_instance

            manager = GCPSecretManager(project_id="test-project")
            result = manager.get_secret("test_secret")

            assert result == '{"key1": "value1", "key2": "value2"}'

    def test_get_secret_with_quantchain_prefix(self) -> None:
        """Test getting secret with quantchain prefix in key."""
        with patch("google.cloud.secretmanager.SecretManagerServiceClient") as mock_client:
            mock_instance = Mock()
            mock_instance.list_secrets.return_value = Mock()
            
            mock_payload = Mock()
            mock_payload.data = b"test_value"
            mock_response = Mock()
            mock_response.payload = mock_payload
            mock_instance.access_secret_version.return_value = mock_response
            mock_client.return_value = mock_instance

            manager = GCPSecretManager(project_id="test-project")
            
            # Test with quantchain prefix
            result = manager.get_secret("quantchain/test")
            assert result == "test_value"
            
            # Verify the correct secret name was used (quantchain/ is not duplicated)
            expected_name = "projects/test-project/secrets/quantchain/test/versions/latest"
            mock_instance.access_secret_version.assert_called_with(request={"name": expected_name})

    def test_get_secret_not_found(self) -> None:
        """Test secret not found case."""
        with patch("google.cloud.secretmanager.SecretManagerServiceClient") as mock_client:
            mock_instance = Mock()
            mock_instance.list_secrets.return_value = Mock()
            mock_instance.access_secret_version.side_effect = gcp_exceptions.NotFound("Secret not found")
            mock_client.return_value = mock_instance

            manager = GCPSecretManager(project_id="test-project")
            result = manager.get_secret("nonexistent_secret")

            assert result is None

    def test_get_secret_no_payload(self) -> None:
        """Test secret retrieval when no payload is returned."""
        with patch("google.cloud.secretmanager.SecretManagerServiceClient") as mock_client:
            mock_instance = Mock()
            mock_instance.list_secrets.return_value = Mock()
            mock_instance.access_secret_version.return_value = {}
            mock_client.return_value = mock_instance

            manager = GCPSecretManager(project_id="test-project")
            result = manager.get_secret("test_secret")

            assert result is None

    def test_get_secret_no_payload_data(self) -> None:
        """Test secret retrieval when payload has no data."""
        with patch("google.cloud.secretmanager.SecretManagerServiceClient") as mock_client:
            mock_instance = Mock()
            mock_instance.list_secrets.return_value = Mock()
            
            mock_payload = Mock()
            del mock_payload.data  # Remove data attribute
            mock_response = {"payload": mock_payload}
            mock_instance.access_secret_version.return_value = mock_response
            mock_client.return_value = mock_instance

            manager = GCPSecretManager(project_id="test-project")
            result = manager.get_secret("test_secret")

            assert result is None

    def test_get_secret_other_exception(self) -> None:
        """Test secret retrieval with other exception."""
        with patch("google.cloud.secretmanager.SecretManagerServiceClient") as mock_client:
            mock_instance = Mock()
            mock_instance.list_secrets.return_value = Mock()
            mock_instance.access_secret_version.side_effect = Exception("Some error")
            mock_client.return_value = mock_instance

            manager = GCPSecretManager(project_id="test-project")
            result = manager.get_secret("test_secret")

            assert result is None

    def test_get_service_credentials_success(self) -> None:
        """Test successful service credentials retrieval."""
        with patch("google.cloud.secretmanager.SecretManagerServiceClient") as mock_client:
            mock_instance = Mock()
            mock_instance.list_secrets.return_value = Mock()
            
            mock_payload = Mock()
            mock_payload.data = b'{"api_key": "key123", "api_secret": "secret123"}'
            mock_response = Mock()
            mock_response.payload = mock_payload
            mock_instance.access_secret_version.return_value = mock_response
            mock_client.return_value = mock_instance

            manager = GCPSecretManager(project_id="test-project")
            result = manager.get_service_credentials("alpaca")

            assert result == {"api_key": "key123", "api_secret": "secret123"}

    def test_get_service_credentials_not_json(self) -> None:
        """Test service credentials retrieval with non-JSON string."""
        with patch("google.cloud.secretmanager.SecretManagerServiceClient") as mock_client:
            mock_instance = Mock()
            mock_instance.list_secrets.return_value = Mock()
            
            mock_payload = Mock()
            mock_payload.data = b"plain_text_secret"
            mock_response = Mock()
            mock_response.payload = mock_payload
            mock_instance.access_secret_version.return_value = mock_response
            mock_client.return_value = mock_instance

            manager = GCPSecretManager(project_id="test-project")
            result = manager.get_service_credentials("alpaca")

            assert result == {"value": "plain_text_secret"}

    def test_get_service_credentials_not_found(self) -> None:
        """Test service credentials not found."""
        with patch("google.cloud.secretmanager.SecretManagerServiceClient") as mock_client:
            mock_instance = Mock()
            mock_instance.list_secrets.return_value = Mock()
            mock_instance.access_secret_version.side_effect = gcp_exceptions.NotFound("Secret not found")
            mock_client.return_value = mock_instance

            manager = GCPSecretManager(project_id="test-project")
            result = manager.get_service_credentials("nonexistent_service")

            assert result == {}

    def test_get_service_credentials_no_payload(self) -> None:
        """Test service credentials with no payload."""
        with patch("google.cloud.secretmanager.SecretManagerServiceClient") as mock_client:
            mock_instance = Mock()
            mock_instance.list_secrets.return_value = Mock()
            mock_instance.access_secret_version.return_value = {}
            mock_client.return_value = mock_instance

            manager = GCPSecretManager(project_id="test-project")
            result = manager.get_service_credentials("alpaca")

            assert result == {}

    def test_validate_service_success(self) -> None:
        """Test successful service validation."""
        with patch("google.cloud.secretmanager.SecretManagerServiceClient") as mock_client:
            mock_instance = Mock()
            mock_instance.list_secrets.return_value = Mock()
            
            mock_secret = Mock()
            mock_secret.state.name = "ENABLED"
            mock_instance.get_secret.return_value = mock_secret
            mock_client.return_value = mock_instance

            manager = GCPSecretManager(project_id="test-project")
            result = manager.validate_service("alpaca")

            assert result is True

    def test_validate_service_destroyed(self) -> None:
        """Test service validation for destroyed secret."""
        with patch("google.cloud.secretmanager.SecretManagerServiceClient") as mock_client:
            mock_instance = Mock()
            mock_instance.list_secrets.return_value = Mock()
            
            mock_secret = Mock()
            mock_secret.state.name = "DESTROYED"
            mock_instance.get_secret.return_value = mock_secret
            mock_client.return_value = mock_instance

            manager = GCPSecretManager(project_id="test-project")
            result = manager.validate_service("alpaca")

            assert result is False

    def test_validate_service_not_found(self) -> None:
        """Test service validation when not found."""
        with patch("google.cloud.secretmanager.SecretManagerServiceClient") as mock_client:
            mock_instance = Mock()
            mock_instance.list_secrets.return_value = Mock()
            mock_instance.get_secret.side_effect = gcp_exceptions.NotFound("Secret not found")
            mock_client.return_value = mock_instance

            manager = GCPSecretManager(project_id="test-project")
            result = manager.validate_service("nonexistent_service")

            assert result is False

    def test_validate_service_other_exception(self) -> None:
        """Test service validation with other exception."""
        with patch("google.cloud.secretmanager.SecretManagerServiceClient") as mock_client:
            mock_instance = Mock()
            mock_instance.list_secrets.return_value = Mock()
            mock_instance.get_secret.side_effect = Exception("Some error")
            mock_client.return_value = mock_instance

            manager = GCPSecretManager(project_id="test-project")
            result = manager.validate_service("alpaca")

            assert result is False
