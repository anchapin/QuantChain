"""Simple tests for security module to improve coverage."""

import os
from unittest.mock import MagicMock, patch

import pytest

from quantchain.core.security import APISecurityManager


@pytest.mark.unit
class TestAPISecurityManagerSimple:
    """Simple tests for APISecurityManager."""

    def test_init(self):
        """Test initialization."""
        manager = APISecurityManager()
        assert manager is not None

    def test_init_with_env_backend(self):
        """Test initialization with env backend."""
        with patch.dict(os.environ, {"QUANTCHAIN_SECRET_BACKEND": "env"}):
            manager = APISecurityManager()
            assert manager is not None

    def test_validate_service_supported(self):
        """Test validation for supported services."""
        manager = APISecurityManager()

        # Set up credentials for each service first
        manager.set_api_key(
            "alpaca",
            "ABCDEFGHIJKLMNOPQRST",
            "wJalrXUtnFEMIK7MDENGbPxRfiCYEXAMPLEKEY123456789",
        )
        manager.set_api_key("polygon", "AbCdEfGhIjKlMnOpQrStUvWx123456789")
        manager.set_api_key("alpha_vantage", "ABCDEFGHIJKLMNOP")
        manager.set_api_key("anthropic", "sk-ant-" + "a" * 95)
        manager.set_api_key("openai", "sk-test1234567890abcdef")

        # Should validate true for supported services
        assert manager.validate_service("alpaca") is True
        assert manager.validate_service("polygon") is True
        assert manager.validate_service("alpha_vantage") is True
        assert manager.validate_service("anthropic") is True
        assert manager.validate_service("openai") is True

    def test_validate_service_unsupported(self):
        """Test validation for unsupported services."""
        manager = APISecurityManager()

        # Should validate false for unsupported service
        assert manager.validate_service("unsupported_service") is False

    def test_set_and_get_api_key(self):
        """Test setting and getting API key."""
        import os
        from unittest.mock import patch

        # Clear environment variables that might interfere
        with patch.dict(os.environ, {}, clear=True):
            manager = APISecurityManager()

            # Set API key for openai (supported service)
            manager.set_api_key("openai", "sk-test1234567890abcdef")

            # Get API key
            result = manager.get_api_key("openai")
            assert result == "sk-test1234567890abcdef"

    def test_set_and_get_api_key_with_secret(self):
        """Test setting and getting API key with secret."""
        import os
        from unittest.mock import patch

        # Clear environment variables that might interfere
        with patch.dict(os.environ, {}, clear=True):
            manager = APISecurityManager()

            # Set API key with secret for alpaca (supported service with secret)
            manager.set_api_key(
                "alpaca",
                "ABCDEFGHIJKLMNOPQRST",
                "wJalrXUtnFEMIK7MDENGbPxRfiCYEXAMPLEKEY123456789",
            )

            # Get API key
            key = manager.get_api_key("alpaca")
            secret = manager.get_api_secret("alpaca")

            assert key == "ABCDEFGHIJKLMNOPQRST"
            assert secret == "wJalrXUtnFEMIK7MDENGbPxRfiCYEXAMPLEKEY123456789"

    def test_set_api_key_unsupported_service(self):
        """Test setting API key for unsupported service."""
        import os
        from unittest.mock import patch

        # Clear environment variables that might interfere
        with patch.dict(os.environ, {}, clear=True):
            manager = APISecurityManager()

            from quantchain.core.secret_managers.env import SecurityConfigurationError

            with pytest.raises(SecurityConfigurationError):
                manager.set_api_key("unsupported_service", "some_key")

    def test_get_nonexistent_api_key(self):
        """Test getting non-existent API key."""
        manager = APISecurityManager()

        from quantchain.core.security import CredentialNotFoundError

        with pytest.raises(CredentialNotFoundError):
            manager.get_api_key("nonexistent_service")

    def test_get_nonexistent_api_secret(self):
        """Test getting non-existent API secret."""
        manager = APISecurityManager()

        # Should return None for non-existent secret
        result = manager.get_api_secret("nonexistent_service")
        assert result is None

    def test_list_services_empty(self):
        """Test listing services when empty."""
        import os
        from unittest.mock import patch

        # Clear environment variables that might interfere and disable .env file
        with patch.dict(os.environ, {}, clear=True), patch(
            "quantchain.core.secret_managers.env.Path.exists", return_value=False
        ):
            manager = APISecurityManager()

            services = manager.list_services()
            assert services == []

    def test_list_services_after_adding(self):
        """Test listing services after adding."""
        import os
        from unittest.mock import patch

        # Clear environment variables that might interfere
        with patch.dict(os.environ, {}, clear=True):
            manager = APISecurityManager()

            # Add services
            manager.set_api_key("openai", "sk-test1234567890abcdef")
            manager.set_api_key("polygon", "AbCdEfGhIjKlMnOpQrStUvWx123456789")

            services = manager.list_services()
            assert "openai" in services
            assert "polygon" in services

    def test_remove_service(self):
        """Test removing a service."""
        import os
        from unittest.mock import patch

        # Clear environment variables that might interfere
        with patch.dict(os.environ, {}, clear=True):
            manager = APISecurityManager()

            # Add and then remove service
            manager.set_api_key("openai", "sk-test1234567890abcdef")
            manager.remove_service("openai")

            # Should be removed
            from quantchain.core.security import CredentialNotFoundError

            with pytest.raises(CredentialNotFoundError):
                manager.get_api_key("openai")

    def test_remove_nonexistent_service(self):
        """Test removing non-existent service."""
        manager = APISecurityManager()

        # Should not raise
        manager.remove_service("nonexistent_service")

    def test_get_service_credentials(self):
        """Test getting service credentials."""
        import os
        from unittest.mock import patch

        # Clear environment variables that might interfere
        with patch.dict(os.environ, {}, clear=True):
            manager = APISecurityManager()

            # Set credentials
            manager.set_api_key(
                "alpaca",
                "ABCDEFGHIJKLMNOPQRST",
                "wJalrXUtnFEMIK7MDENGbPxRfiCYEXAMPLEKEY123456789",
            )

            # Get credentials
            credentials = manager.get_service_credentials("alpaca")
            assert credentials["key"] == "ABCDEFGHIJKLMNOPQRST"
            assert (
                credentials["secret"]
                == "wJalrXUtnFEMIK7MDENGbPxRfiCYEXAMPLEKEY123456789"
            )

    def test_validate_credentials_alpaca(self):
        """Test credential validation for Alpaca."""
        manager = APISecurityManager()

        # Valid Alpaca credentials
        valid_key = "ABCDEFGHIJKLMNOPQRST"
        valid_secret = "wJalrXUtnFEMIK7MDENGbPxRfiCYEXAMPLEKEY123456789"

        result = manager.validate_credentials("alpaca", valid_key, valid_secret)
        assert result is True

    def test_validate_credentials_alpaca_invalid(self):
        """Test invalid credential validation for Alpaca."""
        manager = APISecurityManager()

        # Invalid Alpaca key
        invalid_key = "invalid"
        invalid_secret = "invalid"

        result = manager.validate_credentials("alpaca", invalid_key, invalid_secret)
        assert result is False

    def test_validate_credentials_polygon(self):
        """Test credential validation for Polygon."""
        manager = APISecurityManager()

        # Valid Polygon key
        valid_key = "abcdefghijklmnopqrstuvwxy123456"

        result = manager.validate_credentials("polygon", valid_key)
        assert result is True

    def test_validate_credentials_polygon_invalid(self):
        """Test invalid credential validation for Polygon."""
        manager = APISecurityManager()

        # Invalid Polygon key
        invalid_key = "x"

        result = manager.validate_credentials("polygon", invalid_key)
        assert result is False

    def test_validate_credentials_unsupported(self):
        """Test credential validation for unsupported service."""
        manager = APISecurityManager()

        # Should return False for unsupported service
        result = manager.validate_credentials("unsupported", "key", "secret")
        assert result is False
