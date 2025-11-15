"""Tests for secret manager implementations."""




import os
from unittest.mock import Mock, patch
import pytest
from quantchain.core.secret_managers import (
from quantchain.core.secret_managers import VaultSecretManager
from quantchain.core.secret_managers import AWSSecretsManager
from quantchain.core.secret_managers import GCPSecretManager
import tempfile
import tempfile
import tempfile
import tempfile
import tempfile
import tempfile
from google.api_core import exceptions
import hvac

    EnvSecretManager,
    SecretManager,
    create_secret_manager,
    get_default_secret_manager,
)

# Optional imports for testing
try:

    _VAULT_AVAILABLE = True
except ImportError:
    _VAULT_AVAILABLE = False

try:

    _AWS_AVAILABLE = True
except ImportError:
    _AWS_AVAILABLE = False

try:

    _GCP_AVAILABLE = True
except ImportError:
    _GCP_AVAILABLE = False


@pytest.mark.unit


class TestEnvSecretManager:
    """Test environment variable secret manager."""



def test_init_with_defaults(self) -> None:
        """Test initialization with default settings."""
        # Create a temporary directory for test to avoid .env file loading

        with tempfile.TemporaryDirectory() as tmpdir:
            # Manually patch environment
            original_env = os.environ.copy()
            os.environ.clear()
            try:
                # Ensure no .env file exists in temp dir
                manager = EnvSecretManager(
                    env_file=os.path.join(tmpdir, "nonexistent.env")
                )
                assert manager._credentials == {}
            finally:
                # Restore environment
                os.environ.clear()
                os.environ.update(original_env)



def test_init_with_custom_env_file(self, tmp_path) -> None:
        """Test initialization with custom .env file."""
        env_file = tmp_path / "test.env"
        env_file.write_text('ALPACA_API_KEY="test_key"\n')

        manager = EnvSecretManager(env_file=str(env_file))
        assert manager.get_service_credentials("alpaca")["key"] == "test_key"



def test_get_api_key_from_env(self) -> None:
        """Test retrieving API key from environment."""
        # Manually patch environment
        original_env = os.environ.copy()
        os.environ.clear()
        os.environ["ALPACA_API_KEY"] = "test_key"
        try:
            manager = EnvSecretManager()
            assert manager.get_api_key("alpaca") == "test_key"
        finally:
            # Restore environment
            os.environ.clear()
            os.environ.update(original_env)



def test_get_api_secret_from_env(self) -> None:
        """Test retrieving API secret from environment."""

        with tempfile.TemporaryDirectory() as tmpdir:
            # Manually patch environment
            original_env = os.environ.copy()
            os.environ.clear()
            os.environ.update(
                {"ALPACA_API_KEY": "test_key", "ALPACA_API_SECRET": "test_secret"}
            )
            try:
                manager = EnvSecretManager(
                    env_file=os.path.join(tmpdir, "nonexistent.env")
                )
                assert manager.get_api_secret("alpaca") == "test_secret"
            finally:
                # Restore environment
                os.environ.clear()
                os.environ.update(original_env)



def test_get_service_credentials(self) -> None:
        """Test retrieving all service credentials."""

        with tempfile.TemporaryDirectory() as tmpdir:
            # Manually patch environment
            original_env = os.environ.copy()
            os.environ.clear()
            os.environ.update(
                {"ALPACA_API_KEY": "test_key", "ALPACA_API_SECRET": "test_secret"}
            )
            try:
                manager = EnvSecretManager(
                    env_file=os.path.join(tmpdir, "nonexistent.env")
                )
                creds = manager.get_service_credentials("alpaca")
                assert creds["key"] == "test_key"
                assert creds["secret"] == "test_secret"
            finally:
                # Restore environment
                os.environ.clear()
                os.environ.update(original_env)



def test_validate_service(self) -> None:
        """Test service validation."""

        with tempfile.TemporaryDirectory() as tmpdir:
            # Manually patch environment
            original_env = os.environ.copy()
            os.environ.clear()
            os.environ["ALPACA_API_KEY"] = "test_key"
            try:
                manager = EnvSecretManager(
                    env_file=os.path.join(tmpdir, "nonexistent.env")
                )
                assert manager.validate_service("alpaca") is True
                assert manager.validate_service("nonexistent") is False
            finally:
                # Restore environment
                os.environ.clear()
                os.environ.update(original_env)



def test_set_api_key(self) -> None:
        """Test setting API key."""

        with tempfile.TemporaryDirectory() as tmpdir:
            manager = EnvSecretManager(env_file=os.path.join(tmpdir, "test.env"))
            manager.set_api_key(
                "alpaca",
                "ABCDEFGHIJKLMNOPQR",
                "ABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890AB++",
            )
            assert manager.get_api_key("alpaca") == "ABCDEFGHIJKLMNOPQR"
            assert (
                manager.get_api_secret("alpaca")
                == "ABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890AB++"
            )



