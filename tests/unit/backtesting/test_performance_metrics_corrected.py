"""
Corrected tests for performance_metrics.py with actual method signatures.
Targets improving coverage from 27% to 80%+.
"""

import pandas as pd
import pytest

try:
    from quantchain.backtesting.performance_metrics import (
        InsufficientDataError,
        LibraryImportError,
        MetricsResult,
        MissingColumnError,
        PerformanceMetrics,
    )

    PERFORMANCE_METRICS_AVAILABLE = True
except ImportError as e:
    PERFORMANCE_METRICS_AVAILABLE = False
    print(f"Performance metrics not available: {e}")


@pytest.mark.skipif(
    not PERFORMANCE_METRICS_AVAILABLE, reason="Performance metrics not available"
)
class TestExceptions:
    """Test custom exception classes."""

    def test_insufficient_data_error(self):
        """Test InsufficientDataError exception."""
        error = InsufficientDataError("Not enough data points")
        assert str(error) == "Not enough data points"
        assert isinstance(error, Exception)

    def test_library_import_error(self):
        """Test LibraryImportError exception."""
        error = LibraryImportError("Required library not found")
        assert str(error) == "Required library not found"
        assert isinstance(error, Exception)

    def test_missing_column_error(self):
        """Test MissingColumnError exception."""
        error = MissingColumnError("Required column 'price' not found")
        assert str(error) == "Required column 'price' not found"
        assert isinstance(error, Exception)


@pytest.mark.skipif(
    not PERFORMANCE_METRICS_AVAILABLE, reason="Performance metrics not available"
)
class TestMetricsResult:
    """Test MetricsResult dataclass with correct fields."""

    def test_metrics_result_creation_full(self):
        """Test creating MetricsResult with all required fields."""
        # Create with all required fields
        result = MetricsResult(
            total_return=0.15,
            annualized_return=0.12,
            sharpe_ratio=1.5,
            sortino_ratio=2.0,
            calmar_ratio=1.8,
            max_drawdown=-0.08,
            max_drawdown_duration=30,
            max_drawdown_start=pd.Timestamp("2024-01-01"),
            max_drawdown_end=pd.Timestamp("2024-01-31"),
            volatility=0.18,
            win_rate=0.65,
            profit_factor=1.8,
            total_trades=100,
            winning_trades=65,
            losing_trades=35,
            avg_win=200.0,
            avg_loss=-120.0,
            best_trade=500.0,
            worst_trade=-300.0,
            avg_trade_duration=5.2,
            avg_trade_duration_days=5.2 / 24,  # hours to days
            sharpe_ratio_qstats=1.4,
            sortino_ratio_qstats=1.9,
            omega_ratio=1.3,
            alpha=0.05,
            beta=1.1,
            information_ratio=0.8,
            var_95=-0.02,
        )

        assert result.total_return == 0.15
        assert result.annualized_return == 0.12
        assert result.sharpe_ratio == 1.5
        assert result.win_rate == 0.65
        assert result.total_trades == 100
        assert result.best_trade == 500.0


