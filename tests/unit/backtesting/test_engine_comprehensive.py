"""Comprehensive tests for the backtesting engine module."""

from datetime import datetime, timezone
from typing import Any, Optional
from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
import pytest

from quantchain.backtesting.engine import (
    BacktestConfig,
    BacktestEngine,
    BacktestResult,
    MetricsResult,
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

        # Create metrics with required parameters
        metrics = MetricsResult(
            total_return=0.10,
            annualized_return=0.10,
            sharpe_ratio=1.5,
            sortino_ratio=2.0,
            calmar_ratio=1.0,
            max_drawdown=0.05,
            max_drawdown_duration=30,
            volatility=0.15,
            win_rate=0.60,
            profit_factor=1.8,
            total_trades=100,
            winning_trades=60,
            losing_trades=40,
            avg_win=100.0,
            avg_loss=-50.0,
            best_trade=500.0,
            worst_trade=-250.0,
            avg_trade_duration=1.0,
            avg_trade_duration_days=1.0,
            sharpe_ratio_qstats=1.5,
            sortino_ratio_qstats=2.0,
            omega_ratio=1.2,
            alpha=0.02,
            beta=0.8,
            information_ratio=0.5,
            var_95=-0.02,
            cvar_95=-0.03,
            skewness=0.1,
            kurtosis=0.2,
        )

        self._results = BacktestResult(
            equity_curve=self._equity_curve,
            trade_log=pd.DataFrame(),
            summary_stats={
                "total_return": 0.10,
                "initial_cash": config.initial_cash,
                "final_cash": config.initial_cash * 1.1,
                "max_drawdown": 0.05,
                "win_rate": 0.60,
                "profit_factor": 1.8,
                "total_trades": 100,
                "winning_trades": 60,
                "losing_trades": 40,
                "avg_trade": 50.0,
                "avg_win": 100.0,
                "avg_loss": -50.0,
                "best_trade": 500.0,
                "worst_trade": -250.0,
            },
            metrics=metrics,
            execution_time=1.5,
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

    def test_config_dict_like_access(self) -> None:
        """Test that BacktestConfig behaves like a dict."""
        config = BacktestConfig(initial_cash=75000.0)

        # Test attribute access
        assert config.initial_cash == 75000.0

        # Test that we can convert to dict-like structure
        config_dict = {
            "initial_cash": config.initial_cash,
            "commission_rate": config.commission_rate,
            "slippage_model": config.slippage_model,
        }

        assert config_dict["initial_cash"] == 75000.0
        assert config_dict["commission_rate"] == 0.001
        assert config_dict["slippage_model"] == "fixed"


@pytest.mark.unit
class TestBacktestResult:
    """Test suite for BacktestResult dataclass."""

    def test_backtest_result_creation(self) -> None:
        """Test creating a BacktestResult."""
        start = datetime(2024, 1, 1, tzinfo=timezone.utc)
        end = datetime(2024, 6, 30, tzinfo=timezone.utc)
        equity_curve = pd.Series([100000, 105000, 110000], name="equity")
        trades = pd.DataFrame({"symbol": ["AAPL"], "pnl": [5000]})
        daily_returns = pd.Series([0.05, 0.0476, -0.02])

        config = BacktestConfig(start_date=start, end_date=end, initial_cash=100000.0)
        metrics = MetricsResult(
            total_return=0.10,
            annualized_return=0.20,
            sharpe_ratio=1.5,
            sortino_ratio=2.0,
            calmar_ratio=1.2,
            max_drawdown=0.05,
            max_drawdown_duration=10,
        )

        result = BacktestResult(
            equity_curve=equity_curve,
            trade_log=trades,
            summary_stats={"total_return": 0.10},
            metrics=metrics,
            execution_time=1.5,
            config=config,
        )

        # Test dataclass properties
        assert result.equity_curve.equals(equity_curve)
        assert result.trade_log.equals(trades)
        assert result.summary_stats == {"total_return": 0.10}
        assert result.execution_time == 1.5
        assert result.config == config

    def test_backtest_result_with_minimum_values(self) -> None:
        """Test creating a BacktestResult with minimum values."""
        from quantchain.backtesting.engine import BacktestConfig, MetricsResult

        start = datetime(2024, 1, 1, tzinfo=timezone.utc)
        end = datetime(2024, 1, 31, tzinfo=timezone.utc)
        equity_curve = pd.Series([100000], name="equity")

        # Create required components for the current BacktestResult structure
        config = BacktestConfig(start_date=start, end_date=end, initial_cash=100000.0)
        metrics = MetricsResult(
            total_return=0.0,
            annualized_return=0.0,
            sharpe_ratio=0.0,
            sortino_ratio=0.0,
            calmar_ratio=0.0,
            max_drawdown=0.0,
            max_drawdown_duration=0.0
        )

        result = BacktestResult(
            equity_curve=equity_curve,
            trade_log=pd.DataFrame(),
            summary_stats={},
            metrics=metrics,
            execution_time=0.1,
            config=config
        )

        # Test the actual structure
        assert result.equity_curve.equals(equity_curve)
        assert len(result.trade_log) == 0
        assert result.summary_stats == {}
        assert result.execution_time == 0.1
        assert result.config == config
        assert result.metrics == metrics


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
        assert results.config.initial_cash == 100000.0
        assert results.summary_stats["initial_cash"] == 100000.0
        assert abs(results.summary_stats["final_cash"] - 110000.0) < 0.01  # Allow for floating point precision
        assert abs(results.summary_stats["total_return"] - 0.10) < 0.01
        assert len(results.equity_curve) == 3
        assert results.metrics.total_return == 0.10
        assert results.metrics.total_trades == 100

        # Check stored results
        assert engine.get_results() is not None
        assert engine.get_equity_curve() is not None
        assert engine.get_results() == results
        assert engine.get_equity_curve().equals(results.equity_curve)

    def test_engine_with_different_configurations(self) -> None:
        """Test engine with different configurations."""
        engine = MockBacktestEngine()

        # Test with hourly data
        hourly_data = pd.DataFrame(
            {
                "close": np.random.randn(24) * 0.01 + 100,
            }
        )
        hourly_data.index = pd.date_range("2024-01-01", periods=24, freq="H")

        hourly_config = BacktestConfig(
            data_frequency="1h",
            initial_cash=50000.0,
            commission_rate=0.0005,
        )

        results = engine.run(MagicMock(), hourly_data, hourly_config)
        assert results.initial_cash == 50000.0
        assert len(results.equity_curve) == 24

        # Test with minute data
        minute_data = pd.DataFrame(
            {
                "close": np.random.randn(60) * 0.001 + 100,
            }
        )
        minute_data.index = pd.date_range("2024-01-01", periods=60, freq="1min")

        minute_config = BacktestConfig(
            data_frequency="1m",
            initial_cash=200000.0,
            commission_rate=0.001,
            slippage_model="volume_impact",
        )

        results = engine.run(MagicMock(), minute_data, minute_config)
        assert results.initial_cash == 200000.0
        assert len(results.equity_curve) == 60

    def test_engine_state_isolation(self) -> None:
        """Test that engine state is isolated between runs."""
        engine = MockBacktestEngine()

        # First run
        data1 = pd.DataFrame(
            {
                "close": [100, 105, 110],
            }
        )
        data1.index = pd.date_range("2024-01-01", periods=3, freq="D")

        config1 = BacktestConfig(initial_cash=100000.0)
        results1 = engine.run(MagicMock(), data1, config1)

        # Second run
        data2 = pd.DataFrame(
            {
                "close": [200, 205, 210],
            }
        )
        data2.index = pd.date_range("2024-02-01", periods=3, freq="D")

        config2 = BacktestConfig(initial_cash=200000.0)
        results2 = engine.run(MagicMock(), data2, config2)

        # Check that results are different
        assert results1.initial_cash == 100000.0
        assert results2.initial_cash == 200000.0
        assert engine.get_results() == results2
        assert engine.get_results() != results1

    def test_engine_with_realistic_strategy(self) -> None:
        """Test engine with a more realistic strategy mock."""
        engine = MockBacktestEngine()

        # Create realistic OHLCV data
        dates = pd.date_range("2024-01-01", periods=252, freq="D")  # Trading days
        np.random.seed(42)  # For reproducibility

        # Generate synthetic price data with drift
        returns = np.random.normal(0.0005, 0.02, 252)  # Daily returns
        prices = 100 * np.exp(np.cumsum(returns))  # Price series

        data = pd.DataFrame(
            {
                "open": prices * (1 + np.random.normal(0, 0.001, 252)),
                "high": prices * (1 + np.abs(np.random.normal(0, 0.01, 252))),
                "low": prices * (1 - np.abs(np.random.normal(0, 0.01, 252))),
                "close": prices,
                "volume": np.random.randint(100000, 1000000, 252),
            },
            index=dates,
        )

        # Create a mock strategy that simulates signals
        class MockStrategy:
            def __init__(self):
                self.signals = np.random.choice([-1, 0, 1], size=len(data))

            def generate_signals(self, data):
                return pd.Series(self.signals, index=data.index)

        strategy = MockStrategy()
        config = BacktestConfig(
            start_date=dates[0],
            end_date=dates[-1],
            initial_cash=100000.0,
        )

        results = engine.run(strategy, data, config)

        # Verify results
        assert results.total_trades >= 0
        assert len(results.equity_curve) == 252
        assert results.initial_cash == 100000.0
        assert isinstance(results.daily_returns, pd.Series)
        assert len(results.daily_returns) <= 252

    def test_error_handling(self) -> None:
        """Test engine error handling."""
        engine = MockBacktestEngine()

        # Test with empty data
        empty_data = pd.DataFrame()
        config = BacktestConfig()

        # Should still work but return minimal results
        results = engine.run(MagicMock(), empty_data, config)
        assert results is not None
        assert len(results.equity_curve) == 0

    def test_performance_metrics_consistency(self) -> None:
        """Test that performance metrics are consistent."""
        engine = MockBacktestEngine()

        data = pd.DataFrame(
            {
                "close": [100, 105, 110, 115, 120],
            }
        )
        data.index = pd.date_range("2024-01-01", periods=5, freq="D")

        config = BacktestConfig(initial_cash=100000.0)
        results = engine.run(MagicMock(), data, config)

        # Check consistency
        assert results.winning_trades + results.losing_trades <= results.total_trades
        assert results.total_trades >= 0
        assert results.win_rate >= 0 and results.win_rate <= 1

        # Check P&L calculations
        if results.total_trades > 0:
            expected_avg = (
                results.avg_win * results.winning_trades
                + results.avg_loss * results.losing_trades
            ) / results.total_trades
            assert abs(results.avg_trade - expected_avg) < 0.01
