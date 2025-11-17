"""
Comprehensive tests for quantchain.core.config module.
These tests are designed to achieve high test coverage for the config module.
"""

import json
import os
import tempfile
from unittest.mock import mock_open, patch

import pytest

from quantchain.core.config import LogLevel, QuantChainConfig


class TestLogLevel:
    """Test LogLevel enum functionality."""

    def test_log_level_values(self) -> None:
        """Test LogLevel enum values."""
        assert LogLevel.DEBUG.value == "debug"
        assert LogLevel.INFO.value == "info"
        assert LogLevel.WARNING.value == "warning"
        assert LogLevel.ERROR.value == "error"
        assert LogLevel.CRITICAL.value == "critical"

    def test_log_level_comparison(self) -> None:
        """Test LogLevel enum comparison."""
        assert LogLevel.DEBUG == LogLevel.DEBUG
        assert LogLevel.DEBUG != LogLevel.INFO

    def test_log_level_string_conversion(self) -> None:
        """Test LogLevel to string conversion."""
        assert LogLevel.DEBUG.value == "debug"
        assert LogLevel.INFO.value == "info"


class TestQuantChainConfig:
    """Test QuantChainConfig class functionality."""

    def test_config_init_default(self) -> None:
        """Test QuantChainConfig initialization with defaults."""
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

    def test_config_init_with_parameters(self) -> None:
        """Test QuantChainConfig initialization with custom parameters."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config = QuantChainConfig(
                agent_type="chart_reader",
                llm_provider="anthropic",
                llm_model="claude-3",
                temperature=0.5,
                max_tokens=1024,
                enable_rag=True,
                enable_reflection=True,
                vector_store_path=f"{temp_dir}/vector_store",
                db_path=f"{temp_dir}/database.db",
                vision_provider="claude-3-vision",
                max_retries=5,
                retry_delay=2.0,
                log_level=LogLevel.DEBUG,
            )

            assert config.agent_type == "chart_reader"
            assert config.llm_provider == "anthropic"
            assert config.llm_model == "claude-3"
            assert config.temperature == 0.5
            assert config.max_tokens == 1024
            assert config.enable_rag is True
            assert config.enable_reflection is True
            assert config.vector_store_path == f"{temp_dir}/vector_store"
            assert config.db_path == f"{temp_dir}/database.db"
            assert config.vision_provider == "claude-3-vision"
            assert config.max_retries == 5
            assert config.retry_delay == 2.0
            assert config.log_level == LogLevel.DEBUG

    def test_config_init_with_string_log_level(self) -> None:
        """Test QuantChainConfig with string log level."""
        config = QuantChainConfig(log_level="error")
        assert config.log_level == LogLevel.ERROR

    def test_config_init_with_agent_type_none(self) -> None:
        """Test QuantChainConfig with None agent_type uses default."""
        config = QuantChainConfig(agent_type=None)
        assert config.agent_type == "default"

    def test_config_init_with_default_paths(self) -> None:
        """Test that default directories are created."""
        with tempfile.TemporaryDirectory() as temp_dir:
            vector_path = os.path.join(temp_dir, "vectors", "store")
            db_path = os.path.join(temp_dir, "data", "test.db")

            config = QuantChainConfig(vector_store_path=vector_path, db_path=db_path)

            # Parent directories should be created
            assert os.path.exists(os.path.dirname(vector_path))
            assert os.path.exists(os.path.dirname(db_path))

    def test_config_get_existing_attribute(self) -> None:
        """Test getting existing configuration attribute."""
        config = QuantChainConfig(llm_provider="test_provider")
        assert config.get("llm_provider") == "test_provider"

    def test_config_get_non_existent_attribute(self) -> None:
        """Test getting non-existent configuration attribute."""
        config = QuantChainConfig()
        assert config.get("non_existent") is None

    def test_config_get_non_existent_with_default(self) -> None:
        """Test getting non-existent attribute with default value."""
        config = QuantChainConfig()
        assert config.get("non_existent", "default_value") == "default_value"

    def test_config_set_attribute(self) -> None:
        """Test setting configuration attribute."""
        config = QuantChainConfig()
        config.set("custom_attribute", "custom_value")
        assert config.get("custom_attribute") == "custom_value"

    def test_config_set_existing_attribute(self) -> None:
        """Test setting existing configuration attribute."""
        config = QuantChainConfig(temperature=0.5)
        config.set("temperature", 0.9)
        assert config.get("temperature") == 0.9

    def test_config_to_dict(self) -> None:
        """Test converting configuration to dictionary."""
        config = QuantChainConfig(
            llm_provider="test_provider",
            temperature=0.5,
            enable_rag=True,
            log_level=LogLevel.DEBUG,
        )

        config_dict = config.to_dict()

        assert isinstance(config_dict, dict)
        assert config_dict["llm_provider"] == "test_provider"
        assert config_dict["temperature"] == 0.5
        assert config_dict["enable_rag"] is True
        assert config_dict["log_level"] == "debug"  # Enum should be converted to string

    def test_config_to_dict_excludes_private_attributes(self) -> None:
        """Test that private attributes are excluded from to_dict."""
        config = QuantChainConfig()
        config._private_attr = "should_not_appear"

        config_dict = config.to_dict()

        assert "_private_attr" not in config_dict

    def test_config_save_to_file(self) -> None:
        """Test saving configuration to file."""
        config = QuantChainConfig(
            llm_provider="test_provider", temperature=0.5, enable_rag=True
        )

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            temp_file = f.name

        try:
            config.save_to_file(temp_file)

            # Verify file content
            with open(temp_file, "r") as f:
                saved_data = json.load(f)

            assert saved_data["llm_provider"] == "test_provider"
            assert saved_data["temperature"] == 0.5
            assert saved_data["enable_rag"] is True
        finally:
            os.unlink(temp_file)

    def test_config_save_to_file_error_handling(self) -> None:
        """Test error handling when saving to file."""
        config = QuantChainConfig()

        with patch("builtins.open", side_effect=PermissionError("Permission denied")):
            # Should not raise an exception, should just print error
            config.save_to_file("/restricted/path/config.json")

    def test_config_load_from_file(self) -> None:
        """Test loading configuration from file."""
        config_data = {
            "llm_provider": "anthropic",
            "temperature": 0.3,
            "enable_rag": True,
            "custom_attribute": "custom_value",
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(config_data, f)
            temp_file = f.name

        try:
            config = QuantChainConfig(config_file=temp_file)

            assert config.llm_provider == "anthropic"
            assert config.temperature == 0.3
            assert config.enable_rag is True
            assert config.get("custom_attribute") == "custom_value"
        finally:
            os.unlink(temp_file)

    def test_config_load_from_nonexistent_file(self) -> None:
        """Test loading from non-existent file uses defaults."""
        config = QuantChainConfig(config_file="/nonexistent/config.json")
        assert config.llm_provider == "openai"  # Should use default

    def test_config_load_from_file_error_handling(self) -> None:
        """Test error handling when loading from file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("invalid json content")
            temp_file = f.name

        try:
            # Should not raise an exception, should just print error and use defaults
            config = QuantChainConfig(config_file=temp_file)
            assert config.llm_provider == "openai"  # Should use default
        finally:
            os.unlink(temp_file)

    def test_config_validate_no_errors(self) -> None:
        """Test validation with valid configuration."""
        config = QuantChainConfig(
            llm_provider="openai",
            temperature=0.7,
            max_tokens=2048,
            max_retries=3,
            retry_delay=1.0,
        )

        errors = config.validate()
        assert errors == []

    def test_config_validate_missing_llm_provider(self) -> None:
        """Test validation with missing LLM provider."""
        config = QuantChainConfig()
        config.llm_provider = ""

        errors = config.validate()
        assert "LLM provider is required" in errors

    def test_config_validate_invalid_temperature(self) -> None:
        """Test validation with invalid temperature values."""
        # Test temperature too low
        config = QuantChainConfig(temperature=-0.1)
        errors = config.validate()
        assert "Temperature must be between 0 and 2" in errors

        # Test temperature too high
        config = QuantChainConfig(temperature=2.1)
        errors = config.validate()
        assert "Temperature must be between 0 and 2" in errors

    def test_config_validate_invalid_max_tokens(self) -> None:
        """Test validation with invalid max tokens."""
        config = QuantChainConfig(max_tokens=0)
        errors = config.validate()
        assert "Max tokens must be positive" in errors

    def test_config_validate_negative_max_retries(self) -> None:
        """Test validation with negative max retries."""
        config = QuantChainConfig(max_retries=-1)
        errors = config.validate()
        assert "Max retries must be non-negative" in errors

    def test_config_validate_negative_retry_delay(self) -> None:
        """Test validation with negative retry delay."""
        config = QuantChainConfig(retry_delay=-0.1)
        errors = config.validate()
        assert "Retry delay must be non-negative" in errors

    def test_config_validate_multiple_errors(self) -> None:
        """Test validation with multiple errors."""
        config = QuantChainConfig(
            llm_provider="",
            temperature=3.0,
            max_tokens=-1,
            max_retries=-1,
            retry_delay=-1.0,
        )

        errors = config.validate()
        assert len(errors) >= 5
        assert "LLM provider is required" in errors
        assert "Temperature must be between 0 and 2" in errors
        assert "Max tokens must be positive" in errors
        assert "Max retries must be non-negative" in errors
        assert "Retry delay must be non-negative" in errors

    def test_config_with_none_values(self) -> None:
        """Test configuration with None values."""
        config = QuantChainConfig(vector_store_path=None, db_path=None)

        assert config.vector_store_path == "./data/vector_store"  # Should use default
        assert config.db_path == "./data/quantchain.db"  # Should use default

    def test_config_custom_attributes_serialization(self) -> None:
        """Test serialization of custom attributes."""
        config = QuantChainConfig()
        config.set("custom_string", "test_value")
        config.set("custom_int", 42)
        config.set("custom_bool", True)
        config.set("custom_none", None)

        config_dict = config.to_dict()

        assert config_dict["custom_string"] == "test_value"
        assert config_dict["custom_int"] == 42
        assert config_dict["custom_bool"] is True
        assert config_dict["custom_none"] is None

    def test_config_attributes_filtering(self) -> None:
        """Test that only certain attribute types are included in serialization."""
        config = QuantChainConfig()
        config.set("string_attr", "string_value")
        config.set("method_attr", lambda x: x)  # Function should not be included

        config_dict = config.to_dict()

        assert "string_attr" in config_dict
        assert "method_attr" not in config_dict

    def test_config_directory_creation_with_nested_paths(self) -> None:
        """Test directory creation with deeply nested paths."""
        with tempfile.TemporaryDirectory() as temp_dir:
            deep_path = os.path.join(
                temp_dir, "level1", "level2", "level3", "vector_store"
            )
            config = QuantChainConfig(vector_store_path=deep_path)

            # All parent directories should be created
            assert os.path.exists(os.path.dirname(deep_path))


