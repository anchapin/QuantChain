"""
Comprehensive test suite for secret managers module.
"""

import os
import pytest
from unittest.mock import Mock, patch

# Try to import the secret manager modules, skip if not available
try:
    from quantchain.core.secret_managers.env import EnvSecretManager
    from quantchain.core.secret_managers.gcp import GCPSecretManager
    from quantchain.core.secret_managers.aws import AWSSecretManager
    from quantchain.core.secret_managers.vault import VaultSecretManager
    SECRET_MANAGERS_AVAILABLE = True
except ImportError:
    SECRET_MANAGERS_AVAILABLE = False


@pytest.mark.skipif(not SECRET_MANAGERS_AVAILABLE, reason="Secret manager modules not available")
class TestEnvSecretManager:
    """Test environment variable secret manager."""

    def test_get_secret_exists(self) -> None:
        """Test getting an existing secret from environment."""
        # Set up test environment variable
        test_key = "TEST_SECRET_KEY"
        test_value = "test_secret_value"

        with patch.dict(os.environ, {test_key: test_value}):
            manager = EnvSecretManager()
            result = manager.get_secret(test_key)
            assert result == test_value

    def test_get_secret_not_exists(self) -> None:
        """Test getting a non-existent secret from environment."""
        with patch.dict(os.environ, {}, clear=True):
            manager = EnvSecretManager()
            result = manager.get_secret("NON_EXISTENT_KEY")
            assert result is None

    def test_init_default(self) -> None:
        """Test default initialization."""
        manager = EnvSecretManager()
        assert manager is not None


@pytest.mark.skipif(not SECRET_MANAGERS_AVAILABLE, reason="Secret manager modules not available")
class TestGCPSecretManager:
    """Test GCP secret manager."""

    @patch("quantchain.core.secret_managers.gcp.secretmanager.SecretManagerServiceClient")
    def test_get_secret_success(self, mock_client: Mock) -> None:
        """Test successful secret retrieval."""
        from google.cloud.secretmanager import SecretPayload

        # Mock the response
        mock_payload = Mock(spec=SecretPayload)
        mock_payload.data = b"secret_value"

        mock_response = Mock()
        mock_response.payload = mock_payload

        mock_client_instance = Mock()
        mock_client_instance.access_secret_version.return_value = mock_response
        mock_client.return_value = mock_client_instance

        manager = GCPSecretManager(project_id="test-project")
        result = manager.get_secret("test-secret")

        assert result == "secret_value"
        mock_client_instance.access_secret_version.assert_called_once()

    @patch("quantchain.core.secret_managers.gcp.secretmanager.SecretManagerServiceClient")
    def test_get_secret_not_found(self, mock_client: Mock) -> None:
        """Test secret not found."""
        from google.api_core import exceptions

        mock_client_instance = Mock()
        mock_client_instance.access_secret_version.side_effect = exceptions.NotFound("Secret not found")
        mock_client.return_value = mock_client_instance

        manager = GCPSecretManager(project_id="test-project")
        result = manager.get_secret("test-secret")

        assert result is None

    @patch("quantchain.core.secret_managers.gcp.secretmanager.SecretManagerServiceClient")
    def test_get_secret_permission_denied(self, mock_client: Mock) -> None:
        """Test permission denied when accessing secret."""
        from google.api_core import exceptions

        mock_client_instance = Mock()
        mock_client_instance.access_secret_version.side_effect = exceptions.PermissionDenied("Permission denied")
        mock_client.return_value = mock_client_instance

        manager = GCPSecretManager(project_id="test-project")
        result = manager.get_secret("test-secret")

        assert result is None

    def test_init_project_id(self) -> None:
        """Test initialization with project ID."""
        manager = GCPSecretManager(project_id="test-project")
        assert manager.project_id == "test-project"


