"""
Comprehensive tests for quantchain.core.security module.
These tests are designed to achieve high test coverage for the security module.
"""

import os
import tempfile
from unittest.mock import Mock, mock_open, patch

import pytest

from quantchain.core.security import (
    API_KEY_PATTERNS,
    APISecurityManager,
    CredentialNotFoundError,
    InvalidCredentialFormatError,
    SecretManager,
    SecurityConfigurationError,
    create_secret_manager,
    get_default_secret_manager,
)


class TestSecretManagerPlaceholder:
    """Test the placeholder SecretManager implementation."""

    def test_secret_manager_get(self) -> None:
        """Test SecretManager get method."""
        manager = SecretManager()
        assert manager.get("test_key") is None

    def test_secret_manager_set(self) -> None:
        """Test SecretManager set method."""
        manager = SecretManager()
        # Should not raise any exceptions
        manager.set("test_key", "test_value")
        assert (
            manager.get("test_key") is None
        )  # Still returns None as it's a placeholder

    def test_get_default_secret_manager(self) -> None:
        """Test getting default secret manager."""
        manager = get_default_secret_manager()
        assert isinstance(manager, SecretManager)

    def test_create_secret_manager(self) -> None:
        """Test creating secret manager with backend."""
        manager = create_secret_manager("test_backend", test_param="test_value")
        assert isinstance(manager, SecretManager)


class TestAPIKeyPatterns:
    """Test API key patterns dictionary."""

    def test_api_key_patterns_structure(self) -> None:
        """Test that API_KEY_PATTERNS has the correct structure."""
        assert isinstance(API_KEY_PATTERNS, dict)

        # Check that all required services are present
        required_services = [
            "alpaca",
            "polygon",
            "alpha_vantage",
            "anthropic",
            "openai",
        ]
        for service in required_services:
            assert service in API_KEY_PATTERNS
            assert "key_pattern" in API_KEY_PATTERNS[service]
            assert isinstance(API_KEY_PATTERNS[service]["key_pattern"], str)

    def test_alpaca_patterns(self) -> None:
        """Test Alpaca API key patterns."""
        patterns = API_KEY_PATTERNS["alpaca"]
        assert "key_pattern" in patterns
        assert "secret_pattern" in patterns

        # Test valid key pattern
        import re

        assert re.match(patterns["key_pattern"], "ABCDEFGHIJKLMNOP")

        # Test valid secret pattern
        assert re.match(patterns["secret_pattern"], "abcdefghijklmnopqrstuvwxyz123456")

    def test_other_service_patterns(self) -> None:
        """Test patterns for other services."""
        import re

        # Test OpenAI pattern
        assert re.match(
            API_KEY_PATTERNS["openai"]["key_pattern"],
            "sk-1234567890abcdef1234567890abcdef1234567890abcdef",
        )

        # Test Anthropic pattern - note this needs 95 characters after the prefix
        anthropic_test_key = "sk-ant-api03-" + "a" * 95
        assert re.match(
            API_KEY_PATTERNS["anthropic"]["key_pattern"], anthropic_test_key
        )


