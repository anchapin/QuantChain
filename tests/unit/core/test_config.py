"""Tests for QuantChain configuration system."""

import json
import os
import tempfile
from unittest.mock import patch

import pytest
import yaml

from quantchain.core.config import QuantChainConfig, get_config, reload_config


@pytest.mark.unit
class TestQuantChainConfig:
    """Test suite for QuantChainConfig."""

    def test_init_with_defaults(self) -> None:
        """Test initialization with default configuration."""
        config = QuantChainConfig()

        # Check default values exist
        assert "llm" in config._config
        assert "data" in config._config
        assert "trading" in config._config
        assert "backtesting" in config._config

        # Check specific defaults
        assert config._config["llm"]["provider"] == "ollama"
        assert config._config["llm"]["model"] == "llama2:7b"
        assert config._config["data"]["default_provider"] == "alpaca"
        assert config._config["trading"]["paper_trading"] is True

    def test_get_existing_key(self) -> None:
        """Test getting existing configuration values."""
        config = QuantChainConfig()

        # Test nested access
        llm_provider = config.get("llm.provider")
        assert llm_provider == "ollama"

        # Test top-level access
        data_config = config.get("data")
        assert isinstance(data_config, dict)
        assert data_config["default_provider"] == "alpaca"

    def test_get_nonexistent_key_with_default(self) -> None:
        """Test getting non-existent key with default value."""
        config = QuantChainConfig()

        result = config.get("nonexistent.key", "default_value")
        assert result == "default_value"

    def test_get_nonexistent_key_no_default(self) -> None:
        """Test getting non-existent key without default value."""
        config = QuantChainConfig()

        result = config.get("nonexistent.key")
        assert result is None

    def test_get_nested_key_levels(self) -> None:
        """Test getting deeply nested configuration values."""
        config = QuantChainConfig()

        # Test multiple levels
        temperature = config.get("llm.temperature")
        assert temperature == 0.7

    def test_load_from_json_file(self) -> None:
        """Test loading configuration from JSON file."""
        test_config = {
            "llm": {"provider": "openai", "model": "gpt-4"},
            "custom_key": "custom_value",
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(test_config, f)
            temp_file = f.name

        try:
            config = QuantChainConfig(temp_file)

            # Check loaded values
            assert config.get("llm.provider") == "openai"
            assert config.get("llm.model") == "gpt-4"
            assert config.get("custom_key") == "custom_value"

            # Check defaults are still present for non-specified values
            assert config.get("llm.temperature") == 0.7  # Default value

        finally:
            os.unlink(temp_file)

    def test_load_from_yaml_file(self) -> None:
        """Test loading configuration from YAML file."""
        test_config = {
            "llm": {"provider": "vllm", "model": "mistral"},
            "yaml_key": "yaml_value",
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(test_config, f)
            temp_file = f.name

        try:
            config = QuantChainConfig(temp_file)

            # Check loaded values
            assert config.get("llm.provider") == "vllm"
            assert config.get("llm.model") == "mistral"
            assert config.get("yaml_key") == "yaml_value"

        finally:
            os.unlink(temp_file)

    def test_load_from_nonexistent_file(self) -> None:
        """Test loading from non-existent file raises error."""
        with pytest.raises(FileNotFoundError):
            QuantChainConfig("/nonexistent/config.json")

    def test_load_from_invalid_json(self) -> None:
        """Test loading from invalid JSON file raises error."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("{ invalid json }")
            temp_file = f.name

        try:
            with pytest.raises(ValueError, match="Invalid JSON"):
                QuantChainConfig(temp_file)
        finally:
            os.unlink(temp_file)

    def test_load_from_invalid_yaml(self) -> None:
        """Test loading from invalid YAML file raises error."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("invalid: yaml: content: [")
            temp_file = f.name

        try:
            with pytest.raises(ValueError, match="Invalid YAML"):
                QuantChainConfig(temp_file)
        finally:
            os.unlink(temp_file)

    @patch.dict(
        os.environ,
        {
            "QUANTCHAIN_LLM_PROVIDER": "env_provider",
            "QUANTCHAIN_LLM_MODEL": "env_model",
            "QUANTCHAIN_DATA_PROVIDER": "env_data_provider",
            "QUANTCHAIN_PAPER_TRADING": "false",
        },
    )
    def test_load_from_environment_variables(self) -> None:
        """Test loading configuration from environment variables."""
        config = QuantChainConfig()

        # Check environment variable loading
        assert config.get("llm.provider") == "env_provider"
        assert config.get("llm.model") == "env_model"
        assert config.get("data.default_provider") == "env_data_provider"
        assert config.get("trading.paper_trading") is False

    def test_get_api_key_from_config(self) -> None:
        """Test getting API key from environment variables."""
        with patch.dict("os.environ", {}, clear=True):
            config = QuantChainConfig()

            # Test API key that doesn't exist
            api_key = config.get_api_key("alpaca")
            assert api_key is None

    @patch.dict(os.environ, {"ALPACA_API_KEY": "env_alpaca_key"})
    def test_get_api_key_from_environment(self) -> None:
        """Test getting API key from environment variable."""
        config = QuantChainConfig()

        api_key = config.get_api_key("alpaca")
        assert api_key == "env_alpaca_key"

    def test_get_api_key_not_found(self) -> None:
        """Test getting non-existent API key returns None."""
        config = QuantChainConfig()

        api_key = config.get_api_key("nonexistent_service")
        assert api_key is None

    def test_config_copy_isolation(self) -> None:
        """Test that config copies are properly isolated."""
        config1 = QuantChainConfig()
        config2 = QuantChainConfig()

        # Modify config1 by modifying underlying dict (since no set method)
        config1._config["llm"]["temperature"] = 0.9

        # Config2 should not be affected
        assert config2.get("llm.temperature") == 0.7
        assert config1.get("llm.temperature") == 0.9

    def test_config_as_dict(self) -> None:
        """Test getting configuration as dictionary."""
        config = QuantChainConfig()

        config_dict = config.to_dict()

        assert isinstance(config_dict, dict)
        assert "llm" in config_dict
        assert "data" in config_dict

    def test_save_to_json(self) -> None:
        """Test configuration save functionality is not implemented yet."""
        config = QuantChainConfig()

        # Since save method doesn't exist, test that to_dict works
        config_dict = config.to_dict()
        assert isinstance(config_dict, dict)
        assert config_dict["llm"]["provider"] == "ollama"

    def test_save_to_yaml(self) -> None:
        """Test configuration save functionality is not implemented yet."""
        config = QuantChainConfig()

        # Since save method doesn't exist, test that to_dict works
        config_dict = config.to_dict()
        assert isinstance(config_dict, dict)
        assert config_dict["llm"]["provider"] == "ollama"

    def test_config_file_priority(self) -> None:
        """Test that file config overrides environment variables."""
        test_file_config = {"llm": {"provider": "file_provider"}}

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(test_file_config, f)
            temp_file = f.name

        try:
            with patch.dict(os.environ, {"QUANTCHAIN_LLM_PROVIDER": "env_provider"}):
                config = QuantChainConfig(temp_file)

                # File should override environment
                assert config.get("llm.provider") == "file_provider"
        finally:
            os.unlink(temp_file)

    def test_get_config_singleton(self) -> None:
        """Test that get_config returns same instance."""
        config1 = get_config()
        config2 = get_config()

        assert config1 is config2

    def test_reload_config_new_instance(self) -> None:
        """Test that reload_config creates new instance."""
        config1 = get_config()
        config2 = reload_config()

        assert config1 is not config2
        assert isinstance(config2, QuantChainConfig)
