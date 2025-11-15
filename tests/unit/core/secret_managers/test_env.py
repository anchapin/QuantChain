"""Tests for environment variable secret manager implementation."""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from quantchain.core.secret_managers.env import (
    EnvSecretManager,
    InvalidCredentialFormatError,
    SecurityConfigurationError,
)


@pytest.fixture


def temp_env_file():
    """Create a temporary .env file for testing."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as f:
        f.write("# Test environment variables\n")
        f.write('ALPACA_API_KEY="AATEST123456789012345"\n')
        f.write(
            'ALPACA_API_SECRET="testsecret12345678901234567890123456789012345678"\n'
        )
        f.write('POLYGON_API_KEY="test_polygon_key_12345"\n')
        f.write("OPENAI_API_KEY=sk-test12345678901234567890\n")
        temp_path = f.name

    yield temp_path

    # Cleanup
    if os.path.exists(temp_path):
        os.unlink(temp_path)


@pytest.fixture


def env_manager(temp_env_file):
    """Create an EnvSecretManager instance with temp file."""
    with patch.dict(
        os.environ, {}, clear=True
    ):  # Clear env vars to avoid loading system variables
        manager = EnvSecretManager(
            env_file=temp_env_file, allow_production_warning=False
        )
        yield manager


@pytest.mark.unit


class TestEnvSecretManager:
    """Test environment variable secret manager."""



def test_init_with_env_file(self, temp_env_file):
        """Test initialization with env file."""
        manager = EnvSecretManager(
            env_file=temp_env_file, allow_production_warning=False
        )
        assert manager.env_file == Path(temp_env_file)
        assert "alpaca" in manager._credentials
        assert "polygon" in manager._credentials
        assert "openai" in manager._credentials



def test_init_without_env_file(self):
        """Test initialization without existing env file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            non_existent = Path(tmpdir) / "non_existent.env"
            with patch.dict(
                os.environ, {}, clear=True
            ):  # Clear env vars to avoid loading system variables
                manager = EnvSecretManager(
                    env_file=str(non_existent), allow_production_warning=False
                )
                assert manager.env_file == non_existent
                assert not manager._credentials



def test_load_credentials_from_env(self):
        """Test loading credentials from environment variables."""
        with patch.dict(
            os.environ,
            {
                "ALPHA_VANTAGE_API_KEY": "TEST1234567890ABCD",
                "ANTHROPIC_API_KEY": "sk-ant-test123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890",
            },
        ):
            manager = EnvSecretManager(allow_production_warning=False)
            assert "alpha_vantage" in manager._credentials
            assert "anthropic" in manager._credentials
            assert manager._credentials["alpha_vantage"]["key"] == "TEST1234567890ABCD"
            assert manager._credentials["anthropic"]["key"].startswith("sk-ant-")



def test_get_secret_existing(self, env_manager):
        """Test getting an existing secret."""
        assert env_manager.get_secret("ALPACA_API_KEY") == "AATEST123456789012345"
        assert (
            env_manager.get_secret("ALPACA_API_SECRET")
            == "testsecret12345678901234567890123456789012345678"
        )
        assert env_manager.get_secret("POLYGON_API_KEY") == "test_polygon_key_12345"



def test_get_secret_nonexistent(self, env_manager):
        """Test getting a non-existent secret."""
        assert env_manager.get_secret("NONEXISTENT_API_KEY") is None
        assert env_manager.get_secret("MISSING_SECRET") is None



def test_get_service_credentials(self, env_manager):
        """Test getting all credentials for a service."""
        alpaca_creds = env_manager.get_service_credentials("alpaca")
        assert alpaca_creds["key"] == "AATEST123456789012345"
        assert (
            alpaca_creds["secret"] == "testsecret12345678901234567890123456789012345678"
        )

        polygon_creds = env_manager.get_service_credentials("polygon")
        assert polygon_creds["key"] == "test_polygon_key_12345"
        assert "secret" not in polygon_creds



def test_validate_service_existing(self, env_manager):
        """Test validating an existing service."""
        assert env_manager.validate_service("alpaca") is True
        assert env_manager.validate_service("polygon") is True
        assert env_manager.validate_service("openai") is True



