"""Comprehensive tests for execution module."""

from unittest.mock import MagicMock, patch

import pytest

from quantchain.connectors.alpaca_execution import AlpacaExecutionConnector
from quantchain.tools.execution import AlpacaExecutionTool
from quantchain.tools.trading_execution import (
    AccountInfo,
    ExecutionError,
    OrderRequest,
    OrderResult,
    OrderSide,
    OrderStatus,
    OrderType,
    Position,
)


@pytest.mark.unit
class TestAlpacaExecutionTool:
    """Test AlpacaExecutionTool class."""

    def test_init(self):
        """Test AlpacaExecutionTool initialization."""
        mock_connector = MagicMock(spec=AlpacaExecutionConnector)
        tool = AlpacaExecutionTool(connector=mock_connector)
        assert tool.connector == mock_connector

    def test_from_credentials(self):
        """Test creating tool from credentials."""
        with patch(
            "quantchain.tools.execution.AlpacaExecutionConnector"
        ) as mock_connector_class:
            mock_connector = MagicMock()
            mock_connector_class.return_value = mock_connector

            tool = AlpacaExecutionTool.from_credentials(
                api_key="test_key",
                api_secret="test_secret",
                use_paper=True,
                additional_param="test",
            )

            assert tool.connector == mock_connector
            mock_connector_class.assert_called_once_with(
                api_key="test_key",
                api_secret="test_secret",
                use_paper=True,
                additional_param="test",
            )

    def test_from_credentials_default_paper(self):
        """Test creating tool from credentials with default paper trading."""
        with patch(
            "quantchain.tools.execution.AlpacaExecutionConnector"
        ) as mock_connector_class:
            mock_connector = MagicMock()
            mock_connector_class.return_value = mock_connector

            tool = AlpacaExecutionTool.from_credentials(
                api_key="test_key", api_secret="test_secret"
            )

            mock_connector_class.assert_called_once_with(
                api_key="test_key", api_secret="test_secret", use_paper=True
            )

    def test_execute_market_order_buy(self):
        """Test executing a buy market order."""
        mock_connector = MagicMock()
        mock_order_result = MagicMock(spec=OrderResult)
        mock_order_result.order_id = "test_order_id"
        mock_connector.place_order.return_value = mock_order_result

        tool = AlpacaExecutionTool(connector=mock_connector)
        result = tool.execute_market_order("AAPL", "buy", 100)

        assert result == mock_order_result
        mock_connector.place_order.assert_called_once()

        # Check the order request
        call_args = mock_connector.place_order.call_args[0][0]
        assert isinstance(call_args, OrderRequest)
        assert call_args.symbol == "AAPL"
        assert call_args.side == OrderSide.BUY
        assert call_args.order_type == OrderType.MARKET
        assert call_args.quantity == 100

    def test_execute_market_order_sell(self):
        """Test executing a sell market order."""
        mock_connector = MagicMock()
        mock_order_result = MagicMock(spec=OrderResult)
        mock_connector.place_order.return_value = mock_order_result

        tool = AlpacaExecutionTool(connector=mock_connector)
        result = tool.execute_market_order("AAPL", "SELL", 50)

        assert result == mock_order_result
        mock_connector.place_order.assert_called_once()

        # Check the order request
        call_args = mock_connector.place_order.call_args[0][0]
        assert call_args.side == OrderSide.SELL
        assert call_args.quantity == 50

    def test_execute_market_order_invalid_side(self):
        """Test executing market order with invalid side."""
        mock_connector = MagicMock()
        tool = AlpacaExecutionTool(connector=mock_connector)

        with pytest.raises(ValueError, match="Invalid side: invalid"):
            tool.execute_market_order("AAPL", "invalid", 100)

    def test_execute_market_order_whitespace_side(self):
        """Test executing market order with whitespace in side."""
        mock_connector = MagicMock()
        mock_order_result = MagicMock(spec=OrderResult)
        mock_connector.place_order.return_value = mock_order_result

        tool = AlpacaExecutionTool(connector=mock_connector)
        result = tool.execute_market_order("AAPL", "  BUY  ", 100)

        assert result == mock_order_result
        call_args = mock_connector.place_order.call_args[0][0]
        assert call_args.side == OrderSide.BUY

    def test_execute_market_order_case_insensitive_side(self):
        """Test executing market order with case insensitive side."""
        mock_connector = MagicMock()
        mock_order_result = MagicMock(spec=OrderResult)
        mock_connector.place_order.return_value = mock_order_result

        tool = AlpacaExecutionTool(connector=mock_connector)
        result = tool.execute_market_order("AAPL", "Buy", 100)

        assert result == mock_order_result
        call_args = mock_connector.place_order.call_args[0][0]
        assert call_args.side == OrderSide.BUY

    def test_execute_market_order_execution_error(self):
        """Test executing market order when connector raises ExecutionError."""
        mock_connector = MagicMock()
        mock_connector.place_order.side_effect = ExecutionError("Execution failed")

        tool = AlpacaExecutionTool(connector=mock_connector)

        with pytest.raises(ExecutionError, match="Execution failed"):
            tool.execute_market_order("AAPL", "buy", 100)

    def test_get_account_balance(self):
        """Test getting account balance."""
        mock_connector = MagicMock()
        mock_account = MagicMock(spec=AccountInfo)
        mock_account.buying_power = 50000.0
        mock_account.cash = 40000.0
        mock_account.portfolio_value = 60000.0
        mock_account.total_equity = 100000.0
        mock_connector.get_account.return_value = mock_account

        tool = AlpacaExecutionTool(connector=mock_connector)
        balance = tool.get_account_balance()

        assert balance == {
            "buying_power": 50000.0,
            "cash": 40000.0,
            "portfolio_value": 60000.0,
            "total_equity": 100000.0,
        }
        mock_connector.get_account.assert_called_once()

    def test_get_positions(self):
        """Test getting positions."""
        mock_connector = MagicMock()
        mock_positions = [MagicMock(spec=Position), MagicMock(spec=Position)]
        mock_positions[0].symbol = "AAPL"
        mock_positions[0].quantity = 100.0
        mock_positions[0].market_value = 15000.0
        mock_positions[0].cost_basis = 12000.0

        mock_positions[1].symbol = "GOOGL"
        mock_positions[1].quantity = 10.0
        mock_positions[1].market_value = 15000.0
        mock_positions[1].cost_basis = 14000.0

        mock_connector.get_positions.return_value = mock_positions

        tool = AlpacaExecutionTool(connector=mock_connector)
        positions = tool.get_positions()

        assert len(positions) == 2
        assert positions[0]["symbol"] == "AAPL"
        assert positions[0]["quantity"] == 100.0
        assert positions[0]["market_value"] == 15000.0
        assert positions[0]["cost_basis"] == 12000.0

        assert positions[1]["symbol"] == "GOOGL"
        assert positions[1]["quantity"] == 10.0
        assert positions[1]["market_value"] == 15000.0
        assert positions[1]["cost_basis"] == 14000.0

    def test_get_positions_empty(self):
        """Test getting positions when there are none."""
        mock_connector = MagicMock()
        mock_connector.get_positions.return_value = []

        tool = AlpacaExecutionTool(connector=mock_connector)
        positions = tool.get_positions()

        assert positions == []

    def test_get_positions_connector_error(self):
        """Test getting positions when connector raises error."""
        mock_connector = MagicMock()
        mock_connector.get_positions.side_effect = ExecutionError(
            "Failed to get positions"
        )

        tool = AlpacaExecutionTool(connector=mock_connector)

        with pytest.raises(ExecutionError, match="Failed to get positions"):
            tool.get_positions()


