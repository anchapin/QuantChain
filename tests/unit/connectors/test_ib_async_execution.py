"""Tests for IB async execution connector."""

import asyncio
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

try:
    from quantchain.connectors.ib_async_execution import IBExecutionConnector
    from quantchain.tools.trading_execution import (
        AccountInfo,
        OrderRequest,
        OrderSide,
        OrderType,
        OrderStatus,
        Position,
        TimeInForce,
        ExecutionError,
        InsufficientFundsError,
        OrderNotFoundError,
        ValidationError,
    )

    IB_EXECUTION_AVAILABLE = True
except ImportError as e:
    IB_EXECUTION_AVAILABLE = False
    print(f"Import error: {e}")

pytestmark = pytest.mark.skipif(
    not IB_EXECUTION_AVAILABLE, reason="IB execution connector not available"
)


@pytest.mark.unit
class TestIBExecutionConnector:
    """Test cases for IBExecutionConnector."""

    @pytest.fixture
    def connector(self):
        """Create a connector instance with mocked IB."""
        with patch("quantchain.connectors.ib_async_execution.IB") as mock_ib:
            mock_ib.return_value = AsyncMock()
            return IBExecutionConnector(
                host="127.0.0.1",
                port=7497,
                client_id=1,
                timeout=10,
            )

    def test_initialization(self, connector):
        """Test connector initialization."""
        assert connector.host == "127.0.0.1"
        assert connector.port == 7497
        assert connector.client_id == 1
        assert connector.timeout == 10

    def test_initialization_with_custom_values(self):
        """Test initialization with custom values."""
        with patch("quantchain.connectors.ib_async_execution.IB") as mock_ib:
            mock_ib.return_value = AsyncMock()
            connector = IBExecutionConnector(
                host="192.168.1.100",
                port=4001,
                client_id=999,
                timeout=30,
            )
            assert connector.host == "192.168.1.100"
            assert connector.port == 4001
            assert connector.client_id == 999
            assert connector.timeout == 30

    @pytest.mark.asyncio
    async def test_connect(self, connector):
        """Test connecting to IB."""
        await connector.connect()
        connector.ib.connect.assert_called_once_with(
            host="127.0.0.1",
            port=7497,
            clientId=1,
            timeout=10,
        )

    @pytest.mark.asyncio
    async def test_connect_error(self, connector):
        """Test connection error handling."""
        connector.ib.connect.side_effect = Exception("Connection failed")

        with pytest.raises(ExecutionError, match="Failed to connect"):
            await connector.connect()

    @pytest.mark.asyncio
    async def test_disconnect(self, connector):
        """Test disconnecting from IB."""
        await connector.disconnect()
        connector.ib.disconnect.assert_called_once()

    @pytest.mark.asyncio
    async def test_is_connected_true(self, connector):
        """Test is_connected when connected."""
        connector.ib.isConnected.return_value = True
        result = await connector.is_connected()
        assert result is True

    @pytest.mark.asyncio
    async def test_is_connected_false(self, connector):
        """Test is_connected when not connected."""
        connector.ib.isConnected.return_value = False
        result = await connector.is_connected()
        assert result is False

    @pytest.mark.asyncio
    async def test_place_market_order(self, connector):
        """Test placing a market order."""
        # Mock the contract
        mock_contract = MagicMock()
        connector._create_stock_contract.return_value = mock_contract

        # Mock the order
        mock_order = MagicMock()
        connector._create_order.return_value = mock_order

        # Mock the trade
        mock_trade = MagicMock()
        mock_trade.orderStatus.return_value = OrderStatus.FILLED
        mock_trade.orderId.return_value = "12345"
        mock_ib_order = MagicMock()
        mock_ib_order.totalQuantity.return_value = 100
        mock_trade.order.return_value = mock_ib_order
        connector.ib.placeOrder.return_value = mock_trade

        # Create order request
        request = OrderRequest(
            symbol="AAPL",
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=100,
        )

        result = await connector.place_order(request)

        assert result.order_id == "12345"
        assert result.status == OrderStatus.FILLED
        assert result.filled_quantity == 100
        connector._create_stock_contract.assert_called_once_with("AAPL", "SMART", "USD")
        connector._create_order.assert_called_once_with(request)

    @pytest.mark.asyncio
    async def test_place_limit_order(self, connector):
        """Test placing a limit order."""
        mock_contract = MagicMock()
        connector._create_stock_contract.return_value = mock_contract

        mock_order = MagicMock()
        connector._create_order.return_value = mock_order

        mock_trade = MagicMock()
        mock_trade.orderStatus.return_value = OrderStatus.SUBMITTED
        mock_trade.orderId.return_value = "67890"
        mock_ib_order = MagicMock()
        mock_ib_order.totalQuantity.return_value = 50
        mock_trade.order.return_value = mock_ib_order
        connector.ib.placeOrder.return_value = mock_trade

        request = OrderRequest(
            symbol="GOOGL",
            side=OrderSide.SELL,
            order_type=OrderType.LIMIT,
            quantity=50,
            limit_price=2500.0,
        )

        result = await connector.place_order(request)

        assert result.order_id == "67890"
        assert result.status == OrderStatus.SUBMITTED
        assert result.filled_quantity == 0  # Not filled yet

    @pytest.mark.asyncio
    async def test_place_stop_order(self, connector):
        """Test placing a stop order."""
        mock_contract = MagicMock()
        connector._create_stock_contract.return_value = mock_contract

        mock_order = MagicMock()
        connector._create_order.return_value = mock_order

        mock_trade = MagicMock()
        mock_trade.orderStatus.return_value = OrderStatus.SUBMITTED
        mock_trade.orderId.return_value = "11111"
        mock_ib_order = MagicMock()
        mock_ib_order.totalQuantity.return_value = 200
        mock_trade.order.return_value = mock_ib_order
        connector.ib.placeOrder.return_value = mock_trade

        request = OrderRequest(
            symbol="MSFT",
            side=OrderSide.SELL,
            order_type=OrderType.STOP,
            quantity=200,
            stop_price=300.0,
        )

        result = await connector.place_order(request)

        assert result.order_id == "11111"
        assert result.status == OrderStatus.SUBMITTED

    @pytest.mark.asyncio
    async def test_place_order_error(self, connector):
        """Test order placement error."""
        connector.ib.placeOrder.side_effect = Exception("Order failed")

        request = OrderRequest(
            symbol="AAPL",
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=100,
        )

        with pytest.raises(ExecutionError, match="Failed to place order"):
            await connector.place_order(request)

    @pytest.mark.asyncio
    async def test_place_order_insufficient_funds(self, connector):
        """Test order placement with insufficient funds."""
        connector.ib.placeOrder.side_effect = Exception("Insufficient funds")

        request = OrderRequest(
            symbol="AAPL",
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=1000000,
        )

        with pytest.raises(InsufficientFundsError):
            await connector.place_order(request)

    @pytest.mark.asyncio
    async def test_cancel_order(self, connector):
        """Test cancelling an order."""
        mock_order = MagicMock()
        connector.ib.cancelOrder.return_value = None

        await connector.cancel_order("12345")

        # Find the order and cancel it
        connector.ib.cancelOrder.assert_called_once()

    @pytest.mark.asyncio
    async def test_cancel_order_not_found(self, connector):
        """Test cancelling a non-existent order."""
        connector.ib.cancelOrder.side_effect = Exception("Order not found")

        with pytest.raises(OrderNotFoundError):
            await connector.cancel_order("99999")

    @pytest.mark.asyncio
    async def test_get_order_status(self, connector):
        """Test getting order status."""
        mock_order = MagicMock()
        mock_order.orderId.return_value = "12345"
        mock_order.orderStatus.return_value = OrderStatus.FILLED
        connector.ib.orders.return_value = [mock_order]

        result = await connector.get_order_status("12345")

        assert result == OrderStatus.FILLED

    @pytest.mark.asyncio
    async def test_get_order_status_not_found(self, connector):
        """Test getting status for non-existent order."""
        mock_order = MagicMock()
        mock_order.orderId.return_value = "67890"
        connector.ib.orders.return_value = [mock_order]

        result = await connector.get_order_status("12345")

        assert result is None

    @pytest.mark.asyncio
    async def test_get_account(self, connector):
        """Test getting account information."""
        mock_account = MagicMock()
        mock_account.totalCashBalance.return_value = 100000.0
        mock_account.buyingPower.return_value = 200000.0
        mock_account.netLiquidation.return_value = 150000.0
        connector.ib.accountSummary.return_value = [mock_account]

        result = await connector.get_account()

        assert isinstance(result, AccountInfo)
        assert result.cash == 100000.0
        assert result.buying_power == 200000.0
        assert result.total_equity == 150000.0

    @pytest.mark.asyncio
    async def test_get_positions(self, connector):
        """Test getting positions."""
        mock_position = MagicMock()
        mock_position.contract.symbol.return_value = "AAPL"
        mock_position.position.return_value = 100
        mock_position.marketPrice.return_value = 150.0
        mock_position.marketValue.return_value = 15000.0
        mock_position.averageCost.return_value = 140.0
        connector.ib.positions.return_value = [mock_position]

        result = await connector.get_positions()

        assert len(result) == 1
        assert result[0].symbol == "AAPL"
        assert result[0].quantity == 100
        assert result[0].current_price == 150.0
        assert result[0].market_value == 15000.0
        assert result[0].cost_basis == 14000.0

    @pytest.mark.asyncio
    async def test_get_positions_empty(self, connector):
        """Test getting positions when empty."""
        connector.ib.positions.return_value = []

        result = await connector.get_positions()

        assert result == []

    def test_create_stock_contract(self, connector):
        """Test creating a stock contract."""
        with patch("quantchain.connectors.ib_async_execution.Stock") as mock_stock:
            mock_contract = MagicMock()
            mock_stock.return_value = mock_contract

            result = connector._create_stock_contract("AAPL", "SMART", "USD")

            mock_stock.assert_called_once_with(
                symbol="AAPL",
                exchange="SMART",
                currency="USD",
            )
            assert result == mock_contract

    def test_create_order_market(self, connector):
        """Test creating a market order."""
        with patch(
            "quantchain.connectors.ib_async_execution.MarketOrder"
        ) as mock_market:
            mock_order = MagicMock()
            mock_market.return_value = mock_order

            request = OrderRequest(
                symbol="AAPL",
                side=OrderSide.BUY,
                order_type=OrderType.MARKET,
                quantity=100,
            )

            result = connector._create_order(request)

            mock_market.assert_called_once_with(
                action="BUY",
                totalQuantity=100,
            )
            assert result == mock_order

    def test_create_order_limit(self, connector):
        """Test creating a limit order."""
        with patch("quantchain.connectors.ib_async_execution.LimitOrder") as mock_limit:
            mock_order = MagicMock()
            mock_limit.return_value = mock_order

            request = OrderRequest(
                symbol="AAPL",
                side=OrderSide.SELL,
                order_type=OrderType.LIMIT,
                quantity=50,
                limit_price=150.0,
            )

            result = connector._create_order(request)

            mock_limit.assert_called_once_with(
                action="SELL",
                totalQuantity=50,
                lmtPrice=150.0,
            )
            assert result == mock_order

    def test_create_order_stop(self, connector):
        """Test creating a stop order."""
        with patch("quantchain.connectors.ib_async_execution.StopOrder") as mock_stop:
            mock_order = MagicMock()
            mock_stop.return_value = mock_order

            request = OrderRequest(
                symbol="AAPL",
                side=OrderSide.SELL,
                order_type=OrderType.STOP,
                quantity=100,
                stop_price=140.0,
            )

            result = connector._create_order(request)

            mock_stop.assert_called_once_with(
                action="SELL",
                totalQuantity=100,
                stopPrice=140.0,
            )
            assert result == mock_order

    def test_create_order_stop_limit(self, connector):
        """Test creating a stop-limit order."""
        with patch(
            "quantchain.connectors.ib_async_execution.StopLimitOrder"
        ) as mock_stop_limit:
            mock_order = MagicMock()
            mock_stop_limit.return_value = mock_order

            request = OrderRequest(
                symbol="AAPL",
                side=OrderSide.BUY,
                order_type=OrderType.STOP_LIMIT,
                quantity=100,
                stop_price=160.0,
                limit_price=155.0,
            )

            result = connector._create_order(request)

            mock_stop_limit.assert_called_once_with(
                action="BUY",
                totalQuantity=100,
                stopPrice=160.0,
                lmtPrice=155.0,
            )
            assert result == mock_order

    def test_create_order_time_in_force(self, connector):
        """Test creating order with time in force."""
        with patch("quantchain.connectors.ib_async_execution.LimitOrder") as mock_limit:
            mock_order = MagicMock()
            mock_limit.return_value = mock_order

            request = OrderRequest(
                symbol="AAPL",
                side=OrderSide.BUY,
                order_type=OrderType.LIMIT,
                quantity=100,
                limit_price=150.0,
                time_in_force=TimeInForce.DAY,
            )

            result = connector._create_order(request)

            assert result.tif == "DAY"

    def test_validate_order_request(self, connector):
        """Test order request validation."""
        # Valid order
        request = OrderRequest(
            symbol="AAPL",
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=100,
        )

        # Should not raise
        connector._validate_order_request(request)

        # Missing symbol
        with pytest.raises(ValidationError, match="symbol is required"):
            request = OrderRequest(
                symbol="",
                side=OrderSide.BUY,
                order_type=OrderType.MARKET,
                quantity=100,
            )
            connector._validate_order_request(request)

        # Zero quantity
        with pytest.raises(ValidationError, match="quantity must be greater than 0"):
            request = OrderRequest(
                symbol="AAPL",
                side=OrderSide.BUY,
                order_type=OrderType.MARKET,
                quantity=0,
            )
            connector._validate_order_request(request)

    def test_validate_limit_order(self, connector):
        """Test limit order validation."""
        # Valid limit order
        request = OrderRequest(
            symbol="AAPL",
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            quantity=100,
            limit_price=150.0,
        )
        connector._validate_order_request(request)

        # Missing limit price
        with pytest.raises(ValidationError, match="limit_price is required"):
            request = OrderRequest(
                symbol="AAPL",
                side=OrderSide.BUY,
                order_type=OrderType.LIMIT,
                quantity=100,
            )
            connector._validate_order_request(request)

    def test_validate_stop_order(self, connector):
        """Test stop order validation."""
        # Valid stop order
        request = OrderRequest(
            symbol="AAPL",
            side=OrderSide.SELL,
            order_type=OrderType.STOP,
            quantity=100,
            stop_price=140.0,
        )
        connector._validate_order_request(request)

        # Missing stop price
        with pytest.raises(ValidationError, match="stop_price is required"):
            request = OrderRequest(
                symbol="AAPL",
                side=OrderSide.SELL,
                order_type=OrderType.STOP,
                quantity=100,
            )
            connector._validate_order_request(request)

    def test_convert_order_status(self, connector):
        """Test converting IB order status."""
        from ib_async import OrderStatus as IBOrderStatus

        # Test various status conversions
        assert (
            connector._convert_order_status(IBOrderStatus.PendingSubmit)
            == OrderStatus.PENDING
        )
        assert (
            connector._convert_order_status(IBOrderStatus.Submitted)
            == OrderStatus.SUBMITTED
        )
        assert (
            connector._convert_order_status(IBOrderStatus.Filled) == OrderStatus.FILLED
        )
        assert (
            connector._convert_order_status(IBOrderStatus.Cancelled)
            == OrderStatus.CANCELLED
        )


