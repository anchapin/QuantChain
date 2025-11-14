"""
Performance metrics calculation using QuantStats and Empyrical libraries.
"""

from typing import Any, Dict, Optional

import numpy as np
import pandas as pd

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


class InvalidFrequencyError(Exception):
    """Raised for unsupported data frequencies."""


class MissingColumnError(Exception):
    """Raised when required columns are missing from trade data."""


class MetricsCalculationError(Exception):
    """Raised for general calculation failures."""


class LibraryImportError(Exception):
    """Raised when required libraries are not available."""


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
            # Handle pandas version compatibility for pct_change
            # In pandas 2.1.0+, fill_method is deprecated and should be None
            return equity_curve.pct_change(fill_method=None).dropna()
        except Exception as e:
            raise MetricsCalculationError(f"Failed to calculate returns: {e}") from e

    def calculate_max_drawdown_duration(self, equity_curve: pd.Series) -> int:
        """
        Calculate maximum drawdown duration.

        Args:
            equity_curve: Portfolio value over time

        Returns:
            Maximum drawdown duration in periods
        """
        result = self.calculate_max_drawdown(equity_curve)
        return result.get("max_drawdown_duration", 0)

    def calculate_calmar_ratio(
        self, equity_curve: pd.Series, max_drawdown: Optional[float] = None
    ) -> float:
        """
        Calculate Calmar ratio (annual return / max drawdown).

        Args:
            equity_curve: Portfolio value over time
            max_drawdown: Maximum drawdown as positive decimal (optional, will be calculated if not provided)

        Returns:
            float: Calmar ratio
        """
        if max_drawdown is None:
            max_drawdown_info = self.calculate_max_drawdown(equity_curve)
            max_drawdown = max_drawdown_info.get("max_drawdown", 0.0)

        returns = self.calculate_returns(equity_curve)

        if max_drawdown == 0:
            return 0.0 if len(returns) == 0 else float("inf")

        try:
            annual_return = self.calculate_annualized_return(equity_curve)
            return annual_return / max_drawdown
        except Exception as e:
            raise MetricsCalculationError(
                f"Failed to calculate Calmar ratio: {e}"
            ) from e

    def calculate_total_return(self, equity_curve: pd.Series) -> float:
        """
        Calculate total return over the entire period.

        Args:
            equity_curve: Portfolio value over time

        Returns:
            Total return as a percentage (decimal)
        """
        if len(equity_curve) < 1:
            raise InsufficientDataError("Equity curve must have at least 1 point")

        if len(equity_curve) == 1:
            return 0.0

        try:
            total_return = (equity_curve.iloc[-1] / equity_curve.iloc[0]) - 1
            return total_return
        except Exception as e:
            raise MetricsCalculationError(
                f"Failed to calculate total return: {e}"
            ) from e
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
            raise MissingColumnError("Required column 'pnl' not found")

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

    def calculate_average_trade(self, trades: pd.DataFrame) -> float:
        """
        Calculate average trade P&L.

        Args:
            trades: Trade log with columns including 'pnl'

        Returns:
            float: Average trade P&L
        """
        if len(trades) == 0:
            return 0.0

        if "pnl" not in trades.columns:
            raise MissingColumnError("Required column 'pnl' not found")

        try:
            return trades["pnl"].mean()
        except Exception as e:
            raise MetricsCalculationError(
                f"Failed to calculate average trade: {e}"
            ) from e

    def calculate_total_trades(self, trades: pd.DataFrame) -> int:
        """
        Calculate total number of trades.

        Args:
            trades: Trade log DataFrame

        Returns:
            int: Number of trades
        """
        return len(trades)

    def calculate_largest_win(self, trades: pd.DataFrame) -> float:
        """
        Calculate largest winning trade.

        Args:
            trades: Trade log with columns including 'pnl'

        Returns:
            float: Largest winning trade P&L
        """
        if len(trades) == 0:
            return 0.0

        if "pnl" not in trades.columns:
            raise KeyError("Trade log must contain 'pnl' column")

        try:
            winning_trades = trades[trades["pnl"] > 0]["pnl"]
            return winning_trades.max() if len(winning_trades) > 0 else 0.0
        except Exception as e:
            raise MetricsCalculationError(
                f"Failed to calculate largest win: {e}"
            ) from e

    def calculate_largest_loss(self, trades: pd.DataFrame) -> float:
        """
        Calculate largest losing trade.

        Args:
            trades: Trade log with columns including 'pnl'

        Returns:
            float: Largest losing trade P&L (as a positive number)
        """
        if len(trades) == 0:
            return 0.0

        if "pnl" not in trades.columns:
            raise MissingColumnError("Required column 'pnl' not found")

        try:
            losing_trades = trades[trades["pnl"] < 0]["pnl"]
            return abs(losing_trades.min()) if len(losing_trades) > 0 else 0.0
        except Exception as e:
            raise MetricsCalculationError(
                f"Failed to calculate largest loss: {e}"
            ) from e

    def calculate_average_win(self, trades: pd.DataFrame) -> float:
        """
        Calculate average winning trade.

        Args:
            trades: Trade log with columns including 'pnl'

        Returns:
            float: Average winning trade P&L
        """
        if len(trades) == 0:
            return 0.0

        if "pnl" not in trades.columns:
            raise MissingColumnError("Required column 'pnl' not found")

        try:
            winning_trades = trades[trades["pnl"] > 0]["pnl"]
            return winning_trades.mean() if len(winning_trades) > 0 else 0.0
        except Exception as e:
            raise MetricsCalculationError(
                f"Failed to calculate average win: {e}"
            ) from e

    def calculate_average_loss(self, trades: pd.DataFrame) -> float:
        """
        Calculate average losing trade.

        Args:
            trades: Trade log with columns including 'pnl'

        Returns:
            float: Average losing trade P&L (as a positive number)
        """
        if len(trades) == 0:
            return 0.0

        if "pnl" not in trades.columns:
            raise MissingColumnError("Required column 'pnl' not found")

        try:
            losing_trades = trades[trades["pnl"] < 0]["pnl"]
            return abs(losing_trades.mean()) if len(losing_trades) > 0 else 0.0
        except Exception as e:
            raise MetricsCalculationError(
                f"Failed to calculate average loss: {e}"
            ) from e

    def calculate_win_loss_ratio(self, trades: pd.DataFrame) -> float:
        """
        Calculate win/loss ratio: average win / average loss.

        Args:
            trades: Trade log with columns including 'pnl'

        Returns:
            float: Win/loss ratio
        """
        if len(trades) == 0:
            return 0.0

        if "pnl" not in trades.columns:
            raise MissingColumnError("Required column 'pnl' not found")

        try:
            winning_trades = trades[trades["pnl"] > 0]["pnl"]
            losing_trades = trades[trades["pnl"] < 0]["pnl"]

            if len(winning_trades) == 0 or len(losing_trades) == 0:
                return 0.0

            avg_win = winning_trades.mean()
            avg_loss = abs(losing_trades.mean())

            return avg_win / avg_loss if avg_loss > 0 else float("inf")
        except Exception as e:
            raise MetricsCalculationError(
                f"Failed to calculate win/loss ratio: {e}"
            ) from e

    def calculate_var(
        self, returns: pd.Series, confidence_level: float = 0.95
    ) -> float:
        """
        Calculate Value at Risk (VaR).

        Args:
            returns: Returns series (equity curve returns, not equity curve values)
            confidence_level: Confidence level for VaR (0.0 to 1.0)

        Returns:
            float: VaR at the specified confidence level (negative value representing loss)
        """
        if len(returns) < 2:
            return 0.0

        if not 0 < confidence_level < 1:
            raise ValueError("Confidence level must be between 0 and 1")

        try:
            # Calculate returns from equity curve if not already returns
            if "returns" not in locals():
                returns = (
                    self.calculate_returns(returns)
                    if len(returns) > 1
                    else pd.Series([0.0])
                )

            # Calculate VaR at the specified confidence level
            var = np.percentile(returns, (1 - confidence_level) * 100)
            return var
        except Exception as e:
            raise MetricsCalculationError(f"Failed to calculate VaR: {e}") from e

    def calculate_cvar(
        self, returns: pd.Series, confidence_level: float = 0.95
    ) -> float:
        """
        Calculate Conditional Value at Risk (CVaR).

        Args:
            returns: Returns series (equity curve returns, not equity curve values)
            confidence_level: Confidence level for CVaR (0.0 to 1.0)

        Returns:
            float: CVaR at the specified confidence level (negative value representing loss)
        """
        if len(returns) < 2:
            return 0.0

        if not 0 < confidence_level < 1:
            raise ValueError("Confidence level must be between 0 and 1")

        try:
            # Calculate returns from equity curve if not already returns
            if "returns" not in locals():
                returns = (
                    self.calculate_returns(returns)
                    if len(returns) > 1
                    else pd.Series([0.0])
                )

            # Calculate VaR at the specified confidence level
            var = self.calculate_var(returns, confidence_level)

            # Calculate CVaR as the mean of returns beyond the VaR threshold
            cvar = returns[returns <= var].mean()
            return cvar
        except Exception as e:
            raise MetricsCalculationError(f"Failed to calculate CVaR: {e}") from e

    def calculate_beta(self, equity_curve: pd.Series) -> float:
        """
        Calculate beta relative to benchmark.

        Args:
            equity_curve: Portfolio equity curve

        Returns:
            float: Beta coefficient
        """
        if len(equity_curve) < 2:
            return 0.0

        if self.benchmark_returns is None or len(self.benchmark_returns) < 2:
            raise ValueError("Benchmark returns required for beta calculation")

        try:
            # Calculate returns for both equity curve and benchmark
            returns = self.calculate_returns(equity_curve)

            # Align the returns series (make sure they have the same length)
            min_len = min(len(returns), len(self.benchmark_returns))
            returns = returns.iloc[:min_len]
            benchmark_aligned = self.benchmark_returns.iloc[:min_len]

            # Calculate covariance and variance
            covariance = np.cov(returns, benchmark_aligned)[0, 1]
            variance = np.var(benchmark_aligned)

            # Return 0 if variance is 0 to avoid division by zero
            return covariance / variance if variance > 0 else 0.0
        except Exception as e:
            raise MetricsCalculationError(f"Failed to calculate beta: {e}") from e

    def calculate_alpha(self, equity_curve: pd.Series) -> float:
        """
        Calculate alpha relative to benchmark and risk-free rate.

        Args:
            equity_curve: Portfolio equity curve

        Returns:
            float: Alpha coefficient
        """
        if len(equity_curve) < 2:
            return 0.0

        if self.benchmark_returns is None or len(self.benchmark_returns) < 2:
            raise ValueError("Benchmark returns required for alpha calculation")

        try:
            # Calculate returns for both equity curve and benchmark
            returns = self.calculate_returns(equity_curve)
            portfolio_annual_return = self.calculate_annualized_return(equity_curve)

            # Calculate benchmark annual return
            benchmark_annual_return = self.calculate_annualized_return(
                (1 + self.benchmark_returns).cumprod()
            )

            # Calculate beta
            beta = self.calculate_beta(equity_curve)

            # Calculate alpha using CAPM: alpha = portfolio_return - (risk_free_rate + beta * (benchmark_return - risk_free_rate))
            alpha = portfolio_annual_return - (
                self.risk_free_rate
                + beta * (benchmark_annual_return - self.risk_free_rate)
            )

            return alpha
        except Exception as e:
            raise MetricsCalculationError(f"Failed to calculate alpha: {e}") from e

    def calculate_information_ratio(self, equity_curve: pd.Series) -> float:
        """
        Calculate information ratio: excess return / tracking error.

        Args:
            equity_curve: Portfolio equity curve

        Returns:
            float: Information ratio
        """
        if len(equity_curve) < 2:
            return 0.0

        if self.benchmark_returns is None or len(self.benchmark_returns) < 2:
            raise ValueError(
                "Benchmark returns required for information ratio calculation"
            )

        try:
            # Calculate returns for both equity curve and benchmark
            returns = self.calculate_returns(equity_curve)

            # Align the returns series
            min_len = min(len(returns), len(self.benchmark_returns))
            returns = returns.iloc[:min_len]
            benchmark_aligned = self.benchmark_returns.iloc[:min_len]

            # Calculate active returns (excess returns over benchmark)
            active_returns = returns - benchmark_aligned

            # Calculate mean of active returns
            mean_active_return = active_returns.mean()

            # Calculate tracking error (standard deviation of active returns)
            tracking_error = active_returns.std()

            # Information ratio is active return / tracking error
            return mean_active_return / tracking_error if tracking_error > 0 else 0.0
        except Exception as e:
            raise MetricsCalculationError(
                f"Failed to calculate information ratio: {e}"
            ) from e

    def calculate_volatility(self, equity_curve: pd.Series) -> float:
        """
        Calculate volatility (standard deviation of returns).

        Args:
            equity_curve: Portfolio equity curve

        Returns:
            float: Volatility (standard deviation of returns)
        """
        if len(equity_curve) < 2:
            raise InsufficientDataError(
                "Equity curve must have at least 2 points for volatility calculation"
            )

        try:
            returns = self.calculate_returns(equity_curve)
            return returns.std()
        except Exception as e:
            raise MetricsCalculationError(f"Failed to calculate volatility: {e}") from e

    def calculate_quantstats_metrics(self, equity_curve: pd.Series) -> Dict[str, Any]:
        """
        Calculate QuantStats metrics.

        Args:
            equity_curve: Portfolio equity curve

        Returns:
            Dict with QuantStats metrics

        Raises:
            Exception: When QuantStats library is not available
        """
        if not QUANTSTATS_AVAILABLE:
            raise LibraryImportError("QuantStats library is not available")

        try:
            # Use QuantStats to calculate metrics
            if hasattr(qs, "reports"):
                return qs.reports.metrics(equity_curve)
            else:
                # Fallback to basic implementation
                return {
                    "sharpe_ratio": self.calculate_sharpe_ratio(equity_curve),
                    "max_drawdown": self.calculate_max_drawdown(equity_curve)[
                        "max_drawdown"
                    ],
                    "volatility": self.calculate_volatility(equity_curve),
                }
        except Exception as e:
            raise MetricsCalculationError(
                f"Failed to calculate QuantStats metrics: {e}"
            ) from e

    def calculate_comprehensive_metrics(
        self, equity_curve: pd.Series, trades: Optional[pd.DataFrame] = None
    ) -> Dict[str, Any]:
        """
        Calculate comprehensive metrics including returns, risk, and trade statistics.

        Args:
            equity_curve: Portfolio equity curve
            trades: Trade log DataFrame (optional)

        Returns:
            Dict with comprehensive metrics organized by category
        """
        try:
            comprehensive_metrics = {
                "return_metrics": {
                    "total_return": self.calculate_total_return(equity_curve),
                    "annualized_return": self.calculate_annualized_return(equity_curve),
                    "sharpe_ratio": self.calculate_sharpe_ratio(equity_curve),
                    "sortino_ratio": self.calculate_sortino_ratio(equity_curve),
                    "calmar_ratio": self.calculate_calmar_ratio(equity_curve),
                },
                "risk_metrics": {
                    "max_drawdown": self.calculate_max_drawdown(equity_curve)[
                        "max_drawdown"
                    ],
                    "max_drawdown_duration": self.calculate_max_drawdown_duration(
                        equity_curve
                    ),
                    "var_95": self.calculate_var(equity_curve, confidence_level=0.95),
                    "cvar_95": self.calculate_cvar(equity_curve, confidence_level=0.95),
                },
            }

            # Add trade metrics if trades are provided
            if trades is not None:
                comprehensive_metrics["trade_metrics"] = {
                    "total_trades": self.calculate_total_trades(trades),
                    "win_rate": self.calculate_win_rate(trades),
                    "profit_factor": self.calculate_profit_factor(trades),
                    "average_trade": self.calculate_average_trade(trades),
                    "largest_win": self.calculate_largest_win(trades),
                    "largest_loss": self.calculate_largest_loss(trades),
                    "win_loss_ratio": self.calculate_win_loss_ratio(trades),
                }

            # Add benchmark metrics if available
            if self.benchmark_returns is not None:
                comprehensive_metrics["benchmark_metrics"] = {
                    "alpha": self.calculate_alpha(equity_curve),
                    "beta": self.calculate_beta(equity_curve),
                    "information_ratio": self.calculate_information_ratio(equity_curve),
                }

            return comprehensive_metrics
        except Exception as e:
            raise MetricsCalculationError(
                f"Failed to calculate comprehensive metrics: {e}"
            ) from e

    def generate_metrics_report(
        self, equity_curve: pd.Series, trades: Optional[pd.DataFrame] = None
    ) -> str:
        """
        Generate a formatted metrics report.

        Args:
            equity_curve: Portfolio equity curve
            trades: Trade log DataFrame (optional)

        Returns:
            str: Formatted metrics report
        """
        try:
            metrics = self.calculate_comprehensive_metrics(equity_curve, trades)

            report_lines = []
            report_lines.append("=== Performance Metrics Report ===\n")

            # Return metrics
            if "return_metrics" in metrics:
                report_lines.append("Return Metrics:")
                for name, value in metrics["return_metrics"].items():
                    formatted_name = name.replace("_", " ").title()
                    report_lines.append(f"  {formatted_name}: {value:.4f}")
                report_lines.append("")

            # Risk metrics
            if "risk_metrics" in metrics:
                report_lines.append("Risk Metrics:")
                for name, value in metrics["risk_metrics"].items():
                    formatted_name = name.replace("_", " ").title()
                    if name == "var_95":
                        report_lines.append(f"  {formatted_name}: {value:.4f}")
                    elif name == "cvar_95":
                        report_lines.append(f"  {formatted_name}: {value:.4f}")
                    else:
                        report_lines.append(f"  {formatted_name}: {value:.4f}")
                report_lines.append("")

            # Trade metrics
            if "trade_metrics" in metrics:
                report_lines.append("Trade Metrics:")
                for name, value in metrics["trade_metrics"].items():
                    formatted_name = name.replace("_", " ").title()
                    report_lines.append(f"  {formatted_name}: {value:.4f}")
                report_lines.append("")

            # Benchmark metrics
            if "benchmark_metrics" in metrics:
                report_lines.append("Benchmark Metrics:")
                for name, value in metrics["benchmark_metrics"].items():
                    formatted_name = name.replace("_", " ").title()
                    report_lines.append(f"  {formatted_name}: {value:.4f}")
                report_lines.append("")

            return "\n".join(report_lines)
        except Exception as e:
            raise MetricsCalculationError(f"Failed to generate tear sheet: {e}") from e

    def calculate_rolling_metrics(
        self, equity_curve: pd.Series, window: int
    ) -> pd.DataFrame:
        """
        Calculate rolling metrics over a sliding window.

        Args:
            equity_curve: Portfolio equity curve
            window: Window size for rolling calculations

        Returns:
            DataFrame with rolling metrics
        """
        if len(equity_curve) < window:
            raise ValueError("Window size cannot be larger than data length")

        try:
            returns = self.calculate_returns(equity_curve)

            # Calculate rolling metrics
            rolling_return = returns.rolling(window=window).mean()
            rolling_volatility = returns.rolling(window=window).std()

            # Calculate rolling Sharpe ratio
            rolling_sharpe = (
                rolling_return / rolling_volatility * np.sqrt(252)
            )  # Assuming daily returns
            rolling_sharpe = rolling_sharpe.fillna(0)

            # Create result DataFrame
            result = pd.DataFrame(
                {
                    "rolling_return": rolling_return,
                    "rolling_volatility": rolling_volatility,
                    "rolling_sharpe": rolling_sharpe,
                }
            )

            # Drop NaN values from the start
            result = result.dropna()

            return result
        except Exception as e:
            raise MetricsCalculationError(
                f"Failed to calculate rolling metrics: {e}"
            ) from e

    def calculate_metrics_by_period(
        self, equity_curve: pd.Series, period: str
    ) -> pd.DataFrame:
        """
        Calculate metrics by time period (e.g., monthly, quarterly).

        Args:
            equity_curve: Portfolio equity curve
            period: Period string (e.g., 'M' for monthly, 'Q' for quarterly)

        Returns:
            DataFrame with period-based metrics
        """
        if period not in ["M", "Q", "A", "D"]:
            raise ValueError(
                f"Invalid period: {period}. Must be one of 'M', 'Q', 'A', 'D'"
            )

        try:
            # Resample equity curve by period
            period_equity = equity_curve.resample(period).last()

            # Calculate returns for each period
            period_returns = period_equity.pct_change().dropna()

            # Calculate metrics for each period
            period_metrics = pd.DataFrame(
                {
                    "return": period_returns,
                    "cumulative_return": (1 + period_returns).cumprod() - 1,
                }
            )

            # Add period-specific metrics
            period_metrics["high"] = equity_curve.resample(period).max()
            period_metrics["low"] = equity_curve.resample(period).min()

            # Calculate drawdown within each period
            period_high = equity_curve.resample(period).max()
            period_low = equity_curve.resample(period).min()
            period_drawdown = (period_low - period_high) / period_high

            # Add to results
            period_metrics["drawdown"] = period_drawdown

            # Drop periods with no data
            period_metrics = period_metrics.dropna()

            return period_metrics
        except Exception as e:
            raise MetricsCalculationError(
                f"Failed to calculate metrics by period: {e}"
            ) from e

    def compare_strategies(
        self, equity_curve1: pd.Series, equity_curve2: pd.Series
    ) -> Dict[str, Any]:
        """
        Compare two strategies based on their equity curves.

        Args:
            equity_curve1: First strategy equity curve
            equity_curve2: Second strategy equity curve

        Returns:
            Dict with comparison metrics
        """
        try:
            # Calculate returns for both strategies
            returns1 = self.calculate_returns(equity_curve1)
            returns2 = self.calculate_returns(equity_curve2)

            # Calculate basic metrics for each strategy
            total_return1 = self.calculate_total_return(equity_curve1)
            total_return2 = self.calculate_total_return(equity_curve2)

            sharpe1 = self.calculate_sharpe_ratio(equity_curve1)
            sharpe2 = self.calculate_sharpe_ratio(equity_curve2)

            max_dd1 = self.calculate_max_drawdown(equity_curve1)["max_drawdown"]
            max_dd2 = self.calculate_max_drawdown(equity_curve2)["max_drawdown"]

            # Calculate correlation between strategies
            # Align the returns series
            min_len = min(len(returns1), len(returns2))
            aligned_returns1 = returns1.iloc[:min_len]
            aligned_returns2 = returns2.iloc[:min_len]

            correlation = aligned_returns1.corr(aligned_returns2)

            # Determine winner based on Sharpe ratio
            winner = "strategy_1" if sharpe1 > sharpe2 else "strategy_2"

            return {
                "strategy_1": {
                    "total_return": total_return1,
                    "sharpe_ratio": sharpe1,
                    "max_drawdown": max_dd1,
                },
                "strategy_2": {
                    "total_return": total_return2,
                    "sharpe_ratio": sharpe2,
                    "max_drawdown": max_dd2,
                },
                "correlation": correlation,
                "winner": winner,
            }
        except Exception as e:
            raise MetricsCalculationError(f"Failed to compare strategies: {e}") from e

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
            raise LibraryImportError("Empyrical library is not available")

        try:
            metrics = {}

            # Alpha and Beta (if benchmark available)
            if self.benchmark_returns is not None:
                metrics["alpha"] = empyrical.alpha(returns, self.benchmark_returns)
                metrics["beta"] = empyrical.beta(returns, self.benchmark_returns)

            # Risk metrics
            metrics["sharpe_ratio"] = empyrical.sharpe_ratio(
                returns, risk_free=self.risk_free_rate
            )
            metrics["max_drawdown"] = empyrical.max_drawdown(returns)
            metrics["annual_volatility"] = empyrical.annual_volatility(returns)

            # Additional risk metrics
            if hasattr(empyrical, "value_at_risk"):
                metrics["var_95"] = empyrical.value_at_risk(returns, 0.05)
            if hasattr(empyrical, "conditional_value_at_risk"):
                metrics["cvar_95"] = empyrical.conditional_value_at_risk(returns, 0.05)
            if hasattr(empyrical, "omega_ratio"):
                metrics["omega_ratio"] = empyrical.omega_ratio(returns)

            # Distribution metrics
            if hasattr(empyrical.stats, "skew"):
                metrics["skewness"] = empyrical.stats.skew(returns)
            if hasattr(empyrical.stats, "kurtosis"):
                metrics["kurtosis"] = empyrical.stats.kurtosis(returns)

            return metrics
        except Exception as e:
            raise MetricsCalculationError(
                f"Failed to calculate Empyrical metrics: {e}"
            ) from e

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

    def _calculate_basic_metrics(
        self, equity_curve: pd.Series, frequency: str
    ) -> Dict[str, Any]:
        """Calculate basic return metrics."""
        returns = self.calculate_returns(equity_curve, frequency)
        total_return = self.calculate_total_return(equity_curve)
        annualized_return = self.calculate_annualized_return(returns, frequency)

        return {
            "returns": returns,
            "total_return": total_return,
            "annualized_return": annualized_return,
        }

    def _calculate_risk_metrics(
        self, returns: pd.Series, frequency: str, max_drawdown: float
    ) -> Dict[str, Any]:
        """Calculate risk-related metrics."""
        sharpe_ratio = self.calculate_sharpe_ratio(returns, frequency)
        sortino_ratio = self.calculate_sortino_ratio(returns, frequency)
        calmar_ratio = self.calculate_calmar_ratio(returns, max_drawdown)
        volatility = returns.std() * np.sqrt(252)  # Annualized

        return {
            "sharpe_ratio": sharpe_ratio,
            "sortino_ratio": sortino_ratio,
            "calmar_ratio": calmar_ratio,
            "volatility": volatility,
        }

    def _calculate_trade_statistics(self, trades: pd.DataFrame) -> Dict[str, Any]:
        """Calculate trade-based statistics."""
        if len(trades) == 0:
            return {
                "win_rate": 0.0,
                "profit_factor": 0.0,
                "total_trades": 0,
                "avg_win": 0.0,
                "avg_loss": 0.0,
                "best_trade": 0.0,
                "worst_trade": 0.0,
                "avg_trade_duration": 0.0,
                "avg_trade_duration_days": 0.0,
            }

        win_rate = self.calculate_win_rate(trades)
        profit_factor = self.calculate_profit_factor(trades)
        total_trades = len(trades)

        if "pnl" not in trades.columns:
            return {
                "win_rate": win_rate,
                "profit_factor": profit_factor,
                "total_trades": len(trades),
                "avg_win": 0.0,
                "avg_loss": 0.0,
                "best_trade": 0.0,
                "worst_trade": 0.0,
                "avg_trade_duration": 0.0,
                "avg_trade_duration_days": 0.0,
            }

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

        return {
            "win_rate": win_rate,
            "profit_factor": profit_factor,
            "total_trades": total_trades,
            "avg_win": avg_win,
            "avg_loss": avg_loss,
            "best_trade": best_trade,
            "worst_trade": worst_trade,
            "avg_trade_duration": avg_trade_duration,
            "avg_trade_duration_days": avg_trade_duration_days,
        }

    def _calculate_quantstats_metrics(self, returns: pd.Series) -> Dict[str, float]:
        """Calculate QuantStats metrics if available."""
        if not QUANTSTATS_AVAILABLE:
            return {"sharpe_ratio_qstats": 0.0, "sortino_ratio_qstats": 0.0}

        try:
            sharpe_ratio_qstats = qs.stats.sharpe(returns)
            sortino_ratio_qstats = qs.stats.sortino(returns)
        except Exception:
            sharpe_ratio_qstats = 0.0
            sortino_ratio_qstats = 0.0

        return {
            "sharpe_ratio_qstats": sharpe_ratio_qstats,
            "sortino_ratio_qstats": sortino_ratio_qstats,
        }

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
            # Calculate basic metrics
            basic_metrics = self._calculate_basic_metrics(equity_curve, frequency)
            returns = basic_metrics["returns"]
            total_return = basic_metrics["total_return"]
            annualized_return = basic_metrics["annualized_return"]

            # Calculate drawdown info
            drawdown_info = self.calculate_max_drawdown(equity_curve)
            max_drawdown = drawdown_info["max_drawdown"]
            max_drawdown_duration = drawdown_info["max_drawdown_duration"]
            max_drawdown_start = drawdown_info["max_drawdown_start"]
            max_drawdown_end = drawdown_info["max_drawdown_end"]

            # Calculate risk metrics
            risk_metrics = self._calculate_risk_metrics(
                returns, frequency, max_drawdown
            )
            sharpe_ratio = risk_metrics["sharpe_ratio"]
            sortino_ratio = risk_metrics["sortino_ratio"]
            calmar_ratio = risk_metrics["calmar_ratio"]
            volatility = risk_metrics["volatility"]

            # Calculate trade statistics
            trade_stats = self._calculate_trade_statistics(trades)

            # Calculate QuantStats metrics
            qstats_metrics = self._calculate_quantstats_metrics(returns)

            # Calculate Empyrical metrics
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
                omega_ratio = alpha = beta = information_ratio = 0.0
                var_95 = cvar_95 = skewness = kurtosis = 0.0

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
                win_rate=trade_stats["win_rate"],
                profit_factor=trade_stats["profit_factor"],
                total_trades=trade_stats["total_trades"],
                winning_trades=0,  # Not needed for simplified stats
                losing_trades=0,  # Not needed for simplified stats
                avg_win=trade_stats["avg_win"],
                avg_loss=trade_stats["avg_loss"],
                best_trade=trade_stats["best_trade"],
                worst_trade=trade_stats["worst_trade"],
                avg_trade_duration=trade_stats["avg_trade_duration"],
                avg_trade_duration_days=trade_stats["avg_trade_duration_days"],
                sharpe_ratio_qstats=qstats_metrics["sharpe_ratio_qstats"],
                sortino_ratio_qstats=qstats_metrics["sortino_ratio_qstats"],
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
