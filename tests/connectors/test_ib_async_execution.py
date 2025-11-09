"""Tests for Interactive Brokers execution connector."""

import pytest
import asyncio
from datetime import datetime, timezone, timedelta
from unittest.mock import Mock, AsyncMock, patch, MagicMock

from quantchain.connectors.ib_async_execution import IBExecutionConnector
from quantchain.tools.trading_execution import (
    OrderRequest,
    OrderResult,
    OrderSide,
    OrderType,
    OrderStatus,
    TimeInForce,
    Position,
    AccountInfo,
    ValidationError,
    InsufficientFundsError,
    OrderNotFoundError,
    ExecutionError,
)

# Mock ib_async module before importing the connector
ib_async_mock = MagicMock()
ib_async_mock.IB = MagicMock
ib_async_mock.Stock = MagicMock
ib_async_mock.Forex = MagicMock
ib_async_mock.Future = MagicMock
ib_async_mock.Option = MagicMock
ib_async_mock.Contract = MagicMock
ib_async_mock.Order = MagicMock
ib_async_mock.MarketOrder = MagicMock
ib_async_mock.LimitOrder = MagicMock
ib_async_mock.StopOrder = MagicMock
ib_async_mock.StopLimitOrder = MagicMock
ib_async_mock.Trade = MagicMock
# Add exception classes
ib_async_mock.ConnectionRefusedError = ConnectionRefusedError

# Create a proper RequestError mock
class MockRequestError(Exception):
    def __init__(self, message, code=None):
        super().__init__(message)
        self.code = code

ib_async_mock.RequestError = MockRequestError


