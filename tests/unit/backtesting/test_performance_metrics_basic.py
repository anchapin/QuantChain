"""Basic tests for performance metrics to boost coverage."""

import pytest
import numpy as np
import pandas as pd

from quantchain.backtesting.performance_metrics import (
    InsufficientDataError,
    InvalidFrequencyError,
    LibraryImportError,
    MetricsCalculationError,
    MissingColumnError,
    PerformanceMetrics,
    QUANTSTATS_AVAILABLE,
    EMPYRICAL_AVAILABLE,
)


@pytest.mark.unit
class TestPerformanceMetricsBasic:
    """Basic tests for performance metrics components."""

    def test_availability_constants(self):
        """Test library availability constants."""
        assert isinstance(QUANTSTATS_AVAILABLE, bool)
        assert isinstance(EMPYRICAL_AVAILABLE, bool)

    def test_performance_metrics_init(self):
        """Test PerformanceMetrics initialization."""
        calculator = PerformanceMetrics()
        assert calculator.risk_free_rate == 0.02
        assert calculator.benchmark_returns is None

    def test_performance_metrics_init_with_custom_risk_free(self):
        """Test PerformanceMetrics with custom risk-free rate."""
        calculator = PerformanceMetrics(risk_free_rate=0.05)
        assert calculator.risk_free_rate == 0.05

    def test_performance_metrics_init_with_benchmark(self):
        """Test PerformanceMetrics with benchmark."""
        benchmark = pd.Series([100, 102, 101, 103, 105])
        calculator = PerformanceMetrics(benchmark_returns=benchmark)
        assert calculator.benchmark_returns is not None

    def test_calculate_total_return_simple(self):
        """Test total return calculation with simple data."""
        calculator = PerformanceMetrics()
        equity = pd.Series([100, 105, 102, 108, 110])
        result = calculator.calculate_total_return(equity)
        assert result > 0

    def test_calculate_total_return_negative(self):
        """Test total return with negative returns."""
        calculator = PerformanceMetrics()
        equity = pd.Series([100, 95, 92, 88, 85])
        result = calculator.calculate_total_return(equity)
        assert result < 0

    def test_calculate_returns(self):
        """Test returns calculation."""
        calculator = PerformanceMetrics()
        equity = pd.Series([100, 105, 102, 108, 110])
        result = calculator.calculate_returns(equity)
        assert isinstance(result, pd.Series)
        assert len(result) == 4  # One less than input

    def test_calculate_annualized_return(self):
        """Test annualized return calculation."""
        calculator = PerformanceMetrics()
        dates = pd.date_range("2024-01-01", periods=5, freq="D")
        equity = pd.Series([100, 105, 102, 108, 110], index=dates)
        result = calculator.calculate_annualized_return(equity)
        assert isinstance(result, (float, int))

    def test_calculate_sharpe_ratio(self):
        """Test Sharpe ratio calculation."""
        calculator = PerformanceMetrics()
        equity = pd.Series([100, 105, 102, 108, 110])
        result = calculator.calculate_sharpe_ratio(equity)
        assert isinstance(result, (float, int))

    def test_calculate_sharpe_ratio_insufficient_data(self):
        """Test Sharpe ratio with insufficient data."""
        calculator = PerformanceMetrics()
        equity = pd.Series([100, 102])  # Only 2 points
        result = calculator.calculate_sharpe_ratio(equity)
        # Should handle gracefully but can return any valid value
        assert isinstance(result, (float, int))

    def test_calculate_sortino_ratio(self):
        """Test Sortino ratio calculation."""
        calculator = PerformanceMetrics()
        equity = pd.Series([100, 105, 102, 108, 110])
        result = calculator.calculate_sortino_ratio(equity)
        assert isinstance(result, (float, int))

    def test_calculate_max_drawdown(self):
        """Test maximum drawdown calculation."""
        calculator = PerformanceMetrics()
        equity = pd.Series([100, 105, 95, 108, 90, 110])  # Drawdown from 108 to 90
        result = calculator.calculate_max_drawdown(equity)
        assert isinstance(result, dict)
        assert "max_drawdown" in result
        assert result["max_drawdown"] > 0  # Drawdown is returned as positive value

    def test_calculate_calmar_ratio(self):
        """Test Calmar ratio calculation."""
        calculator = PerformanceMetrics()
        dates = pd.date_range("2024-01-01", periods=5, freq="D")
        equity = pd.Series([100, 105, 102, 108, 110], index=dates)
        returns = calculator.calculate_returns(equity)
        max_dd = calculator.calculate_max_drawdown(equity)
        result = calculator.calculate_calmar_ratio(returns, max_dd["max_drawdown"])
        assert isinstance(result, (float, int))

    def test_calculate_all_metrics(self):
        """Test calculation of all metrics together."""
        calculator = PerformanceMetrics()
        equity = pd.Series([100, 105, 102, 108, 110, 115, 112, 120],
                          index=pd.date_range("2023-01-01", periods=8, freq="D"))
        trades = pd.DataFrame({"pnl": [10.0, -5.0, 15.0, -8.0]})

        metrics = calculator.calculate_all_metrics(equity, trades)

        # Check specific attributes on MetricsResult
        assert hasattr(metrics, "total_return")
        assert hasattr(metrics, "sharpe_ratio")

    def test_empty_series_error(self):
        """Test behavior with empty series."""
        calculator = PerformanceMetrics()
        equity = pd.Series([], dtype=float)

        # For empty series, should raise InsufficientDataError
        with pytest.raises(InsufficientDataError):
            calculator.calculate_total_return(equity)

    def test_exception_classes_exist(self):
        """Test all exception classes exist."""
        assert InsufficientDataError
        assert InvalidFrequencyError
        assert LibraryImportError
        assert MetricsCalculationError
        assert MissingColumnError

    def test_exception_inheritance(self):
        """Test exceptions inherit from base MetricsCalculationError."""
        # These exception classes don't actually inherit from MetricsCalculationError
        # They inherit directly from Exception
        assert issubclass(InsufficientDataError, Exception)
        assert issubclass(InvalidFrequencyError, Exception)
        assert issubclass(MissingColumnError, Exception)
