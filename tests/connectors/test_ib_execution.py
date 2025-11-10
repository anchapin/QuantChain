"""Tests for Interactive Brokers execution connector."""

import threading
import time
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, Mock, patch

import pytest

from quantchain.connectors.ib_execution import IBExecutionConnector
from quantchain.tools.trading_execution import (
    AccountInfo,
    ExecutionError,
    InsufficientFundsError,
    OrderNotFoundError,
    OrderRequest,
    OrderResult,
    OrderSide,
    OrderStatus,
    OrderType,
    Position,
    TimeInForce,
    ValidationError,
)


@pytest.mark.unit
class TestIBExecutionConnector:
    """Test cases for IBExecutionConnector."""

    @pytest.fixture
    def mock_ib_wrapper(self):
        """Create a mock IB wrapper."""
        wrapper = MagicMock()
        wrapper._connected = True
        wrapper._next_order_id = 1001
        wrapper._order_statuses = {}
        wrapper._account_summary = {}
        wrapper._positions = []
        wrapper._executions = []
        wrapper._contracts = {}
        wrapper._error_codes = {}
        wrapper._events = {}
        return wrapper

    @pytest.fixture
    def mock_ib_client(self, mock_ib_wrapper):
        """Create a mock IB client."""
        client = MagicMock()
        client.get_next_req_id.return_value = 1
        return client

    @patch('quantchain.connectors.ib_execution.threading.Thread')
    @patch('quantchain.connectors.ib_execution.IBWrapper')
    @patch('quantchain.connectors.ib_execution.IBClient')
    def test_init_success(self, mock_client_class, mock_wrapper_class, mock_thread):
        """Test successful initialization of IB connector."""
        # Setup mocks
        mock_wrapper = MagicMock()
        mock_wrapper._connected = True
        mock_wrapper._next_order_id = 1001
        mock_wrapper._events = {}
        mock_wrapper_class.return_value = mock_wrapper
        
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        mock_thread_instance = MagicMock()
        mock_thread.return_value = mock_thread_instance
        
        # Mock the _connect method to avoid actual connection
        with patch.object(IBExecutionConnector, '_connect'):
            # Create connector
            connector = IBExecutionConnector(
                host="127.0.0.1",
                port=7497,
                client_id=1,
                timeout=5
            )
            
            # Verify initialization
            assert connector.host == "127.0.0.1"
            assert connector.port == 7497
            assert connector.client_id == 1
            assert connector.timeout == 5
            
            # The connect shouldn't be called since we mocked it
            assert not mock_client.connect.called

    def test_create_stock_contract(self, mock_ib_wrapper, mock_ib_client):
        """Test creating a stock contract."""
        with patch('quantchain.connectors.ib_execution.IBWrapper', return_value=mock_ib_wrapper), \
             patch('quantchain.connectors.ib_execution.IBClient', return_value=mock_ib_client), \
             patch.object(IBExecutionConnector, '_connect'):
            connector = IBExecutionConnector(host="127.0.0.1", port=7497, client_id=1)
            contract = connector._create_contract("AAPL")
            
            assert contract.symbol == "AAPL"
            assert contract.secType == "STK"
            assert contract.currency == "USD"
            assert contract.exchange == "SMART"

    def test_create_forex_contract(self, mock_ib_wrapper, mock_ib_client):
        """Test creating a forex contract."""
        with patch('quantchain.connectors.ib_execution.IBWrapper', return_value=mock_ib_wrapper), \
             patch('quantchain.connectors.ib_execution.IBClient', return_value=mock_ib_client), \
             patch.object(IBExecutionConnector, '_connect'):
            connector = IBExecutionConnector(host="127.0.0.1", port=7497, client_id=1)
            contract = connector._create_contract("EURUSD")
            
            assert contract.symbol == "EUR"
            assert contract.secType == "CASH"
            assert contract.currency == "USD"
            assert contract.exchange == "IDEALPRO"

    def test_create_option_contract(self, mock_ib_wrapper, mock_ib_client):
        """Test creating an option contract."""
        with patch('quantchain.connectors.ib_execution.IBWrapper', return_value=mock_ib_wrapper), \
             patch('quantchain.connectors.ib_execution.IBClient', return_value=mock_ib_client), \
             patch.object(IBExecutionConnector, '_connect'):
            connector = IBExecutionConnector(host="127.0.0.1", port=7497, client_id=1)
            contract = connector._create_contract("AAPL 20231215 150 C")
            
            assert contract.symbol == "AAPL"
            assert contract.secType == "OPT"
            assert contract.currency == "USD"
            assert contract.exchange == "SMART"
            assert contract.lastTradeDateOrContractMonth == "20231215"
            assert contract.strike == 150
            assert contract.right == "CALL"
            assert contract.multiplier == "100"

    def test_convert_market_order(self, mock_ib_wrapper, mock_ib_client):
        """Test converting a market order to IB format."""
        with patch('quantchain.connectors.ib_execution.IBWrapper', return_value=mock_ib_wrapper), \
             patch('quantchain.connectors.ib_execution.IBClient', return_value=mock_ib_client), \
             patch.object(IBExecutionConnector, '_connect'):
            connector = IBExecutionConnector(host="127.0.0.1", port=7497, client_id=1)
            
            order_request = OrderRequest(
                symbol="AAPL",
                side=OrderSide.BUY,
                order_type=OrderType.MARKET,
                quantity=100,
                time_in_force=TimeInForce.DAY
            )
            
            ib_order = connector._convert_order_to_ib(order_request)
            
            assert ib_order.orderType == "MKT"
            assert ib_order.action == "BUY"
            assert ib_order.totalQuantity == 100
            assert ib_order.tif == "DAY"

    def test_convert_limit_order(self, mock_ib_wrapper, mock_ib_client):
        """Test converting a limit order to IB format."""
        with patch('quantchain.connectors.ib_execution.IBWrapper', return_value=mock_ib_wrapper), \
             patch('quantchain.connectors.ib_execution.IBClient', return_value=mock_ib_client), \
             patch.object(IBExecutionConnector, '_connect'):
            connector = IBExecutionConnector(host="127.0.0.1", port=7497, client_id=1)
            
            order_request = OrderRequest(
                symbol="AAPL",
                side=OrderSide.BUY,
                order_type=OrderType.LIMIT,
                quantity=100,
                price=150.25,
                time_in_force=TimeInForce.GTC
            )
            
            ib_order = connector._convert_order_to_ib(order_request)
            
            assert ib_order.orderType == "LMT"
            assert ib_order.action == "BUY"
            assert ib_order.totalQuantity == 100
            assert ib_order.lmtPrice == 150.25
            assert ib_order.tif == "GTC"

    def test_convert_stop_order(self, mock_ib_wrapper, mock_ib_client):
        """Test converting a stop order to IB format."""
        with patch('quantchain.connectors.ib_execution.IBWrapper', return_value=mock_ib_wrapper), \
             patch('quantchain.connectors.ib_execution.IBClient', return_value=mock_ib_client), \
             patch.object(IBExecutionConnector, '_connect'):
            connector = IBExecutionConnector(host="127.0.0.1", port=7497, client_id=1)
            
            order_request = OrderRequest(
                symbol="AAPL",
                side=OrderSide.SELL,
                order_type=OrderType.STOP,
                quantity=100,
                stop_price=149.75,
                time_in_force=TimeInForce.DAY
            )
            
            ib_order = connector._convert_order_to_ib(order_request)
            
            assert ib_order.orderType == "STP"
            assert ib_order.action == "SELL"
            assert ib_order.totalQuantity == 100
            assert ib_order.auxPrice == 149.75
            assert ib_order.tif == "DAY"

    def test_convert_stop_limit_order(self, mock_ib_wrapper, mock_ib_client):
        """Test converting a stop limit order to IB format."""
        with patch('quantchain.connectors.ib_execution.IBWrapper', return_value=mock_ib_wrapper), \
             patch('quantchain.connectors.ib_execution.IBClient', return_value=mock_ib_client), \
             patch.object(IBExecutionConnector, '_connect'):
            connector = IBExecutionConnector(host="127.0.0.1", port=7497, client_id=1)
            
            order_request = OrderRequest(
                symbol="AAPL",
                side=OrderSide.SELL,
                order_type=OrderType.STOP_LIMIT,
                quantity=100,
                price=149.50,
                stop_price=149.75,
                time_in_force=TimeInForce.DAY
            )
            
            ib_order = connector._convert_order_to_ib(order_request)
            
            assert ib_order.orderType == "STP LMT"
            assert ib_order.action == "SELL"
            assert ib_order.totalQuantity == 100
            assert ib_order.lmtPrice == 149.50
            assert ib_order.auxPrice == 149.75
            assert ib_order.tif == "DAY"

    def test_place_order(self, mock_ib_wrapper, mock_ib_client):
        """Test placing an order."""
        with patch('quantchain.connectors.ib_execution.IBWrapper', return_value=mock_ib_wrapper), \
             patch('quantchain.connectors.ib_execution.IBClient', return_value=mock_ib_client), \
             patch.object(IBExecutionConnector, '_connect'):
            connector = IBExecutionConnector(host="127.0.0.1", port=7497, client_id=1)
            
            # Mock contract qualification
            with patch.object(connector, '_qualify_contract', return_value=True):
                order_request = OrderRequest(
                    symbol="AAPL",
                    side=OrderSide.BUY,
                    order_type=OrderType.MARKET,
                    quantity=100,
                    time_in_force=TimeInForce.DAY
                )
                
                result = connector.place_order(order_request)
                
                assert result.symbol == "AAPL"
                assert result.side == OrderSide.BUY
                assert result.order_type == OrderType.MARKET
                assert result.quantity == 100
                assert result.status == OrderStatus.PENDING
                assert result.filled_quantity == 0

    def test_get_order(self, mock_ib_wrapper, mock_ib_client):
        """Test getting order status."""
        # Setup mock order status
        mock_ib_wrapper._order_statuses[1001] = {
            'status': 'Filled',
            'filled': 100,
            'remaining': 0,
            'avgFillPrice': 150.25,
            'lastFillPrice': 150.25,
        }
        
        with patch('quantchain.connectors.ib_execution.IBWrapper', return_value=mock_ib_wrapper), \
             patch('quantchain.connectors.ib_execution.IBClient', return_value=mock_ib_client), \
             patch.object(IBExecutionConnector, '_connect'):
            connector = IBExecutionConnector(host="127.0.0.1", port=7497, client_id=1)
            
            result = connector.get_order("1001")
            
            assert result.order_id == "1001"
            assert result.filled_quantity == 100
            assert result.avg_fill_price == 150.25
            assert result.status == OrderStatus.FILLED

    def test_get_order_not_found(self, mock_ib_wrapper, mock_ib_client):
        """Test getting a non-existent order."""
        with patch('quantchain.connectors.ib_execution.IBWrapper', return_value=mock_ib_wrapper), \
             patch('quantchain.connectors.ib_execution.IBClient', return_value=mock_ib_client), \
             patch.object(IBExecutionConnector, '_connect'):
            connector = IBExecutionConnector(host="127.0.0.1", port=7497, client_id=1)
            
            with pytest.raises(ExecutionError, match="Failed to get order: Order not found: 1001"):
                connector.get_order("1001")

    def test_cancel_order(self, mock_ib_wrapper, mock_ib_client):
        """Test canceling an order."""
        with patch('quantchain.connectors.ib_execution.IBWrapper', return_value=mock_ib_wrapper), \
             patch('quantchain.connectors.ib_execution.IBClient', return_value=mock_ib_client), \
             patch.object(IBExecutionConnector, '_connect'):
            connector = IBExecutionConnector(host="127.0.0.1", port=7497, client_id=1)
            
            # Mock get_order to avoid recursion
            with patch.object(connector, 'get_order') as mock_get_order:
                mock_get_order.return_value = OrderResult(
                    order_id="1001",
                    client_order_id=None,
                    symbol="AAPL",
                    side=OrderSide.BUY,
                    order_type=OrderType.MARKET,
                    quantity=100,
                    filled_quantity=0,
                    price=None,
                    stop_price=None,
                    avg_fill_price=None,
                    status=OrderStatus.CANCELLED,
                    timestamp=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc)
                )
                
                result = connector.cancel_order("1001")
                
                assert result.order_id == "1001"
                assert result.status == OrderStatus.CANCELLED
                mock_ib_client.cancelOrder.assert_called_once_with(1001)

    def test_get_account(self, mock_ib_wrapper, mock_ib_client):
        """Test getting account information."""
        # Setup mock account summary
        mock_ib_wrapper._account_summary = {
            'NetLiquidation': 100000.0,
            'AvailableFunds': 50000.0,
            'BuyingPower': 200000.0,
            'TotalCashValue': 50000.0,
        }
        
        # Setup mock positions
        mock_ib_wrapper._positions = [
            {
                'symbol': 'AAPL',
                'position': 100,
                'avgCost': 150.25,
            },
            {
                'symbol': 'GOOGL',
                'position': 50,
                'avgCost': 2500.50,
            },
        ]
        
        with patch('quantchain.connectors.ib_execution.IBWrapper', return_value=mock_ib_wrapper), \
             patch('quantchain.connectors.ib_execution.IBClient', return_value=mock_ib_client), \
             patch.object(IBExecutionConnector, '_connect'):
            connector = IBExecutionConnector(host="127.0.0.1", port=7497, client_id=1)
            
            with patch.object(connector, '_wait_for_response', return_value=True):
                account = connector.get_account()
                
                assert account.account_id == "1"
                assert account.buying_power == 200000.0
                assert account.cash == 50000.0
                assert account.portfolio_value == 100000.0
                assert account.margin_available == 50000.0
                assert len(account.positions) == 2
                
                assert account.positions[0].symbol == "AAPL"
                assert account.positions[0].quantity == 100
                assert account.positions[0].avg_entry_price == 150.25
                
                assert account.positions[1].symbol == "GOOGL"
                assert account.positions[1].quantity == 50
                assert account.positions[1].avg_entry_price == 2500.50

    def test_get_positions(self, mock_ib_wrapper, mock_ib_client):
        """Test getting current positions."""
        # Setup mock positions
        mock_ib_wrapper._positions = [
            {
                'symbol': 'AAPL',
                'position': 100,
                'avgCost': 150.25,
            },
            {
                'symbol': 'GOOGL',
                'position': 50,
                'avgCost': 2500.50,
            },
        ]
        
        with patch('quantchain.connectors.ib_execution.IBWrapper', return_value=mock_ib_wrapper), \
             patch('quantchain.connectors.ib_execution.IBClient', return_value=mock_ib_client), \
             patch.object(IBExecutionConnector, '_connect'):
            connector = IBExecutionConnector(host="127.0.0.1", port=7497, client_id=1)
            
            positions = connector.get_positions()
            
            assert len(positions) == 2
            
            assert positions[0].symbol == "AAPL"
            assert positions[0].quantity == 100
            assert positions[0].avg_entry_price == 150.25
            assert positions[0].current_price == 150.25
            assert positions[0].market_value == 100 * 150.25
            
            assert positions[1].symbol == "GOOGL"
            assert positions[1].quantity == 50
            assert positions[1].avg_entry_price == 2500.50
            assert positions[1].current_price == 2500.50
            assert positions[1].market_value == 50 * 2500.50

    def test_get_order_history(self, mock_ib_wrapper, mock_ib_client):
        """Test getting order history."""
        # Setup mock executions
        now = datetime.now(timezone.utc)
        mock_ib_wrapper._executions = [
            {
                'orderId': 1001,
                'clientId': 1,
                'symbol': 'AAPL',
                'side': 'BOT',
                'shares': 100,
                'price': 150.25,
                'time': now - timedelta(days=1),
            },
            {
                'orderId': 1002,
                'clientId': 2,
                'symbol': 'GOOGL',
                'side': 'BOT',
                'shares': 50,
                'price': 2500.50,
                'time': now - timedelta(days=2),
            },
        ]
        
        with patch('quantchain.connectors.ib_execution.IBWrapper', return_value=mock_ib_wrapper), \
             patch('quantchain.connectors.ib_execution.IBClient', return_value=mock_ib_client), \
             patch.object(IBExecutionConnector, '_connect'):
            connector = IBExecutionConnector(host="127.0.0.1", port=7497, client_id=1)
            
            with patch.object(connector, '_wait_for_response', return_value=True):
                history = connector.get_order_history()
                
                assert len(history) == 2
                
                # Should be sorted by timestamp descending
                assert history[0].order_id == "1001"
                assert history[0].symbol == "AAPL"
                assert history[0].side == OrderSide.BUY
                assert history[0].quantity == 100
                assert history[0].avg_fill_price == 150.25
                assert history[0].status == OrderStatus.FILLED
                
                assert history[1].order_id == "1002"
                assert history[1].symbol == "GOOGL"
                assert history[1].side == OrderSide.BUY
                assert history[1].quantity == 50
                assert history[1].avg_fill_price == 2500.50
                assert history[1].status == OrderStatus.FILLED

    def test_validate_order(self, mock_ib_wrapper, mock_ib_client):
        """Test order validation."""
        with patch('quantchain.connectors.ib_execution.IBWrapper', return_value=mock_ib_wrapper), \
             patch('quantchain.connectors.ib_execution.IBClient', return_value=mock_ib_client), \
             patch.object(IBExecutionConnector, '_connect'):
            connector = IBExecutionConnector(host="127.0.0.1", port=7497, client_id=1)
            
            # Valid order should pass
            order = OrderRequest(
                symbol="AAPL",
                side=OrderSide.BUY,
                order_type=OrderType.MARKET,
                quantity=100,
                time_in_force=TimeInForce.DAY
            )
            
            # Should not raise an exception
            connector.validate_order(order)
            
            # Empty symbol should raise ValidationError
            order.symbol = ""
            
            with pytest.raises(ValidationError, match="Symbol is required"):
                connector.validate_order(order)

    def test_get_symbol_info(self, mock_ib_wrapper, mock_ib_client):
        """Test getting symbol information."""
        # Setup mock contract details
        mock_details = MagicMock()
        mock_details.longName = "Apple Inc."
        mock_details.underSecType = "STK"
        mock_details.exchange = "NASDAQ"
        mock_details.currency = "USD"
        mock_details.minTick = 0.01
        mock_details.multiplier = "1"
        
        mock_ib_wrapper._contracts[1] = mock_details
        
        with patch('quantchain.connectors.ib_execution.IBWrapper', return_value=mock_ib_wrapper), \
             patch('quantchain.connectors.ib_execution.IBClient', return_value=mock_ib_client), \
             patch.object(IBExecutionConnector, '_connect'):
            connector = IBExecutionConnector(host="127.0.0.1", port=7497, client_id=1)
            
            with patch.object(connector, '_wait_for_response', return_value=True):
                info = connector.get_symbol_info("AAPL")
                
                assert info['symbol'] == "AAPL"
                assert info['name'] == "Apple Inc."
                assert info['security_type'] == "STK"
                assert info['exchange'] == "NASDAQ"
                assert info['currency'] == "USD"
                assert info['min_tick'] == 0.01
                assert info['price_precision'] == 2
                assert info['multiplier'] == "1"

    def test_is_market_open(self, mock_ib_wrapper, mock_ib_client):
        """Test checking if market is open."""
        with patch('quantchain.connectors.ib_execution.IBWrapper', return_value=mock_ib_wrapper), \
             patch('quantchain.connectors.ib_execution.IBClient', return_value=mock_ib_client), \
             patch.object(IBExecutionConnector, '_connect'):
            connector = IBExecutionConnector(host="127.0.0.1", port=7497, client_id=1)
            
            # For simplicity, the implementation always returns True
            assert connector.is_market_open() is True
            assert connector.is_market_open("AAPL") is True

    def test_disconnect(self, mock_ib_wrapper, mock_ib_client):
        """Test disconnecting from IB."""
        with patch('quantchain.connectors.ib_execution.IBWrapper', return_value=mock_ib_wrapper), \
             patch('quantchain.connectors.ib_execution.IBClient', return_value=mock_ib_client), \
             patch.object(IBExecutionConnector, '_connect'):
            connector = IBExecutionConnector(host="127.0.0.1", port=7497, client_id=1)
            
            connector.disconnect()
            
            mock_ib_client.disconnect.assert_called_once()
