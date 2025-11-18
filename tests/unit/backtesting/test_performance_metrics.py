"""Comprehensive tests for quantchain.backtesting.performance_metrics module."""

import pytest
import pandas as pd
import numpy as np
from unittest.mock import Mock, patch

from quantchain.backtesting.performance_metrics import (
    InsufficientDataError,
    LibraryImportError,
    MissingColumnError,
    MetricsResult,
    PerformanceMetrics,
)


@pytest.mark.unit
class TestExceptions:
    """Test performance metrics exceptions."""

    def test_insufficient_data_error(self) -> None:
        """Test InsufficientDataError exception."""
        error = InsufficientDataError("Test message")
        assert str(error) == "Test message"

    def test_library_import_error(self) -> None:
        """Test LibraryImportError exception."""
        error = LibraryImportError("Test message")
        assert str(error) == "Test message"

    def test_missing_column_error(self) -> None:
        """Test MissingColumnError exception."""
        error = MissingColumnError("Test message")
        assert str(error) == "Test message"


@pytest.mark.unit
class TestMetricsResult:
    """Test MetricsResult dataclass."""

    def test_metrics_result_creation(self) -> None:
        """Test MetricsResult creation with all fields."""
        timestamp = pd.Timestamp("2023-01-01")
        result = MetricsResult(
            total_return=0.15,
            annualized_return=0.12,
            sharpe_ratio=1.5,
            sortino_ratio=2.0,
            calmar_ratio=1.2,
            max_drawdown=-0.05,
            max_drawdown_duration=30,
            max_drawdown_start=timestamp,
            max_drawdown_end=timestamp + pd.Timedelta(days=30),
            volatility=0.1,
            win_rate=0.6,
            profit_factor=1.8,
            total_trades=100,
            winning_trades=60,
            losing_trades=40,
            avg_win=0.02,
            avg_loss=-0.01,
            best_trade=0.05,
            worst_trade=-0.03,
            avg_trade_duration=5.5,
            avg_trade_duration_days=5.5,
            sharpe_ratio_qstats=1.4,
            sortino_ratio_qstats=1.9,
            omega_ratio=1.3,
            alpha=0.02,
            beta=0.8,
            information_ratio=0.5,
            var_95=-0.02
        )

        assert result.total_return == 0.15
        assert result.annualized_return == 0.12
        assert result.sharpe_ratio == 1.5
        assert result.win_rate == 0.6
        assert result.total_trades == 100

    def test_metrics_result_equality(self) -> None:
        """Test MetricsResult equality."""
        result1 = MetricsResult(
            total_return=0.15, annualized_return=0.12, sharpe_ratio=1.5,
            sortino_ratio=2.0, calmar_ratio=1.2, max_drawdown=-0.05,
            max_drawdown_duration=30, max_drawdown_start=pd.Timestamp("2023-01-01"),
            max_drawdown_end=pd.Timestamp("2023-01-31"), volatility=0.1,
            win_rate=0.6, profit_factor=1.8, total_trades=100,
            winning_trades=60, losing_trades=40, avg_win=0.02, avg_loss=-0.01,
            best_trade=0.05, worst_trade=-0.03, avg_trade_duration=5.5,
            avg_trade_duration_days=5.5, sharpe_ratio_qstats=1.4,
            sortino_ratio_qstats=1.9, omega_ratio=1.3, alpha=0.02, beta=0.8,
            information_ratio=0.5, var_95=-0.02
        )

        result2 = MetricsResult(
            total_return=0.15, annualized_return=0.12, sharpe_ratio=1.5,
            sortino_ratio=2.0, calmar_ratio=1.2, max_drawdown=-0.05,
            max_drawdown_duration=30, max_drawdown_start=pd.Timestamp("2023-01-01"),
            max_drawdown_end=pd.Timestamp("2023-01-31"), volatility=0.1,
            win_rate=0.6, profit_factor=1.8, total_trades=100,
            winning_trades=60, losing_trades=40, avg_win=0.02, avg_loss=-0.01,
            best_trade=0.05, worst_trade=-0.03, avg_trade_duration=5.5,
            avg_trade_duration_days=5.5, sharpe_ratio_qstats=1.4,
            sortino_ratio_qstats=1.9, omega_ratio=1.3, alpha=0.02, beta=0.8,
            information_ratio=0.5, var_95=-0.02
        )

        assert result1 == result2


