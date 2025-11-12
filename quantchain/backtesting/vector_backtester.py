"""
Vector-based backtesting engine for high-performance strategy testing.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Tuple

import pandas as pd

from .engine import BacktestConfig, DataValidationError
from .market_friction import (
    FixedLatency,
    FixedSlippage,
    MarketFrictionConfig,
    MarketFrictionSimulator,
    PercentageCommission,
)


# Custom Exceptions
class VectorBacktestError(Exception):
    """Raised for vector backtester specific errors."""

    pass


class SignalProcessingError(Exception):
    """Raised for signal processing errors."""

    pass


@dataclass
class VectorBacktestResult:
    """Results from vector backtester execution."""

    equity_curve: pd.Series
    trade_log: pd.DataFrame
    positions: pd.Series
    returns: pd.Series
    metrics: Dict[str, Any] = field(default_factory=dict)


class VectorizedPositionManager:
    """Manages positions and equity calculations using vectorized operations."""

    def __init__(
        self,
        initial_cash: float = 100000.0,
        commission_rate: float = 0.0,
        slippage_rate: float = 0.0,
    ):
        """Initialize position manager with initial cash and cost parameters."""
        self.initial_cash = initial_cash
        self.current_cash = initial_cash
        self.commission_rate = commission_rate
        self.slippage_rate = slippage_rate
        self.positions = None
        self.equity_curve = None
        self.trade_log = None

    def _process_buy_signal(
        self,
        timestamp: Any,
        price: float,
        signal: float,
        current_position: float,
        current_cash: float,
    ) -> Tuple[float, float, Dict[str, Any]]:
        """Process a buy signal and return updated position, cash, and trade record."""
        if signal > 0 and current_position == 0:
            execution_price = price * (1 + self.slippage_rate)
            shares_to_buy = current_cash / execution_price
            cost = shares_to_buy * execution_price
            commission = cost * self.commission_rate
            total_cost = cost + commission

            if cost <= current_cash + 0.01:  # Small tolerance
                cash_before = current_cash
                current_cash -= total_cost
                current_position += shares_to_buy

                trade = {
                    "timestamp": timestamp,
                    "signal": signal,
                    "price": execution_price,
                    "shares": shares_to_buy,
                    "commission": commission,
                    "slippage": cost * self.slippage_rate,
                    "cash_before": cash_before,
                    "cash_after": current_cash,
                    "position": current_position,
                }
            else:
                trade = {}
        else:
            trade = {}

        return current_position, current_cash, trade

    def _process_sell_signal_long(
        self,
        timestamp: Any,
        price: float,
        signal: float,
        current_position: float,
        current_cash: float,
    ) -> Tuple[float, float, Dict[str, Any]]:
        """Process a sell signal for closing long position."""
        if signal < 0 and current_position > 0:
            execution_price = price * (1 - self.slippage_rate)
            proceeds = current_position * execution_price
            commission = proceeds * self.commission_rate
            net_proceeds = proceeds - commission

            cash_before = current_cash
            current_cash += net_proceeds

            trade = {
                "timestamp": timestamp,
                "signal": signal,
                "price": execution_price,
                "shares": -current_position,
                "commission": commission,
                "slippage": proceeds * self.slippage_rate,
                "cash_before": cash_before,
                "cash_after": current_cash,
                "position": 0.0,
            }
            current_position = 0.0
        else:
            current_position = current_position
            current_cash = current_cash
            trade = {}

        return current_position, current_cash, trade

    def _process_sell_signal_short(
        self,
        timestamp: Any,
        price: float,
        signal: float,
        current_position: float,
        current_cash: float,
    ) -> Tuple[float, float, Dict[str, Any]]:
        """Process a sell signal for covering short position."""
        if signal < 0 and current_position < 0:
            execution_price = price * (1 + self.slippage_rate)
            cost_to_cover = abs(current_position) * execution_price
            commission = cost_to_cover * self.commission_rate
            total_cost = cost_to_cover + commission

            if total_cost <= current_cash + 0.01:
                cash_before = current_cash
                current_cash -= total_cost
                current_position = 0.0

                trade = {
                    "timestamp": timestamp,
                    "signal": signal,
                    "price": execution_price,
                    "shares": abs(current_position),
                    "commission": commission,
                    "slippage": cost_to_cover * self.slippage_rate,
                    "cash_before": cash_before,
                    "cash_after": current_cash,
                    "position": current_position,
                }
            else:
                trade = {}
        else:
            trade = {}

        return current_position, current_cash, trade

    def process_signals(
        self, prices: pd.Series, signals: pd.Series
    ) -> Tuple[pd.Series, pd.DataFrame, float]:
        """
        Process trading signals and calculate positions and trades.

        Args:
            prices: Series of asset prices
            signals: Series of trading signals (1=buy, -1=sell, 0=hold)

        Returns:
            Tuple of (positions, trades)
        """
        if len(prices) != len(signals):
            raise SignalProcessingError(
                f"Length mismatch: {len(prices)} prices vs {len(signals)} signals"
            )

        # Initialize positions and trades
        positions = pd.Series(0.0, index=prices.index)
        trades = []

        # Track current position and cash
        current_position = 0.0
        current_cash = self.initial_cash

        # Process all signals
        for i, (timestamp, price, signal) in enumerate(
            zip(prices.index, prices, signals)
        ):
            if signal != 0:
                # Process buy signal
                if signal > 0 and current_position == 0:
                    current_position, current_cash, trade = self._process_buy_signal(
                        timestamp, price, signal, current_position, current_cash
                    )
                    if trade:
                        trades.append(trade)

                # Process sell signal for long position
                elif signal < 0 and current_position > 0:
                    current_position, current_cash, trade = (
                        self._process_sell_signal_long(
                            timestamp, price, signal, current_position, current_cash
                        )
                    )
                    if trade:
                        trades.append(trade)

                # Process sell signal for short position
                elif signal < 0 and current_position < 0:
                    current_position, current_cash, trade = (
                        self._process_sell_signal_short(
                            timestamp, price, signal, current_position, current_cash
                        )
                    )
                    if trade:
                        trades.append(trade)

            positions.iloc[i] = current_position

        self.positions = positions
        self.trade_log = pd.DataFrame(trades) if trades else pd.DataFrame()
        self.current_cash = current_cash

        return positions, self.trade_log, self.current_cash

    def calculate_equity(self, prices: pd.Series, positions: pd.Series) -> pd.Series:
        """
        Calculate equity curve from prices and positions.

        Args:
            prices: Series of asset prices
            positions: Series of positions

        Returns:
            Series of equity values over time
        """
        if len(prices) != len(positions):
            raise SignalProcessingError(
                f"Length mismatch: {len(prices)} prices vs {len(positions)} positions"
            )

        # Initialize cash tracking with initial cash
        cash_series = pd.Series(self.initial_cash, index=prices.index)

        # Update cash at trade timestamps using forward fill for efficiency
        if self.trade_log is not None and not self.trade_log.empty:
            # Manually update cash at each trade timestamp and forward fill
            for _, trade in self.trade_log.iterrows():
                cash_after = trade["cash_after"]
                timestamp = trade["timestamp"]
                # Update all entries from this timestamp forward
                mask = prices.index >= timestamp
                cash_series[mask] = cash_after
        elif len(positions) > 0 and positions.iloc[0] > 0:
            # All cash was used to buy initial position
            cash_series[:] = 0.0

        # Calculate position value and total equity using vectorized operations
        position_values = positions * prices
        equity_curve = cash_series + position_values

        self.equity_curve = equity_curve
        return equity_curve


class VectorBacktester:
    """High-performance vector-based backtesting engine."""

    def __init__(self, config: Optional[BacktestConfig] = None):
        """
        Initialize vector backtester.

        Args:
            config: Backtest configuration, uses defaults if None
        """
        self.config = config or BacktestConfig()
        self.position_manager = VectorizedPositionManager(
            initial_cash=self.config.initial_cash,
            commission_rate=self.config.commission_rate,
            slippage_rate=self.config.slippage_rate,
        )

        # Convert BacktestConfig to MarketFrictionConfig
        friction_config = MarketFrictionConfig(
            commission_model=PercentageCommission(rate=self.config.commission_rate),
            slippage_model=FixedSlippage(rate=self.config.slippage_rate),
            latency_model=FixedLatency(latency_ms=self.config.latency_ms),
        )
        self.market_friction = MarketFrictionSimulator(friction_config)
        self._result: Optional[VectorBacktestResult] = None

    def run(
        self,
        signals: pd.Series,
        data: pd.DataFrame,
        config: Optional[BacktestConfig] = None,
    ) -> VectorBacktestResult:
        """
        Run vector backtest with given signals and data.

        Args:
            signals: Trading signals series
            data: OHLCV data DataFrame
            config: Optional override configuration

        Returns:
            VectorBacktestResult with equity curve and trade log
        """
        if config:
            self.config = config
            self.position_manager = VectorizedPositionManager(
                initial_cash=self.config.initial_cash,
                commission_rate=self.config.commission_rate,
                slippage_rate=self.config.slippage_rate,
            )

        # Validate inputs
        self._validate_inputs(data, signals)

        # Extract price data
        if "close" not in data.columns:
            raise DataValidationError("Data must contain 'close' column")

        prices = data["close"]

        # Process signals and calculate positions
        positions, trades, final_cash = self.position_manager.process_signals(
            prices, signals
        )

        # Note: Market friction already applied in process_signals
        # via commission and slippage rates

        # Calculate equity curve
        equity_curve = self.position_manager.calculate_equity(prices, positions)

        # Calculate returns
        returns = equity_curve.pct_change().fillna(0)

        # Store result
        self._result = VectorBacktestResult(
            equity_curve=equity_curve,
            trade_log=trades,
            positions=positions,
            returns=returns,
            metrics={
                "total_trades": len(trades),
                "final_equity": equity_curve.iloc[-1],
                "initial_equity": self.config.initial_cash,
                "total_return": (equity_curve.iloc[-1] - self.config.initial_cash)
                / self.config.initial_cash,
            },
        )

        return self._result

    def get_results(self) -> Optional[VectorBacktestResult]:
        """Get results of the last backtest."""
        return self._result

    def get_equity_curve(self) -> Optional[pd.Series]:
        """Get equity curve from the last backtest."""
        return self._result.equity_curve if self._result else None

    def _validate_inputs(self, data: pd.DataFrame, signals: pd.Series) -> None:
        """Validate input data and signals."""
        if data.empty:
            raise VectorBacktestError("Empty data provided")

        if signals.empty:
            raise SignalProcessingError("Signals cannot be empty")

        if len(signals) != len(data):
            raise SignalProcessingError(
                f"Signal and data length mismatch: {len(signals)} vs {len(data)}"
            )

        # Check signal values are valid (-1, 0, 1)
        invalid_signals = signals[~signals.isin([-1, 0, 1])]
        if not invalid_signals.empty:
            # Get unique invalid values - signals could be Series
            if hasattr(invalid_signals, 'unique'):
                invalid_values = invalid_signals.unique()
            else:
                invalid_values = list(set(invalid_signals))
            raise SignalProcessingError(
                f"Invalid signal values found: {invalid_values}. "
                "Signals must be -1 (sell), 0 (hold), or 1 (buy)"
            )
