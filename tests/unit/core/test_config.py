"""Tests for QuantChain configuration system."""

import tempfile
import os
import unittest.mock

import pytest

from quantchain.core.config import QuantChainConfig, LogLevel


@pytest.mark.unit
class TestQuantChainConfig:
    """Test suite for QuantChainConfig."""

    def test_init_with_defaults(self) -> None:
        """Test initialization with default configuration."""
        config = QuantChainConfig()

        # Check default values exist
        assert config.llm_provider == "openai"
        assert config.llm_model == "gpt-4"
        assert config.temperature == 0.7
        assert config.max_tokens == 2048
        assert config.enable_rag is False
        assert config.enable_reflection is False
        assert config.max_retries == 3
        assert config.retry_delay == 1.0

    def test_init_with_custom_values(self) -> None:
        """Test initialization with custom values."""
        config = QuantChainConfig(
            llm_provider="ollama",
            llm_model="llama2:7b",
            temperature=0.5,
            enable_rag=True,
        )

        assert config.llm_provider == "ollama"
        assert config.llm_model == "llama2:7b"
        assert config.temperature == 0.5
        assert config.enable_rag is True

    def test_get_existing_key(self) -> None:
        """Test getting existing configuration values."""
        config = QuantChainConfig(llm_provider="test_provider")

        # Test getting known configuration value
        result = config.get("llm_provider")
        assert result == "test_provider"

    def test_get_nonexistent_key_with_default(self) -> None:
        """Test getting non-existent key with default value."""
        config = QuantChainConfig()

        result = config.get("nonexistent_key", "default_value")
        assert result == "default_value"

    def test_get_nonexistent_key_no_default(self) -> None:
        """Test getting non-existent key without default value."""
        config = QuantChainConfig()

        result = config.get("nonexistent_key")
        assert result is None

    def test_set_key(self) -> None:
        """Test setting configuration values."""
        config = QuantChainConfig()

        config.set("custom_key", "custom_value")
        result = config.get("custom_key")
        assert result == "custom_value"

    def test_to_dict(self) -> None:
        """Test getting configuration as dictionary."""
        config = QuantChainConfig(llm_provider="test_provider")

        config_dict = config.to_dict()

        assert isinstance(config_dict, dict)
        assert config_dict["llm_provider"] == "test_provider"
        assert config_dict["llm_model"] == "gpt-4"

    def test_validate_valid_config(self) -> None:
        """Test validation of valid configuration."""
        config = QuantChainConfig()

        errors = config.validate()
        assert len(errors) == 0

    def test_load_from_file(self) -> None:
        """Test loading configuration from file."""
        # Create a temporary config file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write('{"llm_provider": "file_provider", "temperature": 0.8}')
            temp_file = f.name

        try:
            config = QuantChainConfig()
            config._load_from_file(temp_file)

            assert config.get("llm_provider") == "file_provider"
            assert config.get("temperature") == 0.8
        finally:
            os.unlink(temp_file)

    def test_save_to_file(self) -> None:
        """Test saving configuration to file."""
        config = QuantChainConfig(llm_provider="save_test")

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            temp_file = f.name

        try:
            config.save_to_file(temp_file)

            # Verify file was created and has content
            assert os.path.exists(temp_file)
            assert os.path.getsize(temp_file) > 0
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)


@pytest.mark.unit
class TestLogLevel:
    """Test suite for LogLevel enum."""

    def test_log_level_values(self) -> None:
        """Test that LogLevel enum has correct values."""
        assert LogLevel.DEBUG.value == "debug"
        assert LogLevel.INFO.value == "info"
        assert LogLevel.WARNING.value == "warning"
        assert LogLevel.ERROR.value == "error"
        assert LogLevel.CRITICAL.value == "critical"

    def test_log_level_from_string(self) -> None:
        """Test creating LogLevel from string."""
        level = LogLevel("info")
        assert level == LogLevel.INFO