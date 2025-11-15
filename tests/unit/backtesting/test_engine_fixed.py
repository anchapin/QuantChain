"""Comprehensive tests for backtesting engine module."""

from datetime import datetime, timezone
from typing import Any, Optional
from unittest.mock import MagicMock

import numpy as np
import pandas as pd
import pytest

from quantchain.backtesting.engine import (
    BacktestConfig,
    BacktestEngine,
    BacktestExecutionError,
    BacktestResult,
    ConfigurationError,
    DataValidationError,
    MetricsResult,
    calculate_basic_statistics,
    filter_data_by_date_range,
    validate_ohlcv_data,
)


class MockBacktestEngine(BacktestEngine):
    """Mock implementation of BacktestEngine for testing."""



def __init__(self):
        self._results = None
        self._equity_curve = None



def run(
        self, strategy: Any, data: pd.DataFrame, config: BacktestConfig
    ) -> BacktestResult:
        """Mock run method that returns test results."""
        # Create mock results based on data
        self._equity_curve = pd.Series(
            [config.initial_cash] * len(data), index=data.index, name="equity"
        )

        # Create metrics result
        metrics = MetricsResult(
            total_return=0.10,
            annualized_return=0.10,
            max_drawdown=0.05,
            sharpe_ratio=1.5,
            sortino_ratio=2.0,
            win_rate=0.60,
            profit_factor=1.8,
            total_trades=100,
            winning_trades=60,
            losing_trades=40,
            avg_trade=50.0,
            avg_win=100.0,
            avg_loss=-50.0,
            best_trade=500.0,
            worst_trade=-250.0,
        )

        self._results = BacktestResult(
            equity_curve=self._equity_curve,
            trade_log=pd.DataFrame(),
            summary_stats={"execution_time": 1.0},
            metrics=metrics,
            execution_time=1.0,
            config=config,
        )

        return self._results



def get_results(self) -> Optional[BacktestResult]:
        """Get results of last backtest."""
        return self._results



def get_equity_curve(self) -> Optional[pd.Series]:
        """Get equity curve from last backtest."""
        return self._equity_curve


@pytest.mark.unit


class TestBacktestConfig:
    """Test suite for BacktestConfig."""



def test_default_initialization(self) -> None:
        """Test BacktestConfig with default values."""
        config = BacktestConfig()

        assert config.initial_cash == 100000.0
        assert config.commission_rate == 0.001
        assert config.slippage_model == "fixed"
        assert config.slippage_rate == 0.0001
        assert config.latency_model == "fixed"
        assert config.latency_ms == 10.0
        assert config.start_date is None
        assert config.end_date is None
        assert config.data_frequency == "1d"
        assert config.additional_params == {}



def test_custom_initialization(self) -> None:
        """Test BacktestConfig with custom values."""
        start = datetime(2024, 1, 1, tzinfo=timezone.utc)
        end = datetime(2024, 12, 31, tzinfo=timezone.utc)
        params = {"risk_free_rate": 0.02}

        config = BacktestConfig(
            initial_cash=50000.0,
            commission_rate=0.002,
            slippage_model="volume_impact",
            slippage_rate=0.0002,
            latency_model="normal",
            latency_ms=20.0,
            start_date=start,
            end_date=end,
            data_frequency="1h",
            additional_params=params,
        )

        assert config.initial_cash == 50000.0
        assert config.commission_rate == 0.002
        assert config.slippage_model == "volume_impact"
        assert config.slippage_rate == 0.0002
        assert config.latency_model == "normal"
        assert config.latency_ms == 20.0
        assert config.start_date == start
        assert config.end_date == end
        assert config.data_frequency == "1h"
        assert config.additional_params == params



def test_post_init_with_none_additional_params(self) -> None:
        """Test BacktestConfig post_init with None additional_params."""
        config = BacktestConfig()
        config.additional_params = None
        config.__post_init__()
        assert config.additional_params == {}


@pytest.mark.unit


class TestMetricsResult:
    """Test suite for MetricsResult dataclass."""



def test_metrics_result_creation(self) -> None:
        """Test creating a MetricsResult."""
        metrics = MetricsResult(
            total_return=0.10,
            annualized_return=0.20,
            max_drawdown=0.05,
            sharpe_ratio=1.5,
            sortino_ratio=2.0,
            win_rate=0.60,
            profit_factor=1.8,
            total_trades=100,
            winning_trades=60,
            losing_trades=40,
            avg_trade=50.0,
            avg_win=100.0,
            avg_loss=-50.0,
            best_trade=500.0,
            worst_trade=-250.0,
        )

        assert metrics.total_return == 0.10
        assert metrics.annualized_return == 0.20
        assert metrics.max_drawdown == 0.05
        assert metrics.sharpe_ratio == 1.5
        assert metrics.sortino_ratio == 2.0
        assert metrics.win_rate == 0.60
        assert metrics.profit_factor == 1.8
        assert metrics.total_trades == 100
        assert metrics.winning_trades == 60
        assert metrics.losing_trades == 40
        assert metrics.avg_trade == 50.0
        assert metrics.avg_win == 100.0
        assert metrics.avg_loss == -50.0
        assert metrics.best_trade == 500.0
        assert metrics.worst_trade == -250.0
        assert metrics.additional_metrics == {}



