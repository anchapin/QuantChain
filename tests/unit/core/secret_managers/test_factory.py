"""Tests for secret manager factory."""

import os
from unittest.mock import MagicMock, patch

import pytest

from quantchain.core.secret_managers.base import SecretManager
from quantchain.core.secret_managers.factory import (
    SECRET_MANAGERS,
    create_secret_manager,
    get_default_secret_manager,
    list_secret_managers,
    register_secret_manager,
)


class MockSecretManager(SecretManager):
    """Mock secret manager for testing."""
    
    def __init__(self, **kwargs):
        self.config = kwargs
    
    def get_secret(self, name):
        return f"mock_secret_{name}"
    
    def set_secret(self, name, value):
        pass
    
    def delete_secret(self, name):
        pass
    
    def list_secrets(self):
        return []


@pytest.mark.unit
class TestCreateSecretManager:
    """Test create_secret_manager function."""

    def test_create_env_backend(self):
        """Test creating env backend secret manager."""
        manager = create_secret_manager(backend="env")
        assert isinstance(manager, SECRET_MANAGERS["env"])

    @patch.dict(os.environ, {"QUANTCHAIN_SECRET_BACKEND": "env"})
    def test_create_default_backend_from_env(self):
        """Test creating secret manager using environment variable."""
        manager = create_secret_manager()
        assert isinstance(manager, SECRET_MANAGERS["env"])

    def test_create_default_backend_env(self):
        """Test creating secret manager with default backend."""
        with patch.dict(os.environ, {}, clear=True):  # Remove env var
            manager = create_secret_manager()
            assert isinstance(manager, SECRET_MANAGERS["env"])

    def test_create_with_config(self):
        """Test creating secret manager with config."""
        config = {"test_param": "test_value"}
        with patch('quantchain.core.secret_managers.factory.EnvSecretManager') as mock_class:
            mock_instance = MagicMock()
            mock_class.return_value = mock_instance
            
            manager = create_secret_manager(backend="env", config=config)
            
            mock_class.assert_called_once_with(test_param="test_value")

    def test_create_with_kwargs(self):
        """Test creating secret manager with kwargs."""
        with patch('quantchain.core.secret_managers.factory.EnvSecretManager') as mock_class:
            mock_instance = MagicMock()
            mock_class.return_value = mock_instance
            
            manager = create_secret_manager(backend="env", test_param="test_value", another_param=123)
            
            mock_class.assert_called_once_with(test_param="test_value", another_param=123)

    def test_create_config_and_kwargs_merge(self):
        """Test that config and kwargs are properly merged."""
        config = {"param1": "value1", "param2": "value2"}
        with patch('quantchain.core.secret_managers.factory.EnvSecretManager') as mock_class:
            mock_instance = MagicMock()
            mock_class.return_value = mock_instance
            
            manager = create_secret_manager(backend="env", config=config, param2="new_value2", param3="value3")
            
            mock_class.assert_called_once_with(param1="value1", param2="new_value2", param3="value3")

    def test_create_unsupported_backend(self):
        """Test creating secret manager with unsupported backend."""
        with pytest.raises(ValueError) as exc_info:
            create_secret_manager(backend="unsupported")
        
        assert "Unsupported secret backend: unsupported" in str(exc_info.value)
        assert "env" in str(exc_info.value)  # Should list available backends

    @patch('quantchain.core.secret_managers.factory._vault_available', False)
    def test_create_vault_not_available(self):
        """Test error when vault backend is not available."""
        with pytest.raises(ValueError) as exc_info:
            create_secret_manager(backend="vault")
        
        assert "Backend 'vault' is not available" in str(exc_info.value)
        assert "pip install hvac" in str(exc_info.value)

    @patch('quantchain.core.secret_managers.factory._aws_available', False)
    def test_create_aws_not_available(self):
        """Test error when AWS backend is not available."""
        with pytest.raises(ValueError) as exc_info:
            create_secret_manager(backend="aws")
        
        assert "Backend 'aws' is not available" in str(exc_info.value)
        assert "pip install boto3" in str(exc_info.value)

    @patch('quantchain.core.secret_managers.factory._gcp_available', False)
    def test_create_gcp_not_available(self):
        """Test error when GCP backend is not available."""
        with pytest.raises(ValueError) as exc_info:
            create_secret_manager(backend="gcp")
        
        assert "Backend 'gcp' is not available" in str(exc_info.value)
        assert "pip install google-cloud-secret-manager" in str(exc_info.value)

    def test_create_backend_case_insensitive(self):
        """Test that backend name is case insensitive."""
        with patch('quantchain.core.secret_managers.factory.EnvSecretManager') as mock_class:
            mock_instance = MagicMock()
            mock_class.return_value = mock_instance
            
            # Test uppercase
            create_secret_manager(backend="ENV")
            mock_class.assert_called()
            
            # Test mixed case
            create_secret_manager(backend="Env")
            assert mock_class.call_count == 2

    def test_create_backend_runtime_error(self):
        """Test handling runtime error during secret manager creation."""
        with patch('quantchain.core.secret_managers.factory.EnvSecretManager') as mock_class:
            mock_class.side_effect = Exception("Connection failed")
            
            with pytest.raises(RuntimeError) as exc_info:
                create_secret_manager(backend="env")
            
            assert "Failed to create env secret manager: Connection failed" in str(exc_info.value)


