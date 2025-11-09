"""Configuration system for QuantChain."""

import copy
import os
from pathlib import Path
from typing import Dict, Any, Optional
import json
import yaml


class QuantChainConfig:
    """Configuration manager for QuantChain applications."""

    def __init__(self, config_file: Optional[str] = None):
        """Initialize configuration from environment variables and config file.

        Args:
            config_file: Path to configuration file (JSON or YAML)
        """
        self._config = self._load_default_config()
        self._load_from_env()
        if config_file:
            self._load_from_file(config_file)

    def _load_default_config(self) -> Dict[str, Any]:
        """Load default configuration values."""
        return {
            # LLM Configuration
            "llm": {
                "provider": "ollama",  # or "vllm"
                "model": "llama2:7b",
                "temperature": 0.7,
                "max_tokens": 1000,
            },
            # Data Sources
            "data": {
                "default_provider": "alpaca",
                "cache_enabled": True,
                "cache_dir": "./data/cache",
            },
            # Trading
            "trading": {
                "default_broker": "alpaca",
                "paper_trading": True,
                "max_position_size": 0.1,  # 10% of portfolio
                "ib": {
                    "host": "127.0.0.1",
                    "port": 7497,  # TWS paper trading port
                    "client_id": 1,
                    "timeout": 10,
                    "account": None,
                },
            },
            # Backtesting
            "backtesting": {
                "default_engine": "backtesting.py",
                "initial_balance": 10000,
                "commission": 0.001,  # 0.1%
            },
            # Agent Configuration
            "agent": {
                "max_iterations": 5,
                "reflection_interval": 10,  # actions
            },
            # RAG Configuration
            "rag": {
                "vector_store_type": "chromadb",
                "embedding_model": "all-MiniLM-L6-v2",
                "persist_directory": "./data/chroma_db",
                "enabled": False,  # Disabled by default
            },
            # Tutorial Mode Configuration
            "tutorial": {
                "enabled": False,
                "session_duration": 3600,  # 1 hour default
                "learning_objectives": [],
                "feedback_level": "detailed",  # basic, detailed, comprehensive
                "track_mistakes": True,
                "analyze_market_drivers": True,
                "confidence_threshold": 0.75,
                "max_mistakes_per_session": 10,
            },
            # Logging
            "logging": {
                "level": "INFO",
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "file": "./logs/quantchain.log",
            },
        }

    def _load_from_env(self) -> None:
        """Load configuration from environment variables."""
        # LLM settings
        if "QUANTCHAIN_LLM_PROVIDER" in os.environ:
            self._config["llm"]["provider"] = os.environ["QUANTCHAIN_LLM_PROVIDER"]
        if "QUANTCHAIN_LLM_MODEL" in os.environ:
            self._config["llm"]["model"] = os.environ["QUANTCHAIN_LLM_MODEL"]

        # Data settings
        if "QUANTCHAIN_DATA_PROVIDER" in os.environ:
            self._config["data"]["default_provider"] = os.environ[
                "QUANTCHAIN_DATA_PROVIDER"
            ]

        # Trading settings
        if "QUANTCHAIN_PAPER_TRADING" in os.environ:
            self._config["trading"]["paper_trading"] = (
                os.environ["QUANTCHAIN_PAPER_TRADING"].lower() == "true"
            )

        # Interactive Brokers settings
        if "QUANTCHAIN_IB_HOST" in os.environ:
            self._config["trading"]["ib"]["host"] = os.environ["QUANTCHAIN_IB_HOST"]
        if "QUANTCHAIN_IB_PORT" in os.environ:
            self._config["trading"]["ib"]["port"] = int(
                os.environ["QUANTCHAIN_IB_PORT"]
            )
        if "QUANTCHAIN_IB_CLIENT_ID" in os.environ:
            self._config["trading"]["ib"]["client_id"] = int(
                os.environ["QUANTCHAIN_IB_CLIENT_ID"]
            )
        if "QUANTCHAIN_IB_TIMEOUT" in os.environ:
            self._config["trading"]["ib"]["timeout"] = float(
                os.environ["QUANTCHAIN_IB_TIMEOUT"]
            )
        if "QUANTCHAIN_IB_ACCOUNT" in os.environ:
            self._config["trading"]["ib"]["account"] = os.environ[
                "QUANTCHAIN_IB_ACCOUNT"
            ]

        # Tutorial mode settings
        if "QUANTCHAIN_TUTORIAL_ENABLED" in os.environ:
            self._config["tutorial"]["enabled"] = (
                os.environ["QUANTCHAIN_TUTORIAL_ENABLED"].lower() == "true"
            )
        if "QUANTCHAIN_TUTORIAL_FEEDBACK_LEVEL" in os.environ:
            self._config["tutorial"]["feedback_level"] = os.environ[
                "QUANTCHAIN_TUTORIAL_FEEDBACK_LEVEL"
            ]

        # API Keys (loaded but not stored in config for security)
        self._api_keys = {
            "alpaca_key": os.environ.get("ALPACA_API_KEY"),
            "alpaca_secret": os.environ.get("ALPACA_API_SECRET"),
            "alpha_vantage_key": os.environ.get("ALPHA_VANTAGE_API_KEY"),
        }

    def _load_from_file(self, config_file: str) -> None:
        """Load configuration from JSON or YAML file."""
        config_path = Path(config_file)
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_file}")

        with open(config_path, "r") as f:
            if config_path.suffix.lower() in {".yaml", ".yml"}:
                try:
                    file_config = yaml.safe_load(f)
                except yaml.YAMLError as e:
                    raise ValueError(
                        f"Invalid YAML in configuration file {config_file}: {e}"
                    ) from e
            else:
                try:
                    file_config = json.load(f)
                except json.JSONDecodeError as e:
                    raise ValueError(
                        f"Invalid JSON in configuration file {config_file}: {e}"
                    ) from e

        # Deep merge file config with default config
        self._deep_merge(self._config, file_config)

    def _deep_merge(self, base: Dict[str, Any], update: Dict[str, Any]) -> None:
        """Deep merge update dict into base dict."""
        for key, value in update.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_merge(base[key], value)
            else:
                base[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by dot-separated key."""
        keys = key.split(".")
        value = self._config
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default

    def get_api_key(self, provider: str) -> Optional[str]:
        """Get API key for a specific provider."""
        key_map = {
            "alpaca": "alpaca_key",
            "alpha_vantage": "alpha_vantage_key",
        }
        if key_name := key_map.get(provider):
            return self._api_keys.get(key_name)
        return None

    def to_dict(self) -> Dict[str, Any]:
        """Return configuration as dictionary."""
        return copy.deepcopy(self._config)


# Global configuration instance
_config_instance: Optional[QuantChainConfig] = None


def get_config(config_file: Optional[str] = None) -> QuantChainConfig:
    """Get the global configuration instance."""
    global _config_instance
    if _config_instance is None:
        _config_instance = QuantChainConfig(config_file)
    return _config_instance


def reload_config(config_file: Optional[str] = None) -> QuantChainConfig:
    """Reload the global configuration instance."""
    global _config_instance
    _config_instance = QuantChainConfig(config_file)
    return _config_instance
