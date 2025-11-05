"""
Performance metrics calculation using QuantStats and Empyrical libraries.
"""

from typing import Dict, Any, Optional
import pandas as pd
import numpy as np

# Import from engine for type annotations
from .engine import BacktestResult, MetricsResult

# Try to import optional libraries
try:
    import quantstats as qs

    QUANTSTATS_AVAILABLE = True
except ImportError:
    QUANTSTATS_AVAILABLE = False
    qs = None

try:
    import empyrical

    EMPYRICAL_AVAILABLE = True
except ImportError:
    EMPYRICAL_AVAILABLE = False
    empyrical = None


# Custom Exceptions
class InsufficientDataError(Exception):
    """Raised when there's insufficient data for calculation."""

    pass


class InvalidFrequencyError(Exception):
    """Raised for unsupported data frequencies."""

    pass


class MissingColumnError(Exception):
    """Raised when required columns are missing from trade data."""

    pass


class MetricsCalculationError(Exception):
    """Raised for general calculation failures."""

    pass


class LibraryImportError(Exception):
    """Raised when required libraries are not available."""

    pass


class PerformanceMetrics:
    """Calculate comprehensive performance metrics for backtest results."""

    def __init__(
        self,
        benchmark_returns: Optional[pd.Series] = None,
        risk_free_rate: float = 0.02,
    ):
        """
        Initialize with optional benchmark and risk-free rate.

        Args:
            benchmark_returns: Optional benchmark returns series
            risk_free_rate: Annual risk-free rate (default: 2%)
        """
        self.benchmark_returns = benchmark_returns
        self.risk_free_rate = risk_free_rate

    def calculate_returns(
        self, equity_curve: pd.Series, frequency: str = "1d"
    ) -> pd.Series:
        """
        Calculate returns from equity curve.

        Args:
            equity_curve: Portfolio value over time
            frequency: Data frequency ('1m', '5m', '1h', '1d')

        Returns:
            pd.Series: Returns series with same index as equity_curve

        Raises:
            InsufficientDataError: If equity_curve is empty or has insufficient data
        """
        if len(equity_curve) < 2:
            raise InsufficientDataError("Equity curve must have at least 2 points")

        try:
            return equity_curve.pct_change().dropna()
        except Exception as e:
            raise MetricsCalculationError(f"Failed to calculate returns: {e}") from e

    def calculate_total_return(self, equity_curve: pd.Series) -> float:
        """
        Calculate total return over the entire period.

        Args:
            equity_curve: Portfolio value over time

        Returns:
            float: Total return as decimal (0.1 = 10%)
        """
        if len(equity_curve) < 2:
            return 0.0

        try:
            if equity_curve.isnull().any() or np.isinf(equity_curve).any():
                raise ValueError(
                    "Equity curve contains invalid values (NaN or infinity)"
                )
            return float(equity_curve.iloc[-1] / equity_curve.iloc[0]) - 1
        except Exception as e:
            raise MetricsCalculationError(
                f"Failed to calculate total return: {e}"
            ) from e

    def calculate_annualized_return(
        self, returns: pd.Series, frequency: str = "1d"
    ) -> float:
        """
        Calculate annualized return.

        Args:
            returns: Returns series
            frequency: Data frequency for annualization

        Returns:
            float: Annualized return as decimal
        """
        if len(returns) == 0:
            return 0.0

        try:
            total_return = (1 + returns).prod() - 1

            # Calculate time period in years
            time_period = (returns.index[-1] - returns.index[0]).days / 365.25

            if time_period == 0:
                return float(total_return)

            return float((1 + total_return) ** (1 / time_period) - 1)
        except Exception as e:
            raise MetricsCalculationError(
                f"Failed to calculate annualized return: {e}"
            ) from e

    def calculate_sharpe_ratio(
        self, returns: pd.Series, frequency: str = "1d"
    ) -> float:
        """
        Calculate Sharpe ratio: (return - risk_free_rate) / volatility

        Args:
            returns: Returns series
            frequency: Data frequency for annualization

        Returns:
            float: Sharpe ratio
        """
        if len(returns) == 0:
            return 0.0

        try:
            # Annualization factor
            freq_map = {"1m": 525600, "5m": 105120, "1h": 8760, "1d": 252}

            if frequency not in freq_map:
                raise InvalidFrequencyError(f"Unsupported frequency: {frequency}")

            annual_factor = freq_map[frequency]

            # Annualized return and volatility
            annual_return = float(returns.mean() * annual_factor)
            annual_volatility = float(returns.std() * np.sqrt(annual_factor))

            if annual_volatility <= 1e-10:
                return 0.0

            # Risk-free rate is already annual
            excess_return = annual_return - self.risk_free_rate
            return float(excess_return / annual_volatility)
        except Exception as e:
            if isinstance(e, (InvalidFrequencyError, MetricsCalculationError)):
                raise
            raise MetricsCalculationError(
                f"Failed to calculate Sharpe ratio: {e}"
            ) from e

    def calculate_sortino_ratio(
        self, returns: pd.Series, frequency: str = "1d"
    ) -> float:
        """
        Calculate Sortino ratio using downside deviation.

        Args:
            returns: Returns series
            frequency: Data frequency for annualization

        Returns:
            float: Sortino ratio
        """
        if len(returns) == 0:
            return 0.0

        try:
            # Annualization factor
            freq_map = {"1m": 525600, "5m": 105120, "1h": 8760, "1d": 252}

            if frequency not in freq_map:
                raise InvalidFrequencyError(f"Unsupported frequency: {frequency}")

            annual_factor = freq_map[frequency]

            # Annualized return
            annual_return = float(returns.mean() * annual_factor)

            # Downside deviation (only negative returns)
            downside_returns = returns[returns < 0]
            if len(downside_returns) == 0:
                return float("inf") if annual_return > self.risk_free_rate else 0.0

            downside_volatility = float(downside_returns.std() * np.sqrt(annual_factor))

            if downside_volatility == 0:
                return 0.0

            excess_return = annual_return - self.risk_free_rate
            return float(excess_return / downside_volatility)
        except Exception as e:
            if isinstance(e, (InvalidFrequencyError, MetricsCalculationError)):
                raise
            raise MetricsCalculationError(
                f"Failed to calculate Sortino ratio: {e}"
            ) from e

    def calculate_max_drawdown(self, equity_curve: pd.Series) -> Dict[str, Any]:
        """
        Calculate maximum drawdown and related metrics.

        Args:
            equity_curve: Portfolio value over time

        Returns:
            Dict with max_drawdown, duration, start_date, end_date
        """
        if len(equity_curve) < 2:
            return {
                "max_drawdown": 0.0,
                "max_drawdown_duration": 0,
                "max_drawdown_start": None,
                "max_drawdown_end": None,
            }

        try:
            # Calculate running maximum
            running_max = equity_curve.expanding().max()

            # Calculate drawdown
            drawdown = (equity_curve - running_max) / running_max
            max_dd = drawdown.min()

            # Find drawdown periods
            drawdown_periods = []
            in_drawdown = False
            start_idx = None

            for i, dd in enumerate(drawdown):
                if dd < -0.001 and not in_drawdown:  # Start of drawdown
                    in_drawdown = True
                    start_idx = i
                elif dd >= -0.001 and in_drawdown:  # End of drawdown
                    in_drawdown = False
                    end_idx = i
                    duration = end_idx - (start_idx or 0)
                    drawdown_periods.append((start_idx or 0, end_idx, duration))

            # Handle ongoing drawdown
            if in_drawdown:
                end_idx = len(drawdown) - 1
                duration = end_idx - (start_idx or 0)
                drawdown_periods.append((start_idx or 0, end_idx, duration))

            # Find max duration
            max_duration = max((d[2] for d in drawdown_periods), default=0)

            # Find dates for max drawdown
            max_dd_idx = drawdown.idxmin()
            max_dd_start_date = None
            max_dd_end_date = None

            # Convert index to positional index for comparison
            max_dd_pos = drawdown.index.get_loc(max_dd_idx)

            if max_dd_pos >= 0:
                for start_idx, end_idx, _ in drawdown_periods:
                    if start_idx <= max_dd_pos <= end_idx:
                        max_dd_start_date = equity_curve.index[start_idx]
                        max_dd_end_date = equity_curve.index[end_idx]
                        break

            return {
                "max_drawdown": abs(max_dd),
                "max_drawdown_duration": max_duration,
                "max_drawdown_start": max_dd_start_date,
                "max_drawdown_end": max_dd_end_date,
            }
        except Exception as e:
            raise MetricsCalculationError(
                f"Failed to calculate max drawdown: {e}"
            ) from e

    def calculate_calmar_ratio(self, returns: pd.Series, max_drawdown: float) -> float:
        """
        Calculate Calmar ratio (annual return / max drawdown).

        Args:
            returns: Returns series
            max_drawdown: Maximum drawdown as positive decimal

        Returns:
            float: Calmar ratio
        """
        if max_drawdown == 0:
            return 0.0 if len(returns) == 0 else float("inf")

        try:
            annual_return = self.calculate_annualized_return(returns)
            return annual_return / max_drawdown
        except Exception as e:
            raise MetricsCalculationError(
                f"Failed to calculate Calmar ratio: {e}"
            ) from e

    def calculate_win_rate(self, trades: pd.DataFrame) -> float:
        """
        Calculate win rate from trade log.

        Args:
            trades: Trade log with columns including 'pnl'

        Returns:
            float: Win rate (0.0 to 1.0)
        """
        if len(trades) == 0:
            return 0.0

        if "pnl" not in trades.columns:
            raise MissingColumnError("Trade log must contain 'pnl' column")

        try:
            winning_trades = trades[trades["pnl"] > 0]
            return len(winning_trades) / len(trades)
        except Exception as e:
            raise MetricsCalculationError(f"Failed to calculate win rate: {e}") from e

    def calculate_profit_factor(self, trades: pd.DataFrame) -> float:
        """
        Calculate profit factor: gross profit / gross loss.

        Args:
            trades: Trade log with columns including 'pnl'

        Returns:
            float: Profit factor
        """
        if len(trades) == 0:
            return 0.0

        if "pnl" not in trades.columns:
            raise MissingColumnError("Trade log must contain 'pnl' column")

        try:
            gross_profit = trades[trades["pnl"] > 0]["pnl"].sum()
            gross_loss = abs(trades[trades["pnl"] < 0]["pnl"].sum())

            return gross_profit / gross_loss if gross_loss > 0 else float("inf")
        except Exception as e:
            raise MetricsCalculationError(
                f"Failed to calculate profit factor: {e}"
            ) from e

    def generate_tear_sheet(
        self, results: "BacktestResult", save_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate comprehensive QuantStats tear sheet.

        Args:
            results: BacktestResult object
            save_path: Optional path to save HTML tear sheet

        Returns:
            Dict: QuantStats metrics and analysis

        Raises:
            LibraryImportError: If QuantStats is not available
        """
        if not QUANTSTATS_AVAILABLE:
            raise LibraryImportError("QuantStats is required for tear sheet generation")

        try:
            returns = self.calculate_returns(results.equity_curve)

            # Generate basic stats
            stats = qs.reports.metrics(returns, mode="basic")

            # Generate HTML report if save path provided
            if save_path:
                qs.reports.html(returns, output=save_path, title="Backtest Analysis")

            # Generate full stats if benchmark available
            if self.benchmark_returns is not None:
                full_stats = qs.reports.metrics(
                    returns, mode="full", benchmark=self.benchmark_returns
                )
                return {"basic_stats": stats, "full_stats": full_stats}

            return {"basic_stats": stats}
        except Exception as e:
            if isinstance(e, LibraryImportError):
                raise
            raise MetricsCalculationError(f"Failed to generate tear sheet: {e}") from e

    def calculate_empyrical_metrics(self, returns: pd.Series) -> Dict[str, float]:
        """
        Calculate Empyrical risk metrics.

        Args:
            returns: Returns series

        Returns:
            Dict: Empyrical metrics

        Raises:
            LibraryImportError: If Empyrical is not available
        """
        if not EMPYRICAL_AVAILABLE:
            raise LibraryImportError("Empyrical is required for advanced risk metrics")

        try:
            metrics = {}

            # Alpha and Beta (if benchmark available)
            if self.benchmark_returns is not None:
                metrics["alpha"] = empyrical.alpha(returns, self.benchmark_returns)
                metrics["beta"] = empyrical.beta(returns, self.benchmark_returns)
                metrics["information_ratio"] = empyrical.information_ratio(
                    returns, self.benchmark_returns
                )

            # Value at Risk
            metrics["var_95"] = empyrical.value_at_risk(returns, 0.05)
            metrics["cvar_95"] = empyrical.conditional_value_at_risk(returns, 0.05)

            # Other risk metrics
            metrics["omega_ratio"] = empyrical.omega_ratio(returns)
            metrics["skewness"] = empyrical.stats.skew(returns)
            metrics["kurtosis"] = empyrical.stats.kurtosis(returns)

            return metrics
        except Exception as e:
            if isinstance(e, LibraryImportError):
                raise
            raise MetricsCalculationError(
                f"Failed to calculate Empyrical metrics: {e}"
            ) from e

    def calculate_all_metrics(
        self, equity_curve: pd.Series, trades: pd.DataFrame, frequency: str = "1d"
    ) -> "MetricsResult":
        """
        Calculate all metrics and return MetricsResult.

        Args:
            equity_curve: Portfolio equity over time
            trades: Trade log DataFrame
            frequency: Data frequency

        Returns:
            MetricsResult: Complete performance metrics
        """
        try:
            # Basic returns
            returns = self.calculate_returns(equity_curve, frequency)
            total_return = self.calculate_total_return(equity_curve)
            annualized_return = self.calculate_annualized_return(returns, frequency)

            # Risk metrics
            sharpe_ratio = self.calculate_sharpe_ratio(returns, frequency)
            sortino_ratio = self.calculate_sortino_ratio(returns, frequency)

            drawdown_info = self.calculate_max_drawdown(equity_curve)
            max_drawdown = drawdown_info["max_drawdown"]
            max_drawdown_duration = drawdown_info["max_drawdown_duration"]
            max_drawdown_start = drawdown_info["max_drawdown_start"]
            max_drawdown_end = drawdown_info["max_drawdown_end"]

            calmar_ratio = self.calculate_calmar_ratio(returns, max_drawdown)
            volatility = returns.std() * np.sqrt(252)  # Annualized

            # Trade-based metrics
            win_rate = self.calculate_win_rate(trades) if len(trades) > 0 else 0.0
            profit_factor = (
                self.calculate_profit_factor(trades) if len(trades) > 0 else 0.0
            )

            # Trade statistics
            if len(trades) > 0 and "pnl" in trades.columns:
                total_trades = len(trades)
                winning_trades = len(trades[trades["pnl"] > 0])
                losing_trades = len(trades[trades["pnl"] < 0])

                winning_pnls = trades[trades["pnl"] > 0]["pnl"]
                losing_pnls = trades[trades["pnl"] < 0]["pnl"]

                avg_win = winning_pnls.mean() if len(winning_pnls) > 0 else 0.0
                avg_loss = losing_pnls.mean() if len(losing_pnls) > 0 else 0.0
                best_trade = trades["pnl"].max()
                worst_trade = trades["pnl"].min()

                # Trade duration
                if "entry_time" in trades.columns and "exit_time" in trades.columns:
                    trade_durations = (
                        trades["exit_time"] - trades["entry_time"]
                    ).dt.total_seconds() / 3600
                    avg_trade_duration = trade_durations.mean()
                    avg_trade_duration_days = avg_trade_duration / 24
                else:
                    avg_trade_duration = 0.0
                    avg_trade_duration_days = 0.0
            else:
                total_trades = winning_trades = losing_trades = 0
                avg_win = avg_loss = best_trade = worst_trade = 0.0
                avg_trade_duration = avg_trade_duration_days = 0.0

            # QuantStats metrics
            sharpe_ratio_qstats = 0.0
            sortino_ratio_qstats = 0.0
            if QUANTSTATS_AVAILABLE:
                try:
                    sharpe_ratio_qstats = qs.stats.sharpe(returns)
                    sortino_ratio_qstats = qs.stats.sortino(returns)
                except Exception:
                    pass  # Use calculated values if QuantStats fails

            # Empyrical metrics
            omega_ratio = alpha = beta = information_ratio = 0.0
            var_95 = cvar_95 = skewness = kurtosis = 0.0

            try:
                emp_metrics = self.calculate_empyrical_metrics(returns)
                omega_ratio = emp_metrics.get("omega_ratio", 0.0)
                alpha = emp_metrics.get("alpha", 0.0)
                beta = emp_metrics.get("beta", 0.0)
                information_ratio = emp_metrics.get("information_ratio", 0.0)
                var_95 = emp_metrics.get("var_95", 0.0)
                cvar_95 = emp_metrics.get("cvar_95", 0.0)
                skewness = emp_metrics.get("skewness", 0.0)
                kurtosis = emp_metrics.get("kurtosis", 0.0)
            except Exception:
                pass  # Use zero values if Empyrical fails or not available

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
                avg_win=avg_win,
                avg_loss=avg_loss,
                best_trade=best_trade,
                worst_trade=worst_trade,
                avg_trade_duration=avg_trade_duration,
                avg_trade_duration_days=avg_trade_duration_days,
                sharpe_ratio_qstats=sharpe_ratio_qstats,
                sortino_ratio_qstats=sortino_ratio_qstats,
                omega_ratio=omega_ratio,
                alpha=alpha,
                beta=beta,
                information_ratio=information_ratio,
                var_95=var_95,
                cvar_95=cvar_95,
                skewness=skewness,
                kurtosis=kurtosis,
                additional_metrics={},
            )
        except Exception as e:
            if isinstance(e, MetricsCalculationError):
                raise
            raise MetricsCalculationError(
                f"Failed to calculate all metrics: {e}"
            ) from e