def test_metrics_result_with_minimum_values(self) -> None:
        """Test creating a MetricsResult with minimum values."""
        metrics = MetricsResult()

        assert metrics.total_return == 0.0
        assert metrics.annualized_return == 0.0
        assert metrics.max_drawdown == 0.0
        assert metrics.sharpe_ratio == 0.0
        assert metrics.sortino_ratio == 0.0
        assert metrics.win_rate == 0.0
        assert metrics.profit_factor == 0.0
        assert metrics.total_trades == 0
        assert metrics.winning_trades == 0
        assert metrics.losing_trades == 0
        assert metrics.avg_trade == 0.0
        assert metrics.avg_win == 0.0
        assert metrics.avg_loss == 0.0
        assert metrics.best_trade == 0.0
        assert metrics.worst_trade == 0.0


@pytest.mark.unit


class TestBacktestResult:
    """Test suite for BacktestResult dataclass."""



def test_backtest_result_creation(self) -> None:
        """Test creating a BacktestResult."""
        start = datetime(2024, 1, 1, tzinfo=timezone.utc)
        end = datetime(2024, 6, 30, tzinfo=timezone.utc)
        config = BacktestConfig(start_date=start, end_date=end)
        equity_curve = pd.Series([100000, 105000, 110000], name="equity")
        trades = pd.DataFrame({"symbol": ["AAPL"], "pnl": [5000]})
        metrics = MetricsResult(total_return=0.10)

        result = BacktestResult(
            equity_curve=equity_curve,
            trade_log=trades,
            summary_stats={"test": "value"},
            metrics=metrics,
            execution_time=5.0,
            config=config,
        )

        assert result.equity_curve.equals(equity_curve)
        assert result.trade_log.equals(trades)
        assert result.summary_stats == {"test": "value"}
        assert result.metrics == metrics
        assert result.execution_time == 5.0
        assert result.config == config



def test_backtest_result_validation(self) -> None:
        """Test BacktestResult validation."""
        config = BacktestConfig()
        equity_curve = pd.Series([100000], name="equity")
        trades = pd.DataFrame()
        metrics = MetricsResult()

        # Valid result should not raise
        result = BacktestResult(
            equity_curve=equity_curve,
            trade_log=trades,
            summary_stats={},
            metrics=metrics,
            execution_time=1.0,
            config=config,
        )
        assert result is not None

        # Invalid equity_curve should raise
        with pytest.raises(ValueError, match="equity_curve must be a pandas Series"):
            BacktestResult(
                equity_curve="not a series",
                trade_log=trades,
                summary_stats={},
                metrics=metrics,
                execution_time=1.0,
                config=config,
            )

        # Invalid trade_log should raise
        with pytest.raises(ValueError, match="trade_log must be a pandas DataFrame"):
            BacktestResult(
                equity_curve=equity_curve,
                trade_log="not a dataframe",
                summary_stats={},
                metrics=metrics,
                execution_time=1.0,
                config=config,
            )


@pytest.mark.unit


class TestBacktestEngine:
    """Test suite for BacktestEngine abstract class."""



def test_abstract_class(self) -> None:
        """Test that BacktestEngine cannot be instantiated directly."""
        with pytest.raises(TypeError):
            BacktestEngine()  # type: ignore[abstract]



def test_mock_implementation(self) -> None:
        """Test that mock implementation works correctly."""
        engine = MockBacktestEngine()

        # Test initial state
        assert engine.get_results() is None
        assert engine.get_equity_curve() is None

        # Create test data
        data = pd.DataFrame(
            {
                "open": [100, 105, 110],
                "high": [105, 110, 115],
                "low": [95, 100, 105],
                "close": [105, 110, 115],
                "volume": [1000, 1500, 2000],
            }
        )
        data.index = pd.date_range("2024-01-01", periods=3, freq="D")

        # Create test config
        config = BacktestConfig(
            start_date=datetime(2024, 1, 1, tzinfo=timezone.utc),
            end_date=datetime(2024, 1, 3, tzinfo=timezone.utc),
        )

        # Run backtest
        mock_strategy = MagicMock()
        results = engine.run(mock_strategy, data, config)

        # Check results
        assert results is not None
        assert results.metrics.total_return == 0.10
        assert len(results.equity_curve) == 3

        # Check stored results
        assert engine.get_results() is not None
        assert engine.get_equity_curve() is not None
        assert engine.get_results() == results
        assert engine.get_equity_curve().equals(results.equity_curve)


@pytest.mark.unit


class TestValidationFunctions:
    """Test suite for validation functions."""



