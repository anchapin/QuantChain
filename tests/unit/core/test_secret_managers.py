"""Tests for secret manager implementations."""

import os
import pytest
from unittest.mock import Mock, patch

from quantchain.core.secret_managers import (
    SecretManager,
    EnvSecretManager,
    create_secret_manager,
    get_default_secret_manager,
)

# Optional imports for testing
try:
    from quantchain.core.secret_managers import VaultSecretManager
    _VAULT_AVAILABLE = True
except ImportError:
    _VAULT_AVAILABLE = False

try:
    from quantchain.core.secret_managers import AWSSecretsManager
    _AWS_AVAILABLE = True
except ImportError:
    _AWS_AVAILABLE = False

try:
    from quantchain.core.secret_managers import GCPSecretManager
    _GCP_AVAILABLE = True
except ImportError:
    _GCP_AVAILABLE = False


@pytest.mark.unit
class TestEnvSecretManager:
    """Test environment variable secret manager."""

    def test_init_with_defaults(self) -> None:
        """Test initialization with default settings."""
        with patch.dict(os.environ, {}):
            manager = EnvSecretManager()
            assert manager._credentials == {}

    def test_init_with_custom_env_file(self, tmp_path) -> None:
        """Test initialization with custom .env file."""
        env_file = tmp_path / "test.env"
        env_file.write_text("ALPACA_API_KEY=\"test_key\"\n")

        manager = EnvSecretManager(env_file=str(env_file))
        assert manager.get_service_credentials("alpaca")["key"] == "test_key"

    def test_get_api_key_from_env(self) -> None:
        """Test retrieving API key from environment."""
        with patch.dict(os.environ, {"ALPACA_API_KEY": "test_key"}):
            manager = EnvSecretManager()
            assert manager.get_api_key("alpaca") == "test_key"

    def test_get_api_secret_from_env(self) -> None:
        """Test retrieving API secret from environment."""
        with patch.dict(os.environ, {"ALPACA_API_SECRET": "test_secret"}):
            manager = EnvSecretManager()
            assert manager.get_api_secret("alpaca") == "test_secret"

    def test_get_service_credentials(self) -> None:
        """Test retrieving all service credentials."""
        with patch.dict(os.environ, {
            "ALPACA_API_KEY": "test_key",
            "ALPACA_API_SECRET": "test_secret"
        }):
            manager = EnvSecretManager()
            creds = manager.get_service_credentials("alpaca")
            assert creds["key"] == "test_key"
            assert creds["secret"] == "test_secret"

    def test_validate_service(self) -> None:
        """Test service validation."""
        with patch.dict(os.environ, {"ALPACA_API_KEY": "test_key"}):
            manager = EnvSecretManager()
            assert manager.validate_service("alpaca") is True
            assert manager.validate_service("nonexistent") is False

    def test_set_api_key(self) -> None:
        """Test setting API key."""
        manager = EnvSecretManager()
        manager.set_api_key("alpaca", "test_key", "test_secret")
        assert manager.get_api_key("alpaca") == "test_key"
        assert manager.get_api_secret("alpaca") == "test_secret"

    def test_remove_service(self) -> None:
        """Test removing service credentials."""
        manager = EnvSecretManager()
        manager.set_api_key("alpaca", "test_key")
        manager.remove_service("alpaca")
        assert manager.get_api_key("alpaca") is None


