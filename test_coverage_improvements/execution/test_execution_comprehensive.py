"""Comprehensive tests for Execution Tools to improve test coverage."""

import os
import time
import uuid
from datetime import datetime, timedelta
from unittest.mock import MagicMock, Mock, patch, PropertyMock

import pytest

from quantchain.tools.execution import (
    OrderSide,
    OrderType,
    OrderStatus,
    OrderRequest,
    OrderResult,
    AccountInfo,
    Position,
    AlpacaExecutionTool,
)
from quantchain.core.exceptions import (
    InsufficientFundsError,
    OrderNotFoundError,
    ValidationError,
    TradingError,
)


@pytest.mark.unit
class TestOrderSide:
    """Test OrderSide enum."""

    def test_order_side_values(self) -> None:
        """Test that OrderSide has correct values."""
        assert OrderSide.BUY.value == "buy"
        assert OrderSide.SELL.value == "sell"


@pytest.mark.unit
class TestOrderType:
    """Test OrderType enum."""

    def test_order_type_values(self) -> None:
        """Test that OrderType has correct values."""
        assert OrderType.MARKET.value == "market"
        assert OrderType.LIMIT.value == "limit"
        assert OrderType.STOP.value == "stop"
        assert OrderType.STOP_LIMIT.value == "stop_limit"


@pytest.mark.unit
class TestOrderStatus:
    """Test OrderStatus enum."""

    def test_order_status_values(self) -> None:
        """Test that OrderStatus has correct values."""
        assert OrderStatus.NEW.value == "new"
        assert OrderStatus.SUBMITTED.value == "submitted"
        assert OrderStatus.FILLED.value == "filled"
        assert OrderStatus.PARTIALLY_FILLED.value == "partially_filled"
        assert OrderStatus.REJECTED.value == "rejected"
        assert OrderStatus.CANCELLED.value == "cancelled"
        assert OrderStatus.EXPIRED.value == "expired"


@pytest.mark.unit
class TestOrderRequest:
    """Test OrderRequest class."""

    def test_order_request_creation_market(self) -> None:
        """Test creating a market order request."""
        request = OrderRequest(
            symbol="AAPL", side=OrderSide.BUY, order_type=OrderType.MARKET, quantity=100
        )

        assert request.symbol == "AAPL"
        assert request.side == OrderSide.BUY
        assert request.order_type == OrderType.MARKET
        assert request.quantity == 100
        assert request.price is None
        assert request.stop_price is None
        assert request.time_in_force == "GTC"  # Default value
        assert request.client_order_id is not None
        assert isinstance(request.created_at, datetime)

    def test_order_request_creation_limit(self) -> None:
        """Test creating a limit order request."""
        request = OrderRequest(
            symbol="AAPL",
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            quantity=100,
            price=150.0,
        )

        assert request.symbol == "AAPL"
        assert request.side == OrderSide.BUY
        assert request.order_type == OrderType.LIMIT
        assert request.quantity == 100
        assert request.price == 150.0
        assert request.stop_price is None

    def test_order_request_creation_stop(self) -> None:
        """Test creating a stop order request."""
        request = OrderRequest(
            symbol="AAPL",
            side=OrderSide.SELL,
            order_type=OrderType.STOP,
            quantity=100,
            stop_price=140.0,
        )

        assert request.symbol == "AAPL"
        assert request.side == OrderSide.SELL
        assert request.order_type == OrderType.STOP
        assert request.quantity == 100
        assert request.price is None
        assert request.stop_price == 140.0

    def test_order_request_creation_stop_limit(self) -> None:
        """Test creating a stop-limit order request."""
        request = OrderRequest(
            symbol="AAPL",
            side=OrderSide.SELL,
            order_type=OrderType.STOP_LIMIT,
            quantity=100,
            price=145.0,
            stop_price=140.0,
        )

        assert request.symbol == "AAPL"
        assert request.side == OrderSide.SELL
        assert request.order_type == OrderType.STOP_LIMIT
        assert request.quantity == 100
        assert request.price == 145.0
        assert request.stop_price == 140.0

    def test_order_request_custom_client_id(self) -> None:
        """Test creating an order request with custom client ID."""
        client_order_id = "custom_order_123"
        request = OrderRequest(
            symbol="AAPL",
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=100,
            client_order_id=client_order_id,
        )

        assert request.client_order_id == client_order_id

    def test_order_request_custom_time_in_force(self) -> None:
        """Test creating an order request with custom time in force."""
        request = OrderRequest(
            symbol="AAPL",
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=100,
            time_in_force="DAY",
        )

        assert request.time_in_force == "DAY"

    def test_order_request_validation_limit_without_price(self) -> None:
        """Test that limit order without price raises ValidationError."""
        with pytest.raises(ValidationError, match="Price is required for limit order"):
            OrderRequest(
                symbol="AAPL",
                side=OrderSide.BUY,
                order_type=OrderType.LIMIT,
                quantity=100,
            )

    def test_order_request_validation_stop_limit_without_price(self) -> None:
        """Test that stop-limit order without price raises ValidationError."""
        with pytest.raises(ValidationError, match="Price is required for limit order"):
            OrderRequest(
                symbol="AAPL",
                side=OrderSide.BUY,
                order_type=OrderType.STOP_LIMIT,
                quantity=100,
                stop_price=140.0,
            )

    def test_order_request_validation_stop_without_stop_price(self) -> None:
        """Test that stop order without stop price raises ValidationError."""
        with pytest.raises(
            ValidationError, match="Stop price is required for stop order"
        ):
            OrderRequest(
                symbol="AAPL",
                side=OrderSide.SELL,
                order_type=OrderType.STOP,
                quantity=100,
            )

    def test_order_request_validation_stop_limit_without_stop_price(self) -> None:
        """Test that stop-limit order without stop price raises ValidationError."""
        with pytest.raises(
            ValidationError, match="Stop price is required for stop order"
        ):
            OrderRequest(
                symbol="AAPL",
                side=OrderSide.SELL,
                order_type=OrderType.STOP_LIMIT,
                quantity=100,
                price=145.0,
            )


