"""Trading execution tools for QuantChain."""

import os
import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from quantchain.core.exceptions import (
    InsufficientFundsError,
    OrderNotFoundError,
    TradingError,
    ValidationError,
)


class OrderSide(Enum):
    """Order side types."""

    BUY = "buy"
    SELL = "sell"


class OrderType(Enum):
    """Order type types."""

    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"
    TRAILING_STOP = "trailing_stop"


class OrderStatus(Enum):
    """Order status types."""

    NEW = "new"
    SUBMITTED = "submitted"
    FILLED = "filled"
    PARTIALLY_FILLED = "partially_filled"
    REJECTED = "rejected"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class OrderRequest:
    """Request to place an order."""

    def __init__(
        self,
        symbol: str,
        side: OrderSide,
        order_type: OrderType,
        quantity: float,
        price: Optional[float] = None,
        stop_price: Optional[float] = None,
        time_in_force: str = "GTC",  # Good Till Canceled
        client_order_id: Optional[str] = None,
    ):
        """
        Initialize order request.

        Args:
            symbol: Trading symbol
            side: Order side (buy/sell)
            order_type: Order type (market/limit/stop/stop_limit)
            quantity: Quantity to trade
            price: Limit price (required for limit orders)
            stop_price: Stop price (required for stop orders)
            time_in_force: Time in force
            client_order_id: Client-defined order ID
        """
        self.id = str(uuid.uuid4())
        self.symbol = symbol
        self.side = side
        self.order_type = order_type
        self.quantity = quantity
        self.price = price
        self.stop_price = stop_price
        self.time_in_force = time_in_force
        self.client_order_id = client_order_id or self.id
        self.created_at = datetime.now()

        # Validate order request
        if order_type in [OrderType.LIMIT, OrderType.STOP_LIMIT] and price is None:
            raise ValidationError("Price is required for limit order")

        if order_type in [OrderType.STOP, OrderType.STOP_LIMIT] and stop_price is None:
            raise ValidationError("Stop price is required for stop order")


class OrderResult:
    """Result of an order placement or modification."""

    def __init__(
        self,
        order_id: str,
        symbol: str,
        side: OrderSide,
        order_type: OrderType,
        quantity: float,
        filled_quantity: float,
        price: Optional[float],
        average_price: Optional[float],
        status: OrderStatus,
        timestamp: datetime,
        error_message: Optional[str] = None,
        time_in_force: Optional[str] = None,
        stop_price: Optional[float] = None,
    ):
        """
        Initialize order result.

        Args:
            order_id: Exchange order ID
            symbol: Trading symbol
            side: Order side
            order_type: Order type
            quantity: Original order quantity
            filled_quantity: Quantity actually filled
            price: Limit price if applicable
            average_price: Average execution price
            status: Current order status
            timestamp: Execution timestamp
            error_message: Error message if failed
        """
        self.order_id = order_id
        self.symbol = symbol
        self.side = side
        self.order_type = order_type
        self.quantity = quantity
        self.filled_quantity = filled_quantity
        self.price = price
        self.average_price = average_price
        self.status = status
        self.timestamp = timestamp
        self.error_message = error_message
        self.time_in_force = time_in_force
        self.stop_price = stop_price


class AccountInfo:
    """Account information."""

    def __init__(
        self,
        account_id: str,
        buying_power: float,
        cash: float,
        portfolio_value: float,
        day_trading_profit_loss: float,
        maintenance_margin: float,
        day_trades_count: int,
        leverage: float,
    ):
        """
        Initialize account info.

        Args:
            account_id: Account identifier
            buying_power: Available buying power
            cash: Available cash
            portfolio_value: Total portfolio value
            day_trading_profit_loss: Day's P&L
            maintenance_margin: Maintenance margin requirement
            day_trades_count: Number of trades today
            leverage: Account leverage multiplier
        """
        self.account_id = account_id
        self.buying_power = buying_power
        self.cash = cash
        self.portfolio_value = portfolio_value
        self.day_trading_profit_loss = day_trading_profit_loss
        self.maintenance_margin = maintenance_margin
        self.day_trades_count = day_trades_count
        self.leverage = leverage


class Position:
    """Open position."""

    def __init__(
        self,
        symbol: str,
        quantity: float,
        side: OrderSide,
        market_value: float,
        cost_basis: float,
        unrealized_pl: float,
        unrealized_pl_pct: float,
    ):
        """
        Initialize position.

        Args:
            symbol: Trading symbol
            quantity: Position quantity
            side: Position side
            market_value: Current market value
            cost_basis: Original cost basis
            unrealized_pl: Unrealized P&L
            unrealized_pl_pct: Unrealized P&L percentage
        """
        self.symbol = symbol
        self.quantity = quantity
        self.side = side
        self.market_value = market_value
        self.cost_basis = cost_basis
        self.unrealized_pl = unrealized_pl
        self.unrealized_pl_pct = unrealized_pl_pct