@pytest.mark.unit
class TestSecretManagerFactory:
    """Test secret manager factory."""

    def test_create_env_manager(self) -> None:
        """Test creating environment secret manager."""
        with patch.dict(os.environ, {"QUANTCHAIN_SECRET_BACKEND": "env"}):
            manager = create_secret_manager()
            assert isinstance(manager, EnvSecretManager)

    @pytest.mark.skipif(not _VAULT_AVAILABLE, reason="hvac not installed")
    def test_create_vault_manager(self) -> None:
        """Test creating Vault secret manager."""
        with patch("hvac.Client") as mock_client:
            mock_instance = Mock()
            mock_instance.is_authenticated.return_value = True
            mock_client.return_value = mock_instance

            manager = create_secret_manager(
                backend="vault",
                url="https://vault.example.com",
                token="test_token"
            )
            assert isinstance(manager, VaultSecretManager)

    @pytest.mark.skipif(not _AWS_AVAILABLE, reason="boto3 not installed")
    def test_create_aws_manager(self) -> None:
        """Test creating AWS Secrets Manager."""
        with patch("boto3.Session") as mock_session:
            mock_client = Mock()
            mock_session.return_value.client.return_value = mock_client
            mock_client.list_secrets.return_value = {"SecretList": []}

            manager = create_secret_manager(
                backend="aws",
                region_name="us-east-1"
            )
            assert isinstance(manager, AWSSecretsManager)

    @pytest.mark.skipif(not _GCP_AVAILABLE, reason="google-cloud-secret-manager not installed")
    def test_create_gcp_manager(self) -> None:
        """Test creating GCP Secret Manager."""
        with patch("google.cloud.secretmanager.SecretManagerServiceClient") as mock_client:
            mock_instance = Mock()
            mock_client.return_value = mock_instance
            mock_instance.list_secrets.return_value = Mock()

            manager = create_secret_manager(
                backend="gcp",
                project_id="test-project"
            )
            assert isinstance(manager, GCPSecretManager)

    def test_unsupported_backend(self) -> None:
        """Test error for unsupported backend."""
        with pytest.raises(ValueError, match="Unsupported secret backend"):
            create_secret_manager(backend="unsupported")

    def test_get_default_manager(self) -> None:
        """Test getting default manager."""
        manager = get_default_secret_manager()
        assert isinstance(manager, SecretManager)


@pytest.mark.unit
class TestProductionSecretManagers:
    """Test production secret manager implementations (with mocks)."""

    @pytest.mark.skipif(not _VAULT_AVAILABLE, reason="hvac not installed")
    def test_vault_secret_manager(self) -> None:
        """Test Vault secret manager with mock."""
        with patch("hvac.Client") as mock_client:
            mock_instance = Mock()
            mock_instance.is_authenticated.return_value = True
            mock_client.return_value = mock_instance

            # Mock successful secret retrieval
            mock_instance.secrets.kv.v2.read_secret_version.return_value = {
                "data": {
                    "data": {"key": "test_value"}
                }
            }

            manager = VaultSecretManager(
                url="https://vault.example.com",
                token="test_token"
            )

            assert manager.get_secret("test/secret") == "test_value"
            assert manager.validate_service("alpaca") is True

    @pytest.mark.skipif(not _AWS_AVAILABLE, reason="boto3 not installed")
    def test_aws_secrets_manager(self) -> None:
        """Test AWS Secrets Manager with mock."""
        with patch("boto3.Session") as mock_session:
            mock_client = Mock()
            mock_session.return_value.client.return_value = mock_client
            mock_client.list_secrets.return_value = {"SecretList": []}

            # Mock successful secret retrieval
            mock_client.get_secret_value.return_value = {
                "SecretString": '{"key": "test_value"}'
            }

            manager = AWSSecretsManager(region_name="us-east-1")

            assert manager.get_secret("quantchain/alpaca") == '{"key": "test_value"}'
            assert manager.validate_service("alpaca") is True

    @pytest.mark.skipif(not _GCP_AVAILABLE, reason="google-cloud-secret-manager not installed")
    def test_gcp_secret_manager(self) -> None:
        """Test GCP Secret Manager with mock."""
        with patch("google.cloud.secretmanager.SecretManagerServiceClient") as mock_client:
            mock_instance = Mock()
            mock_client.return_value = mock_instance

            # Mock successful secret retrieval
            mock_payload = Mock()
            mock_payload.data = b'{"key": "test_value"}'
            mock_instance.access_secret_version.return_value = {
                "payload": mock_payload
            }
            mock_instance.list_secrets.return_value = Mock()

            manager = GCPSecretManager(project_id="test-project")

            assert manager.get_secret("quantchain/alpaca") == '{"key": "test_value"}'
            assert manager.validate_service("alpaca") is True
