"""Simple tests for config module."""

import json
import os
import pytest
import tempfile
from pathlib import Path

from quantchain.core.config import QuantChainConfig, LogLevel


class TestLogLevel:
    """Test LogLevel enum."""

    def test_log_level_values(self) -> None:
        """Test that log level values are correct."""
        assert LogLevel.DEBUG.value == "debug"
        assert LogLevel.INFO.value == "info"
        assert LogLevel.WARNING.value == "warning"
        assert LogLevel.ERROR.value == "error"
        assert LogLevel.CRITICAL.value == "critical"


class TestQuantChainConfig:
    """Test QuantChainConfig class."""

    def test_initialization_with_defaults(self) -> None:
        """Test config initialization with default values."""
        config = QuantChainConfig()

        assert config.agent_type == "default"
        assert config.llm_provider == "openai"
        assert config.llm_model == "gpt-4"
        assert config.temperature == 0.7
        assert config.max_tokens == 2048
        assert config.enable_rag is False
        assert config.enable_reflection is False
        assert config.vector_store_path == "./data/vector_store"
        assert config.db_path == "./data/quantchain.db"
        assert config.vision_provider == "gpt-4-vision-preview"
        assert config.max_retries == 3
        assert config.retry_delay == 1.0
        assert config.log_level == LogLevel.INFO

    def test_get_existing_attribute(self) -> None:
        """Test getting an existing configuration value."""
        config = QuantChainConfig(llm_model="test_model")

        assert config.get("llm_model") == "test_model"

    def test_get_nonexistent_attribute_with_default(self) -> None:
        """Test getting a non-existent configuration value with default."""
        config = QuantChainConfig()

        assert config.get("nonexistent", "default_value") == "default_value"

    def test_get_nonexistent_attribute_no_default(self) -> None:
        """Test getting a non-existent configuration value without default."""
        config = QuantChainConfig()

        assert config.get("nonexistent") is None

    def test_set_attribute(self) -> None:
        """Test setting a configuration value."""
        config = QuantChainConfig()

        config.set("llm_model", "new_model")

        assert config.llm_model == "new_model"

    def test_to_dict(self) -> None:
        """Test converting configuration to a dictionary."""
        config = QuantChainConfig(
            agent_type="dict_test",
            temperature=0.6,
            enable_rag=True,
            log_level=LogLevel.DEBUG
        )

        config_dict = config.to_dict()

        assert config_dict["agent_type"] == "dict_test"
        assert config_dict["temperature"] == 0.6
        assert config_dict["enable_rag"] is True
        assert config_dict["log_level"] == "debug"  # Enum value
        # Should not include private attributes
        assert "_private" not in config_dict

    def test_validate_success(self) -> None:
        """Test validation with valid configuration."""
        config = QuantChainConfig(
            llm_provider="openai",
            temperature=0.7,
            max_tokens=2048,
            max_retries=3,
            retry_delay=1.0
        )

        errors = config.validate()

        assert len(errors) == 0

    def test_validate_missing_llm_provider(self) -> None:
        """Test validation with missing LLM provider."""
        config = QuantChainConfig(llm_provider="")

        errors = config.validate()

        assert len(errors) > 0
        assert any("LLM provider is required" in error for error in errors)

    def test_validate_temperature_too_low(self) -> None:
        """Test validation with temperature too low."""
        config = QuantChainConfig(temperature=-0.1)

        errors = config.validate()

        assert len(errors) > 0
        assert any("Temperature must be between 0 and 2" in error for error in errors)

    def test_validate_temperature_too_high(self) -> None:
        """Test validation with temperature too high."""
        config = QuantChainConfig(temperature=2.1)

        errors = config.validate()

        assert len(errors) > 0
        assert any("Temperature must be between 0 and 2" in error for error in errors)

    def test_validate_invalid_max_tokens(self) -> None:
        """Test validation with invalid max tokens."""
        config = QuantChainConfig(max_tokens=0)

        errors = config.validate()

        assert len(errors) > 0
        assert any("Max tokens must be positive" in error for error in errors)

    def test_validate_negative_max_retries(self) -> None:
        """Test validation with negative max retries."""
        config = QuantChainConfig(max_retries=-1)

        errors = config.validate()

        assert len(errors) > 0
        assert any("Max retries must be non-negative" in error for error in errors)

    def test_validate_negative_retry_delay(self) -> None:
        """Test validation with negative retry delay."""
        config = QuantChainConfig(retry_delay=-1.0)

        errors = config.validate()

        assert len(errors) > 0
        assert any("Retry delay must be non-negative" in error for error in errors)
