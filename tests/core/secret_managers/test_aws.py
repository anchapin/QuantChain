"""Tests for AWS Secrets Manager implementation."""

import pytest
from unittest.mock import MagicMock, patch
import json

from quantchain.core.secret_managers.aws import (
    AWSSecretManager,
    AWSSecretManagerConfig,
    AWSSecretsManager,
    create_aws_secret_manager,
)


class TestAWSSecretManagerConfig:
    """Test cases for AWSSecretManagerConfig."""

    def test_config_initialization(self):
        """Test default config initialization."""
        config = AWSSecretManagerConfig()

        assert config.region_name == "us-east-1"
        assert config.max_retries == 3
        assert config.backoff_factor == 1.0

    def test_config_custom_values(self):
        """Test config with custom values."""
        config = AWSSecretManagerConfig(
            region_name="us-west-2",
            max_retries=5,
            backoff_factor=2.0,
        )

        assert config.region_name == "us-west-2"
        assert config.max_retries == 5
        assert config.backoff_factor == 2.0


class TestAWSSecretsManager:
    """Test cases for AWSSecretsManager."""

    def setup_method(self):
        """Set up test fixtures."""
        self.region_name = "us-west-2"

    @patch("quantchain.core.secret_managers.aws.boto3")
    def test_initialization(self, mock_boto3):
        """Test manager initialization."""
        mock_session = MagicMock()
        mock_client = MagicMock()
        mock_boto3.Session.return_value = mock_session
        mock_session.client.return_value = mock_client

        # Mock successful connection
        mock_client.list_secrets.return_value = {"SecretList": []}

        manager = AWSSecretsManager(region_name=self.region_name)

        assert manager.region_name == self.region_name
        assert manager.client == mock_client
        mock_session.client.assert_called_once_with(
            "secretsmanager", region_name="us-west-2"
        )

    @patch("quantchain.core.secret_managers.aws.boto3")
    def test_initialization_with_env_vars(self, mock_boto3):
        """Test manager initialization using environment variables."""
        mock_session = MagicMock()
        mock_client = MagicMock()
        mock_boto3.Session.return_value = mock_session
        mock_session.client.return_value = mock_client

        # Mock successful connection
        mock_client.list_secrets.return_value = {"SecretList": []}

        manager = AWSSecretsManager()

        assert manager.region_name == "us-east-1"  # Default
        assert manager.client == mock_client

    @patch("quantchain.core.secret_managers.aws.boto3")
    def test_get_secret_success_json(self, mock_boto3):
        """Test successful JSON secret retrieval."""
        mock_session = MagicMock()
        mock_client = MagicMock()
        mock_boto3.Session.return_value = mock_session
        mock_session.client.return_value = mock_client

        # Mock successful connection
        mock_client.list_secrets.return_value = {"SecretList": []}

        secret_data = {"username": "testuser", "password": "testpass"}
        mock_response = {"SecretString": json.dumps(secret_data)}
        mock_client.get_secret_value.return_value = mock_response

        manager = AWSSecretsManager(region_name=self.region_name)
        result = manager.get_secret("test-secret")

        assert result == json.dumps(secret_data)
        mock_client.get_secret_value.assert_called_once_with(SecretId="test-secret")

    @patch("quantchain.core.secret_managers.aws.boto3")
    def test_get_secret_success_single_value_json(self, mock_boto3):
        """Test successful single value JSON secret retrieval."""
        mock_session = MagicMock()
        mock_client = MagicMock()
        mock_boto3.Session.return_value = mock_session
        mock_session.client.return_value = mock_client

        # Mock successful connection
        mock_client.list_secrets.return_value = {"SecretList": []}

        secret_data = {"api_key": "test-key-12345"}
        mock_response = {"SecretString": json.dumps(secret_data)}
        mock_client.get_secret_value.return_value = mock_response

        manager = AWSSecretsManager(region_name=self.region_name)
        result = manager.get_secret("test-secret")

        assert result == "test-key-12345"
        mock_client.get_secret_value.assert_called_once_with(SecretId="test-secret")

    @patch("quantchain.core.secret_managers.aws.boto3")
    def test_get_secret_success_binary(self, mock_boto3):
        """Test successful binary secret retrieval."""
        mock_session = MagicMock()
        mock_client = MagicMock()
        mock_boto3.Session.return_value = mock_session
        mock_session.client.return_value = mock_client

        # Mock successful connection
        mock_client.list_secrets.return_value = {"SecretList": []}

        binary_data = b"binary_secret_data"
        mock_response = {"SecretBinary": binary_data}
        mock_client.get_secret_value.return_value = mock_response

        manager = AWSSecretsManager(region_name=self.region_name)
        result = manager.get_secret("test-secret-binary")

        assert result == "binary_secret_data"
        mock_client.get_secret_value.assert_called_once_with(
            SecretId="test-secret-binary"
        )

    @patch("quantchain.core.secret_managers.aws.boto3")
    def test_get_secret_success_string(self, mock_boto3):
        """Test successful string secret retrieval (non-JSON)."""
        mock_session = MagicMock()
        mock_client = MagicMock()
        mock_boto3.Session.return_value = mock_session
        mock_session.client.return_value = mock_client

        # Mock successful connection
        mock_client.list_secrets.return_value = {"SecretList": []}

        secret_string = "simple-secret-value"
        mock_response = {"SecretString": secret_string}
        mock_client.get_secret_value.return_value = mock_response

        manager = AWSSecretsManager(region_name=self.region_name)
        result = manager.get_secret("test-secret")

        assert result == secret_string
        mock_client.get_secret_value.assert_called_once_with(SecretId="test-secret")

    @patch("quantchain.core.secret_managers.aws.boto3")
    def test_get_secret_not_found(self, mock_boto3):
        """Test secret not found error."""
        mock_session = MagicMock()
        mock_client = MagicMock()
        mock_boto3.Session.return_value = mock_session
        mock_session.client.return_value = mock_client

        # Mock successful connection
        mock_client.list_secrets.return_value = {"SecretList": []}

        from botocore.exceptions import ClientError

        error_response = {
            "Error": {
                "Code": "ResourceNotFoundException",
                "Message": "Secret not found",
            }
        }
        mock_client.get_secret_value.side_effect = ClientError(
            error_response, "GetSecretValue"
        )

        manager = AWSSecretsManager(region_name=self.region_name)
        result = manager.get_secret("test-secret")

        assert result is None

    @patch("quantchain.core.secret_managers.aws.boto3")
    def test_get_secret_access_denied(self, mock_boto3):
        """Test access denied error."""
        mock_session = MagicMock()
        mock_client = MagicMock()
        mock_boto3.Session.return_value = mock_session
        mock_session.client.return_value = mock_client

        # Mock successful connection
        mock_client.list_secrets.return_value = {"SecretList": []}

        from botocore.exceptions import ClientError

        error_response = {
            "Error": {"Code": "AccessDeniedException", "Message": "Access denied"}
        }
        mock_client.get_secret_value.side_effect = ClientError(
            error_response, "GetSecretValue"
        )

        manager = AWSSecretsManager(region_name=self.region_name)
        result = manager.get_secret("test-secret")

        assert result is None

    @patch("quantchain.core.secret_managers.aws.boto3")
    def test_get_secret_client_error(self, mock_boto3):
        """Test generic client error."""
        mock_session = MagicMock()
        mock_client = MagicMock()
        mock_boto3.Session.return_value = mock_session
        mock_session.client.return_value = mock_client

        # Mock successful connection
        mock_client.list_secrets.return_value = {"SecretList": []}

        from botocore.exceptions import ClientError

        error_response = {
            "Error": {"Code": "InternalServiceException", "Message": "Internal error"}
        }
        mock_client.get_secret_value.side_effect = ClientError(
            error_response, "GetSecretValue"
        )

        manager = AWSSecretsManager(region_name=self.region_name)
        result = manager.get_secret("test-secret")

        assert result is None

    @patch("quantchain.core.secret_managers.aws.boto3")
    def test_get_secret_unexpected_error(self, mock_boto3):
        """Test unexpected error during secret retrieval."""
        mock_session = MagicMock()
        mock_client = MagicMock()
        mock_boto3.Session.return_value = mock_session
        mock_session.client.return_value = mock_client

        # Mock successful connection
        mock_client.list_secrets.return_value = {"SecretList": []}

        # Note: The actual implementation catches all exceptions and returns None
        mock_client.get_secret_value.side_effect = Exception("Unexpected error")

        manager = AWSSecretsManager(region_name=self.region_name)
        result = manager.get_secret("test-secret")

        # Implementation catches all exceptions and returns None
        assert result is None

    @patch("quantchain.core.secret_managers.aws.boto3")
    def test_get_service_credentials_success(self, mock_boto3):
        """Test successful service credentials retrieval."""
        mock_session = MagicMock()
        mock_client = MagicMock()
        mock_boto3.Session.return_value = mock_session
        mock_session.client.return_value = mock_client

        # Mock successful connection
        mock_client.list_secrets.return_value = {"SecretList": []}

        service_credentials = {
            "api_key": "test-key-123",
            "api_secret": "test-secret-456",
            "base_url": "https://api.example.com",
        }
        mock_response = {"SecretString": json.dumps(service_credentials)}
        mock_client.get_secret_value.return_value = mock_response

        manager = AWSSecretsManager(region_name=self.region_name)
        result = manager.get_service_credentials("test-service")

        assert result == service_credentials
        mock_client.get_secret_value.assert_called_once_with(
            SecretId="quantchain/test-service"
        )

    @patch("quantchain.core.secret_managers.aws.boto3")
    def test_get_service_credentials_not_found(self, mock_boto3):
        """Test service credentials not found."""
        mock_session = MagicMock()
        mock_client = MagicMock()
        mock_boto3.Session.return_value = mock_session
        mock_session.client.return_value = mock_client

        # Mock successful connection
        mock_client.list_secrets.return_value = {"SecretList": []}

        from botocore.exceptions import ClientError

        error_response = {
            "Error": {
                "Code": "ResourceNotFoundException",
                "Message": "Secret not found",
            }
        }
        mock_client.get_secret_value.side_effect = ClientError(
            error_response, "GetSecretValue"
        )

        manager = AWSSecretsManager(region_name=self.region_name)
        result = manager.get_service_credentials("test-service")

        assert result == {}

    @patch("quantchain.core.secret_managers.aws.boto3")
    def test_get_service_credentials_invalid_json(self, mock_boto3):
        """Test service credentials with invalid JSON."""
        mock_session = MagicMock()
        mock_client = MagicMock()
        mock_boto3.Session.return_value = mock_session
        mock_session.client.return_value = mock_client

        # Mock successful connection
        mock_client.list_secrets.return_value = {"SecretList": []}

        mock_response = {"SecretString": "invalid-json-string"}
        mock_client.get_secret_value.return_value = mock_response

        manager = AWSSecretsManager(region_name=self.region_name)
        result = manager.get_service_credentials("test-service")

        assert result == {"value": "invalid-json-string"}

    @patch("quantchain.core.secret_managers.aws.boto3")
    def test_validate_service_success(self, mock_boto3):
        """Test successful service validation."""
        mock_session = MagicMock()
        mock_client = MagicMock()
        mock_boto3.Session.return_value = mock_session
        mock_session.client.return_value = mock_client

        # Mock successful connection
        mock_client.list_secrets.return_value = {"SecretList": []}

        mock_response = {"SecretString": json.dumps({"api_key": "test-key"})}
        mock_client.get_secret_value.return_value = mock_response

        manager = AWSSecretsManager(region_name=self.region_name)
        result = manager.validate_service("test-service")

        assert result is True
        mock_client.get_secret_value.assert_called_once_with(
            SecretId="quantchain/test-service"
        )

    @patch("quantchain.core.secret_managers.aws.boto3")
    def test_validate_service_not_found(self, mock_boto3):
        """Test service validation when secret not found."""
        mock_session = MagicMock()
        mock_client = MagicMock()
        mock_boto3.Session.return_value = mock_session
        mock_session.client.return_value = mock_client

        # Mock successful connection
        mock_client.list_secrets.return_value = {"SecretList": []}

        from botocore.exceptions import ClientError

        error_response = {
            "Error": {
                "Code": "ResourceNotFoundException",
                "Message": "Secret not found",
            }
        }
        mock_client.get_secret_value.side_effect = ClientError(
            error_response, "GetSecretValue"
        )

        manager = AWSSecretsManager(region_name=self.region_name)
        result = manager.validate_service("test-service")

        assert result is False

    @patch("quantchain.core.secret_managers.aws.boto3")
    def test_validate_service_access_denied(self, mock_boto3):
        """Test service validation when access denied."""
        mock_session = MagicMock()
        mock_client = MagicMock()
        mock_boto3.Session.return_value = mock_session
        mock_session.client.return_value = mock_client

        # Mock successful connection
        mock_client.list_secrets.return_value = {"SecretList": []}

        from botocore.exceptions import ClientError

        error_response = {
            "Error": {"Code": "AccessDeniedException", "Message": "Access denied"}
        }
        mock_client.get_secret_value.side_effect = ClientError(
            error_response, "GetSecretValue"
        )

        manager = AWSSecretsManager(region_name=self.region_name)
        result = manager.validate_service("test-service")

        assert result is False

    @patch("quantchain.core.secret_managers.aws.boto3")
    def test_get_api_key_convenience(self, mock_boto3):
        """Test get_api_key convenience method."""
        mock_session = MagicMock()
        mock_client = MagicMock()
        mock_boto3.Session.return_value = mock_session
        mock_session.client.return_value = mock_client

        # Mock successful connection
        mock_client.list_secrets.return_value = {"SecretList": []}

        service_credentials = {
            "key": "test-api-key-123",  # Note: base class uses "key" not "api_key"
            "secret": "test-api-secret",
        }
        mock_response = {"SecretString": json.dumps(service_credentials)}
        mock_client.get_secret_value.return_value = mock_response

        manager = AWSSecretsManager(region_name=self.region_name)
        result = manager.get_api_key("test-service")

        assert result == "test-api-key-123"

    @patch("quantchain.core.secret_managers.aws.boto3")
    def test_get_api_secret_convenience(self, mock_boto3):
        """Test get_api_secret convenience method."""
        mock_session = MagicMock()
        mock_client = MagicMock()
        mock_boto3.Session.return_value = mock_session
        mock_session.client.return_value = mock_client

        # Mock successful connection
        mock_client.list_secrets.return_value = {"SecretList": []}

        service_credentials = {
            "key": "test-api-key-123",
            "secret": "test-api-secret-456",  # Note: base class uses "secret" not "api_secret"
        }
        mock_response = {"SecretString": json.dumps(service_credentials)}
        mock_client.get_secret_value.return_value = mock_response

        manager = AWSSecretsManager(region_name=self.region_name)
        result = manager.get_api_secret("test-service")

        assert result == "test-api-secret-456"

    @patch("quantchain.core.secret_managers.aws.boto3")
    def test_has_credentials_convenience(self, mock_boto3):
        """Test has_credentials convenience method."""
        mock_session = MagicMock()
        mock_client = MagicMock()
        mock_boto3.Session.return_value = mock_session
        mock_session.client.return_value = mock_client

        # Mock successful connection
        mock_client.list_secrets.return_value = {"SecretList": []}

        service_credentials = {
            "api_key": "test-api-key-123",
            "api_secret": "test-api-secret",
        }
        mock_response = {"SecretString": json.dumps(service_credentials)}
        mock_client.get_secret_value.return_value = mock_response

        manager = AWSSecretsManager(region_name=self.region_name)
        result = manager.has_credentials("test-service")

        assert result is True


