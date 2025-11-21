"""Performance metrics calculation for backtesting."""

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Dict, Optional

import numpy as np
import pandas as pd

if TYPE_CHECKING:
    from quantchain.backtesting.engine import BacktestResult


class InsufficientDataError(Exception):
    """Raised when insufficient data is provided for calculations."""

    pass


class LibraryImportError(Exception):
    """Raised when optional library is not available."""

    pass


class MissingColumnError(Exception):
    """Raised when a required column is missing from DataFrame."""

    pass


@dataclass
class MetricsResult:
    """Complete performance metrics result."""

    total_return: float
    annualized_return: float
    sharpe_ratio: float
    sortino_ratio: float
    calmar_ratio: float
    max_drawdown: float
    max_drawdown_duration: int
    max_drawdown_start: pd.Timestamp
    max_drawdown_end: pd.Timestamp
    volatility: float
    win_rate: float
    profit_factor: float
    total_trades: int
    winning_trades: int
    losing_trades: int
    avg_win: float
    avg_loss: float
    best_trade: float
    worst_trade: float
    avg_trade_duration: float
    avg_trade_duration_days: float
    sharpe_ratio_qstats: float
    sortino_ratio_qstats: float
    omega_ratio: float
    alpha: float
    beta: float
    information_ratio: float
    var_95: float