@pytest.mark.skipif(not SECRET_MANAGERS_AVAILABLE, reason="Secret manager modules not available")
class TestAWSSecretManager:
    """Test AWS secret manager."""

    @patch("boto3.client")
    def test_get_secret_success(self, mock_boto_client: Mock) -> None:
        """Test successful secret retrieval."""
        # Mock the response
        mock_response = {
            'SecretString': 'aws_secret_value'
        }

        mock_client_instance = Mock()
        mock_client_instance.get_secret_value.return_value = mock_response
        mock_boto_client.return_value = mock_client_instance

        manager = AWSSecretManager(region_name="us-east-1")
        result = manager.get_secret("test-secret")

        assert result == "aws_secret_value"
        mock_client_instance.get_secret_value.assert_called_once()

    @patch("boto3.client")
    def test_get_secret_binary_success(self, mock_boto_client: Mock) -> None:
        """Test successful binary secret retrieval."""
        # Mock the response with binary secret
        mock_response = {
            'SecretBinary': b'binary_secret_value'
        }

        mock_client_instance = Mock()
        mock_client_instance.get_secret_value.return_value = mock_response
        mock_boto_client.return_value = mock_client_instance

        manager = AWSSecretManager(region_name="us-east-1")
        result = manager.get_secret("test-secret")

        assert result == b'binary_secret_value'

    @patch("boto3.client")
    def test_get_secret_not_found(self, mock_boto_client: Mock) -> None:
        """Test secret not found."""
        from botocore.exceptions import ClientError

        mock_client_instance = Mock()
        mock_client_instance.get_secret_value.side_effect = ClientError(
            {'Error': {'Code': 'ResourceNotFoundException'}}, 'GetSecretValue'
        )
        mock_boto_client.return_value = mock_client_instance

        manager = AWSSecretManager(region_name="us-east-1")
        result = manager.get_secret("test-secret")

        assert result is None

    def test_init_region(self) -> None:
        """Test initialization with region."""
        manager = AWSSecretManager(region_name="us-west-2")
        assert manager.region_name == "us-west-2"


@pytest.mark.skipif(not SECRET_MANAGERS_AVAILABLE, reason="Secret manager modules not available")
class TestVaultSecretManager:
    """Test Vault secret manager."""

    @patch("hvac.Client")
    def test_get_secret_success(self, mock_hvac_client: Mock) -> None:
        """Test successful secret retrieval."""
        # Mock the response
        mock_response = {
            'data': {
                'value': 'vault_secret_value'
            }
        }

        mock_client_instance = Mock()
        mock_client_instance.secrets.kv.v2.read_secret_version.return_value = mock_response
        mock_hvac_client.return_value = mock_client_instance

        manager = VaultSecretManager(url="https://vault.example.com", token="test-token")
        result = manager.get_secret("test-secret")

        assert result == "vault_secret_value"
        mock_client_instance.secrets.kv.v2.read_secret_version.assert_called_once_with(
            path="test-secret"
        )

    @patch("hvac.Client")
    def test_get_secret_not_found(self, mock_hvac_client: Mock) -> None:
        """Test secret not found."""
        from hvac.exceptions import InvalidPath

        mock_client_instance = Mock()
        mock_client_instance.secrets.kv.v2.read_secret_version.side_effect = InvalidPath()
        mock_hvac_client.return_value = mock_client_instance

        manager = VaultSecretManager(url="https://vault.example.com", token="test-token")
        result = manager.get_secret("test-secret")

        assert result is None

    def test_init_credentials(self) -> None:
        """Test initialization with credentials."""
        manager = VaultSecretManager(
            url="https://vault.example.com",
            token="test-token",
            namespace="admin"
        )
        assert manager.url == "https://vault.example.com"
        assert manager.token == "test-token"
        assert manager.namespace == "admin"


@pytest.mark.skipif(not SECRET_MANAGERS_AVAILABLE, reason="Secret manager modules not available")
class TestSecretManagerFactory:
    """Test secret manager factory."""

    def test_create_env_manager(self) -> None:
        """Test creating environment manager."""
        from quantchain.core.secret_managers.factory import SecretManagerFactory

        factory = SecretManagerFactory()
        manager = factory.create_manager("env")
        assert isinstance(manager, EnvSecretManager)

    def test_create_gcp_manager(self) -> None:
        """Test creating GCP manager."""
        from quantchain.core.secret_managers.factory import SecretManagerFactory

        factory = SecretManagerFactory()
        manager = factory.create_manager("gcp", project_id="test-project")
        assert isinstance(manager, GCPSecretManager)
        assert manager.project_id == "test-project"

    def test_create_aws_manager(self) -> None:
        """Test creating AWS manager."""
        from quantchain.core.secret_managers.factory import SecretManagerFactory

        factory = SecretManagerFactory()
        manager = factory.create_manager("aws", region_name="us-east-1")
        assert isinstance(manager, AWSSecretManager)
        assert manager.region_name == "us-east-1"

    def test_create_vault_manager(self) -> None:
        """Test creating Vault manager."""
        from quantchain.core.secret_managers.factory import SecretManagerFactory

        factory = SecretManagerFactory()
        manager = factory.create_manager(
            "vault",
            url="https://vault.example.com",
            token="test-token"
        )
        assert isinstance(manager, VaultSecretManager)
        assert manager.url == "https://vault.example.com"
        assert manager.token == "test-token"

    def test_create_unknown_manager(self) -> None:
        """Test creating unknown manager type."""
        from quantchain.core.secret_managers.factory import SecretManagerFactory

        factory = SecretManagerFactory()
        with pytest.raises(ValueError):
            factory.create_manager("unknown_type")