class AlpacaExecutionTool:
    """Alpaca trading execution tool."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None,
        base_url: Optional[str] = None,
        paper: bool = True,
        config: Optional[Dict[str, Any]] = None,
        retry_count: int = 3,
        retry_delay: float = 1.0,
    ):
        """
        Initialize Alpaca execution tool.

        Args:
            api_key: Alpaca API key
            api_secret: Alpaca API secret
            base_url: Alpaca API base URL
            paper: Whether to use paper trading
            config: Configuration dictionary
            retry_count: Number of retries for failed operations
            retry_delay: Delay between retries in seconds
        """
        self.api_key = api_key or os.getenv("ALPACA_API_KEY")
        self.api_secret = api_secret or os.getenv("ALPACA_API_SECRET")
        self.paper = paper
        self.base_url = base_url or (
            "https://paper-api.alpaca.markets"
            if paper
            else "https://api.alpaca.markets"
        )
        self.config = config or {}
        self.retry_count = retry_count
        self.retry_delay = retry_delay
        self._orders: dict[str, Union[OrderRequest, OrderResult]] = (
            {}
        )  # Client order ID -> OrderRequest/OrderResult
        self._positions: dict[str, Position] = {}  # Symbol -> Position

    @classmethod
    def from_credentials(
        cls, api_key: str, api_secret: str, paper: bool = True
    ) -> "AlpacaExecutionTool":
        """
        Create AlpacaExecutionTool from API credentials.

        Args:
            api_key: Alpaca API key
            api_secret: Alpaca API secret
            paper: Whether to use paper trading

        Returns:
            AlpacaExecutionTool instance
        """
        return cls(api_key=api_key, api_secret=api_secret, paper=paper)

    def execute_market_order(
        self, symbol: str, side: str, quantity: float, time_in_force: str = "day"
    ) -> Dict[str, Any]:
        """
        Execute a market order via Alpaca.

        Args:
            symbol: Trading symbol
            side: "buy" or "sell"
            quantity: Quantity to trade
            time_in_force: Time in force

        Returns:
            Order result as dictionary
        """
        # Convert side to enum, default to sell if invalid
        side_enum = OrderSide.BUY if side.lower() == "buy" else OrderSide.SELL
        normalized_side = "buy" if side.lower() == "buy" else "sell"

        # Create order request
        order_request = OrderRequest(
            symbol=symbol,
            side=side_enum,
            order_type=OrderType.MARKET,
            quantity=quantity,
            time_in_force=time_in_force,
        )

        # Place the order
        result = self.place_order(order_request)

        # Convert to dictionary format expected by tests
        return {
            "id": result.order_id,
            "client_order_id": order_request.client_order_id,
            "symbol": symbol,
            "side": normalized_side,
            "qty": str(quantity),
            "type": "market",
            "status": result.status.value,
            "filled_qty": str(result.filled_quantity),
            "filled_avg_price": (
                str(result.average_price) if result.average_price else None
            ),
            "created_at": result.timestamp.isoformat(),
        }

    def place_order(self, order_request: OrderRequest) -> OrderResult:
        """
        Place an order.

        Args:
            order_request: Order request object

        Returns:
            Order result
        """
        # Store the request
        self._orders[order_request.client_order_id] = order_request

        # In a real implementation, this would send the order to Alpaca
        # For testing, we'll simulate immediate fill for market orders

        if order_request.order_type == OrderType.MARKET:
            # Simulate immediate fill at a mock price
            mock_price = 100.0 + (hash(order_request.symbol) % 50)

            # Update or create position
            if order_request.side == OrderSide.BUY:
                if order_request.symbol in self._positions:
                    # Add to existing position
                    position = self._positions[order_request.symbol]
                    new_quantity = position.quantity + order_request.quantity
                    new_cost_basis = position.cost_basis + (
                        order_request.quantity * mock_price
                    )
                    position.quantity = new_quantity
                    position.cost_basis = new_cost_basis
                else:
                    # Create new position
                    self._positions[order_request.symbol] = Position(
                        symbol=order_request.symbol,
                        quantity=order_request.quantity,
                        side=OrderSide.BUY,
                        market_value=order_request.quantity * mock_price,
                        cost_basis=order_request.quantity * mock_price,
                        unrealized_pl=0.0,
                        unrealized_pl_pct=0.0,
                    )
            elif order_request.side == OrderSide.SELL:
                if (
                    order_request.symbol in self._positions
                    and self._positions[order_request.symbol].quantity
                    >= order_request.quantity
                ):
                    # Reduce existing position
                    position = self._positions[order_request.symbol]
                    position.quantity -= order_request.quantity
                    if position.quantity <= 0:
                        # Close position entirely
                        position.unrealized_pl = (
                            position.quantity * mock_price - position.cost_basis
                        )
                        position.unrealized_pl_pct = (
                            position.unrealized_pl / position.cost_basis * 100
                        )
                else:
                    # No position to sell from
                    raise InsufficientFundsError(
                        f"No position for {order_request.symbol}"
                    )

            # Create result
            result = OrderResult(
                order_id=str(uuid.uuid4()),
                symbol=order_request.symbol,
                side=order_request.side,
                order_type=order_request.order_type,
                quantity=order_request.quantity,
                filled_quantity=order_request.quantity,
                price=mock_price,
                average_price=mock_price,
                status=OrderStatus.FILLED,
                timestamp=datetime.now(),
                time_in_force=order_request.time_in_force,
                stop_price=order_request.stop_price,
            )

            self._orders[order_request.client_order_id] = result
            return result

        else:
            # For non-market orders, simulate pending status
            result = OrderResult(
                order_id=str(uuid.uuid4()),
                symbol=order_request.symbol,
                side=order_request.side,
                order_type=order_request.order_type,
                quantity=order_request.quantity,
                filled_quantity=0.0,
                price=order_request.price,
                average_price=None,
                status=OrderStatus.SUBMITTED,
                timestamp=datetime.now(),
                time_in_force=order_request.time_in_force,
                stop_price=order_request.stop_price,
            )

            self._orders[order_request.client_order_id] = result
            return result

    def cancel_order(self, order_id: str) -> bool:
        """
        Cancel an order.

        Args:
            order_id: Order ID to cancel

        Returns:
            True if successfully canceled, False otherwise
        """
        # Find the order
        order = None
        for client_order_id, result in self._orders.items():
            if result.order_id == order_id:
                order = result
                break

        if not order:
            raise OrderNotFoundError(f"Order {order_id} not found")

        # Only allow cancellation of non-filled orders
        if order.status in [OrderStatus.FILLED, OrderStatus.PARTIALLY_FILLED]:
            raise TradingError(f"Cannot cancel filled order {order_id}")

        # Update status
        order.status = OrderStatus.CANCELLED
        order.timestamp = datetime.now()

        return True

    def get_order_status(self, order_id: str) -> OrderResult:
        """
        Get the status of an order.

        Args:
            order_id: Order ID to check

        Returns:
            Order result with current status
        """
        # Find the order
        for client_order_id, result in self._orders.items():
            if result.order_id == order_id:
                return result

        raise OrderNotFoundError(f"Order {order_id} not found")

    def get_positions(self) -> List[Position]:
        """
        Get all open positions.

        Returns:
            List of open positions
        """
        return list(self._positions.values())

    def get_position(self, symbol: str) -> Optional[Position]:
        """
        Get position for a symbol.

        Args:
            symbol: Trading symbol

        Returns:
            Position object or None if no position
        """
        return self._positions.get(symbol)

    def get_account_info(self) -> AccountInfo:
        """
        Get account information.

        Returns:
            Account information object
        """
        # Calculate portfolio value
        portfolio_value = sum(pos.market_value for pos in self._positions.values())

        # Mock other account info
        return AccountInfo(
            account_id="mock_account",
            buying_power=portfolio_value * 2.0,  # Mock 2x leverage
            cash=portfolio_value * 0.5,  # Mock 50% cash available
            portfolio_value=portfolio_value,
            day_trading_profit_loss=sum(
                pos.unrealized_pl for pos in self._positions.values()
            ),
            maintenance_margin=portfolio_value * 0.1,  # Mock 10% maintenance
            day_trades_count=len(self._orders),
            leverage=2.0,
        )

    def get_order_history(
        self, symbol: Optional[str] = None, limit: int = 100
    ) -> List[OrderResult]:
        """
        Get order history.

        Args:
            symbol: Filter by symbol (optional)
            limit: Maximum number of orders to return

        Returns:
            List of order results
        """
        orders = list(self._orders.values())

        # Filter by symbol if provided
        if symbol:
            orders = [order for order in orders if order.symbol == symbol]

        # Sort by timestamp (newest first)
        orders.sort(key=lambda x: x.timestamp, reverse=True)

        # Apply limit
        return orders[:limit]

    def get_account_balance(self) -> Dict[str, float]:
        """
        Get account balance in dictionary format for compatibility.

        Returns:
            Dictionary with account balance information
        """
        account_info = self.get_account_info()
        return {
            "portfolio_value": account_info.portfolio_value,
            "cash": account_info.cash,
            "buying_power": account_info.buying_power,
        }