def test_validate_service_nonexistent(self, env_manager):
        """Test validating a non-existent service."""
        assert env_manager.validate_service("nonexistent") is False



def test_validate_credentials_alpaca(self, env_manager):
        """Test validating Alpaca credentials."""
        assert env_manager.validate_credentials("alpaca") is True

        # Test invalid format
        assert (
            env_manager.validate_credentials("alpaca", "invalid_key", "invalid_secret")
            is False
        )
        assert env_manager.validate_credentials("alpaca", "short") is False



def test_validate_credentials_polygon(self, env_manager):
        """Test validating Polygon credentials."""
        assert env_manager.validate_credentials("polygon") is True

        # Polygon doesn't require secret
        assert (
            env_manager.validate_credentials("polygon", "test_polygon_key_12345")
            is True
        )



def test_validate_credentials_unsupported_service(self, env_manager):
        """Test validating credentials for unsupported service."""
        assert env_manager.validate_credentials("unsupported_service") is False



def test_set_api_key(self, env_manager):
        """Test setting API key for a service."""
        # Alpaca key: starts with 'A', 17-21 chars total (A + 16-20 chars)
        # Secret: 40-50 chars of base64-like
        env_manager.set_api_key(
            "alpaca",
            "ANEWKEY12345678901",
            "newsecret1234567890123456789012345678901234567890",
        )

        creds = env_manager.get_service_credentials("alpaca")
        assert creds["key"] == "ANEWKEY12345678901"
        assert creds["secret"] == "newsecret1234567890123456789012345678901234567890"



def test_set_api_key_invalid_format(self, env_manager):
        """Test setting API key with invalid format."""
        with pytest.raises(InvalidCredentialFormatError):
            env_manager.set_api_key("alpaca", "invalid", "invalid")



def test_set_api_key_unsupported_service(self, env_manager):
        """Test setting API key for unsupported service."""
        with pytest.raises(SecurityConfigurationError):
            env_manager.set_api_key("unsupported", "key", "secret")



def test_remove_service(self, env_manager):
        """Test removing service credentials."""
        assert env_manager.validate_service("alpaca") is True
        env_manager.remove_service("alpaca")
        assert env_manager.validate_service("alpaca") is False



def test_save_to_env_file(self, env_manager):
        """Test saving credentials to env file."""
        # Set new credentials - Alpha Vantage needs exactly 16 chars
        env_manager.set_api_key("alpha_vantage", "TEST1234567890AB")

        # Save to file
        env_manager.save_to_env_file()

        # Read file content
        with open(env_manager.env_file, "r") as f:
            content = f.read()

        assert "ALPHA_VANTAGE_API_KEY" in content
        assert "TEST1234567890AB" in content



def test_save_to_env_file_new_file(self, env_manager):
        """Test saving to a new env file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as f:
            temp_path = f.name

        # Remove the file to test creating new one
        os.unlink(temp_path)

        env_manager.env_file = Path(temp_path)
        env_manager.save_to_env_file()

        assert os.path.exists(temp_path)

        # Cleanup
        if os.path.exists(temp_path):
            os.unlink(temp_path)



def test_load_credentials_invalid_env_file(self):
        """Test loading from invalid env file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as f:
            f.write("invalid line without equals\n")
            f.write("VALID_KEY=value\n")
            temp_path = f.name

        try:
            with patch.dict(
                os.environ, {}, clear=True
            ):  # Clear env vars to avoid loading system variables
                manager = EnvSecretManager(
                    env_file=temp_path, allow_production_warning=False
                )
                # Should load valid lines despite invalid ones
                assert (
                    not manager._credentials
                )  # No valid service patterns in this test
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)



def test_production_warning(self):
        """Test production warning is shown by default."""
        with patch("quantchain.core.secret_managers.env.logger") as mock_logger:
            EnvSecretManager()
            mock_logger.warning.assert_called_once_with(
                "Using EnvSecretManager - FOR DEVELOPMENT ONLY. "
                "DO NOT use in production environments."
            )



def test_no_production_warning(self):
        """Test production warning can be disabled."""
        with patch("quantchain.core.secret_managers.env.logger") as mock_logger:
            EnvSecretManager(allow_production_warning=False)
            mock_logger.warning.assert_not_called()
