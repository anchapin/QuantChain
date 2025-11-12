"""Comprehensive tests for AWS Secrets Manager implementation."""

import json
import os
from unittest.mock import Mock, patch

import pytest

# Import the module under test
try:
    from quantchain.core.secret_managers.aws import (
        AWSSecretManagerConfig,
        AWSSecretManagerError,
        AWSSecretsManager,
        create_aws_secret_manager,
    )

    try:
        from botocore.exceptions import ClientError
    except ImportError:
        # Mock ClientError for testing when botocore is not available
        class ClientError(Exception):
            def __init__(self, error_response, operation_name):
                self.response = error_response

    _AWS_AVAILABLE = True
except ImportError:
    _AWS_AVAILABLE = False

    # Mock classes for when boto3 is not available
    class ClientError(Exception):
        def __init__(self, error_response, operation_name):
            self.response = error_response


@pytest.mark.skipif(not _AWS_AVAILABLE, reason="boto3 not installed")
@pytest.mark.unit
class TestAWSSecretManagerConfig:
    """Test AWS Secrets Manager configuration."""

    def test_default_config(self) -> None:
        """Test default configuration values."""
        config = AWSSecretManagerConfig()
        assert config.region_name == "us-east-1"
        assert config.max_retries == 3
        assert config.backoff_factor == 1.0

    def test_custom_config(self) -> None:
        """Test custom configuration values."""
        config = AWSSecretManagerConfig(
            region_name="us-west-2", max_retries=5, backoff_factor=2.0
        )
        assert config.region_name == "us-west-2"
        assert config.max_retries == 5
        assert config.backoff_factor == 2.0


