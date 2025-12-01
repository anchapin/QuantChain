"""Comprehensive tests for performance metrics calculation."""

import pandas as pd
import pytest

try:
    from quantchain.backtesting.performance_metrics import (
        InsufficientDataError,
        LibraryImportError,
        MetricsResult,
        MissingColumnError,
    )
except ImportError:
    pytest.skip("performance_metrics module not available", allow_module_level=True)


@pytest.mark.unit
class TestPerformanceMetricsExceptions:
    """Test exception classes."""

    def test_insufficient_data_error(self):
        """Test InsufficientDataError exception."""
        error = InsufficientDataError("Not enough data")
        assert str(error) == "Not enough data"
        assert isinstance(error, Exception)

    def test_library_import_error(self):
        """Test LibraryImportError exception."""
        error = LibraryImportError("Library not available")
        assert str(error) == "Library not available"
        assert isinstance(error, Exception)

    def test_missing_column_error(self):
        """Test MissingColumnError exception."""
        error = MissingColumnError("Column missing")
        assert str(error) == "Column missing"
        assert isinstance(error, Exception)


@pytest.mark.unit
class TestMetricsResult:
    """Test MetricsResult dataclass."""

    def test_metrics_result_creation(self):
        """Test creating MetricsResult with all fields."""
        timestamp = pd.Timestamp("2023-01-01")
        result = MetricsResult(
            total_return=0.15,
            annualized_return=0.12,
            sharpe_ratio=1.5,
            sortino_ratio=2.0,
            calmar_ratio=1.8,
            max_drawdown=0.05,
            max_drawdown_duration=30,
            max_drawdown_start=timestamp,
            max_drawdown_end=timestamp + pd.Timedelta(days=30),
            volatility=0.1,
            win_rate=0.6,
            profit_factor=1.5,
            total_trades=100,
            winning_trades=60,
            losing_trades=40,
            avg_win=0.02,
            avg_loss=-0.01,
            best_trade=0.05,
            worst_trade=-0.03,
            avg_trade_duration=5.0,
            avg_trade_duration_days=5.0,
            sharpe_ratio_qstats=1.5,
            sortino_ratio_qstats=2.0,
            omega_ratio=1.2,
            alpha=0.05,
            beta=1.1,
            information_ratio=0.8,
            var_95=0.02,
        )
        assert result.total_return == 0.15
        assert result.annualized_return == 0.12
        assert result.sharpe_ratio == 1.5
        assert result.win_rate == 0.6
        assert result.total_trades == 100

    def test_metrics_result_defaults(self):
        """Test MetricsResult with minimal required fields."""
        timestamp = pd.Timestamp("2023-01-01")
        result = MetricsResult(
            total_return=0.0,
            annualized_return=0.0,
            sharpe_ratio=0.0,
            sortino_ratio=0.0,
            calmar_ratio=0.0,
            max_drawdown=0.0,
            max_drawdown_duration=0,
            max_drawdown_start=timestamp,
            max_drawdown_end=timestamp,
            volatility=0.0,
            win_rate=0.0,
            profit_factor=0.0,
            total_trades=0,
            winning_trades=0,
            losing_trades=0,
            avg_win=0.0,
            avg_loss=0.0,
            best_trade=0.0,
            worst_trade=0.0,
            avg_trade_duration=0.0,
            avg_trade_duration_days=0.0,
            sharpe_ratio_qstats=0.0,
            sortino_ratio_qstats=0.0,
            omega_ratio=0.0,
            alpha=0.0,
            beta=0.0,
            information_ratio=0.0,
            var_95=0.0,
        )
        assert result.total_return == 0.0
        assert result.total_trades == 0
        assert result.win_rate == 0.0