@pytest.mark.unit
class TestGetDefaultSecretManager:
    """Test get_default_secret_manager function."""

    @patch.dict(os.environ, {"QUANTCHAIN_SECRET_BACKEND": "env"})
    def test_get_default_from_env(self):
        """Test getting default secret manager from environment."""
        with patch('quantchain.core.secret_managers.factory.create_secret_manager') as mock_create:
            mock_manager = MagicMock()
            mock_create.return_value = mock_manager
            
            result = get_default_secret_manager()
            
            mock_create.assert_called_once_with()
            assert result == mock_manager

    def test_get_default_no_env(self):
        """Test getting default secret manager with no env var."""
        with patch.dict(os.environ, {}, clear=True):
            with patch('quantchain.core.secret_managers.factory.create_secret_manager') as mock_create:
                mock_manager = MagicMock()
                mock_create.return_value = mock_manager
                
                result = get_default_secret_manager()
                
                mock_create.assert_called_once_with()
                assert result == mock_manager


@pytest.mark.unit
class TestRegisterSecretManager:
    """Test register_secret_manager function."""

    def test_register_custom_manager(self):
        """Test registering a custom secret manager."""
        # Get original list
        original_managers = list_secret_managers()
        
        # Register custom manager
        register_secret_manager("custom", MockSecretManager)
        
        # Check it was added
        managers = list_secret_managers()
        assert "custom" in managers
        assert len(managers) == len(original_managers) + 1

    def test_register_overwrite_existing(self):
        """Test registering over an existing manager."""
        # Register a custom manager with existing name
        register_secret_manager("env", MockSecretManager)
        
        # Check the manager was replaced
        assert SECRET_MANAGERS["env"] == MockSecretManager

    def test_register_case_insensitive(self):
        """Test that registration is case insensitive."""
        register_secret_manager("TestManager", MockSecretManager)
        
        # Should be accessible in lowercase
        assert "testmanager" in SECRET_MANAGERS
        assert SECRET_MANAGERS["testmanager"] == MockSecretManager


@pytest.mark.unit
class TestListSecretManagers:
    """Test list_secret_managers function."""

    def test_list_all_managers(self):
        """Test listing all available managers."""
        managers = list_secret_managers()
        
        assert isinstance(managers, list)
        assert "env" in managers  # Should always have env manager
        assert len(managers) >= 1

    def test_list_after_register(self):
        """Test listing managers after registration."""
        original_count = len(list_secret_managers())
        
        register_secret_manager("test_manager", MockSecretManager)
        
        new_count = len(list_secret_managers())
        assert new_count == original_count + 1
        assert "test_manager" in list_secret_managers()