@pytest.mark.skipif(not _AWS_AVAILABLE, reason="boto3 not installed")
@pytest.mark.unit
class TestAWSSecretsManager:
    """Test AWS Secrets Manager implementation."""

    @patch("boto3.Session")
    def test_init_with_explicit_credentials(self, mock_session: Mock) -> None:
        """Test initialization with explicit credentials."""
        mock_client = Mock()
        mock_client.list_secrets.return_value = {"SecretList": []}
        mock_session.return_value.client.return_value = mock_client

        manager = AWSSecretsManager(
            region_name="us-west-2",
            aws_access_key_id="test_key",
            aws_secret_access_key="test_secret",
        )

        assert manager.region_name == "us-west-2"
        assert manager.aws_access_key_id == "test_key"
        assert manager.aws_secret_access_key == "test_secret"
        mock_client.list_secrets.assert_called_once_with(MaxResults=1)

    @patch("boto3.Session")
    def test_init_with_env_credentials(self, mock_session: Mock) -> None:
        """Test initialization with environment variables."""
        mock_client = Mock()
        mock_client.list_secrets.return_value = {"SecretList": []}
        mock_session.return_value.client.return_value = mock_client

        with patch.dict(
            os.environ,
            {
                "AWS_REGION": "us-east-1",
                "AWS_ACCESS_KEY_ID": "env_key",
                "AWS_SECRET_ACCESS_KEY": "env_secret",
            },
        ):
            manager = AWSSecretsManager()

            assert manager.region_name == "us-east-1"
            assert manager.aws_access_key_id == "env_key"
            assert manager.aws_secret_access_key == "env_secret"

    @patch("boto3.Session")
    def test_init_with_profile(self, mock_session: Mock) -> None:
        """Test initialization with AWS profile."""
        mock_client = Mock()
        mock_client.list_secrets.return_value = {"SecretList": []}
        mock_session.return_value.client.return_value = mock_client

        manager = AWSSecretsManager(profile_name="test-profile")

        mock_session.assert_called_once_with(profile_name="test-profile")

    @patch("boto3.Session")
    def test_init_connection_failure(self, mock_session: Mock) -> None:
        """Test initialization with connection failure."""
        mock_client = Mock()
        mock_client.list_secrets.side_effect = Exception("Connection failed")
        mock_session.return_value.client.return_value = mock_client

        with pytest.raises(
            RuntimeError, match="Failed to connect to AWS Secrets Manager"
        ):
            AWSSecretsManager()

    @patch("boto3.Session")
    def test_get_secret_success_string(self, mock_session: Mock) -> None:
        """Test successful secret retrieval as string."""
        mock_client = Mock()
        mock_client.list_secrets.return_value = {"SecretList": []}
        mock_client.get_secret_value.return_value = {
            "SecretString": "test_secret_value"
        }
        mock_session.return_value.client.return_value = mock_client

        manager = AWSSecretsManager()
        result = manager.get_secret("test_secret")

        assert result == "test_secret_value"
        mock_client.get_secret_value.assert_called_once_with(SecretId="test_secret")

    @patch("boto3.Session")
    def test_get_secret_success_json_single_value(self, mock_session: Mock) -> None:
        """Test successful secret retrieval as JSON with single value."""
        mock_client = Mock()
        mock_client.list_secrets.return_value = {"SecretList": []}
        mock_client.get_secret_value.return_value = {
            "SecretString": json.dumps({"key": "value"})
        }
        mock_session.return_value.client.return_value = mock_client

        manager = AWSSecretsManager()
        result = manager.get_secret("test_secret")

        assert result == "value"

    @patch("boto3.Session")
    def test_get_secret_success_json_multiple_values(self, mock_session: Mock) -> None:
        """Test successful secret retrieval as JSON with multiple values."""
        mock_client = Mock()
        mock_client.list_secrets.return_value = {"SecretList": []}
        mock_client.get_secret_value.return_value = {
            "SecretString": json.dumps({"key1": "value1", "key2": "value2"})
        }
        mock_session.return_value.client.return_value = mock_client

        manager = AWSSecretsManager()
        result = manager.get_secret("test_secret")

        assert result == '{"key1": "value1", "key2": "value2"}'

    @patch("boto3.Session")
    def test_get_secret_success_binary(self, mock_session: Mock) -> None:
        """Test successful secret retrieval as binary data."""
        mock_client = Mock()
        mock_client.list_secrets.return_value = {"SecretList": []}
        mock_client.get_secret_value.return_value = {"SecretBinary": b"binary_data"}
        mock_session.return_value.client.return_value = mock_client

        manager = AWSSecretsManager()
        result = manager.get_secret("test_secret")

        assert result == "binary_data"

    @patch("boto3.Session")
    def test_get_secret_not_found(self, mock_session: Mock) -> None:
        """Test secret not found case."""
        mock_client = Mock()
        mock_client.list_secrets.return_value = {"SecretList": []}
        mock_client.get_secret_value.side_effect = ClientError(
            {"Error": {"Code": "ResourceNotFoundException"}}, "GetSecretValue"
        )
        mock_session.return_value.client.return_value = mock_client

        manager = AWSSecretsManager()
        result = manager.get_secret("nonexistent_secret")

        assert result is None

    @patch("boto3.Session")
    def test_get_secret_client_error(self, mock_session: Mock) -> None:
        """Test client error during secret retrieval."""
        mock_client = Mock()
        mock_client.list_secrets.return_value = {"SecretList": []}
        mock_client.get_secret_value.side_effect = ClientError(
            {
                "Error": {
                    "Code": "InvalidParameterException",
                    "Message": "Invalid secret",
                }
            },
            "GetSecretValue",
        )
        mock_session.return_value.client.return_value = mock_client

        manager = AWSSecretsManager()
        result = manager.get_secret("test_secret")

        assert result is None

    @patch("boto3.Session")
    def test_get_service_credentials_success(self, mock_session: Mock) -> None:
        """Test successful service credentials retrieval."""
        mock_client = Mock()
        mock_client.list_secrets.return_value = {"SecretList": []}
        mock_client.get_secret_value.return_value = {
            "SecretString": json.dumps({"api_key": "key123", "api_secret": "secret123"})
        }
        mock_session.return_value.client.return_value = mock_client

        manager = AWSSecretsManager()
        result = manager.get_service_credentials("alpaca")

        assert result == {"api_key": "key123", "api_secret": "secret123"}
        mock_client.get_secret_value.assert_called_once_with(
            SecretId="quantchain/alpaca"
        )

    @patch("boto3.Session")
    def test_get_service_credentials_not_json(self, mock_session: Mock) -> None:
        """Test service credentials retrieval with non-JSON string."""
        mock_client = Mock()
        mock_client.list_secrets.return_value = {"SecretList": []}
        mock_client.get_secret_value.return_value = {
            "SecretString": "plain_text_secret"
        }
        mock_session.return_value.client.return_value = mock_client

        manager = AWSSecretsManager()
        result = manager.get_service_credentials("alpaca")

        assert result == {"value": "plain_text_secret"}

    @patch("boto3.Session")
    def test_get_service_credentials_not_found(self, mock_session: Mock) -> None:
        """Test service credentials not found."""
        mock_client = Mock()
        mock_client.list_secrets.return_value = {"SecretList": []}
        mock_client.get_secret_value.side_effect = ClientError(
            {"Error": {"Code": "ResourceNotFoundException"}}, "GetSecretValue"
        )
        mock_session.return_value.client.return_value = mock_client

        manager = AWSSecretsManager()
        result = manager.get_service_credentials("nonexistent_service")

        assert result == {}

    @patch("boto3.Session")
    def test_validate_service_success(self, mock_session: Mock) -> None:
        """Test successful service validation."""
        mock_client = Mock()
        mock_client.list_secrets.return_value = {"SecretList": []}
        mock_client.get_secret_value.return_value = {"SecretString": "some_secret"}
        mock_session.return_value.client.return_value = mock_client

        manager = AWSSecretsManager()
        result = manager.validate_service("alpaca")

        assert result is True
        mock_client.get_secret_value.assert_called_once_with(
            SecretId="quantchain/alpaca"
        )

    @patch("boto3.Session")
    def test_validate_service_not_found(self, mock_session: Mock) -> None:
        """Test service validation when not found."""
        mock_client = Mock()
        mock_client.list_secrets.return_value = {"SecretList": []}
        mock_client.get_secret_value.side_effect = ClientError(
            {"Error": {"Code": "ResourceNotFoundException"}}, "GetSecretValue"
        )
        mock_session.return_value.client.return_value = mock_client

        manager = AWSSecretsManager()
        result = manager.validate_service("nonexistent_service")

        assert result is False

    @patch("boto3.Session")
    def test_validate_service_other_error(self, mock_session: Mock) -> None:
        """Test service validation with other error."""
        mock_client = Mock()
        mock_client.list_secrets.return_value = {"SecretList": []}
        mock_client.get_secret_value.side_effect = ClientError(
            {"Error": {"Code": "AccessDeniedException", "Message": "Access denied"}},
            "GetSecretValue",
        )
        mock_session.return_value.client.return_value = mock_client

        manager = AWSSecretsManager()
        result = manager.validate_service("alpaca")

        assert result is False


@pytest.mark.skipif(not _AWS_AVAILABLE, reason="boto3 not installed")
@pytest.mark.unit
class TestCreateAWSSecretManager:
    """Test factory function for AWS Secrets Manager."""

    @patch("boto3.Session")
    def test_create_aws_secret_manager(self, mock_session: Mock) -> None:
        """Test creating AWS Secret Manager with factory function."""
        mock_client = Mock()
        mock_client.list_secrets.return_value = {"SecretList": []}
        mock_session.return_value.client.return_value = mock_client

        manager = create_aws_secret_manager(region_name="us-east-1")

        assert isinstance(manager, AWSSecretsManager)
        assert manager.region_name == "us-east-1"


@pytest.mark.skipif(not _AWS_AVAILABLE, reason="boto3 not installed")
@pytest.mark.unit
class TestAWSSecretManagerError:
    """Test AWS Secret Manager error class."""

    def test_error_instantiation(self) -> None:
        """Test creating an AWS Secret Manager error."""
        error = AWSSecretManagerError("Test error")
        assert str(error) == "Test error"
