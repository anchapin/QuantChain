"""Tests for the trading execution base interface."""

import pytest
from datetime import datetime
from typing import Optional

from quantchain.tools.trading_execution import (
    OrderRequest,
    OrderResult,
    OrderSide,
    OrderType,
    OrderStatus,
    TimeInForce,
    Position,
    AccountInfo,
    TradingExecutionInterface,
    ValidationError,
    OrderNotFoundError,
)


class MockTradingExecutor(TradingExecutionInterface):
    """Mock implementation for testing the abstract interface."""

    def __init__(self):
        self.orders = {}
        self.positions: list[float] = []
        self.account = AccountInfo(
            account_id="test-account",
            buying_power=100000.0,
            cash=50000.0,
            portfolio_value=100000.0,
            positions=[],
        )

    def place_order(self, order: OrderRequest) -> OrderResult:
        """Mock order placement."""
        order_id = f"order_{len(self.orders)}"
        result = OrderResult(
            order_id=order_id,
            client_order_id=order.client_order_id,
            symbol=order.symbol,
            side=order.side,
            order_type=order.order_type,
            quantity=order.quantity,
            filled_quantity=order.quantity,
            price=order.price,
            stop_price=order.stop_price,
            avg_fill_price=order.price or 100.0,
            status=OrderStatus.FILLED,
            timestamp=datetime.now(),
        )
        self.orders[order_id] = result
        return result

    def cancel_order(self, order_id: str) -> OrderResult:
        """Mock order cancellation."""
        if order_id not in self.orders:
            raise OrderNotFoundError(f"Order {order_id} not found")

        order = self.orders[order_id]
        order.status = OrderStatus.CANCELLED
        order.updated_at = datetime.now()
        return order

    def get_order(self, order_id: str) -> OrderResult:
        """Mock order retrieval."""
        if order_id not in self.orders:
            raise OrderNotFoundError(f"Order {order_id} not found")
        return self.orders[order_id]

    def get_account(self) -> AccountInfo:
        """Mock account retrieval."""
        return self.account

    def get_positions(self) -> list:
        """Mock positions retrieval."""
        return self.positions

    def get_order_history(
        self,
        symbol: Optional[str] = None,
        status: Optional[OrderStatus] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: Optional[int] = None,
    ) -> list:
        """Mock order history retrieval."""
        orders = list(self.orders.values())

        # Apply filters
        if symbol:
            orders: list[float] = [o for o in orders if o.symbol == symbol]
        if status:
            orders: list[float] = [o for o in orders if o.status == status]
        if start_date:
            orders: list[float] = [o for o in orders if o.timestamp >= start_date]
        if end_date:
            orders: list[float] = [o for o in orders if o.timestamp <= end_date]
        if limit:
            orders = orders[:limit]

        return orders

    def is_market_open(self, symbol: Optional[str] = None) -> bool:
        """Mock market status check."""
        return True