@pytest.mark.unit
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
            quantity=100,
            filled_quantity=100,
            price=150.0,
            average_price=150.5,
            status=OrderStatus.FILLED,
            timestamp=timestamp,
        )

        assert result.order_id == "order_123"
        assert result.symbol == "AAPL"
        assert result.side == OrderSide.BUY
        assert result.order_type == OrderType.MARKET
        assert result.quantity == 100
        assert result.filled_quantity == 100
        assert result.price == 150.0
        assert result.average_price == 150.5
        assert result.status == OrderStatus.FILLED
        assert result.timestamp == timestamp
        assert result.error_message is None

    def test_order_result_with_error(self) -> None:
        """Test creating an order result with error."""
        timestamp = datetime.now()
        result = OrderResult(
            order_id="order_123",
            symbol="AAPL",
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=100,
            filled_quantity=0,
            price=None,
            average_price=None,
            status=OrderStatus.REJECTED,
            timestamp=timestamp,
            error_message="Insufficient funds",
        )

        assert result.error_message == "Insufficient funds"
        assert result.status == OrderStatus.REJECTED
        assert result.filled_quantity == 0

    def test_order_result_partial_fill(self) -> None:
        """Test creating an order result with partial fill."""
        timestamp = datetime.now()
        result = OrderResult(
            order_id="order_123",
            symbol="AAPL",
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            quantity=100,
            filled_quantity=50,
            price=150.0,
            average_price=150.1,
            status=OrderStatus.PARTIALLY_FILLED,
            timestamp=timestamp,
        )

        assert result.quantity == 100
        assert result.filled_quantity == 50
        assert result.status == OrderStatus.PARTIALLY_FILLED


@pytest.mark.unit
class TestAccountInfo:
    """Test AccountInfo class."""

    def test_account_info_creation(self) -> None:
        """Test creating account information."""
        account = AccountInfo(
            account_id="account_123",
            buying_power=50000.0,
            cash=25000.0,
            portfolio_value=75000.0,
            day_trading_profit_loss=1500.0,
            maintenance_margin=7500.0,
            day_trades_count=5,
            leverage=2.0,
        )

        assert account.account_id == "account_123"
        assert account.buying_power == 50000.0
        assert account.cash == 25000.0
        assert account.portfolio_value == 75000.0
        assert account.day_trading_profit_loss == 1500.0
        assert account.maintenance_margin == 7500.0
        assert account.day_trades_count == 5
        assert account.leverage == 2.0


