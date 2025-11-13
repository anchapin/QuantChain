"""Edge case tests for security module to achieve 100% coverage."""

import os
from unittest.mock import MagicMock, patch

import pytest

from quantchain.core.security import (
    APISecurityManager,
    CredentialNotFoundError,
    SecurityConfigurationError,
)


@pytest.mark.unit
class TestSecurityEdgeCases:
    """Edge case tests for security module."""

    def test_set_api_key_production_manager_raises_error(self):
        """Test that set_api_key raises error for production secret managers."""
        # Create a mock secret manager that doesn't have set_api_key method
        mock_secret_manager = MagicMock()
        del mock_secret_manager.set_api_key  # Remove the method
        
        with patch('quantchain.core.security.get_default_secret_manager', return_value=mock_secret_manager):
            manager = APISecurityManager()
            
            with pytest.raises(SecurityConfigurationError) as exc_info:
                manager.set_api_key("openai", "sk-test-key")
            
            assert "Cannot set credentials in production secret managers" in str(exc_info.value)

    def test_validate_credentials_service_without_pattern(self):
        """Test validate_credentials for service not in patterns."""
        manager = APISecurityManager()
        
        # Test with service that has no pattern (should return False)
        result = manager.validate_credentials("nonexistent_service")
        assert result is False

    def test_init_with_env_file_backward_compatibility(self):
        """Test initialization with .env file for backward compatibility."""
        import tempfile
        from unittest.mock import patch
        
        with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as f:
            f.write('OPENAI_API_KEY="test-key"\n')
            env_file_path = f.name
        
        try:
            # Test backward compatibility: passing .env file as first argument
            with patch.dict(os.environ, {}, clear=True):
                # This should use 'env' backend due to .env extension
                manager = APISecurityManager(env_file_path)
                assert manager is not None
        finally:
            os.unlink(env_file_path)

    def test_validate_credentials_empty_key_with_secret(self):
        """Test validate_credentials with empty key but provided secret."""
        manager = APISecurityManager()
        
        # Test with empty key (should fail validation)
        result = manager.validate_credentials("openai", "", "some-secret")
        assert result is False

    def test_validate_credentials_no_key_with_secret_for_service_without_secret(self):
        """Test validate_credentials with no key but secret for service that doesn't need secret."""
        import os
        from unittest.mock import patch
        
        # Clear environment variables that might interfere
        with patch.dict(os.environ, {}, clear=True), \
             patch('quantchain.core.secret_managers.env.Path.exists', return_value=False):
            manager = APISecurityManager()
            
            # For openai which doesn't require secret, if key is None but secret is provided
            # According to the logic, this returns True because "No secret required for this service"
            result = manager.validate_credentials("openai", None, "some-secret")
            assert result is True

    def test_validate_credentials_key_none_with_secret_none(self):
        """Test validate_credentials when both key and secret are None."""
        import os
        from unittest.mock import patch
        
        # Clear environment variables that might interfere
        with patch.dict(os.environ, {}, clear=True), \
             patch('quantchain.core.secret_managers.env.Path.exists', return_value=False):
            manager = APISecurityManager()
            
            # Mock secret manager to return None for both
            manager._secret_manager.get_api_key = MagicMock(return_value=None)
            manager._secret_manager.get_api_secret = MagicMock(return_value=None)
            
            # This should return False as no credentials are provided
            result = manager.validate_credentials("openai", None, None)
            assert result is False

    def test_validate_credentials_key_none_with_secret_valid(self):
        """Test validate_credentials with key=None but valid secret."""
        import os
        from unittest.mock import patch
        
        # Clear environment variables that might interfere
        with patch.dict(os.environ, {}, clear=True), \
             patch('quantchain.core.secret_managers.env.Path.exists', return_value=False):
            manager = APISecurityManager()
            
            # Mock secret manager to return None for key (not stored) but secret is provided
            manager._secret_manager.get_api_key = MagicMock(return_value=None)
            
            # For alpaca which requires secret, test with key=None but valid secret
            # This should pass the secret validation
            result = manager.validate_credentials("alpaca", None, "wJalrXUtnFEMIK7MDENGbPxRfiCYEXAMPLEKEY123456789")
            assert result is True

    def test_validate_credentials_with_stored_credentials_missing_secret(self):
        """Test validate_credentials when stored credentials are missing required secret."""
        manager = APISecurityManager()
        
        # Mock secret manager to return only key but no secret for alpaca
        mock_creds = {"key": "ABCDEFGHIJKLMNOPQRST"}
        manager._secret_manager.get_api_key = MagicMock(return_value="ABCDEFGHIJKLMNOPQRST")
        manager._secret_manager.get_api_secret = MagicMock(return_value=None)
        
        # This should fail because alpaca requires secret but it's missing
        result = manager.validate_credentials("alpaca")
        assert result is False

    def test_validate_credentials_when_secret_required_but_none_provided(self):
        """Test line 170: when secret is required but None is provided."""
        import os
        from unittest.mock import patch
        
        # Clear environment variables that might interfere
        with patch.dict(os.environ, {}, clear=True), \
             patch('quantchain.core.secret_managers.env.Path.exists', return_value=False):
            manager = APISecurityManager()
            
            # Mock secret manager to return key but None for secret 
            manager._secret_manager.get_api_key = MagicMock(return_value="AAAAAAAAAAAAAAAAAAA")
            manager._secret_manager.get_api_secret = MagicMock(return_value=None)
            
            # This should fail because secret is required but not provided (line 170)
            result = manager.validate_credentials("alpaca")
            assert result is False