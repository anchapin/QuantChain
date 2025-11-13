"""Tests for IB async execution connector."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
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

    @pytest.mark.asyncio
    async def test_connector_initialization(self):
        """Test connector initialization."""
        with patch("quantchain.connectors.ib_async_execution.IB") as mock_ib:
            connector = IBExecutionConnector(**self.config)

            assert connector.host == "127.0.0.1"
            assert connector.port == 7497
            assert connector.client_id == 1
            assert connector.timeout == 10
            assert connector.readonly is True
            assert not connector._connected

    @pytest.mark.asyncio
    async def test_connect_success(self):
        """Test successful connection to IB."""
        with patch("quantchain.connectors.ib_async_execution.IB") as mock_ib_class:
            mock_ib = AsyncMock()
            mock_ib_class.return_value = mock_ib

            connector = IBExecutionConnector(**self.config)

            # Mock the connection process
            mock_ib.connect = AsyncMock()
            mock_ib.reqCurrentTime = AsyncMock(return_value=datetime.now(timezone.utc))

            # Test connection
            await connector.connect()

            # Verify connection was attempted
            mock_ib.connect.assert_called_once_with(
                host="127.0.0.1",
                port=7497,
                clientId=1,
                timeout=10,
                readonly=True,
            )

            assert connector._connected

    @pytest.mark.asyncio
    async def test_connect_failure(self):
        """Test connection failure handling."""
        with patch("quantchain.connectors.ib_async_execution.IB") as mock_ib_class:
            mock_ib = AsyncMock()
            mock_ib_class.return_value = mock_ib
            mock_ib.connect = AsyncMock(side_effect=Exception("Connection failed"))

            connector = IBExecutionConnector(**self.config)

            with pytest.raises(
                ExecutionError, match="Failed to connect to Interactive Brokers"
            ):
                await connector.connect()

            assert not connector._connected

    @pytest.mark.asyncio
    async def test_disconnect(self):
        """Test disconnection from IB."""
        with patch("quantchain.connectors.ib_async_execution.IB") as mock_ib_class:
            mock_ib = AsyncMock()
            mock_ib_class.return_value = mock_ib

            connector = IBExecutionConnector(**self.config)
            connector._connected = True
            connector._ib = mock_ib

            await connector.disconnect()

            mock_ib.disconnect.assert_called_once()
            assert not connector._connected

    @pytest.mark.asyncio
    async def test_is_connected(self):
        """Test connection status checking."""
        connector = IBExecutionConnector(**self.config)

        # Test when not connected
        assert not await connector.is_connected()

        # Mock connected state
        with patch("quantchain.connectors.ib_async_execution.IB") as mock_ib_class:
            mock_ib = AsyncMock()
            mock_ib_class.return_value = mock_ib
            mock_ib.isConnected = MagicMock(return_value=True)

            connector._connected = True
            connector._ib = mock_ib

            assert await connector.is_connected()

    @pytest.mark.asyncio
    async def test_validate_order_request(self):
        """Test order request validation."""
        with patch("quantchain.connectors.ib_async_execution.IB"):
            connector = IBExecutionConnector(**self.config)

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

            # Invalid order (zero quantity)
            invalid_order = OrderRequest(
                symbol="AAPL",
                side=OrderSide.BUY,
                quantity=0,
                order_type=OrderType.MARKET,
                time_in_force=TimeInForce.DAY,
            )

            with pytest.raises(ValidationError):
                connector.validate_order(invalid_order)

    @pytest.mark.asyncio
    async def test_place_order_market(self):
        """Test placing a market order."""
        with patch("quantchain.connectors.ib_async_execution.IB") as mock_ib_class:
            mock_ib = AsyncMock()
            mock_ib_class.return_value = mock_ib

            # Mock contract
            mock_contract = MagicMock()
            mock_ib.qualifyContracts = AsyncMock(return_value=[mock_contract])

            # Mock order and trade
            mock_trade = AsyncMock()
            mock_trade.orderStatus.status = "Filled"
            mock_trade.orderStatus.filled = 100
            mock_trade.orderStatus.avgFillPrice = 150.0
            mock_trade.order.permId = 12345
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

            result = await connector.place_order(order)

            assert isinstance(result, OrderResult)
            assert result.order_id == 12345
            assert result.status == OrderStatus.FILLED
            assert result.filled_quantity == 100
            assert result.average_price == 150.0

    @pytest.mark.asyncio
    async def test_place_order_limit(self):
        """Test placing a limit order."""
        with patch("quantchain.connectors.ib_async_execution.IB") as mock_ib_class:
            mock_ib = AsyncMock()
            mock_ib_class.return_value = mock_ib

            # Mock contract
            mock_contract = MagicMock()
            mock_ib.qualifyContracts = AsyncMock(return_value=[mock_contract])

            # Mock order and trade
            mock_trade = AsyncMock()
            mock_trade.orderStatus.status = "Submitted"
            mock_trade.order.permId = 12346
            mock_ib.placeOrder = AsyncMock(return_value=mock_trade)

            connector = IBExecutionConnector(**self.config)
            connector._connected = True
            connector._ib = mock_ib

            order = OrderRequest(
                symbol="AAPL",
                side=OrderSide.BUY,
                quantity=100,
                order_type=OrderType.LIMIT,
                limit_price=150.0,
                time_in_force=TimeInForce.DAY,
            )

            result = await connector.place_order(order)

            assert isinstance(result, OrderResult)
            assert result.order_id == 12346
            assert result.status == OrderStatus.PENDING

    @pytest.mark.asyncio
    async def test_place_order_not_connected(self):
        """Test placing order when not connected."""
        connector = IBExecutionConnector(**self.config)

        order = OrderRequest(
            symbol="AAPL",
            side=OrderSide.BUY,
            quantity=100,
            order_type=OrderType.MARKET,
            time_in_force=TimeInForce.DAY,
        )

        with pytest.raises(
            ExecutionError, match="Not connected to Interactive Brokers"
        ):
            await connector.place_order(order)

    @pytest.mark.asyncio
    async def test_cancel_order(self):
        """Test cancelling an order."""
        with patch("quantchain.connectors.ib_async_execution.IB") as mock_ib_class:
            mock_ib = AsyncMock()
            mock_ib_class.return_value = mock_ib

            # Mock trade
            mock_trade = AsyncMock()
            mock_trade.orderStatus.status = "Cancelled"
            mock_ib.cancelOrder = AsyncMock()

            connector = IBExecutionConnector(**self.config)
            connector._connected = True
            connector._ib = mock_ib

            # Mock open orders
            connector._open_orders = {12345: mock_trade}

            result = await connector.cancel_order(12345)

            assert result is True
            mock_ib.cancelOrder.assert_called_once_with(mock_trade.order)

    @pytest.mark.asyncio
    async def test_cancel_order_not_found(self):
        """Test cancelling an order that doesn't exist."""
        connector = IBExecutionConnector(**self.config)
        connector._open_orders = {}

        result = await connector.cancel_order(99999)
        assert result is False

    @pytest.mark.asyncio
    async def test_get_order_status(self):
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
            connector._open_orders = {12345: mock_trade}

            result = await connector.get_order_status(12345)

            assert result is not None
            assert result.status == OrderStatus.FILLED
            assert result.filled_quantity == 100
            assert result.average_price == 150.0

    @pytest.mark.asyncio
    async def test_get_positions(self):
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
            mock_ib.positions = [mock_position]

            connector = IBExecutionConnector(**self.config)
            connector._connected = True
            connector._ib = mock_ib

            positions = await connector.get_positions()

            assert len(positions) == 1
            assert positions[0].symbol == "AAPL"
            assert positions[0].quantity == 100
            assert positions[0].average_price == 150.0

    @pytest.mark.asyncio
    async def test_get_account_info(self):
        """Test getting account information."""
        with patch("quantchain.connectors.ib_async_execution.IB") as mock_ib_class:
            mock_ib = AsyncMock()
            mock_ib_class.return_value = mock_ib

            # Mock account summary
            mock_summary = MagicMock()
            mock_summary.tag = "NetLiquidation"
            mock_summary.value = "100000.0"
            mock_ib.accountSummary = MagicMock(return_value=[mock_summary])

            connector = IBExecutionConnector(**self.config)
            connector._connected = True
            connector._ib = mock_ib
            connector._account = "DU123456"

            account_info = await connector.get_account_info()

            assert isinstance(account_info, AccountInfo)
            assert account_info.account_id == "DU123456"
            assert account_info.total_value == 100000.0

    @pytest.mark.asyncio
    async def test_error_handling_ib_request_error(self):
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

            with pytest.raises(ExecutionError, match="IB request failed"):
                await connector.place_order(order)

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

    @pytest.mark.asyncio
    async def test_contract_creation_stock(self):
        """Test stock contract creation."""
        with patch("quantchain.connectors.ib_async_execution.IB"):
            connector = IBExecutionConnector(**self.config)

            order = OrderRequest(
                symbol="AAPL",
                side=OrderSide.BUY,
                quantity=100,
                order_type=OrderType.MARKET,
                time_in_force=TimeInForce.DAY,
            )

            contract = connector._create_contract(order)

            assert contract.symbol == "AAPL"
            assert contract.secType == "STK"
            assert contract.currency == "USD"
            assert contract.exchange == "SMART"

    @pytest.mark.asyncio
    async def test_contract_creation_forex(self):
        """Test forex contract creation."""
        with patch("quantchain.connectors.ib_async_execution.IB"):
            connector = IBExecutionConnector(**self.config)

            order = OrderRequest(
                symbol="EURUSD",
                side=OrderSide.BUY,
                quantity=100000,
                order_type=OrderType.MARKET,
                time_in_force=TimeInForce.DAY,
            )

            contract = connector._create_contract(order)

            assert contract.symbol == "EUR"
            assert contract.currency == "USD"
            assert contract.secType == "CASH"