# Patch RequestError at class level to ensure all imports use the mock
@patch("quantchain.connectors.ib_async_execution.RequestError", new=MockRequestError)
@pytest.mark.unit
class TestIBExecutionConnector:
    """Test cases for IBExecutionConnector."""

    @pytest.fixture
    def mock_ib_client(self):
        """Mock IB client."""
        with patch("quantchain.connectors.ib_async_execution.IB") as mock_ib_class:
            client = Mock()
            mock_ib_class.return_value = client
            
            # Mock async methods
            client.connectAsync = AsyncMock()
            client.qualifyContractsAsync = AsyncMock()
            client.placeOrder = Mock()
            client.cancelOrder = Mock()
            client.positions = Mock(return_value=[])
            client.accountSummary = Mock(return_value=[])
            client.trades = Mock(return_value=[])
            client.openOrders = Mock(return_value=[])
            client.fills = Mock(return_value=[])
            client.reqContractDetails = Mock(return_value=[])
            client.disconnect = Mock()
            
            # Mock IB.RaiseRequestErrors
            ib_async_mock.IB.RaiseRequestErrors = True
            
            yield client

    @pytest.fixture
    def mock_contract(self):
        """Mock IB Contract object."""
        contract = Mock()
        contract.conId = 12345
        contract.symbol = "AAPL"
        contract.secType = "STK"
        contract.exchange = "SMART"
        contract.currency = "USD"
        return contract

    @pytest.fixture
    def mock_trade(self):
        """Mock IB Trade object."""
        trade = Mock()
        trade.orderId = "123456"
        trade.clientId = "client_123"
        trade.action = "BUY"
        trade.totalQuantity = 100.0
        contract = Mock()
        contract.symbol = "AAPL"
        contract.secType = "STK"
        trade.contract = contract
        
        order_status = Mock()
        order_status.status = "Filled"
        order_status.filled = 100.0
        order_status.remaining = 0.0
        order_status.avgFillPrice = 150.25
        trade.orderStatus = order_status
        
        order = Mock()
        order.orderType = "MKT"
        order.lmtPrice = None
        order.auxPrice = None
        order.tif = "DAY"
        trade.order = order
        
        trade.log = []
        trade.fills = []
        
        return trade

    @pytest.fixture
    def connector(self, mock_ib_client):
        """Create IB execution connector with mocked client."""
        return IBExecutionConnector(
            host="127.0.0.1",
            port=7497,
            client_id=1,
            timeout=10
        )

    # Initialization Tests
    def test_initialization(self, mock_ib_client):
        """Test connector initialization."""
        connector = IBExecutionConnector(
            host="127.0.0.1",
            port=7497,
            client_id=1,
            timeout=10,
            readonly=False
        )
        
        assert connector.host == "127.0.0.1"
        assert connector.port == 7497
        assert connector.client_id == 1
        assert connector.timeout == 10
        assert connector.readonly is False
        mock_ib_client.connectAsync.assert_called_once()

    def test_connection_refused(self):
        """Test ConnectionRefusedError handling."""
        with patch("quantchain.connectors.ib_async_execution.IB") as mock_ib_class:
            client = Mock()
            client.connectAsync = AsyncMock(side_effect=ConnectionRefusedError("Connection refused"))
            mock_ib_class.return_value = client
            
            with pytest.raises(ExecutionError) as exc_info:
                IBExecutionConnector(host="127.0.0.1", port=7497, client_id=1)
            
            assert "Async operation failed" in str(exc_info.value)
            assert "Connection refused" in str(exc_info.value)

    def test_connection_timeout(self):
        """Test timeout handling during connection."""
        with patch("quantchain.connectors.ib_async_execution.IB") as mock_ib_class:
            client = Mock()
            client.connectAsync = AsyncMock(side_effect=asyncio.TimeoutError())
            mock_ib_class.return_value = client
            
            with pytest.raises(ExecutionError) as exc_info:
                IBExecutionConnector(host="127.0.0.1", port=7497, client_id=1)
            
            assert "Operation timed out" in str(exc_info.value)

    # Contract Creation Tests
    def test_create_stock_contract(self, connector, mock_contract):
        """Test Stock contract creation for 'AAPL'."""
        from quantchain.connectors import ib_async_execution
        
        with patch.object(ib_async_execution, "Stock", return_value=mock_contract) as mock_stock:
            contract = connector._create_contract("AAPL")
            
            mock_stock.assert_called_once_with("AAPL", "SMART", "USD")
            assert contract == mock_contract

    def test_create_forex_contract(self, connector):
        """Test Forex contract creation for 'EURUSD'."""
        from quantchain.connectors import ib_async_execution
        
        with patch.object(ib_async_execution, "Forex") as mock_forex:
            connector._create_contract("EURUSD")
            mock_forex.assert_called_once_with("EUR", "USD")

    def test_create_future_contract(self, connector):
        """Test Future contract creation for 'ESZ3'."""
        # Import the module and directly patch its attribute
        from quantchain.connectors import ib_async_execution
        
        with patch.object(ib_async_execution, "Future") as mock_future:
            # Debug by checking actual symbol processing
            result = connector._create_contract("ESZ3")
            
            
            
            mock_future.assert_called_once_with("ES", "202312", "", "", "")

    def test_create_option_contract(self, connector):
        """Test Option contract creation for 'AAPL 231215 150 C'."""
        from quantchain.connectors import ib_async_execution
        
        with patch.object(ib_async_execution, "Option") as mock_option:
            result = connector._create_contract("AAPL 231215 150 C")
            
            mock_option.assert_called_once_with("AAPL", "20231215", 150.0, "CALL", "")

    def test_qualify_contracts(self, connector, mock_contract):
        """Test contract qualification process."""
        connector.ib.qualifyContractsAsync = AsyncMock(return_value=[mock_contract])
        
        result = connector._qualify_contract(mock_contract)
        
        assert result == mock_contract
        connector.ib.qualifyContractsAsync.assert_called_once_with(mock_contract)

    # Order Placement Tests
    def test_place_stock_market_order(self, connector, mock_trade, mock_contract):
        """Test placing a market order for stock."""
        order = OrderRequest(
            symbol="AAPL",
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=100.0
        )
        
        with patch.object(connector, "_create_contract", return_value=mock_contract):
            with patch.object(connector, "_qualify_contract", return_value=mock_contract):
                with patch.object(connector, "_convert_order_to_ib"):
                    connector.ib.placeOrder.return_value = mock_trade
                    with patch.object(connector, "_convert_ib_order_to_result", return_value=OrderResult(
                        order_id="123456",
                        client_order_id=None,
                        symbol="AAPL",
                        side=OrderSide.BUY,
                        order_type=OrderType.MARKET,
                        quantity=100.0,
                        filled_quantity=0.0,
                        price=None,
                        stop_price=None,
                        avg_fill_price=None,
                        status=OrderStatus.PENDING,
                        timestamp=datetime.now(timezone.utc)
                    )):
                        result = connector.place_order(order)
                        
                        assert result.symbol == "AAPL"
                        assert result.side == OrderSide.BUY
                        assert result.order_type == OrderType.MARKET

    def test_place_limit_order(self, connector, mock_trade, mock_contract):
        """Test placing a limit order with price."""
        order = OrderRequest(
            symbol="AAPL",
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            quantity=100.0,
            price=150.50
        )
        
        with patch.object(connector, "_create_contract", return_value=mock_contract):
            with patch.object(connector, "_qualify_contract", return_value=mock_contract):
                with patch.object(connector, "_convert_order_to_ib"):
                    connector.ib.placeOrder.return_value = mock_trade
                    with patch.object(connector, "_convert_ib_order_to_result", return_value=OrderResult(
                        order_id="123456",
                        client_order_id=None,
                        symbol="AAPL",
                        side=OrderSide.BUY,
                        order_type=OrderType.LIMIT,
                        quantity=100.0,
                        filled_quantity=0.0,
                        price=150.50,
                        stop_price=None,
                        avg_fill_price=None,
                        status=OrderStatus.PENDING,
                        timestamp=datetime.now(timezone.utc)
                    )):
                        result = connector.place_order(order)
                        
                        assert result.price == 150.50
                        assert result.order_type == OrderType.LIMIT

    def test_place_stop_order(self, connector, mock_trade, mock_contract):
        """Test placing a stop order with stop price."""
        order = OrderRequest(
            symbol="AAPL",
            side=OrderSide.BUY,
            order_type=OrderType.STOP,
            quantity=100.0,
            stop_price=151.00
        )
        
        with patch.object(connector, "_create_contract", return_value=mock_contract):
            with patch.object(connector, "_qualify_contract", return_value=mock_contract):
                with patch.object(connector, "_convert_order_to_ib"):
                    connector.ib.placeOrder.return_value = mock_trade
                    with patch.object(connector, "_convert_ib_order_to_result", return_value=OrderResult(
                        order_id="123456",
                        client_order_id=None,
                        symbol="AAPL",
                        side=OrderSide.BUY,
                        order_type=OrderType.STOP,
                        quantity=100.0,
                        filled_quantity=0.0,
                        price=None,
                        stop_price=151.00,
                        avg_fill_price=None,
                        status=OrderStatus.PENDING,
                        timestamp=datetime.now(timezone.utc)
                    )):
                        result = connector.place_order(order)
                        
                        assert result.stop_price == 151.00
                        assert result.order_type == OrderType.STOP

    def test_place_stop_limit_order(self, connector, mock_trade, mock_contract):
        """Test placing a stop-limit order with both prices."""
        order = OrderRequest(
            symbol="AAPL",
            side=OrderSide.BUY,
            order_type=OrderType.STOP_LIMIT,
            quantity=100.0,
            price=150.50,
            stop_price=151.00
        )
        
        with patch.object(connector, "_create_contract", return_value=mock_contract):
            with patch.object(connector, "_qualify_contract", return_value=mock_contract):
                with patch.object(connector, "_convert_order_to_ib"):
                    connector.ib.placeOrder.return_value = mock_trade
                    with patch.object(connector, "_convert_ib_order_to_result", return_value=OrderResult(
                        order_id="123456",
                        client_order_id=None,
                        symbol="AAPL",
                        side=OrderSide.BUY,
                        order_type=OrderType.STOP_LIMIT,
                        quantity=100.0,
                        filled_quantity=0.0,
                        price=150.50,
                        stop_price=151.00,
                        avg_fill_price=None,
                        status=OrderStatus.PENDING,
                        timestamp=datetime.now(timezone.utc)
                    )):
                        result = connector.place_order(order)
                        
                        assert result.price == 150.50
                        assert result.stop_price == 151.00
                        assert result.order_type == OrderType.STOP_LIMIT

    def test_place_order_with_tif(self, connector, mock_trade, mock_contract):
        """Test placing an order with different TimeInForce options."""
        for tif in [TimeInForce.DAY, TimeInForce.GTC, TimeInForce.IOC, TimeInForce.FOK]:
            order = OrderRequest(
                symbol="AAPL",
                side=OrderSide.BUY,
                order_type=OrderType.LIMIT,
                quantity=100.0,
                price=150.50,
                time_in_force=tif
            )
            
            with patch.object(connector, "_create_contract", return_value=mock_contract):
                with patch.object(connector, "_qualify_contract", return_value=mock_contract):
                    with patch.object(connector, "_convert_order_to_ib") as mock_convert:
                        connector.ib.placeOrder.return_value = mock_trade
                        with patch.object(connector, "_convert_ib_order_to_result", return_value=OrderResult(
                            order_id="123456",
                            client_order_id=None,
                            symbol="AAPL",
                            side=OrderSide.BUY,
                            order_type=OrderType.LIMIT,
                            quantity=100.0,
                            filled_quantity=0.0,
                            price=150.50,
                            stop_price=None,
                            avg_fill_price=None,
                            status=OrderStatus.PENDING,
                            timestamp=datetime.now(timezone.utc)
                        )):
                            connector.place_order(order)
                            # Check that the order was converted with correct TIF
                            mock_convert.assert_called()
                            args, kwargs = mock_convert.call_args
                            assert args[0].time_in_force == tif

    def test_place_order_insufficient_funds(self, connector, mock_contract):
        """Test InsufficientFundsError when IB returns code 10147."""
        error = ib_async_mock.RequestError("Insufficient funds", code=10147)
        
        order = OrderRequest(
            symbol="AAPL",
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=100.0
        )
        
        with patch.object(connector, "_create_contract", return_value=mock_contract):
            with patch.object(connector, "_qualify_contract", return_value=mock_contract):
                with patch.object(connector, "_convert_order_to_ib"):
                    connector.ib.placeOrder.side_effect = error
                    
                    with pytest.raises(InsufficientFundsError):
                        connector.place_order(order)

    def test_place_order_invalid_contract(self, connector, mock_contract):
        """Test ValidationError when IB returns code 321."""
        error = ib_async_mock.RequestError("Invalid contract", code=321)
        
        order = OrderRequest(
            symbol="INVALID",
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=100.0
        )
        
        with patch.object(connector, "_create_contract", return_value=mock_contract):
            with patch.object(connector, "_qualify_contract", side_effect=error):
                
                with pytest.raises(ValidationError):
                    connector.place_order(order)

    def test_place_order_connection_error(self, connector, mock_contract):
        """Test handling of connection errors during order placement."""
        order = OrderRequest(
            symbol="AAPL",
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=100.0
        )
        
        with patch.object(connector, "_create_contract", return_value=mock_contract):
            with patch.object(connector, "_qualify_contract", return_value=mock_contract):
                with patch.object(connector, "_convert_order_to_ib"):
                    connector.ib.placeOrder.side_effect = ConnectionError("Lost connection")
                    
                    with pytest.raises(ExecutionError):
                        connector.place_order(order)

    # Order Management Tests
    def test_cancel_order(self, connector, mock_trade):
        """Test canceling a pending order."""
        connector._order_map["123456"] = mock_trade
        
        with patch.object(connector, "_convert_ib_order_to_result", return_value=OrderResult(
            order_id="123456",
            client_order_id=None,
            symbol="AAPL",
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=100.0,
            filled_quantity=0.0,
            price=None,
            stop_price=None,
            avg_fill_price=None,
            status=OrderStatus.CANCELLED,
            timestamp=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )):
            result = connector.cancel_order("123456")
            
            assert result.status == OrderStatus.CANCELLED
            connector.ib.cancelOrder.assert_called_once_with(mock_trade.order)

    def test_cancel_order_not_found(self, connector):
        """Test OrderNotFoundError when order doesn't exist."""
        with pytest.raises(OrderNotFoundError):
            connector.cancel_order("nonexistent")

    def test_get_order(self, connector, mock_trade):
        """Test retrieving order by ID."""
        connector._order_map["123456"] = mock_trade
        
        with patch.object(connector, "_convert_ib_order_to_result", return_value=OrderResult(
            order_id="123456",
            client_order_id=None,
            symbol="AAPL",
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=100.0,
            filled_quantity=100.0,
            price=None,
            stop_price=None,
            avg_fill_price=150.25,
            status=OrderStatus.FILLED,
            timestamp=datetime.now(timezone.utc)
        )):
            result = connector.get_order("123456")
            
            assert result.order_id == "123456"
            assert result.status == OrderStatus.FILLED
            assert result.filled_quantity == 100.0

    def test_get_order_not_found(self, connector):
        """Test OrderNotFoundError for non-existent order."""
        with pytest.raises(OrderNotFoundError):
            connector.get_order("nonexistent")

    def test_get_order_filled(self, connector, mock_trade):
        """Test retrieving a filled order with fill details."""
        mock_trade.orderStatus.filled = 100.0
        mock_trade.orderStatus.avgFillPrice = 150.25
        connector._order_map["123456"] = mock_trade
        
        with patch.object(connector, "_convert_ib_order_to_result", return_value=OrderResult(
            order_id="123456",
            client_order_id=None,
            symbol="AAPL",
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=100.0,
            filled_quantity=100.0,
            price=None,
            stop_price=None,
            avg_fill_price=150.25,
            status=OrderStatus.FILLED,
            timestamp=datetime.now(timezone.utc)
        )):
            result = connector.get_order("123456")
            
            assert result.filled_quantity == 100.0
            assert result.avg_fill_price == 150.25

    # Account and Position Tests
    def test_get_account(self, connector):
        """Test retrieving account information."""
        # Mock account summary
        account_summary = [
            Mock(tag="NetLiquidation", value="100000.0"),
            Mock(tag="AvailableFunds", value="95000.0"),
            Mock(tag="BuyingPower", value="190000.0"),
            Mock(tag="TotalCashValue", value="95000.0"),
        ]
        connector.ib.accountSummary.return_value = account_summary
        
        # Mock positions
        positions = [
            Mock(
                contract=Mock(symbol="AAPL", secType="STK"),
                position=100.0,
                avgCost=150.0
            )
        ]
        connector.ib.positions.return_value = positions
        
        with patch.object(connector, "get_positions", return_value=[
            Position(
                symbol="AAPL",
                quantity=100.0,
                avg_entry_price=150.0,
                current_price=155.0,
                market_value=15500.0,
                unrealized_pnl=500.0,
                unrealized_pnl_percent=3.33
            )
        ]):
            result = connector.get_account()
            
            assert isinstance(result, AccountInfo)
            assert result.buying_power == 190000.0
            assert result.cash == 95000.0
            assert result.portfolio_value == 100000.0
            assert len(result.positions) == 1
            assert result.positions[0].symbol == "AAPL"

    def test_get_positions(self, connector):
        """Test retrieving position list."""
        # Mock IB positions
        ib_positions = [
            Mock(
                contract=Mock(symbol="AAPL", secType="STK"),
                position=100.0,
                avgCost=150.0
            ),
            Mock(
                contract=Mock(symbol="MSFT", secType="STK"),
                position=-50.0,
                avgCost=250.0
            )
        ]
        connector.ib.positions.return_value = ib_positions
        
        # Mock current prices
        with patch.object(connector.ib, "reqMktData") as mock_req_mkt_data:
            mock_req_mkt_data.side_effect = [
                Mock(last=155.0),  # AAPL current price
                Mock(last=260.0),  # MSFT current price
            ]
            
            result = connector.get_positions()
            
            assert len(result) == 2
            
            # Check AAPL position (long)
            aapl_pos = next(p for p in result if p.symbol == "AAPL")
            assert aapl_pos.quantity == 100.0
            assert aapl_pos.is_long
            
            # Check MSFT position (short)
            msft_pos = next(p for p in result if p.symbol == "MSFT")
            assert msft_pos.quantity == -50.0
            assert msft_pos.is_short

    def test_get_positions_empty(self, connector):
        """Test empty position list."""
        connector.ib.positions.return_value = []
        
        result = connector.get_positions()
        
        assert result == []

    # Order History Tests
    def test_get_order_history(self, connector):
        """Test retrieving all orders."""
        connector.ib.trades.return_value = []
        connector.ib.fills.return_value = []
        
        with patch.object(connector, "_convert_ib_order_to_result", return_value=OrderResult(
            order_id="123456",
            client_order_id=None,
            symbol="AAPL",
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=100.0,
            filled_quantity=100.0,
            price=None,
            stop_price=None,
            avg_fill_price=150.25,
            status=OrderStatus.FILLED,
            timestamp=datetime.now(timezone.utc)
        )):
            result = connector.get_order_history()
            
            assert isinstance(result, list)

    def test_get_order_history_filtered_by_symbol(self, connector):
        """Test filtering order history by symbol."""
        connector.ib.trades.return_value = []
        connector.ib.fills.return_value = []
        
        with patch.object(connector, "_convert_ib_order_to_result", return_value=OrderResult(
            order_id="123456",
            client_order_id=None,
            symbol="AAPL",
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=100.0,
            filled_quantity=100.0,
            price=None,
            stop_price=None,
            avg_fill_price=150.25,
            status=OrderStatus.FILLED,
            timestamp=datetime.now(timezone.utc)
        )):
            result = connector.get_order_history(symbol="AAPL")
            
            assert isinstance(result, list)

    def test_get_order_history_filtered_by_status(self, connector):
        """Test filtering order history by status."""
        connector.ib.trades.return_value = []
        connector.ib.fills.return_value = []
        
        with patch.object(connector, "_convert_ib_order_to_result", return_value=OrderResult(
            order_id="123456",
            client_order_id=None,
            symbol="AAPL",
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=100.0,
            filled_quantity=100.0,
            price=None,
            stop_price=None,
            avg_fill_price=150.25,
            status=OrderStatus.FILLED,
            timestamp=datetime.now(timezone.utc)
        )):
            result = connector.get_order_history(status=OrderStatus.FILLED)
            
            assert isinstance(result, list)

    def test_get_order_history_filtered_by_date(self, connector):
        """Test filtering order history by date range."""
        connector.ib.trades.return_value = []
        connector.ib.fills.return_value = []
        
        start_date = datetime.now(timezone.utc) - timedelta(days=30)
        end_date = datetime.now(timezone.utc)
        
        with patch.object(connector, "_convert_ib_order_to_result", return_value=OrderResult(
            order_id="123456",
            client_order_id=None,
            symbol="AAPL",
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=100.0,
            filled_quantity=100.0,
            price=None,
            stop_price=None,
            avg_fill_price=150.25,
            status=OrderStatus.FILLED,
            timestamp=datetime.now(timezone.utc)
        )):
            result = connector.get_order_history(start_date=start_date, end_date=end_date)
            
            assert isinstance(result, list)

    def test_get_order_history_with_limit(self, connector):
        """Test limiting order history results."""
        connector.ib.trades.return_value = []
        connector.ib.fills.return_value = []
        
        with patch.object(connector, "_convert_ib_order_to_result", return_value=OrderResult(
            order_id="123456",
            client_order_id=None,
            symbol="AAPL",
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=100.0,
            filled_quantity=100.0,
            price=None,
            stop_price=None,
            avg_fill_price=150.25,
            status=OrderStatus.FILLED,
            timestamp=datetime.now(timezone.utc)
        )):
            result = connector.get_order_history(limit=10)
            
            assert isinstance(result, list)

    # Market Status Tests
    def test_is_market_open_stock(self, connector, mock_contract):
        """Test market hours for stocks."""
        with patch.object(connector, "_create_contract", return_value=mock_contract):
            with patch.object(connector, "_qualify_contract", return_value=mock_contract):
                # Mock contract details with trading hours
                contract_details = Mock()
                contract_details.tradingHours = "20231201:0930-1600;20231204-20231208:0930-1600"
                connector.ib.reqContractDetails.return_value = [contract_details]
                
                result = connector.is_market_open("AAPL")
                
                assert isinstance(result, bool)

    def test_is_market_open_forex(self, connector):
        """Test forex market (always open)."""
        result = connector.is_market_open("EURUSD")
        
        assert result is True  # Forex is 24/5

    def test_is_market_open_futures(self, connector, mock_contract):
        """Test futures market hours."""
        with patch.object(connector, "_create_contract", return_value=mock_contract):
            with patch.object(connector, "_qualify_contract", return_value=mock_contract):
                # Mock contract details
                contract_details = Mock()
                contract_details.tradingHours = "20231201:CLOSED;20231203-20231208:0000-2359"
                connector.ib.reqContractDetails.return_value = [contract_details]
                
                result = connector.is_market_open("ES")
                
                assert isinstance(result, bool)

    # Order Status Conversion Tests
    def test_convert_order_status_submitted(self, connector):
        """Test mapping 'Submitted' to PENDING."""
        status = connector._convert_order_status("Submitted")
        assert status == OrderStatus.PENDING

    def test_convert_order_status_filled(self, connector):
        """Test mapping 'Filled' to FILLED."""
        status = connector._convert_order_status("Filled")
        assert status == OrderStatus.FILLED

    def test_convert_order_status_cancelled(self, connector):
        """Test mapping 'Cancelled' to CANCELLED."""
        status = connector._convert_order_status("Cancelled")
        assert status == OrderStatus.CANCELLED

    def test_convert_order_status_inactive(self, connector):
        """Test mapping 'Inactive' to REJECTED."""
        status = connector._convert_order_status("Inactive")
        assert status == OrderStatus.REJECTED

    def test_convert_order_status_partial_fill(self, connector):
        """Test mapping 'PartiallyFilled' to PARTIALLY_FILLED."""
        status = connector._convert_order_status("PartiallyFilled")
        assert status == OrderStatus.PARTIALLY_FILLED

    # Async Wrapper Tests
    def test_run_async_success(self, connector):
        """Test successful async operation execution."""
        async def test_coro():
            return "success"
        
        result = connector._run_async(test_coro())
        assert result == "success"

    def test_run_async_timeout(self, connector):
        """Test timeout handling in async wrapper."""
        async def test_coro():
            await asyncio.sleep(5)
            return "success"
        
        with pytest.raises(ExecutionError):
            connector._run_async(test_coro(), timeout=0.1)

    def test_run_async_exception(self, connector):
        """Test exception propagation from async code."""
        async def test_coro():
            raise ValueError("Test error")
        
        with pytest.raises(ExecutionError):
            connector._run_async(test_coro())

    # Validation Tests
    def test_validate_order_invalid_symbol(self, connector):
        """Test validation error for invalid symbol."""
        order = OrderRequest(
            symbol="",  # Empty symbol
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=100.0
        )
        
        with pytest.raises(ValidationError):
            connector.place_order(order)

    def test_validate_order_negative_quantity(self, connector):
        """Test validation error for negative quantity."""
        # OrderRequest already validates quantity in __post_init__
        with pytest.raises(ValidationError):
            order = OrderRequest(
                symbol="AAPL",
                side=OrderSide.BUY,
                order_type=OrderType.MARKET,
                quantity=-100.0  # Negative quantity
            )

    def test_validate_order_missing_price(self, connector):
        """Test validation error for limit order without price."""
        # OrderRequest already validates price in __post_init__
        with pytest.raises(ValidationError):
            order = OrderRequest(
                symbol="AAPL",
                side=OrderSide.BUY,
                order_type=OrderType.LIMIT,
                quantity=100.0
                # Missing price
            )

    # Integration-like Tests (with full mocking)
    def test_full_order_lifecycle(self, connector, mock_trade, mock_contract):
        """Test complete order lifecycle: place → get → cancel."""
        order = OrderRequest(
            symbol="AAPL",
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=100.0
        )
        
        with patch.object(connector, "_create_contract", return_value=mock_contract):
            with patch.object(connector, "_qualify_contract", return_value=mock_contract):
                with patch.object(connector, "_convert_order_to_ib"):
                    connector.ib.placeOrder.return_value = mock_trade
                    
                    # Place order
                    with patch.object(connector, "_convert_ib_order_to_result", return_value=OrderResult(
                        order_id="123456",
                        client_order_id=None,
                        symbol="AAPL",
                        side=OrderSide.BUY,
                        order_type=OrderType.MARKET,
                        quantity=100.0,
                        filled_quantity=0.0,
                        price=None,
                        stop_price=None,
                        avg_fill_price=None,
                        status=OrderStatus.PENDING,
                        timestamp=datetime.now(timezone.utc)
                    )):
                        place_result = connector.place_order(order)
                        assert place_result.order_id == "123456"
                        assert place_result.status == OrderStatus.PENDING
                    
                    # Get order
                    connector._order_map["123456"] = mock_trade
                    with patch.object(connector, "_convert_ib_order_to_result", return_value=OrderResult(
                        order_id="123456",
                        client_order_id=None,
                        symbol="AAPL",
                        side=OrderSide.BUY,
                        order_type=OrderType.MARKET,
                        quantity=100.0,
                        filled_quantity=0.0,
                        price=None,
                        stop_price=None,
                        avg_fill_price=None,
                        status=OrderStatus.PENDING,
                        timestamp=datetime.now(timezone.utc)
                    )):
                        get_result = connector.get_order("123456")
                        assert get_result.order_id == "123456"
                    
                    # Cancel order
                    with patch.object(connector, "_convert_ib_order_to_result", return_value=OrderResult(
                        order_id="123456",
                        client_order_id=None,
                        symbol="AAPL",
                        side=OrderSide.BUY,
                        order_type=OrderType.MARKET,
                        quantity=100.0,
                        filled_quantity=0.0,
                        price=None,
                        stop_price=None,
                        avg_fill_price=None,
                        status=OrderStatus.CANCELLED,
                        timestamp=datetime.now(timezone.utc),
                        updated_at=datetime.now(timezone.utc)
                    )):
                        cancel_result = connector.cancel_order("123456")
                        assert cancel_result.status == OrderStatus.CANCELLED

    def test_multiple_orders(self, connector, mock_trade, mock_contract):
        """Test placing multiple orders."""
        orders = [
            OrderRequest(
                symbol="AAPL",
                side=OrderSide.BUY,
                order_type=OrderType.MARKET,
                quantity=100.0
            ),
            OrderRequest(
                symbol="MSFT",
                side=OrderSide.BUY,
                order_type=OrderType.MARKET,
                quantity=50.0
            )
        ]
        
        for order in orders:
            with patch.object(connector, "_create_contract", return_value=mock_contract):
                with patch.object(connector, "_qualify_contract", return_value=mock_contract):
                    with patch.object(connector, "_convert_order_to_ib"):
                        connector.ib.placeOrder.return_value = mock_trade
                        with patch.object(connector, "_convert_ib_order_to_result", return_value=OrderResult(
                            order_id="123456",
                            client_order_id=None,
                            symbol=order.symbol,
                            side=OrderSide.BUY,
                            order_type=OrderType.MARKET,
                            quantity=order.quantity,
                            filled_quantity=0.0,
                            price=None,
                            stop_price=None,
                            avg_fill_price=None,
                            status=OrderStatus.PENDING,
                            timestamp=datetime.now(timezone.utc)
                        )):
                            result = connector.place_order(order)
                            assert result.symbol == order.symbol

    def test_position_after_trade(self, connector, mock_trade, mock_contract):
        """Test creating a position after a trade."""
        order = OrderRequest(
            symbol="AAPL",
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=100.0
        )
        
        # Simulate filled order
        mock_trade.orderStatus.status = "Filled"
        mock_trade.orderStatus.filled = 100.0
        mock_trade.orderStatus.avgFillPrice = 150.25
        
        with patch.object(connector, "_create_contract", return_value=mock_contract):
            with patch.object(connector, "_qualify_contract", return_value=mock_contract):
                with patch.object(connector, "_convert_order_to_ib"):
                    connector.ib.placeOrder.return_value = mock_trade
                    
                    # Place order
                    with patch.object(connector, "_convert_ib_order_to_result", return_value=OrderResult(
                        order_id="123456",
                        client_order_id=None,
                        symbol="AAPL",
                        side=OrderSide.BUY,
                        order_type=OrderType.MARKET,
                        quantity=100.0,
                        filled_quantity=100.0,
                        price=None,
                        stop_price=None,
                        avg_fill_price=150.25,
                        status=OrderStatus.FILLED,
                        timestamp=datetime.now(timezone.utc)
                    )):
                        result = connector.place_order(order)
                        assert result.filled_quantity == 100.0
                    
                    # Check position was created
                    ib_positions = [
                        Mock(
                            contract=Mock(symbol="AAPL", secType="STK"),
                            position=100.0,
                            avgCost=150.25
                        )
                    ]
                    connector.ib.positions.return_value = ib_positions
                    
                    # Mock current price
                    with patch.object(connector.ib, "reqMktData", return_value=Mock(last=155.0)):
                        positions = connector.get_positions()
                    assert len(positions) == 1
                    assert positions[0].symbol == "AAPL"
                    assert positions[0].quantity == 100.0

    def test_close_position(self, connector, mock_trade, mock_contract):
        """Test closing a position with a sell order."""
        # Create a buy order first
        buy_order = OrderRequest(
            symbol="AAPL",
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=100.0
        )
        
        # Simulate filled buy order
        mock_trade.orderStatus.status = "Filled"
        mock_trade.orderStatus.filled = 100.0
        mock_trade.orderStatus.avgFillPrice = 150.25
        mock_trade.order.action = "BUY"
        
        with patch.object(connector, "_create_contract", return_value=mock_contract):
            with patch.object(connector, "_qualify_contract", return_value=mock_contract):
                with patch.object(connector, "_convert_order_to_ib"):
                    connector.ib.placeOrder.return_value = mock_trade
                    
                    # Place buy order
                    with patch.object(connector, "_convert_ib_order_to_result", return_value=OrderResult(
                        order_id="123456",
                        client_order_id=None,
                        symbol="AAPL",
                        side=OrderSide.BUY,
                        order_type=OrderType.MARKET,
                        quantity=100.0,
                        filled_quantity=100.0,
                        price=None,
                        stop_price=None,
                        avg_fill_price=150.25,
                        status=OrderStatus.FILLED,
                        timestamp=datetime.now(timezone.utc)
                    )):
                        buy_result = connector.place_order(buy_order)
                        assert buy_result.filled_quantity == 100.0
                    
                    # Create a sell order to close the position
                    sell_order = OrderRequest(
                        symbol="AAPL",
                        side=OrderSide.SELL,
                        order_type=OrderType.MARKET,
                        quantity=100.0
                    )
                    
                    # Simulate filled sell order
                    mock_trade.order.action = "SELL"
                    mock_trade.orderStatus.avgFillPrice = 155.0
                    
                    with patch.object(connector, "_convert_ib_order_to_result", return_value=OrderResult(
                        order_id="123457",
                        client_order_id=None,
                        symbol="AAPL",
                        side=OrderSide.SELL,
                        order_type=OrderType.MARKET,
                        quantity=100.0,
                        filled_quantity=100.0,
                        price=None,
                        stop_price=None,
                        avg_fill_price=155.0,
                        status=OrderStatus.FILLED,
                        timestamp=datetime.now(timezone.utc)
                    )):
                        sell_result = connector.place_order(sell_order)
                        assert sell_result.filled_quantity == 100.0
                        assert sell_result.side == OrderSide.SELL
