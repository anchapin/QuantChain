"""
Comprehensive tests for quantchain.core.security module.
"""

import os
import tempfile
import pytest
from unittest.mock import Mock, patch, mock_open

from quantchain.core.security import (
    APISecurityManager,
    CredentialNotFoundError,
    SecurityConfigurationError,
    InvalidCredentialFormatError,
    API_KEY_PATTERNS,
    SecretManager,
    get_default_secret_manager,
    create_secret_manager,
)


@pytest.mark.unit
class TestSecretManager:
    """Test placeholder SecretManager implementation."""

    def test_secret_manager_get(self) -> None:
        """Test SecretManager get method."""
        manager = SecretManager()
        result = manager.get("test_key")
        assert result is None

    def test_secret_manager_set(self) -> None:
        """Test SecretManager set method."""
        manager = SecretManager()
        manager.set("test_key", "test_value")
        # Should not raise exception

    def test_secret_manager_get_secret(self) -> None:
        """Test SecretManager get_secret method."""
        manager = SecretManager()
        result = manager.get_secret("test_secret")
        assert result is None

    def test_secret_manager_set_secret(self) -> None:
        """Test SecretManager set_secret method."""
        manager = SecretManager()
        manager.set_secret("test_secret", "test_value")
        # Should not raise exception

    def test_secret_manager_delete_secret(self) -> None:
        """Test SecretManager delete_secret method."""
        manager = SecretManager()
        manager.delete_secret("test_secret")
        # Should not raise exception


@pytest.mark.unit
class TestSecretManagerFunctions:
    """Test secret manager factory functions."""

    def test_get_default_secret_manager(self) -> None:
        """Test getting default secret manager."""
        manager = get_default_secret_manager()
        assert isinstance(manager, SecretManager)

    def test_create_secret_manager(self) -> None:
        """Test creating secret manager with backend."""
        manager = create_secret_manager("test_backend", test_param="test_value")
        assert isinstance(manager, SecretManager)


