"""Tests for AWS secret manager."""

import pytest
from unittest.mock import Mock, patch, MagicMock
import boto3
from botocore.exceptions import ClientError

from quantchain.core.secret_managers.aws import (
    AWSSecretsManager,
    create_aws_secret_manager
)


class TestCreateAWSSecretManager:
    """Test create_aws_secret_manager convenience function."""
    
    @patch('quantchain.core.secret_managers.aws.AWSSecretsManager')
    def test_create_convenience_function(self, mock_manager_class):
        """Test convenience function creates manager."""
        mock_manager = Mock()
        mock_manager_class.return_value = mock_manager
        
        manager = create_aws_secret_manager(region_name="eu-central-1")
        
        mock_manager_class.assert_called_once_with(region_name="eu-central-1")
        assert manager == mock_manager


class TestAWSSecretsManager:
    """Test AWSSecretsManager class."""
    
    @patch('quantchain.core.secret_managers.aws.boto3.client')
    def test_init_default(self, mock_client):
        """Test initialization with default config."""
        mock_boto_client = Mock()
        mock_client.return_value = mock_boto_client
        
        manager = AWSSecretsManager()
        
        assert manager.region_name == "us-east-1"
        assert manager.client == mock_boto_client
        mock_client.assert_called_once_with(
            'secretsmanager',
            region_name='us-east-1'
        )
    
    @patch('quantchain.core.secret_managers.aws.boto3.client')
    def test_init_custom_region(self, mock_client):
        """Test initialization with custom region."""
        mock_boto_client = Mock()
        mock_client.return_value = mock_boto_client
        
        manager = AWSSecretsManager(region_name="eu-west-1")
        
        assert manager.region_name == "eu-west-1"
        assert manager.client == mock_boto_client
        mock_client.assert_called_once_with(
            'secretsmanager',
            region_name='eu-west-1'
        )
    
    @patch('quantchain.core.secret_managers.aws.boto3.client')
    def test_get_secret_success(self, mock_client):
        """Test successful secret retrieval."""
        mock_boto_client = Mock()
        mock_client.return_value = mock_boto_client
        
        # Mock successful response
        mock_response = {
            'SecretString': 'my-secret-value',
            'VersionId': 'v1',
            'CreatedDate': 1234567890
        }
        mock_boto_client.get_secret_value.return_value = mock_response
        
        manager = AWSSecretsManager()
        secret = manager.get_secret("test-secret")
        
        assert secret == 'my-secret-value'
        mock_boto_client.get_secret_value.assert_called_once_with(
            SecretId='test-secret'
        )
    
    @patch('quantchain.core.secret_managers.aws.boto3.client')
    def test_get_secret_json(self, mock_client):
        """Test getting JSON secret value."""
        mock_boto_client = Mock()
        mock_client.return_value = mock_boto_client
        
        # Mock JSON secret response
        mock_response = {
            'SecretString': '{"api_key": "test-key", "api_secret": "test-secret"}',
            'VersionId': 'v1'
        }
        mock_boto_client.get_secret_value.return_value = mock_response
        
        manager = AWSSecretsManager()
        secret = manager.get_secret("test-secret")
        
        # Should return JSON string when it's a complex object
        assert secret == '{"api_key": "test-key", "api_secret": "test-secret"}'
        mock_boto_client.get_secret_value.assert_called_once_with(
            SecretId='test-secret'
        )
    
    @patch('quantchain.core.secret_managers.aws.boto3.client')
    def test_get_secret_not_found(self, mock_client):
        """Test secret not found error."""
        mock_boto_client = Mock()
        mock_client.return_value = mock_boto_client
        
        # Mock ResourceNotFoundException
        error = ClientError(
            error_response={'Error': {'Code': 'ResourceNotFoundException'}},
            operation_name='GetSecretValue'
        )
        mock_boto_client.get_secret_value.side_effect = error
        
        manager = AWSSecretsManager()
        
        with pytest.raises(Exception) as exc_info:
            manager.get_secret("non-existent-secret")
        
        assert "not found" in str(exc_info.value).lower()
    
    @patch('quantchain.core.secret_managers.aws.boto3.client')
    def test_set_secret_success(self, mock_client):
        """Test successful secret creation/update."""
        mock_boto_client = Mock()
        mock_client.return_value = mock_boto_client
        
        # Mock successful response
        mock_response = {
            'ARN': 'arn:aws:secretsmanager:us-east-1:123456789012:secret:test-secret',
            'Name': 'test-secret',
            'VersionId': 'v2'
        }
        mock_boto_client.create_secret.return_value = mock_response
        
        manager = AWSSecretsManager()
        result = manager.set_secret("test-secret", "new-secret-value")
        
        assert result['VersionId'] == 'v2'
        mock_boto_client.create_secret.assert_called_once_with(
            Name='test-secret',
            SecretString='new-secret-value'
        )
    
    @patch('quantchain.core.secret_managers.aws.boto3.client')
    def test_set_secret_binary(self, mock_client):
        """Test setting binary secret."""
        mock_boto_client = Mock()
        mock_client.return_value = mock_boto_client
        
        # Mock successful response
        mock_response = {
            'ARN': 'arn:aws:secretsmanager:us-east-1:123456789012:secret:binary-secret',
            'Name': 'binary-secret',
            'VersionId': 'v1'
        }
        mock_boto_client.create_secret.return_value = mock_response
        
        manager = AWSSecretsManager()
        binary_data = b'\x00\x01\x02\x03'
        result = manager.set_secret("binary-secret", binary_data)
        
        assert result['VersionId'] == 'v1'
        mock_boto_client.create_secret.assert_called_once_with(
            Name='binary-secret',
            SecretBinary=binary_data
        )
    
    @patch('quantchain.core.secret_managers.aws.boto3.client')
    def test_delete_secret_success(self, mock_client):
        """Test successful secret deletion."""
        mock_boto_client = Mock()
        mock_client.return_value = mock_boto_client
        
        # Mock successful response
        mock_response = {
            'ARN': 'arn:aws:secretsmanager:us-east-1:123456789012:secret:test-secret',
            'Name': 'test-secret',
            'DeletionDate': 1234567890
        }
        mock_boto_client.delete_secret.return_value = mock_response
        
        manager = AWSSecretsManager()
        result = manager.delete_secret("test-secret")
        
        assert result['Name'] == 'test-secret'
        mock_boto_client.delete_secret.assert_called_once_with(
            SecretId='test-secret'
        )
    
    @patch('quantchain.core.secret_managers.aws.boto3.client')
    def test_validate_service_exists(self, mock_client):
        """Test service validation when service exists."""
        mock_boto_client = Mock()
        mock_client.return_value = mock_boto_client
        
        # Mock successful response
        mock_response = {'SecretString': 'test-value'}
        mock_boto_client.get_secret_value.return_value = mock_response
        
        manager = AWSSecretsManager()
        result = manager.validate_service("test-service")
        
        assert result is True
        mock_boto_client.get_secret_value.assert_called_once_with(
            SecretId='quantchain/test-service'
        )
    
    @patch('quantchain.core.secret_managers.aws.boto3.client')
    def test_validate_service_not_exists(self, mock_client):
        """Test service validation when service doesn't exist."""
        mock_boto_client = Mock()
        mock_client.return_value = mock_boto_client
        
        # Mock ResourceNotFoundException
        error = ClientError(
            error_response={'Error': {'Code': 'ResourceNotFoundException'}},
            operation_name='GetSecretValue'
        )
        mock_boto_client.get_secret_value.side_effect = error
        
        manager = AWSSecretsManager()
        result = manager.validate_service("non-existent-service")
        
        assert result is False
    
    @patch('quantchain.core.secret_managers.aws.boto3.client')
    def test_get_credentials_success(self, mock_client):
        """Test getting service credentials successfully."""
        mock_boto_client = Mock()
        mock_client.return_value = mock_boto_client
        
        # Mock successful response with JSON
        mock_response = {
            'SecretString': '{"api_key": "test-key", "api_secret": "test-secret"}'
        }
        mock_boto_client.get_secret_value.return_value = mock_response
        
        manager = AWSSecretsManager()
        creds = manager.get_credentials("test-service")
        
        assert creds == {"api_key": "test-key", "api_secret": "test-secret"}
        mock_boto_client.get_secret_value.assert_called_once_with(
            SecretId='quantchain/test-service'
        )
    
    @patch('quantchain.core.secret_managers.aws.boto3.client')
    def test_get_credentials_simple_value(self, mock_client):
        """Test getting service credentials with simple string value."""
        mock_boto_client = Mock()
        mock_client.return_value = mock_boto_client
        
        # Mock successful response with simple string
        mock_response = {
            'SecretString': 'simple-api-key-12345'
        }
        mock_boto_client.get_secret_value.return_value = mock_response
        
        manager = AWSSecretsManager()
        creds = manager.get_credentials("test-service")
        
        assert creds == {"api_key": "simple-api-key-12345"}
        mock_boto_client.get_secret_value.assert_called_once_with(
            SecretId='quantchain/test-service'
        )
    
    @patch('quantchain.core.secret_managers.aws.boto3.client')
    def test_get_credentials_not_found(self, mock_client):
        """Test getting credentials when service doesn't exist."""
        mock_boto_client = Mock()
        mock_client.return_value = mock_boto_client
        
        # Mock ResourceNotFoundException
        error = ClientError(
            error_response={'Error': {'Code': 'ResourceNotFoundException'}},
            operation_name='GetSecretValue'
        )
        mock_boto_client.get_secret_value.side_effect = error
        
        manager = AWSSecretsManager()
        creds = manager.get_credentials("non-existent-service")
        
        assert creds == {}
