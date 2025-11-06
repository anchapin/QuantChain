"""Tests for the Security module."""

import pytest
from pathlib import Path

from quantchain.core.security import (
    APISecurityManager,
    CredentialNotFoundError,
    InvalidCredentialFormatError,
)


@pytest.mark.unit
class TestAPISecurityManager:
    """Test the API Security Manager."""

    def test_init_with_default_env_file(self):
        """Test initialization with default .env file."""
        manager = APISecurityManager()
        assert manager.env_file == Path(".env")

    def test_init_with_custom_env_file(self):
        """Test initialization with custom env file path."""
        manager = APISecurityManager("custom.env")
        assert manager.env_file == Path("custom.env")

    def test_set_and_get_api_key(self):
        """Test setting and retrieving an API key."""
        manager = APISecurityManager()
        test_key = "sk-test1234567890abcdef"

        manager.set_api_key("openai", test_key)
        retrieved_key = manager.get_api_key("openai")

        assert retrieved_key == test_key

    def test_get_nonexistent_api_key_raises_error(self):
        """Test that getting a non-existent API key raises CredentialNotFoundError."""
        manager = APISecurityManager()

        with pytest.raises(CredentialNotFoundError):
            manager.get_api_key("nonexistent")

    def test_set_and_get_api_secret(self):
        """Test setting and retrieving an API secret."""
        manager = APISecurityManager()
        test_key = "AAAAAAAAAAAAAAAAAAAAA"  # 21 chars
        test_secret = "wJalrXUtnFEMIK7MDENGbPxRfiCYEXAMPLEKEY123456789"

        manager.set_api_key("alpaca", test_key, test_secret)
        retrieved_secret = manager.get_api_secret("alpaca")

        assert retrieved_secret == test_secret

    def test_get_api_secret_returns_none_when_not_set(self):
        """Test that get_api_secret returns None when no secret is set."""
        manager = APISecurityManager()
        test_key = "sk-test1234567890abcdef"

        manager.set_api_key("openai", test_key)  # No secret
        retrieved_secret = manager.get_api_secret("openai")

        assert retrieved_secret is None

    def test_validate_alpaca_credentials_valid(self):
        """Test validation of valid Alpaca credentials."""
        manager = APISecurityManager()
        valid_key = "AAAAAAAAAAAAAAAAAAAAA"  # 21 chars
        valid_secret = "wJalrXUtnFEMIK7MDENGbPxRfiCYEXAMPLEKEY123456789"

        manager.set_api_key("alpaca", valid_key, valid_secret)
        assert manager.validate_credentials("alpaca") is True

    def test_validate_alpaca_credentials_invalid_key(self):
        """Test validation of invalid Alpaca API key format."""
        manager = APISecurityManager()
        invalid_key = "invalid_key"

        with pytest.raises(InvalidCredentialFormatError):
            manager.set_api_key("alpaca", invalid_key)

    def test_validate_openai_credentials_valid(self):
        """Test validation of valid OpenAI credentials."""
        manager = APISecurityManager()
        valid_key = "sk-test1234567890abcdef"

        manager.set_api_key("openai", valid_key)
        assert manager.validate_credentials("openai") is True

    def test_validate_openai_credentials_invalid_key(self):
        """Test validation of invalid OpenAI API key format."""
        manager = APISecurityManager()
        invalid_key = "invalid_key"

        with pytest.raises(InvalidCredentialFormatError):
            manager.set_api_key("openai", invalid_key)

    def test_list_services_empty(self):
        """Test listing services when none are configured."""
        manager = APISecurityManager()
        services = manager.list_services()

        assert services == []

    def test_list_services_after_setting_keys(self):
        """Test listing services after setting some API keys."""
        manager = APISecurityManager()

        manager.set_api_key("openai", "sk-test1234567890abcdef")
        manager.set_api_key(
            "alpaca",
            "AAAAAAAAAAAAAAAAAAAAA",
            "wJalrXUtnFEMIK7MDENGbPxRfiCYEXAMPLEKEY123456789",
        )

        services = manager.list_services()

        assert set(services) == {"openai", "alpaca"}

    def test_remove_service(self):
        """Test removing a service's credentials."""
        manager = APISecurityManager()

        manager.set_api_key("openai", "sk-test1234567890abcdef")
        assert "openai" in manager.list_services()

        manager.remove_service("openai")
        assert "openai" not in manager.list_services()

    def test_remove_nonexistent_service_no_error(self):
        """Test that removing a non-existent service doesn't raise an error."""
        manager = APISecurityManager()

        # Should not raise an error
        manager.remove_service("nonexistent")

    @pytest.mark.skip(reason="Production backends not yet implemented")
    def test_vault_backend_initialization(self):
        """Test initialization with Vault backend."""
        # TODO: Implement test
        pass

    @pytest.mark.skip(reason="Production backends not yet implemented")
    def test_aws_secrets_manager_backend(self):
        """Test initialization with AWS Secrets Manager backend."""
        # TODO: Implement test
        pass
