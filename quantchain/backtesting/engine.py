"""Core backtesting engine for QuantChain."""

import time
from datetime import datetime
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd


class BacktestExecutionError(Exception):
    """Exception raised when backtesting execution fails."""

    pass


class BacktestConfig:
    """Configuration for backtesting."""

    def __init__(
        self,
        initial_capital: float = 100000.0,
        commission: float = 0.001,
        slippage: float = 0.0005,
        position_size: float = 0.1,
        stop_loss_pct: float = 0.05,
        take_profit_pct: float = 0.1,
        max_open_positions: int = 10,
    ):
        """
        Initialize backtesting configuration.

        Args:
            initial_capital: Starting capital for backtest
            commission: Commission rate per trade (as decimal)
            slippage: Slippage rate per trade (as decimal)
            position_size: Default position size as fraction of capital
            stop_loss_pct: Stop loss percentage
            take_profit_pct: Take profit percentage
            max_open_positions: Maximum number of open positions
        """
        self.initial_capital = initial_capital
        self.commission = commission
        self.slippage = slippage
        self.position_size = position_size
        self.stop_loss_pct = stop_loss_pct
        self.take_profit_pct = take_profit_pct
        self.max_open_positions = max_open_positions

        # Validate values
        if initial_capital <= 0:
            raise ValueError("Initial capital must be positive")
        if commission < 0:
            raise ValueError("Commission must be non-negative")
        if slippage < 0:
            raise ValueError("Slippage must be non-negative")
        if position_size <= 0:
            raise ValueError("Position size must be positive")
        if stop_loss_pct <= 0 or stop_loss_pct >= 1:
            raise ValueError("Stop loss percentage must be between 0 and 1")
        if take_profit_pct <= 0:
            raise ValueError("Take profit percentage must be positive")
        if max_open_positions <= 0:
            raise ValueError("Max open positions must be positive")


class MetricsResult:
    """Result of performance metrics calculation."""

    def __init__(
        self,
        total_return: float = 0.0,
        return_pct: float = 0.0,
        annualized_return: float = 0.0,
        sharpe_ratio: float = 0.0,
        sortino_ratio: float = 0.0,
        calmar_ratio: float = 0.0,
        max_drawdown: float = 0.0,
        max_drawdown_pct: float = 0.0,
        max_drawdown_duration: int = 0,
        win_rate: float = 0.0,
        win_rate_pct: float = 0.0,
        profit_factor: float = 0.0,
        recovery_factor: float = 0.0,
        total_trades: int = 0,
        avg_trade: float = 0.0,
        avg_win_pct: float = 0.0,
        avg_loss_pct: float = 0.0,
        largest_win: float = 0.0,
        largest_loss: float = 0.0,
        avg_drawdown: float = 0.0,
        avg_drawdown_pct: float = 0.0,
        var_95: float = 0.0,
        var_99: float = 0.0,
        skewness: float = 0.0,
        kurtosis: float = 0.0,
    ):
        """
        Initialize performance metrics.

        Args:
            total_return: Total return as decimal
            return_pct: Total return as percentage
            annualized_return: Annualized return as decimal
            sharpe_ratio: Sharpe ratio
            sortino_ratio: Sortino ratio
            calmar_ratio: Calmar ratio
            max_drawdown: Maximum drawdown as decimal
            max_drawdown_pct: Maximum drawdown as percentage
            max_drawdown_duration: Maximum drawdown duration in days
            win_rate: Win rate as decimal
            win_rate_pct: Win rate as percentage
            profit_factor: Profit factor
            recovery_factor: Recovery factor
            total_trades: Total number of trades
            avg_trade: Average trade return as decimal
            avg_win_pct: Average winning trade percentage
            avg_loss_pct: Average losing trade percentage
            largest_win: Largest winning trade as decimal
            largest_loss: Largest losing trade as decimal
            avg_drawdown: Average drawdown as decimal
            avg_drawdown_pct: Average drawdown as percentage
            var_95: 95% Value at Risk
            var_99: 99% Value at Risk
            skewness: Return distribution skewness
            kurtosis: Return distribution kurtosis
        """
        self.total_return = total_return
        self.return_pct = return_pct
        self.annualized_return = annualized_return
        self.sharpe_ratio = sharpe_ratio
        self.sortino_ratio = sortino_ratio
        self.calmar_ratio = calmar_ratio
        self.max_drawdown = max_drawdown
        self.max_drawdown_pct = max_drawdown_pct
        self.max_drawdown_duration = max_drawdown_duration
        self.win_rate = win_rate
        self.win_rate_pct = win_rate_pct
        self.profit_factor = profit_factor
        self.recovery_factor = recovery_factor
        self.total_trades = total_trades
        self.avg_trade = avg_trade
        self.avg_win_pct = avg_win_pct
        self.avg_loss_pct = avg_loss_pct
        self.largest_win = largest_win
        self.largest_loss = largest_loss
        self.avg_drawdown = avg_drawdown
        self.avg_drawdown_pct = avg_drawdown_pct
        self.var_95 = var_95
        self.var_99 = var_99
        self.skewness = skewness
        self.kurtosis = kurtosis


