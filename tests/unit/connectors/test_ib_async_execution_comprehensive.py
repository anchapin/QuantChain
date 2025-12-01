"""Comprehensive tests for ib_async_execution module."""

import sys
from unittest.mock import MagicMock

# Mock ib_async if not installed to allow tests to run in CI/CD
if "ib_async" not in sys.modules:
    mock_ib_async = MagicMock()
    sys.modules["ib_async"] = mock_ib_async

    # Setup minimal structure expected by imports
    mock_ib_async.IB = MagicMock
    mock_ib_async.Contract = MagicMock
    mock_ib_async.Order = MagicMock
    mock_ib_async.PortfolioItem = MagicMock
    mock_ib_async.Position = MagicMock
    mock_ib_async.Trade = MagicMock

import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, Mock, patch

import pytest

from quantchain.connectors.ib_async_execution import (
    IBAsyncConnectionError,
    IBAsyncContractError,
    IBAsyncDataError,
    IBAsyncExecutionConnector,
    IBAsyncExecutionError,
    IBAsyncOrderError,
)
from quantchain.core.exceptions import TradingError
from quantchain.tools.execution import (
    AccountInfo,
    OrderRequest,
    OrderResult,
    OrderSide,
    OrderStatus,
    OrderType,
)


class TestIBAsyncExecutionErrors:
    """Test IB async execution exception classes."""

    @pytest.mark.unit
    def test_ib_async_execution_error(self):
        """Test IBAsyncExecutionError base exception."""
        error = IBAsyncExecutionError("Test error")
        assert str(error) == "Test error"
        assert isinstance(error, TradingError)

    @pytest.mark.unit
    def test_ib_async_connection_error(self):
        """Test IBAsyncConnectionError exception."""
        error = IBAsyncConnectionError("Connection failed")
        assert str(error) == "Connection failed"
        assert isinstance(error, IBAsyncExecutionError)

    @pytest.mark.unit
    def test_ib_async_contract_error(self):
        """Test IBAsyncContractError exception."""
        error = IBAsyncContractError("Invalid contract")
        assert str(error) == "Invalid contract"
        assert isinstance(error, IBAsyncExecutionError)

    @pytest.mark.unit
    def test_ib_async_order_error(self):
        """Test IBAsyncOrderError exception."""
        error = IBAsyncOrderError("Order failed")
        assert str(error) == "Order failed"
        assert isinstance(error, IBAsyncExecutionError)

    @pytest.mark.unit
    def test_ib_async_data_error(self):
        """Test IBAsyncDataError exception."""
        error = IBAsyncDataError("Data retrieval failed")
        assert str(error) == "Data retrieval failed"
        assert isinstance(error, IBAsyncExecutionError)


