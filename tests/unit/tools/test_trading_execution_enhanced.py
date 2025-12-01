"""Enhanced comprehensive tests for trading execution module."""

from datetime import datetime

import pytest

from quantchain.core.exceptions import (
    InsufficientFundsError,
    OrderNotFoundError,
    TradingError,
    ValidationError,
)
from quantchain.tools.trading_execution import (
    AccountInfo,
    OrderRequest,
    OrderResult,
    OrderSide,
    OrderStatus,
    OrderType,
    Position,
    TradingExecutionTool,
)


class TestOrderRequest:
    """Test OrderRequest class functionality."""

    @pytest.mark.unit
    def test_order_request_creation_market(self):
        """Test creating a market order request."""
        order = OrderRequest(
            symbol="AAPL", side=OrderSide.BUY, order_type=OrderType.MARKET, quantity=100
        )

        assert order.symbol == "AAPL"
        assert order.side == OrderSide.BUY
        assert order.order_type == OrderType.MARKET
        assert order.quantity == 100
        assert order.price is None
        assert order.stop_price is None
        assert order.time_in_force == "GTC"
        assert order.client_order_id is not None
        assert order.created_at is not None

    @pytest.mark.unit
    def test_order_request_creation_limit(self):
        """Test creating a limit order request."""
        order = OrderRequest(
            symbol="GOOGL",
            side=OrderSide.SELL,
            order_type=OrderType.LIMIT,
            quantity=50,
            price=150.0,
        )

        assert order.price == 150.0
        assert order.stop_price is None

    @pytest.mark.unit
    def test_order_request_creation_stop(self):
        """Test creating a stop order request."""
        order = OrderRequest(
            symbol="MSFT",
            side=OrderSide.BUY,
            order_type=OrderType.STOP,
            quantity=75,
            stop_price=155.0,
        )

        assert order.price is None
        assert order.stop_price == 155.0

    @pytest.mark.unit
    def test_order_request_creation_stop_limit(self):
        """Test creating a stop-limit order request."""
        order = OrderRequest(
            symbol="TSLA",
            side=OrderSide.SELL,
            order_type=OrderType.STOP_LIMIT,
            quantity=25,
            price=750.0,
            stop_price=760.0,
        )

        assert order.price == 750.0
        assert order.stop_price == 760.0

    @pytest.mark.unit
    def test_order_request_custom_client_id(self):
        """Test creating order request with custom client ID."""
        custom_id = "my_custom_order_123"
        order = OrderRequest(
            symbol="AAPL",
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=100,
            client_order_id=custom_id,
        )

        assert order.client_order_id == custom_id

    @pytest.mark.unit
    def test_order_request_limit_without_price_error(self):
        """Test that limit order without price raises ValidationError."""
        with pytest.raises(ValidationError, match="Price is required for limit order"):
            OrderRequest(
                symbol="AAPL",
                side=OrderSide.BUY,
                order_type=OrderType.LIMIT,
                quantity=100,
            )

    @pytest.mark.unit
    def test_order_request_stop_without_price_error(self):
        """Test that stop order without stop price raises ValidationError."""
        with pytest.raises(
            ValidationError, match="Stop price is required for stop order"
        ):
            OrderRequest(
                symbol="AAPL",
                side=OrderSide.BUY,
                order_type=OrderType.STOP,
                quantity=100,
            )

    @pytest.mark.unit
    def test_order_request_stop_limit_without_prices_error(self):
        """Test that stop-limit order without required prices raises ValidationError."""
        with pytest.raises(ValidationError, match="Price is required for limit order"):
            OrderRequest(
                symbol="AAPL",
                side=OrderSide.BUY,
                order_type=OrderType.STOP_LIMIT,
                quantity=100,
                stop_price=150.0,  # Missing limit price
            )