def test_remove_service(self) -> None:
        """Test removing service credentials."""

        with tempfile.TemporaryDirectory() as tmpdir:
            manager = EnvSecretManager(env_file=os.path.join(tmpdir, "test.env"))
            manager.set_api_key(
                "alpaca",
                "ABCDEFGHIJKLMNOPQR",
                "ABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890AB++",
            )
            manager.remove_service("alpaca")
            assert manager.get_api_key("alpaca") is None


@pytest.mark.unit


class TestSecretManagerFactory:
    """Test secret manager factory."""



def test_create_env_manager(self) -> None:
        """Test creating environment secret manager."""
        # Manually patch environment
        original_env = os.environ.copy()
        os.environ.clear()
        os.environ["QUANTCHAIN_SECRET_BACKEND"] = "env"
        try:
            manager = create_secret_manager()
            assert isinstance(manager, EnvSecretManager)
        finally:
            # Restore environment
            os.environ.clear()
            os.environ.update(original_env)

    @pytest.mark.skipif(not _VAULT_AVAILABLE, reason="hvac not installed")


def test_create_vault_manager(self) -> None:
        """Test creating Vault secret manager."""
        with patch("hvac.Client") as mock_client:
            mock_instance = Mock()
            mock_instance.is_authenticated.return_value = True
            mock_client.return_value = mock_instance

            manager = create_secret_manager(
                backend="vault", url="https://vault.example.com", token="test_token"
            )
            assert isinstance(manager, VaultSecretManager)

    @pytest.mark.skipif(not _AWS_AVAILABLE, reason="boto3 not installed")


def test_create_aws_manager(self) -> None:
        """Test creating AWS Secrets Manager."""
        with patch("boto3.Session") as mock_session:
            mock_client = Mock()
            mock_session.return_value.client.return_value = mock_client
            mock_client.list_secrets.return_value = {"SecretList": []}

            manager = create_secret_manager(backend="aws", region_name="us-east-1")
            assert isinstance(manager, AWSSecretsManager)

    @pytest.mark.skipif(
        not _GCP_AVAILABLE, reason="google-cloud-secret-manager not installed"
    )