class TestIBAsyncExecutionConnector:
    """Test IBAsyncExecutionConnector functionality."""

    @pytest.fixture(autouse=True)
    def setup_ib_mock(self):
        """Setup IB mock for all tests."""
        with patch("quantchain.connectors.ib_async_execution.IB") as mock_ib_class:
            self.mock_ib_class = mock_ib_class
            self.mock_ib_instance = mock_ib_class.return_value

            # Default mock behavior
            self.mock_ib_instance.connectAsync = AsyncMock(return_value=True)
            self.mock_ib_instance.isConnected = Mock(return_value=True)

            # Mock account summary
            account_mock = Mock()
            account_mock.account = "DU123456"
            self.mock_ib_instance.accountSummaryAsync = AsyncMock(
                return_value=[account_mock]
            )

            # Mock other common methods
            self.mock_ib_instance.qualifyContractsAsync = AsyncMock(
                return_value=[Mock()]
            )
            self.mock_ib_instance.placeOrderAsync = AsyncMock(
                return_value=Mock(
                    order=Mock(permId="12345"),
                    orderStatus=Mock(status="Submitted", filled=0, avgFillPrice=0),
                )
            )
            self.mock_ib_instance.reqMktDataAsync = AsyncMock(
                return_value=Mock(
                    last=150.0, bid=149.0, ask=151.0, close=148.0, volume=1000
                )
            )
            self.mock_ib_instance.positionsAsync = AsyncMock(return_value=[])

            yield

    @pytest.mark.unit
    def test_connector_init_default(self):
        """Test connector initialization with default parameters."""
        connector = IBAsyncExecutionConnector()

        assert connector.host == "127.0.0.1"
        assert connector.port == 7497
        assert connector.client_id == 1
        assert connector.account is None
        assert connector.timeout == 10
        assert connector.readonly is False
        assert connector.ib is not None
        assert connector._connected is False
        assert connector._orders == {}
        assert connector._contracts == {}
        assert connector._pending_requests == {}
        assert connector._market_data_cache == {}

    @pytest.mark.unit
    def test_connector_init_custom_params(self):
        """Test connector initialization with custom parameters."""
        connector = IBAsyncExecutionConnector(
            host="192.168.1.100",
            port=7496,
            client_id=2,
            account="DU123456",
            timeout=30,
            readonly=True,
        )

        assert connector.host == "192.168.1.100"
        assert connector.port == 7496
        assert connector.client_id == 2
        assert connector.account == "DU123456"
        assert connector.timeout == 30
        assert connector.readonly is True

    @pytest.mark.unit
    def test_connector_repr(self):
        """Test connector string representation."""
        connector = IBAsyncExecutionConnector(
            host="192.168.1.100", port=7496, client_id=2
        )

        repr_str = repr(connector)
        assert "IBAsyncExecutionConnector" in repr_str
        assert "host=192.168.1.100" in repr_str
        assert "port=7496" in repr_str
        assert "client_id=2" in repr_str

    @pytest.mark.unit
    def test_connector_connection_status(self):
        """Test connection status tracking."""
        connector = IBAsyncExecutionConnector()
        connector.ib.isConnected.return_value = False

        # Initially not connected
        assert not connector.is_connected()

        # Set connected status
        connector._connected = True
        connector.ib.isConnected.return_value = True
        assert connector.is_connected()

    @pytest.mark.unit
    def test_connect_success(self):
        """Test successful connection to IB."""
        # Configure mock from fixture
        self.mock_ib_instance.connectAsync = AsyncMock(return_value=True)
        self.mock_ib_instance.accountSummaryAsync = AsyncMock(
            return_value=[Mock(account="DU123456")]
        )
        self.mock_ib_instance.isConnected.return_value = True

        connector = IBAsyncExecutionConnector()

        async def test_connect():
            result = await connector.connect_async()
            assert result is True
            assert connector._connected is True

        asyncio.run(test_connect())

    @pytest.mark.unit
    def test_connect_failure(self):
        """Test connection failure."""
        self.mock_ib_instance.connectAsync = AsyncMock(side_effect=Exception("Connection failed"))
        
        connector = IBAsyncExecutionConnector()
        
        async def test_connect():
            with pytest.raises(IBAsyncConnectionError, match="Failed to connect to IB"):
                await connector.connect_async()
                
        asyncio.run(test_connect())

    @pytest.mark.unit
    def test_connector_connection_status(self):
        """Test connection status check."""
        connector = IBAsyncExecutionConnector()
        connector.ib.isConnected.return_value = False

        # Test when not connected
        assert not connector.is_connected()

        # Test when connected
        connector._connected = True
        connector.ib.isConnected.return_value = True
        assert connector.is_connected()

        # Test using ib.isConnected method
        connector.ib.isConnected.return_value = False
        connector._connected = True
        assert not connector.is_connected()

        connector.ib.isConnected.return_value = True
        assert connector.is_connected()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_place_order_readonly_mode(self):
        """Test placing order in readonly mode."""
        connector = IBAsyncExecutionConnector(readonly=True)
        connector._connected = True
        connector.ib.isConnected.return_value = True

        order_request = OrderRequest(
            symbol="AAPL", side=OrderSide.BUY, order_type=OrderType.MARKET, quantity=100
        )

        with pytest.raises(
            IBAsyncOrderError, match="Cannot place order in readonly mode"
        ):
            await connector.place_order_async(order_request)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_place_order_not_connected(self):
        """Test placing order when not connected."""
        connector = IBAsyncExecutionConnector(readonly=False)
        connector._connected = False
        # Make connect fail
        connector.ib.connectAsync = AsyncMock(side_effect=Exception("Connection failed"))

        order_request = OrderRequest(
            symbol="AAPL", side=OrderSide.BUY, order_type=OrderType.MARKET, quantity=100
        )

        with pytest.raises(IBAsyncConnectionError, match="Failed to connect to IB"):
            await connector.place_order_async(order_request)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_place_order_success(self):
        """Test successful order placement."""
        connector = IBAsyncExecutionConnector(readonly=False)
        connector._connected = True
        connector.ib.isConnected.return_value = True
        connector.ib.qualifyContractsAsync = AsyncMock(return_value=[Mock()])

        # Mock IB components
        mock_contract = Mock()
        mock_order = Mock()
        mock_trade = Mock()
        mock_trade.orderId = "12345"
        mock_trade.order.permId = "12345"
        mock_trade.orderStatus = Mock()
        mock_trade.orderStatus.status = "Submitted"
        mock_trade.orderStatus.filled = 0.0
        mock_trade.orderStatus.avgFillPrice = 0.0
        mock_trade.orderStatus.time = datetime.now()
        mock_trade.order.totalQuantity = 100.0
        mock_trade.order.lmtPrice = None
        mock_trade.order.auxPrice = None

        with patch.object(
            connector, "_create_contract", return_value=mock_contract
        ), patch.object(
            connector, "_create_order", return_value=mock_order
        ), patch.object(
            connector.ib, "placeOrderAsync", return_value=mock_trade
        ):

            order_request = OrderRequest(
                symbol="AAPL",
                side=OrderSide.BUY,
                order_type=OrderType.MARKET,
                quantity=100,
            )

            result = await connector.place_order_async(order_request)

            assert isinstance(result, OrderResult)
            assert result.order_id == "12345"
            assert result.status == OrderStatus.SUBMITTED
            assert connector._orders["12345"] == mock_trade

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_place_order_ib_error(self):
        """Test order placement with IB error."""
        connector = IBAsyncExecutionConnector(readonly=False)
        connector._connected = True
        connector.ib.isConnected.return_value = True
        connector.ib.qualifyContractsAsync = AsyncMock(return_value=[Mock()])

        with patch.object(
            connector, "_create_contract", return_value=Mock()
        ), patch.object(connector, "_create_order", return_value=Mock()), patch.object(
            connector.ib, "placeOrderAsync", side_effect=Exception("IB Error")
        ):

            order_request = OrderRequest(
                symbol="AAPL",
                side=OrderSide.BUY,
                order_type=OrderType.MARKET,
                quantity=100,
            )

            with pytest.raises(IBAsyncOrderError, match="Failed to place order"):
                await connector.place_order_async(order_request)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_cancel_order_success(self):
        """Test successful order cancellation."""
        connector = IBAsyncExecutionConnector()
        connector._connected = True
        connector.ib.isConnected.return_value = True

        # Mock existing order
        mock_trade = Mock()
        mock_trade.order.permId = "12345"
        connector._orders["12345"] = mock_trade

        with patch.object(
            connector.ib, "cancelOrderAsync", new_callable=AsyncMock
        ) as mock_cancel:
            await connector.cancel_order_async("12345")
            mock_cancel.assert_called_once_with(mock_trade.order)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_cancel_order_not_found(self):
        """Test cancelling non-existent order."""
        connector = IBAsyncExecutionConnector()
        connector._connected = True
        connector.ib.isConnected.return_value = True

        with pytest.raises(IBAsyncOrderError, match="Order 12345 not found"):
            await connector.cancel_order_async("12345")

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_cancel_order_not_connected(self):
        """Test cancelling order when not connected."""
        connector = IBAsyncExecutionConnector()
        connector._connected = False
        # Make connect fail
        connector.ib.connectAsync = AsyncMock(side_effect=Exception("Connection failed"))

        with pytest.raises(IBAsyncConnectionError, match="Failed to connect to IB"):
            await connector.cancel_order_async("12345")

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_account_success(self):
        """Test successful account info retrieval."""
        connector = IBAsyncExecutionConnector()
        connector._connected = True
        connector.ib.isConnected.return_value = True

        # Mock account info
        mock_cash = Mock(tag="TotalCashValue", value="100000.0")
        mock_net_liq = Mock(tag="NetLiquidation", value="150000.0")
        mock_buying_power = Mock(tag="BuyingPower", value="200000.0")

        with patch.object(
            connector.ib, "accountSummaryAsync", new_callable=AsyncMock
        ) as mock_summary:
            mock_summary.return_value = [mock_cash, mock_net_liq, mock_buying_power]

            result = await connector.get_account_async()

            assert isinstance(result, AccountInfo)
            assert result.cash == 100000.0
            assert result.portfolio_value == 150000.0
            assert result.buying_power == 200000.0

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_account_not_connected(self):
        """Test account info retrieval when not connected."""
        connector = IBAsyncExecutionConnector()
        connector._connected = False
        # Make connect fail
        connector.ib.connectAsync = AsyncMock(side_effect=Exception("Connection failed"))

        with pytest.raises(IBAsyncConnectionError, match="Failed to connect to IB"):
            await connector.get_account_async()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_positions_success(self):
        """Test successful positions retrieval."""
        connector = IBAsyncExecutionConnector()
        connector._connected = True
        connector.ib.isConnected.return_value = True

        # Mock positions
        mock_position1 = Mock()
        mock_position1.contract.symbol = "AAPL"
        mock_position1.position = 100
        mock_position1.avgCost = 150.0

        mock_position2 = Mock()
        mock_position2.contract.symbol = "GOOGL"
        mock_position2.position = -50
        mock_position2.avgCost = 2500.0

        with patch.object(
            connector.ib, "positionsAsync", new_callable=AsyncMock
        ) as mock_positions:
            mock_positions.return_value = [mock_position1, mock_position2]

            result = await connector.get_positions_async()

            assert len(result) == 2

            # Check AAPL position
            aapl_position = next(p for p in result if p.symbol == "AAPL")
            assert aapl_position.quantity == 100
            assert aapl_position.cost_basis == 15000.0

            # Check GOOGL position
            googl_position = next(p for p in result if p.symbol == "GOOGL")
            assert (
                googl_position.quantity == 50
            )  # Quantity is absolute in Position object?
            # Wait, Position object quantity is float.
            # In ib_async_execution.py: quantity=float(abs(pos.position))
            assert googl_position.quantity == 50.0
            assert (
                googl_position.cost_basis == -125000.0
            )  # pos.position * pos.avgCost = -50 * 2500.0

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_positions_not_connected(self):
        """Test positions retrieval when not connected."""
        connector = IBAsyncExecutionConnector()
        connector._connected = False
        # Make connect fail
        connector.ib.connectAsync = AsyncMock(side_effect=Exception("Connection failed"))

        with pytest.raises(IBAsyncConnectionError, match="Failed to connect to IB"):
            await connector.get_positions_async()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_market_data_not_connected(self):
        """Test market data retrieval when not connected."""
        connector = IBAsyncExecutionConnector()
        connector._connected = False
        # Make connect fail
        connector.ib.connectAsync = AsyncMock(side_effect=Exception("Connection failed"))

        with pytest.raises(IBAsyncConnectionError, match="Not connected to IB"):
            await connector.get_market_data("AAPL")

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_market_data_success(self):
        """Test successful market data retrieval."""
        connector = IBAsyncExecutionConnector()
        connector._connected = True
        connector.ib.isConnected.return_value = True

        # Mock ticker data
        mock_ticker = Mock()
        mock_ticker.last = 150.0
        mock_ticker.bid = 149.0
        mock_ticker.ask = 151.0
        mock_ticker.midpoint.return_value = 150.0
        mock_ticker.close = 148.0
        mock_ticker.volume = 1000

        # Configure mock
        mock_bar = Mock()
        mock_bar.high = 151.0
        mock_bar.low = 149.0
        mock_bar.close = 150.0
        mock_bar.volume = 1000
        
        # Force manual conversion path by making util.df fail
        mock_ib_async.util.df.side_effect = AttributeError("Mocked error")

        connector.ib.reqMktDataAsync = AsyncMock(return_value=mock_ticker)
        connector.ib.reqHistoricalDataAsync = AsyncMock(return_value=[mock_bar]) # Mock list of bars

        result = await connector.get_market_data("AAPL")

        assert result["close"].iloc[-1] == 150.0
        # last/bid/ask are not returned for default "mid" type
        assert result["volume"].iloc[-1] == 1000

    @pytest.mark.unit
    def test_create_contract_stock(self):
        """Test creating stock contract."""
        connector = IBAsyncExecutionConnector()

        contract = connector._create_contract("AAPL", "STK", "SMART")

        assert contract.symbol == "AAPL"
        assert contract.secType == "STK"
        assert contract.exchange == "SMART"
        assert contract.currency == "USD"

    @pytest.mark.unit
    def test_create_contract_options(self):
        """Test creating options contract."""
        connector = IBAsyncExecutionConnector()

        contract = connector._create_contract(
            "AAPL",
            "OPT",
            "SMART",
            lastTradeDateOrContractMonth="20240120",
            strike=150.0,
            right="CALL",
        )

        assert contract.symbol == "AAPL"
        assert contract.secType == "OPT"
        assert contract.exchange == "SMART"
        assert contract.lastTradeDateOrContractMonth == "20240120"
        assert contract.strike == 150.0
        assert contract.right == "CALL"

    @pytest.mark.unit
    def test_create_contract_error(self):
        """Test contract creation error."""
        connector = IBAsyncExecutionConnector()

        with patch(
            "quantchain.connectors.ib_async_execution.Contract",
            side_effect=Exception("Contract error"),
        ):
            with pytest.raises(IBAsyncContractError, match="Failed to create contract"):
                connector._create_contract("INVALID", "INVALID", "SMART")

    @pytest.mark.unit
    def test_create_order_market(self):
        """Test creating market order."""
        connector = IBAsyncExecutionConnector()

        order_request = OrderRequest(
            symbol="AAPL", side=OrderSide.BUY, order_type=OrderType.MARKET, quantity=100
        )

        order = connector._create_order(order_request)

        assert order.action == "BUY"
        assert order.orderType == "MKT"
        assert order.totalQuantity == 100.0

    @pytest.mark.unit
    def test_create_order_limit(self):
        """Test creating limit order."""
        connector = IBAsyncExecutionConnector()

        order_request = OrderRequest(
            symbol="AAPL",
            side=OrderSide.SELL,
            order_type=OrderType.LIMIT,
            quantity=50,
            price=150.0,
        )

        order = connector._create_order(order_request)

        assert order.action == "SELL"
        assert order.orderType == "LMT"
        assert order.action == "SELL"
        assert order.orderType == "LMT"
        assert order.totalQuantity == 50.0
        assert order.lmtPrice == 150.0

    @pytest.mark.unit
    def test_create_order_stop(self):
        """Test creating stop order."""
        connector = IBAsyncExecutionConnector()

        order_request = OrderRequest(
            symbol="AAPL",
            side=OrderSide.BUY,
            order_type=OrderType.STOP,
            quantity=100,
            stop_price=155.0,
        )

        order = connector._create_order(order_request)

        assert order.action == "BUY"
        assert order.orderType == "STP"
        assert order.action == "BUY"
        assert order.orderType == "STP"
        assert order.totalQuantity == 100.0
        assert order.auxPrice == 155.0

    @pytest.mark.unit
    def test_create_order_stop_limit(self):
        """Test creating stop-limit order."""
        connector = IBAsyncExecutionConnector()

        order_request = OrderRequest(
            symbol="AAPL",
            side=OrderSide.SELL,
            order_type=OrderType.STOP_LIMIT,
            quantity=75,
            stop_price=155.0,
            price=154.5,
        )

        order = connector._create_order(order_request)

        assert order.action == "SELL"
        assert order.orderType == "STPLMT"
        assert order.action == "SELL"
        assert order.orderType == "STPLMT"
        assert order.totalQuantity == 75.0
        assert order.auxPrice == 155.0  # Stop price
        assert order.lmtPrice == 154.5  # Limit price

    @pytest.mark.unit
    def test_create_order_unsupported_type(self):
        """Test creating order with unsupported type."""
        connector = IBAsyncExecutionConnector()

        order_request = OrderRequest(
            symbol="AAPL",
            side=OrderSide.BUY,
            order_type=OrderType.TRAILING_STOP,
            quantity=100,
        )

        with pytest.raises(IBAsyncOrderError, match="Unsupported order type"):
            connector._create_order(order_request)

    @pytest.mark.unit
    def test_order_side_mapping(self):
        """Test order side mapping."""
        connector = IBAsyncExecutionConnector()

        # Test BUY side
        buy_order = OrderRequest(
            symbol="AAPL", side=OrderSide.BUY, order_type=OrderType.MARKET, quantity=100
        )
        order = connector._create_order(buy_order)
        assert order.action == "BUY"

        # Test SELL side
        sell_order = OrderRequest(
            symbol="AAPL",
            side=OrderSide.SELL,
            order_type=OrderType.MARKET,
            quantity=100,
        )
        order = connector._create_order(sell_order)
        assert order.action == "SELL"

    @pytest.mark.unit
    def test_order_type_mapping(self):
        """Test order type mapping."""
        connector = IBAsyncExecutionConnector()

        # Test various order types
        market_order = OrderRequest("AAPL", OrderSide.BUY, OrderType.MARKET, 100)
        order = connector._create_order(market_order)
        assert order.orderType == "MKT"

        limit_order = OrderRequest(
            "AAPL", OrderSide.BUY, OrderType.LIMIT, 100, price=150.0
        )
        order = connector._create_order(limit_order)
        assert order.orderType == "LMT"

        stop_order = OrderRequest(
            "AAPL", OrderSide.BUY, OrderType.STOP, 100, stop_price=155.0
        )
        order = connector._create_order(stop_order)
        assert order.orderType == "STP"

        stop_limit_order = OrderRequest(
            "AAPL",
            OrderSide.BUY,
            OrderType.STOP_LIMIT,
            100,
            stop_price=155.0,
            price=154.5,
        )
        order = connector._create_order(stop_limit_order)
        assert order.orderType == "STPLMT"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_error_handling_wrapper_success(self):
        """Test error handling wrapper with successful operation."""
        connector = IBAsyncExecutionConnector()

        async def successful_operation():
            return "success"

        result = await connector._handle_ib_errors(
            successful_operation, "test operation"
        )
        assert result == "success"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_error_handling_wrapper_ib_error(self):
        """Test error handling wrapper with IB error."""
        connector = IBAsyncExecutionConnector()

        async def failing_operation():
            raise Exception("IB API error")

        with pytest.raises(IBAsyncExecutionError, match="test operation failed"):
            await connector._handle_ib_errors(failing_operation, "test operation")

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_validate_order_request_valid(self):
        """Test validation of valid order request."""
        connector = IBAsyncExecutionConnector()

        valid_order = OrderRequest(
            symbol="AAPL", side=OrderSide.BUY, order_type=OrderType.MARKET, quantity=100
        )

        # Should not raise exception
        connector._validate_order_request(valid_order)

    @pytest.mark.unit
    def test_validate_order_request_missing_symbol(self):
        """Test validation of order with missing symbol."""
        connector = IBAsyncExecutionConnector()

        invalid_order = OrderRequest(
            symbol="", side=OrderSide.BUY, order_type=OrderType.MARKET, quantity=100
        )

        with pytest.raises(IBAsyncOrderError, match="Symbol is required"):
            connector._validate_order_request(invalid_order)

    @pytest.mark.unit
    def test_validate_order_request_invalid_quantity(self):
        """Test validation of order with invalid quantity."""
        connector = IBAsyncExecutionConnector()

        invalid_order = OrderRequest(
            symbol="AAPL", side=OrderSide.BUY, order_type=OrderType.MARKET, quantity=0
        )

        with pytest.raises(IBAsyncOrderError, match="Quantity must be positive"):
            connector._validate_order_request(invalid_order)

    @pytest.mark.unit
    def test_validate_order_request_limit_without_price(self):
        """Test validation of limit order without price."""
        connector = IBAsyncExecutionConnector()

        invalid_order = OrderRequest(
            symbol="AAPL",
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,  # Start as MARKET to pass init validation
            quantity=100,
        )
        # Change to LIMIT to trigger connector validation
        invalid_order.order_type = OrderType.LIMIT

        with pytest.raises(IBAsyncOrderError, match="Limit price is required"):
            connector._validate_order_request(invalid_order)

    @pytest.mark.unit
    def test_validate_order_request_stop_without_price(self):
        """Test validation of stop order without price."""
        connector = IBAsyncExecutionConnector()

        invalid_order = OrderRequest(
            symbol="AAPL",
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,  # Start as MARKET to pass init validation
            quantity=100,
        )
        # Change to STOP to trigger connector validation
        invalid_order.order_type = OrderType.STOP

        with pytest.raises(IBAsyncOrderError, match="Stop price is required"):
            connector._validate_order_request(invalid_order)

    @pytest.mark.unit
    def test_market_status_check(self):
        """Test market status checking."""
        connector = IBAsyncExecutionConnector()
        connector._connected = True
        connector.ib.isConnected.return_value = True

        # Mock IB connection status
        connector.ib = Mock()
        connector.ib.isConnected.return_value = True
        connector.ib.positions.return_value = []
        assert connector.is_market_open() is True

        connector.ib.isConnected.return_value = False
        assert connector.is_market_open() is False

    @pytest.mark.unit
    def test_clean_market_data_cache(self):
        """Test market data cache cleanup."""
        connector = IBAsyncExecutionConnector()

        # Add some cached data
        connector._market_data_cache["AAPL"] = Mock()
        connector._market_data_cache["GOOGL"] = Mock()

        assert len(connector._market_data_cache) == 2

        # Clear cache
        connector.clear_market_data_cache()

        assert len(connector._market_data_cache) == 0

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_order_status_existing(self):
        """Test getting status of existing order."""
        connector = IBAsyncExecutionConnector()
        connector._connected = True
        connector.ib.isConnected.return_value = True

        # Mock existing order
        mock_trade = Mock()
        mock_trade.order.permId = "12345"
        mock_trade.order.totalQuantity = 100.0
        mock_trade.orderStatus.status = "Filled"
        mock_trade.orderStatus.filled = 100.0
        mock_trade.orderStatus.avgFillPrice = 150.0
        connector._orders["12345"] = mock_trade

        status = await connector.get_order_status_async("12345")
        assert status == OrderStatus.FILLED

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_order_status_not_found(self):
        """Test getting status of non-existent order."""
        connector = IBAsyncExecutionConnector()

        with pytest.raises(IBAsyncOrderError, match="Order 12345 not found"):
            await connector.get_order_status_async("12345")
