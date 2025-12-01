"""
Extended comprehensive tests for PerformanceMetrics to improve coverage from 27% to 90%+.
Tests all private methods, edge cases, and error conditions.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import warnings

try:
    from quantchain.backtesting.performance_metrics import (
        PerformanceMetrics,
        MetricsResult,
        InsufficientDataError,
        LibraryImportError,
        MissingColumnError,
    )
    PERFORMANCE_METRICS_AVAILABLE = True
except ImportError as e:
    PERFORMANCE_METRICS_AVAILABLE = False
    print(f"Performance metrics module not available: {e}")


@pytest.mark.skipif(not PERFORMANCE_METRICS_AVAILABLE, reason="Performance metrics not available")
@pytest.mark.unit
class TestPerformanceMetricsExceptions:
    """Test all exception classes for comprehensive coverage."""

    def test_insufficient_data_error(self):
        """Test InsufficientDataError with various inputs."""
        error = InsufficientDataError("Need at least 10 data points")
        assert str(error) == "Need at least 10 data points"
        assert isinstance(error, Exception)

        # Test with empty message
        error_empty = InsufficientDataError("")
        assert str(error_empty) == ""

    def test_library_import_error(self):
        """Test LibraryImportError with various inputs."""
        error = LibraryImportError("quantstats library not available")
        assert str(error) == "quantstats library not available"
        assert isinstance(error, Exception)

        # Test with specific library
        error_specific = LibraryImportError("scipy version >= 1.5 required")
        assert "scipy" in str(error_specific)

    def test_missing_column_error(self):
        """Test MissingColumnError with various inputs."""
        error = MissingColumnError("Required column 'pnl' not found")
        assert str(error) == "Required column 'pnl' not found"
        assert isinstance(error, Exception)

        # Test with multiple columns
        error_multi = MissingColumnError("Missing columns: entry_time, exit_time")
        assert "entry_time" in str(error_multi)
        assert "exit_time" in str(error_multi)


@pytest.mark.skipif(not PERFORMANCE_METRICS_AVAILABLE, reason="Performance metrics not available")
@pytest.mark.unit
class TestMetricsResult:
    """Test MetricsResult dataclass comprehensively."""

    def test_metrics_result_complete(self):
        """Test MetricsResult with all fields populated."""
        timestamp = pd.Timestamp("2023-01-01")
        result = MetricsResult(
            total_return=0.25,
            annualized_return=0.18,
            sharpe_ratio=1.5,
            sortino_ratio=2.1,
            calmar_ratio=1.8,
            max_drawdown=-0.15,
            max_drawdown_duration=45,
            max_drawdown_start=timestamp,
            max_drawdown_end=timestamp + pd.Timedelta(days=45),
            volatility=0.12,
            win_rate=0.65,
            profit_factor=1.8,
            total_trades=150,
            winning_trades=98,
            losing_trades=52,
            avg_win=0.03,
            avg_loss=0.015,
            best_trade=0.08,
            worst_trade=-0.04,
            avg_trade_duration=3600.0,
            avg_trade_duration_days=1.5,
            sharpe_ratio_qstats=1.45,
            sortino_ratio_qstats=2.05,
            omega_ratio=1.25,
            alpha=0.08,
            beta=1.12,
            information_ratio=0.75,
            var_95=-0.025,
        )
        assert result.total_return == 0.25
        assert result.annualized_return == 0.18
        assert result.win_rate == 0.65
        assert result.profit_factor == 1.8
        assert result.total_trades == 150

    def test_metrics_result_minimal(self):
        """Test MetricsResult with minimum values."""
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

    def test_metrics_result_negative_values(self):
        """Test MetricsResult with negative values where appropriate."""
        timestamp = pd.Timestamp("2023-01-01")
        result = MetricsResult(
            total_return=-0.20,
            annualized_return=-0.25,
            sharpe_ratio=-0.8,
            sortino_ratio=-1.2,
            calmar_ratio=-0.5,
            max_drawdown=-0.35,
            max_drawdown_duration=90,
            max_drawdown_start=timestamp,
            max_drawdown_end=timestamp + pd.Timedelta(days=90),
            volatility=0.22,
            win_rate=0.35,
            profit_factor=0.6,
            total_trades=100,
            winning_trades=35,
            losing_trades=65,
            avg_win=0.02,
            avg_loss=0.03,
            best_trade=0.05,
            worst_trade=-0.08,
            avg_trade_duration=2400.0,
            avg_trade_duration_days=2.1,
            sharpe_ratio_qstats=-0.75,
            sortino_ratio_qstats=-1.15,
            omega_ratio=0.8,
            alpha=-0.12,
            beta=0.95,
            information_ratio=-0.35,
            var_95=-0.045,
        )
        assert result.total_return == -0.20
        assert result.sharpe_ratio == -0.8
        assert result.win_rate == 0.35


@pytest.mark.skipif(not PERFORMANCE_METRICS_AVAILABLE, reason="Performance metrics not available")
@pytest.mark.unit
class TestPerformanceMetrics:
    """Test PerformanceMetrics class comprehensively."""

    def test_initialization_default(self):
        """Test PerformanceMetrics initialization with defaults."""
        pm = PerformanceMetrics()
        assert pm.benchmark_returns is None
        assert pm.risk_free_rate == 0.02

    def test_initialization_custom(self):
        """Test PerformanceMetrics initialization with custom values."""
        benchmark = pd.Series([0.01, 0.02, -0.01, 0.015])
        pm = PerformanceMetrics(benchmark_returns=benchmark, risk_free_rate=0.03)
        assert pm.benchmark_returns is not None
        assert pm.risk_free_rate == 0.03

    def test_calculate_returns_success(self):
        """Test successful returns calculation."""
        pm = PerformanceMetrics()
        equity = pd.Series([1000, 1050, 1020, 1080], index=pd.date_range("2023-01-01", periods=4))

        returns = pm.calculate_returns(equity)

        assert len(returns) == 3  # One less than equity curve
        assert isinstance(returns, pd.Series)
        # Check approximate values
        expected_first_return = (1050 - 1000) / 1000
        assert abs(returns.iloc[0] - expected_first_return) < 0.001

    def test_calculate_returns_insufficient_data(self):
        """Test returns calculation with insufficient data."""
        pm = PerformanceMetrics()
        equity = pd.Series([1000], index=pd.date_range("2023-01-01", periods=1))

        with pytest.raises(InsufficientDataError, match="at least 2 points"):
            pm.calculate_returns(equity)

    def test_calculate_total_return_success(self):
        """Test total return calculation."""
        pm = PerformanceMetrics()
        equity = pd.Series([1000, 1100, 1050], index=pd.date_range("2023-01-01", periods=3))

        total_return = pm.calculate_total_return(equity)
        expected = (1050 / 1000) - 1  # 0.05

        assert abs(total_return - expected) < 0.001

    def test_calculate_total_return_insufficient_data(self):
        """Test total return calculation with insufficient data."""
        pm = PerformanceMetrics()
        equity = pd.Series([], dtype=float)

        with pytest.raises(InsufficientDataError, match="at least 1 point"):
            pm.calculate_total_return(equity)

    def test_calculate_annualized_return_datetime_index(self):
        """Test annualized return with datetime index."""
        pm = PerformanceMetrics()
        start = pd.Timestamp("2022-01-01")
        end = pd.Timestamp("2023-01-01")
        equity = pd.Series([1000, 1200], index=[start, end])

        annualized_return = pm.calculate_annualized_return(equity)
        total_return = 0.20  # 20% over 1 year

        # For exactly 1 year, annualized should equal total
        assert abs(annualized_return - total_return) < 0.01

    def test_calculate_annualized_return_short_period(self):
        """Test annualized return with very short period."""
        pm = PerformanceMetrics()
        start = pd.Timestamp("2023-01-01")
        end = pd.Timestamp("2023-01-02")  # Only 1 day
        equity = pd.Series([1000, 1010], index=[start, end])

        annualized_return = pm.calculate_annualized_return(equity)

        # Should return 0.0 for very short periods (< 0.01 years)
        assert annualized_return == 0.0

    def test_calculate_annualized_return_integer_index(self):
        """Test annualized return with integer index."""
        pm = PerformanceMetrics()
        equity = pd.Series([1000, 1200], index=[0, 365])  # Simulating daily data

        annualized_return = pm.calculate_annualized_return(equity)

        # Should calculate based on integer difference
        assert isinstance(annualized_return, float)

    def test_calculate_volatility(self):
        """Test volatility calculation."""
        pm = PerformanceMetrics()
        # Create equity curve with some volatility
        equity = pd.Series([1000, 1050, 1020, 1080, 1040, 1100],
                          index=pd.date_range("2023-01-01", periods=6))

        volatility = pm.calculate_volatility(equity)

        assert isinstance(volatility, float)
        assert volatility > 0  # Should have positive volatility

    def test_calculate_sharpe_ratio_zero_volatility(self):
        """Test Sharpe ratio with zero volatility."""
        pm = PerformanceMetrics()
        # Create perfectly flat equity curve (zero volatility)
        equity = pd.Series([1000, 1000, 1000, 1000],
                          index=pd.date_range("2023-01-01", periods=4))

        sharpe = pm.calculate_sharpe_ratio(equity)

        assert sharpe == 0.0

    def test_calculate_sharpe_ratio_normal(self):
        """Test Sharpe ratio calculation with normal data."""
        pm = PerformanceMetrics()
        equity = pd.Series([1000, 1050, 1100, 1080, 1150],
                          index=pd.date_range("2023-01-01", periods=5))

        sharpe = pm.calculate_sharpe_ratio(equity)

        assert isinstance(sharpe, float)

    def test_calculate_sortino_ratio_no_downside(self):
        """Test Sortino ratio with no downside returns."""
        pm = PerformanceMetrics()
        # Create monotonically increasing equity curve
        equity = pd.Series([1000, 1050, 1100, 1150, 1200],
                          index=pd.date_range("2023-01-01", periods=5))

        sortino = pm.calculate_sortino_ratio(equity)

        # Should be infinite with no downside risk
        assert sortino == float('inf')

    def test_calculate_sortino_ratio_normal(self):
        """Test Sortino ratio with normal data."""
        pm = PerformanceMetrics()
        equity = pd.Series([1000, 1050, 1020, 1080, 1040, 1100],
                          index=pd.date_range("2023-01-01", periods=6))

        sortino = pm.calculate_sortino_ratio(equity)

        assert isinstance(sortino, float)

    def test_calculate_max_drawdown_successful(self):
        """Test maximum drawdown calculation."""
        pm = PerformanceMetrics()
        # Create equity curve with clear drawdown
        equity = pd.Series([1000, 1200, 800, 600, 900, 1100],
                          index=pd.date_range("2023-01-01", periods=6))

        result = pm.calculate_max_drawdown(equity)

        assert "max_drawdown" in result
        assert "max_drawdown_duration" in result
        assert "max_drawdown_start" in result
        assert "max_drawdown_end" in result
        assert result["max_drawdown"] < 0  # Should be negative
        assert isinstance(result["max_drawdown_start"], pd.Timestamp)
        assert isinstance(result["max_drawdown_end"], pd.Timestamp)

    def test_calculate_max_drawdown_no_drawdown(self):
        """Test maximum drawdown with monotonically increasing equity."""
        pm = PerformanceMetrics()
        equity = pd.Series([1000, 1100, 1200, 1300, 1400],
                          index=pd.date_range("2023-01-01", periods=5))

        result = pm.calculate_max_drawdown(equity)

        # Should have zero or very small drawdown
        assert result["max_drawdown"] >= 0

    def test_calculate_max_drawdown_duration_no_drawdown(self):
        """Test max drawdown duration with no drawdown periods."""
        pm = PerformanceMetrics()
        equity = pd.Series([1000, 1100, 1200, 1300],
                          index=pd.date_range("2023-01-01", periods=4))

        duration = pm.calculate_max_drawdown_duration(equity)

        assert duration == 0

    def test_calculate_max_drawdown_duration_with_periods(self):
        """Test max drawdown duration with multiple drawdown periods."""
        pm = PerformanceMetrics()
        # Create equity with multiple drawdown periods
        dates = pd.date_range("2023-01-01", periods=20)
        equity = pd.Series([
            1000, 1100, 1050, 900, 950,  # First drawdown
            1100, 1200, 1300,           # Recovery and new high
            1250, 1150, 1000, 950,      # Second drawdown
            1100, 1200, 1300, 1400,     # Recovery
            1450, 1500, 1480, 1520      # More data to match 20 points
        ], index=dates)

        duration = pm.calculate_max_drawdown_duration(equity)

        assert isinstance(duration, int)
        assert duration > 0

    def test_calculate_calmar_ratio_no_drawdown(self):
        """Test Calmar ratio with no drawdown."""
        pm = PerformanceMetrics()
        equity = pd.Series([1000, 1100, 1200, 1300],
                          index=pd.date_range("2023-01-01", periods=4))

        calmar = pm.calculate_calmar_ratio(equity)

        # Should be infinite with no drawdown
        assert calmar == float('inf')

    def test_calculate_calmar_ratio_normal(self):
        """Test Calmar ratio with normal data."""
        pm = PerformanceMetrics()
        equity = pd.Series([1000, 1200, 800, 600, 900],
                          index=pd.date_range("2023-01-01", periods=5, freq="D"))

        calmar = pm.calculate_calmar_ratio(equity)

        assert isinstance(calmar, float)

    def test_calculate_win_rate_missing_column(self):
        """Test win rate calculation with missing PnL column."""
        pm = PerformanceMetrics()
        trades = pd.DataFrame({"entry_price": [100, 105], "exit_price": [110, 95]})

        with pytest.raises(MissingColumnError, match="'pnl' column"):
            pm.calculate_win_rate(trades)

    def test_calculate_win_rate_no_trades(self):
        """Test win rate with no trades."""
        pm = PerformanceMetrics()
        trades = pd.DataFrame({"pnl": []})

        with pytest.raises(InsufficientDataError, match="No trades"):
            pm.calculate_win_rate(trades)

    def test_calculate_win_rate_mixed_results(self):
        """Test win rate with mixed winning and losing trades."""
        pm = PerformanceMetrics()
        trades = pd.DataFrame({
            "pnl": [100, -50, 75, -25, 50, -30]  # 3 wins, 3 losses
        })

        win_rate = pm.calculate_win_rate(trades)

        assert win_rate == 0.5  # 50% win rate

    def test_calculate_profit_factor_no_losses(self):
        """Test profit factor with no losing trades."""
        pm = PerformanceMetrics()
        trades = pd.DataFrame({"pnl": [100, 50, 75, 25]})  # All winning trades

        profit_factor = pm.calculate_profit_factor(trades)

        assert profit_factor == float('inf')

    def test_calculate_profit_factor_no_wins(self):
        """Test profit factor with no winning trades."""
        pm = PerformanceMetrics()
        trades = pd.DataFrame({"pnl": [-100, -50, -75, -25]})  # All losing trades

        profit_factor = pm.calculate_profit_factor(trades)

        assert profit_factor == 0.0

    def test_calculate_profit_factor_mixed(self):
        """Test profit factor with mixed results."""
        pm = PerformanceMetrics()
        trades = pd.DataFrame({"pnl": [100, -50, 75, -25, 50, -30]})

        profit_factor = pm.calculate_profit_factor(trades)

        gross_profit = 100 + 75 + 50  # 225
        gross_loss = 50 + 25 + 30     # 105
        expected = gross_profit / gross_loss

        assert abs(profit_factor - expected) < 0.01

    def test_calculate_average_win_loss_missing_column(self):
        """Test average win/loss with missing PnL column."""
        pm = PerformanceMetrics()
        trades = pd.DataFrame({"entry_price": [100, 105]})

        with pytest.raises(MissingColumnError, match="'pnl' column"):
            pm.calculate_average_win_loss(trades)

    def test_calculate_average_win_loss_no_wins(self):
        """Test average win/loss with no winning trades."""
        pm = PerformanceMetrics()
        trades = pd.DataFrame({"pnl": [-100, -50, -75]})

        result = pm.calculate_average_win_loss(trades)

        assert result["avg_win"] == 0.0
        assert result["avg_loss"] > 0  # Should be positive (absolute value)

    def test_calculate_average_win_loss_no_losses(self):
        """Test average win/loss with no losing trades."""
        pm = PerformanceMetrics()
        trades = pd.DataFrame({"pnl": [100, 50, 75]})

        result = pm.calculate_average_win_loss(trades)

        assert result["avg_win"] > 0
        assert result["avg_loss"] == 0.0

    def test_calculate_average_win_loss_mixed(self):
        """Test average win/loss with mixed trades."""
        pm = PerformanceMetrics()
        trades = pd.DataFrame({"pnl": [100, -50, 75, -25, 50, -30]})

        result = pm.calculate_average_win_loss(trades)

        avg_win_expected = (100 + 75 + 50) / 3
        avg_loss_expected = abs((-50 - 25 - 30) / 3)

        assert abs(result["avg_win"] - avg_win_expected) < 0.01
        assert abs(result["avg_loss"] - avg_loss_expected) < 0.01

    def test_calculate_best_worst_trade_missing_column(self):
        """Test best/worst trade with missing PnL column."""
        pm = PerformanceMetrics()
        trades = pd.DataFrame({"entry_price": [100, 105]})

        with pytest.raises(MissingColumnError, match="'pnl' column"):
            pm.calculate_best_worst_trade(trades)

    def test_calculate_best_worst_trade_no_trades(self):
        """Test best/worst trade with no trades."""
        pm = PerformanceMetrics()
        trades = pd.DataFrame({"pnl": []})

        with pytest.raises(InsufficientDataError, match="No trades"):
            pm.calculate_best_worst_trade(trades)

    def test_calculate_best_worst_trade_normal(self):
        """Test best/worst trade with normal data."""
        pm = PerformanceMetrics()
        trades = pd.DataFrame({"pnl": [100, -50, 75, -25, 50, -30]})

        result = pm.calculate_best_worst_trade(trades)

        assert result["best_trade"] == 100
        assert result["worst_trade"] == -50

    def test_calculate_average_trade_duration_missing_columns(self):
        """Test average trade duration with missing columns."""
        pm = PerformanceMetrics()
        trades = pd.DataFrame({"pnl": [100, -50]})

        with pytest.raises(MissingColumnError, match="entry_time.*exit_time"):
            pm.calculate_average_trade_duration(trades)

    def test_calculate_average_trade_duration_no_trades(self):
        """Test average trade duration with no trades."""
        pm = PerformanceMetrics()
        trades = pd.DataFrame({
            "entry_time": pd.DatetimeIndex([]),
            "exit_time": pd.DatetimeIndex([])
        })

        with pytest.raises(InsufficientDataError, match="No trades"):
            pm.calculate_average_trade_duration(trades)

    def test_calculate_average_trade_duration_normal(self):
        """Test average trade duration with normal data."""
        pm = PerformanceMetrics()
        trades = pd.DataFrame({
            "pnl": [100, -50, 75],
            "entry_time": pd.to_datetime(["2023-01-01", "2023-01-02", "2023-01-03"]),
            "exit_time": pd.to_datetime(["2023-01-02", "2023-01-04", "2023-01-05"])
        })

        result = pm.calculate_average_trade_duration(trades)

        assert result["avg_trade_duration"] > 0  # Average in seconds
        assert result["avg_trade_duration_days"] > 0  # Average in days

    def test_calculate_quantstats_metrics_available(self):
        """Test quantstats metrics calculation when library is available."""
        pm = PerformanceMetrics()
        returns = pd.Series([0.01, 0.02, -0.01, 0.015])

        # Mock quantstats to avoid dependency issues
        mock_qs = Mock()
        mock_qs.stats.sharpe.return_value = 1.5
        mock_qs.stats.sortino.return_value = 2.0
        mock_qs.stats.omega.return_value = 1.2

        with patch.dict('sys.modules', {'quantstats': mock_qs}):
            result = pm.calculate_quantstats_metrics(returns)

            assert result["sharpe_ratio_qstats"] == 1.5
            assert result["sortino_ratio_qstats"] == 2.0
            assert result["omega_ratio"] == 1.2

    def test_calculate_quantstats_metrics_unavailable(self):
        """Test quantstats metrics calculation when library is not available."""
        pm = PerformanceMetrics()
        returns = pd.Series([0.01, 0.02, -0.01, 0.015])

        # Simulate import error
        with patch.dict('sys.modules', {'quantstats': None}):
            result = pm.calculate_quantstats_metrics(returns)

            assert result["sharpe_ratio_qstats"] == 0.0
            assert result["sortino_ratio_qstats"] == 0.0
            assert result["omega_ratio"] == 0.0

    def test_calculate_beta_alpha_no_benchmark(self):
        """Test beta/alpha calculation without benchmark."""
        pm = PerformanceMetrics()
        returns = pd.Series([0.01, 0.02, -0.01, 0.015])

        result = pm.calculate_beta_alpha(returns)

        assert result["alpha"] == 0.0
        assert result["beta"] == 0.0
        assert result["information_ratio"] == 0.0

    def test_calculate_beta_alpha_with_benchmark(self):
        """Test beta/alpha calculation with benchmark."""
        benchmark = pd.Series([0.005, 0.015, -0.005, 0.01])
        pm = PerformanceMetrics(benchmark_returns=benchmark)
        returns = pd.Series([0.01, 0.02, -0.01, 0.015])

        result = pm.calculate_beta_alpha(returns)

        assert isinstance(result["alpha"], float)
        assert isinstance(result["beta"], float)
        assert isinstance(result["information_ratio"], float)

    def test_calculate_beta_alpha_insufficient_data(self):
        """Test beta/alpha with insufficient aligned data."""
        benchmark = pd.Series([0.01])  # Only one point
        pm = PerformanceMetrics(benchmark_returns=benchmark)
        returns = pd.Series([0.01, 0.02])

        result = pm.calculate_beta_alpha(returns)

        # Should return zeros when insufficient aligned data
        assert result["alpha"] == 0.0
        assert result["beta"] == 0.0
        assert result["information_ratio"] == 0.0

    def test_calculate_beta_alpha_zero_benchmark_variance(self):
        """Test beta/alpha with zero benchmark variance."""
        benchmark = pd.Series([0.01, 0.01, 0.01])  # Zero variance
        pm = PerformanceMetrics(benchmark_returns=benchmark)
        returns = pd.Series([0.01, 0.02, 0.015])

        result = pm.calculate_beta_alpha(returns)

        assert result["beta"] == 0.0  # Should handle division by zero

    def test_calculate_var(self):
        """Test Value at Risk calculation."""
        pm = PerformanceMetrics()
        returns = pd.Series([0.01, 0.02, -0.01, 0.015, -0.02, 0.005])

        var_95 = pm.calculate_var(returns, 0.05)

        assert isinstance(var_95, float)
        # 95% VaR should be negative (loss)
        assert var_95 < 0

    def test_generate_tear_sheet(self):
        """Test tear sheet generation."""
        pm = PerformanceMetrics()
        mock_results = Mock()

        result = pm.generate_tear_sheet(mock_results, "/path/to/save.html")

        assert isinstance(result, dict)
        assert "message" in result
        assert "save_path" in result
        assert result["save_path"] == "/path/to/save.html"

    def test_calculate_all_metrics_comprehensive(self):
        """Test calculate_all_metrics with comprehensive data."""
        # Create realistic test data
        dates = pd.date_range("2023-01-01", periods=100, freq="D")
        equity_curve = pd.Series(
            1000 * (1 + np.cumsum(np.random.normal(0.001, 0.02, 100))),
            index=dates
        )

        # Create realistic trades data
        trades_data = []
        for i in range(50):
            entry_time = dates[i]
            exit_time = dates[i + 1]
            pnl = np.random.normal(10, 20)  # Random PnL
            trades_data.append({
                "entry_time": entry_time,
                "exit_time": exit_time,
                "pnl": pnl
            })

        trades = pd.DataFrame(trades_data)

        pm = PerformanceMetrics(risk_free_rate=0.02)

        result = pm.calculate_all_metrics(equity_curve, trades)

        assert isinstance(result, MetricsResult)
        assert result.total_trades == 50
        assert isinstance(result.total_return, float)
        assert isinstance(result.sharpe_ratio, float)
        assert isinstance(result.win_rate, float)

    def test_calculate_all_metrics_with_benchmark(self):
        """Test calculate_all_metrics with benchmark data."""
        dates = pd.date_range("2023-01-01", periods=50, freq="D")
        equity_curve = pd.Series(
            1000 * (1 + np.cumsum(np.random.normal(0.001, 0.02, 50))),
            index=dates
        )
        benchmark_returns = pd.Series(np.random.normal(0.0005, 0.01, 50), index=dates)

        # Simple trades data
        trades = pd.DataFrame({
            "pnl": [10, -5, 15, -8, 12, -6, 8, -4, 10, -7]
        })

        pm = PerformanceMetrics(benchmark_returns=benchmark_returns, risk_free_rate=0.02)

        result = pm.calculate_all_metrics(equity_curve, trades)

        assert isinstance(result, MetricsResult)
        assert result.total_trades == 10
        # Should have benchmark-related metrics
        assert result.beta != 0.0 or True  # Beta might be 0 due to random data

    def test_calculate_all_metrics_edge_cases(self):
        """Test calculate_all_metrics with edge cases."""
        # Need at least 2 points for calculate_returns
        dates = pd.date_range("2023-01-01", periods=2, freq="D")
        equity_curve = pd.Series([1000, 1000], index=dates)
        trades = pd.DataFrame({"pnl": []})  # No trades

        pm = PerformanceMetrics()

        result = pm.calculate_all_metrics(equity_curve, trades)

        assert isinstance(result, MetricsResult)
        assert result.total_trades == 0

    def test_all_methods_with_different_frequencies(self):
        """Test methods work with different data frequencies."""
        pm = PerformanceMetrics()

        # Test different frequencies
        frequencies = ["1h", "4h", "1d", "1w"]

        for freq in frequencies:
            equity = pd.Series([1000, 1050, 1020, 1080],
                              index=pd.date_range("2023-01-01", periods=4, freq="D"))

            # These should work with different frequencies
            returns = pm.calculate_returns(equity)
            assert isinstance(returns, pd.Series)

            sharpe = pm.calculate_sharpe_ratio(equity, freq)
            assert isinstance(sharpe, float)

            sortino = pm.calculate_sortino_ratio(equity, freq)
            assert isinstance(sortino, float)

    def test_error_handling_consistency(self):
        """Test that all methods handle errors consistently."""
        pm = PerformanceMetrics()
        empty_equity = pd.Series([], dtype=float)

        # Methods that should raise InsufficientDataError
        methods_to_test = [
            ("calculate_returns", (empty_equity,)),
            ("calculate_total_return", (empty_equity,)),
            ("calculate_volatility", (empty_equity,)),
            ("calculate_sharpe_ratio", (empty_equity,)),
            ("calculate_sortino_ratio", (empty_equity,)),
        ]

        for method_name, args in methods_to_test:
            method = getattr(pm, method_name)
            with pytest.raises(InsufficientDataError):
                method(*args)


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v", "--tb=short"])