class PerformanceMetrics:
    """Calculate comprehensive performance metrics for backtest results."""

    def __init__(
        self,
        benchmark_returns: Optional[pd.Series] = None,
        risk_free_rate: float = 0.02,
    ):
        """Initialize with optional benchmark and risk-free rate."""
        self.benchmark_returns = benchmark_returns
        self.risk_free_rate = risk_free_rate

    def calculate_returns(
        self, equity_curve: pd.Series, frequency: str = "1d"
    ) -> pd.Series:
        """Calculate returns from equity curve."""
        if len(equity_curve) < 2:
            raise InsufficientDataError("Equity curve must have at least 2 points")

        returns = equity_curve.pct_change().dropna()
        return returns

    def calculate_total_return(self, equity_curve: pd.Series) -> float:
        """Calculate total return from equity curve."""
        if len(equity_curve) < 1:
            raise InsufficientDataError("Equity curve must have at least 1 point")

        return float((equity_curve.iloc[-1] / equity_curve.iloc[0]) - 1)

    def calculate_annualized_return(self, equity_curve: pd.Series) -> float:
        """Calculate annualized return."""
        total_return = self.calculate_total_return(equity_curve)

        # Get time period in years
        start_date = equity_curve.index[0]
        end_date = equity_curve.index[-1]

        # Handle both datetime and integer indices
        if hasattr(start_date, 'days') or hasattr(end_date, 'days'):
            # For timedelta objects
            years = ((end_date - start_date).days if hasattr(end_date - start_date, 'days') else (end_date - start_date)) / 365.25
        elif hasattr(start_date, 'day') and hasattr(end_date, 'day'):
            # For datetime objects
            years = (end_date - start_date).days / 365.25
        else:
            # For integer indices (assuming daily data)
            years = (end_date - start_date) / 365.25

        if years < 0.01:  # Less than about 3.6 days
            return 0.0

        # Annualized return = (1 + total_return)^(1/years) - 1
        return float(((1 + total_return) ** (1 / years)) - 1)

    def calculate_volatility(self, equity_curve: pd.Series) -> float:
        """Calculate volatility (annualized standard deviation of returns)."""
        returns = self.calculate_returns(equity_curve)
        return float(returns.std() * np.sqrt(252))  # Annualized (trading days)

    def calculate_sharpe_ratio(
        self, equity_curve: pd.Series, frequency: str = "1d"
    ) -> float:
        """Calculate Sharpe ratio with annualization."""
        returns = self.calculate_returns(equity_curve)

        # Annualized excess return
        annualized_return = self.calculate_annualized_return(equity_curve)
        excess_return = annualized_return - self.risk_free_rate

        # Annualized volatility
        volatility = self.calculate_volatility(equity_curve)

        if volatility == 0:
            return 0.0

        return excess_return / volatility

    def calculate_sortino_ratio(
        self, equity_curve: pd.Series, frequency: str = "1d"
    ) -> float:
        """Calculate Sortino ratio (downside deviation)."""
        returns = self.calculate_returns(equity_curve)

        # Calculate downside deviation (standard deviation of negative returns)
        negative_returns = returns[returns < 0]

        if len(negative_returns) == 0:
            return np.inf  # No downside risk

        downside_deviation = negative_returns.std() * np.sqrt(252)  # Annualized

        # Annualized return
        annualized_return = self.calculate_annualized_return(equity_curve)
        excess_return = annualized_return - self.risk_free_rate

        if downside_deviation == 0:
            return np.inf  # No downside risk

        return float(excess_return / downside_deviation)

    def calculate_max_drawdown(self, equity_curve: pd.Series) -> Dict[str, Any]:
        """Calculate maximum drawdown and duration."""
        # Calculate running maximum
        running_max = equity_curve.expanding().max()

        # Calculate drawdown
        drawdown = (equity_curve - running_max) / running_max

        # Maximum drawdown
        max_dd = drawdown.min()

        # Find the start and end dates of max drawdown
        max_dd_end = drawdown.idxmin()
        max_dd_start = equity_curve.loc[:max_dd_end].idxmax()

        # Calculate duration in days
        duration = (max_dd_end - max_dd_start).days if max_dd_start != max_dd_end else 0

        return {
            "max_drawdown": max_dd,
            "max_drawdown_duration": duration,
            "max_drawdown_start": max_dd_start,
            "max_drawdown_end": max_dd_end,
        }

    def calculate_max_drawdown_duration(self, equity_curve: pd.Series) -> int:
        """Calculate maximum drawdown duration in days."""
        # Calculate running maximum
        running_max = equity_curve.expanding().max()

        # Calculate drawdown
        drawdown = (equity_curve - running_max) / running_max

        # Find all drawdown periods
        in_drawdown = drawdown < 0

        # If no drawdown ever occurred
        if not in_drawdown.any():
            return 0

        # Find drawdown periods
        drawdown_starts = []
        drawdown_ends = []

        in_dd = False
        for i, dd in enumerate(in_drawdown):
            if dd and not in_dd:  # Drawdown starts
                drawdown_starts.append(equity_curve.index[i])
                in_dd = True
            elif not dd and in_dd:  # Drawdown ends
                drawdown_ends.append(equity_curve.index[i - 1])
                in_dd = False

        # If in drawdown at the end
        if in_dd:
            drawdown_ends.append(equity_curve.index[-1])

        # Calculate durations
        max_duration = 0
        for start, end in zip(drawdown_starts, drawdown_ends):
            duration = (end - start).days
            if duration > max_duration:
                max_duration = duration

        return max_duration

    def calculate_calmar_ratio(self, equity_curve: pd.Series) -> float:
        """Calculate Calmar ratio (annual return / max drawdown)."""
        annualized_return = self.calculate_annualized_return(equity_curve)

        max_dd_result = self.calculate_max_drawdown(equity_curve)
        max_dd = abs(max_dd_result["max_drawdown"])

        if max_dd == 0:
            return np.inf  # No drawdown

        return float(annualized_return / max_dd)

    def calculate_win_rate(self, trades: pd.DataFrame) -> float:
        """Calculate win rate from trade log."""
        if "pnl" not in trades.columns:
            raise MissingColumnError("Trade log must contain 'pnl' column")

        winning_trades = (trades["pnl"] > 0).sum()
        total_trades = len(trades)

        if total_trades == 0:
            return 0.0

        return float(winning_trades / total_trades)

    def calculate_profit_factor(self, trades: pd.DataFrame) -> float:
        """Calculate profit factor (gross profit / gross loss)."""
        if "pnl" not in trades.columns:
            raise MissingColumnError("Trade log must contain 'pnl' column")

        gross_profit = trades[trades["pnl"] > 0]["pnl"].sum()
        gross_loss = abs(trades[trades["pnl"] < 0]["pnl"].sum())

        if gross_loss == 0:
            return np.inf if gross_profit > 0 else 0.0

        return float(gross_profit / gross_loss)

    def calculate_average_win_loss(self, trades: pd.DataFrame) -> Dict[str, float]:
        """Calculate average win and loss amounts."""
        if "pnl" not in trades.columns:
            raise MissingColumnError("Trade log must contain 'pnl' column")

        winning_trades = trades[trades["pnl"] > 0]
        losing_trades = trades[trades["pnl"] < 0]

        avg_win = winning_trades["pnl"].mean() if len(winning_trades) > 0 else 0.0
        avg_loss = losing_trades["pnl"].mean() if len(losing_trades) > 0 else 0.0

        # Make avg_loss positive for easier interpretation
        avg_loss = abs(avg_loss) if avg_loss < 0 else avg_loss

        return {"avg_win": avg_win, "avg_loss": avg_loss}

    def calculate_best_worst_trade(self, trades: pd.DataFrame) -> Dict[str, float]:
        """Calculate best and worst trade values."""
        if "pnl" not in trades.columns:
            raise MissingColumnError("Trade log must contain 'pnl' column")

        if len(trades) == 0:
            return {"best_trade": 0.0, "worst_trade": 0.0}

        best_trade = trades["pnl"].max()
        worst_trade = trades["pnl"].min()

        return {"best_trade": best_trade, "worst_trade": worst_trade}

    def calculate_average_trade_duration(
        self, trades: pd.DataFrame
    ) -> Dict[str, float]:
        """Calculate average trade duration in days and seconds."""
        if "entry_time" not in trades.columns or "exit_time" not in trades.columns:
            raise MissingColumnError(
                "Trade log must contain 'entry_time' and 'exit_time' columns"
            )

        if len(trades) == 0:
            return {"avg_trade_duration": 0.0, "avg_trade_duration_days": 0.0}

        # Calculate duration for each trade
        durations = trades["exit_time"] - trades["entry_time"]

        # Average duration in seconds
        avg_duration_seconds = durations.total_seconds().mean()

        # Average duration in days
        avg_duration_days = durations.dt.days.mean()

        return {
            "avg_trade_duration": avg_duration_seconds,
            "avg_trade_duration_days": avg_duration_days,
        }

    def calculate_quantstats_metrics(self, returns: pd.Series) -> Dict[str, float]:
        """Calculate metrics using quantstats library if available."""
        metrics = {
            "sharpe_ratio_qstats": 0.0,
            "sortino_ratio_qstats": 0.0,
            "omega_ratio": 0.0,
        }

        try:
            import quantstats as qs

            # Calculate quantstats metrics
            metrics["sharpe_ratio_qstats"] = qs.stats.sharpe(returns)
            metrics["sortino_ratio_qstats"] = qs.stats.sortino(returns)
            metrics["omega_ratio"] = qs.stats.omega(returns)

        except (ImportError, LibraryImportError):
            # quantstats not available, return default values
            pass

        return metrics

    def calculate_beta_alpha(self, returns: pd.Series) -> Dict[str, float]:
        """Calculate alpha and beta against benchmark."""
        metrics = {"alpha": 0.0, "beta": 0.0, "information_ratio": 0.0}

        if self.benchmark_returns is None:
            return metrics

        # Align returns and benchmark
        aligned_returns, aligned_benchmark = returns.align(
            self.benchmark_returns, join="inner"
        )

        if len(aligned_returns) < 2:
            return metrics

        # Calculate beta and alpha
        covariance = np.cov(aligned_returns, aligned_benchmark)[0, 1]
        benchmark_variance = np.var(aligned_benchmark)

        if benchmark_variance == 0:
            return metrics

        beta = covariance / benchmark_variance

        # Annualized returns
        annualized_return = returns.mean() * 252  # Annualized
        annualized_benchmark = aligned_benchmark.mean() * 252  # Annualized

        alpha = annualized_return - (
            self.risk_free_rate + beta * (annualized_benchmark - self.risk_free_rate)
        )

        # Information ratio
        excess_returns = aligned_returns - aligned_benchmark
        tracking_error = np.std(excess_returns) * np.sqrt(252)

        information_ratio = (
            (excess_returns.mean() * 252) / tracking_error
            if tracking_error != 0
            else 0.0
        )

        return {"alpha": alpha, "beta": beta, "information_ratio": information_ratio}

    def calculate_var(self, returns: pd.Series, level: float = 0.05) -> float:
        """Calculate Value at Risk (VaR)."""
        return float(np.percentile(returns, level * 100))

    def generate_tear_sheet(
        self, results: "BacktestResult", save_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate comprehensive QuantStats tear sheet."""
        # This would typically use quantstats.reports.html() to generate a report
        # For now, return a simple dictionary with key metrics
        return {
            "message": "Tear sheet generation not fully implemented",
            "save_path": save_path,
        }

    def calculate_all_metrics(
        self, equity_curve: pd.Series, trades: pd.DataFrame, frequency: str = "1d"
    ) -> MetricsResult:
        """Calculate all metrics and return MetricsResult."""
        # Calculate returns
        returns = self.calculate_returns(equity_curve)

        # Calculate basic metrics
        total_return = self.calculate_total_return(equity_curve)
        annualized_return = self.calculate_annualized_return(equity_curve)
        sharpe_ratio = self.calculate_sharpe_ratio(equity_curve, frequency)
        sortino_ratio = self.calculate_sortino_ratio(equity_curve, frequency)
        volatility = self.calculate_volatility(equity_curve)

        # Calculate drawdown metrics
        max_dd_result = self.calculate_max_drawdown(equity_curve)
        max_drawdown = max_dd_result["max_drawdown"]
        max_drawdown_duration = max_dd_result["max_drawdown_duration"]
        max_drawdown_start = max_dd_result["max_drawdown_start"]
        max_drawdown_end = max_dd_result["max_drawdown_end"]

        # Calculate Calmar ratio
        calmar_ratio = self.calculate_calmar_ratio(equity_curve)

        # Calculate trade metrics
        win_rate = self.calculate_win_rate(trades)
        profit_factor = self.calculate_profit_factor(trades)
        avg_win_loss = self.calculate_average_win_loss(trades)
        best_worst = self.calculate_best_worst_trade(trades)
        avg_duration = self.calculate_average_trade_duration(trades)

        # Calculate advanced metrics
        quantstats_metrics = self.calculate_quantstats_metrics(returns)
        beta_alpha = self.calculate_beta_alpha(returns)
        var_95 = self.calculate_var(returns, 0.05)

        # Count trades
        total_trades = len(trades)
        winning_trades = (
            len(trades[trades["pnl"] > 0]) if "pnl" in trades.columns else 0
        )
        losing_trades = len(trades[trades["pnl"] < 0]) if "pnl" in trades.columns else 0

        return MetricsResult(
            total_return=total_return,
            annualized_return=annualized_return,
            sharpe_ratio=sharpe_ratio,
            sortino_ratio=sortino_ratio,
            calmar_ratio=calmar_ratio,
            max_drawdown=max_drawdown,
            max_drawdown_duration=max_drawdown_duration,
            max_drawdown_start=max_drawdown_start,
            max_drawdown_end=max_drawdown_end,
            volatility=volatility,
            win_rate=win_rate,
            profit_factor=profit_factor,
            total_trades=total_trades,
            winning_trades=winning_trades,
            losing_trades=losing_trades,
            avg_win=avg_win_loss["avg_win"],
            avg_loss=avg_win_loss["avg_loss"],
            best_trade=best_worst["best_trade"],
            worst_trade=best_worst["worst_trade"],
            avg_trade_duration=avg_duration["avg_trade_duration"],
            avg_trade_duration_days=avg_duration["avg_trade_duration_days"],
            sharpe_ratio_qstats=quantstats_metrics["sharpe_ratio_qstats"],
            sortino_ratio_qstats=quantstats_metrics["sortino_ratio_qstats"],
            omega_ratio=quantstats_metrics["omega_ratio"],
            alpha=beta_alpha["alpha"],
            beta=beta_alpha["beta"],
            information_ratio=beta_alpha["information_ratio"],
            var_95=var_95,
        )
