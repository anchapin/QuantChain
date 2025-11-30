"""
Comprehensive tests for quantchain.core.config module.
"""

import json
import os
import tempfile
from unittest.mock import Mock, mock_open, patch

import pytest

from quantchain.core.config import LogLevel, QuantChainConfig


@pytest.mark.unit
class TestLogLevel:
    """Test LogLevel enum."""

    def test_log_level_values(self) -> None:
        """Test LogLevel enum values."""
        assert LogLevel.DEBUG.value == "debug"
        assert LogLevel.INFO.value == "info"
        assert LogLevel.WARNING.value == "warning"
        assert LogLevel.ERROR.value == "error"
        assert LogLevel.CRITICAL.value == "critical"

    def test_log_level_creation(self) -> None:
        """Test creating LogLevel from string."""
        log_level = LogLevel("info")
        assert log_level == LogLevel.INFO

    def test_log_level_equality(self) -> None:
        """Test LogLevel equality."""
        assert LogLevel.INFO == LogLevel.INFO
        assert LogLevel.INFO != LogLevel.ERROR
        assert LogLevel.INFO == "info"


@pytest.mark.unit
class TestQuantChainConfig:
    """Test QuantChainConfig class."""

    def test_init_with_defaults(self) -> None:
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

    def test_init_with_custom_values(self) -> None:
        """Test initialization with custom values."""
        config = QuantChainConfig(
            agent_type="custom_agent",
            llm_provider="anthropic",
            llm_model="claude-3",
            temperature=0.5,
            max_tokens=1024,
            enable_rag=True,
            enable_reflection=True,
            vector_store_path="/custom/vector",
            db_path="/custom/db.sqlite",
            vision_provider="claude-vision",
            max_retries=5,
            retry_delay=2.0,
            log_level=LogLevel.DEBUG,
        )

        assert config.agent_type == "custom_agent"
        assert config.llm_provider == "anthropic"
        assert config.llm_model == "claude-3"
        assert config.temperature == 0.5
        assert config.max_tokens == 1024
        assert config.enable_rag is True
        assert config.enable_reflection is True
        assert config.vector_store_path == "/custom/vector"
        assert config.db_path == "/custom/db.sqlite"
        assert config.vision_provider == "claude-vision"
        assert config.max_retries == 5
        assert config.retry_delay == 2.0
        assert config.log_level == LogLevel.DEBUG

    def test_init_with_log_level_string(self) -> None:
        """Test initialization with log level as string."""
        config = QuantChainConfig(log_level="debug")
        assert config.log_level == LogLevel.DEBUG

    def test_init_with_agent_type_none(self) -> None:
        """Test initialization with agent_type=None."""
        config = QuantChainConfig(agent_type=None)
        assert config.agent_type == "default"

    def test_init_with_custom_paths_and_agent_type(self) -> None:
        """Test initialization with custom paths and agent type."""
        config = QuantChainConfig(
            agent_type="test_agent",
            vector_store_path="/test/vector_store",
            db_path="/test/db.sqlite",
        )
        assert config.agent_type == "test_agent"
        assert config.vector_store_path == "/test/vector_store"
        assert config.db_path == "/test/db.sqlite"

    @patch("os.path.exists")
    @patch("builtins.open", new_callable=mock_open)
    def test_init_with_config_file(
        self, mock_file: mock_open, mock_exists: Mock
    ) -> None:
        """Test initialization with config file."""
        mock_exists.return_value = True
        config_data = {
            "agent_type": "file_agent",
            "llm_provider": "anthropic",
            "temperature": 0.3,
            "enable_rag": True,
            "log_level": "warning",
        }
        mock_file.return_value.read.return_value = json.dumps(config_data)

        config = QuantChainConfig(config_file="test_config.json")

        assert config.agent_type == "file_agent"
        assert config.llm_provider == "anthropic"
        assert config.temperature == 0.3
        assert config.enable_rag is True
        assert config.log_level == LogLevel.WARNING

    @patch("os.path.exists")
    @patch("builtins.open", side_effect=IOError("Permission denied"))
    def test_init_with_config_file_error(
        self, mock_file: Mock, mock_exists: Mock
    ) -> None:
        """Test initialization with config file error."""
        mock_exists.return_value = True

        # Should not raise exception, should use defaults
        config = QuantChainConfig(config_file="nonexistent.json")
        assert config.agent_type == "default"

    @patch("os.path.exists", return_value=False)
    def test_init_with_nonexistent_config_file(self, mock_exists: Mock) -> None:
        """Test initialization with nonexistent config file."""
        config = QuantChainConfig(config_file="nonexistent.json")
        assert config.agent_type == "default"

    @patch("os.makedirs")
    def test_directories_creation(self, mock_makedirs: Mock) -> None:
        """Test that data directories are created."""
        config = QuantChainConfig(
            vector_store_path="/test/vector_store/data.db",
            db_path="/test/db/data.sqlite",
        )

        # Should create parent directories
        mock_makedirs.assert_any_call("/test/vector_store", exist_ok=True)
        mock_makedirs.assert_any_call("/test/db", exist_ok=True)

    @patch("os.makedirs")
    def test_init_with_file_load_creates_directories(self, mock_makedirs: Mock) -> None:
        """Test that directories are created when loading from file."""
        with patch("os.path.exists", return_value=True):
            with patch("builtins.open", mock_open(read_data='{"agent_type": "test"}')):
                QuantChainConfig(config_file="test_config.json")

        # Should create parent directories
        mock_makedirs.assert_any_call("./data", exist_ok=True)
        mock_makedirs.assert_any_call("./data", exist_ok=True)

    def test_load_from_file_success(self) -> None:
        """Test successful loading from file."""
        config = QuantChainConfig()
        config_data = {
            "agent_type": "loaded_agent",
            "llm_provider": "anthropic",
            "temperature": 0.9,
            "max_tokens": 4096,
            "enable_rag": True,
            "log_level": "error",
            "custom_field": "custom_value",
        }

        with patch("builtins.open", mock_open(read_data=json.dumps(config_data))):
            config._load_from_file("test_config.json")

        assert config.agent_type == "loaded_agent"
        assert config.llm_provider == "anthropic"
        assert config.temperature == 0.9
        assert config.max_tokens == 4096
        assert config.enable_rag is True
        assert config.log_level == LogLevel.ERROR
        assert hasattr(config, "custom_field")
        assert config.custom_field == "custom_value"

    def test_load_from_file_with_log_level_string(self) -> None:
        """Test loading from file with log level as string."""
        config = QuantChainConfig()
        config_data = {"log_level": "warning"}

        with patch("builtins.open", mock_open(read_data=json.dumps(config_data))):
            config._load_from_file("test_config.json")

        assert config.log_level == LogLevel.WARNING

    def test_load_from_file_error(self) -> None:
        """Test loading from file with error."""
        config = QuantChainConfig()

        with patch("builtins.open", side_effect=IOError("Permission denied")):
            # Should not raise exception
            config._load_from_file("nonexistent.json")

        # Should still have default values
        assert config.agent_type == "default"

    def test_save_to_file_success(self) -> None:
        """Test successful saving to file."""
        config = QuantChainConfig(
            agent_type="test_agent",
            llm_provider="anthropic",
            temperature=0.5,
            enable_rag=True,
            log_level=LogLevel.DEBUG,
        )

        with tempfile.NamedTemporaryFile(
            mode="w", delete=False, suffix=".json"
        ) as temp_file:
            temp_path = temp_file.name

        try:
            config.save_to_file(temp_path)

            # Read and verify the saved content
            with open(temp_path, "r") as f:
                saved_data = json.load(f)

            assert saved_data["agent_type"] == "test_agent"
            assert saved_data["llm_provider"] == "anthropic"
            assert saved_data["temperature"] == 0.5
            assert saved_data["enable_rag"] is True
            assert saved_data["log_level"] == "debug"
        finally:
            os.unlink(temp_path)

    def test_save_to_file_with_enum(self) -> None:
        """Test saving to file with enum values."""
        config = QuantChainConfig(log_level=LogLevel.CRITICAL)

        with tempfile.NamedTemporaryFile(
            mode="w", delete=False, suffix=".json"
        ) as temp_file:
            temp_path = temp_file.name

        try:
            config.save_to_file(temp_path)

            with open(temp_path, "r") as f:
                saved_data = json.load(f)

            assert saved_data["log_level"] == "critical"
        finally:
            os.unlink(temp_path)

    def test_save_to_file_error(self) -> None:
        """Test saving to file with error."""
        config = QuantChainConfig()

        with patch("builtins.open", side_effect=IOError("Permission denied")):
            # Should not raise exception
            config.save_to_file("/invalid/path/config.json")

    def test_get_existing_attribute(self) -> None:
        """Test getting existing attribute."""
        config = QuantChainConfig(agent_type="test_agent")
        result = config.get("agent_type")
        assert result == "test_agent"

    def test_get_nonexistent_attribute_with_default(self) -> None:
        """Test getting nonexistent attribute with default."""
        config = QuantChainConfig()
        result = config.get("nonexistent", "default_value")
        assert result == "default_value"

    def test_get_nonexistent_attribute_no_default(self) -> None:
        """Test getting nonexistent attribute without default."""
        config = QuantChainConfig()
        result = config.get("nonexistent")
        assert result is None

    def test_set_attribute(self) -> None:
        """Test setting attribute."""
        config = QuantChainConfig()
        config.set("custom_field", "custom_value")
        assert config.custom_field == "custom_value"

    def test_set_existing_attribute(self) -> None:
        """Test setting existing attribute."""
        config = QuantChainConfig(temperature=0.5)
        config.set("temperature", 0.9)
        assert config.temperature == 0.9

    def test_to_dict_with_basic_types(self) -> None:
        """Test converting to dict with basic types."""
        config = QuantChainConfig(
            agent_type="test",
            temperature=0.5,
            max_tokens=1024,
            enable_rag=True,
            log_level=LogLevel.DEBUG,
        )

        result = config.to_dict()

        assert result["agent_type"] == "test"
        assert result["temperature"] == 0.5
        assert result["max_tokens"] == 1024
        assert result["enable_rag"] is True
        assert result["log_level"] == "debug"

    def test_to_dict_excludes_private_attributes(self) -> None:
        """Test to_dict excludes private attributes."""
        config = QuantChainConfig()
        config._private_attr = "private_value"
        config.__another_private = "another_private"

        result = config.to_dict()

        assert "_private_attr" not in result
        assert "__another_private" not in result

    def test_to_dict_with_enum(self) -> None:
        """Test to_dict with enum values."""
        config = QuantChainConfig(log_level=LogLevel.WARNING)

        result = config.to_dict()

        assert result["log_level"] == "warning"

    def test_to_dict_with_methods(self) -> None:
        """Test to_dict excludes methods."""
        config = QuantChainConfig()

        result = config.to_dict()

        assert "to_dict" not in result
        assert "get" not in result
        assert "set" not in result
        assert "validate" not in result

    def test_validate_valid_config(self) -> None:
        """Test validation of valid configuration."""
        config = QuantChainConfig(
            llm_provider="openai",
            temperature=0.7,
            max_tokens=2048,
            max_retries=3,
            retry_delay=1.0,
        )

        errors = config.validate()
        assert len(errors) == 0

    def test_validate_empty_llm_provider(self) -> None:
        """Test validation with empty LLM provider."""
        config = QuantChainConfig(llm_provider="")

        errors = config.validate()
        assert "LLM provider is required" in errors

    def test_validate_none_llm_provider(self) -> None:
        """Test validation with None LLM provider."""
        config = QuantChainConfig()
        config.llm_provider = None

        errors = config.validate()
        assert "LLM provider is required" in errors

    def test_validate_temperature_too_low(self) -> None:
        """Test validation with temperature too low."""
        config = QuantChainConfig(temperature=-0.1)

        errors = config.validate()
        assert "Temperature must be between 0 and 2" in errors

    def test_validate_temperature_too_high(self) -> None:
        """Test validation with temperature too high."""
        config = QuantChainConfig(temperature=2.1)

        errors = config.validate()
        assert "Temperature must be between 0 and 2" in errors

    def test_validate_temperature_boundary_values(self) -> None:
        """Test validation with temperature boundary values."""
        # Test lower boundary
        config_low = QuantChainConfig(temperature=0.0)
        errors_low = config_low.validate()
        assert len(errors_low) == 0

        # Test upper boundary
        config_high = QuantChainConfig(temperature=2.0)
        errors_high = config_high.validate()
        assert len(errors_high) == 0

    def test_validate_negative_max_tokens(self) -> None:
        """Test validation with negative max tokens."""
        config = QuantChainConfig(max_tokens=-1)

        errors = config.validate()
        assert "Max tokens must be positive" in errors

    def test_validate_zero_max_tokens(self) -> None:
        """Test validation with zero max tokens."""
        config = QuantChainConfig(max_tokens=0)

        errors = config.validate()
        assert "Max tokens must be positive" in errors

    def test_validate_negative_max_retries(self) -> None:
        """Test validation with negative max retries."""
        config = QuantChainConfig(max_retries=-1)

        errors = config.validate()
        assert "Max retries must be non-negative" in errors

    def test_validate_negative_retry_delay(self) -> None:
        """Test validation with negative retry delay."""
        config = QuantChainConfig(retry_delay=-0.1)

        errors = config.validate()
        assert "Retry delay must be non-negative" in errors

    def test_validate_multiple_errors(self) -> None:
        """Test validation with multiple errors."""
        config = QuantChainConfig(
            llm_provider="",
            temperature=3.0,
            max_tokens=-100,
            max_retries=-5,
            retry_delay=-2.0,
        )

        errors = config.validate()
        assert len(errors) >= 5
        assert "LLM provider is required" in errors
        assert "Temperature must be between 0 and 2" in errors
        assert "Max tokens must be positive" in errors
        assert "Max retries must be non-negative" in errors
        assert "Retry delay must be non-negative" in errors

    def test_config_attributes_serialization(self) -> None:
        """Test that config attributes can be properly serialized."""
        config = QuantChainConfig(
            agent_type="test",
            temperature=0.5,
            enable_rag=True,
            log_level=LogLevel.WARNING,
        )
        # Add custom attributes directly
        config.custom_list = [1, 2, 3]
        config.custom_dict = {"key": "value"}

        # Add custom attribute
        config.custom_field = "custom_value"

        result = config.to_dict()

        assert result["agent_type"] == "test"
        assert result["temperature"] == 0.5
        assert result["enable_rag"] is True
        assert result["log_level"] == "warning"
        assert result["custom_list"] == [1, 2, 3]
        assert result["custom_dict"] == {"key": "value"}
        assert result["custom_field"] == "custom_value"
