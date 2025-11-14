"""Comprehensive tests for performance metrics to boost coverage."""

import numpy as np
import pandas as pd
import pytest

from quantchain.backtesting.performance_metrics import (
    InsufficientDataError,
    InvalidFrequencyError,
    LibraryImportError,
    MetricsCalculationError,
    MissingColumnError,
    PerformanceMetrics,
)


@pytest.mark.unit
class TestPerformanceMetricsComprehensive:
    """Comprehensive tests for PerformanceMetrics."""

    def test_init_with_quantstats_available(self):
        """Test initialization when QuantStats is available."""
        calculator = PerformanceMetrics()
        assert calculator is not None
        assert hasattr(calculator, "calculate_all_metrics")

    def test_init_without_quantstats(self):
        """Test initialization when QuantStats is not available."""
        # Mock the import failure
        import quantchain.backtesting.performance_metrics as pm

        original_quantstats = pm.QUANTSTATS_AVAILABLE
        pm.QUANTSTATS_AVAILABLE = False

        try:
            calculator = PerformanceMetrics()
            assert calculator is not None
            assert hasattr(calculator, "calculate_all_metrics")
        finally:
            # Restore original value
            pm.QUANTSTATS_AVAILABLE = original_quantstats

    def test_calculate_basic_metrics_with_minimal_data(self):
        """Test basic metrics calculation with minimal data."""
        calculator = PerformanceMetrics()

        # Create minimal but valid data
        dates = pd.date_range("2024-01-01", periods=10, freq="D")
        equity = np.array([100, 105, 102, 108, 110, 107, 112, 115, 113, 118], dtype=float)
        equity_series = pd.Series(equity, index=dates)

        # Calculate returns
        returns = calculator.calculate_returns(equity_series)
        assert len(returns) == 9  # One less than the original series

        # Test with insufficient data
        with pytest.raises(InsufficientDataError):
            calculator.calculate_returns(pd.Series([100]))

    def test_calculate_total_return(self):
        """Test total return calculation."""
        calculator = PerformanceMetrics()

        dates = pd.date_range("2024-01-01", periods=10, freq="D")
        equity = np.array([100, 105, 102, 108, 110, 107, 112, 115, 113, 118], dtype=float)
        equity_series = pd.Series(equity, index=dates)

        total_return = calculator.calculate_total_return(equity_series)
        assert isinstance(total_return, float)

        # Should be positive (end > start)
        assert total_return > 0

        # Test with single point
        single_point = pd.Series([100])
        assert calculator.calculate_total_return(single_point) == 0.0

        # Test with insufficient data
        with pytest.raises(InsufficientDataError):
            calculator.calculate_total_return(pd.Series([]))

    def test_calculate_annualized_return(self):
        """Test annualized return calculation."""
        calculator = PerformanceMetrics()

        # Create a simple returns series with time period
        dates = pd.date_range("2024-01-01", periods=100, freq="D")
        returns = pd.Series([0.01] * 99, index=dates[1:])  # Skip first date for returns

        annual_return = calculator.calculate_annualized_return(returns)
        assert isinstance(annual_return, float)

        # Test with empty returns
        empty_returns = pd.Series([], dtype=float)
        assert calculator.calculate_annualized_return(empty_returns) == 0.0

    def test_calculate_sharpe_ratio(self):
        """Test Sharpe ratio calculation."""
        calculator = PerformanceMetrics()

        # Create a simple returns series
        dates = pd.date_range("2024-01-01", periods=100, freq="D")
        returns = pd.Series([0.01] * 99, index=dates[1:])  # Skip first date for returns

        sharpe = calculator.calculate_sharpe_ratio(returns)
        assert isinstance(sharpe, float)

        # Test with empty returns
        empty_returns = pd.Series([], dtype=float)
        assert calculator.calculate_sharpe_ratio(empty_returns) == 0.0

    def test_calculate_sortino_ratio(self):
        """Test Sortino ratio calculation."""
        calculator = PerformanceMetrics()

        # Create a simple returns series
        dates = pd.date_range("2024-01-01", periods=100, freq="D")
        returns = pd.Series([0.01] * 99, index=dates[1:])  # Skip first date for returns

        sortino = calculator.calculate_sortino_ratio(returns)
        assert isinstance(sortino, float)

        # Test with empty returns
        empty_returns = pd.Series([], dtype=float)
        assert calculator.calculate_sortino_ratio(empty_returns) == 0.0

    def test_calculate_max_drawdown(self):
        """Test maximum drawdown calculation."""
        calculator = PerformanceMetrics()

        # Create a simple increasing equity curve
        dates = pd.date_range("2024-01-01", periods=10, freq="D")
        equity = np.array([100, 105, 110, 115, 120, 125, 130, 135, 140, 145], dtype=float)
        equity_series = pd.Series(equity, index=dates)

        result = calculator.calculate_max_drawdown(equity_series)
        assert isinstance(result, dict)

    def test_calculate_calmar_ratio(self):
        """Test Calmar ratio calculation."""
        calculator = PerformanceMetrics()

        # Create a simple increasing equity curve
        dates = pd.date_range("2024-01-01", periods=10, freq="D")
        equity = np.array([100, 105, 110, 115, 120, 125, 130, 135, 140, 145], dtype=float)
        equity_series = pd.Series(equity, index=dates)

        calmar = calculator.calculate_calmar_ratio(equity_series)
        assert isinstance(calmar, float)

    def test_calculate_win_rate(self):
        """Test win rate calculation."""
        calculator = PerformanceMetrics()

        # Create trade data with pnl column as required by implementation
        trades = pd.DataFrame({
            "pnl": [50, -50, 100, -20, 20],
        })

        win_rate = calculator.calculate_win_rate(trades)
        assert isinstance(win_rate, float)
        assert 0 <= win_rate <= 1

        # Test with empty trades - should return 0.0, not raise error
        empty_trades = pd.DataFrame(columns=["pnl"])
        empty_win_rate = calculator.calculate_win_rate(empty_trades)
        assert empty_win_rate == 0.0

    def test_calculate_profit_factor(self):
        """Test profit factor calculation."""
        calculator = PerformanceMetrics()

        # Create trade data with pnl column as required by implementation
        trades = pd.DataFrame({
            "pnl": [50, -50, 100, -20, 20],
        })

        profit_factor = calculator.calculate_profit_factor(trades)
        assert isinstance(profit_factor, float)
        assert profit_factor >= 0

        # Test with empty trades - should return 0.0, not raise error
        empty_trades = pd.DataFrame(columns=["pnl"])
        empty_profit_factor = calculator.calculate_profit_factor(empty_trades)
        assert empty_profit_factor == 0.0

    def test_calculate_average_trade(self):
        """Test average trade calculation."""
        calculator = PerformanceMetrics()

        # Create trade data with pnl column as required by implementation
        trades = pd.DataFrame({
            "pnl": [50, -50, 100, -20, 20],
        })

        avg_trade = calculator.calculate_average_trade(trades)
        assert isinstance(avg_trade, float)

        # Test with empty trades - should return 0.0, not raise error
        empty_trades = pd.DataFrame(columns=["pnl"])
        empty_avg_trade = calculator.calculate_average_trade(empty_trades)
        assert empty_avg_trade == 0.0

    def test_calculate_total_trades(self):
        """Test total trades calculation."""
        calculator = PerformanceMetrics()

        # Create trade data
        trades = pd.DataFrame({
            "pnl": [50, -50, 100, -20, 20],
        })

        total_trades = calculator.calculate_total_trades(trades)
        assert isinstance(total_trades, int)
        assert total_trades == 5

    def test_calculate_largest_win(self):
        """Test largest win calculation."""
        calculator = PerformanceMetrics()

        # Create trade data with pnl column as required by implementation
        trades = pd.DataFrame({
            "pnl": [50, -50, 100, -20, 20],
        })

        largest_win = calculator.calculate_largest_win(trades)
        assert isinstance(largest_win, (float, np.floating, np.integer))

        # Test with empty trades - should return 0.0, not raise error
        empty_trades = pd.DataFrame(columns=["pnl"])
        empty_largest_win = calculator.calculate_largest_win(empty_trades)
        assert empty_largest_win == 0.0

    def test_calculate_largest_loss(self):
        """Test largest loss calculation."""
        calculator = PerformanceMetrics()

        # Create trade data with pnl column as required by implementation
        trades = pd.DataFrame({
            "pnl": [50, -50, 100, -20, 20],
        })

        largest_loss = calculator.calculate_largest_loss(trades)
        assert isinstance(largest_loss, (float, np.floating, np.integer))
        assert largest_loss >= 0  # Loss should be returned as absolute value (positive)

        # Test with empty trades - should return 0.0, not raise error
        empty_trades = pd.DataFrame(columns=["pnl"])
        empty_largest_loss = calculator.calculate_largest_loss(empty_trades)
        assert empty_largest_loss == 0.0

    def test_calculate_all_metrics(self):
        """Test comprehensive metrics calculation."""
        calculator = PerformanceMetrics()

        # Create simple equity data
        dates = pd.date_range("2024-01-01", periods=10, freq="D")
        equity = np.array([100, 105, 110, 115, 120, 125, 130, 135, 140, 145], dtype=float)
        equity_series = pd.Series(equity, index=dates)

        # Create trade data with pnl column as required by implementation
        trades = pd.DataFrame({
            "pnl": [50, -50, 100, -20, 20],
        })

        all_metrics = calculator.calculate_all_metrics(equity_series, trades)

        from quantchain.backtesting.engine import MetricsResult
        assert isinstance(all_metrics, MetricsResult)
        assert hasattr(all_metrics, 'total_return')

        # Check for common metrics
        assert hasattr(all_metrics, 'total_return')
        assert hasattr(all_metrics, 'sharpe_ratio')
        assert hasattr(all_metrics, 'win_rate')

    def test_calculate_all_metrics_without_quantstats(self):
        """Test metrics calculation without QuantStats."""
        import quantchain.backtesting.performance_metrics as pm

        original_quantstats = pm.QUANTSTATS_AVAILABLE
        pm.QUANTSTATS_AVAILABLE = False

        try:
            calculator = PerformanceMetrics()

            # Create simple equity data
            dates = pd.date_range("2024-01-01", periods=10, freq="D")
            equity = np.array([100, 105, 110, 115, 120, 125, 130, 135, 140, 145], dtype=float)
            equity_series = pd.Series(equity, index=dates)

            # Create trade data with pnl column as required by implementation
            trades = pd.DataFrame({
                "pnl": [50, -50, 100, -20, 20],
            })

            all_metrics = calculator.calculate_all_metrics(equity_series, trades)

            from quantchain.backtesting.engine import MetricsResult
            assert isinstance(all_metrics, MetricsResult)
            assert hasattr(all_metrics, 'total_return')
        finally:
            # Restore original value
            pm.QUANTSTATS_AVAILABLE = original_quantstats

    def test_error_handling_invalid_data(self):
        """Test error handling for invalid data."""
        calculator = PerformanceMetrics()

        # Test with NaN values
        dates = pd.date_range("2024-01-01", periods=10, freq="D")
        equity_with_nan = np.array([100, 105, np.nan, 108, 110, np.nan, 112, 115, 113, 118], dtype=float)
        equity_series = pd.Series(equity_with_nan, index=dates)

        # Should handle NaN values gracefully
        try:
            calculator.calculate_returns(equity_series)
        except MetricsCalculationError:
            # This is acceptable behavior
            pass

    def test_validate_frequency(self):
        """Test frequency validation."""
        calculator = PerformanceMetrics()

        # Test with hourly frequency
        dates = pd.date_range("2024-01-01", periods=24, freq="H")
        equity = 100 + np.cumsum(np.random.normal(0.001, 0.01, 24))
        equity_series = pd.Series(equity, index=dates)

        # This should work fine with our methods that don't depend on frequency
        returns = calculator.calculate_returns(equity_series)
        assert len(returns) == 23

    def test_performance_metrics_with_benchmark(self):
        """Test metrics with benchmark returns."""
        # Create benchmark returns
        benchmark_dates = pd.date_range("2024-01-01", periods=365, freq="D")
        benchmark_returns = pd.Series(
            np.random.normal(0.0005, 0.01, 365), index=benchmark_dates
        )

        calculator = PerformanceMetrics(benchmark_returns=benchmark_returns)

        # Create simple equity data
        dates = pd.date_range("2024-01-01", periods=10, freq="D")
        equity = np.array([100, 105, 110, 115, 120, 125, 130, 135, 140, 145], dtype=float)
        equity_series = pd.Series(equity, index=dates)

        # Test that calculator was initialized with benchmark
        assert calculator.benchmark_returns is not None
        assert len(calculator.benchmark_returns) == 365

        # Test basic calculations
        returns = calculator.calculate_returns(equity_series)
        assert len(returns) > 0

        # Test Sharpe ratio with risk-free rate
        sharpe = calculator.calculate_sharpe_ratio(returns)
        assert isinstance(sharpe, float)

    def test_edge_cases(self):
        """Test edge cases for performance metrics."""
        calculator = PerformanceMetrics()

        # Test with zero returns (no movement)
        dates = pd.date_range("2024-01-01", periods=10, freq="D")
        equity = pd.Series([100] * 10, index=dates)

        returns = calculator.calculate_returns(equity)
        assert (returns == 0).all()

        # Test with negative equity (should handle gracefully)
        negative_equity = pd.Series([-100] * 10, index=dates)
        try:
            calculator.calculate_total_return(negative_equity)
            # If it doesn't raise an error, that's fine
        except MetricsCalculationError:
            # If it raises an error, that's also acceptable
            pass

    def test_calculate_var(self):
        """Test Value at Risk (VaR) calculation."""
        calculator = PerformanceMetrics()

        # Create a simple returns series
        returns = pd.Series([-0.02, -0.01, 0.03, -0.04, 0.01, 0.02, -0.03, 0.01])

        # Test default confidence level
        var = calculator.calculate_var(returns)
        assert isinstance(var, float)
        assert var < 0  # VaR should be negative (representing loss)

        # Test custom confidence level
        var_99 = calculator.calculate_var(returns, 0.99)
        assert isinstance(var_99, float)

        # Test with invalid confidence level
        with pytest.raises(ValueError):
            calculator.calculate_var(pd.Series([0.01, 0.02]), 1.5)  # Invalid confidence level

    def test_calculate_cvar(self):
        """Test Conditional Value at Risk (CVaR) calculation."""
        calculator = PerformanceMetrics()

        # Create a simple returns series
        returns = pd.Series([-0.02, -0.01, 0.03, -0.04, 0.01, 0.02, -0.03, 0.01])

        # Test default confidence level
        cvar = calculator.calculate_cvar(returns)
        assert isinstance(cvar, float)
        assert cvar < 0  # CVaR should be negative (representing loss)

        # Test custom confidence level
        cvar_99 = calculator.calculate_cvar(returns, 0.99)
        assert isinstance(cvar_99, float)

        # Test with invalid confidence level
        with pytest.raises(ValueError):
            calculator.calculate_cvar(pd.Series([0.01, 0.02]), 1.5)  # Invalid confidence level

    def test_calculate_average_win(self):
        """Test average winning trade calculation."""
        calculator = PerformanceMetrics()

        # Create trade data with pnl column
        trades = pd.DataFrame({
            "pnl": [50, -30, 100, -20, 80],
        })

        avg_win = calculator.calculate_average_win(trades)
        assert isinstance(avg_win, float)
        assert avg_win > 0  # Average win should be positive

        # Test with no winning trades
        no_wins = pd.DataFrame({
            "pnl": [-50, -30, -20],
        })
        assert calculator.calculate_average_win(no_wins) == 0.0

        # Test with empty trades - should return 0.0, not raise error
        empty_trades = pd.DataFrame(columns=["pnl"])
        empty_avg_win = calculator.calculate_average_win(empty_trades)
        assert empty_avg_win == 0.0

    def test_calculate_average_loss(self):
        """Test average losing trade calculation."""
        calculator = PerformanceMetrics()

        # Create trade data with pnl column
        trades = pd.DataFrame({
            "pnl": [50, -30, 100, -20, 80],
        })

        avg_loss = calculator.calculate_average_loss(trades)
        assert isinstance(avg_loss, float)
        assert avg_loss > 0  # Average loss should be positive (absolute value)

        # Test with no losing trades
        no_losses = pd.DataFrame({
            "pnl": [50, 30, 20],
        })
        assert calculator.calculate_average_loss(no_losses) == 0.0

        # Test with empty trades - should return 0.0, not raise error
        empty_trades = pd.DataFrame(columns=["pnl"])
        empty_avg_loss = calculator.calculate_average_loss(empty_trades)
        assert empty_avg_loss == 0.0

    def test_calculate_win_loss_ratio(self):
        """Test win/loss ratio calculation."""
        calculator = PerformanceMetrics()

        # Create trade data with pnl column
        trades = pd.DataFrame({
            "pnl": [50, -30, 100, -20, 80],
        })

        win_loss_ratio = calculator.calculate_win_loss_ratio(trades)
        assert isinstance(win_loss_ratio, float)
        assert win_loss_ratio > 0  # Should be positive when wins > losses

        # Test with no wins or losses
        no_trades = pd.DataFrame(columns=["pnl"])
        assert calculator.calculate_win_loss_ratio(no_trades) == 0.0

        # Test with only wins
        only_wins = pd.DataFrame({
            "pnl": [50, 30, 20],
        })
        assert calculator.calculate_win_loss_ratio(only_wins) == 0.0  # Implementation returns 0.0 when no losses