@pytest.mark.unit
class TestIBExecutionConnectorEdgeCases:
    """Test edge cases for IBExecutionConnector."""

    @pytest.fixture
    def connector(self):
        """Create a connector instance."""
        with patch("quantchain.connectors.ib_async_execution.IB") as mock_ib:
            mock_ib.return_value = AsyncMock()
            return IBExecutionConnector()

    @pytest.mark.asyncio
    async def test_place_order_with_extensions(self, connector):
        """Test placing order with extensions."""
        mock_contract = MagicMock()
        connector._create_stock_contract.return_value = mock_contract

        mock_order = MagicMock()
        connector._create_order.return_value = mock_order

        mock_trade = MagicMock()
        mock_trade.orderStatus.return_value = OrderStatus.SUBMITTED
        mock_trade.orderId.return_value = "ext123"
        connector.ib.placeOrder.return_value = mock_trade

        request = OrderRequest(
            symbol="AAPL",
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            quantity=100,
            limit_price=150.0,
            time_in_force=TimeInForce.GTC,
            extended_hours=True,
        )

        result = await connector.place_order(request)

        assert result.order_id == "ext123"
        assert result.status == OrderStatus.SUBMITTED

    @pytest.mark.asyncio
    async def test_get_account_with_multiple_accounts(self, connector):
        """Test getting account info with multiple accounts."""
        mock_account1 = MagicMock()
        mock_account1.accountId.return_value = "DU123456"
        mock_account1.tag.return_value = "TotalCashBalance"
        mock_account1.value.return_value = "100000"
        mock_account1.currency.return_value = "USD"

        mock_account2 = MagicMock()
        mock_account2.accountId.return_value = "DU123456"
        mock_account2.tag.return_value = "BuyingPower"
        mock_account2.value.return_value = "200000"
        mock_account2.currency.return_value = "USD"

        connector.ib.accountSummary.return_value = [mock_account1, mock_account2]

        result = await connector.get_account()

        assert result.cash == 100000.0
        assert result.buying_power == 200000.0

    @pytest.mark.asyncio
    async def test_get_positions_with_zero_positions(self, connector):
        """Test getting positions with zero quantity."""
        mock_position = MagicMock()
        mock_position.contract.symbol.return_value = "AAPL"
        mock_position.position.return_value = 0  # Zero position
        connector.ib.positions.return_value = [mock_position]

        result = await connector.get_positions()

        # Zero positions should be filtered out
        assert len(result) == 0