@pytest.mark.unit
class TestAPISecurityManager:
    """Test APISecurityManager class."""

    def test_init_without_env_file(self) -> None:
        """Test initialization without env file."""
        manager = APISecurityManager(env_file=".env_test")
        assert manager.env_file == ".env_test"
        assert isinstance(manager._services, dict)
        assert manager._secret_manager is not None

    @patch("os.path.exists")
    def test_init_with_env_file(self, mock_exists: Mock) -> None:
        """Test initialization with existing env file."""
        mock_exists.return_value = True
        with patch("builtins.open", mock_open(read_data="ALPACA_API_KEY=test_key\n")):
            manager = APISecurityManager(env_file=".env")
            # Should load from env file
            assert "alpaca" in manager._services

    @patch.dict(os.environ, {
        "ALPACA_API_KEY": "test_alpaca_key",
        "ALPACA_API_SECRET": "test_alpaca_secret",
        "POLYGON_API_KEY": "test_polygon_key",
        "ALPHA_VANTAGE_API_KEY": "test_alpha_key",
        "ANTHROPIC_API_KEY": "test_anthropic_key",
        "OPENAI_API_KEY": "test_openai_key",
    })
    def test_load_from_environment(self) -> None:
        """Test loading credentials from environment variables."""
        manager = APISecurityManager()

        assert manager._services["alpaca"]["key"] == "test_alpaca_key"
        assert manager._services["alpaca"]["secret"] == "test_alpaca_secret"
        assert manager._services["polygon"]["key"] == "test_polygon_key"
        assert manager._services["alpha_vantage"]["key"] == "test_alpha_key"
        assert manager._services["anthropic"]["key"] == "test_anthropic_key"
        assert manager._services["openai"]["key"] == "test_openai_key"

    def test_load_from_env_file(self) -> None:
        """Test loading credentials from .env file."""
        env_content = """
# This is a comment
ALPACA_API_KEY=test_key_from_file
ALPACA_API_SECRET=test_secret_from_file
POLYGON_API_KEY=test_polygon_from_file
# Another comment
ALPHA_VANTAGE_API_KEY=test_alpha_from_file
"""
        with patch("builtins.open", mock_open(read_data=env_content)):
            with patch("os.path.exists", return_value=True):
                manager = APISecurityManager(env_file=".env")

                assert manager._services["alpaca"]["key"] == "test_key_from_file"
                assert manager._services["alpaca"]["secret"] == "test_secret_from_file"
                assert manager._services["polygon"]["key"] == "test_polygon_from_file"
                assert manager._services["alpha_vantage"]["key"] == "test_alpha_from_file"

    def test_load_from_env_file_with_exception(self) -> None:
        """Test loading from env file with exception."""
        with patch("builtins.open", side_effect=IOError("Permission denied")):
            with patch("os.path.exists", return_value=True):
                # Should not raise exception
                manager = APISecurityManager(env_file=".env")
                assert isinstance(manager._services, dict)

    def test_set_api_key_empty_key(self) -> None:
        """Test setting API key with empty key."""
        manager = APISecurityManager()
        with pytest.raises(SecurityConfigurationError):
            manager.set_api_key("alpaca", "")

    def test_set_api_key_invalid_format(self) -> None:
        """Test setting API key with invalid format."""
        manager = APISecurityManager()
        with pytest.raises(InvalidCredentialFormatError):
            manager.set_api_key("alpaca", "invalid_key")

    def test_set_api_key_valid_format(self) -> None:
        """Test setting API key with valid format."""
        manager = APISecurityManager()
        valid_key = "ABCDEFGHIJKLMNOP"
        manager.set_api_key("alpaca", valid_key)
        assert manager._services["alpaca"]["key"] == valid_key

    def test_set_api_key_with_secret(self) -> None:
        """Test setting API key with secret."""
        manager = APISecurityManager()
        valid_key = "ABCDEFGHIJKLMNOP"
        valid_secret = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"
        manager.set_api_key("alpaca", valid_key, valid_secret)
        assert manager._services["alpaca"]["key"] == valid_key
        assert manager._services["alpaca"]["secret"] == valid_secret

    def test_set_api_key_invalid_secret_format(self) -> None:
        """Test setting API key with invalid secret format."""
        manager = APISecurityManager()
        valid_key = "ABCDEFGHIJKLMNOP"
        invalid_secret = "invalid_secret"
        with pytest.raises(InvalidCredentialFormatError):
            manager.set_api_key("alpaca", valid_key, invalid_secret)

    @patch.object(SecretManager, 'set_secret')
    def test_set_api_key_with_secret_manager(self, mock_set_secret: Mock) -> None:
        """Test setting API key with secret manager."""
        manager = APISecurityManager()
        valid_key = "ABCDEFGHIJKLMNOP"
        manager.set_api_key("alpaca", valid_key)

        # Should call secret manager set_secret
        mock_set_secret.assert_called_with("alpaca_api_key", valid_key)

    @patch.object(SecretManager, 'set_secret', side_effect=Exception("Secret manager error"))
    def test_set_api_key_secret_manager_failure(self, mock_set_secret: Mock) -> None:
        """Test setting API key when secret manager fails."""
        manager = APISecurityManager()
        valid_key = "ABCDEFGHIJKLMNOP"
        # Should not raise exception, fall back to memory storage
        manager.set_api_key("alpaca", valid_key)
        assert manager._services["alpaca"]["key"] == valid_key

    def test_get_api_key_not_found(self) -> None:
        """Test getting API key that doesn't exist."""
        manager = APISecurityManager()
        with pytest.raises(CredentialNotFoundError):
            manager.get_api_key("nonexistent_service")

    def test_get_api_key_from_memory(self) -> None:
        """Test getting API key from memory."""
        manager = APISecurityManager()
        valid_key = "ABCDEFGHIJKLMNOP"
        manager.set_api_key("alpaca", valid_key)
        retrieved_key = manager.get_api_key("alpaca")
        assert retrieved_key == valid_key

    @patch.object(SecretManager, 'get_secret')
    def test_get_api_key_from_secret_manager(self, mock_get_secret: Mock) -> None:
        """Test getting API key from secret manager."""
        manager = APISecurityManager()
        valid_key = "ABCDEFGHIJKLMNOP"
        mock_get_secret.return_value = valid_key

        retrieved_key = manager.get_api_key("alpaca")
        assert retrieved_key == valid_key
        assert manager._services["alpaca"]["key"] == valid_key  # Should cache in memory

    @patch.object(SecretManager, 'get_secret', side_effect=Exception("Secret manager error"))
    def test_get_api_key_secret_manager_failure(self, mock_get_secret: Mock) -> None:
        """Test getting API key when secret manager fails."""
        manager = APISecurityManager()
        with pytest.raises(CredentialNotFoundError):
            manager.get_api_key("nonexistent_service")

    def test_get_api_secret_not_found(self) -> None:
        """Test getting API secret that doesn't exist."""
        manager = APISecurityManager()
        result = manager.get_api_secret("nonexistent_service")
        assert result is None

    def test_get_api_secret_from_memory(self) -> None:
        """Test getting API secret from memory."""
        manager = APISecurityManager()
        valid_key = "ABCDEFGHIJKLMNOP"
        valid_secret = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"
        manager.set_api_key("alpaca", valid_key, valid_secret)
        retrieved_secret = manager.get_api_secret("alpaca")
        assert retrieved_secret == valid_secret

    @patch.object(SecretManager, 'get_secret')
    def test_get_api_secret_from_secret_manager(self, mock_get_secret: Mock) -> None:
        """Test getting API secret from secret manager."""
        manager = APISecurityManager()
        valid_secret = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"
        mock_get_secret.return_value = valid_secret

        retrieved_secret = manager.get_api_secret("alpaca")
        assert retrieved_secret == valid_secret

    def test_validate_credentials_no_service(self) -> None:
        """Test validating credentials for service without patterns."""
        manager = APISecurityManager()
        result = manager.validate_credentials("unknown_service", "any_key")
        assert result is True

    def test_validate_credentials_invalid_format(self) -> None:
        """Test validating credentials with invalid format."""
        manager = APISecurityManager()
        result = manager.validate_credentials("alpaca", "invalid_key")
        assert result is False

    def test_validate_credentials_valid_format(self) -> None:
        """Test validating credentials with valid format."""
        manager = APISecurityManager()
        valid_key = "ABCDEFGHIJKLMNOP"
        result = manager.validate_credentials("alpaca", valid_key)
        assert result is True

    def test_validate_credentials_with_secret(self) -> None:
        """Test validating credentials with secret."""
        manager = APISecurityManager()
        valid_key = "ABCDEFGHIJKLMNOP"
        valid_secret = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"
        result = manager.validate_credentials("alpaca", valid_key, valid_secret)
        assert result is True

    def test_validate_credentials_invalid_secret_format(self) -> None:
        """Test validating credentials with invalid secret format."""
        manager = APISecurityManager()
        valid_key = "ABCDEFGHIJKLMNOP"
        invalid_secret = "invalid_secret"
        result = manager.validate_credentials("alpaca", valid_key, invalid_secret)
        assert result is False

    def test_validate_credentials_not_found(self) -> None:
        """Test validating credentials when key not found."""
        manager = APISecurityManager()
        result = manager.validate_credentials("nonexistent_service")
        assert result is False

    def test_list_services(self) -> None:
        """Test listing all configured services."""
        manager = APISecurityManager()
        manager.set_api_key("alpaca", "ABCDEFGHIJKLMNOP")
        manager.set_api_key("polygon", "test_polygon_key")

        services = manager.list_services()
        assert "alpaca" in services
        assert "polygon" in services
        assert len(services) == 2

    def test_remove_service(self) -> None:
        """Test removing stored credentials for a service."""
        manager = APISecurityManager()
        manager.set_api_key("alpaca", "ABCDEFGHIJKLMNOP")
        manager.remove_service("alpaca")

        assert "alpaca" not in manager._services

    @patch.object(SecretManager, 'delete_secret')
    def test_remove_service_with_secret_manager(self, mock_delete_secret: Mock) -> None:
        """Test removing service with secret manager."""
        manager = APISecurityManager()
        manager.set_api_key("alpaca", "ABCDEFGHIJKLMNOP")
        manager.remove_service("alpaca")

        # Should call secret manager delete_secret for both key and secret
        mock_delete_secret.assert_any_call("alpaca_api_key")
        mock_delete_secret.assert_any_call("alpaca_api_secret")

    @patch.object(SecretManager, 'delete_secret', side_effect=Exception("Secret manager error"))
    def test_remove_service_secret_manager_failure(self, mock_delete_secret: Mock) -> None:
        """Test removing service when secret manager fails."""
        manager = APISecurityManager()
        manager.set_api_key("alpaca", "ABCDEFGHIJKLMNOP")
        # Should not raise exception
        manager.remove_service("alpaca")
        assert "alpaca" not in manager._services

    def test_save_to_env_file(self) -> None:
        """Test saving credentials to env file."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.env') as temp_file:
            temp_path = temp_file.name

        try:
            manager = APISecurityManager(env_file=temp_path)
            manager.set_api_key("alpaca", "test_alpaca_key", "test_alpaca_secret")
            manager.set_api_key("polygon", "test_polygon_key")

            manager.save_to_env_file()

            # Read file contents
            with open(temp_path, 'r') as f:
                content = f.read()

            assert "ALPACA_API_KEY=test_alpaca_key" in content
            assert "ALPACA_API_SECRET=test_alpaca_secret" in content
            assert "POLYGON_API_KEY=test_polygon_key" in content
        finally:
            os.unlink(temp_path)

    def test_save_to_env_file_with_existing_content(self) -> None:
        """Test saving credentials to env file with existing non-credential content."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.env') as temp_file:
            temp_file.write("# This is a comment\nOTHER_VAR=value\nANOTHER_VAR=another_value\n")
            temp_path = temp_file.name

        try:
            manager = APISecurityManager(env_file=temp_path)
            manager.set_api_key("alpaca", "test_alpaca_key")

            manager.save_to_env_file()

            # Read file contents
            with open(temp_path, 'r') as f:
                content = f.read()

            assert "# This is a comment" in content
            assert "OTHER_VAR=value" in content
            assert "ANOTHER_VAR=another_value" in content
            assert "ALPACA_API_KEY=test_alpaca_key" in content
        finally:
            os.unlink(temp_path)

    def test_get_service_info(self) -> None:
        """Test getting service information."""
        manager = APISecurityManager()
        manager.set_api_key("alpaca", "test_alpaca_key", "test_alpaca_secret")

        info = manager.get_service_info("alpaca")
        assert info["key"] == "***y_key"  # Should mask the key
        assert info["secret"] == "***t_secret"  # Should mask the secret

    def test_get_service_info_short_key(self) -> None:
        """Test getting service info with short key."""
        manager = APISecurityManager()
        manager.set_api_key("test_service", "key")

        info = manager.get_service_info("test_service")
        assert info["key"] == "****"

    def test_get_service_info_not_found(self) -> None:
        """Test getting service info for nonexistent service."""
        manager = APISecurityManager()
        info = manager.get_service_info("nonexistent_service")
        assert info == {}

    def test_refresh_from_env(self) -> None:
        """Test refreshing credentials from environment."""
        manager = APISecurityManager()
        manager.set_api_key("alpaca", "old_key")

        with patch.dict(os.environ, {"ALPACA_API_KEY": "new_key"}):
            manager.refresh_from_env()
            assert manager._services["alpaca"]["key"] == "new_key"

    @patch.dict(os.environ, {"ALPACA_API_KEY": "env_key"})
    @patch("os.path.exists")
    def test_refresh_from_env_with_file(self, mock_exists: Mock) -> None:
        """Test refreshing credentials from environment and file."""
        mock_exists.return_value = True
        with patch("builtins.open", mock_open(read_data="ALPACA_API_KEY=file_key\n")):
            manager = APISecurityManager()

            # File should override environment
            assert manager._services["alpaca"]["key"] == "file_key"