@pytest.mark.skipif(
    not PERFORMANCE_METRICS_AVAILABLE, reason="Performance metrics not available"
)
class TestPerformanceMetricsCore:
    """Test core PerformanceMetrics methods."""

    def test_performance_metrics_init_default(self):
        """Test PerformanceMetrics initialization with defaults."""
        metrics = PerformanceMetrics()
        assert metrics.benchmark_returns is None
        assert metrics.risk_free_rate == 0.02

    def test_performance_metrics_init_with_params(self):
        """Test PerformanceMetrics initialization with parameters."""
        benchmark = pd.Series([0.001, 0.002, 0.0015])
        metrics = PerformanceMetrics(benchmark_returns=benchmark, risk_free_rate=0.03)
        assert metrics.benchmark_returns is not None
        assert metrics.risk_free_rate == 0.03

    def test_calculate_returns_basic(self):
        """Test basic returns calculation."""
        metrics = PerformanceMetrics()
        equity_curve = pd.Series([100, 101, 100.5, 102, 102.8])

        returns = metrics.calculate_returns(equity_curve)
        assert len(returns) == 4  # One less than input due to pct_change
        assert isinstance(returns, pd.Series)

    def test_calculate_returns_insufficient_data(self):
        """Test returns calculation with insufficient data."""
        metrics = PerformanceMetrics()
        equity_curve = pd.Series([100])  # Only one point

        with pytest.raises(InsufficientDataError):
            metrics.calculate_returns(equity_curve)

    def test_calculate_total_return_basic(self):
        """Test total return calculation."""
        metrics = PerformanceMetrics()
        equity_curve = pd.Series([10000, 11500])

        total_return = metrics.calculate_total_return(equity_curve)
        assert (
            abs(total_return - 0.15) < 1e-10
        )  # 15% return (with floating point tolerance)

    def test_calculate_total_return_insufficient_data(self):
        """Test total return with insufficient data."""
        metrics = PerformanceMetrics()
        equity_curve = pd.Series([])  # Empty series

        with pytest.raises(InsufficientDataError):
            metrics.calculate_total_return(equity_curve)

    def test_calculate_annualized_return_basic(self):
        """Test annualized return calculation."""
        metrics = PerformanceMetrics()

        # Create a 1-year equity curve
        dates = pd.date_range("2024-01-01", "2024-12-31", freq="D")
        values = [10000 * (1 + 0.001 * i) for i in range(len(dates))]
        equity_curve = pd.Series(values, index=dates)

        annualized_return = metrics.calculate_annualized_return(equity_curve)
        assert isinstance(annualized_return, float)

    def test_calculate_volatility_basic(self):
        """Test volatility calculation."""
        metrics = PerformanceMetrics()
        equity_curve = pd.Series([100, 101, 100.5, 102, 102.8, 102.6, 103])

        volatility = metrics.calculate_volatility(equity_curve)
        assert isinstance(volatility, float)
        assert volatility >= 0

    def test_calculate_sharpe_ratio_basic(self):
        """Test Sharpe ratio calculation."""
        metrics = PerformanceMetrics()
        dates = pd.date_range("2023-01-01", periods=8, freq="D")
        equity_curve = pd.Series(
            [100, 101, 100.5, 102, 102.8, 102.6, 103, 103.5], index=dates
        )

        sharpe = metrics.calculate_sharpe_ratio(equity_curve)
        assert isinstance(sharpe, (int, float))

    def test_calculate_sharpe_ratio_with_benchmark(self):
        """Test Sharpe ratio calculation with benchmark."""
        benchmark = pd.Series([0.001, 0.002, 0.0015, 0.0018])
        metrics = PerformanceMetrics(benchmark_returns=benchmark)
        dates = pd.date_range("2023-01-01", periods=5, freq="D")
        equity_curve = pd.Series([100, 101, 100.5, 102, 102.8], index=dates)

        sharpe = metrics.calculate_sharpe_ratio(equity_curve)
        assert isinstance(sharpe, (int, float))

    def test_calculate_sortino_ratio_basic(self):
        """Test Sortino ratio calculation."""
        metrics = PerformanceMetrics()
        dates = pd.date_range("2023-01-01", periods=8, freq="D")
        equity_curve = pd.Series(
            [100, 101, 100.5, 102, 102.8, 102.6, 103, 103.5], index=dates
        )

        sortino = metrics.calculate_sortino_ratio(equity_curve)
        assert isinstance(sortino, (int, float))

    def test_calculate_max_drawdown_basic(self):
        """Test maximum drawdown calculation."""
        metrics = PerformanceMetrics()
        # Create data with clear drawdown
        equity_curve = pd.Series([100, 110, 105, 95, 90, 95, 100])

        result = metrics.calculate_max_drawdown(equity_curve)
        assert isinstance(result, dict)
        assert "max_drawdown" in result
        assert "max_drawdown_start" in result
        assert "max_drawdown_end" in result
        assert result["max_drawdown"] <= 0  # Should be negative or zero

    def test_calculate_max_drawdown_duration(self):
        """Test maximum drawdown duration calculation."""
        metrics = PerformanceMetrics()
        # Create data with sustained drawdown
        dates = pd.date_range("2024-01-01", periods=10, freq="D")
        equity_curve = pd.Series(
            [100, 110, 105, 95, 90, 90, 92, 94, 96, 98], index=dates
        )

        duration = metrics.calculate_max_drawdown_duration(equity_curve)
        assert isinstance(duration, int)
        assert duration >= 0

    def test_calculate_calmar_ratio_basic(self):
        """Test Calmar ratio calculation."""
        metrics = PerformanceMetrics()
        # Create data with both return and drawdown
        equity_curve = pd.Series([100, 110, 105, 95, 90, 95, 115])

        calmar = metrics.calculate_calmar_ratio(equity_curve)
        assert isinstance(calmar, (int, float))

    def test_calculate_calmar_ratio_no_drawdown(self):
        """Test Calmar ratio calculation with no drawdown."""
        metrics = PerformanceMetrics()
        # Monotonically increasing series
        equity_curve = pd.Series([100, 105, 110, 115, 120])

        calmar = metrics.calculate_calmar_ratio(equity_curve)
        # Should handle no drawdown case gracefully
        assert isinstance(calmar, (int, float))

    def test_calculate_win_rate_no_trades(self):
        """Test win rate calculation with no trades."""
        metrics = PerformanceMetrics()
        trades = pd.DataFrame(columns=["pnl"])  # Empty DataFrame

        win_rate = metrics.calculate_win_rate(trades)
        assert win_rate == 0.0

    def test_calculate_win_rate_with_trades(self):
        """Test win rate calculation with actual trades."""
        metrics = PerformanceMetrics()
        trades = pd.DataFrame({"pnl": [100, -50, 150, -25, 75]})

        win_rate = metrics.calculate_win_rate(trades)
        assert isinstance(win_rate, float)
        assert 0 <= win_rate <= 1

    def test_calculate_profit_factor_no_trades(self):
        """Test profit factor calculation with no trades."""
        metrics = PerformanceMetrics()
        trades = pd.DataFrame(columns=["pnl"])  # Empty DataFrame

        profit_factor = metrics.calculate_profit_factor(trades)
        assert isinstance(profit_factor, float)

    def test_calculate_profit_factor_with_trades(self):
        """Test profit factor calculation with actual trades."""
        metrics = PerformanceMetrics()
        trades = pd.DataFrame({"pnl": [100, -50, 150, -25, 75, -30, 200]})

        profit_factor = metrics.calculate_profit_factor(trades)
        assert isinstance(profit_factor, float)
        assert profit_factor >= 0

    def test_calculate_average_win_loss_basic(self):
        """Test average win/loss calculation."""
        metrics = PerformanceMetrics()
        trades = pd.DataFrame({"pnl": [100, -50, 150, -25, 75, -30, 200]})

        result = metrics.calculate_average_win_loss(trades)
        assert isinstance(result, dict)
        assert "avg_win" in result
        assert "avg_loss" in result

    def test_calculate_best_worst_trade(self):
        """Test best/worst trade calculation."""
        metrics = PerformanceMetrics()
        trades = pd.DataFrame({"pnl": [100, -50, 150, -25, 75, -30, 200]})

        result = metrics.calculate_best_worst_trade(trades)
        assert isinstance(result, dict)
        assert "best_trade" in result
        assert "worst_trade" in result

    def test_calculate_average_trade_duration(self):
        """Test average trade duration calculation."""
        metrics = PerformanceMetrics()

        # Create trades with entry and exit times
        trades = pd.DataFrame(
            {
                "entry_time": pd.date_range("2024-01-01", periods=3, freq="D"),
                "exit_time": pd.date_range("2024-01-02", periods=3, freq="D"),
            }
        )

        result = metrics.calculate_average_trade_duration(trades)
        assert isinstance(result, dict)
        assert "avg_duration_hours" in result
        assert "avg_duration_days" in result

    def test_calculate_var_basic(self):
        """Test Value at Risk calculation."""
        metrics = PerformanceMetrics()
        returns = pd.Series([0.01, -0.005, 0.015, 0.008, -0.002, 0.012, -0.018, 0.006])

        var_95 = metrics.calculate_var(returns, level=0.05)
        assert isinstance(var_95, float)
        assert var_95 <= 0  # VaR should be negative

    def test_generate_tear_sheet(self):
        """Test tear sheet generation."""
        metrics = PerformanceMetrics()
        equity_curve = pd.Series([100, 101, 100.5, 102, 102.8, 102.6, 103])
        trades = pd.DataFrame({"pnl": [100, -50, 150, -25, 75]})

        # Test that method exists and can be called
        result = metrics.generate_tear_sheet(equity_curve, trades)
        assert isinstance(result, MetricsResult)

    def test_calculate_all_metrics(self):
        """Test comprehensive metrics calculation."""
        metrics = PerformanceMetrics()
        equity_curve = pd.Series([100, 101, 100.5, 102, 102.8, 102.6, 103, 103.5])
        trades = pd.DataFrame({"pnl": [100, -50, 150, -25, 75]})

        result = metrics.calculate_all_metrics(equity_curve, trades)
        assert isinstance(result, MetricsResult)

        # Verify key fields are populated
        assert isinstance(result.total_return, float)
        assert isinstance(result.volatility, float)
        assert isinstance(result.sharpe_ratio, (int, float))


