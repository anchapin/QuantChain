"""Comprehensive tests for trading_execution module."""

import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

from quantchain.tools.trading_execution import (
    OrderSide,
    OrderType,
    OrderStatus,
    OrderRequest,
    OrderResult,
    AccountInfo,
    Position,
    TradingExecutionTool,
)


class TestOrderSide:
    """Test OrderSide enum."""

    def test_order_side_values(self) -> None:
        """Test that order side values are correct."""
        assert OrderSide.BUY.value == "buy"
        assert OrderSide.SELL.value == "sell"


class TestOrderType:
    """Test OrderType enum."""

    def test_order_type_values(self) -> None:
        """Test that order type values are correct."""
        assert OrderType.MARKET.value == "market"
        assert OrderType.LIMIT.value == "limit"
        assert OrderType.STOP.value == "stop"
        assert OrderType.STOP_LIMIT.value == "stop_limit"


class TestOrderStatus:
    """Test OrderStatus enum."""

    def test_order_status_values(self) -> None:
        """Test that order status values are correct."""
        assert OrderStatus.NEW.value == "new"
        assert OrderStatus.SUBMITTED.value == "submitted"
        assert OrderStatus.FILLED.value == "filled"
        assert OrderStatus.PARTIALLY_FILLED.value == "partially_filled"
        assert OrderStatus.REJECTED.value == "rejected"
        assert OrderStatus.CANCELLED.value == "cancelled"
        assert OrderStatus.EXPIRED.value == "expired"


class TestOrderRequest:
    """Test OrderRequest class."""

    def test_order_request_creation_market(self) -> None:
        """Test creating a market order request."""
        order = OrderRequest(
            symbol="AAPL",
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=100.0,
        )

        assert order.symbol == "AAPL"
        assert order.side == OrderSide.BUY
        assert order.order_type == OrderType.MARKET
        assert order.quantity == 100.0
        assert order.price is None
        assert order.stop_price is None
        assert order.time_in_force == "GTC"
        assert order.client_order_id is not None
        assert order.created_at is not None

    def test_order_request_creation_limit(self) -> None:
        """Test creating a limit order request."""
        order = OrderRequest(
            symbol="MSFT",
            side=OrderSide.SELL,
            order_type=OrderType.LIMIT,
            quantity=50.0,
            price=250.0,
        )

        assert order.symbol == "MSFT"
        assert order.side == OrderSide.SELL
        assert order.order_type == OrderType.LIMIT
        assert order.quantity == 50.0
        assert order.price == 250.0
        assert order.stop_price is None

    def test_order_request_creation_stop(self) -> None:
        """Test creating a stop order request."""
        order = OrderRequest(
            symbol="GOOGL",
            side=OrderSide.BUY,
            order_type=OrderType.STOP,
            quantity=75.0,
            stop_price=150.0,
        )

        assert order.symbol == "GOOGL"
        assert order.side == OrderSide.BUY
        assert order.order_type == OrderType.STOP
        assert order.quantity == 75.0
        assert order.price is None
        assert order.stop_price == 150.0

    def test_order_request_creation_stop_limit(self) -> None:
        """Test creating a stop-limit order request."""
        order = OrderRequest(
            symbol="TSLA",
            side=OrderSide.SELL,
            order_type=OrderType.STOP_LIMIT,
            quantity=25.0,
            price=800.0,
            stop_price=850.0,
        )

        assert order.symbol == "TSLA"
        assert order.side == OrderSide.SELL
        assert order.order_type == OrderType.STOP_LIMIT
        assert order.quantity == 25.0
        assert order.price == 800.0
        assert order.stop_price == 850.0

    def test_order_request_custom_time_in_force(self) -> None:
        """Test creating an order with custom time in force."""
        order = OrderRequest(
            symbol="AMZN",
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            quantity=10.0,
            price=3200.0,
            time_in_force="IOC",  # Immediate or Cancel
        )

        assert order.time_in_force == "IOC"

    def test_order_request_custom_client_id(self) -> None:
        """Test creating an order with custom client order ID."""
        custom_id = "my_custom_order_123"
        order = OrderRequest(
            symbol="NFLX",
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=30.0,
            client_order_id=custom_id,
        )

        assert order.client_order_id == custom_id

    def test_order_request_validation_limit_without_price(self) -> None:
        """Test that limit orders require a price."""
        with pytest.raises(Exception) as excinfo:
            OrderRequest(
                symbol="AAPL",
                side=OrderSide.BUY,
                order_type=OrderType.LIMIT,
                quantity=100.0,
            )

        assert "Price is required for limit order" in str(excinfo.value)

    def test_order_request_validation_stop_without_stop_price(self) -> None:
        """Test that stop orders require a stop price."""
        with pytest.raises(Exception) as excinfo:
            OrderRequest(
                symbol="AAPL",
                side=OrderSide.BUY,
                order_type=OrderType.STOP,
                quantity=100.0,
            )

        assert "Stop price is required for stop order" in str(excinfo.value)

    def test_order_request_validation_stop_limit_without_prices(self) -> None:
        """Test that stop-limit orders require both price and stop price."""
        with pytest.raises(Exception) as excinfo:
            OrderRequest(
                symbol="AAPL",
                side=OrderSide.BUY,
                order_type=OrderType.STOP_LIMIT,
                quantity=100.0,
                price=150.0,
                # Missing stop_price
            )

        assert "Stop price is required for stop order" in str(excinfo.value)