class TestOrderRequest:
    """Test cases for OrderRequest."""

    def test_valid_market_order(self) -> None:
        """Test creation of a valid market order."""
        order = OrderRequest(
            symbol="AAPL", side=OrderSide.BUY, order_type=OrderType.MARKET, quantity=100
        )
        assert order.symbol == "AAPL"
        assert order.side == OrderSide.BUY
        assert order.order_type == OrderType.MARKET
        assert order.quantity == 100
        assert order.price is None
        assert order.time_in_force == TimeInForce.DAY

    def test_valid_limit_order(self) -> None:
        """Test creation of a valid limit order."""
        order = OrderRequest(
            symbol="MSFT",
            side=OrderSide.SELL,
            order_type=OrderType.LIMIT,
            quantity=50,
            price=250.0,
        )
        assert order.price == 250.0
        assert order.quantity == 50

    def test_valid_stop_order(self) -> None:
        """Test creation of a valid stop order."""
        order = OrderRequest(
            symbol="TSLA",
            side=OrderSide.BUY,
            order_type=OrderType.STOP,
            quantity=25,
            stop_price=800.0,
        )
        assert order.stop_price == 800.0

    def test_valid_stop_limit_order(self) -> None:
        """Test creation of a valid stop limit order."""
        order = OrderRequest(
            symbol="NVDA",
            side=OrderSide.SELL,
            order_type=OrderType.STOP_LIMIT,
            quantity=30,
            price=500.0,
            stop_price=450.0,
        )
        assert order.price == 500.0
        assert order.stop_price == 450.0

    def test_invalid_quantity(self) -> None:
        """Test that orders with invalid quantity raise ValidationError."""
        with pytest.raises(ValidationError, match="Order quantity must be positive"):
            OrderRequest(
                symbol="AAPL",
                side=OrderSide.BUY,
                order_type=OrderType.MARKET,
                quantity=0,
            )

        with pytest.raises(ValidationError, match="Order quantity must be positive"):
            OrderRequest(
                symbol="AAPL",
                side=OrderSide.BUY,
                order_type=OrderType.MARKET,
                quantity=-10,
            )

    def test_limit_order_without_price(self) -> None:
        """Test that limit orders without price raise ValidationError."""
        with pytest.raises(ValidationError, match="Limit orders require a price"):
            OrderRequest(
                symbol="AAPL",
                side=OrderSide.BUY,
                order_type=OrderType.LIMIT,
                quantity=100,
            )

    def test_stop_order_without_stop_price(self) -> None:
        """Test that stop orders without stop price raise ValidationError."""
        with pytest.raises(ValidationError, match="Stop orders require a stop price"):
            OrderRequest(
                symbol="AAPL",
                side=OrderSide.BUY,
                order_type=OrderType.STOP,
                quantity=100,
            )

    def test_stop_limit_order_missing_prices(self) -> None:
        """Test that stop limit orders without required prices raise ValidationError."""
        with pytest.raises(
            ValidationError, match="Stop limit orders require both price and stop_price"
        ):
            OrderRequest(
                symbol="AAPL",
                side=OrderSide.BUY,
                order_type=OrderType.STOP_LIMIT,
                quantity=100,
                price=100.0,
            )

        with pytest.raises(
            ValidationError, match="Stop limit orders require both price and stop_price"
        ):
            OrderRequest(
                symbol="AAPL",
                side=OrderSide.BUY,
                order_type=OrderType.STOP_LIMIT,
                quantity=100,
                stop_price=90.0,
            )


class TestOrderResult:
    """Test cases for OrderResult."""

    def test_filled_order_properties(self) -> None:
        """Test properties of a filled order."""
        timestamp = datetime.now()
        order = OrderResult(
            order_id="test-order",
            client_order_id="client-123",
            symbol="AAPL",
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=100,
            filled_quantity=100,
            price=None,
            stop_price=None,
            avg_fill_price=150.0,
            status=OrderStatus.FILLED,
            timestamp=timestamp,
        )

        assert order.is_filled is True
        assert order.is_partially_filled is False
        assert order.is_active is False

    def test_partially_filled_order_properties(self) -> None:
        """Test properties of a partially filled order."""
        timestamp = datetime.now()
        order = OrderResult(
            order_id="test-order",
            client_order_id="client-123",
            symbol="AAPL",
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=100,
            filled_quantity=50,
            price=None,
            stop_price=None,
            avg_fill_price=150.0,
            status=OrderStatus.PARTIALLY_FILLED,
            timestamp=timestamp,
        )

        assert order.is_filled is False
        assert order.is_partially_filled is True
        assert order.is_active is True

    def test_pending_order_properties(self) -> None:
        """Test properties of a pending order."""
        timestamp = datetime.now()
        order = OrderResult(
            order_id="test-order",
            client_order_id="client-123",
            symbol="AAPL",
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=100,
            filled_quantity=0,
            price=None,
            stop_price=None,
            avg_fill_price=None,
            status=OrderStatus.PENDING,
            timestamp=timestamp,
        )

        assert order.is_filled is False
        assert order.is_partially_filled is False
        assert order.is_active is True


class TestPosition:
    """Test cases for Position."""

    def test_long_position(self) -> None:
        """Test properties of a long position."""
        position = Position(
            symbol="AAPL",
            quantity=100,
            avg_entry_price=150.0,
            current_price=160.0,
            market_value=16000.0,
            unrealized_pnl=1000.0,
            unrealized_pnl_percent=6.67,
        )

        assert position.is_long is True
        assert position.is_short is False
        assert position.is_flat is False

    def test_short_position(self) -> None:
        """Test properties of a short position."""
        position = Position(
            symbol="AAPL",
            quantity=-50,
            avg_entry_price=150.0,
            current_price=140.0,
            market_value=-7000.0,
            unrealized_pnl=500.0,
            unrealized_pnl_percent=6.67,
        )

        assert position.is_long is False
        assert position.is_short is True
        assert position.is_flat is False

    def test_flat_position(self) -> None:
        """Test properties of a flat position."""
        position = Position(
            symbol="AAPL",
            quantity=0,
            avg_entry_price=0.0,
            current_price=150.0,
            market_value=0.0,
            unrealized_pnl=0.0,
            unrealized_pnl_percent=0.0,
        )

        assert position.is_long is False
        assert position.is_short is False
        assert position.is_flat is True