class TestCreateAWSSecretManager:
    """Test cases for create_aws_secret_manager function."""

    @patch("quantchain.core.secret_managers.aws.boto3")
    def test_create_with_default_params(self, mock_boto3):
        """Test creating manager with default parameters."""
        mock_session = MagicMock()
        mock_client = MagicMock()
        mock_boto3.Session.return_value = mock_session
        mock_session.client.return_value = mock_client

        # Mock successful connection
        mock_client.list_secrets.return_value = {"SecretList": []}

        manager = create_aws_secret_manager()

        assert isinstance(manager, AWSSecretsManager)
        assert manager.region_name == "us-east-1"

    @patch("quantchain.core.secret_managers.aws.boto3")
    def test_create_with_custom_params(self, mock_boto3):
        """Test creating manager with custom parameters."""
        mock_session = MagicMock()
        mock_client = MagicMock()
        mock_boto3.Session.return_value = mock_session
        mock_session.client.return_value = mock_client

        # Mock successful connection
        mock_client.list_secrets.return_value = {"SecretList": []}

        manager = create_aws_secret_manager(
            region_name="eu-west-1",
            aws_access_key_id="test-key",
            aws_secret_access_key="test-secret",
        )

        assert isinstance(manager, AWSSecretsManager)
        assert manager.region_name == "eu-west-1"
        assert manager.aws_access_key_id == "test-key"
        assert manager.aws_secret_access_key == "test-secret"
