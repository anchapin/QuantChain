"""Final tests for AWS secret manager."""

import pytest
from unittest.mock import Mock, patch, MagicMock

from quantchain.core.secret_managers.aws import AWSSecretsManager


class TestAWSSecretsManager:
    """Test AWSSecretsManager class with proper method names."""
    
    @patch('quantchain.core.secret_managers.aws.boto3.Session')
    def test_init_default(self, mock_session_class):
        """Test initialization with default config."""
        mock_session = Mock()
        mock_client = Mock()
        mock_session_class.return_value = mock_session
        mock_session.client.return_value = mock_client
        mock_client.list_secrets.return_value = {'SecretList': []}
        
        manager = AWSSecretsManager()
        
        assert manager.region_name == "us-east-1"
        assert manager.client == mock_client
        mock_session_class.assert_called_once()
        mock_session.client.assert_called_once_with(
            'secretsmanager',
            region_name='us-east-1'
        )
    
    @patch('quantchain.core.secret_managers.aws.boto3.Session')
    def test_get_secret_success(self, mock_session_class):
        """Test successful secret retrieval."""
        mock_session = Mock()
        mock_client = Mock()
        mock_session_class.return_value = mock_session
        mock_session.client.return_value = mock_client
        mock_client.list_secrets.return_value = {'SecretList': []}
        
        # Mock successful response
        mock_response = {
            'SecretString': 'my-secret-value',
            'VersionId': 'v1',
            'CreatedDate': 1234567890
        }
        mock_client.get_secret_value.return_value = mock_response
        
        manager = AWSSecretsManager()
        secret = manager.get_secret("test-secret")
        
        assert secret == 'my-secret-value'
        mock_client.get_secret_value.assert_called_once_with(
            SecretId='test-secret'
        )
    
    @patch('quantchain.core.secret_managers.aws.boto3.Session')
    def test_get_secret_json(self, mock_session_class):
        """Test getting JSON secret value."""
        mock_session = Mock()
        mock_client = Mock()
        mock_session_class.return_value = mock_session
        mock_session.client.return_value = mock_client
        mock_client.list_secrets.return_value = {'SecretList': []}
        
        # Mock JSON secret response
        mock_response = {
            'SecretString': '{"api_key": "test-key", "api_secret": "test-secret"}',
            'VersionId': 'v1'
        }
        mock_client.get_secret_value.return_value = mock_response
        
        manager = AWSSecretsManager()
        secret = manager.get_secret("test-secret")
        
        # Should return JSON string when it's a complex object
        assert secret == '{"api_key": "test-key", "api_secret": "test-secret"}'
        mock_client.get_secret_value.assert_called_once_with(
            SecretId='test-secret'
        )
    
    @patch('quantchain.core.secret_managers.aws.boto3.Session')
    def test_get_secret_not_found(self, mock_session_class):
        """Test secret not found error."""
        mock_session = Mock()
        mock_client = Mock()
        mock_session_class.return_value = mock_session
        mock_session.client.return_value = mock_client
        mock_client.list_secrets.return_value = {'SecretList': []}
        
        # Mock ResourceNotFoundException
        from botocore.exceptions import ClientError
        error = ClientError(
            error_response={'Error': {'Code': 'ResourceNotFoundException'}},
            operation_name='GetSecretValue'
        )
        mock_client.get_secret_value.side_effect = error
        
        manager = AWSSecretsManager()
        
        # Should return None when secret not found
        secret = manager.get_secret("non-existent-secret")
        assert secret is None
    
    @patch('quantchain.core.secret_managers.aws.boto3.Session')
    def test_validate_service_exists(self, mock_session_class):
        """Test service validation when service exists."""
        mock_session = Mock()
        mock_client = Mock()
        mock_session_class.return_value = mock_session
        mock_session.client.return_value = mock_client
        mock_client.list_secrets.return_value = {'SecretList': []}
        
        # Mock successful response
        mock_response = {'SecretString': 'test-value'}
        mock_client.get_secret_value.return_value = mock_response
        
        manager = AWSSecretsManager()
        result = manager.validate_service("test-service")
        
        assert result is True
        mock_client.get_secret_value.assert_called_once_with(
            SecretId='quantchain/test-service'
        )
    
    @patch('quantchain.core.secret_managers.aws.boto3.Session')
    def test_validate_service_not_exists(self, mock_session_class):
        """Test service validation when service doesn't exist."""
        mock_session = Mock()
        mock_client = Mock()
        mock_session_class.return_value = mock_session
        mock_session.client.return_value = mock_client
        mock_client.list_secrets.return_value = {'SecretList': []}
        
        # Mock ResourceNotFoundException
        from botocore.exceptions import ClientError
        error = ClientError(
            error_response={'Error': {'Code': 'ResourceNotFoundException'}},
            operation_name='GetSecretValue'
        )
        mock_client.get_secret_value.side_effect = error
        
        manager = AWSSecretsManager()
        result = manager.validate_service("non-existent-service")
        
        assert result is False
    
    @patch('quantchain.core.secret_managers.aws.boto3.Session')
    def test_get_service_credentials_success(self, mock_session_class):
        """Test getting service credentials successfully."""
        mock_session = Mock()
        mock_client = Mock()
        mock_session_class.return_value = mock_session
        mock_session.client.return_value = mock_client
        mock_client.list_secrets.return_value = {'SecretList': []}
        
        # Mock successful response with JSON
        mock_response = {
            'SecretString': '{"api_key": "test-key", "api_secret": "test-secret"}'
        }
        mock_client.get_secret_value.return_value = mock_response
        
        manager = AWSSecretsManager()
        creds = manager.get_service_credentials("test-service")
        
        assert creds == {"api_key": "test-key", "api_secret": "test-secret"}
        mock_client.get_secret_value.assert_called_once_with(
            SecretId='quantchain/test-service'
        )
    
    @patch('quantchain.core.secret_managers.aws.boto3.Session')
    def test_get_service_credentials_simple_value(self, mock_session_class):
        """Test getting service credentials with simple string value."""
        mock_session = Mock()
        mock_client = Mock()
        mock_session_class.return_value = mock_session
        mock_session.client.return_value = mock_client
        mock_client.list_secrets.return_value = {'SecretList': []}
        
        # Mock successful response with simple string
        mock_response = {
            'SecretString': 'simple-api-key-12345'
        }
        mock_client.get_secret_value.return_value = mock_response
        
        manager = AWSSecretsManager()
        creds = manager.get_service_credentials("test-service")
        
        assert creds == {"value": "simple-api-key-12345"}
        mock_client.get_secret_value.assert_called_once_with(
            SecretId='quantchain/test-service'
        )
    
    @patch('quantchain.core.secret_managers.aws.boto3.Session')
    def test_get_service_credentials_not_found(self, mock_session_class):
        """Test getting service credentials when service doesn't exist."""
        mock_session = Mock()
        mock_client = Mock()
        mock_session_class.return_value = mock_session
        mock_session.client.return_value = mock_client
        mock_client.list_secrets.return_value = {'SecretList': []}
        
        # Mock ResourceNotFoundException
        from botocore.exceptions import ClientError
        error = ClientError(
            error_response={'Error': {'Code': 'ResourceNotFoundException'}},
            operation_name='GetSecretValue'
        )
        mock_client.get_secret_value.side_effect = error
        
        manager = AWSSecretsManager()
        creds = manager.get_service_credentials("non-existent-service")
        
        assert creds == {}