def test_validate_ohlcv_data_valid(self) -> None:
        """Test OHLCV validation with valid data."""
        data = pd.DataFrame(
            {
                "open": [100.0, 105.0, 110.0],
                "high": [105.0, 110.0, 115.0],
                "low": [95.0, 100.0, 105.0],
                "close": [105.0, 110.0, 115.0],
                "volume": [1000, 1500, 2000],
            }
        )

        # Should not raise
        validate_ohlcv_data(data)



def test_validate_ohlcv_data_empty(self) -> None:
        """Test OHLCV validation with empty data."""
        with pytest.raises(DataValidationError, match="Data cannot be empty"):
            validate_ohlcv_data(pd.DataFrame())



def test_validate_ohlcv_data_missing_columns(self) -> None:
        """Test OHLCV validation with missing columns."""
        data = pd.DataFrame(
            {
                "open": [100.0, 105.0],
                "high": [105.0, 110.0],
                # Missing low, close, volume
            }
        )

        with pytest.raises(DataValidationError, match="Missing required columns"):
            validate_ohlcv_data(data)



def test_validate_ohlcv_data_invalid_types(self) -> None:
        """Test OHLCV validation with invalid data types."""
        # String columns instead of numeric
        data = pd.DataFrame(
            {
                "open": ["100", "105"],
                "high": ["105", "110"],
                "low": ["95", "100"],
                "close": ["105", "110"],
                "volume": [1000, 1500],  # Numeric
            }
        )

        with pytest.raises(DataValidationError, match="OHLC columns must be numeric"):
            validate_ohlcv_data(data)



def test_validate_ohlcv_data_logical_errors(self) -> None:
        """Test OHLCV validation with logical errors."""
        # High lower than low
        data = pd.DataFrame(
            {
                "open": [100.0, 105.0],
                "high": [105.0, 110.0],
                "low": [110.0, 115.0],  # Higher than high
                "close": [105.0, 110.0],
                "volume": [1000, 1500],
            }
        )

        with pytest.raises(
            DataValidationError, match="High prices cannot be lower than low prices"
        ):
            validate_ohlcv_data(data)

        # Negative volume
        data = pd.DataFrame(
            {
                "open": [100.0, 105.0],
                "high": [105.0, 110.0],
                "low": [95.0, 100.0],
                "close": [105.0, 110.0],
                "volume": [-1000, 1500],  # Negative
            }
        )

        with pytest.raises(DataValidationError, match="Volume cannot be negative"):
            validate_ohlcv_data(data)



def test_filter_data_by_date_range(self) -> None:
        """Test filtering data by date range."""
        dates = pd.date_range("2024-01-01", periods=10, freq="D")
        data = pd.DataFrame(
            {
                "close": np.arange(10),
            },
            index=dates,
        )

        # Filter with both start and end
        start = datetime(2024, 1, 3)  # No timezone to match DataFrame index
        end = datetime(2024, 1, 7)  # No timezone to match DataFrame index

        filtered = filter_data_by_date_range(data, start, end)

        assert len(filtered) == 5  # Days 3-7 inclusive
        # Compare with pandas Timestamp for proper comparison
        assert filtered.index[0] == pd.Timestamp(start)
        assert filtered.index[-1] == pd.Timestamp(end)

        # Filter with only start
        filtered = filter_data_by_date_range(data, start, None)

        assert len(filtered) == 8  # Days 3-10
        assert filtered.index[0] == start

        # Filter with only end
        filtered = filter_data_by_date_range(data, None, end)

        assert len(filtered) == 7  # Days 1-7
        assert filtered.index[-1] == end

        # No filter
        filtered = filter_data_by_date_range(data, None, None)

        assert len(filtered) == 10
        assert filtered.equals(data)



def test_calculate_basic_statistics(self) -> None:
        """Test basic statistics calculation."""
        equity_curve = pd.Series([100000, 105000, 110000], name="equity")
        initial_cash = 100000.0

        stats = calculate_basic_statistics(equity_curve, initial_cash)

        assert stats["total_return"] == 0.10
        assert stats["final_equity"] == 110000.0
        assert stats["initial_equity"] == initial_cash
        assert "annualized_return" in stats


@pytest.mark.unit


class TestExceptionClasses:
    """Test suite for custom exception classes."""



def test_configuration_error(self) -> None:
        """Test ConfigurationError."""
        with pytest.raises(ConfigurationError) as exc_info:
            raise ConfigurationError("Invalid config")

        assert "Invalid config" in str(exc_info.value)
        assert isinstance(exc_info.value, Exception)



def test_data_validation_error(self) -> None:
        """Test DataValidationError."""
        with pytest.raises(DataValidationError) as exc_info:
            raise DataValidationError("Invalid data")

        assert "Invalid data" in str(exc_info.value)
        assert isinstance(exc_info.value, Exception)



def test_backtest_execution_error(self) -> None:
        """Test BacktestExecutionError."""
        with pytest.raises(BacktestExecutionError) as exc_info:
            raise BacktestExecutionError("Execution failed")

        assert "Execution failed" in str(exc_info.value)
        assert isinstance(exc_info.value, Exception)
