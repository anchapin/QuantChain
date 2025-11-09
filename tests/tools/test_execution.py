"""Tests for Alpaca execution tool."""

import pytest
from datetime import datetime
from unittest.mock import MagicMock, patch

from quantchain.tools.execution import AlpacaExecutionTool
from quantchain.tools.trading_execution import (
    OrderRequest,
    OrderSide,
    OrderType,
    OrderResult,
    OrderStatus,
    ExecutionError,
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
            order_id="order_123",
            client_order_id="client_123",
            symbol="AAPL",
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=100.0,
            filled_quantity=100.0,
            price=50.25,
            stop_price=None,
            avg_fill_price=50.25,
            status=OrderStatus.FILLED,
            timestamp=datetime.now(),
        )
        mock_connector.place_order.return_value = mock_result

        tool = AlpacaExecutionTool(connector=mock_connector)

        result = tool.execute_market_order("AAPL", "buy", 100.0)

        assert result == mock_result
        mock_connector.place_order.assert_called_once()

        # Check the order request passed to connector
        call_args = mock_connector.place_order.call_args[0][0]
        assert isinstance(call_args, OrderRequest)
        assert call_args.symbol == "AAPL"
        assert call_args.side == OrderSide.BUY
        assert call_args.quantity == 100.0
        assert call_args.order_type == OrderType.MARKET

    def test_execute_market_order_sell(self) -> None:
        """Test market order execution for sell side."""
        # Setup mock connector
        mock_connector = MagicMock()
        mock_result = OrderResult(
            order_id="order_456",
            client_order_id="client_456",
            symbol="TSLA",
            side=OrderSide.SELL,
            order_type=OrderType.MARKET,
            quantity=50.0,
            filled_quantity=50.0,
            price=75.50,
            stop_price=None,
            avg_fill_price=75.50,
            status=OrderStatus.FILLED,
            timestamp=datetime.now(),
        )
        mock_connector.place_order.return_value = mock_result

        tool = AlpacaExecutionTool(connector=mock_connector)

        result = tool.execute_market_order("TSLA", "sell", 50.0)

        assert result == mock_result
        mock_connector.place_order.assert_called_once()

        # Check the connector method call details
        call_args = mock_connector.place_order.call_args[0][0]
        assert call_args.symbol == "TSLA"
        assert call_args.side == OrderSide.SELL
        assert call_args.quantity == 50.0
        assert call_args.order_type == OrderType.MARKET

    def test_execute_market_order_connector_error(self) -> None:
        """Test handling of connector errors during order execution."""
        from quantchain.tools.trading_execution import ExecutionError

        mock_connector = MagicMock()
        mock_connector.place_order.side_effect = ExecutionError("API error")

        tool = AlpacaExecutionTool(connector=mock_connector)

        with pytest.raises(ExecutionError, match="API error"):
            tool.execute_market_order("BTC", "buy", 1.0)

    def test_tool_dataclass_structure(self) -> None:
        """Test that tool maintains proper dataclass structure."""
        mock_connector = MagicMock()
        tool = AlpacaExecutionTool(connector=mock_connector)

        assert hasattr(tool, "connector")
        assert tool.connector == mock_connector

    def test_execute_market_order_parameters(self) -> None:
        """Test various parameter combinations for market orders."""
        mock_connector = MagicMock()
        mock_result = OrderResult(
            order_id="test",
            client_order_id="test_client",
            symbol="BTC",
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=1.0,
            filled_quantity=1.0,
            price=50000.0,
            stop_price=None,
            avg_fill_price=50000.0,
            status=OrderStatus.FILLED,
            timestamp=datetime.now(),
        )
        mock_connector.place_order.return_value = mock_result

        tool = AlpacaExecutionTool(connector=mock_connector)

        # Test with symbol variations
        tool.execute_market_order("BTC/USD", "buy", 0.5)
        tool.execute_market_order("ETH-USD", "sell", 2.0)

        assert mock_connector.place_order.call_count == 2

        # Verify the calls used correct order types
        first_call_args = mock_connector.place_order.call_args_list[0]
        second_call_args = mock_connector.place_order.call_args_list[1]

        # Extract OrderRequest objects from call args
        first_order_request = first_call_args.args[0]
        second_order_request = second_call_args.args[0]
        # Extract OrderRequest objects from call args
        first_order_request = first_call_args.args[0]
        second_order_request = second_call_args.args[0]

        assert first_order_request.order_type == OrderType.MARKET
        assert second_order_request.order_type == OrderType.MARKET

    def test_execute_market_order_invalid_side(self) -> None:
        """Test ValueError is raised for invalid order sides."""
        mock_connector = MagicMock()
        tool = AlpacaExecutionTool(connector=mock_connector)

        # Test various invalid side values that should raise ValueError
        # Note: "BUY" and "SELL" are actually valid
        # (they get normalized to "buy" and "sell")
        invalid_sides = [
            "invalid",
            "hold",
            "",
            "  ",
            "buy_more",
            "sell_now",
            "long",
            "short",
        ]

        for invalid_side in invalid_sides:
            with pytest.raises(ValueError, match="Invalid side"):
                tool.execute_market_order("AAPL", invalid_side, 10.0)

    def test_execute_market_order_valid_case_insensitive(self) -> None:
        """Test that valid sides work regardless of case."""
        mock_connector = MagicMock()
        mock_result = OrderResult(
            order_id="order_123",
            client_order_id="client_123",
            symbol="AAPL",
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=100.0,
            filled_quantity=100.0,
            price=50.25,
            stop_price=None,
            avg_fill_price=50.25,
            status=OrderStatus.FILLED,
            timestamp=datetime.now(),
        )
        mock_connector.place_order.return_value = mock_result

        tool = AlpacaExecutionTool(connector=mock_connector)

        # Test that case-insensitive valid sides work
        valid_sides: list[float] = ["buy", "BUY", "Buy", "bUy", "sell", "SELL", "Sell", "sElL"]

        for valid_side in valid_sides:
            result = tool.execute_market_order("AAPL", valid_side, 10.0)
            assert result == mock_result

        # Verify all calls were made
        assert mock_connector.place_order.call_count == len(valid_sides)

    def test_get_account_balance(self) -> None:
        """Test get_account_balance method."""
        # Setup mock account data
        mock_account = MagicMock()
        mock_account.buying_power = 100000.0
        mock_account.cash = 50000.0
        mock_account.portfolio_value = 75000.0
        mock_account.total_equity = 125000.0

        mock_connector = MagicMock()
        mock_connector.get_account.return_value = mock_account

        tool = AlpacaExecutionTool(connector=mock_connector)

        result = tool.get_account_balance()

        expected_result = {
            "buying_power": 100000.0,
            "cash": 50000.0,
            "portfolio_value": 75000.0,
            "total_equity": 125000.0,
        }

        assert result == expected_result
        mock_connector.get_account.assert_called_once()

    def test_get_positions(self) -> None:
        """Test get_positions method."""
        # Setup mock positions data
        mock_position1 = MagicMock()
        mock_position1.symbol = "AAPL"
        mock_position1.quantity = 100.0
        mock_position1.avg_entry_price = 150.0
        mock_position1.current_price = 155.0
        mock_position1.market_value = 15500.0
        mock_position1.unrealized_pnl = 500.0
        mock_position1.unrealized_pnl_percent = 3.33

        mock_position2 = MagicMock()
        mock_position2.symbol = "TSLA"
        mock_position2.quantity = 50.0
        mock_position2.avg_entry_price = 200.0
        mock_position2.current_price = 195.0
        mock_position2.market_value = 9750.0
        mock_position2.unrealized_pnl = -250.0
        mock_position2.unrealized_pnl_percent = -2.5

        mock_positions: list[float] = [mock_position1, mock_position2]

        mock_connector = MagicMock()
        mock_connector.get_positions.return_value = mock_positions

        tool = AlpacaExecutionTool(connector=mock_connector)

        result = tool.get_positions()

        expected_result = [
            {
                "symbol": "AAPL",
                "quantity": 100.0,
                "avg_entry_price": 150.0,
                "current_price": 155.0,
                "market_value": 15500.0,
                "unrealized_pnl": 500.0,
                "unrealized_pnl_percent": 3.33,
            },
            {
                "symbol": "TSLA",
                "quantity": 50.0,
                "avg_entry_price": 200.0,
                "current_price": 195.0,
                "market_value": 9750.0,
                "unrealized_pnl": -250.0,
                "unrealized_pnl_percent": -2.5,
            },
        ]

        assert result == expected_result
        mock_connector.get_positions.assert_called_once()

    def test_get_account_balance_connector_error(self) -> None:
        """Test handling of connector errors in get_account_balance."""
        from quantchain.tools.trading_execution import ExecutionError

        mock_connector = MagicMock()
        mock_connector.get_account.side_effect = ExecutionError("API error")

        tool = AlpacaExecutionTool(connector=mock_connector)

        with pytest.raises(ExecutionError, match="API error"):
            tool.get_account_balance()

    def test_get_positions_connector_error(self) -> None:
        """Test handling of connector errors in get_positions."""
        from quantchain.tools.trading_execution import ExecutionError

        mock_connector = MagicMock()
        mock_connector.get_positions.side_effect = ExecutionError("API error")

        tool = AlpacaExecutionTool(connector=mock_connector)

        with pytest.raises(ExecutionError, match="API error"):
            tool.get_positions()

    def test_get_account_balance_empty_positions(self) -> None:
        """Test get_account_balance with empty/zero values."""
        mock_account = MagicMock()
        mock_account.buying_power = 0.0
        mock_account.cash = 0.0
        mock_account.portfolio_value = 0.0
        mock_account.total_equity = 0.0

        mock_connector = MagicMock()
        mock_connector.get_account.return_value = mock_account

        tool = AlpacaExecutionTool(connector=mock_connector)

        result = tool.get_account_balance()

        expected_result = {
            "buying_power": 0.0,
            "cash": 0.0,
            "portfolio_value": 0.0,
            "total_equity": 0.0,
        }

        assert result == expected_result

    def test_get_positions_empty_list(self) -> None:
        """Test get_positions when no positions exist."""
        mock_connector = MagicMock()
        mock_connector.get_positions.return_value: list[float] = []

        tool = AlpacaExecutionTool(connector=mock_connector)

        result = tool.get_positions()

        assert result == []
        mock_connector.get_positions.assert_called_once()


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
                client_order_id="lifecycle_client",
                symbol="TEST",
                side=OrderSide.BUY,
                order_type=OrderType.MARKET,
                quantity=10.0,
                filled_quantity=10.0,
                price=100.0,
                stop_price=None,
                avg_fill_price=100.0,
                status=OrderStatus.FILLED,
                timestamp=datetime.now(),
            )
            mock_connector.place_order.return_value = mock_result
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
            mock_connector.place_order.assert_called_once()

    def test_error_propagation(self) -> None:
        """Test that connector errors are properly propagated."""
        with patch(
            "quantchain.tools.execution.AlpacaExecutionConnector"
        ) as mock_connector_class:
            mock_connector = MagicMock()
            mock_connector.place_order.side_effect = ExecutionError("Network error")
            mock_connector_class.return_value = mock_connector

            tool = AlpacaExecutionTool.from_credentials("key", "secret")

            # Error should propagate up
            with pytest.raises(ExecutionError, match="Network error"):
                tool.execute_market_order("FAIL", "sell", 1.0)


