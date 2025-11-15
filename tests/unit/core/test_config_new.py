"""Tests for QuantChain configuration system."""

import json
import os
import tempfile
from unittest.mock import patch
from pathlib import Path
import pytest

from quantchain.core.config import QuantChainConfig, LogLevel


@pytest.mark.unit
class TestQuantChainConfig:
    """Test suite for QuantChainConfig."""

    def test_initialization_with_defaults(self) -> None:
        """Test initialization with default values."""
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

    def test_initialization_with_custom_values(self) -> None:
        """Test initialization with custom values."""
        config = QuantChainConfig(
            agent_type="trader",
            llm_provider="anthropic",
            llm_model="claude-3",
            temperature=0.5,
            max_tokens=4096,
            enable_rag=True,
            enable_reflection=True,
            vector_store_path="./custom/vector",
            db_path="./custom/db",
            vision_provider="claude-3-vision",
            max_retries=5,
            retry_delay=2.0,
            log_level=LogLevel.DEBUG
        )

        assert config.agent_type == "trader"
        assert config.llm_provider == "anthropic"
        assert config.llm_model == "claude-3"
        assert config.temperature == 0.5
        assert config.max_tokens == 4096
        assert config.enable_rag is True
        assert config.enable_reflection is True
        assert config.vector_store_path == "./custom/vector"
        assert config.db_path == "./custom/db"
        assert config.vision_provider == "claude-3-vision"
        assert config.max_retries == 5
        assert config.retry_delay == 2.0
        assert config.log_level == LogLevel.DEBUG

    def test_initialization_with_string_log_level(self) -> None:
        """Test initialization with log level as string."""
        config = QuantChainConfig(log_level="error")
        assert config.log_level == LogLevel.ERROR

    def test_load_from_file(self) -> None:
        """Test loading configuration from a file."""
        # Create a temporary config file
        config_data = {
            "agent_type": "custom_agent",
            "llm_provider": "custom_provider",
            "llm_model": "custom_model",
            "temperature": 0.8,
            "max_tokens": 1024,
            "enable_rag": True,
            "enable_reflection": True,
            "vector_store_path": "./test/vector",
            "db_path": "./test/db",
            "vision_provider": "test_vision",
            "max_retries": 10,
            "retry_delay": 3.0,
            "log_level": "warning"
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(config_data, f)
            temp_file = f.name

        try:
            config = QuantChainConfig(config_file=temp_file)

            # Check that values were loaded
            assert config.agent_type == "custom_agent"
            assert config.llm_provider == "custom_provider"
            assert config.llm_model == "custom_model"
            assert config.temperature == 0.8
            assert config.max_tokens == 1024
            assert config.enable_rag is True
            assert config.enable_reflection is True
            assert config.vector_store_path == "./test/vector"
            assert config.db_path == "./test/db"
            assert config.vision_provider == "test_vision"
            assert config.max_retries == 10
            assert config.retry_delay == 3.0
            assert config.log_level == LogLevel.WARNING
        finally:
            os.unlink(temp_file)

    def test_load_from_nonexistent_file(self) -> None:
        """Test loading configuration from a non-existent file."""
        config = QuantChainConfig(config_file="/nonexistent/config.json")

        # Should use default values when file doesn't exist
        assert config.agent_type == "default"
        assert config.llm_provider == "openai"

    def test_save_to_file(self) -> None:
        """Test saving configuration to a file."""
        config = QuantChainConfig(
            agent_type="test_agent",
            llm_provider="test_provider"
        )

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            temp_file = f.name

        try:
            config.save_to_file(temp_file)

            # Verify file was created and contains expected data
            with open(temp_file, 'r') as f:
                saved_data = json.load(f)

            assert saved_data["agent_type"] == "test_agent"
            assert saved_data["llm_provider"] == "test_provider"
        finally:
            os.unlink(temp_file)

    def test_get_method(self) -> None:
        """Test get method."""
        config = QuantChainConfig(agent_type="test")

        assert config.get("agent_type") == "test"
        assert config.get("nonexistent") is None
        assert config.get("nonexistent", "default") == "default"

    def test_set_method(self) -> None:
        """Test set method."""
        config = QuantChainConfig()

        config.set("agent_type", "modified")
        assert config.agent_type == "modified"

        config.set("custom_key", "custom_value")
        assert config.get("custom_key") == "custom_value"

    def test_to_dict(self) -> None:
        """Test converting configuration to dictionary."""
        config = QuantChainConfig(
            agent_type="test",
            log_level=LogLevel.DEBUG
        )

        config_dict = config.to_dict()

        assert isinstance(config_dict, dict)
        assert config_dict["agent_type"] == "test"
        assert config_dict["log_level"] == "debug"  # Enum should be converted to string

    def test_validate(self) -> None:
        """Test configuration validation."""
        # Valid config
        config = QuantChainConfig()
        errors = config.validate()
        assert len(errors) == 0

        # Invalid configs
        invalid_config = QuantChainConfig(
            llm_provider="",  # Empty string
            temperature=3.0,  # Too high
            max_tokens=-1,  # Negative
            max_retries=-1,  # Negative
            retry_delay=-1.0  # Negative
        )
        errors = invalid_config.validate()

        # Should have multiple errors
        assert len(errors) > 0
        assert any("LLM provider is required" in error for error in errors)
        assert any("Temperature must be between 0 and 2" in error for error in errors)
        assert any("Max tokens must be positive" in error for error in errors)
        assert any("Max retries must be non-negative" in error for error in errors)
        assert any("Retry delay must be non-negative" in error for error in errors)

    def test_directory_creation(self) -> None:
        """Test that data directories are created."""
        with tempfile.TemporaryDirectory() as temp_dir:
            vector_path = os.path.join(temp_dir, "vectors", "store")
            db_path = os.path.join(temp_dir, "data", "db")

            config = QuantChainConfig(
                vector_store_path=vector_path,
                db_path=db_path
            )

            # Check directories were created
            assert os.path.exists(os.path.dirname(vector_path))
            assert os.path.exists(os.path.dirname(db_path))

    def test_load_from_file_error_handling(self) -> None:
        """Test error handling in _load_from_file method."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("{ invalid json }")
            temp_file = f.name

        try:
            # Create a config that loads from file
            config = QuantChainConfig(config_file=temp_file)
            # Should not crash but use defaults
            assert config.llm_provider == "openai"  # Default value
        finally:
            os.unlink(temp_file)

    def test_save_to_file_error_handling(self) -> None:
        """Test error handling in save_to_file method."""
        config = QuantChainConfig()

        # Try to save to an invalid path
        try:
            # This should not crash the program
            config.save_to_file("/invalid/path/config.json")
        except Exception:
            # Expected to fail due to invalid path
            pass

    def test_to_dict_with_enum_values(self) -> None:
        """Test to_dict method properly converts enum values."""
        config = QuantChainConfig(log_level=LogLevel.WARNING)

        config_dict = config.to_dict()

        assert config_dict["log_level"] == "warning"