class TestOrderResult:
    """Test OrderResult class functionality."""

    @pytest.mark.unit
    def test_order_result_creation_filled(self):
        """Test creating a filled order result."""
        result = OrderResult(
            order_id="exchange_123",
            symbol="AAPL",
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=100,
            filled_quantity=100,
            price=150.0,
            average_price=150.25,
            status=OrderStatus.FILLED,
            timestamp=datetime.now(),
        )

        assert result.order_id == "exchange_123"
        assert result.symbol == "AAPL"
        assert result.side == OrderSide.BUY
        assert result.order_type == OrderType.MARKET
        assert result.quantity == 100
        assert result.filled_quantity == 100
        assert result.price == 150.0
        assert result.average_price == 150.25
        assert result.status == OrderStatus.FILLED
        assert result.error_message is None

    @pytest.mark.unit
    def test_order_result_creation_partial_fill(self):
        """Test creating a partially filled order result."""
        result = OrderResult(
            order_id="exchange_456",
            symbol="GOOGL",
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            quantity=200,
            filled_quantity=50,
            price=2800.0,
            average_price=2799.5,
            status=OrderStatus.PARTIALLY_FILLED,
            timestamp=datetime.now(),
        )

        assert result.status == OrderStatus.PARTIALLY_FILLED
        assert result.filled_quantity == 50

    @pytest.mark.unit
    def test_order_result_creation_rejected(self):
        """Test creating a rejected order result."""
        result = OrderResult(
            order_id="exchange_789",
            symbol="TSLA",
            side=OrderSide.SELL,
            order_type=OrderType.STOP,
            quantity=75,
            filled_quantity=0,
            price=None,
            average_price=None,
            status=OrderStatus.REJECTED,
            timestamp=datetime.now(),
            error_message="Insufficient margin",
        )

        assert result.status == OrderStatus.REJECTED
        assert result.error_message == "Insufficient margin"


class TestPosition:
    """Test Position class functionality."""

    @pytest.mark.unit
    def test_position_creation_long(self):
        """Test creating a long position."""
        position = Position(
            symbol="AAPL",
            quantity=100,
            side=OrderSide.BUY,
            market_value=15000.0,
            cost_basis=14000.0,
            unrealized_pl=1000.0,
            unrealized_pl_pct=7.14,
        )

        assert position.symbol == "AAPL"
        assert position.quantity == 100
        assert position.side == OrderSide.BUY
        assert position.market_value == 15000.0
        assert position.cost_basis == 14000.0
        assert position.unrealized_pl == 1000.0
        assert position.unrealized_pl_pct == 7.14

    @pytest.mark.unit
    def test_position_creation_short(self):
        """Test creating a short position."""
        position = Position(
            symbol="TSLA",
            quantity=50,
            side=OrderSide.SELL,
            market_value=12500.0,
            cost_basis=13000.0,
            unrealized_pl=500.0,
            unrealized_pl_pct=3.85,
        )

        assert position.side == OrderSide.SELL


class TestAccountInfo:
    """Test AccountInfo class functionality."""

    @pytest.mark.unit
    def test_account_info_creation(self):
        """Test creating account information."""
        account = AccountInfo(
            account_id="ACC123456",
            buying_power=50000.0,
            cash=25000.0,
            portfolio_value=75000.0,
            day_trading_profit_loss=1250.0,
            maintenance_margin=7500.0,
            day_trades_count=15,
            leverage=2.0,
        )

        assert account.account_id == "ACC123456"
        assert account.buying_power == 50000.0
        assert account.cash == 25000.0
        assert account.portfolio_value == 75000.0
        assert account.day_trading_profit_loss == 1250.0
        assert account.maintenance_margin == 7500.0
        assert account.day_trades_count == 15
        assert account.leverage == 2.0


