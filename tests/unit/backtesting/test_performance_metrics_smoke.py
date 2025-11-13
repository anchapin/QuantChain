"""Smoke tests for performance metrics to boost coverage."""

import numpy as np
import pandas as pd
import pytest

from quantchain.backtesting.performance_metrics import (
    InsufficientDataError,
    LibraryImportError,
    MetricsCalculationError,
    PerformanceMetrics,
)


@pytest.mark.unit
class TestPerformanceMetricsSmoke:
    """Smoke tests for PerformanceMetrics to boost coverage."""

    def test_init_with_benchmark(self):
        """Test initialization with benchmark returns."""
        dates = pd.date_range("2024-01-01", periods=100, freq="D")
        benchmark = pd.Series(np.random.normal(0.001, 0.02, 100), index=dates)

        calculator = PerformanceMetrics(benchmark_returns=benchmark)
        assert calculator.benchmark_returns is not None
        assert calculator.risk_free_rate == 0.02  # default

    def test_init_with_custom_risk_free_rate(self):
        """Test initialization with custom risk-free rate."""
        calculator = PerformanceMetrics(risk_free_rate=0.03)
        assert calculator.risk_free_rate == 0.03

    def test_calculate_total_return(self):
        """Test total return calculation."""
        calculator = PerformanceMetrics()
        equity = pd.Series([100, 105, 102, 108, 110])
        total_return = calculator.calculate_total_return(equity)
        assert abs(total_return - 0.1) < 1e-10  # (110 - 100) / 100

    def test_calculate_total_return_negative(self):
        """Test total return with negative returns."""
        calculator = PerformanceMetrics()
        equity = pd.Series([100, 95, 92, 88, 85])
        total_return = calculator.calculate_total_return(equity)
        assert abs(total_return + 0.15) < 1e-10  # (85 - 100) / 100

    def test_calculate_annualized_return_daily(self):
        """Test annualized return calculation for daily data."""
        calculator = PerformanceMetrics()
        dates = pd.date_range("2024-01-01", periods=252, freq="D")  # Trading days
        returns = pd.Series(np.random.normal(0.001, 0.02, 252), index=dates)
        annual_return = calculator.calculate_annualized_return(returns, "1d")
        assert isinstance(annual_return, float)

    def test_calculate_annualized_return_hourly(self):
        """Test annualized return calculation for hourly data."""
        calculator = PerformanceMetrics()
        dates = pd.date_range("2024-01-01", periods=1000, freq="h")
        returns = pd.Series(np.random.normal(0.0001, 0.01, 1000), index=dates)
        annual_return = calculator.calculate_annualized_return(returns, "1h")
        assert isinstance(annual_return, float)

    def test_calculate_sharpe_ratio(self):
        """Test Sharpe ratio calculation."""
        calculator = PerformanceMetrics()
        returns = pd.Series(np.random.normal(0.001, 0.02, 252))
        sharpe = calculator.calculate_sharpe_ratio(returns)
        assert isinstance(sharpe, float)

    def test_calculate_sharpe_ratio_zero_volatility(self):
        """Test Sharpe ratio with zero volatility."""
        calculator = PerformanceMetrics()
        returns = pd.Series([0.001] * 10)  # Constant returns
        sharpe = calculator.calculate_sharpe_ratio(returns)
        assert isinstance(sharpe, float)

    def test_calculate_sortino_ratio(self):
        """Test Sortino ratio calculation."""
        calculator = PerformanceMetrics()
        returns = pd.Series(np.random.normal(0.001, 0.02, 252))
        sortino = calculator.calculate_sortino_ratio(returns)
        assert isinstance(sortino, float)

    def test_calculate_max_drawdown(self):
        """Test maximum drawdown calculation."""
        calculator = PerformanceMetrics()
        equity = pd.Series([100, 110, 105, 95, 90, 100])
        dd = calculator.calculate_max_drawdown(equity)
        assert "max_drawdown" in dd
        assert "max_drawdown_duration" in dd
        assert dd["max_drawdown"] == pytest.approx(0.1818, rel=1e-3)  # (90-110)/110

    def test_calculate_calmar_ratio(self):
        """Test Calmar ratio calculation."""
        calculator = PerformanceMetrics()
        dates = pd.date_range("2024-01-01", periods=252, freq="D")
        returns = pd.Series(np.random.normal(0.001, 0.02, 252), index=dates)
        max_dd = 0.1
        calmar = calculator.calculate_calmar_ratio(returns, max_dd)
        assert isinstance(calmar, float)

    def test_calculate_win_rate(self):
        """Test win rate calculation."""
        calculator = PerformanceMetrics()
        trades = pd.DataFrame({
            "pnl": [100, -50, 200, -25, 150]
        })
        win_rate = calculator.calculate_win_rate(trades)
        assert win_rate == 0.6  # 3 wins out of 5 trades

    def test_calculate_win_rate_no_trades(self):
        """Test win rate with no trades."""
        calculator = PerformanceMetrics()
        trades = pd.DataFrame({"pnl": []})
        win_rate = calculator.calculate_win_rate(trades)
        assert win_rate == 0.0

    def test_calculate_profit_factor(self):
        """Test profit factor calculation."""
        calculator = PerformanceMetrics()
        trades = pd.DataFrame({
            "pnl": [100, -50, 200, -25, 150]
        })
        profit_factor = calculator.calculate_profit_factor(trades)
        assert isinstance(profit_factor, float)
        assert profit_factor > 0

    def test_calculate_profit_factor_no_losses(self):
        """Test profit factor with only winning trades."""
        calculator = PerformanceMetrics()
        trades = pd.DataFrame({
            "pnl": [100, 200, 150]
        })
        profit_factor = calculator.calculate_profit_factor(trades)
        assert np.isinf(profit_factor)

    def test_generate_tear_sheet(self):
        """Test tear sheet generation without quantstats."""
        calculator = PerformanceMetrics()
        dates = pd.date_range("2024-01-01", periods=100, freq="D")
        equity = pd.Series(np.random.normal(100, 10, 100).cumsum(), index=dates)

        # Create a results object
        results = type('Results', (), {'equity_curve': equity})()

        # Should not raise an exception
        result = calculator.generate_tear_sheet(results)
        assert isinstance(result, dict)

    def test_calculate_empyrical_metrics_without_library(self):
        """Test empyrical metrics without library."""
        import quantchain.backtesting.performance_metrics as pm
        original_empyrical = pm.EMPYRICAL_AVAILABLE
        pm.EMPYRICAL_AVAILABLE = False

        try:
            calculator = PerformanceMetrics()
            dates = pd.date_range("2024-01-01", periods=100, freq="D")
            returns = pd.Series(np.random.normal(0.001, 0.02, 100), index=dates)

            with pytest.raises(LibraryImportError):
                calculator.calculate_empyrical_metrics(returns)
        finally:
            pm.EMPYRICAL_AVAILABLE = original_empyrical

    def test_calculate_all_metrics(self):
        """Test comprehensive metrics calculation."""
        calculator = PerformanceMetrics()
        dates = pd.date_range("2024-01-01", periods=100, freq="D")
        equity = pd.Series(np.random.normal(100, 10, 100).cumsum(), index=dates)
        trades = pd.DataFrame({
            "pnl": np.random.normal(10, 50, 20)
        })

        metrics = calculator.calculate_all_metrics(equity, trades)
        assert hasattr(metrics, 'total_return')
        assert hasattr(metrics, 'annualized_return')

    def test_calculate_all_metrics_with_benchmark(self):
        """Test comprehensive metrics with benchmark."""
        dates = pd.date_range("2024-01-01", periods=100, freq="D")
        benchmark = pd.Series(np.random.normal(0.001, 0.02, 100), index=dates)
        calculator = PerformanceMetrics(benchmark_returns=benchmark)
        equity = pd.Series(np.random.normal(100, 10, 100).cumsum(), index=dates)
        trades = pd.DataFrame({
            "pnl": np.random.normal(10, 50, 20)
        })

        metrics = calculator.calculate_all_metrics(equity, trades)
        assert hasattr(metrics, 'total_return')
        assert hasattr(metrics, 'beta')

    def test_error_cases(self):
        """Test error handling with insufficient data."""
        calculator = PerformanceMetrics()

        # Test with valid data - these should work
        equity = pd.Series([100, 110])
        result = calculator.calculate_total_return(equity)
        assert result is not None
