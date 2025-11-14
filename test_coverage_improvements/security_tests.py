"""
Comprehensive tests for security.py to improve coverage from 38.9% to 90%+
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import re
import os
import tempfile
import json
from pathlib import Path

# Import the actual classes from the security module
from quantchain.core.security import (
    APISecurityManager,
    API_KEY_PATTERNS,
    CredentialNotFoundError,
    SecurityConfigurationError
)


class TestAPISecurityManager:
    """Test APISecurityManager class"""

    @patch('quantchain.core.security.create_secret_manager')
    @patch('quantchain.core.security.get_default_secret_manager')
    def test_initialization_with_default_manager(self, mock_get_default, mock_create):
        """Test initialization with default secret manager"""
        # Setup mocks
        mock_manager = Mock()
        mock_get_default.return_value = mock_manager

        # Create manager
        manager = APISecurityManager()

        # Verify default manager was used
        mock_get_default.assert_called_once()
        mock_create.assert_not_called()
        assert manager._secret_manager == mock_manager
        assert manager.api_key_patterns == API_KEY_PATTERNS

    @patch('quantchain.core.security.create_secret_manager')
    def test_initialization_with_backend(self, mock_create):
        """Test initialization with specific backend"""
        # Setup mocks
        mock_manager = Mock()
        mock_create.return_value = mock_manager

        # Create manager with backend
        manager = APISecurityManager(backend="vault")

        # Verify create was called with backend
        mock_create.assert_called_once_with("vault", None)
        assert manager._secret_manager == mock_manager
        assert manager.api_key_patterns == API_KEY_PATTERNS

    @patch('quantchain.core.security.create_secret_manager')
    def test_initialization_with_config(self, mock_create):
        """Test initialization with configuration"""
        # Setup mocks
        mock_manager = Mock()
        mock_create.return_value = mock_manager

        # Create manager with config
        config = {"test": "config"}
        manager = APISecurityManager(config=config)

        # Verify create was called with config
        mock_create.assert_called_once_with(None, config)
        assert manager._secret_manager == mock_manager

    @patch('quantchain.core.security.create_secret_manager')
    def test_initialization_with_env_file_compatibility(self, mock_create):
        """Test initialization with .env file (backward compatibility)"""
        # Setup mocks
        mock_manager = Mock()
        mock_create.return_value = mock_manager

        # Create manager with .env file
        manager = APISecurityManager(backend=".env")

        # Verify create was called with env backend and env_file
        mock_create.assert_called_once_with("env", None, env_file=".env")
        assert manager._secret_manager == mock_manager

    @patch('quantchain.core.security.create_secret_manager')
    def test_initialization_with_kwargs(self, mock_create):
        """Test initialization with additional kwargs"""
        # Setup mocks
        mock_manager = Mock()
        mock_create.return_value = mock_manager

        # Create manager with kwargs
        manager = APISecurityManager(test_kwarg="test_value")

        # Verify create was called with kwargs
        mock_create.assert_called_once_with(None, None, test_kwarg="test_value")
        assert manager._secret_manager == mock_manager

    def test_get_api_key_success(self):
        """Test successful API key retrieval"""
        # Setup mocks
        mock_manager = Mock()
        mock_manager.get_api_key.return_value = "test_api_key"

        manager = APISecurityManager()
        manager._secret_manager = mock_manager

        # Get API key
        result = manager.get_api_key("test_service")

        # Verify manager was called and key returned
        mock_manager.get_api_key.assert_called_once_with("test_service")
        assert result == "test_api_key"

    def test_get_api_key_not_found(self):
        """Test API key not found"""
        # Setup mocks
        mock_manager = Mock()
        mock_manager.get_api_key.return_value = None

        manager = APISecurityManager()
        manager._secret_manager = mock_manager

        # Should raise exception
        with pytest.raises(CredentialNotFoundError, match="No API key found"):
            manager.get_api_key("test_service")

    def test_get_api_secret_success(self):
        """Test successful API secret retrieval"""
        # Setup mocks
        mock_manager = Mock()
        mock_manager.get_api_secret.return_value = "test_secret"

        manager = APISecurityManager()
        manager._secret_manager = mock_manager

        # Get API secret
        result = manager.get_api_secret("test_service")

        # Verify manager was called and secret returned
        mock_manager.get_api_secret.assert_called_once_with("test_service")
        assert result == "test_secret"

    def test_get_api_secret_none(self):
        """Test API secret that doesn't exist (returns None)"""
        # Setup mocks
        mock_manager = Mock()
        mock_manager.get_api_secret.return_value = None

        manager = APISecurityManager()
        manager._secret_manager = mock_manager

        # Get API secret
        result = manager.get_api_secret("test_service")

        # Verify manager was called and None returned
        mock_manager.get_api_secret.assert_called_once_with("test_service")
        assert result is None

    @patch('quantchain.core.security.APISecurityManager')
    def test_set_api_key_with_env_manager(self, mock_api_manager_class):
        """Test set_api_key with EnvSecretManager"""
        # Setup mocks
        mock_manager_instance = Mock()
        mock_manager_instance.set_api_key = Mock()
        mock_api_manager_class.return_value = mock_manager_instance

        # Create manager instance with env backend
        manager = APISecurityManager(backend="env")

        # Set API key
        manager.set_api_key("test_service", "test_key")

        # Verify method was called
        manager._secret_manager.set_api_key.assert_called_once_with("test_service", "test_key", None)

    @patch('quantchain.core.security.logger')
    def test_set_api_key_warning(self, mock_logger):
        """Test set_api_key logs warning"""
        # Setup mocks
        mock_manager = Mock()
        # Mock without set_api_key method
        manager = APISecurityManager()
        manager._secret_manager = mock_manager

        # Set API key
        manager.set_api_key("test_service", "test_key")

        # Verify warning was logged
        mock_logger.warning.assert_called_once()

    @patch('quantchain.core.security.APISecurityManager')
    def test_set_api_key_with_production_manager(self, mock_api_manager_class):
        """Test set_api_key with production secret manager"""
        # Setup mocks
        mock_manager_instance = Mock()
        # Mock without set_api_key method
        mock_api_manager_class.return_value = mock_manager_instance

        # Create manager instance with production backend
        manager = APISecurityManager(backend="vault")

        # Should raise exception
        with pytest.raises(SecurityConfigurationError, match="Cannot set credentials"):
            manager.set_api_key("test_service", "test_key")

    def test_validate_credentials_valid_pattern(self):
        """Test credential validation with valid pattern"""
        # Setup mocks
        mock_manager = Mock()
        mock_manager.get_api_key.return_value = "AKABCDEFGHIJKLMNOPQRS"  # Valid Alpaca pattern

        manager = APISecurityManager()
        manager._secret_manager = mock_manager

        # Validate with default key (stored)
        result = manager.validate_credentials("alpaca")

        # Should return True
        assert result is True

    def test_validate_credentials_invalid_pattern(self):
        """Test credential validation with invalid pattern"""
        # Setup mocks
        mock_manager = Mock()
        mock_manager.get_api_key.return_value = "invalid_key"  # Invalid Alpaca pattern

        manager = APISecurityManager()
        manager._secret_manager = mock_manager

        # Validate with default key (stored)
        result = manager.validate_credentials("alpaca")

        # Should return False
        assert result is False

    def test_validate_credentials_with_provided_key(self):
        """Test credential validation with provided key"""
        manager = APISecurityManager()

        # Test with valid key
        result = manager.validate_credentials("alpaca", key="AKABCDEFGHIJKLMNOPQRS")
        assert result is True

        # Test with invalid key
        result = manager.validate_credentials("alpaca", key="invalid_key")
        assert result is False

    def test_validate_credentials_with_provided_secret(self):
        """Test credential validation with provided secret"""
        manager = APISecurityManager()

        # Test with valid secret (Base64-like)
        result = manager.validate_credentials("alpaca", secret="ABCDEFGHIJKLMNOPABCDEFGHIJKLMNOPABCDEFGHIJKLMNOP")
        assert result is True

        # Test with invalid secret
        result = manager.validate_credentials("alpaca", secret="invalid")
        assert result is False

    def test_validate_credentials_unknown_service(self):
        """Test credential validation for unknown service"""
        manager = APISecurityManager()

        # Should return False for unknown service
        result = manager.validate_credentials("unknown_service", key="some_key")
        assert result is False

    def test_alpaca_pattern_validation(self):
        """Test Alpaca API key pattern validation"""
        manager = APISecurityManager()

        # Valid Alpaca keys
        valid_keys = [
            "AKABCDEFGHIJKLMNOPQRS",  # Minimum 16 chars
            "AKABCDEFGHIJKLMNOPQRSTUV",  # More than 16 chars
            "AKABCDEFGHIJKLMNOPQRSTU"  # Maximum 20 chars
        ]

        for key in valid_keys:
            assert manager.validate_credentials("alpaca", key=key) is True

        # Invalid Alpaca keys
        invalid_keys = [
            "KABCDEFGHIJKLMNOPQRS",  # Doesn't start with 'A'
            "AKABCDEFGHIJKLMNOPQR",  # Too short (15 chars)
            "AKABCDEFGHIJKLMNOPQRSTUVWX",  # Too long (22 chars)
            "ABCDEFGHIJKLMNOPQRS",  # Missing 'A' prefix but right length
        ]

        for key in invalid_keys:
            assert manager.validate_credentials("alpaca", key=key) is False

    def test_polygon_pattern_validation(self):
        """Test Polygon API key pattern validation"""
        manager = APISecurityManager()

        # Valid Polygon keys
        valid_keys = [
            "abcdefghijklmnopqrstu",  # 20 chars
            "abcdefghijklmnopqrstuv",  # 22 chars
            "abcdefghijklmnopqrstuvwx",  # 24 chars
            "ABCDEFGHIJKLMNOPQRSTUVWX",  # Uppercase allowed
            "abcdefghijklmnopqrstuvwx_123",  # Underscore and digits allowed
            "abcdefghijklmnop-qrstuv",  # Hyphen allowed
        ]

        for key in valid_keys:
            assert manager.validate_credentials("polygon", key=key) is True

        # Invalid Polygon keys
        invalid_keys = [
            "abcdefghijklmnopqrst",  # Too short (18 chars)
            "abcdefghijklmnopqrstu",  # 21 chars with trailing space
            "abcdefghijklmnopqrstuvwxyza",  # 26 chars (too long)
            "abcdefghijklmnopqrstu@",  # Invalid character '@'
        ]

        for key in invalid_keys:
            assert manager.validate_credentials("polygon", key=key) is False

    def test_alpha_vantage_pattern_validation(self):
        """Test Alpha Vantage API key pattern validation"""
        manager = APISecurityManager()

        # Valid Alpha Vantage keys
        valid_keys = [
            "ABCDEFGHIJKLMNOP",  # 16 chars
            "A1B2C3D4E5F6G7H8"  # Mix of letters and numbers
        ]

        for key in valid_keys:
            assert manager.validate_credentials("alpha_vantage", key=key) is True

        # Invalid Alpha Vantage keys
        invalid_keys = [
            "ABCDEFGHIJKLMNO",    # 15 chars (too short)
            "ABCDEFGHIJKLMNOPQ",  # 17 chars (too long)
            "ABCDEFGHIJKLMNOP!"  # Invalid character '!'
        ]

        for key in invalid_keys:
            assert manager.validate_credentials("alpha_vantage", key=key) is False

    def test_anthropic_pattern_validation(self):
        """Test Anthropic API key pattern validation"""
        manager = APISecurityManager()

        # Valid Anthropic keys
        valid_keys = [
            "sk-ant-api03aBCdefghijKLMnopqrstu",  # Minimum 35 chars
            "sk-ant-api03" + "A"*80  # Maximum 90 chars
        ]

        for key in valid_keys:
            assert manager.validate_credentials("anthropic", key=key) is True

        # Invalid Anthropic keys
        invalid_keys = [
            "sk-ant-api03BCdefghijKLMnopqrstu",  # Too short (33 chars)
            "sk-ant-api03" + "A"*110,  # Too long (115 chars)
            "sk-anthropic-aBCdefghijKLMnopqrstu",  # Missing 'api03' part
        ]

        for key in invalid_keys:
            assert manager.validate_credentials("anthropic", key=key) is False

    def test_openai_pattern_validation(self):
        """Test OpenAI API key pattern validation"""
        manager = APISecurityManager()

        # Valid OpenAI keys
        valid_keys = [
            "sk-1234567890abcdefghijklmnopqr",  # 31 chars (minimum)
            "sk-" + "A"*180  # Maximum 183 chars
        ]

        for key in valid_keys:
            assert manager.validate_credentials("openai", key=key) is True

        # Invalid OpenAI keys
        invalid_keys = [
            "1234567890abcdefghijklmnopqr",  # Missing 'sk-' prefix
            "sk-1234567890abcdefghijklmnopq",  # Too short (30 chars)
            "sk-" + "A"*201  # Too long (205 chars)
        ]

        for key in invalid_keys:
            assert manager.validate_credentials("openai", key=key) is False