def test_create_gcp_manager(self) -> None:
        """Test creating GCP Secret Manager."""
        with patch(
            "google.cloud.secretmanager.SecretManagerServiceClient"
        ) as mock_client:
            mock_instance = Mock()
            mock_client.return_value = mock_instance
            mock_instance.list_secrets.return_value = Mock()

            manager = create_secret_manager(backend="gcp", project_id="test-project")
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
                "data": {"data": {"key": "test_value"}}
            }

            manager = VaultSecretManager(
                url="https://vault.example.com", token="test_token"
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
            mock_client.get_secret_value.return_value = {"SecretString": "test_value"}

            manager = AWSSecretsManager(region_name="us-east-1")

            assert manager.get_secret("quantchain/alpaca") == "test_value"
            assert manager.validate_service("alpaca") is True

    @pytest.mark.skipif(
        not _GCP_AVAILABLE, reason="google-cloud-secret-manager not installed"
    )


def test_gcp_secret_manager(self) -> None:
        """Test GCP Secret Manager with mock."""
        with patch(
            "google.cloud.secretmanager.SecretManagerServiceClient"
        ) as mock_client:
            mock_instance = Mock()
            mock_client.return_value = mock_instance

            # Mock successful secret retrieval
            mock_payload = Mock()
            mock_payload.data = b'{"key": "test_value"}'
            mock_instance.access_secret_version.return_value = {"payload": mock_payload}
            mock_instance.list_secrets.return_value = Mock()

            manager = GCPSecretManager(project_id="test-project")

            assert manager.get_secret("quantchain/alpaca") == '{"key": "test_value"}'
            assert manager.validate_service("alpaca") is True


@pytest.mark.skipif(
    not _GCP_AVAILABLE, reason="google-cloud-secret-manager not installed"
)
@pytest.mark.unit


class TestGCPSecretManagerDetailed:
    """Detailed tests for GCP secret manager."""



def test_init(self) -> None:
        """Test initialization."""
        manager = GCPSecretManager(project_id="test-project")
        assert manager.project_id == "test-project"



def test_init_with_env_var(self) -> None:
        """Test initialization with environment variable."""
        with patch.dict(os.environ, {"GCP_PROJECT": "env-project"}):
            manager = GCPSecretManager()
            assert manager.project_id == "env-project"



def test_init_missing_project_id(self) -> None:
        """Test initialization fails without project ID."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="GCP project ID must be provided"):
                GCPSecretManager()

    @patch(
        "quantchain.core.secret_managers.gcp.secretmanager.SecretManagerServiceClient"
    )


def test_get_secret_success(self, mock_client: Mock) -> None:
        """Test successful secret retrieval."""
        # Mock client and response
        mock_response = Mock()
        mock_response.payload.data = b"test-value"
        mock_client_instance = Mock()
        mock_client_instance.access_secret_version.return_value = mock_response
        mock_client.return_value = mock_client_instance

        manager = GCPSecretManager(project_id="test-project")
        value = manager.get_secret("test-secret")

        assert value == "test-value"
        mock_client_instance.access_secret_version.assert_called_once()

    @patch(
        "quantchain.core.secret_managers.gcp.secretmanager.SecretManagerServiceClient"
    )


def test_get_secret_not_found(self, mock_client: Mock) -> None:
        """Test secret not found."""

        mock_client_instance = Mock()
        mock_client_instance.access_secret_version.side_effect = exceptions.NotFound(
            "Secret not found"
        )
        mock_client.return_value = mock_client_instance

        manager = GCPSecretManager(project_id="test-project")
        value = manager.get_secret("test-secret")

        assert value is None

    @patch(
        "quantchain.core.secret_managers.gcp.secretmanager.SecretManagerServiceClient"
    )


def test_set_secret_success(self, mock_client: Mock) -> None:
        """Test successful secret creation/update."""
        # Mock client and response
        mock_response = Mock()
        mock_response.name = "projects/test-project/secrets/test-secret/versions/1"
        mock_client_instance = Mock()
        mock_client_instance.add_secret_version.return_value = mock_response
        mock_client.return_value = mock_client_instance

        manager = GCPSecretManager(project_id="test-project")
        success = manager.set_secret("test-secret", "test-value")

        assert success is True
        mock_client_instance.add_secret_version.assert_called_once()


@pytest.mark.skipif(not _VAULT_AVAILABLE, reason="hvac not installed")
@pytest.mark.unit


class TestVaultSecretManagerDetailed:
    """Detailed tests for Vault secret manager."""



def test_init_missing_url(self) -> None:
        """Test initialization fails without URL."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="Vault URL must be provided"):
                VaultSecretManager()



def test_init_missing_token(self) -> None:
        """Test initialization fails without token."""
        with patch.dict(os.environ, {"VAULT_ADDR": "http://vault:8200"}, clear=True):
            with pytest.raises(ValueError, match="Vault token must be provided"):
                VaultSecretManager()

    @patch("quantchain.core.secret_managers.vault.hvac.Client")


def test_init_success(self, mock_client: Mock) -> None:
        """Test successful initialization."""
        mock_client_instance = Mock()
        mock_client_instance.is_authenticated.return_value = True
        mock_client.return_value = mock_client_instance

        with patch.dict(
            os.environ, {"VAULT_ADDR": "http://vault:8200", "VAULT_TOKEN": "test-token"}
        ):
            manager = VaultSecretManager()
            assert manager.url == "http://vault:8200"
            assert manager.token == "test-token"

    @patch("quantchain.core.secret_managers.vault.hvac.Client")


def test_get_secret_success(self, mock_client: Mock) -> None:
        """Test successful secret retrieval."""
        mock_client_instance = Mock()
        mock_client_instance.is_authenticated.return_value = True
        mock_client_instance.secrets.kv.v2.read_secret_version.return_value = {
            "data": {"data": {"key": "value"}}
        }
        mock_client.return_value = mock_client_instance

        with patch.dict(
            os.environ, {"VAULT_ADDR": "http://vault:8200", "VAULT_TOKEN": "test-token"}
        ):
            manager = VaultSecretManager()
            result = manager.get_secret("test-secret")
            assert result == {"key": "value"}

    @patch("quantchain.core.secret_managers.vault.hvac.Client")


def test_get_secret_not_found(self, mock_client: Mock) -> None:
        """Test secret not found."""

        mock_client_instance = Mock()
        mock_client_instance.is_authenticated.return_value = True
        mock_client_instance.secrets.kv.v2.read_secret_version.side_effect = (
            hvac.exceptions.InvalidPath()
        )
        mock_client.return_value = mock_client_instance

        with patch.dict(
            os.environ, {"VAULT_ADDR": "http://vault:8200", "VAULT_TOKEN": "test-token"}
        ):
            manager = VaultSecretManager()
            result = manager.get_secret("test-secret")
            assert result is None

    @patch("quantchain.core.secret_managers.vault.hvac.Client")


def test_set_secret_success(self, mock_client: Mock) -> None:
        """Test successful secret creation/update."""
        mock_client_instance = Mock()
        mock_client_instance.is_authenticated.return_value = True
        mock_client_instance.secrets.kv.v2.create_or_update_secret.return_value = {
            "success": True
        }
        mock_client.return_value = mock_client_instance

        with patch.dict(
            os.environ, {"VAULT_ADDR": "http://vault:8200", "VAULT_TOKEN": "test-token"}
        ):
            manager = VaultSecretManager()
            success = manager.set_secret("test-secret", {"key": "value"})
            assert success is True
