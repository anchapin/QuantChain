"""Tests for QuantChain configuration system."""

import pytest
from quantchain.core.config import QuantChainConfig, get_config


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


if __name__ == "__main__":
    pytest.main([__file__])