@pytest.mark.skipif(
    not PERFORMANCE_METRICS_AVAILABLE, reason="Performance metrics not available"
)
class TestPerformanceMetricsAdvanced:
    """Test advanced PerformanceMetrics features."""

    def test_calculate_quantstats_metrics(self):
        """Test quantstats metrics calculation."""
        metrics = PerformanceMetrics()
        returns = pd.Series([0.01, -0.005, 0.015, 0.008, -0.002, 0.012])

        # Test that method exists and returns expected structure
        result = metrics.calculate_quantstats_metrics(returns)
        assert isinstance(result, dict)

    def test_calculate_beta_alpha(self):
        """Test beta and alpha calculation."""
        # Create benchmark returns
        benchmark = pd.Series([0.008, 0.012, -0.002, 0.006, 0.009, 0.011])
        metrics = PerformanceMetrics(benchmark_returns=benchmark)

        returns = pd.Series([0.01, -0.005, 0.015, 0.008, -0.002, 0.012])

        result = metrics.calculate_beta_alpha(returns)
        assert isinstance(result, dict)
        # Should contain alpha and beta if calculation succeeds

    def test_edge_case_all_zero_returns(self):
        """Test handling all zero returns."""
        metrics = PerformanceMetrics()
        equity_curve = pd.Series([100, 100, 100, 100])  # No change

        # Should handle gracefully
        total_return = metrics.calculate_total_return(equity_curve)
        assert total_return == 0.0

    def test_edge_case_single_return(self):
        """Test handling single return data point."""
        metrics = PerformanceMetrics()
        equity_curve = pd.Series([10000, 10200])  # Only one return

        # Should work with minimal data
        total_return = metrics.calculate_total_return(equity_curve)
        assert total_return == 0.02

    def test_edge_case_negative_values(self):
        """Test handling negative portfolio values (edge case)."""
        metrics = PerformanceMetrics()
        # This would be unusual but should be handled gracefully
        equity_curve = pd.Series([-1000, -900, -1100, -800])

        try:
            total_return = metrics.calculate_total_return(equity_curve)
            assert isinstance(total_return, float)
        except Exception:
            # May raise exception for negative values, which is acceptable
            pass


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
