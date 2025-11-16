"""Simple tests for TradingExecution to improve coverage."""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime

try:
    from quantchain.tools.trading_execution import TradingExecution

    TRADING_EXECUTION_AVAILABLE = True
except ImportError as e:
    TRADING_EXECUTION_AVAILABLE = False
    print(f"Import error: {e}")

pytestmark = pytest.mark.skipif(
    not TRADING_EXECUTION_AVAILABLE, reason="TradingExecution not available"
)


class TestTradingExecution:
    """Tests for TradingExecution."""

    @pytest.fixture
    def config(self):
        """Create test configuration."""
        return {
            "alpaca": {
                "api_key": "test_key",
                "secret_key": "test_secret",
                "base_url": "https://paper-api.alpaca.markets",
            }
        }

    def test_initialization(self, config):
        """Test TradingExecution initialization."""
        if TRADING_EXECUTION_AVAILABLE:
            execution = TradingExecution(config)
            assert execution is not None
            assert hasattr(execution, "config")

    def test_place_order_buy(self, config):
        """Test placing a BUY order."""
        if TRADING_EXECUTION_AVAILABLE:
            execution = TradingExecution(config)

            # Mock the actual API call
            with patch.object(execution, "_execute_order") as mock_execute:
                mock_execute.return_value = {
                    "order_id": "12345",
                    "status": "filled",
                    "symbol": "AAPL",
                    "side": "buy",
                    "qty": 100,
                    "filled_avg_price": 150.0,
                }

                # Place order
                result = execution.place_order(
                    symbol="AAPL",
                    side="buy",
                    quantity=100,
                    order_type="market",
                    time_in_force="day",
                )

                # Check result
                assert result["status"] == "filled"
                assert result["symbol"] == "AAPL"
                assert result["side"] == "buy"
                mock_execute.assert_called_once()

    def test_place_order_sell(self, config):
        """Test placing a SELL order."""
        if TRADING_EXECUTION_AVAILABLE:
            execution = TradingExecution(config)

            # Mock the actual API call
            with patch.object(execution, "_execute_order") as mock_execute:
                mock_execute.return_value = {
                    "order_id": "12345",
                    "status": "filled",
                    "symbol": "AAPL",
                    "side": "sell",
                    "qty": 100,
                    "filled_avg_price": 150.0,
                }

                # Place order
                result = execution.place_order(
                    symbol="AAPL",
                    side="sell",
                    quantity=100,
                    order_type="market",
                    time_in_force="day",
                )

                # Check result
                assert result["status"] == "filled"
                assert result["symbol"] == "AAPL"
                assert result["side"] == "sell"
                mock_execute.assert_called_once()

    def test_get_positions(self, config):
        """Test getting current positions."""
        if TRADING_EXECUTION_AVAILABLE:
            execution = TradingExecution(config)

            # Mock the actual API call
            with patch.object(execution, "_get_positions") as mock_get:
                mock_get.return_value = [
                    {
                        "symbol": "AAPL",
                        "side": "long",
                        "qty": 100,
                        "market_value": 15000.0,
                    }
                ]

                # Get positions
                positions = execution.get_positions()

                # Check result
                assert len(positions) == 1
                assert positions[0]["symbol"] == "AAPL"
                assert positions[0]["side"] == "long"
                mock_get.assert_called_once()

    def test_error_handling(self, config):
        """Test error handling."""
        if TRADING_EXECUTION_AVAILABLE:
            execution = TradingExecution(config)

            # Mock the actual API call to raise an exception
            with patch.object(execution, "_execute_order") as mock_execute:
                mock_execute.side_effect = Exception("API error")

                # Check that method handles the error
                with pytest.raises(Exception):
                    execution.place_order(
                        symbol="AAPL",
                        side="buy",
                        quantity=100,
                        order_type="market",
                        time_in_force="day",
                    )