@pytest.mark.unit
class TestAlpacaExecutionToolEdgeCases:
    """Test edge cases for AlpacaExecutionTool."""

    def test_execute_market_order_zero_quantity(self):
        """Test executing market order with zero quantity."""
        mock_connector = MagicMock()
        mock_order_result = MagicMock(spec=OrderResult)
        mock_connector.place_order.return_value = mock_order_result

        tool = AlpacaExecutionTool(connector=mock_connector)
        result = tool.execute_market_order("AAPL", "buy", 0)

        assert result == mock_order_result
        call_args = mock_connector.place_order.call_args[0][0]
        assert call_args.quantity == 0

    def test_execute_market_order_negative_quantity(self):
        """Test executing market order with negative quantity."""
        mock_connector = MagicMock()
        mock_order_result = MagicMock(spec=OrderResult)
        mock_connector.place_order.return_value = mock_order_result

        tool = AlpacaExecutionTool(connector=mock_connector)
        result = tool.execute_market_order("AAPL", "sell", -50)

        assert result == mock_order_result
        call_args = mock_connector.place_order.call_args[0][0]
        assert call_args.quantity == -50

    def test_execute_market_order_float_quantity(self):
        """Test executing market order with float quantity."""
        mock_connector = MagicMock()
        mock_order_result = MagicMock(spec=OrderResult)
        mock_connector.place_order.return_value = mock_order_result

        tool = AlpacaExecutionTool(connector=mock_connector)
        result = tool.execute_market_order("AAPL", "buy", 1.5)

        assert result == mock_order_result
        call_args = mock_connector.place_order.call_args[0][0]
        assert call_args.quantity == 1.5

    def test_get_account_balance_negative_values(self):
        """Test getting account balance with negative values (margin)."""
        mock_connector = MagicMock()
        mock_account = MagicMock(spec=AccountInfo)
        mock_account.buying_power = -10000.0  # Negative buying power (margin)
        mock_account.cash = 0.0
        mock_account.portfolio_value = 50000.0
        mock_account.total_equity = 40000.0
        mock_connector.get_account.return_value = mock_account

        tool = AlpacaExecutionTool(connector=mock_connector)
        balance = tool.get_account_balance()

        assert balance["buying_power"] == -10000.0
        assert balance["cash"] == 0.0
        assert balance["portfolio_value"] == 50000.0
        assert balance["total_equity"] == 40000.0

    def test_from_credentials_with_many_kwargs(self):
        """Test creating tool from credentials with many additional parameters."""
        with patch(
            "quantchain.tools.execution.AlpacaExecutionConnector"
        ) as mock_connector_class:
            mock_connector = MagicMock()
            mock_connector_class.return_value = mock_connector

            tool = AlpacaExecutionTool.from_credentials(
                api_key="test_key",
                api_secret="test_secret",
                use_paper=False,
                api_url="https://api.alpaca.com",
                data_url="https://data.alpaca.com",
                timeout=30,
                retry_count=3,
                custom_param="value",
            )

            mock_connector_class.assert_called_once_with(
                api_key="test_key",
                api_secret="test_secret",
                use_paper=False,
                api_url="https://api.alpaca.com",
                data_url="https://data.alpaca.com",
                timeout=30,
                retry_count=3,
                custom_param="value",
            )


