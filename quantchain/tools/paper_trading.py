"""Paper trading executor for risk-free strategy testing."""

import random
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from dataclasses import dataclass

import pandas as pd

from .trading_execution import (
    TradingExecutionInterface,
    OrderRequest,
    OrderResult,
    OrderSide,
    OrderType,
    OrderStatus,
    Position,
    AccountInfo,
    ExecutionError,
    ValidationError,
    OrderNotFoundError,
)


# Slippage models
@dataclass
class SlippageModel:
    """Base class for slippage models."""

    def apply_slippage(self, order: OrderRequest, market_price: float) -> float:
        """Apply slippage to market price."""
        return market_price


@dataclass
class NoSlippage(SlippageModel):
    """No slippage model."""

    def apply_slippage(self, order: OrderRequest, market_price: float) -> float:
        return market_price


@dataclass
class FixedSlippage(SlippageModel):
    """Fixed percentage slippage model."""

    slippage_percent: float = 0.1  # Default 0.1%

    def apply_slippage(self, order: OrderRequest, market_price: float) -> float:
        slippage_amount = market_price * (self.slippage_percent / 100)

        if order.side == OrderSide.BUY:
            return market_price + slippage_amount  # Worse price for buyers
        else:
            return market_price - slippage_amount  # Worse price for sellers


@dataclass
class VolumeSlippage(SlippageModel):
    """Volume-based slippage model."""

    base_slippage: float = 0.05  # Base 0.05%
    volume_threshold: float = 1000000  # $1M threshold

    def apply_slippage(self, order: OrderRequest, market_price: float) -> float:
        order_value = market_price * order.quantity
        volume_impact = max(0, (order_value / self.volume_threshold) - 1)
        slippage_percent = self.base_slippage * (1 + volume_impact)

        slippage_amount = market_price * (slippage_percent / 100)

        if order.side == OrderSide.BUY:
            return float(market_price + slippage_amount)
        else:
            return float(market_price - slippage_amount)


@dataclass
class RandomSlippage(SlippageModel):
    """Random slippage model for market uncertainty."""

    min_slippage: float = 0.0
    max_slippage: float = 0.2  # Max 0.2%

    def apply_slippage(self, order: OrderRequest, market_price: float) -> float:
        slippage_percent = random.uniform(self.min_slippage, self.max_slippage)
        slippage_amount = market_price * (slippage_percent / 100)

        # Random direction
        if random.random() < 0.5:
            return market_price + slippage_amount
        else:
            return market_price - slippage_amount


# Fill models
@dataclass
class FillModel:
    """Base class for fill models."""

    def should_fill(self, order: OrderRequest, market_price: float) -> bool:
        """Determine if order should fill."""
        return True


@dataclass
class ImmediateFill(FillModel):
    """Immediate fill model - orders fill immediately if conditions met."""

    def should_fill(self, order: OrderRequest, market_price: float) -> bool:
        if order.order_type == OrderType.MARKET:
            return True
        elif order.order_type == OrderType.LIMIT:
            if order.price is None:
                return False
            if order.side == OrderSide.BUY:
                return market_price <= order.price  # type: ignore[no-any-return]
            else:
                return market_price >= order.price  # type: ignore[no-any-return]
        elif order.order_type == OrderType.STOP:
            if order.stop_price is None:
                return False
            if order.side == OrderSide.BUY:
                return market_price >= order.stop_price  # type: ignore[no-any-return]
            else:
                return market_price <= order.stop_price  # type: ignore[no-any-return]
        elif order.order_type == OrderType.STOP_LIMIT:
            # First check stop condition
            if order.stop_price is None or order.price is None:
                return False
            if (
                order.side == OrderSide.BUY
                and market_price < order.stop_price
                or order.side != OrderSide.BUY
                and market_price > order.stop_price
            ):
                return False
            # Then check limit condition
            if order.side == OrderSide.BUY:
                return market_price <= order.price  # type: ignore[no-any-return]
            else:
                return market_price >= order.price  # type: ignore[no-any-return]

        return False


@dataclass
class PerformanceMetrics:
    """Performance tracking for paper trading."""

    total_return: float = 0.0
    win_rate: float = 0.0
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    gross_profit: float = 0.0
    gross_loss: float = 0.0
    max_drawdown: float = 0.0
    sharpe_ratio: Optional[float] = None
    profit_factor: Optional[float] = None

    def update_metrics(self, trade_pnl: float, equity_curve: List[float]) -> None:
        """Update performance metrics after a trade."""
        self.total_trades += 1

        if trade_pnl > 0:
            self.winning_trades += 1
            self.gross_profit += trade_pnl
        else:
            self.losing_trades += 1
            self.gross_loss += abs(trade_pnl)

        self.win_rate = (
            (self.winning_trades / self.total_trades) * 100
            if self.total_trades > 0
            else 0
        )

        # Calculate max drawdown
        if equity_curve:
            peak = max(equity_curve)
            current = equity_curve[-1]
            self.max_drawdown = ((peak - current) / peak) * 100 if peak > 0 else 0

        # Calculate profit factor
        if self.gross_loss > 0:
            self.profit_factor = self.gross_profit / self.gross_loss

        # Calculate total return
        if equity_curve and len(equity_curve) > 1:
            self.total_return = (
                (equity_curve[-1] - equity_curve[0]) / equity_curve[0]
            ) * 100


