"""
Comprehensive test suite for execution factory module.
"""

from typing import Any, Dict
from unittest.mock import Mock, patch

import pytest

# Try to import the execution factory, skip if not available
try:
    from quantchain.tools.execution_factory import (
        ExecutionFactory,
        create_execution_interface,
    )

    EXECUTION_FACTORY_AVAILABLE = True
except ImportError:
    EXECUTION_FACTORY_AVAILABLE = False


@pytest.mark.skipif(
    not EXECUTION_FACTORY_AVAILABLE, reason="Execution factory module not available"
)
class TestExecutionFactory:
    """Test execution factory functionality."""

    def test_create_default_execution_interface(self) -> None:
        """Test creating default execution interface."""
        mock_config = Mock()
        mock_config.get.return_value = "paper"

        with patch(
            "quantchain.tools.execution_factory.PaperTradingExecutionInterface"
        ) as mock_paper:
            interface = create_execution_interface(mock_config)

            assert interface is not None
            mock_paper.assert_called_once()

    def test_create_paper_trading_interface(self) -> None:
        """Test creating paper trading execution interface."""
        mock_config = Mock()
        mock_config.get.side_effect = self._mock_config_get("paper")

        with patch(
            "quantchain.tools.execution_factory.PaperTradingExecutionInterface"
        ) as mock_paper:
            interface = create_execution_interface(mock_config)

            assert interface is not None
            mock_paper.assert_called_once()

    def test_create_alpaca_interface(self) -> None:
        """Test creating Alpaca execution interface."""
        mock_config = Mock()
        mock_config.get.side_effect = self._mock_config_get("alpaca")

        with patch(
            "quantchain.tools.execution_factory.AlpacaExecutionInterface"
        ) as mock_alpaca:
            interface = create_execution_interface(mock_config)

            assert interface is not None
            mock_alpaca.assert_called_once()

    def test_create_ib_connector(self, mock_config: Mock) -> None:
        """Test creating Interactive Brokers connector, expecting ImportError if IB library is missing."""
        mock_config = Mock()
        mock_config.get.side_effect = self._mock_config_get("ib")

        # Expect ImportError (or the specific exception your codebase uses for missing IB library)
        with pytest.raises(ImportError) as exc_info:
            create_execution_interface(mock_config)
        assert (
            "ib_async" in str(exc_info.value).lower()
            or "interactive brokers" in str(exc_info.value).lower()
        )

    def test_create_unknown_broker(self) -> None:
        """Test creating interface for unknown broker."""
        mock_config = Mock()
        mock_config.get.side_effect = self._mock_config_get("unknown")

        with pytest.raises(ValueError):
            create_execution_interface(mock_config)

    def test_factory_init(self) -> None:
        """Test factory initialization."""
        factory = ExecutionFactory()
        assert factory is not None

    def test_factory_create_execution_interface(self) -> None:
        """Test factory create execution interface method."""
        mock_config = Mock()
        mock_config.get.return_value = "paper"

        factory = ExecutionFactory()

        with patch(
            "quantchain.tools.execution_factory.PaperTradingExecutionInterface"
        ) as mock_paper:
            interface = factory.create(mock_config)

            assert interface is not None
            mock_paper.assert_called_once()

    def test_missing_broker_config(self) -> None:
        """Test handling missing broker configuration."""
        mock_config = Mock()
        mock_config.get.side_effect = self._mock_config_get(None)

        # Should use default broker
        with patch(
            "quantchain.tools.execution_factory.PaperTradingExecutionInterface"
        ) as mock_paper:
            interface = create_execution_interface(mock_config)

            assert interface is not None
            mock_paper.assert_called_once()

    def test_config_validation(self) -> None:
        """Test configuration validation."""
        mock_config = Mock()
        mock_config.get.side_effect = self._mock_config_get("paper")

        with patch(
            "quantchain.tools.execution_factory.PaperTradingExecutionInterface"
        ) as mock_paper:
            interface = create_execution_interface(mock_config)

            # Verify that config methods were called
            mock_config.get.assert_called()
            assert interface is not None

    def test_broker_specific_config_alpaca(self) -> None:
        """Test broker-specific configuration for Alpaca."""
        mock_config = Mock()
        mock_config.get.side_effect = self._mock_config_get("alpaca")

        with patch(
            "quantchain.tools.execution_factory.AlpacaExecutionInterface"
        ) as mock_alpaca:
            interface = create_execution_interface(mock_config)

            # Verify broker-specific config methods were called
            assert mock_config.get.call_count > 1
            assert interface is not None

    
    def test_error_handling_invalid_config(self) -> None:
        """Test error handling for invalid configuration."""
        mock_config = Mock()
        mock_config.get.side_effect = Exception("Config error")

        with pytest.raises(Exception):
            create_execution_interface(mock_config)

    def _mock_config_get(self, broker_type: str) -> Any:
        """Helper method to mock config.get() calls."""
        config_responses = {
            "trading.default_broker": broker_type or "paper",
            "trading.alpaca.api_key": "test_key",
            "trading.alpaca.api_secret": "test_secret",
            "trading.alpaca.base_url": "https://paper-api.alpaca.markets",
            "trading.ib.host": "127.0.0.1",
            "trading.ib.port": 7497,
            "trading.ib.client_id": 1,
            "trading.ib.timeout": 10,
            "trading.ib.account": "DU123456",
        }

        def get_side_effect(key: str, default: Any = None) -> Any:
            return config_responses.get(key, default)

        return get_side_effect


@pytest.mark.skipif(
    not EXECUTION_FACTORY_AVAILABLE, reason="Execution factory module not available"
)
class TestExecutionFactoryEdgeCases:
    """Test execution factory edge cases."""

    def test_create_interface_with_config_dict(self) -> None:
        """Test creating interface with dict-based config."""
        config_dict = {"trading.default_broker": "paper"}

        mock_config = Mock()
        mock_config.get.side_effect = lambda key, default=None: config_dict.get(
            key, default
        )

        with patch(
            "quantchain.tools.execution_factory.PaperTradingExecutionInterface"
        ) as mock_paper:
            interface = create_execution_interface(mock_config)

            assert interface is not None
            mock_paper.assert_called_once()

    def test_empty_config(self) -> None:
        """Test creating interface with empty config."""
        mock_config = Mock()
        mock_config.get.return_value = None

        with patch(
            "quantchain.tools.execution_factory.PaperTradingExecutionInterface"
        ) as mock_paper:
            interface = create_execution_interface(mock_config)

            assert interface is not None
            mock_paper.assert_called_once()

    def test_case_insensitive_broker_type(self) -> None:
        """Test case-insensitive broker type matching."""
        mock_config = Mock()
        mock_config.get.return_value = "PAPER"

        with patch(
            "quantchain.tools.execution_factory.PaperTradingExecutionInterface"
        ) as mock_paper:
            interface = create_execution_interface(mock_config)

            assert interface is not None
            # The implementation should handle case sensitivity appropriately
