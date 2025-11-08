"""Tests for execution interface factory."""

import pytest
from unittest.mock import Mock

from quantchain.core.config import QuantChainConfig
from quantchain.core.exceptions import AuthenticationError, ConfigurationError


class TestExecutionFactory:
    """Test cases for execution interface factory."""

    @pytest.fixture
    def mock_config(self):
        """Create a mock QuantChainConfig."""
        return Mock(spec=QuantChainConfig)

    def test_create_alpaca_paper_trading(self, mock_config):
        """Test creating Alpaca connector in paper trading mode."""

        def mock_get(key, default=None):
            mock_responses = {
                "trading.default_broker": "alpaca",
                "trading.paper_trading": True,
            }
            return mock_responses.get(key, default)

        mock_config.get.side_effect = mock_get
        mock_config.get_api_key.side_effect = lambda key: (
            "test-key" if key == "alpaca" else "test-secret"
        )

        from quantchain.tools.execution_factory import create_execution_interface

        executor = create_execution_interface(mock_config)

        assert hasattr(executor, "use_paper")
        assert executor.use_paper is True

    def test_create_alpaca_live_trading(self, mock_config):
        """Test creating Alpaca connector in live trading mode."""

        def mock_get(key, default=None):
            mock_responses = {
                "trading.default_broker": "alpaca",
                "trading.paper_trading": False,
            }
            return mock_responses.get(key, default)

        mock_config.get.side_effect = mock_get
        mock_config.get_api_key.side_effect = lambda key: (
            "test-key" if key == "alpaca" else "test-secret"
        )

        from quantchain.tools.execution_factory import create_execution_interface

        executor = create_execution_interface(mock_config)

        assert hasattr(executor, "use_paper")
        assert executor.use_paper is False

    def test_create_paper_trading_executor(self, mock_config):
        """Test creating standalone paper trading executor."""

        def mock_get(key, default=None):
            return "paper" if key == "trading.default_broker" else default

        mock_config.get.side_effect = mock_get

        from quantchain.tools.execution_factory import create_execution_interface

        executor = create_execution_interface(mock_config)

        assert hasattr(executor, "initial_cash")
        assert executor.initial_cash == 100000.0

    def test_missing_api_key_for_live_trading(self, mock_config):
        """Test error when API key is missing for live trading."""

        def mock_get(key, default=None):
            mock_responses = {
                "trading.default_broker": "alpaca",
                "trading.paper_trading": False,
            }
            return mock_responses.get(key, default)

        mock_config.get.side_effect = mock_get
        mock_config.get_api_key.return_value = None

        from quantchain.tools.execution_factory import create_execution_interface

        with pytest.raises(AuthenticationError):
            create_execution_interface(mock_config)

    def test_unsupported_broker(self, mock_config):
        """Test error for unsupported broker."""

        def mock_get(key, default=None):
            if key == "trading.default_broker":
                return "unsupported_broker"
            return default

        mock_config.get.side_effect = mock_get

        from quantchain.tools.execution_factory import create_execution_interface

        with pytest.raises(ConfigurationError):
            create_execution_interface(mock_config)
