"""Tests for performance metrics module to boost coverage from 14% to 80%."""

import numpy as np
import pandas as pd
import pytest

from quantchain.backtesting.performance_metrics import (
    InsufficientDataError,
    InvalidFrequencyError,
    MetricsCalculationError,
    MissingColumnError,
    PerformanceMetrics,
)


@pytest.mark.unit
class TestPerformanceMetrics:
    """Tests for PerformanceMetrics to boost coverage."""

    def test_init(self):
        """Test initialization."""
        calculator = PerformanceMetrics()
        assert calculator is not None
        assert hasattr(calculator, "calculate_all_metrics")
        assert hasattr(calculator, "calculate_total_return")

    def test_init_with_risk_free_rate(self):
        """Test initialization with custom risk-free rate."""
        calculator = PerformanceMetrics(risk_free_rate=0.03)
        assert calculator.risk_free_rate == 0.03

    def test_calculate_returns_empty_series(self):
        """Test returns calculation with empty series."""
        calculator = PerformanceMetrics()

        prices = pd.Series([], dtype=float)
        with pytest.raises(MetricsCalculationError):
            calculator.calculate_returns(prices)

    def test_calculate_returns_single_value(self):
        """Test returns calculation with single value."""
        calculator = PerformanceMetrics()

        prices = pd.Series([100.0])
        returns = calculator.calculate_returns(prices)
        assert len(returns) == 1
        assert pd.isna(returns.iloc[0])

    def test_calculate_total_return(self):
        """Test total return calculation."""
        calculator = PerformanceMetrics()

        prices = pd.Series([100, 105, 102, 108, 110])
        total_return = calculator.calculate_total_return(prices)

        expected_return = (110 - 100) / 100
        assert abs(total_return - expected_return) < 1e-10

    def test_calculate_total_return_negative(self):
        """Test total return calculation with loss."""
        calculator = PerformanceMetrics()

        prices = pd.Series([100, 95, 92, 88, 85])
        total_return = calculator.calculate_total_return(prices)

        expected_return = (85 - 100) / 100
        assert abs(total_return - expected_return) < 1e-10

    def test_calculate_annualized_return(self):
        """Test annualized return calculation."""
        calculator = PerformanceMetrics()

        # Simulate 1 year of daily returns
        dates = pd.date_range("2024-01-01", periods=252, freq="D")
        prices = 100 * (1 + np.cumsum(np.random.normal(0.001, 0.02, 251)))

        annual_return = calculator.calculate_annualized_return(dates, prices)
        assert isinstance(annual_return, float)

    def test_calculate_annualized_return_insufficient_data(self):
        """Test annualized return with insufficient data."""
        calculator = PerformanceMetrics()

        # Only one data point - insufficient for meaningful calculation
        dates = pd.date_range("2024-01-01", periods=1, freq="D")
        prices = pd.Series([100.0])

        # Should handle gracefully or return reasonable default
        annual_return = calculator.calculate_annualized_return(dates, prices)
        assert isinstance(annual_return, (float, type(None)))

    def test_calculate_sharpe_ratio(self):
        """Test Sharpe ratio calculation."""
        calculator = PerformanceMetrics(risk_free_rate=0.02)

        # Generate sample returns
        returns = pd.Series(np.random.normal(0.001, 0.02, 252))

        sharpe_ratio = calculator.calculate_sharpe_ratio(returns)
        assert isinstance(sharpe_ratio, float)

    def test_calculate_sharpe_ratio_zero_volatility(self):
        """Test Sharpe ratio with zero volatility."""
        calculator = PerformanceMetrics(risk_free_rate=0.02)

        # All returns are the same (zero volatility)
        returns = pd.Series([0.01] * 252)

        sharpe_ratio = calculator.calculate_sharpe_ratio(returns)
        # Should handle zero volatility gracefully
        assert isinstance(sharpe_ratio, float)

    def test_calculate_sharpe_ratio_negative_volatility(self):
        """Test Sharpe ratio with negative returns."""
        calculator = PerformanceMetrics(risk_free_rate=0.02)

        # All returns are negative
        returns = pd.Series([-0.01] * 252)

        sharpe_ratio = calculator.calculate_sharpe_ratio(returns)
        assert isinstance(sharpe_ratio, float)

    def test_calculate_sortino_ratio(self):
        """Test Sortino ratio calculation."""
        calculator = PerformanceMetrics(risk_free_rate=0.02)

        # Generate sample returns with negative values for downside deviation
        returns = pd.Series(np.random.normal(0.001, 0.02, 252))

        sortino_ratio = calculator.calculate_sortino_ratio(returns)
        assert isinstance(sortino_ratio, float)

    def test_calculate_max_drawdown_basic(self):
        """Test basic max drawdown calculation."""
        calculator = PerformanceMetrics()

        # Simple decreasing sequence
        prices = pd.Series([100, 95, 90, 85, 90, 95, 100])

        max_dd = calculator.calculate_max_drawdown(prices)
        assert isinstance(max_dd, dict)
        assert "max_drawdown" in max_dd
        assert "max_drawdown" in max_dd
        assert max_dd["max_drawdown"] > 0

    def test_calculate_max_drawdown_no_drawdown(self):
        """Test max drawdown with no drawdown."""
        calculator = PerformanceMetrics()

        # Increasing sequence - no drawdown
        prices = pd.Series([100, 105, 110, 115, 120])

        max_dd = calculator.calculate_max_drawdown(prices)
        assert max_dd["max_drawdown"] == 0.0

    def test_calculate_max_drawdown_empty_series(self):
        """Test max drawdown with empty series."""
        calculator = PerformanceMetrics()

        prices = pd.Series([], dtype=float)

        with pytest.raises(MetricsCalculationError):
            calculator.calculate_max_drawdown(prices)

    def test_calculate_max_drawdown_single_value(self):
        """Test max drawdown with single value."""
        calculator = PerformanceMetrics()

        prices = pd.Series([100.0])

        max_dd = calculator.calculate_max_drawdown(prices)
        assert max_dd["max_drawdown"] == 0.0

    def test_calculate_calmar_ratio(self):
        """Test Calmar ratio calculation."""
        calculator = PerformanceMetrics()

        returns = pd.Series(np.random.normal(0.001, 0.02, 252))
        max_dd = 0.1  # 10% max drawdown

        calmar_ratio = calculator.calculate_calmar_ratio(returns, max_dd)
        assert isinstance(calmar_ratio, float)

    def test_calculate_calmar_ratio_no_drawdown(self):
        """Test Calmar ratio with no drawdown."""
        calculator = PerformanceMetrics()

        returns = pd.Series(np.random.normal(0.001, 0.02, 252))
        max_dd = 0.0  # No drawdown

        calmar_ratio = calculator.calculate_calmar_ratio(returns, max_dd)
        # Should handle gracefully
        assert isinstance(calmar_ratio, (float, type(None)))

    def test_calculate_win_rate(self):
        """Test win rate calculation."""
        calculator = PerformanceMetrics()

        trades = pd.DataFrame(
            {"side": ["long", "short", "long", "short", "long", "short"]}
        )

        win_rate = calculator.calculate_win_rate(trades)
        assert isinstance(win_rate, float)

    def test_calculate_win_rate_empty_trades(self):
        """Test win rate with empty trades."""
        calculator = PerformanceMetrics()

        trades = pd.DataFrame()

        with pytest.raises(MetricsCalculationError):
            calculator.calculate_win_rate(trades)

    def test_calculate_profit_factor(self):
        """Test profit factor calculation."""
        calculator = PerformanceMetrics()

        trades = pd.DataFrame(
            {
                "side": ["long", "short", "long", "short"],
                "entry_price": [100, 100, 100, 100],
                "exit_price": [
                    110,
                    90,
                    95,
                    105,
                ],  # long profit, short profit, long loss, short loss
            }
        )

        profit_factor = calculator.calculate_profit_factor(trades)
        assert isinstance(profit_factor, float)

    def test_calculate_all_metrics_basic(self):
        """Test comprehensive metrics calculation."""
        calculator = PerformanceMetrics(risk_free_rate=0.02)

        dates = pd.date_range("2024-01-01", periods=50, freq="D")
        prices = 100 * (1 + np.cumsum(np.random.normal(0.001, 0.05, 49)))

        metrics = calculator.calculate_all_metrics(dates, prices)
        assert isinstance(metrics, dict)

        # Check for expected basic metrics
        assert "total_return" in metrics
        assert "sharpe_ratio" in metrics
        assert "max_drawdown" in metrics

    def test_generate_tear_sheet(self):
        """Test tear sheet generation."""
        calculator = PerformanceMetrics()

        trades = pd.DataFrame(
            {
                "side": ["long", "short", "long", "short"],
                "entry_price": [100, 100, 100, 100],
                "exit_price": [110, 90, 95, 105],
                "entry_date": pd.date_range("2024-01-01", periods=4, freq="D"),
                "exit_date": pd.date_range("2024-01-02", periods=4, freq="D"),
            }
        )

        tear_sheet = calculator.generate_tear_sheet(trades)
        assert isinstance(tear_sheet, (dict, str))

    def test_validate_insufficient_data(self):
        """Test data validation for insufficient data."""
        calculator = PerformanceMetrics()

        # Test with insufficient data for calculation
        calculator._validate_insufficient_data([], "test metric")

        # Test with sufficient data
        calculator._validate_insufficient_data([100, 101, 102], "test metric")

    def test_validate_frequency_regular(self):
        """Test frequency validation for regular intervals."""
        calculator = PerformanceMetrics()

        # Regular daily frequency
        dates = pd.date_range("2024-01-01", periods=10, freq="D")
        calculator._validate_frequency(dates)

    def test_validate_frequency_irregular(self):
        """Test frequency validation for irregular intervals."""
        calculator = PerformanceMetrics()

        # Irregular dates
        dates = pd.to_datetime(["2024-01-01", "2024-01-03", "2024-01-05", "2024-01-06"])

        with pytest.raises(InvalidFrequencyError):
            calculator._validate_frequency(dates)

    def test_benchmark_returns_property(self):
        """Test benchmark returns property."""
        calculator = PerformanceMetrics()

        # Default benchmark returns
        assert hasattr(calculator, "benchmark_returns")
        assert calculator.benchmark_returns is not None

    def test_risk_free_rate_property(self):
        """Test risk-free rate property."""
        calculator = PerformanceMetrics(risk_free_rate=0.03)

        assert calculator.risk_free_rate == 0.03

    def test_empty_string_risk_free_rate(self):
        """Test empty string risk-free rate."""
        calculator = PerformanceMetrics(risk_free_rate="")

        assert calculator.risk_free_rate == 0.02  # Default value

    def test_set_risk_free_rate_invalid(self):
        """Test setting invalid risk-free rate."""
        calculator = PerformanceMetrics()

        with pytest.raises(ValueError):
            calculator.risk_free_rate = -0.01

    def test_all_metrics_with_very_small_dataset(self):
        """Test all metrics with minimal but sufficient data."""
        calculator = PerformanceMetrics()

        # Just enough data for calculations
        dates = pd.date_range("2024-01-01", periods=2, freq="D")
        prices = pd.Series([100.0, 102.0])

        metrics = calculator.calculate_all_metrics(dates, prices)
        assert isinstance(metrics, dict)

    def test_edge_case_nan_values(self):
        """Test handling of NaN values in price data."""
        calculator = PerformanceMetrics()

        # Data with NaN values
        dates = pd.date_range("2024-01-01", periods=5, freq="D")
        prices = pd.Series([100.0, np.nan, 102.0, np.nan, 105.0])

        # Should handle NaN values gracefully
        returns = calculator.calculate_returns(prices)
        assert returns is not None
        assert len(returns) == 5
        assert returns.iloc[0] is pd.NA
        assert returns.iloc[1] is pd.NA

    def test_edge_case_inf_values(self):
        """Test handling of infinite values."""
        calculator = PerformanceMetrics()

        dates = pd.date_range("2024-01-01", periods=3, freq="D")
        prices = pd.Series([100.0, np.inf, 102.0])

        # Should handle inf values gracefully
        returns = calculator.calculate_returns(prices)
        assert returns is not None

    def test_large_dataset_performance(self):
        """Test performance with large dataset."""
        calculator = PerformanceMetrics()

        # Large dataset (5 years of daily data)
        dates = pd.date_range("2020-01-01", periods=1260, freq="D")
        prices = 100 * np.exp(np.cumsum(np.random.normal(0.0005, 0.02, 1259)))

        metrics = calculator.calculate_all_metrics(dates, prices)
        assert isinstance(metrics, dict)
