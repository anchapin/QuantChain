"""Configuration management for QuantChain."""

import os
from enum import Enum
from typing import Dict, List, Optional, Any, Union


class LogLevel(Enum):
    """Logging levels for the system."""

    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class QuantChainConfig:
    """Main configuration class for QuantChain."""

    def __init__(
        self,
        agent_type: Optional[str] = None,
        llm_provider: str = "openai",
        llm_model: str = "gpt-4",
        temperature: float = 0.7,
        max_tokens: int = 2048,
        enable_rag: bool = False,
        enable_reflection: bool = False,
        vector_store_path: Optional[str] = None,
        db_path: Optional[str] = None,
        vision_provider: str = "gpt-4-vision-preview",
        max_retries: int = 3,
        retry_delay: float = 1.0,
        log_level: Union[LogLevel, str] = LogLevel.INFO,
        config_file: Optional[str] = None,
    ):
        """
        Initialize QuantChain configuration.

        Args:
            agent_type: Type of agent to use
            llm_provider: LLM provider to use
            llm_model: LLM model to use
            temperature: Temperature for LLM generation
            max_tokens: Maximum tokens for LLM generation
            enable_rag: Whether to enable RAG
            enable_reflection: Whether to enable reflection
            vector_store_path: Path to vector store
            db_path: Path to database
            vision_provider: Vision model provider
            max_retries: Maximum retries for operations
            retry_delay: Delay between retries in seconds
            log_level: Logging level
            config_file: Path to configuration file
        """
        # Load from file if provided
        if config_file and os.path.exists(config_file):
            self._load_from_file(config_file)
            return

        # Set default values
        self.agent_type = agent_type or "default"
        self.llm_provider = llm_provider
        self.llm_model = llm_model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.enable_rag = enable_rag
        self.enable_reflection = enable_reflection
        self.vector_store_path = vector_store_path or "./data/vector_store"
        self.db_path = db_path or "./data/quantchain.db"
        self.vision_provider = vision_provider
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.log_level = (
            log_level if isinstance(log_level, LogLevel) else LogLevel(log_level)
        )

        # Create data directories if they don't exist
        os.makedirs(os.path.dirname(self.vector_store_path), exist_ok=True)
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

    def _load_from_file(self, config_file: str) -> None:
        """Load configuration from a file."""
        try:
            import json

            with open(config_file, "r") as f:
                config_data = json.load(f)

            # Set attributes from config file
            for key, value in config_data.items():
                if hasattr(self, key):
                    setattr(self, key, value)
        except Exception as e:
            print(f"Error loading config file: {e}")

    def save_to_file(self, config_file: str) -> None:
        """Save configuration to a file."""
        try:
            import json

            config_data = {}

            # Get all serializable attributes
            for key in dir(self):
                if not key.startswith("_"):
                    value = getattr(self, key)
                    if isinstance(
                        value, (str, int, float, bool, list, dict, type(None))
                    ):
                        if isinstance(value, Enum):
                            config_data[key] = value.value
                        else:
                            config_data[key] = value

            with open(config_file, "w") as f:
                json.dump(config_data, f, indent=2)
        except Exception as e:
            print(f"Error saving config file: {e}")

    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value."""
        return getattr(self, key, default)

    def set(self, key: str, value: Any) -> None:
        """Set a configuration value."""
        setattr(self, key, value)

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to a dictionary."""
        config = {}
        for key in dir(self):
            if not key.startswith("_"):
                value = getattr(self, key)
                if isinstance(value, (str, int, float, bool, list, dict, type(None))):
                    if isinstance(value, Enum):
                        config[key] = value.value
                    else:
                        config[key] = value
        return config

    def validate(self) -> List[str]:
        """Validate the configuration and return any errors."""
        errors = []

        if not self.llm_provider:
            errors.append("LLM provider is required")

        if self.temperature < 0 or self.temperature > 2:
            errors.append("Temperature must be between 0 and 2")

        if self.max_tokens <= 0:
            errors.append("Max tokens must be positive")

        if self.max_retries < 0:
            errors.append("Max retries must be non-negative")

        if self.retry_delay < 0:
            errors.append("Retry delay must be non-negative")

        return errors
