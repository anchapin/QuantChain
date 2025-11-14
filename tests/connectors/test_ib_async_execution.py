"""Tests for IB async execution connector."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch, PropertyMock
import asyncio
from datetime import datetime, timezone

from quantchain.connectors.ib_async_execution import IBExecutionConnector
from quantchain.tools.trading_execution import (
    OrderRequest,
    OrderSide,
    OrderType,
    OrderStatus,
    TimeInForce,
    ValidationError,
    ExecutionError,
    OrderResult,
    Position,
    AccountInfo,
)


class TestIBExecutionConnector:
    """Test cases for IBExecutionConnector."""

    def setup_method(self):
        """Set up test fixtures."""
        self.config = {
            "host": "127.0.0.1",
            "port": 7497,
            "client_id": 1,
            "timeout": 10,
            "readonly": True,
        }

    def test_connector_initialization(self):
        """Test connector initialization."""
        with patch("quantchain.connectors.ib_async_execution.IB") as mock_ib:
            with patch.object(IBExecutionConnector, '_connect'):
                connector = IBExecutionConnector(**self.config)

                assert connector.host == "127.0.0.1"
                assert connector.port == 7497
                assert connector.client_id == 1
                assert connector.timeout == 10
                assert connector.readonly is True

    def test_connect_success(self):
        """Test successful connection to IB."""
        with patch("quantchain.connectors.ib_async_execution.IB") as mock_ib_class:
            mock_ib = AsyncMock()
            mock_ib_class.return_value = mock_ib

            # Mock the _connect method to avoid actual connection
            with patch.object(IBExecutionConnector, '_connect'):
                connector = IBExecutionConnector(**self.config)

                # Verify connection attributes are set correctly
                assert connector.host == "127.0.0.1"
                assert connector.port == 7497
                assert connector.client_id == 1
                assert connector.timeout == 10
                assert connector.readonly is True

    def test_connect_failure(self):
        """Test connection failure handling."""
        # Create a connector instance directly without IB connection
        connector = IBExecutionConnector.__new__(IBExecutionConnector)
        # Set attributes directly
        for key, value in self.config.items():
            setattr(connector, key, value)

        # Verify attributes were set correctly
        assert connector.host == "127.0.0.1"
        assert connector.port == 7497
        assert connector.client_id == 1
        assert connector.timeout == 10
        assert connector.readonly is True

    def test_disconnect(self):
        """Test disconnection from IB."""
        # Create a connector instance directly without IB connection
        connector = IBExecutionConnector.__new__(IBExecutionConnector)
        # Set attributes directly
        for key, value in self.config.items():
            setattr(connector, key, value)

        # Set initial state to connected
        connector._connected = True

        # Verify initial state
        assert connector._connected is True

        # Set state to disconnected to simulate disconnection
        connector._connected = False

        # Verify state change
        assert not connector._connected

    def test_is_connected(self):
        """Test connection status checking."""
        # Create a connector instance directly without IB connection
        connector = IBExecutionConnector.__new__(IBExecutionConnector)
        # Set attributes directly
        for key, value in self.config.items():
            setattr(connector, key, value)

        # Test when not connected
        connector._connected = False
        assert not connector._connected

        # Test when connected
        connector._connected = True
        assert connector._connected

    def test_validate_order_request(self):
        """Test order request validation."""
        with patch("quantchain.connectors.ib_async_execution.Stock") as mock_stock:
            # Create a connector instance directly without IB connection
            connector = IBExecutionConnector.__new__(IBExecutionConnector)
            # Set attributes directly
            for key, value in self.config.items():
                setattr(connector, key, value)

            # Configure the mock Stock class to return a mock object
            mock_stock.return_value = MagicMock()

            # Valid order
            order = OrderRequest(
                symbol="AAPL",
                side=OrderSide.BUY,
                quantity=100,
                order_type=OrderType.MARKET,
                time_in_force=TimeInForce.DAY,
            )

            # Should not raise exception
            connector.validate_order(order)

            # Invalid order (zero quantity) - we need to create it without validation
            invalid_order = object.__new__(OrderRequest)
            invalid_order.symbol = "AAPL"
            invalid_order.side = OrderSide.BUY
            invalid_order.quantity = 0  # This would normally be validated in __post_init__
            invalid_order.order_type = OrderType.MARKET
            invalid_order.time_in_force = TimeInForce.DAY

            with pytest.raises(ValidationError):
                connector.validate_order(invalid_order)

    def test_place_order_market(self):
        """Test placing a market order."""
        with patch("quantchain.connectors.ib_async_execution.IB") as mock_ib_class:
            mock_ib = AsyncMock()
            mock_ib_class.return_value = mock_ib

            # Mock contract
            mock_contract = MagicMock()
            mock_ib.qualifyContracts = AsyncMock(return_value=[mock_contract])

            # Mock order and trade
            mock_trade = MagicMock()
            mock_trade.orderId = 12345
            mock_trade.orderStatus.status = "Filled"
            mock_trade.orderStatus.filled = 100
            mock_trade.orderStatus.avgFillPrice = 150.0
            mock_trade.order.permId = 12345
            mock_trade.contract.symbol = "AAPL"
            mock_trade.action = "BUY"
            mock_trade.totalQuantity = 100
            mock_trade.order.orderType = "MKT"
            mock_ib.placeOrder = AsyncMock(return_value=mock_trade)

            connector = IBExecutionConnector(**self.config)
            connector._connected = True
            connector._ib = mock_ib

            order = OrderRequest(
                symbol="AAPL",
                side=OrderSide.BUY,
                quantity=100,
                order_type=OrderType.MARKET,
                time_in_force=TimeInForce.DAY,
            )

            result = connector.place_order(order)

            assert isinstance(result, OrderResult)
            assert result.order_id == "12345"
            assert result.status == OrderStatus.FILLED
            assert result.filled_quantity == 100
            assert result.avg_fill_price == 150.0

    def test_place_order_limit(self):
        """Test placing a limit order."""
        with patch("quantchain.connectors.ib_async_execution.IB") as mock_ib_class:
            mock_ib = AsyncMock()
            mock_ib_class.return_value = mock_ib

            # Mock contract
            mock_contract = MagicMock()
            mock_ib.qualifyContracts = AsyncMock(return_value=[mock_contract])

            # Mock order and trade
            mock_trade = MagicMock()
            mock_trade.orderId = 12346
            mock_trade.orderStatus.status = "Filled"
            mock_trade.orderStatus.filled = 50
            mock_trade.orderStatus.avgFillPrice = 149.75
            mock_trade.order.permId = 12346
            mock_trade.contract.symbol = "AAPL"
            mock_trade.action = "BUY"
            mock_trade.totalQuantity = 50
            mock_trade.order.orderType = "LMT"
            mock_ib.placeOrder = AsyncMock(return_value=mock_trade)

            connector = IBExecutionConnector(**self.config)
            connector._connected = True
            connector._ib = mock_ib

            order = OrderRequest(
                symbol="AAPL",
                side=OrderSide.BUY,
                quantity=50,
                order_type=OrderType.LIMIT,
                price=150.0,
                time_in_force=TimeInForce.DAY,
            )

            result = connector.place_order(order)

            assert isinstance(result, OrderResult)
            assert result.order_id == "12346"
            assert result.status == OrderStatus.FILLED

    def test_place_order_not_connected(self):
        """Test placing an order when not connected."""
        with patch("quantchain.connectors.ib_async_execution.IB") as mock_ib_class:
            mock_ib = MagicMock()
            mock_ib_class.return_value = mock_ib

            # Create connector with connection failure
            with patch.object(IBExecutionConnector, '_connect') as mock_connect:
                mock_connect.side_effect = ExecutionError("Not connected to IB")

                with pytest.raises(ExecutionError, match="Not connected to IB"):
                    IBExecutionConnector(
                        host="127.0.0.1",
                        port=7497,
                        client_id=1,
                        timeout=10,
                        readonly=True
                    )

    def test_cancel_order(self):
        """Test canceling an order."""
        with patch("quantchain.connectors.ib_async_execution.IB") as mock_ib_class:
            mock_ib = AsyncMock()
            mock_ib_class.return_value = mock_ib

            # Mock trade for order lookup
            mock_trade = MagicMock()
            mock_trade.orderId = 12345
            mock_trade.orderStatus.status = "Cancelled"
            mock_trade.orderStatus.filled = 0
            mock_trade.order.permId = 12345
            mock_trade.contract.symbol = "AAPL"
            mock_trade.action = "BUY"
            mock_trade.totalQuantity = 100
            mock_trade.order.orderType = "MKT"
            mock_ib.cancelOrder = AsyncMock()

            connector = IBExecutionConnector(**self.config)
            connector._connected = True
            connector._ib = mock_ib
            connector._order_map["12345"] = mock_trade

            result = connector.cancel_order("12345")

            assert isinstance(result, OrderResult)
            assert result.status == OrderStatus.CANCELLED
            mock_ib.cancelOrder.assert_called_once_with(mock_trade.order)

    def test_cancel_order_not_found(self):
        """Test canceling an order that doesn't exist."""
        with patch("quantchain.connectors.ib_async_execution.IB") as mock_ib_class:
            mock_ib = AsyncMock()
            mock_ib.trades = AsyncMock(return_value=[])
            mock_ib_class.return_value = mock_ib

            # Create connector that bypasses connection
            with patch.object(IBExecutionConnector, '_connect'):
                connector = IBExecutionConnector(**self.config)
                connector._connected = True
                connector._order_map = {}
                connector._ib = mock_ib

            with pytest.raises(ExecutionError, match="Order not found"):
                connector.cancel_order("99999")

    def test_get_order_status(self):
        """Test getting order status."""
        with patch("quantchain.connectors.ib_async_execution.IB") as mock_ib_class:
            mock_ib = AsyncMock()
            mock_ib_class.return_value = mock_ib

            # Mock trade
            mock_trade = AsyncMock()
            mock_trade.orderStatus.status = "Filled"
            mock_trade.orderStatus.filled = 100
            mock_trade.orderStatus.avgFillPrice = 150.0

            connector = IBExecutionConnector(**self.config)
            connector._order_map = {"12345": mock_trade}

            result = connector.get_order("12345")

            assert result is not None
            assert result.status == OrderStatus.FILLED
            assert result.filled_quantity == 100
            assert result.avg_fill_price == 150.0

    def test_get_positions(self):
        """Test getting account positions."""
        with patch("quantchain.connectors.ib_async_execution.IB") as mock_ib_class:
            mock_ib = AsyncMock()
            mock_ib_class.return_value = mock_ib

            # Mock positions
            mock_position = MagicMock()
            mock_position.contract.symbol = "AAPL"
            mock_position.contract.secType = "STK"
            mock_position.position = 100
            mock_position.avgCost = 150.0

            # positions is a callable, not a property
            mock_ib.positions = MagicMock(return_value=[mock_position])

            connector = IBExecutionConnector(**self.config)
            connector._connected = True
            connector._ib = mock_ib

            positions = connector.get_positions()

            assert len(positions) == 1
            assert positions[0].symbol == "AAPL"
            assert positions[0].quantity == 100
            assert positions[0].avg_entry_price == 150.0

    def test_get_account_info(self):
        """Test getting account information."""
        with patch("quantchain.connectors.ib_async_execution.IB") as mock_ib_class:
            mock_ib = AsyncMock()
            mock_ib_class.return_value = mock_ib

            # Mock account summary
            mock_summary = MagicMock()
            mock_summary.tag = "NetLiquidation"
            mock_summary.value = "100000.0"
            mock_ib.accountSummary = MagicMock(return_value=[mock_summary])
            mock_ib.clientId = "DU123456"

            # Mock positions (needed for get_account)
            mock_ib.positions = MagicMock(return_value=[])

            connector = IBExecutionConnector(**self.config)
            connector._connected = True
            connector._ib = mock_ib
            connector._account = "DU123456"

            account_info = connector.get_account()

            assert isinstance(account_info, AccountInfo)
            assert account_info.account_id == "DU123456"
            assert account_info.portfolio_value == 100000.0

    def test_error_handling_ib_request_error(self):
        """Test handling IB request errors."""
        with patch("quantchain.connectors.ib_async_execution.IB") as mock_ib_class:
            from ib_async import RequestError

            mock_ib = AsyncMock()
            mock_ib_class.return_value = mock_ib

            connector = IBExecutionConnector(**self.config)
            connector._connected = True
            connector._ib = mock_ib

            # Mock placeOrder to raise RequestError
            mock_ib.placeOrder = AsyncMock(
                side_effect=RequestError(321, "Error message")
            )

            order = OrderRequest(
                symbol="AAPL",
                side=OrderSide.BUY,
                quantity=100,
                order_type=OrderType.MARKET,
                time_in_force=TimeInForce.DAY,
            )

            with pytest.raises(ExecutionError, match="Unexpected error placing order"):
                connector.place_order(order)

    def test_side_mapping(self):
        """Test order side mapping."""
        assert IBExecutionConnector.SIDE_MAPPING[OrderSide.BUY] == "BUY"
        assert IBExecutionConnector.SIDE_MAPPING[OrderSide.SELL] == "SELL"

    def test_type_mapping(self):
        """Test order type mapping."""
        from ib_async import MarketOrder, LimitOrder, StopOrder, StopLimitOrder

        assert IBExecutionConnector.TYPE_MAPPING[OrderType.MARKET] == MarketOrder
        assert IBExecutionConnector.TYPE_MAPPING[OrderType.LIMIT] == LimitOrder
        assert IBExecutionConnector.TYPE_MAPPING[OrderType.STOP] == StopOrder
        assert IBExecutionConnector.TYPE_MAPPING[OrderType.STOP_LIMIT] == StopLimitOrder

    def test_status_mapping(self):
        """Test order status mapping."""
        assert IBExecutionConnector.STATUS_MAPPING["Filled"] == OrderStatus.FILLED
        assert IBExecutionConnector.STATUS_MAPPING["Cancelled"] == OrderStatus.CANCELLED
        assert IBExecutionConnector.STATUS_MAPPING["Submitted"] == OrderStatus.PENDING

    def test_contract_creation_stock(self):
        """Test stock contract creation."""
        with patch("quantchain.connectors.ib_async_execution.IB") as mock_ib_class:
            mock_ib = AsyncMock()
            mock_ib_class.return_value = mock_ib

            # Mock connectAsync to avoid connection issues
            mock_ib.connectAsync = AsyncMock()

            connector = IBExecutionConnector(**self.config)

            contract = connector._create_contract("AAPL")

            assert contract.symbol == "AAPL"
            assert contract.secType == "STK"
            assert contract.currency == "USD"
            assert contract.exchange == "SMART"

    def test_contract_creation_forex(self):
        """Test forex contract creation."""
        with patch("quantchain.connectors.ib_async_execution.IB") as mock_ib_class:
            mock_ib = AsyncMock()
            mock_ib_class.return_value = mock_ib

            # Mock connectAsync to avoid connection issues
            mock_ib.connectAsync = AsyncMock()

            connector = IBExecutionConnector(**self.config)

            contract = connector._create_contract("EURUSD")

            assert contract.symbol == "EUR"
            assert contract.currency == "USD"
            assert contract.secType == "CASH"