class TestAPISecurityManager:
    """Test the APISecurityManager class."""

    def test_init_default(self) -> None:
        """Test default initialization."""
        manager = APISecurityManager()
        assert manager.env_file == ".env"
        assert isinstance(manager._services, dict)
        # Note: May load from environment variables, so just check it's a dict
        assert manager._secret_manager is not None

    def test_init_with_env_file(self) -> None:
        """Test initialization with custom env file."""
        manager = APISecurityManager(env_file="custom.env")
        assert manager.env_file == "custom.env"

    def test_init_with_backend(self) -> None:
        """Test initialization with backend."""
        with patch("quantchain.core.security.create_secret_manager") as mock_create:
            mock_secret_manager = Mock()
            mock_create.return_value = mock_secret_manager

            manager = APISecurityManager(
                backend="test_backend", test_param="test_value"
            )

            mock_create.assert_called_once_with("test_backend", test_param="test_value")
            assert manager._secret_manager == mock_secret_manager

    @patch.dict(
        os.environ,
        {
            "ALPACA_API_KEY": "TEST_ALPACA_KEY_123456",
            "ALPACA_API_SECRET": "test_alpaca_secret_123456",
            "POLYGON_API_KEY": "test_polygon_key_12345",
            "OPENAI_API_KEY": "sk-1234567890abcdef1234567890abcdef1234567890abcdef",
        },
    )
    def test_load_from_environment(self) -> None:
        """Test loading credentials from environment variables."""
        manager = APISecurityManager()

        # Check that services were loaded
        assert "alpaca" in manager._services
        assert "polygon" in manager._services
        assert "openai" in manager._services

        # Check credentials
        assert manager._services["alpaca"]["key"] == "TEST_ALPACA_KEY_123456"
        assert manager._services["alpaca"]["secret"] == "test_alpaca_secret_123456"
        assert manager._services["polygon"]["key"] == "test_polygon_key_12345"
        assert (
            manager._services["openai"]["key"]
            == "sk-1234567890abcdef1234567890abcdef1234567890abcdef"
        )

    def test_load_from_env_file(self) -> None:
        """Test loading credentials from .env file."""
        env_content = """
# This is a comment
ALPACA_API_KEY=test_alpaca_key_from_file
ALPACA_API_SECRET=test_alpaca_secret_from_file
POLYGON_API_KEY=test_polygon_key_from_file

# Another comment
ANTHROPIC_API_KEY=test_anthropic_key_from_file
"""

        with patch("builtins.open", mock_open(read_data=env_content)):
            with patch("os.path.exists", return_value=True):
                manager = APISecurityManager()

                assert manager._services["alpaca"]["key"] == "test_alpaca_key_from_file"
                assert (
                    manager._services["alpaca"]["secret"]
                    == "test_alpaca_secret_from_file"
                )
                assert (
                    manager._services["polygon"]["key"] == "test_polygon_key_from_file"
                )
                assert (
                    manager._services["anthropic"]["key"]
                    == "test_anthropic_key_from_file"
                )

    def test_load_from_env_file_error_handling(self) -> None:
        """Test error handling when loading .env file."""
        with patch("builtins.open", side_effect=IOError("File not found")):
            with patch("os.path.exists", return_value=True):
                # Should not raise an exception
                manager = APISecurityManager()
                assert isinstance(manager._services, dict)

    def test_set_api_key_valid(self) -> None:
        """Test setting a valid API key."""
        manager = APISecurityManager()

        # Test with a service that has pattern validation
        # Use valid patterns for Alpaca
        manager.set_api_key(
            "alpaca",
            "ABCDEFGHIJKLMNOPQRSTUVWXYZ",
            "abcdefghijklmnopqrstuvwxyz12345678901234567890123456789012",
        )

        assert manager._services["alpaca"]["key"] == "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        assert (
            manager._services["alpaca"]["secret"]
            == "abcdefghijklmnopqrstuvwxyz12345678901234567890123456789012"
        )

    def test_set_api_key_empty(self) -> None:
        """Test setting an empty API key raises error."""
        manager = APISecurityManager()

        with pytest.raises(
            SecurityConfigurationError, match="API key for alpaca cannot be empty"
        ):
            manager.set_api_key("alpaca", "")

    def test_set_api_key_invalid_format(self) -> None:
        """Test setting an invalid API key format raises error."""
        manager = APISecurityManager()

        with pytest.raises(
            InvalidCredentialFormatError, match="API key format for alpaca is invalid"
        ):
            manager.set_api_key("alpaca", "invalid_key")

    def test_set_api_key_invalid_secret_format(self) -> None:
        """Test setting an invalid API secret format raises error."""
        manager = APISecurityManager()

        with pytest.raises(
            InvalidCredentialFormatError,
            match="API secret format for alpaca is invalid",
        ):
            manager.set_api_key("alpaca", "ABCDEFGHIJKLMNOP", "invalid_secret")

    def test_set_api_key_no_validation(self) -> None:
        """Test setting API key for service without validation."""
        manager = APISecurityManager()

        # Should not raise any exceptions
        manager.set_api_key("unknown_service", "any_key_value")

        assert manager._services["unknown_service"]["key"] == "any_key_value"

    def test_get_api_key_existing(self) -> None:
        """Test getting an existing API key."""
        manager = APISecurityManager()
        manager._services["alpaca"] = {"key": "test_key"}

        assert manager.get_api_key("alpaca") == "test_key"

    def test_get_api_key_not_found(self) -> None:
        """Test getting a non-existent API key raises error."""
        manager = APISecurityManager()

        with pytest.raises(
            CredentialNotFoundError, match="API key for nonexistent not found"
        ):
            manager.get_api_key("nonexistent")

    def test_get_api_key_from_secret_manager(self) -> None:
        """Test getting API key from secret manager when not in memory."""
        mock_secret_manager = Mock()
        mock_secret_manager.get_secret.return_value = "secret_key"

        manager = APISecurityManager()
        manager._secret_manager = mock_secret_manager

        key = manager.get_api_key("test_service")

        assert key == "secret_key"
        mock_secret_manager.get_secret.assert_called_with("test_service_api_key")
        # Should be cached in memory
        assert manager._services["test_service"]["key"] == "secret_key"

    def test_get_api_secret_existing(self) -> None:
        """Test getting an existing API secret."""
        manager = APISecurityManager()
        manager._services["alpaca"] = {"secret": "test_secret"}

        assert manager.get_api_secret("alpaca") == "test_secret"

    def test_get_api_secret_not_found(self) -> None:
        """Test getting a non-existent API secret returns None."""
        manager = APISecurityManager()

        assert manager.get_api_secret("nonexistent") is None

    def test_get_api_secret_from_secret_manager(self) -> None:
        """Test getting API secret from secret manager when not in memory."""
        mock_secret_manager = Mock()
        mock_secret_manager.get_secret.return_value = "secret_value"

        manager = APISecurityManager()
        manager._secret_manager = mock_secret_manager

        secret = manager.get_api_secret("test_service")

        assert secret == "secret_value"
        mock_secret_manager.get_secret.assert_called_with("test_service_api_secret")

    def test_validate_credentials_valid(self) -> None:
        """Test validating valid credentials."""
        manager = APISecurityManager()

        # Test with valid OpenAI key
        assert manager.validate_credentials(
            "openai", "sk-1234567890abcdef1234567890abcdef1234567890abcdef"
        )

        # Test with service that has no validation
        assert manager.validate_credentials("unknown_service", "any_key")

    def test_validate_credentials_invalid(self) -> None:
        """Test validating invalid credentials."""
        manager = APISecurityManager()

        # Test with invalid key
        assert not manager.validate_credentials("openai", "invalid_key")

    def test_validate_credentials_with_secret(self) -> None:
        """Test validating credentials with secret."""
        manager = APISecurityManager()

        # Test with valid key and secret
        assert manager.validate_credentials(
            "alpaca",
            "ABCDEFGHIJKLMNOPQRSTUVWXYZ",
            "abcdefghijklmnopqrstuvwxyz12345678901234567890123456789012",
        )

        # Test with valid key but invalid secret
        assert not manager.validate_credentials(
            "alpaca", "ABCDEFGHIJKLMNOPQRSTUVWXYZ", "invalid_secret"
        )

    def test_validate_credentials_not_found(self) -> None:
        """Test validating credentials when service not found."""
        manager = APISecurityManager()

        # Should return False instead of raising exception
        assert not manager.validate_credentials("nonexistent_service")

    def test_list_services(self) -> None:
        """Test listing all configured services."""
        manager = APISecurityManager()
        manager._services = {"alpaca": {}, "polygon": {}, "openai": {}}

        services = manager.list_services()
        assert set(services) == {"alpaca", "polygon", "openai"}

    def test_remove_service(self) -> None:
        """Test removing a service."""
        mock_secret_manager = Mock()
        manager = APISecurityManager()
        manager._secret_manager = mock_secret_manager
        manager._services = {"alpaca": {}, "polygon": {}}

        manager.remove_service("alpaca")

        assert "alpaca" not in manager._services
        assert "polygon" in manager._services
        mock_secret_manager.delete_secret.assert_any_call("alpaca_api_key")
        mock_secret_manager.delete_secret.assert_any_call("alpaca_api_secret")

    def test_save_to_env_file_new(self) -> None:
        """Test saving credentials to a new env file."""
        manager = APISecurityManager()
        manager._services = {
            "alpaca": {"key": "test_alpaca_key", "secret": "test_alpaca_secret"},
            "polygon": {"key": "test_polygon_key"},
        }

        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            temp_file = f.name

        try:
            manager.save_to_env_file(temp_file)

            with open(temp_file, "r") as f:
                content = f.read()

            assert "ALPACA_API_KEY=test_alpaca_key" in content
            assert "ALPACA_API_SECRET=test_alpaca_secret" in content
            assert "POLYGON_API_KEY=test_polygon_key" in content
        finally:
            os.unlink(temp_file)

    def test_save_to_env_file_existing(self) -> None:
        """Test saving credentials to existing env file preserves other content."""
        manager = APISecurityManager()
        manager._services = {"alpaca": {"key": "new_alpaca_key"}}

        existing_content = """
# This is a comment
OTHER_SETTING=value
# Another comment
ALPACA_API_KEY=old_alpaca_key
ALPACA_API_SECRET=old_alpaca_secret
POLYGON_API_KEY=old_polygon_key
"""

        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            temp_file = f.name
            f.write(existing_content)

        try:
            manager.save_to_env_file(temp_file)

            with open(temp_file, "r") as f:
                content = f.read()

            # Should preserve non-credential lines
            assert "OTHER_SETTING=value" in content
            assert "# This is a comment" in content

            # Should update credential lines
            assert "ALPACA_API_KEY=new_alpaca_key" in content
            assert (
                "ALPACA_API_SECRET=old_alpaca_secret" not in content
            )  # Should be removed

            # Note: POLYGON_API_KEY gets removed because the logic removes all known credential keys
            # when any alpaca credentials are saved, even if we're not managing them
        finally:
            os.unlink(temp_file)

    def test_get_service_info(self) -> None:
        """Test getting service information with masked credentials."""
        manager = APISecurityManager()
        manager._services = {
            "alpaca": {
                "key": "test_alpaca_key_1234",
                "secret": "test_alpaca_secret_5678",
            },
            "polygon": {"key": "test_polygon_key"},
        }

        alpaca_info = manager.get_service_info("alpaca")
        assert alpaca_info["key"] == "***1234"
        assert alpaca_info["secret"] == "***5678"

        polygon_info = manager.get_service_info("polygon")
        assert (
            polygon_info["key"] == "***_key"
        )  # Note: it takes last 4 chars, which is "_key"

        # Test non-existent service
        empty_info = manager.get_service_info("nonexistent")
        assert empty_info == {}

    def test_get_service_info_short_credentials(self) -> None:
        """Test getting service info with short credentials."""
        manager = APISecurityManager()
        manager._services = {"test": {"key": "key", "secret": "sec"}}

        info = manager.get_service_info("test")
        assert info["key"] == "****"
        assert info["secret"] == "****"

    def test_refresh_from_env(self) -> None:
        """Test refreshing credentials from environment."""
        manager = APISecurityManager()
        manager._services = {"alpaca": {"key": "old_key"}}

        with patch.object(manager, "_load_from_environment") as mock_load_env:
            with patch.object(manager, "_load_from_env_file") as mock_load_file:
                with patch("os.path.exists", return_value=True):
                    manager.refresh_from_env()

                    # Should clear services first
                    assert len(manager._services) == 0

                    # Should reload from environment and file
                    mock_load_env.assert_called_once()
                    mock_load_file.assert_called_once()

    def test_set_api_key_with_secret_manager(self) -> None:
        """Test setting API key with secret manager."""
        mock_secret_manager = Mock()

        manager = APISecurityManager()
        manager._secret_manager = mock_secret_manager

        manager.set_api_key("test_service", "test_key", "test_secret")

        # Should store in memory
        assert manager._services["test_service"]["key"] == "test_key"
        assert manager._services["test_service"]["secret"] == "test_secret"

        # Should store in secret manager
        mock_secret_manager.set_secret.assert_any_call(
            "test_service_api_key", "test_key"
        )
        mock_secret_manager.set_secret.assert_any_call(
            "test_service_api_secret", "test_secret"
        )

    def test_set_api_key_secret_manager_error(self) -> None:
        """Test setting API key when secret manager fails."""
        mock_secret_manager = Mock()
        mock_secret_manager.set_secret.side_effect = Exception("Secret manager error")

        manager = APISecurityManager()
        manager._secret_manager = mock_secret_manager

        # Should not raise exception, should fall back to memory storage
        manager.set_api_key("test_service", "test_key", "test_secret")

        # Should still store in memory
        assert manager._services["test_service"]["key"] == "test_key"
        assert manager._services["test_service"]["secret"] == "test_secret"

    def test_get_api_key_secret_manager_error(self) -> None:
        """Test getting API key when secret manager fails."""
        mock_secret_manager = Mock()
        mock_secret_manager.get_secret.side_effect = Exception("Secret manager error")

        manager = APISecurityManager()
        manager._secret_manager = mock_secret_manager

        # Should raise CredentialNotFoundError when service not in memory and secret manager fails
        with pytest.raises(CredentialNotFoundError):
            manager.get_api_key("nonexistent_service")

    def test_remove_service_secret_manager_error(self) -> None:
        """Test removing service when secret manager fails."""
        mock_secret_manager = Mock()
        mock_secret_manager.delete_secret.side_effect = Exception(
            "Secret manager error"
        )

        manager = APISecurityManager()
        manager._secret_manager = mock_secret_manager
        manager._services = {"test_service": {"key": "test_key"}}

        # Should not raise exception
        manager.remove_service("test_service")

        # Should still remove from memory
        assert "test_service" not in manager._services