class TestCredentialNotFoundError:
    """Test CredentialNotFoundError exception"""

    def test_exception_initialization(self):
        """Test exception initialization"""
        error = CredentialNotFoundError("Test message")

        assert str(error) == "Test message"
        assert isinstance(error, Exception)

    def test_exception_inheritance(self):
        """Test exception inheritance"""
        # Should inherit from Exception
        assert issubclass(CredentialNotFoundError, Exception)


class TestSecurityConfigurationError:
    """Test SecurityConfigurationError exception"""

    def test_exception_initialization(self):
        """Test exception initialization"""
        error = SecurityConfigurationError("Test message")

        assert str(error) == "Test message"
        assert isinstance(error, Exception)

    def test_exception_inheritance(self):
        """Test exception inheritance"""
        # Should inherit from Exception
        assert issubclass(SecurityConfigurationError, Exception)


class TestAPIKeyPatterns:
    """Test API_KEY_PATTERNS constant"""

    def test_patterns_structure(self):
        """Test that patterns have the expected structure"""
        # Should have patterns for known services
        assert "alpaca" in API_KEY_PATTERNS
        assert "polygon" in API_KEY_PATTERNS
        assert "alpha_vantage" in API_KEY_PATTERNS
        assert "anthropic" in API_KEY_PATTERNS
        assert "openai" in API_KEY_PATTERNS

        # Each pattern should have key_pattern
        for service, patterns in API_KEY_PATTERNS.items():
            assert "key_pattern" in patterns
            assert "secret_pattern" in patterns

    def test_alpaca_pattern_regex(self):
        """Test Alpaca pattern regex"""
        pattern = re.compile(API_KEY_PATTERNS["alpaca"]["key_pattern"])

        # Valid matches
        assert pattern.match("AKABCDEFGHIJKLMNOPQRS") is not None
        assert pattern.match("AK1234567890123456") is not None

        # Invalid matches
        assert pattern.match("KABCDEFGHIJKLMNOPQRS") is None  # Doesn't start with A
        assert pattern.match("AK12345") is None  # Too short

    def test_polygon_pattern_regex(self):
        """Test Polygon pattern regex"""
        pattern = re.compile(API_KEY_PATTERNS["polygon"]["key_pattern"])

        # Valid matches
        assert pattern.match("abcdefghijklmnopqrstu") is not None
        assert pattern.match("1234567890123456789012") is not None

        # Invalid matches
        assert pattern.match("abcdefghijklmnopqrst") is None  # Too short
        assert pattern.match("abcdefghijklmnopqrst@uv") is None  # Invalid character

    def test_alpha_vantage_pattern_regex(self):
        """Test Alpha Vantage pattern regex"""
        pattern = re.compile(API_KEY_PATTERNS["alpha_vantage"]["key_pattern"])

        # Valid matches
        assert pattern.match("ABCDEFGHIJKLMNOP") is not None
        assert pattern.match("1234567890123456") is not None

        # Invalid matches
        assert pattern.match("ABCDEFGHIJKLMNO") is None  # Too short
        assert pattern.match("ABCDEFGHIJKLMNOPQ") is None  # Too long

    def test_anthropic_pattern_regex(self):
        """Test Anthropic pattern regex"""
        pattern = re.compile(API_KEY_PATTERNS["anthropic"]["key_pattern"])

        # Valid matches
        assert pattern.match("sk-ant-api03abcdefghijklmnopqrstu") is not None
        assert pattern.match("sk-ant-api031234567890123456789012") is not None

        # Invalid matches
        assert pattern.match("sk-ant-apiaBCdefghijKLMnopqrstu") is None  # Missing '03'
        assert pattern.match("sk-ant-api03BCdefghijKLMnopqr") is None  # Too short

    def test_openai_pattern_regex(self):
        """Test OpenAI pattern regex"""
        pattern = re.compile(API_KEY_PATTERNS["openai"]["key_pattern"])

        # Valid matches
        assert pattern.match("sk-1234567890abcdefghijklmnopqr") is not None
        assert pattern.match("sk-abc123") is not None

        # Invalid matches
        assert pattern.match("1234567890abcdefghijklmnopqr") is None  # Missing 'sk-'
        assert pattern.match("sk-123") is None  # Too short


