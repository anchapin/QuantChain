"""
Core backtesting engine with abstract base class and data structures.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, Optional
import pandas as pd
from datetime import datetime


class BacktestEngine(ABC):
    """Abstract base class for backtesting engines."""

    @abstractmethod
    def run(
        self, strategy: Any, data: pd.DataFrame, config: "BacktestConfig"
    ) -> "BacktestResult":
        """Run backtest with given strategy, data, and configuration."""
        pass

    @abstractmethod
    def get_results(self) -> Optional["BacktestResult"]:
        """Get results of the last backtest."""
        pass

    @abstractmethod
    def get_equity_curve(self) -> Optional[pd.Series]:
        """Get equity curve from the last backtest."""
        pass


@dataclass
class BacktestConfig:
    """Configuration for backtesting parameters."""

    initial_cash: float = 100000.0
    commission_rate: float = 0.001
    slippage_model: str = "fixed"  # 'fixed', 'volume_impact', 'bid_ask_spread'
    slippage_rate: float = 0.0001
    latency_model: str = "fixed"  # 'fixed', 'uniform', 'normal'
    latency_ms: float = 10.0
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    data_frequency: str = "1d"  # '1m', '5m', '1h', '1d'
    additional_params: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate configuration parameters."""
        if self.additional_params is None:
            self.additional_params = {}

        # Validate initial cash
        if self.initial_cash <= 0:
            raise ConfigurationError("initial_cash must be positive")

        # Validate commission rate
        if self.commission_rate < 0:
            raise ConfigurationError("commission_rate must be non-negative")

        # Validate data frequency
        valid_frequencies = ["1m", "5m", "1h", "1d"]
        if self.data_frequency not in valid_frequencies:
            raise ConfigurationError(f"Invalid data_frequency: {self.data_frequency}")

        # Validate slippage model
        valid_slippage_models = ["fixed", "volume_impact", "bid_ask_spread"]
        if self.slippage_model not in valid_slippage_models:
            raise ConfigurationError(f"Invalid slippage_model: {self.slippage_model}")

        # Validate latency model
        valid_latency_models = ["fixed", "uniform", "normal"]
        if self.latency_model not in valid_latency_models:
            raise ConfigurationError(f"Invalid latency_model: {self.latency_model}")

        # Validate date consistency
        if self.start_date and self.end_date:
            if self.start_date >= self.end_date:
                raise ConfigurationError("end_date must be after start_date")


