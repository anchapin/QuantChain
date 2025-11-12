"""Tests for AWS secret manager."""

import pytest
from unittest.mock import Mock, patch, MagicMock

# Mock boto3 before importing the module
with patch.dict('sys.modules', {'boto3': Mock(), 'botocore.exceptions': Mock()}):
    from quantchain.core.secret_managers.aws import (
        AWSSecretsManager,
        AWSSecretManagerError,
        create_aws_secret_manager,
        AWSSecretManagerConfig,
        AWSSecretManager,
    )


class TestAWSSecretManagerError:
    """Test AWSSecretManagerError exception."""
    
    def test_error_creation(self):
        """Test error can be created with message."""
        error = AWSSecretManagerError("Test AWS error")
        assert str(error) == "Test AWS error"
        assert isinstance(error, Exception)


class TestAWSSecretManagerConfig:
    """Test AWSSecretManagerConfig dataclass."""
    
    def test_creation_default(self):
        """Test config creation with defaults."""
        config = AWSSecretManagerConfig()
        assert config.region_name == "us-east-1"
        assert config.max_retries == 3
        assert config.backoff_factor == 1.0
    
    def test_creation_custom(self):
        """Test config creation with custom values."""
        config = AWSSecretManagerConfig(
            region_name="eu-west-1",
            max_retries=5,
            backoff_factor=2.0
        )
        assert config.region_name == "eu-west-1"
        assert config.max_retries == 5
        assert config.backoff_factor == 2.0


class TestAWSSecretsManager:
    """Test AWSSecretsManager class."""
    
    @patch('quantchain.core.secret_managers.aws.boto3.client')
    def test_init(self, mock_client):
        """Test initialization."""
        mock_boto_client = Mock()
        mock_client.return_value = mock_boto_client
        
        manager = AWSSecretsManager(region_name="us-west-1")
        
        assert manager.region_name == "us-west-1"
        mock_client.assert_called_once_with(
            'secretsmanager',
            region_name='us-west-1'
        )


class TestCreateAWSSecretManager:
    """Test the create_aws_secret_manager convenience function."""
    
    @patch('quantchain.core.secret_managers.aws.AWSSecretsManager')
    def test_create_convenience_function(self, mock_manager_class):
        """Test the convenience function creates manager."""
        mock_manager = Mock()
        mock_manager_class.return_value = mock_manager
        
        manager = create_aws_secret_manager(region_name="eu-central-1")
        
        mock_manager_class.assert_called_once_with(region_name="eu-central-1")
        assert manager == mock_manager


class TestAWSSecretManager:
    """Test AWSSecretManager class."""
    
    @patch('quantchain.core.secret_managers.aws.boto3.client')
    def test_init_default(self, mock_client):
        """Test initialization with default config."""
        mock_boto_client = Mock()
        mock_client.return_value = mock_boto_client
        
        manager = AWSSecretManager()
        
        assert manager.region_name == "us-east-1"
        assert manager.client == mock_boto_client
        mock_client.assert_called_once_with(
            'secretsmanager',
            region_name='us-east-1'
        )
    
    @patch('quantchain.core.secret_managers.aws.boto3.client')
    def test_init_custom_config(self, mock_client):
        """Test initialization with custom config."""
        mock_boto_client = Mock()
        mock_client.return_value = mock_boto_client
        
        manager = AWSSecretManager(region_name="ap-southeast-1")
        
        assert manager.region_name == "ap-southeast-1"
        assert manager.client == mock_boto_client
        mock_client.assert_called_once_with(
            'secretsmanager',
            region_name='ap-southeast-1'
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
        
        manager = AWSSecretManager()
        secret = manager.get_secret("test-secret")
        
        assert secret == 'my-secret-value'
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
        
        manager = AWSSecretManager()
        
        with pytest.raises(AWSSecretManagerError) as exc_info:
            manager.get_secret("non-existent-secret")
        
        assert "not found" in str(exc_info.value).lower()
    
    @patch('quantchain.core.secret_managers.aws.boto3.client')
    def test_get_secret_access_denied(self, mock_client):
        """Test access denied error."""
        mock_boto_client = Mock()
        mock_client.return_value = mock_boto_client
        
        # Mock AccessDeniedException
        error = ClientError(
            error_response={'Error': {'Code': 'AccessDeniedException'}},
            operation_name='GetSecretValue'
        )
        mock_boto_client.get_secret_value.side_effect = error
        
        manager = AWSSecretManager()
        
        with pytest.raises(AWSSecretManagerError) as exc_info:
            manager.get_secret("restricted-secret")
        
        assert "access denied" in str(exc_info.value).lower()
    
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
        
        manager = AWSSecretManager()
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
        
        manager = AWSSecretManager()
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
        
        manager = AWSSecretManager()
        result = manager.delete_secret("test-secret")
        
        assert result['Name'] == 'test-secret'
        mock_boto_client.delete_secret.assert_called_once_with(
            SecretId='test-secret'
        )
    
    @patch('quantchain.core.secret_managers.aws.boto3.client')
    def test_list_secrets_success(self, mock_client):
        """Test successful secret listing."""
        mock_boto_client = Mock()
        mock_client.return_value = mock_boto_client
        
        # Mock paginated response
        first_page = {
            'SecretList': [
                {'ARN': 'arn:aws:secretsmanager:us-east-1:123456:secret:secret1', 'Name': 'secret1'},
                {'ARN': 'arn:aws:secretsmanager:us-east-1:123456:secret:secret2', 'Name': 'secret2'}
            ],
            'NextToken': 'token123'
        }
        second_page = {
            'SecretList': [
                {'ARN': 'arn:aws:secretsmanager:us-east-1:123456:secret:secret3', 'Name': 'secret3'}
            ]
        }
        
        mock_paginator = Mock()
        mock_paginator.paginate.return_value = [first_page, second_page]
        mock_boto_client.get_paginator.return_value = mock_paginator
        
        manager = AWSSecretManager()
        secrets = manager.list_secrets()
        
        assert len(secrets) == 3
        assert secrets[0]['Name'] == 'secret1'
        assert secrets[1]['Name'] == 'secret2'
        assert secrets[2]['Name'] == 'secret3'
        mock_boto_client.get_paginator.assert_called_once_with('list_secrets')
    
    @patch('quantchain.core.secret_managers.aws.boto3.client')
    def test_rotate_secret_success(self, mock_client):
        """Test successful secret rotation."""
        mock_boto_client = Mock()
        mock_client.return_value = mock_boto_client
        
        # Mock successful response
        mock_response = {
            'SecretId': 'test-secret',
            'VersionId': 'v2'
        }
        mock_boto_client.rotate_secret.return_value = mock_response
        
        manager = AWSSecretManager()
        result = manager.rotate_secret("test-secret")
        
        assert result['VersionId'] == 'v2'
        mock_boto_client.rotate_secret.assert_called_once_with(
            SecretId='test-secret'
        )