@pytest.mark.unit
class TestPerformanceMetrics:
    """Test PerformanceMetrics class."""

    def test_init_without_benchmark(self) -> None:
        """Test initialization without benchmark."""
        metrics = PerformanceMetrics()
        assert metrics.benchmark_returns is None
        assert metrics.risk_free_rate == 0.02

    def test_init_with_benchmark(self) -> None:
        """Test initialization with benchmark."""
        benchmark = pd.Series([0.01, 0.02, -0.01], index=pd.date_range("2023-01-01", periods=3))
        metrics = PerformanceMetrics(benchmark_returns=benchmark, risk_free_rate=0.03)
        assert metrics.benchmark_returns is not None
        assert metrics.risk_free_rate == 0.03

    def test_init_with_custom_risk_free_rate(self) -> None:
        """Test initialization with custom risk-free rate."""
        metrics = PerformanceMetrics(risk_free_rate=0.05)
        assert metrics.risk_free_rate == 0.05

    def test_calculate_returns_insufficient_data(self) -> None:
        """Test calculate_returns with insufficient data."""
        metrics = PerformanceMetrics()
        equity_curve = pd.Series([1000], index=pd.date_range("2023-01-01", periods=1))

        with pytest.raises(InsufficientDataError, match="Equity curve must have at least 2 points"):
            metrics.calculate_returns(equity_curve)

    def test_calculate_returns_success(self) -> None:
        """Test calculate_returns success."""
        metrics = PerformanceMetrics()
        equity_curve = pd.Series([1000, 1100, 1050], index=pd.date_range("2023-01-01", periods=3))

        returns = metrics.calculate_returns(equity_curve)

        assert len(returns) == 2  # One less than equity curve due to pct_change
        assert not returns.isnull().any()

    def test_calculate_total_return_insufficient_data(self) -> None:
        """Test calculate_total_return with insufficient data."""
        metrics = PerformanceMetrics()
        equity_curve = pd.Series([], index=pd.date_range("2023-01-01", periods=0), dtype=float)

        with pytest.raises(InsufficientDataError, match="Equity curve must have at least 1 point"):
            metrics.calculate_total_return(equity_curve)

    def test_calculate_total_return_single_point(self) -> None:
        """Test calculate_total_return with single point."""
        metrics = PerformanceMetrics()
        equity_curve = pd.Series([1000], index=pd.date_range("2023-01-01", periods=1))

        total_return = metrics.calculate_total_return(equity_curve)
        assert total_return == 0.0  # (1000/1000) - 1 = 0

    def test_calculate_total_return_success(self) -> None:
        """Test calculate_total_return success."""
        metrics = PerformanceMetrics()
        equity_curve = pd.Series([1000, 1100, 1200], index=pd.date_range("2023-01-01", periods=3))

        total_return = metrics.calculate_total_return(equity_curve)
        assert total_return == 0.2  # (1200/1000) - 1 = 0.2

    def test_calculate_annualized_return_less_than_one_year(self) -> None:
        """Test calculate_annualized_return with less than one year."""
        metrics = PerformanceMetrics()
        # 6 months of data
        equity_curve = pd.Series(
            [1000, 1100],
            index=pd.date_range("2023-01-01", periods=2, freq="6M")
        )

        annualized_return = metrics.calculate_annualized_return(equity_curve)
        # Should annualize the 0.1 return over 6 months
        expected = (1 + 0.1) ** (1 / 0.5) - 1
        assert abs(annualized_return - expected) < 0.01

    def test_calculate_annualized_return_more_than_one_year(self) -> None:
        """Test calculate_annualized_return with more than one year."""
        metrics = PerformanceMetrics()
        # 2 years of data
        equity_curve = pd.Series(
            [1000, 1200],
            index=pd.date_range("2023-01-01", periods=2, freq="2Y")
        )

        annualized_return = metrics.calculate_annualized_return(equity_curve)
        # Should compound the 0.2 return over 2 years
        expected = (1 + 0.2) ** (1 / 2) - 1
        assert abs(annualized_return - expected) < 0.01

    def test_calculate_volatility_insufficient_data(self) -> None:
        """Test calculate_volatility with insufficient data."""
        metrics = PerformanceMetrics()
        equity_curve = pd.Series([1000], index=pd.date_range("2023-01-01", periods=1))

        with pytest.raises(InsufficientDataError):
            metrics.calculate_volatility(equity_curve)

    def test_calculate_volatility_success(self) -> None:
        """Test calculate_volatility success."""
        metrics = PerformanceMetrics()
        equity_curve = pd.Series([1000, 1100, 1050, 1150, 1200], index=pd.date_range("2023-01-01", periods=5))

        volatility = metrics.calculate_volatility(equity_curve)
        assert volatility > 0
        assert isinstance(volatility, float)

    def test_calculate_sharpe_ratio_insufficient_data(self) -> None:
        """Test calculate_sharpe_ratio with insufficient data."""
        metrics = PerformanceMetrics()
        equity_curve = pd.Series([1000, 1100], index=pd.date_range("2023-01-01", periods=2))

        with pytest.raises(InsufficientDataError):
            metrics.calculate_sharpe_ratio(equity_curve)

    def test_calculate_sharpe_ratio_zero_volatility(self) -> None:
        """Test calculate_sharpe_ratio with zero volatility."""
        metrics = PerformanceMetrics()
        # Constant equity curve should have zero volatility
        equity_curve = pd.Series([1000, 1000, 1000, 1000], index=pd.date_range("2023-01-01", periods=4))

        sharpe = metrics.calculate_sharpe_ratio(equity_curve)
        assert sharpe == 0.0

    def test_calculate_sharpe_ratio_success(self) -> None:
        """Test calculate_sharpe_ratio success."""
        metrics = PerformanceMetrics()
        equity_curve = pd.Series([1000, 1100, 1050, 1150, 1200], index=pd.date_range("2023-01-01", periods=5))

        sharpe = metrics.calculate_sharpe_ratio(equity_curve)
        assert isinstance(sharpe, float)

    def test_calculate_sharpe_ratio_with_custom_frequency(self) -> None:
        """Test calculate_sharpe_ratio with custom frequency."""
        metrics = PerformanceMetrics()
        equity_curve = pd.Series([1000, 1100, 1050, 1150, 1200], index=pd.date_range("2023-01-01", periods=5))

        sharpe_daily = metrics.calculate_sharpe_ratio(equity_curve, frequency="1d")
        sharpe_weekly = metrics.calculate_sharpe_ratio(equity_curve, frequency="1w")

        assert isinstance(sharpe_daily, float)
        assert isinstance(sharpe_weekly, float)

    def test_calculate_sortino_ratio_insufficient_data(self) -> None:
        """Test calculate_sortino_ratio with insufficient data."""
        metrics = PerformanceMetrics()
        equity_curve = pd.Series([1000, 1100], index=pd.date_range("2023-01-01", periods=2))

        with pytest.raises(InsufficientDataError):
            metrics.calculate_sortino_ratio(equity_curve)

    def test_calculate_sortino_ratio_success(self) -> None:
        """Test calculate_sortino_ratio success."""
        metrics = PerformanceMetrics()
        equity_curve = pd.Series([1000, 1100, 1050, 1150, 1200], index=pd.date_range("2023-01-01", periods=5))

        sortino = metrics.calculate_sortino_ratio(equity_curve)
        assert isinstance(sortino, float)

    def test_calculate_max_drawdown_insufficient_data(self) -> None:
        """Test calculate_max_drawdown with insufficient data."""
        metrics = PerformanceMetrics()
        equity_curve = pd.Series([1000], index=pd.date_range("2023-01-01", periods=1))

        with pytest.raises(InsufficientDataError):
            metrics.calculate_max_drawdown(equity_curve)

    def test_calculate_max_drawdown_no_drawdown(self) -> None:
        """Test calculate_max_drawdown with no drawdown."""
        metrics = PerformanceMetrics()
        # Monotonically increasing equity curve
        equity_curve = pd.Series([1000, 1100, 1200, 1300], index=pd.date_range("2023-01-01", periods=4))

        drawdown = metrics.calculate_max_drawdown(equity_curve)
        assert drawdown["max_drawdown"] == 0.0
        assert drawdown["max_drawdown_pct"] == 0.0

    def test_calculate_max_drawdown_with_drawdown(self) -> None:
        """Test calculate_max_drawdown with drawdown."""
        metrics = PerformanceMetrics()
        equity_curve = pd.Series([1000, 1200, 1100, 900, 1000], index=pd.date_range("2023-01-01", periods=5))

        drawdown = metrics.calculate_max_drawdown(equity_curve)
        assert drawdown["max_drawdown"] < 0  # Should be negative
        assert drawdown["max_drawdown_pct"] < 0  # Should be negative
        assert "max_drawdown_start" in drawdown
        assert "max_drawdown_end" in drawdown
        assert isinstance(drawdown["max_drawdown_start"], pd.Timestamp)
        assert isinstance(drawdown["max_drawdown_end"], pd.Timestamp)

    def test_calculate_max_drawdown_duration_insufficient_data(self) -> None:
        """Test calculate_max_drawdown_duration with insufficient data."""
        metrics = PerformanceMetrics()
        equity_curve = pd.Series([1000], index=pd.date_range("2023-01-01", periods=1))

        with pytest.raises(InsufficientDataError):
            metrics.calculate_max_drawdown_duration(equity_curve)

    def test_calculate_max_drawdown_duration_no_drawdown(self) -> None:
        """Test calculate_max_drawdown_duration with no drawdown."""
        metrics = PerformanceMetrics()
        equity_curve = pd.Series([1000, 1100, 1200, 1300], index=pd.date_range("2023-01-01", periods=4))

        duration = metrics.calculate_max_drawdown_duration(equity_curve)
        assert duration == 0

    def test_calculate_max_drawdown_duration_with_drawdown(self) -> None:
        """Test calculate_max_drawdown_duration with drawdown."""
        metrics = PerformanceMetrics()
        equity_curve = pd.Series([1000, 1200, 1100, 900, 800, 1000], index=pd.date_range("2023-01-01", periods=6))

        duration = metrics.calculate_max_drawdown_duration(equity_curve)
        assert duration > 0
        assert isinstance(duration, int)

    def test_calculate_calmar_ratio_no_drawdown(self) -> None:
        """Test calculate_calmar_ratio with no drawdown."""
        metrics = PerformanceMetrics()
        equity_curve = pd.Series([1000, 1100, 1200, 1300], index=pd.date_range("2023-01-01", periods=4))

        calmar = metrics.calculate_calmar_ratio(equity_curve)
        assert calmar > 0

    def test_calculate_calmar_ratio_with_drawdown(self) -> None:
        """Test calculate_calmar_ratio with drawdown."""
        metrics = PerformanceMetrics()
        equity_curve = pd.Series([1000, 1200, 1100, 900, 1000], index=pd.date_range("2023-01-01", periods=5))

        calmar = metrics.calculate_calmar_ratio(equity_curve)
        assert isinstance(calmar, float)

    def test_calculate_win_rate_no_trades(self) -> None:
        """Test calculate_win_rate with no trades."""
        metrics = PerformanceMetrics()
        trades = pd.DataFrame(columns=["pnl"])

        with pytest.raises(InsufficientDataError):
            metrics.calculate_win_rate(trades)

    def test_calculate_win_rate_missing_column(self) -> None:
        """Test calculate_win_rate with missing PnL column."""
        metrics = PerformanceMetrics()
        trades = pd.DataFrame({"entry_price": [100, 110], "exit_price": [110, 120]})

        with pytest.raises(MissingColumnError):
            metrics.calculate_win_rate(trades)

    def test_calculate_win_rate_all_winning(self) -> None:
        """Test calculate_win_rate with all winning trades."""
        metrics = PerformanceMetrics()
        trades = pd.DataFrame({"pnl": [10, 20, 15]})

        win_rate = metrics.calculate_win_rate(trades)
        assert win_rate == 1.0

    def test_calculate_win_rate_all_losing(self) -> None:
        """Test calculate_win_rate with all losing trades."""
        metrics = PerformanceMetrics()
        trades = pd.DataFrame({"pnl": [-10, -20, -15]})

        win_rate = metrics.calculate_win_rate(trades)
        assert win_rate == 0.0

    def test_calculate_win_rate_mixed(self) -> None:
        """Test calculate_win_rate with mixed trades."""
        metrics = PerformanceMetrics()
        trades = pd.DataFrame({"pnl": [10, -5, 20, -10, 15]})

        win_rate = metrics.calculate_win_rate(trades)
        assert win_rate == 0.6  # 3 winning out of 5 trades

    def test_calculate_profit_factor_no_trades(self) -> None:
        """Test calculate_profit_factor with no trades."""
        metrics = PerformanceMetrics()
        trades = pd.DataFrame(columns=["pnl"])

        with pytest.raises(InsufficientDataError):
            metrics.calculate_profit_factor(trades)

    def test_calculate_profit_factor_missing_column(self) -> None:
        """Test calculate_profit_factor with missing PnL column."""
        metrics = PerformanceMetrics()
        trades = pd.DataFrame({"entry_price": [100, 110], "exit_price": [110, 120]})

        with pytest.raises(MissingColumnError):
            metrics.calculate_profit_factor(trades)

    def test_calculate_profit_factor_all_winning(self) -> None:
        """Test calculate_profit_factor with all winning trades."""
        metrics = PerformanceMetrics()
        trades = pd.DataFrame({"pnl": [10, 20, 15]})

        profit_factor = metrics.calculate_profit_factor(trades)
        assert profit_factor == float('inf')  # No losing trades

    def test_calculate_profit_factor_all_losing(self) -> None:
        """Test calculate_profit_factor with all losing trades."""
        metrics = PerformanceMetrics()
        trades = pd.DataFrame({"pnl": [-10, -20, -15]})

        profit_factor = metrics.calculate_profit_factor(trades)
        assert profit_factor == 0.0  # No winning trades

    def test_calculate_profit_factor_mixed(self) -> None:
        """Test calculate_profit_factor with mixed trades."""
        metrics = PerformanceMetrics()
        trades = pd.DataFrame({"pnl": [10, -5, 20, -10, 15]})

        profit_factor = metrics.calculate_profit_factor(trades)
        gross_profit = 10 + 20 + 15  # 45
        gross_loss = abs(-5) + abs(-10)  # 15
        expected = gross_profit / gross_loss  # 3.0
        assert abs(profit_factor - expected) < 0.01

    def test_calculate_average_win_loss_no_trades(self) -> None:
        """Test calculate_average_win_loss with no trades."""
        metrics = PerformanceMetrics()
        trades = pd.DataFrame(columns=["pnl"])

        with pytest.raises(InsufficientDataError):
            metrics.calculate_average_win_loss(trades)

    def test_calculate_average_win_loss_missing_column(self) -> None:
        """Test calculate_average_win_loss with missing PnL column."""
        metrics = PerformanceMetrics()
        trades = pd.DataFrame({"entry_price": [100, 110], "exit_price": [110, 120]})

        with pytest.raises(MissingColumnError):
            metrics.calculate_average_win_loss(trades)

    def test_calculate_average_win_loss_mixed(self) -> None:
        """Test calculate_average_win_loss with mixed trades."""
        metrics = PerformanceMetrics()
        trades = pd.DataFrame({"pnl": [10, -5, 20, -10, 15]})

        result = metrics.calculate_average_win_loss(trades)
        assert result["avg_win"] == 15.0  # (10 + 20 + 15) / 3
        assert result["avg_loss"] == -7.5  # (-5 + -10) / 2

    def test_calculate_best_worst_trade_no_trades(self) -> None:
        """Test calculate_best_worst_trade with no trades."""
        metrics = PerformanceMetrics()
        trades = pd.DataFrame(columns=["pnl"])

        with pytest.raises(InsufficientDataError):
            metrics.calculate_best_worst_trade(trades)

    def test_calculate_best_worst_trade_missing_column(self) -> None:
        """Test calculate_best_worst_trade with missing PnL column."""
        metrics = PerformanceMetrics()
        trades = pd.DataFrame({"entry_price": [100, 110], "exit_price": [110, 120]})

        with pytest.raises(MissingColumnError):
            metrics.calculate_best_worst_trade(trades)

    def test_calculate_best_worst_trade_mixed(self) -> None:
        """Test calculate_best_worst_trade with mixed trades."""
        metrics = PerformanceMetrics()
        trades = pd.DataFrame({"pnl": [10, -5, 20, -10, 15]})

        result = metrics.calculate_best_worst_trade(trades)
        assert result["best_trade"] == 20.0
        assert result["worst_trade"] == -10.0

    def test_calculate_average_trade_duration_no_trades(self) -> None:
        """Test calculate_average_trade_duration with no trades."""
        metrics = PerformanceMetrics()
        trades = pd.DataFrame(columns=["entry_time", "exit_time"])

        with pytest.raises(InsufficientDataError):
            metrics.calculate_average_trade_duration(trades)

    def test_calculate_average_trade_duration_missing_columns(self) -> None:
        """Test calculate_average_trade_duration with missing time columns."""
        metrics = PerformanceMetrics()
        trades = pd.DataFrame({"pnl": [10, -5], "entry_price": [100, 110]})

        with pytest.raises(MissingColumnError):
            metrics.calculate_average_trade_duration(trades)

    def test_calculate_average_trade_duration_success(self) -> None:
        """Test calculate_average_trade_duration success."""
        metrics = PerformanceMetrics()
        trades = pd.DataFrame({
            "entry_time": pd.date_range("2023-01-01", periods=3, freq="1D"),
            "exit_time": pd.date_range("2023-01-02", periods=3, freq="1D")
        })

        result = metrics.calculate_average_trade_duration(trades)
        assert "avg_duration" in result
        assert "avg_duration_days" in result
        assert result["avg_duration_days"] == 1.0

    def test_calculate_comprehensive_metrics_with_trades(self) -> None:
        """Test calculate_comprehensive_metrics with trades."""
        metrics = PerformanceMetrics()
        equity_curve = pd.Series([1000, 1100, 1050, 1150, 1200], index=pd.date_range("2023-01-01", periods=5))

        trades = pd.DataFrame({
            "pnl": [10, -5, 20, -10, 15],
            "entry_time": pd.date_range("2023-01-01", periods=5, freq="1D"),
            "exit_time": pd.date_range("2023-01-02", periods=5, freq="1D")
        })

        result = metrics.calculate_comprehensive_metrics(equity_curve, trades)
        assert isinstance(result, MetricsResult)
        assert hasattr(result, 'total_return')
        assert hasattr(result, 'sharpe_ratio')
        assert hasattr(result, 'win_rate')
        assert hasattr(result, 'total_trades')

    def test_calculate_comprehensive_metrics_without_trades(self) -> None:
        """Test calculate_comprehensive_metrics without trades."""
        metrics = PerformanceMetrics()
        equity_curve = pd.Series([1000, 1100, 1050, 1150, 1200], index=pd.date_range("2023-01-01", periods=5))

        result = metrics.calculate_comprehensive_metrics(equity_curve)
        assert isinstance(result, MetricsResult)
        assert hasattr(result, 'total_return')
        assert hasattr(result, 'sharpe_ratio')
        # Trade-related fields should have default values
        assert result.total_trades == 0
        assert result.winning_trades == 0
        assert result.losing_trades == 0

    def test_calculate_comprehensive_metrics_with_benchmark(self) -> None:
        """Test calculate_comprehensive_metrics with benchmark."""
        benchmark = pd.Series([0.01, 0.02, -0.01, 0.01, 0.02], index=pd.date_range("2023-01-01", periods=5))
        metrics = PerformanceMetrics(benchmark_returns=benchmark)
        equity_curve = pd.Series([1000, 1100, 1050, 1150, 1200], index=pd.date_range("2023-01-01", periods=5))

        result = metrics.calculate_comprehensive_metrics(equity_curve)
        assert isinstance(result, MetricsResult)
        # Should have benchmark-related metrics
        assert hasattr(result, 'alpha')
        assert hasattr(result, 'beta')
        assert hasattr(result, 'information_ratio')