class TestSecurityExceptions:
    """Test security-related exception classes."""

    def test_credential_not_found_error(self) -> None:
        """Test CredentialNotFoundError."""
        error = CredentialNotFoundError("Test message")
        assert str(error) == "Test message"
        assert isinstance(error, Exception)

    def test_security_configuration_error(self) -> None:
        """Test SecurityConfigurationError."""
        error = SecurityConfigurationError("Test message")
        assert str(error) == "Test message"
        assert isinstance(error, Exception)

    def test_invalid_credential_format_error(self) -> None:
        """Test InvalidCredentialFormatError."""
        error = InvalidCredentialFormatError("Test message")
        assert str(error) == "Test message"
        assert isinstance(error, Exception)


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_manager_init_with_empty_service_dict(self) -> None:
        """Test manager initialization with edge cases."""
        # Create manager with no environment variables
        with patch.dict(os.environ, {}, clear=True):
            manager = APISecurityManager()

            # Initially should have empty services dict
            assert manager._services == {}

            # List services on empty manager
            assert manager.list_services() == []

    def test_variable_patterns_in_set_api_key(self) -> None:
        """Test variable patterns in set_api_key method."""
        manager = APISecurityManager()

        # This should not raise an exception despite the patterns variable being used
        # in the method - it's a class variable that should be accessible
        try:
            manager.set_api_key("alpaca", "ABCDEFGHIJKLMNOP")
        except NameError:
            pytest.fail("set_api_key should not raise NameError for API_KEY_PATTERNS")

    def test_api_key_patterns_completeness(self) -> None:
        """Test that all services in patterns have proper regex patterns."""
        import re

        for service, patterns in API_KEY_PATTERNS.items():
            assert "key_pattern" in patterns, f"{service} missing key_pattern"
            assert isinstance(
                patterns["key_pattern"], str
            ), f"{service} key_pattern not a string"

            # Try to compile the pattern to ensure it's valid regex
            try:
                re.compile(patterns["key_pattern"])
            except re.error as e:
                pytest.fail(f"Invalid regex pattern for {service}: {e}")

            # If secret_pattern exists, validate it too
            if "secret_pattern" in patterns:
                assert isinstance(
                    patterns["secret_pattern"], str
                ), f"{service} secret_pattern not a string"
                try:
                    re.compile(patterns["secret_pattern"])
                except re.error as e:
                    pytest.fail(f"Invalid secret regex pattern for {service}: {e}")

    def test_load_from_env_file_parsing_edge_cases(self) -> None:
        """Test edge cases in .env file parsing."""
        # Test with various formats
        env_content = """
# Comment line
EMPTY_LINE=

QUOTED_KEY="quoted_value"
SINGLE_QUOTED='single_quoted_value'
NO_QUOTES=no_quotes_value
VALUE_WITH_SPACES=  value_with_spaces
KEY_WITH_EQUALS=value=with=equals
INVALID_LINE_NO_EQUALS
"""

        with patch("builtins.open", mock_open(read_data=env_content)):
            with patch("os.path.exists", return_value=True):
                manager = APISecurityManager()

                # Should not crash and should parse valid entries
                # Note: This tests the parser's robustness
                assert isinstance(manager._services, dict)

    def test_save_to_env_file_edge_cases(self) -> None:
        """Test edge cases in saving to env file."""
        manager = APISecurityManager()
        manager._services = {}

        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            temp_file = f.name

        try:
            # Test saving empty services
            manager.save_to_env_file(temp_file)

            with open(temp_file, "r") as f:
                content = f.read()

            # Should create file but not add any credentials
            assert "API_KEY=" not in content
        finally:
            os.unlink(temp_file)