@pytest.mark.unit
class TestAlpacaExecutionToolIntegration:
    """Integration-style tests for AlpacaExecutionTool."""

    def test_full_order_workflow(self):
        """Test full order workflow from execution to position checking."""
        mock_connector = MagicMock()

        # Mock order execution
        mock_order_result = MagicMock(spec=OrderResult)
        mock_order_result.order_id = "order_123"
        mock_order_result.status = OrderStatus.FILLED
        mock_connector.place_order.return_value = mock_order_result

        # Mock positions
        mock_position = MagicMock(spec=Position)
        mock_position.symbol = "AAPL"
        mock_position.quantity = 100.0
        mock_position.market_value = 15000.0
        mock_position.cost_basis = 12000.0
        mock_connector.get_positions.return_value = [mock_position]

        # Mock account
        mock_account = MagicMock(spec=AccountInfo)
        mock_account.buying_power = 35000.0
        mock_account.cash = 25000.0
        mock_account.portfolio_value = 65000.0
        mock_account.total_equity = 90000.0
        mock_connector.get_account.return_value = mock_account

        tool = AlpacaExecutionTool(connector=mock_connector)

        # Execute order
        result = tool.execute_market_order("AAPL", "buy", 100)
        assert result.order_id == "order_123"
        assert result.status == OrderStatus.FILLED

        # Check positions
        positions = tool.get_positions()
        assert len(positions) == 1
        assert positions[0]["symbol"] == "AAPL"
        assert positions[0]["quantity"] == 100.0

        # Check account balance
        balance = tool.get_account_balance()
        assert balance["buying_power"] == 35000.0
        assert balance["portfolio_value"] == 65000.0

        # Verify all methods were called
        mock_connector.place_order.assert_called_once()
        mock_connector.get_positions.assert_called_once()
        mock_connector.get_account.assert_called_once()

    def test_error_handling_workflow(self):
        """Test error handling in workflow."""
        mock_connector = MagicMock()

        # Mock order execution failure
        mock_connector.place_order.side_effect = ExecutionError(
            "Insufficient buying power"
        )

        tool = AlpacaExecutionTool(connector=mock_connector)

        # Order should fail
        with pytest.raises(ExecutionError, match="Insufficient buying power"):
            tool.execute_market_order("AAPL", "buy", 1000000)

        # Position and account calls should still work
        mock_connector.get_positions.return_value = []
        mock_connector.get_account.return_value = MagicMock(spec=AccountInfo)

        positions = tool.get_positions()
        assert positions == []

        balance = tool.get_account_balance()
        assert isinstance(balance, dict)

        # Order was attempted, position/account were checked
        mock_connector.place_order.assert_called_once()
        mock_connector.get_positions.assert_called_once()
        mock_connector.get_account.assert_called_once()
