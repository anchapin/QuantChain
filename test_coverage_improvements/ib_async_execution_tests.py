"""
Comprehensive tests for ib_async_execution.py to improve coverage from 52.3% to 90%+
"""
import pytest
from unittest.mock import Mock, patch, MagicMock, AsyncMock
import asyncio
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import ib_async
from ib_async import (
    Contract, Stock, Option, Future, Forex, Order, LimitOrder,
    MarketOrder, StopOrder, RequestError
)

# Mock missing classes that aren't directly available in ib_async
class Commodity:
    """Mock Commodity class"""
    pass

class Bond:
    """Mock Bond class"""
    pass

class CFD:
    """Mock CFD class"""
    pass

class MutualFund:
    """Mock MutualFund class"""
    pass

class Warrant:
    """Mock Warrant class"""
    pass

class TrailOrder:
    """Mock TrailOrder class"""
    pass

class Execution:
    """Mock Execution class"""
    pass

class Fill:
    """Mock Fill class"""
    pass

class CommissionReport:
    """Mock CommissionReport class"""
    pass

from quantchain.connectors.ib_async_execution import (
    IBExecutionConnector,
    ExecutionError,
    InsufficientFundsError,
    OrderNotFoundError,
    ValidationError,
)

class TestIBExecutionConnector:
    """Test cases for IBExecutionConnector class"""

    @pytest.fixture
    def mock_ib(self):
        """Mock IB client"""
        mock = Mock(spec=ib_async.IB)
        mock.isConnected = Mock(return_value=True)
        mock.reqContractDetails = Mock(return_value=[])
        mock.reqMktData = Mock()
        mock.cancelMktData = Mock()
        mock.reqHistoricalData = Mock(return_value=[])
        mock.reqRealTimeBars = Mock()
        mock.cancelRealTimeBars = Mock()
        mock.reqMarketDepth = Mock()
        mock.cancelMarketDepth = Mock()
        mock.reqScannerSubscription = Mock()
        mock.cancelScannerSubscription = Mock()
        mock.reqScannerParameters = Mock(return_value="")
        mock.reqMktDepthExchanges = Mock(return_value=[])
        mock.placeOrder = Mock()
        mock.cancelOrder = Mock()
        mock.reqGlobalCancel = Mock()
        mock.reqOpenOrders = Mock(return_value=[])
        mock.reqAllOpenOrders = Mock(return_value=[])
        mock.reqExecutions = Mock(return_value=[])
        mock.reqCommissionReport = Mock(return_value=[])
        mock.positions = Mock(return_value=[])
        mock.accountSummary = Mock(return_value=[])
        mock.accountValues = Mock(return_value=[])
        mock.managedAccounts = Mock(return_value=[])
        mock.updateAccount = Mock()
        mock.updateAccountValue = Mock()
        mock.updatePortfolio = Mock()
        mock.disconnect = Mock()
        mock.trades = Mock(return_value=[])
        mock.connectAsync = AsyncMock()
        return mock

    @pytest.fixture
    def ib_connector(self, mock_ib):
        """Create IBExecutionConnector instance with mocked IB client"""
        # Mock connectAsync for initialization
        mock_ib.connectAsync = AsyncMock()

        with patch('quantchain.connectors.ib_async_execution.IB', return_value=mock_ib):
            connector = IBExecutionConnector(
                host="127.0.0.1",
                port=7497,
                client_id=123,
                readonly=False,
            )
            connector.ib = mock_ib  # Directly set the mocked IB instance
            connector._order_map = {}
            return connector

    @pytest.fixture
    def sample_order_request(self):
        """Sample order request for testing"""
        from quantchain.tools.trading_execution import (
            OrderRequest, OrderSide, OrderType, TimeInForce
        )
        return OrderRequest(
            symbol="AAPL",
            quantity=100,
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            time_in_force=TimeInForce.DAY,
            price=None,
        )

    @pytest.fixture
    def sample_contract(self):
        """Sample contract for testing"""
        contract = Mock(spec=Stock)
        contract.symbol = "AAPL"
        contract.exchange = "SMART"
        contract.currency = "USD"
        return contract

    def test_init(self):
        """Test IBExecutionConnector initialization"""
        with patch('quantchain.connectors.ib_async_execution.IB') as mock_ib:
            mock_ib_instance = Mock()
            mock_ib_instance.connectAsync = AsyncMock()
            mock_ib.return_value = mock_ib_instance

            connector = IBExecutionConnector()
            assert connector.host == "127.0.0.1"
            assert connector.port == 7497
            assert connector.client_id == 1
            assert connector.readonly is False
            mock_ib.assert_called_once()

    def test_disconnect(self, ib_connector, mock_ib):
        """Test disconnecting from IB"""
        ib_connector.disconnect()
        mock_ib.disconnect.assert_called_once()

    def test_place_order_market(self, ib_connector, mock_ib, sample_order_request):
        """Test placing a market order"""
        from quantchain.tools.trading_execution import OrderStatus, OrderResult

        # Mock order placement
        mock_trade = Mock()
        mock_trade.orderStatus.status = "Filled"
        mock_trade.order.permId = 12345
        mock_trade.order.orderType = "MKT"
        mock_ib.placeOrder.return_value = mock_trade

        # Add to order map
        ib_connector._order_map["12345"] = mock_trade

        result = ib_connector.place_order(sample_order_request)

        assert isinstance(result, OrderResult)
        assert result.order_id == "12345"
        assert result.status == OrderStatus.FILLED
        mock_ib.placeOrder.assert_called_once()

    def test_place_order_limit(self, ib_connector, mock_ib):
        """Test placing a limit order"""
        from quantchain.tools.trading_execution import (
            OrderRequest, OrderSide, OrderType, TimeInForce, OrderStatus, OrderResult
        )

        order_request = OrderRequest(
            symbol="AAPL",
            quantity=100,
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            time_in_force=TimeInForce.DAY,
            price=150.0,
        )

        # Mock order placement
        mock_trade = Mock()
        mock_trade.orderStatus.status = "Submitted"
        mock_trade.order.permId = 12345
        mock_trade.order.orderType = "LMT"
        mock_trade.order.lmtPrice = 150.0
        mock_ib.placeOrder.return_value = mock_trade

        # Add to order map
        ib_connector._order_map["12345"] = mock_trade

        result = ib_connector.place_order(order_request)

        assert isinstance(result, OrderResult)
        assert result.order_id == "12345"
        assert result.status == OrderStatus.PENDING
        mock_ib.placeOrder.assert_called_once()

    def test_place_order_with_error(self, ib_connector, mock_ib, sample_order_request):
        """Test placing an order with error"""
        from quantchain.tools.trading_execution import ValidationError

        # Mock contract qualification to raise an error
        with patch.object(ib_connector, '_qualify_contract', side_effect=RequestError("Invalid contract")):
            with pytest.raises(ExecutionError):
                ib_connector.place_order(sample_order_request)

    def test_cancel_order(self, ib_connector, mock_ib):
        """Test cancelling an order"""
        # Mock an existing order
        order_id = "12345"
        mock_trade = Mock()
        ib_connector._order_map[order_id] = mock_trade

        # Mock the cancel method to set order status
        mock_trade.orderStatus.status = "Cancelled"

        result = ib_connector.cancel_order(order_id)

        assert result.order_id == order_id
        mock_ib.cancelOrder.assert_called_once()
        assert order_id not in ib_connector._order_map

    def test_cancel_nonexistent_order(self, ib_connector):
        """Test cancelling a non-existent order"""
        from quantchain.tools.trading_execution import OrderNotFoundError

        with pytest.raises(OrderNotFoundError):
            ib_connector.cancel_order("99999")

    def test_get_order(self, ib_connector, mock_ib):
        """Test getting order details"""
        # Mock an existing order
        order_id = "12345"
        mock_trade = Mock()
        mock_trade.orderStatus.status = "Filled"
        mock_trade.order.permId = order_id
        ib_connector._order_map[order_id] = mock_trade

        result = ib_connector.get_order(order_id)

        assert result.order_id == order_id

    def test_get_order_nonexistent(self, ib_connector):
        """Test getting a non-existent order"""
        from quantchain.tools.trading_execution import OrderNotFoundError

        with pytest.raises(OrderNotFoundError):
            ib_connector.get_order("99999")

    def test_get_account(self, ib_connector, mock_ib):
        """Test getting account information"""
        # Mock account summary
        mock_summary = Mock()
        mock_summary.tag = "NetLiquidation"
        mock_summary.value = "100000.0"
        mock_summary.currency = "USD"

        mock_summary2 = Mock()
        mock_summary2.tag = "BuyingPower"
        mock_summary2.value = "200000.0"
        mock_summary2.currency = "USD"

        mock_ib.accountSummary.return_value = [mock_summary, mock_summary2]

        account = ib_connector.get_account()

        assert "net_liquidation" in account
        assert account["net_liquidation"] == 100000.0
        assert "buying_power" in account
        assert account["buying_power"] == 200000.0

    def test_get_positions(self, ib_connector, mock_ib):
        """Test getting positions"""
        # Mock positions
        mock_position = Mock()
        mock_position.contract = Mock()
        mock_position.contract.symbol = "AAPL"
        mock_position.position = 100
        mock_position.marketPrice = 150.0
        mock_position.unrealizedPNL = 500.0

        mock_ib.positions.return_value = [mock_position]

        positions = ib_connector.get_positions()

        assert len(positions) == 1
        assert positions[0]["symbol"] == "AAPL"
        assert positions[0]["quantity"] == 100
        assert positions[0]["current_price"] == 150.0
        assert positions[0]["unrealized_pnl"] == 500.0

    def test_get_order_history(self, ib_connector, mock_ib):
        """Test getting order history"""
        # Mock order executions
        mock_exec = Mock()
        mock_exec.time = datetime.now()
        mock_exec.permId = "12345"
        mock_exec.side = "BOT"
        mock_exec.shares = 100
        mock_exec.price = 150.0

        mock_ib.trades.return_value = [mock_exec]

        orders = ib_connector.get_order_history(limit=10)

        assert len(orders) == 1
        assert orders[0]["order_id"] == "12345"
        assert orders[0]["side"] == "BUY"
        assert orders[0]["quantity"] == 100
        assert orders[0]["price"] == 150.0

    def test_get_historical_data(self, ib_connector, mock_ib, sample_contract):
        """Test getting historical data"""
        # Mock historical data
        mock_bar = Mock()
        mock_bar.date = "20230101 09:30:00"
        mock_bar.open = 145.0
        mock_bar.high = 150.0
        mock_bar.low = 144.0
        mock_bar.close = 149.0
        mock_bar.volume = 10000

        mock_ib.reqHistoricalData.return_value = [mock_bar]

        # Mock contract qualification
        with patch.object(ib_connector, '_qualify_contract', return_value=sample_contract):
            data = ib_connector.get_historical_data(
                symbol="AAPL",
                timeframe="1d",
                start_date=datetime(2023, 1, 1),
                end_date=datetime(2023, 1, 2),
            )

        assert isinstance(data, pd.DataFrame)
        assert len(data) == 1
        assert "open" in data.columns
        assert "high" in data.columns
        assert "low" in data.columns
        assert "close" in data.columns
        assert "volume" in data.columns

    def test_is_market_open(self, ib_connector):
        """Test checking if market is open"""
        # Test forex (always open 24/5)
        assert ib_connector.is_market_open("EURUSD") is True

        # Test error handling
        with patch.object(ib_connector, '_create_contract', side_effect=Exception()):
            assert ib_connector.is_market_open("INVALID") is True

    def test_validate_order(self, ib_connector):
        """Test order validation"""
        from quantchain.tools.trading_execution import (
            OrderRequest, OrderSide, OrderType, TimeInForce
        )

        # Valid order
        valid_order = OrderRequest(
            symbol="AAPL",
            quantity=100,
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            time_in_force=TimeInForce.DAY,
        )

        # Should not raise exception
        ib_connector.validate_order(valid_order)

        # Invalid order - empty symbol
        invalid_order = OrderRequest(
            symbol="",
            quantity=100,
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            time_in_force=TimeInForce.DAY,
        )

        with pytest.raises(ValidationError):
            ib_connector.validate_order(invalid_order)

    def test_get_symbol_info(self, ib_connector, mock_ib):
        """Test getting symbol information"""
        # Mock contract details
        mock_detail = Mock()
        mock_detail.longName = "Apple Inc."
        mock_detail.secType = "STK"
        mock_detail.exchange = "SMART"
        mock_detail.currency = "USD"
        mock_detail.minTick = 0.01
        mock_detail.multiplier = None

        mock_ib.reqContractDetails.return_value = [mock_detail]

        # Mock contract qualification
        with patch.object(ib_connector, '_qualify_contract'):
            info = ib_connector.get_symbol_info("AAPL")

        assert info["symbol"] == "AAPL"
        assert info["name"] == "Apple Inc."
        assert info["security_type"] == "STK"
        assert info["exchange"] == "SMART"
        assert info["currency"] == "USD"
        assert info["min_tick"] == 0.01
        assert info["price_precision"] == 2
        assert info["multiplier"] is None

    def test_get_symbol_info_with_error(self, ib_connector, mock_ib):
        """Test getting symbol information with error"""
        # Mock contract details to raise an error
        mock_ib.reqContractDetails.side_effect = RequestError("Contract not found")

        # Mock contract qualification
        with patch.object(ib_connector, '_qualify_contract'):
            with pytest.raises(ExecutionError):
                ib_connector.get_symbol_info("INVALID")