@pytest.mark.unit
class TestFactoryEdgeCases:
    """Test edge cases for factory functions."""

    @patch.dict(os.environ, {"QUANTCHAIN_SECRET_BACKEND": "env"})
    def test_env_backend_warning(self, caplog):
        """Test warning for env backend in production."""
        # Remove dev mode env var to trigger warning
        with patch.dict(os.environ, {}, clear=True):
            # Reset env var for this test
            os.environ["QUANTCHAIN_SECRET_BACKEND"] = "env"
            # Ensure QUANTCHAIN_DEV_MODE is not set
            
            with caplog.at_level('WARNING'):
                create_secret_manager()
            
            # Should log warning about production use
            warning_found = any(
                "environment variables for secret management" in record.message and
                "NOT recommended for production" in record.message
                for record in caplog.records
            )
            assert warning_found

    @patch.dict(os.environ, {"QUANTCHAIN_DEV_MODE": "true"})
    def test_env_backend_no_warning_in_dev(self, caplog):
        """Test no warning for env backend in development mode."""
        with caplog.at_level('WARNING'):
            create_secret_manager(backend="env")
        
        # Should not log warning in dev mode
        warning_found = any(
            "environment variables for secret management" in record.message
            for record in caplog.records
        )
        assert not warning_found

    def test_empty_config_dict(self):
        """Test creating manager with empty config dict."""
        config = {}
        with patch('quantchain.core.secret_managers.factory.EnvSecretManager') as mock_class:
            mock_instance = MagicMock()
            mock_class.return_value = mock_instance
            
            manager = create_secret_manager(backend="env", config=config)
            
            mock_class.assert_called_once_with()

    def test_none_config(self):
        """Test creating manager with None config."""
        with patch('quantchain.core.secret_managers.factory.EnvSecretManager') as mock_class:
            mock_instance = MagicMock()
            mock_class.return_value = mock_instance
            
            manager = create_secret_manager(backend="env", config=None)
            
            mock_class.assert_called_once_with()

    def test_backend_whitespace_handling(self):
        """Test backend name with whitespace."""
        with patch('quantchain.core.secret_managers.factory.EnvSecretManager') as mock_class:
            mock_instance = MagicMock()
            mock_class.return_value = mock_instance
            
            manager = create_secret_manager(backend="  env  ")
            
            mock_class.assert_called_once()


@pytest.mark.unit
class TestFactoryWithOptionalDependencies:
    """Test factory behavior with optional dependencies."""

    @patch('quantchain.core.secret_managers.factory._vault_available', True)
    @patch('quantchain.core.secret_managers.factory.VaultSecretManager')
    def test_create_vault_when_available(self, mock_vault_class):
        """Test creating vault manager when available."""
        mock_instance = MagicMock()
        mock_vault_class.return_value = mock_instance
        
        manager = create_secret_manager(backend="vault")
        
        assert manager == mock_instance
        mock_vault_class.assert_called_once()

    @patch('quantchain.core.secret_managers.factory._aws_available', True)
    @patch('quantchain.core.secret_managers.factory.AWSSecretsManager')
    def test_create_aws_when_available(self, mock_aws_class):
        """Test creating AWS manager when available."""
        mock_instance = MagicMock()
        mock_aws_class.return_value = mock_instance
        
        manager = create_secret_manager(backend="aws")
        
        assert manager == mock_instance
        mock_aws_class.assert_called_once()

    @patch('quantchain.core.secret_managers.factory._gcp_available', True)
    @patch('quantchain.core.secret_managers.factory.GCPSecretManager')
    def test_create_gcp_when_available(self, mock_gcp_class):
        """Test creating GCP manager when available."""
        mock_instance = MagicMock()
        mock_gcp_class.return_value = mock_instance
        
        manager = create_secret_manager(backend="gcp")
        
        assert manager == mock_instance
        mock_gcp_class.assert_called_once()


@pytest.mark.unit
class TestFactoryIntegration:
    """Integration-style tests for factory."""

    def test_full_workflow(self):
        """Test full workflow of registration and usage."""
        # Register custom manager
        register_secret_manager("integration_test", MockSecretManager)
        
        # Create manager using the registered type
        manager = create_secret_manager("integration_test", test_param="test_value")
        
        # Verify it works
        assert isinstance(manager, MockSecretManager)
        assert manager.config["test_param"] == "test_value"
        
        # Test it works as secret manager
        secret = manager.get_secret("test")
        assert secret == "mock_secret_test"

    def test_multiple_managers(self):
        """Test creating multiple different managers."""
        env_manager = create_secret_manager("env")
        
        register_secret_manager("test1", MockSecretManager)
        test1_manager = create_secret_manager("test1", param1="value1")
        
        register_secret_manager("test2", MockSecretManager)
        test2_manager = create_secret_manager("test2", param2="value2")
        
        # All should be different instances
        assert env_manager is not test1_manager
        assert env_manager is not test2_manager
        assert test1_manager is not test2_manager
        
        # Each should have correct config
        assert test1_manager.config["param1"] == "value1"
        assert test2_manager.config["param2"] == "value2"