class TestSecurityIntegration:
    """Integration tests for security functionality"""

    @patch('quantchain.core.security.create_secret_manager')
    @patch('quantchain.core.security.get_default_secret_manager')
    def test_env_file_integration(self, mock_get_default, mock_create):
        """Test integration with .env file"""
        # Setup mocks
        mock_manager = Mock()
        mock_manager.get_api_key.return_value = "test_api_key"
        mock_manager.set_api_key = Mock()

        # Create .env file with test content
        with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
            f.write("TEST_SERVICE=test_api_key\n")
            f.flush()

            # Initialize with .env file
            manager = APISecurityManager(backend=f.name)

            # Verify env file was set
            assert manager._secret_manager == mock_manager

            # Test retrieving key
            result = manager.get_api_key("TEST_SERVICE")
            assert result == "test_api_key"

            # Test setting key
            manager.set_api_key("TEST_SERVICE", "new_key")
            mock_manager.set_api_key.assert_called_once_with("TEST_SERVICE", "new_key", None)

            # Clean up
            os.unlink(f.name)

    @patch('quantchain.core.security.create_secret_manager')
    def test_custom_configuration(self, mock_create):
        """Test with custom configuration"""
        # Setup mocks
        mock_manager = Mock()
        mock_manager.get_api_key.return_value = "test_key"
        mock_create.return_value = mock_manager

        # Custom config
        config = {"test_param": "test_value"}
        manager = APISecurityManager(config=config)

        # Verify config was passed
        mock_create.assert_called_once_with(None, config)

        # Test getting key
        result = manager.get_api_key("test_service")
        assert result == "test_key"

    def test_multiple_service_credentials(self):
        """Test working with multiple service credentials"""
        manager = APISecurityManager()

        # Test keys for different services
        alpaca_key = "AKABCDEFGHIJKLMNOPQRS"
        polygon_key = "abcdefghijklmnopqrstu"

        # Validate each
        assert manager.validate_credentials("alpaca", key=alpaca_key) is True
        assert manager.validate_credentials("polygon", key=polygon_key) is True

        # Cross-validate (should fail)
        assert manager.validate_credentials("alpaca", key=polygon_key) is False
        assert manager.validate_credentials("polygon", key=alpaca_key) is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