class TestIBExecutionConnectorAsync:
    """Test cases for async methods in IBExecutionConnector"""

    @pytest.fixture
    def mock_ib(self):
        """Mock IB client"""
        mock = Mock(spec=ib_async.IB)
        mock.isConnected = Mock(return_value=True)
        mock.reqContractDetails = Mock(return_value=[])
        mock.reqMktData = Mock()
        mock.cancelMktData = Mock()
        mock.reqHistoricalData = Mock(return_value=[])
        mock.reqRealTimeBars = Mock()
        mock.cancelRealTimeBars = Mock()
        mock.reqMarketDepth = Mock()
        mock.cancelMarketDepth = Mock()
        mock.reqScannerSubscription = Mock()
        mock.cancelScannerSubscription = Mock()
        mock.reqScannerParameters = Mock(return_value="")
        mock.reqMktDepthExchanges = Mock(return_value=[])
        mock.placeOrder = Mock()
        mock.cancelOrder = Mock()
        mock.reqGlobalCancel = Mock()
        mock.reqOpenOrders = Mock(return_value=[])
        mock.reqAllOpenOrders = Mock(return_value=[])
        mock.reqExecutions = Mock(return_value=[])
        mock.reqCommissionReport = Mock(return_value=[])
        mock.positions = Mock(return_value=[])
        mock.accountSummary = Mock(return_value=[])
        mock.accountValues = Mock(return_value=[])
        mock.managedAccounts = Mock(return_value=[])
        mock.updateAccount = Mock()
        mock.updateAccountValue = Mock()
        mock.updatePortfolio = Mock()
        mock.disconnect = Mock()
        mock.trades = Mock(return_value=[])
        mock.connectAsync = AsyncMock()
        return mock

    @pytest.fixture
    def ib_connector(self, mock_ib):
        """Create IBExecutionConnector instance with mocked IB client"""
        # Mock connectAsync for initialization
        mock_ib.connectAsync = AsyncMock()

        with patch('quantchain.connectors.ib_async_execution.IB', return_value=mock_ib):
            connector = IBExecutionConnector()
            connector.ib = mock_ib  # Directly set the mocked IB instance
            connector._order_map = {}
            return connector

    @pytest.mark.asyncio
    async def test_async_place_order(self, ib_connector, mock_ib):
        """Test async order placement"""
        from quantchain.tools.trading_execution import (
            OrderRequest, OrderSide, OrderType, TimeInForce
        )

        order_request = OrderRequest(
            symbol="AAPL",
            quantity=100,
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            time_in_force=TimeInForce.DAY,
        )

        # Mock qualification of contract
        with patch.object(ib_connector, '_qualify_contract', return_value=Mock()):
            # Mock order placement
            mock_trade = Mock()
            mock_trade.orderStatus.status = "Filled"
            mock_trade.order.permId = 12345
            mock_ib.placeOrder.return_value = mock_trade

            result = ib_connector.place_order(order_request)

            assert result.order_id == "12345"
            assert result.status.value == "filled"
            mock_ib.placeOrder.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_cancel_order(self, ib_connector, mock_ib):
        """Test async order cancellation"""
        # Mock an existing order
        order_id = "12345"
        mock_trade = Mock()
        ib_connector._order_map[order_id] = mock_trade

        # Mock the cancel method to set order status
        mock_trade.orderStatus.status = "Cancelled"

        result = ib_connector.cancel_order(order_id)

        assert result.order_id == order_id
        mock_ib.cancelOrder.assert_called_once()
        assert order_id not in ib_connector._order_map


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