class PaperTradingExecutor(TradingExecutionInterface):
    """Paper trading implementation for strategy testing."""

    def __init__(self, initial_cash: float = 100000.0, **kwargs: Any) -> None:
        """Initialize paper trading executor.

        Args:
            initial_cash: Starting cash balance (default: 100000.0)
            **kwargs: Additional configuration
                - commission_per_trade: Commission per trade (default: 0.0)
                - commission_per_share: Commission per share (default: 0.0)
                - slippage_model: SlippageModel (default: NoSlippage)
                - fill_model: FillModel (default: ImmediateFill)
        """
        self.initial_cash = initial_cash
        self.cash = initial_cash
        self.commission_per_trade = kwargs.get("commission_per_trade", 0.0)
        self.commission_per_share = kwargs.get("commission_per_share", 0.0)
        self.slippage_model = kwargs.get("slippage_model", NoSlippage())
        self.fill_model = kwargs.get("fill_model", ImmediateFill())

        # Trading state
        self.positions: Dict[str, Position] = {}
        self.orders: Dict[str, OrderResult] = {}
        self.order_counter = 1
        self.equity_curve: List[float] = [initial_cash]

        # Performance tracking
        self.performance_metrics = PerformanceMetrics()

        # Market data storage
        self.market_prices: Dict[str, float] = {}

    def _generate_order_id(self) -> str:
        """Generate unique order ID."""
        order_id = f"PAPER_{self.order_counter:06d}"
        self.order_counter += 1
        return order_id

    def _calculate_commission(self, order: OrderRequest) -> float:
        """Calculate commission for an order."""
        return float(
            self.commission_per_trade + (self.commission_per_share * order.quantity)
        )

    def _get_market_price(self, symbol: str) -> float:
        """Get current market price for a symbol."""
        if symbol not in self.market_prices:
            # Generate default price if not set
            self.market_prices[symbol] = 100.0 + random.uniform(-10, 10)
        return self.market_prices[symbol]

    def place_order(self, order: OrderRequest) -> OrderResult:
        """Place a trading order in paper trading."""
        try:
            # Validate order
            self.validate_order(order)

            # Get market price
            market_price = self._get_market_price(order.symbol)

            # Check if order should fill based on original market price
            if not self.fill_model.should_fill(order, market_price):
                # Return pending order
                order_id = self._generate_order_id()
                result = OrderResult(
                    order_id=order_id,
                    client_order_id=order.client_order_id,
                    symbol=order.symbol,
                    side=order.side,
                    order_type=order.order_type,
                    quantity=order.quantity,
                    filled_quantity=0.0,
                    price=order.price,
                    stop_price=order.stop_price,
                    avg_fill_price=None,
                    status=OrderStatus.PENDING,
                    timestamp=datetime.now(timezone.utc),
                )
                self.orders[order_id] = result
                return result

            # Apply slippage only for filled orders
            fill_price = self.slippage_model.apply_slippage(order, market_price)

            # Calculate commission
            commission = self._calculate_commission(order)

            # Calculate total cost
            total_cost = fill_price * order.quantity + commission

            # Check sufficient funds for buy orders
            if order.side == OrderSide.BUY:
                if self.cash < total_cost:
                    raise ExecutionError(
                        f"Insufficient funds: need {total_cost:.2f}, "
                        f"have {self.cash:.2f}"
                    )

                # Update cash and position
                self.cash -= total_cost

                # Update or create position
                if order.symbol in self.positions:
                    pos = self.positions[order.symbol]
                    new_quantity = pos.quantity + order.quantity
                    new_cost_basis = (pos.avg_entry_price * pos.quantity) + (
                        fill_price * order.quantity
                    )
                    pos.avg_entry_price = new_cost_basis / new_quantity
                    pos.quantity = new_quantity
                else:
                    self.positions[order.symbol] = Position(
                        symbol=order.symbol,
                        quantity=order.quantity,
                        avg_entry_price=fill_price,
                        current_price=fill_price,
                        market_value=fill_price * order.quantity,
                        unrealized_pnl=0.0,
                        unrealized_pnl_percent=0.0,
                    )

            else:  # SELL order
                # Check if we have position to sell
                if (
                    order.symbol not in self.positions
                    or self.positions[order.symbol].quantity < order.quantity
                ):
                    raise ExecutionError(f"Insufficient position for {order.symbol}")

                # Update position
                pos = self.positions[order.symbol]
                remaining_quantity = pos.quantity - order.quantity

                # Calculate realized P&L
                realized_pnl = (fill_price - pos.avg_entry_price) * order.quantity
                self.cash += (fill_price * order.quantity) - commission

                if remaining_quantity < 1e-10:  # Position closed
                    del self.positions[order.symbol]
                    # Update performance metrics
                    self.performance_metrics.update_metrics(
                        realized_pnl, self.equity_curve
                    )
                else:
                    pos.quantity = remaining_quantity

            # Create order result
            order_id = self._generate_order_id()
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
                avg_fill_price=fill_price,
                status=OrderStatus.FILLED,
                timestamp=datetime.now(timezone.utc),
            )

            self.orders[order_id] = result

            # Update equity curve
            portfolio_value = self.cash + sum(
                pos.market_value for pos in self.positions.values()
            )
            self.equity_curve.append(portfolio_value)

            return result

        except Exception as e:
            if isinstance(e, (ValidationError, ExecutionError)):
                raise
            raise ExecutionError(f"Failed to place order: {str(e)}") from e

    def cancel_order(self, order_id: str) -> OrderResult:
        """Cancel an existing order."""
        if order_id not in self.orders:
            raise OrderNotFoundError(f"Order {order_id} not found")

        order = self.orders[order_id]
        if order.status not in [OrderStatus.PENDING, OrderStatus.PARTIALLY_FILLED]:
            raise ExecutionError(
                f"Cannot cancel order {order_id} with status {order.status}"
            )

        order.status = OrderStatus.CANCELLED
        order.updated_at = datetime.now(timezone.utc)

        return order

    def get_order(self, order_id: str) -> OrderResult:
        """Retrieve order status and details."""
        if order_id not in self.orders:
            raise OrderNotFoundError(f"Order {order_id} not found")
        return self.orders[order_id]

    def get_account(self) -> AccountInfo:
        """Retrieve account information."""
        portfolio_value = self.cash + sum(
            pos.market_value for pos in self.positions.values()
        )
        positions = list(self.positions.values())

        return AccountInfo(
            account_id="PAPER_TRADING",
            buying_power=self.cash,
            cash=self.cash,
            portfolio_value=portfolio_value,
            positions=positions,
        )

    def get_positions(self) -> List[Position]:
        """Retrieve current open positions."""
        # Update current prices and P&L
        for symbol, pos in self.positions.items():
            current_price = self._get_market_price(symbol)
            pos.current_price = current_price
            pos.market_value = current_price * pos.quantity

            # Calculate unrealized P&L
            if abs(pos.quantity) > 1e-10 and pos.avg_entry_price > 0:
                pos.unrealized_pnl = (current_price - pos.avg_entry_price) * abs(
                    pos.quantity
                )
                pos.unrealized_pnl_percent = (
                    (current_price - pos.avg_entry_price) / pos.avg_entry_price
                ) * 100
            else:
                pos.unrealized_pnl = 0.0
                pos.unrealized_pnl_percent = 0.0

        return list(self.positions.values())

    def get_order_history(
        self,
        symbol: Optional[str] = None,
        status: Optional[OrderStatus] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: Optional[int] = None,
    ) -> List[OrderResult]:
        """Retrieve historical orders."""
        orders = list(self.orders.values())

        # Apply filters
        if symbol:
            orders = [o for o in orders if o.symbol == symbol]
        if status:
            orders = [o for o in orders if o.status == status]
        if start_date:
            orders = [o for o in orders if o.timestamp >= start_date]
        if end_date:
            orders = [o for o in orders if o.timestamp <= end_date]
        if limit:
            orders = orders[:limit]

        return sorted(orders, key=lambda o: o.timestamp, reverse=True)

    def is_market_open(self, symbol: Optional[str] = None) -> bool:
        """Paper trading markets are always open."""
        return True

    def set_market_price(self, symbol: str, price: float) -> None:
        """Set market price for a symbol (for testing)."""
        if price <= 0:
            raise ValidationError("Price must be positive")
        self.market_prices[symbol] = price

    def update_market_data(self, symbols: List[str]) -> None:
        """Update market prices for multiple symbols."""
        for symbol in symbols:
            # Simulate small price movements
            if symbol in self.market_prices:
                change = random.uniform(-0.02, 0.02)  # ±2% change
                self.market_prices[symbol] *= 1 + change
            else:
                self.market_prices[symbol] = 100.0 + random.uniform(-10, 10)

    def get_performance_metrics(self) -> PerformanceMetrics:
        """Get current performance metrics."""
        # Update metrics based on current equity curve
        if self.equity_curve:
            current_value = self.equity_curve[-1]
            total_return = (
                (current_value - self.initial_cash) / self.initial_cash
            ) * 100
            self.performance_metrics.total_return = total_return

        return self.performance_metrics

    def export_trade_history(self) -> pd.DataFrame:
        """Export complete trade history."""
        orders = self.get_order_history()

        data = [
            {
                "timestamp": order.timestamp,
                "order_id": order.order_id,
                "symbol": order.symbol,
                "side": order.side.value,
                "order_type": order.order_type.value,
                "quantity": order.quantity,
                "filled_quantity": order.filled_quantity,
                "avg_fill_price": order.avg_fill_price,
                "status": order.status.value,
            }
            for order in orders
        ]
        return pd.DataFrame(data)

    def reset(self) -> None:
        """Reset paper trading state."""
        self.cash = self.initial_cash
        self.positions.clear()
        self.orders.clear()
        self.order_counter = 1
        self.equity_curve = [self.initial_cash]
        self.market_prices.clear()
        self.performance_metrics = PerformanceMetrics()
