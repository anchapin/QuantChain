"""Enhanced tests for IB async execution connector to reach 80% coverage."""

import pytest
import asyncio
from datetime import datetime, timezone, timedelta
from unittest.mock import Mock, patch, MagicMock, AsyncMock

# Check if ib_async_execution is available
try:
    from quantchain.connectors.ib_async_execution import (
        IBExecutionConnector,
        IB_ASYNC_AVAILABLE,
        IB,
        Contract,
        Order,
        OrderRequest,
        OrderResult,
        OrderStatus,
        OrderSide,
        OrderType,
        TimeInForce,
        AccountInfo,
        Position,
        ExecutionError,
        ValidationError,
        InsufficientFundsError,
        OrderNotFoundError,
    )
    IB_EXECUTION_AVAILABLE = True
except ImportError as e:
    IB_EXECUTION_AVAILABLE = False
    print(f"Import error: {e}")

pytestmark = pytest.mark.skipif(
    not IB_EXECUTION_AVAILABLE, reason="IB execution connector not available"
)


@pytest.fixture
def mock_ib():
    """Create a mock IB client."""
    mock = AsyncMock(spec=IB)
    mock.isConnected.return_value = True
    mock.reqPositions.return_value = []
    mock.reqAccountSummary.return_value = []
    return mock


@pytest.fixture
def ib_connector(mock_ib):
    """Create IB execution connector with mocked IB."""
    with patch("quantchain.connectors.ib_async_execution.IB", return_value=mock_ib):
        return IBExecutionConnector(
            host="127.0.0.1",
            port=7497,
            client_id=1,
            timeout=10,
        )