class TestOrderResult:
    """Test OrderResult class."""

    def test_order_result_creation(self) -> None:
        """Test creating an order result."""
        timestamp = datetime.now()
        result = OrderResult(
            order_id="order_123",
            symbol="AAPL",
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=100.0,
            filled_quantity=100.0,
            price=None,
            average_price=150.0,
            status=OrderStatus.FILLED,
            timestamp=timestamp,
        )

        assert result.order_id == "order_123"
        assert result.symbol == "AAPL"
        assert result.side == OrderSide.BUY
        assert result.order_type == OrderType.MARKET
        assert result.quantity == 100.0
        assert result.filled_quantity == 100.0
        assert result.price is None
        assert result.average_price == 150.0
        assert result.status == OrderStatus.FILLED
        assert result.timestamp == timestamp
        assert result.error_message is None

    def test_order_result_with_error(self) -> None:
        """Test creating an order result with an error."""
        timestamp = datetime.now()
        error_msg = "Insufficient funds"
        result = OrderResult(
            order_id="order_456",
            symbol="MSFT",
            side=OrderSide.SELL,
            order_type=OrderType.MARKET,
            quantity=50.0,
            filled_quantity=0.0,
            price=None,
            average_price=None,
            status=OrderStatus.REJECTED,
            timestamp=timestamp,
            error_message=error_msg,
        )

        assert result.error_message == error_msg

    def test_order_result_partial_fill(self) -> None:
        """Test creating an order result with partial fill."""
        timestamp = datetime.now()
        result = OrderResult(
            order_id="order_789",
            symbol="GOOGL",
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            quantity=100.0,
            filled_quantity=50.0,
            price=1500.0,
            average_price=1500.0,
            status=OrderStatus.PARTIALLY_FILLED,
            timestamp=timestamp,
        )

        assert result.quantity == 100.0
        assert result.filled_quantity == 50.0
        assert result.status == OrderStatus.PARTIALLY_FILLED


class TestAccountInfo:
    """Test AccountInfo class."""

    def test_account_info_creation(self) -> None:
        """Test creating account information."""
        account = AccountInfo(
            account_id="acc_123",
            buying_power=100000.0,
            cash=50000.0,
            portfolio_value=75000.0,
            day_trading_profit_loss=1250.0,
            maintenance_margin=15000.0,
            day_trades_count=5,
            leverage=2.0,
        )

        assert account.account_id == "acc_123"
        assert account.buying_power == 100000.0
        assert account.cash == 50000.0
        assert account.portfolio_value == 75000.0
        assert account.day_trading_profit_loss == 1250.0
        assert account.maintenance_margin == 15000.0
        assert account.day_trades_count == 5
        assert account.leverage == 2.0


class TestPosition:
    """Test Position class."""

    def test_position_creation_long(self) -> None:
        """Test creating a long position."""
        position = Position(
            symbol="AAPL",
            quantity=100.0,
            side=OrderSide.BUY,
            market_value=15000.0,
            cost_basis=14000.0,
            unrealized_pl=1000.0,
            unrealized_pl_pct=7.14,
        )

        assert position.symbol == "AAPL"
        assert position.quantity == 100.0
        assert position.side == OrderSide.BUY
        assert position.market_value == 15000.0
        assert position.cost_basis == 14000.0
        assert position.unrealized_pl == 1000.0
        assert position.unrealized_pl_pct == 7.14

    def test_position_creation_short(self) -> None:
        """Test creating a short position."""
        position = Position(
            symbol="TSLA",
            quantity=50.0,
            side=OrderSide.SELL,
            market_value=20000.0,
            cost_basis=21000.0,
            unrealized_pl=-1000.0,
            unrealized_pl_pct=-4.76,
        )

        assert position.symbol == "TSLA"
        assert position.quantity == 50.0
        assert position.side == OrderSide.SELL
        assert position.market_value == 20000.0
        assert position.cost_basis == 21000.0
        assert position.unrealized_pl == -1000.0
        assert position.unrealized_pl_pct == -4.76

    def test_position_zero_quantity(self) -> None:
        """Test creating a position with zero quantity (closed position)."""
        position = Position(
            symbol="MSFT",
            quantity=0.0,
            side=OrderSide.BUY,
            market_value=0.0,
            cost_basis=5000.0,
            unrealized_pl=-500.0,
            unrealized_pl_pct=-10.0,
        )

        assert position.quantity == 0.0
        assert position.market_value == 0.0