@dataclass
class MetricsResult:
    """Performance metrics from backtest."""

    total_return: float
    annualized_return: float
    sharpe_ratio: float
    sortino_ratio: float
    calmar_ratio: float
    max_drawdown: float
    max_drawdown_duration: int
    max_drawdown_start: Optional[datetime] = None
    max_drawdown_end: Optional[datetime] = None
    volatility: float = 0.0
    win_rate: float = 0.0
    profit_factor: float = 0.0
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    avg_win: float = 0.0
    avg_loss: float = 0.0
    best_trade: float = 0.0
    worst_trade: float = 0.0
    avg_trade_duration: float = 0.0
    avg_trade_duration_days: float = 0.0
    sharpe_ratio_qstats: float = 0.0
    sortino_ratio_qstats: float = 0.0
    omega_ratio: float = 0.0
    alpha: float = 0.0
    beta: float = 0.0
    information_ratio: float = 0.0
    var_95: float = 0.0
    cvar_95: float = 0.0
    skewness: float = 0.0
    kurtosis: float = 0.0
    additional_metrics: Dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Initialize additional metrics if needed."""
        if self.additional_metrics is None:
            self.additional_metrics = {}


@dataclass
class BacktestResult:
    """Results from a backtest run."""

    equity_curve: pd.Series
    trade_log: pd.DataFrame
    summary_stats: Dict[str, float]
    metrics: MetricsResult
    execution_time: float
    config: BacktestConfig

    def __post_init__(self) -> None:
        """Validate result structure."""
        if not isinstance(self.equity_curve, pd.Series):
            raise ValueError("equity_curve must be a pandas Series")
        if not isinstance(self.trade_log, pd.DataFrame):
            raise ValueError("trade_log must be a pandas DataFrame")
        if not isinstance(self.summary_stats, dict):
            raise ValueError("summary_stats must be a dictionary")
        if not isinstance(self.metrics, MetricsResult):
            raise ValueError("metrics must be a MetricsResult instance")
        if not isinstance(self.config, BacktestConfig):
            raise ValueError("config must be a BacktestConfig instance")


class ConfigurationError(Exception):
    """Raised for invalid backtest configuration."""

    pass


class DataValidationError(Exception):
    """Raised for invalid input data."""

    pass


class BacktestExecutionError(Exception):
    """Raised for errors during backtest execution."""

    pass


def validate_ohlcv_data(data: pd.DataFrame) -> None:
    """
    Validate OHLCV data format and content.

    Args:
        data: DataFrame with OHLCV data

    Raises:
        DataValidationError: If data format is invalid
    """
    if data is None or len(data) == 0:
        raise DataValidationError("Data cannot be empty")

    required_columns = ["open", "high", "low", "close", "volume"]
    missing_columns = [col for col in required_columns if col not in data.columns]

    if missing_columns:
        raise DataValidationError(f"Missing required columns: {missing_columns}")

    # Validate data types
    if not all(
        data[col].dtype in ["float64", "int64", "float32", "int32"]
        for col in ["open", "high", "low", "close"]
    ):
        raise DataValidationError("OHLC columns must be numeric")

    if not data["volume"].dtype in ["float64", "int64", "float32", "int32"]:
        raise DataValidationError("Volume column must be numeric")

    # Validate logical consistency
    if (data["high"] < data["low"]).any():
        raise DataValidationError("High prices cannot be lower than low prices")

    if (data["high"] < data["open"]).any() or (data["high"] < data["close"]).any():
        raise DataValidationError("High prices cannot be lower than open/close prices")

    if (data["low"] > data["open"]).any() or (data["low"] > data["close"]).any():
        raise DataValidationError("Low prices cannot be higher than open/close prices")

    # Validate non-negative values
    if (data["volume"] < 0).any():
        raise DataValidationError("Volume cannot be negative")

    if (data[["open", "high", "low", "close"]] <= 0).any().any():
        raise DataValidationError("Prices must be positive")


def filter_data_by_date_range(
    data: pd.DataFrame, start_date: Optional[datetime], end_date: Optional[datetime]
) -> pd.DataFrame:
    """
    Filter data by date range.

    Args:
        data: OHLCV data
        start_date: Start date (inclusive)
        end_date: End date (inclusive)

    Returns:
        Filtered DataFrame
    """
    filtered_data = data.copy()

    if start_date:
        filtered_data = filtered_data[filtered_data.index >= start_date]

    if end_date:
        filtered_data = filtered_data[filtered_data.index <= end_date]

    return filtered_data


def calculate_basic_statistics(
    equity_curve: pd.Series, initial_cash: float
) -> Dict[str, float]:
    """
    Calculate basic backtest statistics.

    Args:
        equity_curve: Portfolio equity over time
        initial_cash: Initial cash amount

    Returns:
        Dictionary with basic statistics
    """
    if len(equity_curve) == 0:
        return {"total_return": 0.0, "annualized_return": 0.0}

    final_equity = equity_curve.iloc[-1]
    total_return = (final_equity - initial_cash) / initial_cash

    # Calculate annualized return
    if len(equity_curve) > 1:
        time_span_days = (equity_curve.index[-1] - equity_curve.index[0]).days
        if time_span_days > 0:
            years = time_span_days / 365.25
            annualized_return = (final_equity / initial_cash) ** (1 / years) - 1
        else:
            annualized_return = total_return
    else:
        annualized_return = total_return

    return {
        "total_return": total_return,
        "annualized_return": annualized_return,
        "final_equity": final_equity,
        "initial_equity": initial_cash,
    }