class TestTradingExecutionTool:
    """Test TradingExecutionTool functionality."""

    @pytest.fixture
    def trading_tool(self):
        """Create a trading execution tool for testing."""
        return TradingExecutionTool()

    @pytest.fixture
    def market_order_request(self):
        """Create a market order request for testing."""
        return OrderRequest(
            symbol="AAPL", side=OrderSide.BUY, order_type=OrderType.MARKET, quantity=100
        )

    @pytest.fixture
    def limit_order_request(self):
        """Create a limit order request for testing."""
        return OrderRequest(
            symbol="GOOGL",
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            quantity=50,
            price=150.0,
        )

    @pytest.mark.unit
    def test_trading_tool_init_default(self, trading_tool):
        """Test trading tool initialization with default parameters."""
        assert trading_tool.config == {}
        assert trading_tool.retry_count == 3
        assert trading_tool.retry_delay == 1.0
        assert trading_tool._orders == {}
        assert trading_tool._positions == {}

    @pytest.mark.unit
    def test_trading_tool_init_custom(self):
        """Test trading tool initialization with custom parameters."""
        config = {"test_param": "test_value"}
        tool = TradingExecutionTool(config=config, retry_count=5, retry_delay=2.0)

        assert tool.config == config
        assert tool.retry_count == 5
        assert tool.retry_delay == 2.0

    @pytest.mark.unit
    def test_place_market_order_buy(self, trading_tool, market_order_request):
        """Test placing a market buy order."""
        result = trading_tool.place_order(market_order_request)

        # Check that order was stored
        assert market_order_request.client_order_id in trading_tool._orders

        # Check result properties
        assert result.symbol == "AAPL"
        assert result.side == OrderSide.BUY
        assert result.order_type == OrderType.MARKET
        assert result.quantity == 100
        assert result.filled_quantity == 100
        assert result.status == OrderStatus.FILLED
        assert result.average_price is not None
        assert result.price is not None

        # Check that position was created
        assert "AAPL" in trading_tool._positions
        position = trading_tool._positions["AAPL"]
        assert position.quantity == 100
        assert position.side == OrderSide.BUY

    @pytest.mark.unit
    def test_place_market_order_sell_existing_position(self, trading_tool):
        """Test placing a market sell order with existing position."""
        # First create a position by buying
        buy_order = OrderRequest(
            symbol="AAPL", side=OrderSide.BUY, order_type=OrderType.MARKET, quantity=200
        )
        trading_tool.place_order(buy_order)

        # Now sell part of the position
        sell_order = OrderRequest(
            symbol="AAPL", side=OrderSide.SELL, order_type=OrderType.MARKET, quantity=50
        )
        result = trading_tool.place_order(sell_order)

        assert result.status == OrderStatus.FILLED
        assert result.filled_quantity == 50

        # Check that position was reduced
        position = trading_tool._positions["AAPL"]
        assert position.quantity == 150

    @pytest.mark.unit
    def test_place_market_order_sell_insufficient_position(self, trading_tool):
        """Test placing a market sell order with insufficient position."""
        sell_order = OrderRequest(
            symbol="AAPL",
            side=OrderSide.SELL,
            order_type=OrderType.MARKET,
            quantity=100,
        )

        with pytest.raises(InsufficientFundsError, match="No position for AAPL"):
            trading_tool.place_order(sell_order)

    @pytest.mark.unit
    def test_place_limit_order(self, trading_tool, limit_order_request):
        """Test placing a limit order."""
        result = trading_tool.place_order(limit_order_request)

        # Check that order is submitted but not filled
        assert result.status == OrderStatus.SUBMITTED
        assert result.filled_quantity == 0
        assert result.price == 150.0
        assert result.average_price is None

        # Position should not be created for limit orders
        assert "GOOGL" not in trading_tool._positions

    @pytest.mark.unit
    def test_place_stop_order(self, trading_tool):
        """Test placing a stop order."""
        stop_order = OrderRequest(
            symbol="MSFT",
            side=OrderSide.BUY,
            order_type=OrderType.STOP,
            quantity=75,
            stop_price=155.0,
        )

        result = trading_tool.place_order(stop_order)

        assert result.status == OrderStatus.SUBMITTED
        assert result.stop_price == 155.0

    @pytest.mark.unit
    def test_place_stop_limit_order(self, trading_tool):
        """Test placing a stop-limit order."""
        stop_limit_order = OrderRequest(
            symbol="TSLA",
            side=OrderSide.SELL,
            order_type=OrderType.STOP_LIMIT,
            quantity=25,
            price=750.0,
            stop_price=760.0,
        )

        result = trading_tool.place_order(stop_limit_order)

        assert result.status == OrderStatus.SUBMITTED
        assert result.price == 750.0
        assert result.stop_price == 760.0

    @pytest.mark.unit
    def test_cancel_order_submitted(self, trading_tool, limit_order_request):
        """Test cancelling a submitted order."""
        # Place a limit order
        order_result = trading_tool.place_order(limit_order_request)
        order_id = order_result.order_id

        # Cancel the order
        success = trading_tool.cancel_order(order_id)

        assert success is True

        # Check that order status was updated
        updated_order = trading_tool.get_order_status(order_id)
        assert updated_order.status == OrderStatus.CANCELLED

    @pytest.mark.unit
    def test_cancel_order_request_not_submitted(self, trading_tool):
        """Test cancelling an order that hasn't been submitted yet."""
        order_request = OrderRequest(
            symbol="AAPL",
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            quantity=100,
            price=150.0,
        )

        # Manually add the request without submitting
        trading_tool._orders[order_request.client_order_id] = order_request

        # Cancel the order
        success = trading_tool.cancel_order(order_request.client_order_id)

        assert success is True

    @pytest.mark.unit
    def test_cancel_filled_order_error(self, trading_tool, market_order_request):
        """Test that cancelling a filled order raises error."""
        # Place and fill a market order
        order_result = trading_tool.place_order(market_order_request)
        order_id = order_result.order_id

        # Try to cancel the filled order
        with pytest.raises(TradingError, match="Cannot cancel filled order"):
            trading_tool.cancel_order(order_id)

    @pytest.mark.unit
    def test_cancel_nonexistent_order_error(self, trading_tool):
        """Test that cancelling non-existent order raises error."""
        with pytest.raises(OrderNotFoundError, match="Order nonexistent not found"):
            trading_tool.cancel_order("nonexistent")

    @pytest.mark.unit
    def test_get_order_status_existing(self, trading_tool, market_order_request):
        """Test getting status of existing order."""
        order_result = trading_tool.place_order(market_order_request)
        order_id = order_result.order_id

        status = trading_tool.get_order_status(order_id)

        assert status.order_id == order_id
        assert status.symbol == "AAPL"
        assert status.status == OrderStatus.FILLED

    @pytest.mark.unit
    def test_get_order_status_request_not_submitted(self, trading_tool):
        """Test getting status of order request that hasn't been submitted."""
        order_request = OrderRequest(
            symbol="AAPL",
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            quantity=100,
            price=150.0,
        )

        # Manually add the request without submitting
        trading_tool._orders[order_request.client_order_id] = order_request

        status = trading_tool.get_order_status(order_request.client_order_id)

        assert status.status == OrderStatus.SUBMITTED
        assert status.symbol == "AAPL"

    @pytest.mark.unit
    def test_get_order_status_nonexistent(self, trading_tool):
        """Test getting status of non-existent order."""
        with pytest.raises(OrderNotFoundError, match="Order nonexistent not found"):
            trading_tool.get_order_status("nonexistent")

    @pytest.mark.unit
    def test_get_positions_empty(self, trading_tool):
        """Test getting positions when none exist."""
        positions = trading_tool.get_positions()
        assert positions == []

    @pytest.mark.unit
    def test_get_positions_with_positions(self, trading_tool):
        """Test getting positions when positions exist."""
        # Create some positions
        orders = [
            OrderRequest("AAPL", OrderSide.BUY, OrderType.MARKET, 100),
            OrderRequest("GOOGL", OrderSide.BUY, OrderType.MARKET, 50),
        ]

        for order in orders:
            trading_tool.place_order(order)

        positions = trading_tool.get_positions()
        assert len(positions) == 2

        symbols = [pos.symbol for pos in positions]
        assert "AAPL" in symbols
        assert "GOOGL" in symbols

    @pytest.mark.unit
    def test_get_position_existing(self, trading_tool, market_order_request):
        """Test getting position for existing symbol."""
        trading_tool.place_order(market_order_request)

        position = trading_tool.get_position("AAPL")

        assert position is not None
        assert position.symbol == "AAPL"
        assert position.quantity == 100

    @pytest.mark.unit
    def test_get_position_nonexistent(self, trading_tool):
        """Test getting position for non-existent symbol."""
        position = trading_tool.get_position("NONEXISTENT")
        assert position is None

    @pytest.mark.unit
    def test_get_account_info_empty(self, trading_tool):
        """Test getting account info with no positions."""
        account = trading_tool.get_account_info()

        assert account.account_id == "mock_account"
        assert account.buying_power == 0.0
        assert account.cash == 0.0
        assert account.portfolio_value == 0.0
        assert account.day_trading_profit_loss == 0.0
        assert account.maintenance_margin == 0.0
        assert account.day_trades_count == 0
        assert account.leverage == 2.0

    @pytest.mark.unit
    def test_get_account_info_with_positions(self, trading_tool):
        """Test getting account info with positions."""
        # Create some positions
        orders = [
            OrderRequest("AAPL", OrderSide.BUY, OrderType.MARKET, 100),
            OrderRequest("GOOGL", OrderSide.BUY, OrderType.MARKET, 50),
        ]

        for order in orders:
            trading_tool.place_order(order)

        account = trading_tool.get_account_info()

        assert account.portfolio_value > 0
        assert account.buying_power > 0
        assert account.cash > 0
        assert account.day_trades_count >= 2  # At least 2 orders placed

    @pytest.mark.unit
    def test_get_order_history_all(self, trading_tool):
        """Test getting all order history."""
        # Place some orders
        orders = [
            OrderRequest("AAPL", OrderSide.BUY, OrderType.MARKET, 100),
            OrderRequest("GOOGL", OrderSide.BUY, OrderType.LIMIT, 50, price=150.0),
        ]

        for order in orders:
            trading_tool.place_order(order)

        history = trading_tool.get_order_history()

        assert len(history) >= 2

        # Should be sorted by timestamp (newest first)
        timestamps = [order.timestamp for order in history]
        assert timestamps == sorted(timestamps, reverse=True)

    @pytest.mark.unit
    def test_get_order_history_symbol_filter(self, trading_tool):
        """Test getting order history filtered by symbol."""
        # Place some orders
        orders = [
            OrderRequest("AAPL", OrderSide.BUY, OrderType.MARKET, 100),
            OrderRequest("GOOGL", OrderSide.BUY, OrderType.MARKET, 50),
            OrderRequest("AAPL", OrderSide.SELL, OrderType.MARKET, 25),
        ]

        for order in orders:
            # For the sell order, we need to have a position first
            if order.side == OrderSide.SELL:
                # Create position first by buying more
                buy_order = OrderRequest("AAPL", OrderSide.BUY, OrderType.MARKET, 100)
                trading_tool.place_order(buy_order)
            trading_tool.place_order(order)

        aapl_history = trading_tool.get_order_history(symbol="AAPL")
        googl_history = trading_tool.get_order_history(symbol="GOOGL")

        # All AAPL orders should be in AAPL history
        assert len(aapl_history) >= 2
        for order in aapl_history:
            assert order.symbol == "AAPL"

        # All GOOGL orders should be in GOOGL history
        assert len(googl_history) >= 1
        for order in googl_history:
            assert order.symbol == "GOOGL"

    @pytest.mark.unit
    def test_get_order_history_limit(self, trading_tool):
        """Test getting order history with limit."""
        # Place more orders than the limit
        for i in range(5):
            order = OrderRequest(f"STOCK{i}", OrderSide.BUY, OrderType.MARKET, 100)
            trading_tool.place_order(order)

        history = trading_tool.get_order_history(limit=3)

        assert len(history) == 3

    @pytest.mark.unit
    def test_multiple_buy_orders_same_symbol(self, trading_tool):
        """Test multiple buy orders for the same symbol."""
        order1 = OrderRequest("AAPL", OrderSide.BUY, OrderType.MARKET, 100)
        order2 = OrderRequest("AAPL", OrderSide.BUY, OrderType.MARKET, 50)

        trading_tool.place_order(order1)
        trading_tool.place_order(order2)

        position = trading_tool.get_position("AAPL")
        assert position.quantity == 150

        # Cost basis should be accumulated
        assert position.cost_basis > 0

    @pytest.mark.unit
    def test_sell_entire_position(self, trading_tool):
        """Test selling entire position."""
        # Create a position
        buy_order = OrderRequest("AAPL", OrderSide.BUY, OrderType.MARKET, 100)
        trading_tool.place_order(buy_order)

        # Sell the entire position
        sell_order = OrderRequest("AAPL", OrderSide.SELL, OrderType.MARKET, 100)
        result = trading_tool.place_order(sell_order)

        assert result.status == OrderStatus.FILLED

        # Position should be closed (quantity 0)
        position = trading_tool.get_position("AAPL")
        assert position.quantity == 0

    @pytest.mark.unit
    def test_order_id_uniqueness(self, trading_tool):
        """Test that each order gets a unique ID."""
        orders = [
            OrderRequest("AAPL", OrderSide.BUY, OrderType.MARKET, 100),
            OrderRequest("GOOGL", OrderSide.BUY, OrderType.MARKET, 50),
        ]

        order_ids = []
        for order in orders:
            result = trading_tool.place_order(order)
            order_ids.append(result.order_id)

        # All order IDs should be unique
        assert len(set(order_ids)) == len(order_ids)