class TestTradingExecutionTool:
    """Test TradingExecutionTool class."""

    @pytest.fixture
    def tool(self) -> TradingExecutionTool:
        """Create a trading execution tool for testing."""
        return TradingExecutionTool()

    def test_initialization(self, tool: TradingExecutionTool) -> None:
        """Test trading execution tool initialization."""
        assert tool is not None
        assert hasattr(tool, "_positions")
        assert hasattr(tool, "_orders")

    def test_place_order_market_buy(self, tool: TradingExecutionTool) -> None:
        """Test placing a market buy order."""
        order_request = OrderRequest(
            symbol="AAPL",
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=100.0,
        )

        result = tool.place_order(order_request)

        assert result.symbol == "AAPL"
        assert result.side == OrderSide.BUY
        assert result.order_type == OrderType.MARKET
        assert result.quantity == 100.0
        assert result.filled_quantity == 100.0
        assert result.status == OrderStatus.FILLED
        assert result.average_price is not None
        assert result.order_id is not None

    def test_place_order_market_sell(self, tool: TradingExecutionTool) -> None:
        """Test placing a market sell order with existing position."""
        # First create a position
        tool._positions["AAPL"] = Position(
            symbol="AAPL",
            quantity=200.0,
            side=OrderSide.BUY,
            market_value=30000.0,
            cost_basis=28000.0,
            unrealized_pl=2000.0,
            unrealized_pl_pct=7.14,
        )

        order_request = OrderRequest(
            symbol="AAPL",
            side=OrderSide.SELL,
            order_type=OrderType.MARKET,
            quantity=50.0,
        )

        result = tool.place_order(order_request)

        assert result.symbol == "AAPL"
        assert result.side == OrderSide.SELL
        assert result.order_type == OrderType.MARKET
        assert result.quantity == 50.0
        assert result.filled_quantity == 50.0
        assert result.status == OrderStatus.FILLED

        # Check position was updated
        position = tool._positions["AAPL"]
        assert position.quantity == 150.0  # 200 - 50

    def test_place_order_limit(self, tool: TradingExecutionTool) -> None:
        """Test placing a limit order."""
        order_request = OrderRequest(
            symbol="MSFT",
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            quantity=75.0,
            price=250.0,
        )

        result = tool.place_order(order_request)

        assert result.symbol == "MSFT"
        assert result.side == OrderSide.BUY
        assert result.order_type == OrderType.LIMIT
        assert result.quantity == 75.0
        assert result.filled_quantity == 0.0
        assert result.status == OrderStatus.SUBMITTED
        assert result.price == 250.0

    def test_place_order_stop(self, tool: TradingExecutionTool) -> None:
        """Test placing a stop order."""
        order_request = OrderRequest(
            symbol="GOOGL",
            side=OrderSide.SELL,
            order_type=OrderType.STOP,
            quantity=30.0,
            stop_price=1400.0,
        )

        result = tool.place_order(order_request)

        assert result.symbol == "GOOGL"
        assert result.side == OrderSide.SELL
        assert result.order_type == OrderType.STOP
        assert result.quantity == 30.0
        assert result.filled_quantity == 0.0
        assert result.status == OrderStatus.SUBMITTED
        assert result.stop_price == 1400.0

    def test_place_order_stop_limit(self, tool: TradingExecutionTool) -> None:
        """Test placing a stop-limit order."""
        order_request = OrderRequest(
            symbol="TSLA",
            side=OrderSide.BUY,
            order_type=OrderType.STOP_LIMIT,
            quantity=25.0,
            price=800.0,
            stop_price=850.0,
        )

        result = tool.place_order(order_request)

        assert result.symbol == "TSLA"
        assert result.side == OrderSide.BUY
        assert result.order_type == OrderType.STOP_LIMIT
        assert result.quantity == 25.0
        assert result.filled_quantity == 0.0
        assert result.status == OrderStatus.SUBMITTED
        assert result.price == 800.0
        assert result.stop_price == 850.0

    def test_place_order_insufficient_position(
        self, tool: TradingExecutionTool
    ) -> None:
        """Test placing a sell order without sufficient position."""
        order_request = OrderRequest(
            symbol="AAPL",
            side=OrderSide.SELL,
            order_type=OrderType.MARKET,
            quantity=100.0,
        )

        # Should raise an error when trying to sell without position
        with pytest.raises(Exception):
            tool.place_order(order_request)

    def test_cancel_order(self, tool: TradingExecutionTool) -> None:
        """Test canceling an order."""
        # First place a limit order
        order_request = OrderRequest(
            symbol="AAPL",
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            quantity=100.0,
            price=150.0,
        )

        result = tool.place_order(order_request)
        order_id = result.order_id

        # Now cancel it
        cancel_result = tool.cancel_order(order_id)

        assert cancel_result is True

        # Check order status is updated
        updated_order = tool.get_order_status(order_id)
        assert updated_order.status == OrderStatus.CANCELLED

    def test_cancel_nonexistent_order(self, tool: TradingExecutionTool) -> None:
        """Test canceling an order that doesn't exist."""
        with pytest.raises(Exception):
            tool.cancel_order("nonexistent_order_id")

    def test_cancel_filled_order(self, tool: TradingExecutionTool) -> None:
        """Test canceling an already filled order."""
        # First place a market order (which fills immediately)
        order_request = OrderRequest(
            symbol="AAPL",
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=100.0,
        )

        result = tool.place_order(order_request)
        order_id = result.order_id

        # Should not be able to cancel a filled order
        with pytest.raises(Exception):
            tool.cancel_order(order_id)

    def test_get_order_status(self, tool: TradingExecutionTool) -> None:
        """Test getting order status information."""
        # Place an order first
        order_request = OrderRequest(
            symbol="AAPL",
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=100.0,
        )

        placed_order = tool.place_order(order_request)
        order_id = placed_order.order_id

        # Get the order status
        retrieved_order = tool.get_order_status(order_id)

        assert retrieved_order is not None
        assert retrieved_order.order_id == order_id
        assert retrieved_order.symbol == "AAPL"
        assert retrieved_order.side == OrderSide.BUY

    def test_get_nonexistent_order_status(self, tool: TradingExecutionTool) -> None:
        """Test getting status for an order that doesn't exist."""
        with pytest.raises(Exception):
            tool.get_order_status("nonexistent_order_id")

    def test_get_positions(self, tool: TradingExecutionTool) -> None:
        """Test getting all positions."""
        # Initially should be empty
        positions = tool.get_positions()
        assert positions == []

        # Place a buy order to create a position
        order_request = OrderRequest(
            symbol="AAPL",
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=100.0,
        )

        tool.place_order(order_request)

        # Now should have one position
        positions = tool.get_positions()
        assert len(positions) == 1
        assert positions[0].symbol == "AAPL"
        assert positions[0].quantity == 100.0

    def test_get_position(self, tool: TradingExecutionTool) -> None:
        """Test getting a specific position."""
        # Place a buy order to create a position
        order_request = OrderRequest(
            symbol="AAPL",
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=100.0,
        )

        tool.place_order(order_request)

        # Get the position
        position = tool.get_position("AAPL")

        assert position is not None
        assert position.symbol == "AAPL"
        assert position.quantity == 100.0

    def test_get_nonexistent_position(self, tool: TradingExecutionTool) -> None:
        """Test getting a position that doesn't exist."""
        position = tool.get_position("NON_EXISTENT")
        assert position is None

    def test_get_account_info(self, tool: TradingExecutionTool) -> None:
        """Test getting account information."""
        account_info = tool.get_account_info()

        assert account_info is not None
        assert account_info.account_id is not None
        assert account_info.buying_power >= 0
        assert account_info.cash >= 0
        assert account_info.portfolio_value >= 0
        assert account_info.maintenance_margin >= 0
        assert account_info.day_trades_count >= 0
        assert account_info.leverage > 0

    def test_get_order_history(self, tool: TradingExecutionTool) -> None:
        """Test getting order history."""
        # Place a few orders
        order_request1 = OrderRequest(
            symbol="AAPL",
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=100.0,
        )

        order_request2 = OrderRequest(
            symbol="MSFT",
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            quantity=50.0,
            price=250.0,
        )

        tool.place_order(order_request1)
        # Add small delay to ensure different timestamps
        import time

        time.sleep(0.01)
        tool.place_order(order_request2)

        # Get order history
        history = tool.get_order_history()

        assert len(history) == 2
        # Should be sorted by timestamp (newest first)
        assert history[0].symbol == "MSFT"  # Placed second
        assert history[1].symbol == "AAPL"  # Placed first

        # Test filtering by symbol
        aapl_history = tool.get_order_history(symbol="AAPL")
        assert len(aapl_history) == 1
        assert aapl_history[0].symbol == "AAPL"

        # Test limit
        limited_history = tool.get_order_history(limit=1)
        assert len(limited_history) == 1
        assert limited_history[0].symbol == "MSFT"  # Most recent