class TestConfigEdgeCases:
    """Test edge cases and error conditions."""

    def test_config_with_special_characters_in_paths(self) -> None:
        """Test configuration with special characters in paths."""
        with tempfile.TemporaryDirectory() as temp_dir:
            special_path = os.path.join(
                temp_dir, "path with spaces", "special-chars_123"
            )
            config = QuantChainConfig(vector_store_path=special_path)

            assert config.vector_store_path == special_path
            assert os.path.exists(os.path.dirname(special_path))

    def test_config_load_file_with_partial_config(self) -> None:
        """Test loading file with only partial configuration."""
        partial_config = {"llm_provider": "anthropic", "temperature": 0.1}

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(partial_config, f)
            temp_file = f.name

        try:
            config = QuantChainConfig(config_file=temp_file)

            # Loaded values should be applied
            assert config.llm_provider == "anthropic"
            assert config.temperature == 0.1

            # Default values should be used for others
            assert config.llm_model == "gpt-4"
            assert config.max_tokens == 2048
        finally:
            os.unlink(temp_file)

    def test_config_load_file_with_invalid_attributes(self) -> None:
        """Test loading file with invalid/corrupt data."""
        invalid_config = {
            "llm_provider": "test",
            "temperature": "not_a_number",  # Invalid type
            "enable_rag": "not_a_bool",  # Invalid type
            "max_tokens": "not_a_number",
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(invalid_config, f)
            temp_file = f.name

        try:
            config = QuantChainConfig(config_file=temp_file)

            # Should load what it can, even if types are wrong
            # The actual behavior depends on the implementation
            assert hasattr(config, "llm_provider")
        finally:
            os.unlink(temp_file)

    def test_config_serialization_roundtrip(self) -> None:
        """Test that configuration survives save/load roundtrip."""
        original_config = QuantChainConfig(
            llm_provider="anthropic", temperature=0.5, enable_rag=True, max_retries=5
        )

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            temp_file = f.name

        try:
            # Save and reload
            original_config.save_to_file(temp_file)
            loaded_config = QuantChainConfig(config_file=temp_file)

            # Check that values are preserved
            assert loaded_config.llm_provider == original_config.llm_provider
            assert loaded_config.temperature == original_config.temperature
            assert loaded_config.enable_rag == original_config.enable_rag
            assert loaded_config.max_retries == original_config.max_retries
        finally:
            os.unlink(temp_file)
