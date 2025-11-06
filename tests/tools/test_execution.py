"""Tests for Alpaca execution tool."""

import pytest
from unittest.mock import MagicMock, patch

from quantchain.tools.execution import AlpacaExecutionTool
from quantchain.tools.trading_execution import (
    OrderRequest,
    OrderSide,
    OrderType,
    OrderResult,
)


@pytest.mark.unit
class TestAlpacaExecutionTool:
    """Test the AlpacaExecutionTool class."""

    def test_from_credentials_paper_trading(self) -> None:
        """Test tool creation with paper trading."""
        with patch(
            "quantchain.tools.execution.AlpacaExecutionConnector"
        ) as mock_connector_class:
            mock_connector = MagicMock()
            mock_connector_class.return_value = mock_connector

            tool = AlpacaExecutionTool.from_credentials(
                api_key="test_key", api_secret="test_secret", use_paper=True
            )

            assert tool.connector == mock_connector
            mock_connector_class.assert_called_once_with(
                api_key="test_key", api_secret="test_secret", use_paper=True
            )

    def test_from_credentials_live_trading(self) -> None:
        """Test tool creation with live trading."""
        with patch(
            "quantchain.tools.execution.AlpacaExecutionConnector"
        ) as mock_connector_class:
            mock_connector = MagicMock()
            mock_connector_class.return_value = mock_connector

            tool = AlpacaExecutionTool.from_credentials(
                api_key="live_key",
                api_secret="live_secret",
                use_paper=False,
                timeout=30,
            )

            assert tool.connector == mock_connector
            mock_connector_class.assert_called_once_with(
                api_key="live_key",
                api_secret="live_secret",
                use_paper=False,
                timeout=30,
            )

    def test_from_credentials_with_kwargs(self) -> None:
        """Test tool creation passes through additional kwargs."""
        with patch(
            "quantchain.tools.execution.AlpacaExecutionConnector"
        ) as mock_connector_class:
            mock_connector = MagicMock()
            mock_connector_class.return_value = mock_connector

            tool = AlpacaExecutionTool.from_credentials(
                api_key="key",
                api_secret="secret",
                custom_param="value",
                another_param=123,
            )

            assert tool.connector == mock_connector
            mock_connector_class.assert_called_once_with(
                api_key="key",
                api_secret="secret",
                use_paper=True,
                custom_param="value",
                another_param=123,
            )

    def test_execute_market_order_buy(self) -> None:
        """Test market order execution for buy side."""
        # Setup mock connector and tool directly
        mock_connector = MagicMock()
        mock_result = OrderResult(
            order_id="order_123", status="filled", filled_quantity=100.0, price=50.25
        )
        mock_connector.submit_market_order.return_value = mock_result

        tool = AlpacaExecutionTool(connector=mock_connector)

        result = tool.execute_market_order("AAPL", "buy", 100.0)

        assert result == mock_result
        mock_connector.submit_market_order.assert_called_once()

        # Check the order request passed to connector
        call_args = mock_connector.submit_market_order.call_args[0][0]
        assert isinstance(call_args, OrderRequest)
        assert call_args.symbol == "AAPL"
        assert call_args.side == OrderSide.BUY
        assert call_args.quantity == 100.0
        assert call_args.order_type == OrderType.MARKET

    @patch.object(AlpacaExecutionTool, "connector")
    def test_execute_market_order_sell(self, mock_connector) -> None:
        """Test market order execution for sell side."""
        # Setup mock connector
        mock_order = MagicMock()
        mock_result = OrderResult(
            order_id="order_456", status="filled", filled_quantity=50.0, price=75.50
        )
        mock_connector.submit_market_order.return_value = mock_result

        tool = AlpacaExecutionTool(connector=mock_connector)

        result = tool.execute_market_order("TSLA", "sell", 50.0)

        assert result == mock_result
        mock_connector.submit_market_order.assert_called_once()

        # Check the order request passed to connector
        call_args = mock_connector.submit_market_order.call_args[0][0]
        assert call_args.symbol == "TSLA"
        assert call_args.side == OrderSide.SELL
        assert call_args.quantity == 50.0
        assert call_args.order_type == OrderType.MARKET

    @patch.object(AlpacaExecutionTool, "connector")
    def test_execute_market_order_connector_error(self, mock_connector) -> None:
        """Test handling of connector errors during order execution."""
        from quantchain.core.exceptions import TradingError

        mock_connector.submit_market_order.side_effect = TradingError("API error")

        tool = AlpacaExecutionTool(connector=mock_connector)

        with pytest.raises(TradingError, match="API error"):
            tool.execute_market_order("BTC", "buy", 1.0)

    def test_tool_dataclass_structure(self) -> None:
        """Test that tool maintains proper dataclass structure."""
        mock_connector = MagicMock()
        tool = AlpacaExecutionTool(connector=mock_connector)

        assert hasattr(tool, "connector")
        assert tool.connector == mock_connector

    @patch.object(AlpacaExecutionTool, "connector")
    def test_execute_market_order_parameters(self, mock_connector) -> None:
        """Test various parameter combinations for market orders."""
        mock_result = OrderResult(order_id="test", status="submitted")
        mock_connector.submit_market_order.return_value = mock_result

        tool = AlpacaExecutionTool(connector=mock_connector)

        # Test with symbol variations
        tool.execute_market_order("BTC/USD", "buy", 0.5)
        tool.execute_market_order("ETH-USD", "sell", 2.0)

        assert mock_connector.submit_market_order.call_count == 2

        # Verify the calls used correct order types
        first_call = mock_connector.submit_market_order.call_args_list[0][0]
        second_call = mock_connector.submit_market_order.call_args_list[1][0]

        assert first_call.order_type == OrderType.MARKET
        assert second_call.order_type == OrderType.MARKET


@pytest.mark.unit
class TestAlpacaExecutionToolIntegration:
    """Integration tests for AlpacaExecutionTool."""

    def test_tool_lifecycle(self) -> None:
        """Test complete tool lifecycle from creation to execution."""
        with patch(
            "quantchain.tools.execution.AlpacaExecutionConnector"
        ) as mock_connector_class:
            mock_connector = MagicMock()
            mock_result = OrderResult(
                order_id="lifecycle_test",
                status="filled",
                filled_quantity=10.0,
                price=100.0,
            )
            mock_connector.submit_market_order.return_value = mock_result
            mock_connector_class.return_value = mock_connector

            # Create tool
            tool = AlpacaExecutionTool.from_credentials(
                api_key="test_key", api_secret="test_secret"
            )

            # Execute order
            result = tool.execute_market_order("TEST", "buy", 10.0)

            # Verify complete flow
            assert tool.connector == mock_connector
            assert result == mock_result
            mock_connector_class.assert_called_once()
            mock_connector.submit_market_order.assert_called_once()

    def test_error_propagation(self) -> None:
        """Test that connector errors are properly propagated."""
        with patch(
            "quantchain.tools.execution.AlpacaExecutionConnector"
        ) as mock_connector_class:
            mock_connector = MagicMock()
            mock_connector.submit_market_order.side_effect = ExecutionError(
                "Network error"
            )
            mock_connector_class.return_value = mock_connector

            tool = AlpacaExecutionTool.from_credentials("key", "secret")

            # Error should propagate up
            with pytest.raises(ExecutionError, match="Network error"):
                tool.execute_market_order("FAIL", "sell", 1.0)
