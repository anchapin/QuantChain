"""Tests for QuantChain configuration system."""

import pytest
import os
import tempfile
import json
import yaml
from unittest.mock import patch
from quantchain.core.config import QuantChainConfig, get_config, reload_config


class TestQuantChainConfig:
    """Test QuantChainConfig class."""

    def test_default_config(self):
        """Test loading default configuration."""
        config = QuantChainConfig()
        assert config.get("llm.provider") == "ollama"
        assert config.get("trading.paper_trading") is True
        assert config.get("backtesting.initial_balance") == 10000

    def test_config_get_with_default(self):
        """Test getting config value with default."""
        config = QuantChainConfig()
        assert config.get("nonexistent.key", "default") == "default"

    def test_config_to_dict(self):
        """Test converting config to dictionary."""
        config = QuantChainConfig()
        config_dict = config.to_dict()
        assert isinstance(config_dict, dict)
        assert "llm" in config_dict
        assert "trading" in config_dict

    def test_get_config_singleton(self):
        """Test that get_config returns singleton instance."""
        config1 = get_config()
        config2 = get_config()
        assert config1 is config2

    @patch.dict(
        os.environ,
        {
            "QUANTCHAIN_LLM_PROVIDER": "vllm",
            "QUANTCHAIN_LLM_MODEL": "gpt-4",
            "QUANTCHAIN_DATA_PROVIDER": "alpha_vantage",
            "QUANTCHAIN_PAPER_TRADING": "false",
        },
    )
    def test_load_from_env(self):
        """Test loading configuration from environment variables."""
        config = QuantChainConfig()
        assert config.get("llm.provider") == "vllm"
        assert config.get("llm.model") == "gpt-4"
        assert config.get("data.default_provider") == "alpha_vantage"
        assert config.get("trading.paper_trading") is False

    def test_load_from_file_json(self):
        """Test loading configuration from JSON file."""
        config_data = {"llm": {"provider": "vllm"}, "trading": {"paper_trading": False}}
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(config_data, f)
            config_file = f.name

        try:
            config = QuantChainConfig(config_file)
            assert config.get("llm.provider") == "vllm"
            assert config.get("trading.paper_trading") is False
            # Ensure defaults are preserved
            assert config.get("backtesting.initial_balance") == 10000
        finally:
            os.unlink(config_file)

    def test_load_from_file_yaml(self):
        """Test loading configuration from YAML file."""
        config_data = {"llm": {"model": "gpt-4"}, "data": {"cache_enabled": False}}
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(config_data, f)
            config_file = f.name

        try:
            config = QuantChainConfig(config_file)
            assert config.get("llm.model") == "gpt-4"
            assert config.get("data.cache_enabled") is False
        finally:
            os.unlink(config_file)

    def test_load_from_file_not_found(self):
        """Test error when config file not found."""
        with pytest.raises(FileNotFoundError):
            QuantChainConfig("nonexistent.json")

    def test_deep_merge(self):
        """Test deep merge of configuration dictionaries."""
        base = {"a": {"b": 1}, "c": 2}
        update = {"a": {"d": 3}, "e": 4}
        config = QuantChainConfig()
        config._deep_merge(base, update)
        assert base == {"a": {"b": 1, "d": 3}, "c": 2, "e": 4}

    def test_get_api_key(self):
        """Test getting API keys for providers."""
        with patch.dict(
            os.environ,
            {"ALPACA_API_KEY": "test_key", "ALPHA_VANTAGE_API_KEY": "test_key2"},
        ):
            config = QuantChainConfig()
            assert config.get_api_key("alpaca") == "test_key"
            assert config.get_api_key("alpha_vantage") == "test_key2"
            assert config.get_api_key("unknown") is None

    def test_reload_config(self):
        """Test reloading the global configuration instance."""
        # First, get config
        config1 = get_config()
        # Reload
        config2 = reload_config()
        # Should be a new instance
        assert config1 is not config2

    def test_get_edge_cases(self):
        """Test edge cases for get method."""
        config = QuantChainConfig()
        # Empty key
        assert config.get("") is None
        # Invalid key structure
        assert config.get("invalid.key.path", "default") == "default"


if __name__ == "__main__":
    pytest.main([__file__])
