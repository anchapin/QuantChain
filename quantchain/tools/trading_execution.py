"""Trading execution interface and base classes for QuantChain."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any

from ..core.exceptions import QuantChainError


class OrderSide(Enum):
    """Order side (buy or sell)."""

    BUY = "buy"
    SELL = "sell"


class OrderType(Enum):
    """Order types supported by the execution interface."""

    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"


class OrderStatus(Enum):
    """Order status values."""

    PENDING = "pending"
    FILLED = "filled"
    PARTIALLY_FILLED = "partially_filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"
    EXPIRED = "expired"


class TimeInForce(Enum):
    """Time in force options for orders."""

    DAY = "day"
    GTC = "gtc"  # Good Till Cancelled
    IOC = "ioc"  # Immediate Or Cancel
    FOK = "fok"  # Fill Or Kill


# Custom exceptions for trading execution
class ExecutionError(QuantChainError):
    """Raised when order execution fails."""

    pass


class ValidationError(QuantChainError):
    """Raised when order parameters are invalid."""

    pass


class InsufficientFundsError(ExecutionError):
    """Raised when insufficient funds are available for order."""

    pass


class OrderNotFoundError(ExecutionError):
    """Raised when order cannot be found."""

    pass


@dataclass
class OrderRequest:
    """Request for placing a trading order."""

    symbol: str
    side: OrderSide
    order_type: OrderType
    quantity: float
    price: Optional[float] = None
    stop_price: Optional[float] = None
    time_in_force: TimeInForce = TimeInForce.DAY
    client_order_id: Optional[str] = None

    def __post_init__(self) -> None:
        """Validate order request after initialization."""
        if self.quantity <= 0:
            raise ValidationError("Order quantity must be positive")

        if self.order_type == OrderType.LIMIT and self.price is None:
            raise ValidationError("Limit orders require a price")

        if self.order_type == OrderType.STOP and self.stop_price is None:
            raise ValidationError("Stop orders require a stop price")

        if self.order_type == OrderType.STOP_LIMIT and (
            self.price is None or self.stop_price is None
        ):
            raise ValidationError("Stop limit orders require both price and stop_price")


@dataclass
class OrderResult:
    """Result of an order placement or status query."""

    order_id: str
    client_order_id: Optional[str]
    symbol: str
    side: OrderSide
    order_type: OrderType
    quantity: float
    filled_quantity: float
    price: Optional[float]
    stop_price: Optional[float]
    avg_fill_price: Optional[float]
    status: OrderStatus
    timestamp: datetime
    updated_at: Optional[datetime] = None

    @property
    def is_filled(self) -> bool:
        """Check if order is completely filled."""
        return self.status == OrderStatus.FILLED

    @property
    def is_partially_filled(self) -> bool:
        """Check if order is partially filled."""
        return self.status == OrderStatus.PARTIALLY_FILLED

    @property
    def is_active(self) -> bool:
        """Check if order is still active (pending, partially filled)."""
        return self.status in [OrderStatus.PENDING, OrderStatus.PARTIALLY_FILLED]


@dataclass
class Position:
    """Position information for a symbol."""

    symbol: str
    quantity: float
    avg_entry_price: float
    current_price: float
    market_value: float
    unrealized_pnl: float
    unrealized_pnl_percent: float

    @property
    def is_long(self) -> bool:
        """Check if position is long."""
        return self.quantity > 0

    @property
    def is_short(self) -> bool:
        """Check if position is short."""
        return self.quantity < 0

    @property
    def is_flat(self) -> bool:
        """Check if position is flat."""
        return abs(self.quantity) < 1e-10


@dataclass
class AccountInfo:
    """Account information."""

    account_id: str
    buying_power: float
    cash: float
    portfolio_value: float
    positions: List[Position]
    margin_available: Optional[float] = None

    @property
    def total_equity(self) -> float:
        """Total equity including cash and positions."""
        return self.portfolio_value

    @property
    def available_margin(self) -> float:
        """Available margin for trading."""
        return self.margin_available or self.buying_power


class TradingExecutionInterface(ABC):
    """Abstract base interface for trading execution systems."""

    @abstractmethod
    def place_order(self, order: OrderRequest) -> OrderResult:
        """Place a trading order and return the result."""
        pass

    @abstractmethod
    def cancel_order(self, order_id: str) -> OrderResult:
        """Cancel an existing order."""
        pass

    @abstractmethod
    def get_order(self, order_id: str) -> OrderResult:
        """Retrieve order status and details."""
        pass

    @abstractmethod
    def get_account(self) -> AccountInfo:
        """Retrieve account information."""
        pass

    @abstractmethod
    def get_positions(self) -> List[Position]:
        """Retrieve current open positions."""
        pass

    @abstractmethod
    def get_order_history(
        self,
        symbol: Optional[str] = None,
        status: Optional[OrderStatus] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: Optional[int] = None,
    ) -> List[OrderResult]:
        """Retrieve historical orders with optional filtering."""
        pass

    @abstractmethod
    def is_market_open(self, symbol: Optional[str] = None) -> bool:
        """Check if the market is open for trading."""
        pass

    def validate_order(self, order: OrderRequest) -> None:
        """
        Validate order parameters (can be overridden for broker-specific validation).

        Basic validation is done in OrderRequest.__post_init__
        """

    def get_symbol_info(self, symbol: str) -> Dict[str, Any]:
        """Get detailed information about a symbol (optional implementation)."""
        return {}

    def get_market_hours(self, symbol: Optional[str] = None) -> Dict[str, Any]:
        """Get market hours for a symbol or market (optional implementation)."""
        return {}