@pytest.mark.unit
class TestPosition:
    """Test Position class."""

    def test_position_creation_long(self) -> None:
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

    def test_position_creation_short(self) -> None:
        """Test creating a short position."""
        position = Position(
            symbol="AAPL",
            quantity=-100,
            side=OrderSide.SELL,
            market_value=-15000.0,
            cost_basis=-14000.0,
            unrealized_pl=-1000.0,
            unrealized_pl_pct=-7.14,
        )

        assert position.symbol == "AAPL"
        assert position.quantity == -100
        assert position.side == OrderSide.SELL
        assert position.market_value == -15000.0
        assert position.cost_basis == -14000.0
        assert position.unrealized_pl == -1000.0
        assert position.unrealized_pl_pct == -7.14

    def test_position_zero_quantity(self) -> None:
        """Test creating a position with zero quantity (closed position)."""
        position = Position(
            symbol="AAPL",
            quantity=0,
            side=OrderSide.BUY,
            market_value=0.0,
            cost_basis=0.0,
            unrealized_pl=0.0,
            unrealized_pl_pct=0.0,
        )

        assert position.quantity == 0
        assert position.market_value == 0.0
        assert position.unrealized_pl == 0.0


@pytest.mark.unit
class TestAlpacaExecutionTool:
    """Test AlpacaExecutionTool class."""

    @pytest.fixture
    def tool(self) -> AlpacaExecutionTool:
        """Create a test execution tool instance."""
        return AlpacaExecutionTool(
            api_key="test_key", api_secret="test_secret", paper=True
        )

    def test_initialization_default(self) -> None:
        """Test default initialization."""
        tool = AlpacaExecutionTool()

        assert tool.api_key is None
        assert tool.api_secret is None
        assert tool.paper is True
        assert tool.base_url == "https://paper-api.alpaca.markets"
        assert tool.config == {}
        assert tool.retry_count == 3
        assert tool.retry_delay == 1.0
        assert tool._orders == {}
        assert tool._positions == {}

    def test_initialization_custom(self) -> None:
        """Test custom initialization."""
        config = {"test": "config"}
        tool = AlpacaExecutionTool(
            api_key="custom_key",
            api_secret="custom_secret",
            base_url="https://custom.api.com",
            paper=False,
            config=config,
            retry_count=5,
            retry_delay=2.0,
        )

        assert tool.api_key == "custom_key"
        assert tool.api_secret == "custom_secret"
        assert tool.base_url == "https://custom.api.com"
        assert tool.paper is False
        assert tool.config == config
        assert tool.retry_count == 5
        assert tool.retry_delay == 2.0

    def test_initialization_paper_url(self) -> None:
        """Test paper URL is set correctly."""
        tool = AlpacaExecutionTool(paper=True)
        assert tool.base_url == "https://paper-api.alpaca.markets"

        tool = AlpacaExecutionTool(paper=False)
        assert tool.base_url == "https://api.alpaca.markets"

    def test_from_credentials(self) -> None:
        """Test creating tool from credentials."""
        tool = AlpacaExecutionTool.from_credentials(
            api_key="cred_key", api_secret="cred_secret", paper=False
        )

        assert tool.api_key == "cred_key"
        assert tool.api_secret == "cred_secret"
        assert tool.paper is False
        assert tool.base_url == "https://api.alpaca.markets"

    def test_from_credentials_default_paper(self) -> None:
        """Test creating tool from credentials with default paper trading."""
        tool = AlpacaExecutionTool.from_credentials(
            api_key="cred_key", api_secret="cred_secret"
        )

        assert tool.api_key == "cred_key"
        assert tool.api_secret == "cred_secret"
        assert tool.paper is True
        assert tool.base_url == "https://paper-api.alpaca.markets"

    def test_execute_market_order_buy(self, tool: AlpacaExecutionTool) -> None:
        """Test executing a buy market order."""
        result = tool.execute_market_order("AAPL", "buy", 100)

        assert result["symbol"] == "AAPL"
        assert result["side"] == "buy"
        assert result["qty"] == "100"
        assert result["type"] == "market"
        assert result["status"] == OrderStatus.FILLED.value
        assert "filled_avg_price" in result
        assert "client_order_id" in result
        assert "created_at" in result

        # Check position was created
        assert "AAPL" in tool._positions
        position = tool._positions["AAPL"]
        assert position.quantity == 100
        assert position.side == OrderSide.BUY

    def test_execute_market_order_sell(self, tool: AlpacaExecutionTool) -> None:
        """Test executing a sell market order with existing position."""
        # First create a position
        tool._positions["AAPL"] = Position(
            symbol="AAPL",
            quantity=200,
            side=OrderSide.BUY,
            market_value=30000.0,
            cost_basis=28000.0,
            unrealized_pl=2000.0,
            unrealized_pl_pct=7.14,
        )

        result = tool.execute_market_order("AAPL", "sell", 50)

        assert result["symbol"] == "AAPL"
        assert result["side"] == "sell"
        assert result["qty"] == "50"
        assert result["status"] == OrderStatus.FILLED.value

        # Check position was updated
        position = tool._positions["AAPL"]
        assert position.quantity == 150  # 200 - 50

    def test_execute_market_order_sell_insufficient_position(
        self, tool: AlpacaExecutionTool
    ) -> None:
        """Test executing a sell order without sufficient position."""
        # Create a smaller position
        tool._positions["AAPL"] = Position(
            symbol="AAPL",
            quantity=25,
            side=OrderSide.BUY,
            market_value=3750.0,
            cost_basis=3500.0,
            unrealized_pl=250.0,
            unrealized_pl_pct=7.14,
        )

        with pytest.raises(InsufficientFundsError, match="No position for AAPL"):
            tool.execute_market_order("AAPL", "sell", 50)

    def test_execute_market_order_sell_no_position(
        self, tool: AlpacaExecutionTool
    ) -> None:
        """Test executing a sell order without any position."""
        with pytest.raises(InsufficientFundsError, match="No position for AAPL"):
            tool.execute_market_order("AAPL", "sell", 50)

    def test_execute_market_order_case_insensitivity(
        self, tool: AlpacaExecutionTool
    ) -> None:
        """Test that side is case insensitive."""
        # Test uppercase
        result_buy = tool.execute_market_order("AAPL", "BUY", 100)
        assert result_buy["side"] == "buy"

        # Test lowercase
        result_sell = tool.execute_market_order("AAPL", "sell", 100)
        assert result_sell["side"] == "sell"

    def test_execute_market_order_invalid_side(self, tool: AlpacaExecutionTool) -> None:
        """Test executing a market order with invalid side."""
        # Create a position first to allow selling
        tool._positions["AAPL"] = Position(
            symbol="AAPL",
            quantity=200,
            side=OrderSide.BUY,
            market_value=30000.0,
            cost_basis=28000.0,
            unrealized_pl=2000.0,
            unrealized_pl_pct=7.14,
        )

        # This will default to sell due to else branch
        result = tool.execute_market_order("AAPL", "invalid", 100)
        assert result["side"] == "sell"

    def test_execute_market_order_custom_time_in_force(
        self, tool: AlpacaExecutionTool
    ) -> None:
        """Test executing a market order with custom time in force."""
        result = tool.execute_market_order("AAPL", "buy", 100, time_in_force="IOC")

        # Check that time_in_force was passed through
        order_id = result["client_order_id"]
        # Access the stored order request
        stored_request = tool._orders.get(order_id)
        assert stored_request.time_in_force == "IOC"

    def test_place_order_market(self, tool: AlpacaExecutionTool) -> None:
        """Test placing a market order."""
        order_request = OrderRequest(
            symbol="AAPL", side=OrderSide.BUY, order_type=OrderType.MARKET, quantity=100
        )

        result = tool.place_order(order_request)

        assert result.symbol == "AAPL"
        assert result.side == OrderSide.BUY
        assert result.order_type == OrderType.MARKET
        assert result.quantity == 100
        assert result.filled_quantity == 100
        assert result.status == OrderStatus.FILLED
        assert result.price is not None
        assert result.average_price is not None
        assert isinstance(result.order_id, str)
        assert isinstance(result.timestamp, datetime)

        # Check that order was stored
        assert order_request.client_order_id in tool._orders
        assert tool._orders[order_request.client_order_id] == result

    def test_place_order_limit(self, tool: AlpacaExecutionTool) -> None:
        """Test placing a limit order."""
        order_request = OrderRequest(
            symbol="AAPL",
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            quantity=100,
            price=150.0,
        )

        result = tool.place_order(order_request)

        assert result.symbol == "AAPL"
        assert result.side == OrderSide.BUY
        assert result.order_type == OrderType.LIMIT
        assert result.quantity == 100
        assert result.filled_quantity == 0  # Not filled for limit order
        assert result.status == OrderStatus.SUBMITTED
        assert result.price == 150.0
        assert result.average_price is None

        # Check that order was stored
        assert order_request.client_order_id in tool._orders
        assert tool._orders[order_request.client_order_id] == result

    def test_place_order_stop(self, tool: AlpacaExecutionTool) -> None:
        """Test placing a stop order."""
        order_request = OrderRequest(
            symbol="AAPL",
            side=OrderSide.SELL,
            order_type=OrderType.STOP,
            quantity=100,
            stop_price=140.0,
        )

        result = tool.place_order(order_request)

        assert result.symbol == "AAPL"
        assert result.side == OrderSide.SELL
        assert result.order_type == OrderType.STOP
        assert result.quantity == 100
        assert result.filled_quantity == 0  # Not filled for stop order
        assert result.status == OrderStatus.SUBMITTED
        assert result.price is None
        assert result.stop_price == 140.0  # This is stored in the request, not result

    def test_place_order_stop_limit(self, tool: AlpacaExecutionTool) -> None:
        """Test placing a stop-limit order."""
        order_request = OrderRequest(
            symbol="AAPL",
            side=OrderSide.SELL,
            order_type=OrderType.STOP_LIMIT,
            quantity=100,
            price=145.0,
            stop_price=140.0,
        )

        result = tool.place_order(order_request)

        assert result.symbol == "AAPL"
        assert result.side == OrderSide.SELL
        assert result.order_type == OrderType.STOP_LIMIT
        assert result.quantity == 100
        assert result.filled_quantity == 0  # Not filled for stop-limit order
        assert result.status == OrderStatus.SUBMITTED
        assert result.price == 145.0

    def test_place_order_add_to_existing_position(
        self, tool: AlpacaExecutionTool
    ) -> None:
        """Test placing an order that adds to an existing position."""
        # Create an existing position
        tool._positions["AAPL"] = Position(
            symbol="AAPL",
            quantity=100,
            side=OrderSide.BUY,
            market_value=15000.0,
            cost_basis=14000.0,
            unrealized_pl=1000.0,
            unrealized_pl_pct=7.14,
        )

        order_request = OrderRequest(
            symbol="AAPL", side=OrderSide.BUY, order_type=OrderType.MARKET, quantity=50
        )

        result = tool.place_order(order_request)

        assert result.status == OrderStatus.FILLED
        assert result.filled_quantity == 50

        # Check position was updated
        position = tool._positions["AAPL"]
        assert position.quantity == 150  # 100 + 50
        assert position.cost_basis > 14000.0  # Should have increased

    def test_place_order_close_position(self, tool: AlpacaExecutionTool) -> None:
        """Test placing an order that closes a position."""
        # Create an existing position
        tool._positions["AAPL"] = Position(
            symbol="AAPL",
            quantity=100,
            side=OrderSide.BUY,
            market_value=15000.0,
            cost_basis=14000.0,
            unrealized_pl=1000.0,
            unrealized_pl_pct=7.14,
        )

        order_request = OrderRequest(
            symbol="AAPL",
            side=OrderSide.SELL,
            order_type=OrderType.MARKET,
            quantity=100,
        )

        result = tool.place_order(order_request)

        assert result.status == OrderStatus.FILLED
        assert result.filled_quantity == 100

        # Check position was updated
        position = tool._positions["AAPL"]
        assert position.quantity == 0  # 100 - 100

    def test_cancel_order_success(self, tool: AlpacaExecutionTool) -> None:
        """Test successfully cancelling an order."""
        # First place an order
        order_request = OrderRequest(
            symbol="AAPL",
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            quantity=100,
            price=150.0,
        )

        order_result = tool.place_order(order_request)

        # Now cancel it
        result = tool.cancel_order(order_result.order_id)

        assert result is True

        # Check that order status was updated
        updated_order = tool.get_order_status(order_result.order_id)
        assert updated_order.status == OrderStatus.CANCELLED

    def test_cancel_order_not_found(self, tool: AlpacaExecutionTool) -> None:
        """Test cancelling an order that doesn't exist."""
        with pytest.raises(OrderNotFoundError, match="Order non_existent not found"):
            tool.cancel_order("non_existent")

    def test_cancel_order_already_filled(self, tool: AlpacaExecutionTool) -> None:
        """Test cancelling an order that is already filled."""
        # First place a market order (will be filled)
        order_request = OrderRequest(
            symbol="AAPL", side=OrderSide.BUY, order_type=OrderType.MARKET, quantity=100
        )

        order_result = tool.place_order(order_request)

        # Now try to cancel it
        with pytest.raises(TradingError, match="Cannot cancel filled order"):
            tool.cancel_order(order_result.order_id)

    def test_get_order_status_success(self, tool: AlpacaExecutionTool) -> None:
        """Test getting order status for an existing order."""
        # First place an order
        order_request = OrderRequest(
            symbol="AAPL",
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            quantity=100,
            price=150.0,
        )

        order_result = tool.place_order(order_request)

        # Get status
        status = tool.get_order_status(order_result.order_id)

        assert status.order_id == order_result.order_id
        assert status.symbol == "AAPL"
        assert status.side == OrderSide.BUY
        assert status.order_type == OrderType.LIMIT
        assert status.quantity == 100
        assert status.status == OrderStatus.SUBMITTED

    def test_get_order_status_not_found(self, tool: AlpacaExecutionTool) -> None:
        """Test getting order status for a non-existent order."""
        with pytest.raises(OrderNotFoundError, match="Order non_existent not found"):
            tool.get_order_status("non_existent")

    def test_get_positions(self, tool: AlpacaExecutionTool) -> None:
        """Test getting all positions."""
        # Create some positions
        tool._positions["AAPL"] = Position(
            symbol="AAPL",
            quantity=100,
            side=OrderSide.BUY,
            market_value=15000.0,
            cost_basis=14000.0,
            unrealized_pl=1000.0,
            unrealized_pl_pct=7.14,
        )

        tool._positions["MSFT"] = Position(
            symbol="MSFT",
            quantity=50,
            side=OrderSide.BUY,
            market_value=10000.0,
            cost_basis=9500.0,
            unrealized_pl=500.0,
            unrealized_pl_pct=5.26,
        )

        positions = tool.get_positions()

        assert len(positions) == 2

        symbols = [pos.symbol for pos in positions]
        assert "AAPL" in symbols
        assert "MSFT" in symbols

        # Check that we get the actual position objects
        aapl_pos = next(pos for pos in positions if pos.symbol == "AAPL")
        assert aapl_pos.quantity == 100

    def test_get_positions_empty(self, tool: AlpacaExecutionTool) -> None:
        """Test getting positions when there are none."""
        positions = tool.get_positions()
        assert positions == []

    def test_get_position(self, tool: AlpacaExecutionTool) -> None:
        """Test getting a specific position."""
        # Create a position
        tool._positions["AAPL"] = Position(
            symbol="AAPL",
            quantity=100,
            side=OrderSide.BUY,
            market_value=15000.0,
            cost_basis=14000.0,
            unrealized_pl=1000.0,
            unrealized_pl_pct=7.14,
        )

        position = tool.get_position("AAPL")

        assert position is not None
        assert position.symbol == "AAPL"
        assert position.quantity == 100

    def test_get_position_not_found(self, tool: AlpacaExecutionTool) -> None:
        """Test getting a position that doesn't exist."""
        position = tool.get_position("NON_EXISTENT")
        assert position is None

    def test_get_account_info(self, tool: AlpacaExecutionTool) -> None:
        """Test getting account information."""
        # Create some positions
        tool._positions["AAPL"] = Position(
            symbol="AAPL",
            quantity=100,
            side=OrderSide.BUY,
            market_value=15000.0,
            cost_basis=14000.0,
            unrealized_pl=1000.0,
            unrealized_pl_pct=7.14,
        )

        tool._positions["MSFT"] = Position(
            symbol="MSFT",
            quantity=50,
            side=OrderSide.BUY,
            market_value=10000.0,
            cost_basis=9500.0,
            unrealized_pl=500.0,
            unrealized_pl_pct=5.26,
        )

        # Create some orders
        tool._orders["order_1"] = OrderResult(
            order_id="order_1",
            symbol="AAPL",
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=100,
            filled_quantity=100,
            price=150.0,
            average_price=150.0,
            status=OrderStatus.FILLED,
            timestamp=datetime.now(),
        )

        account_info = tool.get_account_info()

        assert account_info.account_id == "mock_account"
        assert account_info.buying_power == 50000.0  # 2 * portfolio_value
        assert account_info.cash == 12500.0  # 0.5 * portfolio_value
        assert account_info.portfolio_value == 25000.0  # Sum of market values
        assert account_info.day_trading_profit_loss == 1500.0  # Sum of unrealized_pl
        assert account_info.maintenance_margin == 2500.0  # 0.1 * portfolio_value
        assert account_info.day_trades_count == 1
        assert account_info.leverage == 2.0

    def test_get_account_info_empty(self, tool: AlpacaExecutionTool) -> None:
        """Test getting account information with no positions."""
        account_info = tool.get_account_info()

        assert account_info.account_id == "mock_account"
        assert account_info.buying_power == 0.0  # 2 * 0
        assert account_info.cash == 0.0  # 0.5 * 0
        assert account_info.portfolio_value == 0.0
        assert account_info.day_trading_profit_loss == 0.0
        assert account_info.maintenance_margin == 0.0
        assert account_info.day_trades_count == 0
        assert account_info.leverage == 2.0

    def test_get_order_history(self, tool: AlpacaExecutionTool) -> None:
        """Test getting order history."""
        # Create some orders with different timestamps
        now = datetime.now()
        earlier = now - timedelta(hours=1)
        even_earlier = now - timedelta(hours=2)

        order1 = OrderResult(
            order_id="order_1",
            symbol="AAPL",
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=100,
            filled_quantity=100,
            price=150.0,
            average_price=150.0,
            status=OrderStatus.FILLED,
            timestamp=now,
        )

        order2 = OrderResult(
            order_id="order_2",
            symbol="MSFT",
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            quantity=50,
            filled_quantity=0,
            price=200.0,
            average_price=None,
            status=OrderStatus.SUBMITTED,
            timestamp=earlier,
        )

        order3 = OrderResult(
            order_id="order_3",
            symbol="AAPL",
            side=OrderSide.SELL,
            order_type=OrderType.STOP,
            quantity=25,
            filled_quantity=0,
            price=140.0,  # Stop order requires price parameter
            stop_price=140.0,
            average_price=None,
            status=OrderStatus.CANCELLED,
            timestamp=even_earlier,
        )

        # Store orders using client_order_id as key
        tool._orders["client_1"] = order1
        tool._orders["client_2"] = order2
        tool._orders["client_3"] = order3

        # Get all orders
        all_orders = tool.get_order_history()

        assert len(all_orders) == 3

        # Check they are sorted by timestamp (newest first)
        assert all_orders[0].order_id == "order_1"  # Most recent
        assert all_orders[1].order_id == "order_2"
        assert all_orders[2].order_id == "order_3"  # Oldest

    def test_get_order_history_with_symbol_filter(
        self, tool: AlpacaExecutionTool
    ) -> None:
        """Test getting order history with symbol filter."""
        # Create some orders
        order1 = OrderResult(
            order_id="order_1",
            symbol="AAPL",
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=100,
            filled_quantity=100,
            price=150.0,
            average_price=150.0,
            status=OrderStatus.FILLED,
            timestamp=datetime.now(),
        )

        order2 = OrderResult(
            order_id="order_2",
            symbol="MSFT",
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            quantity=50,
            filled_quantity=0,
            price=200.0,
            average_price=None,
            status=OrderStatus.SUBMITTED,
            timestamp=datetime.now(),
        )

        order3 = OrderResult(
            order_id="order_3",
            symbol="AAPL",
            side=OrderSide.SELL,
            order_type=OrderType.STOP,
            quantity=25,
            filled_quantity=0,
            price=None,
            average_price=None,
            status=OrderStatus.CANCELLED,
            timestamp=datetime.now(),
        )

        # Store orders
        tool._orders["client_1"] = order1
        tool._orders["client_2"] = order2
        tool._orders["client_3"] = order3

        # Get orders for AAPL only
        aapl_orders = tool.get_order_history(symbol="AAPL")

        assert len(aapl_orders) == 2
        assert all(order.symbol == "AAPL" for order in aapl_orders)

    def test_get_order_history_with_limit(self, tool: AlpacaExecutionTool) -> None:
        """Test getting order history with limit."""
        # Create some orders
        for i in range(10):
            order = OrderResult(
                order_id=f"order_{i}",
                symbol="AAPL",
                side=OrderSide.BUY,
                order_type=OrderType.MARKET,
                quantity=100,
                filled_quantity=100,
                price=150.0,
                average_price=150.0,
                status=OrderStatus.FILLED,
                timestamp=datetime.now() - timedelta(minutes=i),
            )

            tool._orders[f"client_{i}"] = order

        # Get only 5 orders
        limited_orders = tool.get_order_history(limit=5)

        assert len(limited_orders) == 5

    def test_get_order_history_empty(self, tool: AlpacaExecutionTool) -> None:
        """Test getting order history when there are no orders."""
        orders = tool.get_order_history()
        assert orders == []

    def test_get_account_balance(self, tool: AlpacaExecutionTool) -> None:
        """Test getting account balance."""
        # Create some positions
        tool._positions["AAPL"] = Position(
            symbol="AAPL",
            quantity=100,
            side=OrderSide.BUY,
            market_value=15000.0,
            cost_basis=14000.0,
            unrealized_pl=1000.0,
            unrealized_pl_pct=7.14,
        )

        balance = tool.get_account_balance()

        assert balance["portfolio_value"] == 15000.0
        assert balance["cash"] == 7500.0  # 0.5 * portfolio_value
        assert balance["buying_power"] == 30000.0  # 2 * portfolio_value

    def test_get_account_balance_empty(self, tool: AlpacaExecutionTool) -> None:
        """Test getting account balance with no positions."""
        balance = tool.get_account_balance()

        assert balance["portfolio_value"] == 0.0
        assert balance["cash"] == 0.0
        assert balance["buying_power"] == 0.0

    @patch.dict(
        os.environ, {"ALPACA_API_KEY": "env_key", "ALPACA_API_SECRET": "env_secret"}
    )
    def test_initialization_from_environment(self) -> None:
        """Test initialization from environment variables."""
        # Remove the tools from the test scope so it uses the real one
        tool = AlpacaExecutionTool()

        assert tool.api_key == "env_key"
        assert tool.api_secret == "env_secret"

    def test_mock_price_generation(self, tool: AlpacaExecutionTool) -> None:
        """Test that mock prices are generated consistently for the same symbol."""
        # Place orders for the same symbol multiple times
        order1 = OrderRequest(
            symbol="AAPL", side=OrderSide.BUY, order_type=OrderType.MARKET, quantity=100
        )

        order2 = OrderRequest(
            symbol="AAPL", side=OrderSide.BUY, order_type=OrderType.MARKET, quantity=100
        )

        result1 = tool.place_order(order1)
        result2 = tool.place_order(order2)

        # Prices should be the same for the same symbol
        assert result1.average_price == result2.average_price

        # But different for different symbols
        order3 = OrderRequest(
            symbol="MSFT", side=OrderSide.BUY, order_type=OrderType.MARKET, quantity=100
        )

        result3 = tool.place_order(order3)
        assert result1.average_price != result3.average_price

    def test_position_updates_after_buy(self, tool: AlpacaExecutionTool) -> None:
        """Test that positions are correctly updated after a buy."""
        # Place a buy order
        order = OrderRequest(
            symbol="AAPL", side=OrderSide.BUY, order_type=OrderType.MARKET, quantity=100
        )

        result = tool.place_order(order)

        # Check position was created
        position = tool._positions["AAPL"]
        assert position.quantity == 100
        assert position.side == OrderSide.BUY
        assert position.market_value == 100 * result.average_price
        assert position.cost_basis == 100 * result.average_price
        assert position.unrealized_pl == 0.0  # Just created, so no P&L
        assert position.unrealized_pl_pct == 0.0

    def test_position_updates_after_sell_exact_quantity(
        self, tool: AlpacaExecutionTool
    ) -> None:
        """Test that positions are correctly updated after a sell of exact quantity."""
        # First create a position
        tool._positions["AAPL"] = Position(
            symbol="AAPL",
            quantity=100,
            side=OrderSide.BUY,
            market_value=15000.0,
            cost_basis=14000.0,
            unrealized_pl=1000.0,
            unrealized_pl_pct=7.14,
        )

        # Sell the exact quantity
        order = OrderRequest(
            symbol="AAPL",
            side=OrderSide.SELL,
            order_type=OrderType.MARKET,
            quantity=100,
        )

        result = tool.place_order(order)

        # Check position was closed
        position = tool._positions["AAPL"]
        assert position.quantity == 0

    def test_position_updates_after_sell_partial_quantity(
        self, tool: AlpacaExecutionTool
    ) -> None:
        """Test that positions are correctly updated after a partial sell."""
        # First create a position
        tool._positions["AAPL"] = Position(
            symbol="AAPL",
            quantity=100,
            side=OrderSide.BUY,
            market_value=15000.0,
            cost_basis=14000.0,
            unrealized_pl=1000.0,
            unrealized_pl_pct=7.14,
        )

        # Sell part of the position
        order = OrderRequest(
            symbol="AAPL", side=OrderSide.SELL, order_type=OrderType.MARKET, quantity=50
        )

        result = tool.place_order(order)

        # Check position was reduced
        position = tool._positions["AAPL"]
        assert position.quantity == 50  # 100 - 50