@pytest.mark.unit
class TestAPIKeyPatterns:
    """Test API key patterns."""

    def test_api_key_patterns_structure(self) -> None:
        """Test that API_KEY_PATTERNS has correct structure."""
        assert isinstance(API_KEY_PATTERNS, dict)
        assert "alpaca" in API_KEY_PATTERNS
        assert "polygon" in API_KEY_PATTERNS
        assert "alpha_vantage" in API_KEY_PATTERNS
        assert "anthropic" in API_KEY_PATTERNS
        assert "openai" in API_KEY_PATTERNS

    def test_alpaca_pattern(self) -> None:
        """Test Alpaca API key pattern."""
        import re
        pattern = API_KEY_PATTERNS["alpaca"]
        assert "key_pattern" in pattern
        assert "secret_pattern" in pattern

        # Test valid key
        valid_key = "ABCDEFGHIJKLMNOP"
        assert re.match(pattern["key_pattern"], valid_key) is not None

        # Test invalid key
        invalid_key = "invalid"
        assert re.match(pattern["key_pattern"], invalid_key) is None

    def test_polygon_pattern(self) -> None:
        """Test Polygon API key pattern."""
        import re
        pattern = API_KEY_PATTERNS["polygon"]
        assert "key_pattern" in pattern

        # Test valid key
        valid_key = "test_polygon_key_12345"
        assert re.match(pattern["key_pattern"], valid_key) is not None

    def test_alpha_vantage_pattern(self) -> None:
        """Test Alpha Vantage API key pattern."""
        import re
        pattern = API_KEY_PATTERNS["alpha_vantage"]
        assert "key_pattern" in pattern

        # Test valid key
        valid_key = "ABCDEFGHIJKLMNOP"
        assert re.match(pattern["key_pattern"], valid_key) is not None

    def test_anthropic_pattern(self) -> None:
        """Test Anthropic API key pattern."""
        import re
        pattern = API_KEY_PATTERNS["anthropic"]
        assert "key_pattern" in pattern

        # Test valid key
        valid_key = "sk-ant-api03-" + "A" * 95
        assert re.match(pattern["key_pattern"], valid_key) is not None

    def test_openai_pattern(self) -> None:
        """Test OpenAI API key pattern."""
        import re
        pattern = API_KEY_PATTERNS["openai"]
        assert "key_pattern" in pattern

        # Test valid key
        valid_key = "sk-" + "A" * 48
        assert re.match(pattern["key_pattern"], valid_key) is not None


@pytest.mark.unit
class TestExceptions:
    """Test security module exceptions."""

    def test_credential_not_found_error(self) -> None:
        """Test CredentialNotFoundError exception."""
        error = CredentialNotFoundError("Test message")
        assert str(error) == "Test message"

    def test_security_configuration_error(self) -> None:
        """Test SecurityConfigurationError exception."""
        error = SecurityConfigurationError("Test message")
        assert str(error) == "Test message"

    def test_invalid_credential_format_error(self) -> None:
        """Test InvalidCredentialFormatError exception."""
        error = InvalidCredentialFormatError("Test message")
        assert str(error) == "Test message"
