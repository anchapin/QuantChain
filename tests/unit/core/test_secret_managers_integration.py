"""Integration tests for secret manager implementations."""

import json
import os
from unittest.mock import Mock, patch

import pytest

from quantchain.core.secret_managers import (
    EnvSecretManager,
    InvalidCredentialFormatError,
    SecurityConfigurationError,
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
class TestSecretManagerEdgeCases:
    """Test edge cases for secret managers."""

    def test_env_manager_empty_credentials(self) -> None:
        """Test handling of empty credentials."""
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            manager = EnvSecretManager(env_file=os.path.join(tmpdir, "nonexistent.env"))

            # Test with None values
            assert manager.get_secret("nonexistent") is None
            assert manager.get_api_key("nonexistent") is None
            assert manager.get_api_secret("nonexistent") is None
            assert manager.get_service_credentials("nonexistent") == {}
            assert not manager.validate_service("nonexistent")
            assert not manager.has_credentials("nonexistent")

    def test_env_manager_invalid_json_in_env_file(self) -> None:
        """Test handling of malformed .env file."""
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            env_file = tmpdir_path / "invalid.env"
            env_file.write_text('INVALID_FORMAT\nALPACA_API_KEY="test"\n')

            manager = EnvSecretManager(env_file=str(env_file))
            assert manager.get_api_key("alpaca") == "test"

    def test_env_manager_special_characters_in_secrets(self) -> None:
        """Test handling of special characters in secrets."""
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            manager = EnvSecretManager(env_file=os.path.join(tmpdir, "test.env"))

            # Test with polygon (which has simpler format requirements)
            special_key = (
                "POLYGON_KEY_123456789012345_TEST"  # Valid polygon format (20+ chars)
            )

            manager.set_api_key("polygon", special_key)
            assert manager.get_api_key("polygon") == special_key

    def test_env_manager_case_sensitivity(self) -> None:
        """Test case sensitivity handling."""
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            manager = EnvSecretManager(env_file=os.path.join(tmpdir, "test.env"))

            # Test case sensitivity with polygon (simpler format)
            manager.set_api_key("polygon", "POLYGON_KEY_123456789012345_TEST")

            # Should be accessible with both cases
            assert manager.get_api_key("polygon") == "POLYGON_KEY_123456789012345_TEST"
            assert manager.get_api_key("Polygon") == "POLYGON_KEY_123456789012345_TEST"
            assert manager.validate_service("polygon")
            assert manager.validate_service("Polygon")

    def test_env_manager_overwrite_credentials(self) -> None:
        """Test overwriting existing credentials."""
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            manager = EnvSecretManager(env_file=os.path.join(tmpdir, "test.env"))

            # Set initial credentials (using polygon for simpler validation)
            manager.set_api_key("polygon", "POLYGON_KEY_123456789012345")

            # Overwrite with new credentials
            manager.set_api_key("polygon", "POLYGON_NEW_KEY_67890ABCDEFGHIJ")

            assert manager.get_api_key("polygon") == "POLYGON_NEW_KEY_67890ABCDEFGHIJ"

    def test_env_manager_validate_credentials_with_invalid_format(self) -> None:
        """Test credential validation with invalid format."""
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            manager = EnvSecretManager(env_file=os.path.join(tmpdir, "test.env"))

            # Test with invalid Alpaca key format
            with pytest.raises(InvalidCredentialFormatError):
                manager.set_api_key("alpaca", "invalid", "secret")

            # Test with unsupported service
            with pytest.raises(SecurityConfigurationError):
                manager.set_api_key("unsupported_service", "key", "secret")

    def test_env_manager_save_to_env_file(self) -> None:
        """Test saving credentials to .env file."""
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            env_file = tmpdir_path / "test.env"
            manager = EnvSecretManager(env_file=str(env_file))

            manager.set_api_key("polygon", "POLYGON_KEY_123456789012345")
            manager.set_api_key("alpha_vantage", "AV12345678901234")

            manager.save_to_env_file()

            # Read the file and verify contents
            content = env_file.read_text()
            assert 'POLYGON_API_KEY="POLYGON_KEY_123456789012345"' in content
            assert 'ALPHA_VANTAGE_API_KEY="AV12345678901234"' in content


@pytest.mark.skipif(not _VAULT_AVAILABLE, reason="hvac not installed")
@pytest.mark.unit
class TestVaultSecretManagerEdgeCases:
    """Test edge cases for Vault secret manager."""

    def test_vault_manager_empty_response(self) -> None:
        """Test handling of empty responses from Vault."""
        with patch("hvac.Client") as mock_client:
            mock_instance = Mock()
            mock_instance.is_authenticated.return_value = True
            mock_client.return_value = mock_instance

            # Mock empty response
            mock_instance.secrets.kv.v2.read_secret_version.return_value = None

            manager = VaultSecretManager(
                url="https://vault.example.com", token="test_token"
            )

            assert manager.get_secret("test/secret") is None
            assert manager.get_service_credentials("alpaca") == {}
            assert not manager.validate_service("alpaca")

    def test_vault_manager_missing_data_in_response(self) -> None:
        """Test handling of missing data in Vault response."""
        with patch("hvac.Client") as mock_client:
            mock_instance = Mock()
            mock_instance.is_authenticated.return_value = True
            mock_client.return_value = mock_instance

            # Mock response with missing data
            mock_instance.secrets.kv.v2.read_secret_version.return_value = {
                "data": {}  # Missing inner data field
            }

            manager = VaultSecretManager(
                url="https://vault.example.com", token="test_token"
            )

            assert manager.get_secret("test/secret") is None
            assert manager.get_service_credentials("alpaca") == {}

    def test_vault_manager_complex_json_response(self) -> None:
        """Test handling of complex JSON responses."""
        with patch("hvac.Client") as mock_client:
            mock_instance = Mock()
            mock_instance.is_authenticated.return_value = True
            mock_client.return_value = mock_instance

            # Mock complex JSON response
            complex_data = {
                "key": "value",
                "nested": {"subkey": "subvalue"},
                "array": [1, 2, 3],
                "number": 42,
                "boolean": True,
            }

            mock_instance.secrets.kv.v2.read_secret_version.return_value = {
                "data": {"data": complex_data}
            }

            manager = VaultSecretManager(
                url="https://vault.example.com", token="test_token"
            )

            # Should return JSON string for complex data
            result = manager.get_secret("test/complex")
            assert json.loads(result) == complex_data

            # Test service credentials with complex data
            result_creds = manager.get_service_credentials("service")
            assert all(isinstance(k, str) for k in result_creds.keys())
            assert all(isinstance(v, str) for v in result_creds.values())


@pytest.mark.skipif(not _AWS_AVAILABLE, reason="boto3 not installed")
@pytest.mark.unit
class TestAWSSecretsManagerEdgeCases:
    """Test edge cases for AWS Secrets Manager."""

    def test_aws_manager_binary_secret(self) -> None:
        """Test handling of binary secrets."""
        with patch("boto3.Session") as mock_session:
            mock_client = Mock()
            mock_session.return_value.client.return_value = mock_client
            mock_client.list_secrets.return_value = {"SecretList": []}

            # Mock binary secret response
            binary_data = b"binary_secret_data"
            mock_client.get_secret_value.return_value = {"SecretBinary": binary_data}

            manager = AWSSecretsManager(region_name="us-east-1")

            result = manager.get_secret("binary/secret")
            assert result == str(binary_data)

    def test_aws_manager_invalid_json_response(self) -> None:
        """Test handling of invalid JSON in response."""
        with patch("boto3.Session") as mock_session:
            mock_client = Mock()
            mock_session.return_value.client.return_value = mock_client
            mock_client.list_secrets.return_value = {"SecretList": []}

            # Mock invalid JSON response
            mock_client.get_secret_value.return_value = {
                "SecretString": "invalid json {"
            }

            manager = AWSSecretsManager(region_name="us-east-1")

            result = manager.get_secret("invalid/json")
            assert result == "invalid json {"

    def test_aws_manager_complex_service_credentials(self) -> None:
        """Test service credentials with complex data."""
        with patch("boto3.Session") as mock_session:
            mock_client = Mock()
            mock_session.return_value.client.return_value = mock_client
            mock_client.list_secrets.return_value = {"SecretList": []}

            # Mock complex service credentials
            complex_creds = {
                "key": "api_key_value",
                "secret": "api_secret_value",
                "endpoint": "https://api.example.com",
                "timeout": 30,
                "retries": 3,
            }

            mock_client.get_secret_value.return_value = {
                "SecretString": json.dumps(complex_creds)
            }

            manager = AWSSecretsManager(region_name="us-east-1")

            result = manager.get_service_credentials("complex_service")
            assert result["key"] == "api_key_value"
            assert result["secret"] == "api_secret_value"
            assert result["endpoint"] == "https://api.example.com"
            assert result["timeout"] == "30"  # Should be string
            assert result["retries"] == "3"  # Should be string


@pytest.mark.skipif(
    not _GCP_AVAILABLE, reason="google-cloud-secret-manager not installed"
)
@pytest.mark.unit
class TestGCPSecretManagerEdgeCases:
    """Test edge cases for GCP Secret Manager."""

    def test_gcp_manager_binary_payload(self) -> None:
        """Test handling of binary payload."""
        with patch(
            "google.cloud.secretmanager.SecretManagerServiceClient"
        ) as mock_client:
            mock_instance = Mock()
            mock_client.return_value = mock_instance
            mock_instance.list_secrets.return_value = Mock()

            # Mock binary payload
            binary_data = b"binary_secret_data"
            mock_payload = Mock()
            mock_payload.data = binary_data
            mock_instance.access_secret_version.return_value = {"payload": mock_payload}

            manager = GCPSecretManager(project_id="test-project")

            result = manager.get_secret("binary/secret")
            assert result == binary_data.decode("UTF-8")

    def test_gcp_manager_invalid_json_in_payload(self) -> None:
        """Test handling of invalid JSON in payload."""
        with patch(
            "google.cloud.secretmanager.SecretManagerServiceClient"
        ) as mock_client:
            mock_instance = Mock()
            mock_client.return_value = mock_instance
            mock_instance.list_secrets.return_value = Mock()

            # Mock invalid JSON in payload
            mock_payload = Mock()
            mock_payload.data = b"invalid json {"
            mock_instance.access_secret_version.return_value = {"payload": mock_payload}

            manager = GCPSecretManager(project_id="test-project")

            result = manager.get_secret("invalid/json")
            assert result == "invalid json {"

    def test_gcp_manager_complex_service_credentials(self) -> None:
        """Test service credentials with complex data."""
        with patch(
            "google.cloud.secretmanager.SecretManagerServiceClient"
        ) as mock_client:
            mock_instance = Mock()
            mock_client.return_value = mock_instance
            mock_instance.list_secrets.return_value = Mock()

            # Mock complex service credentials
            complex_creds = {
                "api_key": "key_value",
                "api_secret": "secret_value",
                "config": {
                    "timeout": 30,
                    "retries": 3,
                    "features": ["feature1", "feature2"],
                },
            }

            mock_payload = Mock()
            mock_payload.data = json.dumps(complex_creds).encode()
            mock_instance.access_secret_version.return_value = {"payload": mock_payload}

            manager = GCPSecretManager(project_id="test-project")

            result = manager.get_service_credentials("complex_service")
            assert result["api_key"] == "key_value"
            assert result["api_secret"] == "secret_value"
            assert result["config"] == str(complex_creds["config"])


@pytest.mark.unit
class TestSecretManagerErrorHandling:
    """Test error handling across all secret managers."""

    def test_env_manager_unauthorized_access(self) -> None:
        """Test handling of unauthorized access scenarios."""
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            manager = EnvSecretManager(env_file=os.path.join(tmpdir, "test.env"))

            # Test operations on non-existent service
            assert not manager.validate_service("nonexistent")
            assert manager.get_service_credentials("nonexistent") == {}

            # Test get_secret with various formats
            assert manager.get_secret("NONEXISTENT_API_KEY") is None
            assert manager.get_secret("nonexistent_api_key") is None
            assert manager.get_secret("NONEXISTENT_API_SECRET") is None

    @pytest.mark.skipif(not _VAULT_AVAILABLE, reason="hvac not installed")
    def test_vault_manager_connection_failure(self) -> None:
        """Test handling of connection failures."""
        with patch("hvac.Client") as mock_client:
            mock_instance = Mock()
            mock_instance.is_authenticated.return_value = False
            mock_client.return_value = mock_instance

            with pytest.raises(RuntimeError, match="Failed to authenticate with Vault"):
                VaultSecretManager(
                    url="https://vault.example.com", token="invalid_token"
                )

    @pytest.mark.skipif(not _AWS_AVAILABLE, reason="boto3 not installed")
    def test_aws_manager_connection_failure(self) -> None:
        """Test handling of AWS connection failures."""
        with patch("boto3.Session") as mock_session:
            mock_instance = Mock()
            mock_client = Mock()
            mock_client.list_secrets.side_effect = Exception("Connection failed")
            mock_instance.client.return_value = mock_client
            mock_session.return_value = mock_instance

            with pytest.raises(
                RuntimeError, match="Failed to connect to AWS Secrets Manager"
            ):
                AWSSecretsManager(region_name="us-east-1")

    @pytest.mark.skipif(
        not _GCP_AVAILABLE, reason="google-cloud-secret-manager not installed"
    )
    def test_gcp_manager_connection_failure(self) -> None:
        """Test handling of GCP connection failures."""
        with patch(
            "google.cloud.secretmanager.SecretManagerServiceClient"
        ) as mock_client:
            mock_client.side_effect = Exception("Connection failed")

            with pytest.raises(
                RuntimeError, match="Failed to connect to GCP Secret Manager"
            ):
                GCPSecretManager(project_id="test-project")
