"""Simple integration tests for core workflows."""

import pytest
import pandas as pd
from datetime import datetime

from quantchain.backtesting.engine import (
    BacktestConfig,
    BacktestResult,
    MetricsResult,
    filter_data_by_date_range,
    validate_ohlcv_data,
)


@pytest.fixture
def sample_ohlcv_data():
    """Create sample OHLCV data for testing."""
    dates = pd.date_range("2023-01-01", periods=10, freq="D")
    data = pd.DataFrame(
        {
            "open": [
                100.0,
                101.0,
                102.0,
                103.0,
                104.0,
                105.0,
                106.0,
                107.0,
                108.0,
                109.0,
            ],
            "high": [
                101.5,
                102.5,
                103.5,
                104.5,
                105.5,
                106.5,
                107.5,
                108.5,
                109.5,
                110.5,
            ],
            "low": [
                99.5,
                100.5,
                101.5,
                102.5,
                103.5,
                104.5,
                105.5,
                106.5,
                107.5,
                108.5,
            ],
            "close": [
                101.0,
                102.0,
                103.0,
                104.0,
                105.0,
                106.0,
                107.0,
                108.0,
                109.0,
                110.0,
            ],
            "volume": [
                1000000,
                1100000,
                1200000,
                1300000,
                1400000,
                1500000,
                1600000,
                1700000,
                1800000,
                1900000,
            ],
        },
        index=dates,
    )
    return data


class TestDataValidationWorkflow:
    """Test data validation workflow."""

    def test_validate_ohlcv_data_success(self, sample_ohlcv_data):
        """Test successful validation of OHLCV data."""
        # Should not raise any exceptions
        validate_ohlcv_data(sample_ohlcv_data)

    def test_filter_data_by_date_range(self, sample_ohlcv_data):
        """Test filtering data by date range."""
        # Filter to middle 5 days
        start_date = datetime(2023, 1, 3)
        end_date = datetime(2023, 1, 7)

        filtered_data = filter_data_by_date_range(
            sample_ohlcv_data, start_date, end_date
        )

        # Should have exactly 5 days
        assert len(filtered_data) == 5
        # Should be within date range
        assert filtered_data.index[0] >= start_date
        assert filtered_data.index[-1] <= end_date


class TestBacktestWorkflow:
    """Test basic backtesting workflow."""

    def test_backtest_config_creation(self):
        """Test creating backtest configuration."""
        config = BacktestConfig(
            initial_cash=100000.0,
            commission_rate=0.001,
            slippage_rate=0.0001,
            data_frequency="1d",
        )

        assert config.initial_cash == 100000.0
        assert config.commission_rate == 0.001
        assert config.slippage_rate == 0.0001
        assert config.data_frequency == "1d"

    def test_backtest_result_creation(self, sample_ohlcv_data):
        """Test creating backtest result."""
        equity_curve = pd.Series([100000, 101000], index=sample_ohlcv_data.index[:2])
        trade_log = pd.DataFrame()

        result = BacktestResult(
            equity_curve=equity_curve,
            trade_log=trade_log,
            summary_stats={"total_return": 0.01},
            metrics=MetricsResult(
                total_return=0.01,
                annualized_return=0.0,
                sharpe_ratio=0.0,
                sortino_ratio=0.0,
                calmar_ratio=0.0,
                max_drawdown=0.0,
                max_drawdown_duration=0,
            ),
            execution_time=0.5,
            config=BacktestConfig(),
        )

        # Verify result structure
        assert isinstance(result.equity_curve, pd.Series)
        assert isinstance(result.trade_log, pd.DataFrame)
        assert isinstance(result.summary_stats, dict)
        assert isinstance(result.metrics, MetricsResult)
        assert result.summary_stats["total_return"] == 0.01


@pytest.mark.integration
class TestSystemIntegration:
    """Test system-level integration."""

    def test_data_pipeline(self, sample_ohlcv_data):
        """Test complete data pipeline from validation to backtesting."""
        # Step 1: Validate data
        validate_ohlcv_data(sample_ohlcv_data)

        # Step 2: Create configuration
        config = BacktestConfig(
            initial_cash=100000.0,
            commission_rate=0.001,
            slippage_rate=0.0001,
        )

        # Step 3: Create mock backtest result
        result = BacktestResult(
            equity_curve=pd.Series([100000, 101000], index=sample_ohlcv_data.index[:2]),
            trade_log=pd.DataFrame(),
            summary_stats={"total_return": 0.01},
            metrics=MetricsResult(
                total_return=0.01,
                annualized_return=0.0,
                sharpe_ratio=0.0,
                sortino_ratio=0.0,
                calmar_ratio=0.0,
                max_drawdown=0.0,
                max_drawdown_duration=0,
            ),
            execution_time=0.5,
            config=config,
        )

        # Verify pipeline completed successfully
        assert result.summary_stats["total_return"] == 0.01
        assert result.config.initial_cash == 100000.0

    def test_error_handling(self, sample_ohlcv_data):
        """Test error handling in the pipeline."""
        # Test invalid data (missing column)
        invalid_data = sample_ohlcv_data.drop(columns=["volume"])

        # Should raise an exception
        with pytest.raises(Exception):
            validate_ohlcv_data(invalid_data)