class BacktestResult:
    """Result of a backtest run."""

    def __init__(
        self,
        equity_curve: pd.DataFrame,
        trade_log: pd.DataFrame,
        summary_stats: Dict[str, Any],
        metrics: MetricsResult,
        execution_time: float,
        config: BacktestConfig,
    ):
        """
        Initialize backtest result.

        Args:
            equity_curve: DataFrame with equity curve data
            trade_log: DataFrame with trade log data
            summary_stats: Dictionary with summary statistics
            metrics: Performance metrics object
            execution_time: Time taken to run the backtest in seconds
            config: Configuration used for the backtest
        """
        self.equity_curve = equity_curve
        self.trade_log = trade_log
        self.summary_stats = summary_stats
        self.metrics = metrics
        self.execution_time = execution_time
        self.config = config


class BacktestEngine:
    """Core backtesting engine for QuantChain."""

    def __init__(self, config: Optional[BacktestConfig] = None):
        """
        Initialize backtesting engine.

        Args:
            config: Backtesting configuration
        """
        self.config = config or BacktestConfig()
        self._reset_state()

    def _reset_state(self) -> None:
        """Reset the engine state for a new backtest."""
        self.current_capital = self.config.initial_capital
        self.open_positions = {}
        self.closed_trades = []
        self.current_datetime = None
        self.equity_curve = []

    def _calculate_position_value(self, symbol: str, price: float) -> float:
        """Calculate the current value of a position."""
        if symbol not in self.open_positions:
            return 0.0

        position = self.open_positions[symbol]
        return position["quantity"] * price

    def _get_total_portfolio_value(self, prices: Dict[str, float]) -> float:
        """Calculate total portfolio value including cash and open positions."""
        total_value = self.current_capital

        for symbol, position in self.open_positions.items():
            if symbol in prices:
                total_value += position["quantity"] * prices[symbol]

        return total_value

    def _execute_trade(
        self, symbol: str, side: str, quantity: float, price: float, timestamp: datetime
    ) -> Dict[str, Any]:
        """Execute a trade and update positions."""
        # Calculate commission and slippage
        commission = quantity * price * self.config.commission
        slippage = quantity * price * self.config.slippage

        if side == "buy":
            # Apply slippage to price (worse price)
            adjusted_price = price * (1 + self.config.slippage)
            cost = quantity * adjusted_price + commission

            # Check if enough cash
            if self.current_capital < cost:
                return {"success": False, "error": "Insufficient capital"}

            # Update state
            self.current_capital -= cost

            # Update or create position
            if symbol in self.open_positions:
                self.open_positions[symbol]["quantity"] += quantity
                # Calculate average price
                total_cost = self.open_positions[symbol]["total_cost"] + cost
                total_quantity = self.open_positions[symbol]["quantity"] + quantity
                self.open_positions[symbol]["avg_price"] = total_cost / total_quantity
                self.open_positions[symbol]["total_cost"] = total_cost
            else:
                self.open_positions[symbol] = {
                    "quantity": quantity,
                    "avg_price": adjusted_price,
                    "total_cost": cost,
                    "stop_loss": price * (1 - self.config.stop_loss_pct),
                    "take_profit": price * (1 + self.config.take_profit_pct),
                    "open_time": timestamp,
                }

            return {
                "success": True,
                "symbol": symbol,
                "side": side,
                "quantity": quantity,
                "price": adjusted_price,
                "commission": commission,
                "timestamp": timestamp,
            }

        elif side == "sell":
            # Apply slippage to price (worse price)
            adjusted_price = price * (1 - self.config.slippage)
            proceeds = quantity * adjusted_price - commission

            # Check if position exists and has enough quantity
            if (
                symbol not in self.open_positions
                or self.open_positions[symbol]["quantity"] < quantity
            ):
                return {
                    "success": False,
                    "error": "No position or insufficient quantity",
                }

            # Update state
            self.current_capital += proceeds
            self.open_positions[symbol]["quantity"] -= quantity
            realized_pnl = (
                adjusted_price - self.open_positions[symbol]["avg_price"]
            ) * quantity

            # Close position if quantity is now zero
            if self.open_positions[symbol]["quantity"] == 0:
                closed_position = self.open_positions.pop(symbol)
                closed_position.update(
                    {
                        "close_time": timestamp,
                        "close_price": adjusted_price,
                        "realized_pnl": realized_pnl,
                        "commission": commission,
                        "slippage": quantity * price * self.config.slippage,
                    }
                )
                self.closed_trades.append(closed_position)

            return {
                "success": True,
                "symbol": symbol,
                "side": side,
                "quantity": quantity,
                "price": adjusted_price,
                "commission": commission,
                "timestamp": timestamp,
                "realized_pnl": realized_pnl if "realized_pnl" in locals() else 0,
            }

        else:
            return {"success": False, "error": "Invalid side"}

    def _check_stops(
        self, current_prices: Dict[str, float], timestamp: datetime
    ) -> List[Dict[str, Any]]:
        """Check for stop loss or take profit conditions."""
        trades_to_close = []

        for symbol, position in list(self.open_positions.items()):
            if symbol in current_prices:
                current_price = current_prices[symbol]

                # Check stop loss
                if current_price <= position["stop_loss"]:
                    trade = self._execute_trade(
                        symbol,
                        "sell",
                        position["quantity"],
                        position["stop_loss"],
                        timestamp,
                    )
                    trade["reason"] = "stop_loss"
                    trades_to_close.append(trade)

                # Check take profit
                elif current_price >= position["take_profit"]:
                    trade = self._execute_trade(
                        symbol,
                        "sell",
                        position["quantity"],
                        position["take_profit"],
                        timestamp,
                    )
                    trade["reason"] = "take_profit"
                    trades_to_close.append(trade)

        return trades_to_close

    def run_backtest(
        self,
        data: pd.DataFrame,
        strategy: Any,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> BacktestResult:
        """
        Run a backtest with the provided data and strategy.

        Args:
            data: DataFrame with OHLCV data
            strategy: Trading strategy object with required methods
            start_date: Optional start date for backtest
            end_date: Optional end date for backtest

        Returns:
            BacktestResult object with performance metrics
        """
        # Reset state
        self._reset_state()

        # Filter data by date range if provided
        if start_date is not None:
            data = data[data.index >= start_date]
        if end_date is not None:
            data = data[data.index <= end_date]

        # Ensure data is sorted by date
        data = data.sort_index()

        # Initialize strategy
        if hasattr(strategy, "initialize"):
            strategy.initialize(self.config)

        # Run through each bar
        for i, (timestamp, row) in enumerate(data.iterrows()):
            self.current_datetime = timestamp

            # Update current prices dictionary
            current_prices = {}
            for symbol in self.open_positions:
                if "close" in row:
                    current_prices[symbol] = row["close"]

            # Check for stops
            closed_trades = self._check_stops(current_prices, timestamp)

            # Get strategy signal
            if hasattr(strategy, "process_bar"):
                signal = strategy.process_bar(timestamp, row)
            else:
                # Default to no signal
                signal = None

            # Execute trades based on signal
            if signal is not None:
                symbol = signal.get("symbol")
                side = signal.get("side")
                quantity = signal.get("quantity")

                # Limit open positions
                if (
                    side == "buy"
                    and len(self.open_positions) >= self.config.max_open_positions
                ):
                    continue

                if symbol in row:
                    trade = self._execute_trade(
                        symbol, side, quantity, row["close"], timestamp
                    )
                    if trade.get("success"):
                        self.closed_trades.append(trade)

            # Update equity curve
            portfolio_value = self._get_total_portfolio_value(current_prices)
            self.equity_curve.append(
                {
                    "timestamp": timestamp,
                    "portfolio_value": portfolio_value,
                    "cash": self.current_capital,
                    "open_positions": len(self.open_positions),
                }
            )

        # Close any remaining positions
        for symbol in list(self.open_positions.keys()):
            if "close" in row:
                trade = self._execute_trade(
                    symbol,
                    "sell",
                    self.open_positions[symbol]["quantity"],
                    row["close"],
                    timestamp,
                )
                if trade.get("success"):
                    trade["reason"] = "end_of_backtest"
                    self.closed_trades.append(trade)

        # Create DataFrames for results
        equity_curve_df = pd.DataFrame(self.equity_curve)
        equity_curve_df.set_index("timestamp", inplace=True)

        trade_log_df = pd.DataFrame(self.closed_trades)

        # Calculate metrics
        metrics = self._calculate_metrics()

        # Create summary stats
        summary_stats = {
            "initial_capital": self.config.initial_capital,
            "final_capital": self.current_capital,
            "total_trades": len(self.closed_trades),
            "winning_trades": len(
                [t for t in self.closed_trades if t.get("realized_pnl", 0) > 0]
            ),
            "losing_trades": len(
                [t for t in self.closed_trades if t.get("realized_pnl", 0) < 0]
            ),
        }

        return BacktestResult(
            equity_curve=equity_curve_df,
            trade_log=trade_log_df,
            summary_stats=summary_stats,
            metrics=metrics,
            execution_time=time.time(),
            config=self.config,
        )

    def _calculate_metrics(self) -> MetricsResult:
        """Calculate performance metrics from backtest results."""
        if not self.equity_curve:
            return MetricsResult()

        equity_curve_df = pd.DataFrame(self.equity_curve)

        # Extract portfolio values
        portfolio_values = equity_curve_df["portfolio_value"].values

        # Calculate returns
        returns = np.diff(portfolio_values) / portfolio_values[:-1]

        # Basic metrics
        total_return = (
            portfolio_values[-1] - self.config.initial_capital
        ) / self.config.initial_capital
        return_pct = total_return * 100

        # Annualized return (assuming daily data)
        n_days = len(portfolio_values)
        if n_days > 0:
            annualized_return = ((1 + total_return) ** (365 / n_days)) - 1
        else:
            annualized_return = 0

        # Sharpe ratio (assuming 0% risk-free rate)
        if len(returns) > 1 and np.std(returns) > 0:
            sharpe_ratio = np.mean(returns) / np.std(returns) * np.sqrt(252)
        else:
            sharpe_ratio = 0

        # Sortino ratio (downside deviation)
        downside_returns = returns[returns < 0]
        if len(downside_returns) > 1 and np.std(downside_returns) > 0:
            sortino_ratio = np.mean(returns) / np.std(downside_returns) * np.sqrt(252)
        else:
            sortino_ratio = 0

        # Maximum drawdown
        running_max = np.maximum.accumulate(portfolio_values)
        drawdown = (portfolio_values - running_max) / running_max
        max_drawdown = np.min(drawdown)
        max_drawdown_pct = max_drawdown * 100

        # Maximum drawdown duration
        drawdown_end = np.where(drawdown < 0)[0]
        max_drawdown_duration = 0
        current_duration = 0

        for i in range(len(drawdown)):
            if drawdown[i] < 0:
                current_duration += 1
                max_drawdown_duration = max(max_drawdown_duration, current_duration)
            else:
                current_duration = 0

        # Win rate
        if self.closed_trades:
            winning_trades = [
                t for t in self.closed_trades if t.get("realized_pnl", 0) > 0
            ]
            win_rate = len(winning_trades) / len(self.closed_trades)
            win_rate_pct = win_rate * 100

            # Profit factor
            total_profit = sum(t.get("realized_pnl", 0) for t in winning_trades)
            losing_trades = [
                t for t in self.closed_trades if t.get("realized_pnl", 0) < 0
            ]
            total_loss = abs(sum(t.get("realized_pnl", 0) for t in losing_trades))

            profit_factor = (
                total_profit / total_loss if total_loss > 0 else float("inf")
            )

            # Recovery factor
            recovery_factor = (
                total_return / max_drawdown if max_drawdown < 0 else float("inf")
            )

            # Average win/loss percentages
            avg_win_pct = (
                np.mean([t.get("realized_pnl", 0) for t in winning_trades]) * 100
                if winning_trades
                else 0
            )
            avg_loss_pct = (
                np.mean([t.get("realized_pnl", 0) for t in losing_trades]) * 100
                if losing_trades
                else 0
            )

            # Largest win/loss
            largest_win = (
                max([t.get("realized_pnl", 0) for t in winning_trades])
                if winning_trades
                else 0
            )
            largest_loss = (
                min([t.get("realized_pnl", 0) for t in losing_trades])
                if losing_trades
                else 0
            )
        else:
            win_rate = 0
            win_rate_pct = 0
            profit_factor = 0
            recovery_factor = 0
            avg_win_pct = 0
            avg_loss_pct = 0
            largest_win = 0
            largest_loss = 0

        # Risk metrics
        if len(returns) > 0:
            skewness = pd.Series(returns).skew()
            kurtosis = pd.Series(returns).kurtosis()
            var_95 = np.percentile(returns, 5)
            var_99 = np.percentile(returns, 1)
        else:
            skewness = 0
            kurtosis = 0
            var_95 = 0
            var_99 = 0

        return MetricsResult(
            total_return=total_return,
            return_pct=return_pct,
            annualized_return=annualized_return,
            sharpe_ratio=sharpe_ratio,
            sortino_ratio=sortino_ratio,
            calmar_ratio=total_return / abs(max_drawdown) if max_drawdown < 0 else 0,
            max_drawdown=max_drawdown,
            max_drawdown_pct=max_drawdown_pct,
            max_drawdown_duration=max_drawdown_duration,
            win_rate=win_rate,
            win_rate_pct=win_rate_pct,
            profit_factor=profit_factor,
            recovery_factor=recovery_factor,
            total_trades=len(self.closed_trades),
            avg_trade=(
                np.mean([t.get("realized_pnl", 0) for t in self.closed_trades])
                if self.closed_trades
                else 0
            ),
            avg_win_pct=avg_win_pct,
            avg_loss_pct=avg_loss_pct,
            largest_win=largest_win,
            largest_loss=largest_loss,
            avg_drawdown=(
                np.mean([draw for draw in drawdown if draw < 0])
                if any(draw < 0 for draw in drawdown)
                else 0
            ),
            avg_drawdown_pct=(
                np.mean([draw * 100 for draw in drawdown if draw < 0])
                if any(draw < 0 for draw in drawdown)
                else 0
            ),
            var_95=var_95,
            var_99=var_99,
            skewness=skewness,
            kurtosis=kurtosis,
        )