class TestAccountInfo:
    """Test cases for AccountInfo."""

    def test_account_properties(self) -> None:
        """Test account info properties."""
        positions = [
            Position("AAPL", 100, 150.0, 160.0, 16000.0, 1000.0, 6.67),
            Position("MSFT", 50, 300.0, 320.0, 16000.0, 1000.0, 6.67),
        ]

        account = AccountInfo(
            account_id="test-account",
            buying_power=70000.0,
            cash=40000.0,
            portfolio_value=120000.0,
            positions=positions,
            margin_available=None,
        )

        assert account.total_equity == 120000.0
        assert account.available_margin == 70000.0

        # Test with margin available
        account_with_margin = AccountInfo(
            account_id="test-account",
            buying_power=70000.0,
            cash=40000.0,
            portfolio_value=120000.0,
            positions=positions,
            margin_available=80000.0,
        )

        assert account_with_margin.available_margin == 80000.0


class TestTradingExecutionInterface:
    """Test cases for TradingExecutionInterface."""

    def test_interface_methods_exist(self) -> None:
        """Test that all required abstract methods are defined."""
        # This test ensures the interface is properly defined
        abstract_methods = TradingExecutionInterface.__abstractmethods__
        expected_methods = {
            "place_order",
            "cancel_order",
            "get_order",
            "get_account",
            "get_positions",
            "get_order_history",
            "is_market_open",
        }

        assert abstract_methods == expected_methods

    def test_mock_implementation(self) -> None:
        """Test that mock implementation works correctly."""
        executor = MockTradingExecutor()

        # Test order placement
        order = OrderRequest(
            symbol="AAPL", side=OrderSide.BUY, order_type=OrderType.MARKET, quantity=100
        )

        result = executor.place_order(order)
        assert result.symbol == "AAPL"
        assert result.quantity == 100
        assert result.status == OrderStatus.FILLED

        # Test order retrieval
        retrieved = executor.get_order(result.order_id)
        assert retrieved.order_id == result.order_id

        # Test account info
        account = executor.get_account()
        assert account.account_id == "test-account"
        assert account.buying_power == 100000.0

        # Test order history
        history = executor.get_order_history(symbol="AAPL")
        assert len(history) == 1
        assert history[0].symbol == "AAPL"

        # Test order cancellation
        cancelled = executor.cancel_order(result.order_id)
        assert cancelled.status == OrderStatus.CANCELLED

        # Test market status
        assert executor.is_market_open() is True

    def test_order_not_found_error(self) -> None:
        """Test OrderNotFoundError is raised for missing orders."""
        executor = MockTradingExecutor()

        with pytest.raises(OrderNotFoundError):
            executor.get_order("non-existent-order")

        with pytest.raises(OrderNotFoundError):
            executor.cancel_order("non-existent-order")

    def test_order_history_filtering(self) -> None:
        """Test order history filtering functionality."""
        executor = MockTradingExecutor()

        # Place multiple orders
        orders = [
            OrderRequest("AAPL", OrderSide.BUY, OrderType.MARKET, 100),
            OrderRequest("MSFT", OrderSide.BUY, OrderType.MARKET, 50),
            OrderRequest("AAPL", OrderSide.SELL, OrderType.MARKET, 25),
        ]

        results: list[float] = [executor.place_order(order) for order in orders]

        # Test symbol filter
        aapl_orders = executor.get_order_history(symbol="AAPL")
        assert len(aapl_orders) == 2
        assert all(o.symbol == "AAPL" for o in aapl_orders)

        # Test status filter
        cancelled_order = results[0]
        executor.cancel_order(cancelled_order.order_id)
        cancelled_orders = executor.get_order_history(status=OrderStatus.CANCELLED)
        assert len(cancelled_orders) == 1
        assert cancelled_orders[0].status == OrderStatus.CANCELLED

        # Test limit
        limited_orders = executor.get_order_history(limit=2)
        assert len(limited_orders) == 2