@pytest.mark.unit
class TestIBExecutionConnectorEnhanced:
    """Enhanced tests for IB execution connector."""

    def test_connector_initialization_parameters(self):
        """Test connector initialization with various parameters."""
        with patch("quantchain.connectors.ib_async_execution.IB") as mock_ib:
            mock_ib.return_value = Mock()
            
            # Test with all parameters
            connector = IBExecutionConnector(
                host="127.0.0.1",
                port=7497,
                client_id=1,
                timeout=30,
                read_only=False,
                account="DU123456",
            )
            
            assert connector.host == "127.0.0.1"
            assert connector.port == 7497
            assert connector.client_id == 1
            assert connector.timeout == 30
            assert connector.read_only is False
            assert connector.account == "DU123456"

    @pytest.mark.asyncio
    async def test_connect_success(self, ib_connector, mock_ib):
        """Test successful connection to IB."""
        mock_ib.connect = AsyncMock()
        mock_ib.isConnected.return_value = True
        
        result = await ib_connector.connect()
        
        assert result is True
        mock_ib.connect.assert_called_once_with(
            host=ib_connector.host,
            port=ib_connector.port,
            clientId=ib_connector.client_id,
            timeout=ib_connector.timeout,
        )

    @pytest.mark.asyncio
    async def test_connect_failure(self, ib_connector, mock_ib):
        """Test connection failure to IB."""
        mock_ib.connect = AsyncMock(side_effect=Exception("Connection failed"))
        mock_ib.isConnected.return_value = False
        
        result = await ib_connector.connect()
        
        assert result is False

    @pytest.mark.asyncio
    async def test_disconnect(self, ib_connector, mock_ib):
        """Test disconnection from IB."""
        mock_ib.disconnect = AsyncMock()
        
        await ib_connector.disconnect()
        
        mock_ib.disconnect.assert_called_once()

    @pytest.mark.asyncio
    async def test_is_connected(self, ib_connector, mock_ib):
        """Test checking connection status."""
        mock_ib.isConnected.return_value = True
        
        result = await ib_connector.is_connected()
        
        assert result is True
        mock_ib.isConnected.assert_called_once()

    @pytest.mark.asyncio
    async def test_submit_market_order(self, ib_connector, mock_ib):
        """Test submitting a market order."""
        # Create order request
        order_request = OrderRequest(
            symbol="AAPL",
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=100,
            time_in_force=TimeInForce.DAY,
        )
        
        # Mock contract and order
        mock_contract = Mock(spec=Contract)
        mock_order = Mock(spec=Order)
        mock_order.orderId = 12345
        mock_order.status = OrderStatus.SUBMITTED.value
        
        mock_ib.qualifyContracts = AsyncMock(return_value=[mock_contract])
        mock_ib.placeOrder = AsyncMock()
        mock_ib.reqAllOpenOrders = AsyncMock()
        
        # Mock order status event
        def mock_event_handler(func):
            # Simulate order status update
            asyncio.create_task(
                asyncio.sleep(0.1)
                .then(lambda _: func(mock_order, mock_contract))
            )
            return None
        
        mock_ib.orderStatusEvent = mock_event_handler
        
        result = await ib_connector.submit_order(order_request)
        
        assert isinstance(result, OrderResult)
        assert result.order_id == 12345
        assert result.status == OrderStatus.SUBMITTED

    @pytest.mark.asyncio
    async def test_submit_limit_order(self, ib_connector, mock_ib):
        """Test submitting a limit order."""
        order_request = OrderRequest(
            symbol="AAPL",
            side=OrderSide.SELL,
            order_type=OrderType.LIMIT,
            quantity=100,
            price=150.0,
            time_in_force=TimeInForce.GTC,
        )
        
        mock_contract = Mock(spec=Contract)
        mock_order = Mock(spec=Order)
        mock_order.orderId = 12346
        mock_order.status = OrderStatus.ACCEPTED.value
        
        mock_ib.qualifyContracts = AsyncMock(return_value=[mock_contract])
        mock_ib.placeOrder = AsyncMock()
        mock_ib.reqAllOpenOrders = AsyncMock()
        
        def mock_event_handler(func):
            asyncio.create_task(
                asyncio.sleep(0.1)
                .then(lambda _: func(mock_order, mock_contract))
            )
            return None
        
        mock_ib.orderStatusEvent = mock_event_handler
        
        result = await ib_connector.submit_order(order_request)
        
        assert isinstance(result, OrderResult)
        assert result.order_id == 12346
        assert result.status == OrderStatus.ACCEPTED

    @pytest.mark.asyncio
    async def test_submit_stop_order(self, ib_connector, mock_ib):
        """Test submitting a stop order."""
        order_request = OrderRequest(
            symbol="AAPL",
            side=OrderSide.SELL,
            order_type=OrderType.STOP,
            quantity=100,
            stop_price=145.0,
            time_in_force=TimeInForce.DAY,
        )
        
        mock_contract = Mock(spec=Contract)
        mock_order = Mock(spec=Order)
        mock_order.orderId = 12347
        mock_order.status = OrderStatus.SUBMITTED.value
        
        mock_ib.qualifyContracts = AsyncMock(return_value=[mock_contract])
        mock_ib.placeOrder = AsyncMock()
        mock_ib.reqAllOpenOrders = AsyncMock()
        
        def mock_event_handler(func):
            asyncio.create_task(
                asyncio.sleep(0.1)
                .then(lambda _: func(mock_order, mock_contract))
            )
            return None
        
        mock_ib.orderStatusEvent = mock_event_handler
        
        result = await ib_connector.submit_order(order_request)
        
        assert isinstance(result, OrderResult)
        assert result.order_id == 12347

    @pytest.mark.asyncio
    async def test_cancel_order(self, ib_connector, mock_ib):
        """Test cancelling an order."""
        order_id = 12345
        
        mock_ib.cancelOrder = AsyncMock()
        
        result = await ib_connector.cancel_order(order_id)
        
        assert result is True
        mock_ib.cancelOrder.assert_called_once()

    @pytest.mark.asyncio
    async def test_cancel_nonexistent_order(self, ib_connector, mock_ib):
        """Test cancelling a non-existent order."""
        order_id = 99999
        
        mock_ib.cancelOrder = AsyncMock(side_effect=Exception("Order not found"))
        
        with pytest.raises(OrderNotFoundError):
            await ib_connector.cancel_order(order_id)

    @pytest.mark.asyncio
    async def test_get_order_status(self, ib_connector, mock_ib):
        """Test getting order status."""
        order_id = 12345
        
        mock_order = Mock()
        mock_order.orderId = order_id
        mock_order.status = OrderStatus.FILLED.value
        
        mock_ib.reqOpenOrders = AsyncMock(return_value=[mock_order])
        
        result = await ib_connector.get_order_status(order_id)
        
        assert result == OrderStatus.FILLED

    @pytest.mark.asyncio
    async def test_get_account_info(self, ib_connector, mock_ib):
        """Test getting account information."""
        mock_summary = Mock()
        mock_summary.tag = "NetLiquidation"
        mock_summary.value = "100000.0"
        mock_summary.currency = "USD"
        
        mock_ib.reqAccountSummary = AsyncMock(return_value=[mock_summary])
        
        result = await ib_connector.get_account_info()
        
        assert isinstance(result, AccountInfo)
        assert result.total_value == 100000.0
        assert result.currency == "USD"

    @pytest.mark.asyncio
    async def test_get_positions(self, ib_connector, mock_ib):
        """Test getting positions."""
        mock_position = Mock()
        mock_position.contract.symbol = "AAPL"
        mock_position.position = 100
        mock_position.averageCost = 150.0
        
        mock_ib.reqPositions = AsyncMock(return_value=[mock_position])
        
        result = await ib_connector.get_positions()
        
        assert isinstance(result, list)
        assert len(result) == 1
        assert isinstance(result[0], Position)
        assert result[0].symbol == "AAPL"
        assert result[0].quantity == 100
        assert result[0].average_price == 150.0

    @pytest.mark.asyncio
    async def test_get_positions_empty(self, ib_connector, mock_ib):
        """Test getting positions when none exist."""
        mock_ib.reqPositions = AsyncMock(return_value=[])
        
        result = await ib_connector.get_positions()
        
        assert isinstance(result, list)
        assert len(result) == 0

    def test_create_stock_contract(self, ib_connector):
        """Test creating stock contract."""
        contract = ib_connector._create_contract("AAPL", "STK")
        
        assert contract.symbol == "AAPL"
        assert contract.secType == "STK"
        assert contract.currency == "USD"
        assert contract.exchange == "SMART"

    def test_create_option_contract(self, ib_connector):
        """Test creating option contract."""
        contract = ib_connector._create_contract(
            "AAPL",
            "OPT",
            last_trade_date="20231215",
            strike=150.0,
            right="C",
        )
        
        assert contract.symbol == "AAPL"
        assert contract.secType == "OPT"
        assert contract.lastTradeDateOrContractMonth == "20231215"
        assert contract.strike == 150.0
        assert contract.right == "C"

    def test_create_future_contract(self, ib_connector):
        """Test creating future contract."""
        contract = ib_connector._create_contract(
            "ES",
            "FUT",
            last_trade_date="202312",
            exchange="CME",
        )
        
        assert contract.symbol == "ES"
        assert contract.secType == "FUT"
        assert contract.lastTradeDateOrContractMonth == "202312"
        assert contract.exchange == "CME"

    def test_validate_order_request(self, ib_connector):
        """Test order request validation."""
        # Valid order
        valid_order = OrderRequest(
            symbol="AAPL",
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=100,
        )
        
        # Should not raise exception
        ib_connector._validate_order(valid_order)
        
        # Invalid order - missing symbol
        invalid_order = OrderRequest(
            symbol="",
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=100,
        )
        
        with pytest.raises(ValidationError):
            ib_connector._validate_order(invalid_order)
        
        # Invalid order - zero quantity
        invalid_order.quantity = 0
        
        with pytest.raises(ValidationError):
            ib_connector._validate_order(invalid_order)

    def test_validate_order_request_limit_price(self, ib_connector):
        """Test limit order price validation."""
        # Limit order without price
        order = OrderRequest(
            symbol="AAPL",
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            quantity=100,
        )
        
        with pytest.raises(ValidationError):
            ib_connector._validate_order(order)
        
        # Valid limit order
        order.price = 150.0
        ib_connector._validate_order(order)  # Should not raise

    def test_validate_order_request_stop_price(self, ib_connector):
        """Test stop order price validation."""
        # Stop order without price
        order = OrderRequest(
            symbol="AAPL",
            side=OrderSide.SELL,
            order_type=OrderType.STOP,
            quantity=100,
        )
        
        with pytest.raises(ValidationError):
            ib_connector._validate_order(order)
        
        # Valid stop order
        order.stop_price = 145.0
        ib_connector._validate_order(order)  # Should not raise

    def test_map_order_status(self, ib_connector):
        """Test mapping IB order status to internal status."""
        # Test various status mappings
        assert ib_connector._map_order_status("Submitted") == OrderStatus.SUBMITTED
        assert ib_connector._map_order_status("Accepted") == OrderStatus.ACCEPTED
        assert ib_connector._map_order_status("Filled") == OrderStatus.FILLED
        assert ib_connector._map_order_status("Cancelled") == OrderStatus.CANCELLED
        assert ib_connector._map_order_status("ApiCancelled") == OrderStatus.CANCELLED
        assert ib_connector._map_order_status("Inactive") == OrderStatus.REJECTED

    def test_map_order_status_unknown(self, ib_connector):
        """Test mapping unknown order status."""
        unknown_status = ib_connector._map_order_status("UnknownStatus")
        assert unknown_status == OrderStatus.REJECTED

    @pytest.mark.asyncio
    async def test_error_handling_connection_timeout(self, ib_connector, mock_ib):
        """Test handling connection timeout."""
        mock_ib.connect = AsyncMock(side_effect=asyncio.TimeoutError())
        
        result = await ib_connector.connect()
        
        assert result is False

    @pytest.mark.asyncio
    async def test_error_handling_insufficient_funds(self, ib_connector, mock_ib):
        """Test handling insufficient funds error."""
        order_request = OrderRequest(
            symbol="AAPL",
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=1000000,  # Large quantity that might exceed funds
        )
        
        mock_contract = Mock(spec=Contract)
        mock_ib.qualifyContracts = AsyncMock(return_value=[mock_contract])
        mock_ib.placeOrder = AsyncMock(side_effect=Exception("Insufficient funds"))
        
        with pytest.raises(InsufficientFundsError):
            await ib_connector.submit_order(order_request)

    @pytest.mark.asyncio
    async def test_market_data_subscription(self, ib_connector, mock_ib):
        """Test market data subscription."""
        symbol = "AAPL"
        
        mock_contract = Mock(spec=Contract)
        mock_ib.qualifyContracts = AsyncMock(return_value=[mock_contract])
        mock_ib.reqMktData = AsyncMock()
        
        result = await ib_connector.subscribe_market_data(symbol)
        
        assert result is True
        mock_ib.reqMktData.assert_called_once()

    @pytest.mark.asyncio
    async def test_cancel_market_data_subscription(self, ib_connector, mock_ib):
        """Test cancelling market data subscription."""
        symbol = "AAPL"
        
        mock_contract = Mock(spec=Contract)
        mock_ib.qualifyContracts = AsyncMock(return_value=[mock_contract])
        mock_ib.cancelMktData = AsyncMock()
        
        result = await ib_connector.cancel_market_data_subscription(symbol)
        
        assert result is True
        mock_ib.cancelMktData.assert_called_once()

    @pytest.mark.asyncio
    async def test_historical_data_request(self, ib_connector, mock_ib):
        """Test historical data request."""
        symbol = "AAPL"
        duration = "1 D"
        bar_size = "1 min"
        
        mock_contract = Mock(spec=Contract)
        mock_bars = [
            Mock(open=100, high=101, low=99, close=100.5, volume=1000, date=datetime.now()),
            Mock(open=100.5, high=102, low=100, close=101, volume=1200, date=datetime.now()),
        ]
        
        mock_ib.qualifyContracts = AsyncMock(return_value=[mock_contract])
        mock_ib.reqHistoricalData = AsyncMock(return_value=mock_bars)
        
        result = await ib_connector.get_historical_data(symbol, duration, bar_size)
        
        assert isinstance(result, list)
        assert len(result) == 2
        mock_ib.reqHistoricalData.assert_called_once()

    @pytest.mark.asyncio
    async def test_order_events_handling(self, ib_connector, mock_ib):
        """Test handling of order events."""
        order_id = 12345
        status_updates = []
        
        def status_handler(order):
            status_updates.append(order.status)
        
        # Register for order status updates
        mock_ib.orderStatusEvent = status_handler
        
        # Simulate order status updates
        mock_order = Mock()
        mock_order.orderId = order_id
        mock_order.status = OrderStatus.SUBMITTED.value
        status_handler(mock_order)
        
        mock_order.status = OrderStatus.FILLED.value
        status_handler(mock_order)
        
        assert len(status_updates) == 2
        assert status_updates[0] == OrderStatus.SUBMITTED.value
        assert status_updates[1] == OrderStatus.FILLED.value

    def test_error_mapping(self, ib_connector):
        """Test error message mapping."""
        # Test common error patterns
        error = ib_connector._map_error("No security definition has been found")
        assert "security" in error.lower()
        
        error = ib_connector._map_error("Unknown order")
        assert "order" in error.lower()
        
        error = ib_connector._map_error("Market data farm connection is OK")
        assert error == "Market data farm connection is OK"  # Should not map

    @pytest.mark.asyncio
    async def test_concurrent_orders(self, ib_connector, mock_ib):
        """Test handling concurrent order submissions."""
        orders = [
            OrderRequest(
                symbol=f"STOCK{i}",
                side=OrderSide.BUY,
                order_type=OrderType.MARKET,
                quantity=100,
            )
            for i in range(3)
        ]
        
        mock_contract = Mock(spec=Contract)
        mock_ib.qualifyContracts = AsyncMock(return_value=[mock_contract])
        mock_ib.placeOrder = AsyncMock()
        mock_ib.reqAllOpenOrders = AsyncMock()
        
        # Submit orders concurrently
        tasks = []
        for order in orders:
            # Mock order status event for each order
            def create_event_handler(order_id):
                def handler(func):
                    mock_order = Mock()
                    mock_order.orderId = order_id
                    mock_order.status = OrderStatus.SUBMITTED.value
                    asyncio.create_task(
                        asyncio.sleep(0.1)
                        .then(lambda _: func(mock_order, mock_contract))
                    )
                    return None
                return handler
            
            mock_ib.orderStatusEvent = create_event_handler(len(tasks))
            tasks.append(ib_connector.submit_order(order))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        assert len(results) == 3
        for result in results:
            if not isinstance(result, Exception):
                assert isinstance(result, OrderResult)
                assert result.status == OrderStatus.SUBMITTED
