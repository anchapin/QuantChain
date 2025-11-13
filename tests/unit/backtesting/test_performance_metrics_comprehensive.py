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
        equity = np.array([100, 105, 102, 108, 110, 107, 112, 115, 113, 118])
        equity_series = pd.Series(equity, index=dates)

        # Test individual methods
        total_return = calculator.calculate_total_return(equity_series)
        returns = calculator.calculate_returns(equity_series)
        annual_return = calculator.calculate_annualized_return(returns)
        volatility = calculator.calculate_volatility(returns)
        sharpe = calculator.calculate_sharpe_ratio(returns)
        
        # Test basic calculations work
        assert total_return > 0
        assert isinstance(returns, pd.Series)
        assert isinstance(annual_return, float)
        assert isinstance(volatility, float)
        assert isinstance(sharpe, float)

    def test_calculate_performance_metrics_empty_data(self):
        """Test metrics calculation with empty data."""
        calculator = PerformanceMetrics()

        with pytest.raises(InsufficientDataError):
            calculator.calculate_returns(pd.Series([]))

    def test_calculate_performance_metrics_insufficient_data(self):
        """Test metrics calculation with insufficient data (less than 2 points)."""
        calculator = PerformanceMetrics()

        dates = pd.date_range("2024-01-01", periods=1, freq="D")
        equity = np.array([100])

        with pytest.raises(InsufficientDataError):
            calculator.calculate_performance_metrics(dates, equity)

    def test_calculate_performance_metrics_single_valid_point(self):
        """Test metrics calculation with single data point."""
        calculator = PerformanceMetrics()

        # Create single point but use fallback calculation
        dates = pd.date_range("2024-01-01", periods=1, freq="D")
        equity = np.array([100])

        metrics = calculator._calculate_basic_metrics(dates, equity)
        assert metrics["total_return"] == 0.0

    def test_calculate_basic_metrics_no_returns(self):
        """Test basic metrics calculation with no returns."""
        calculator = PerformanceMetrics()

        dates = pd.date_range("2024-01-01", periods=5, freq="D")
        equity = np.array([100, 100, 100, 100, 100])  # No change

        metrics = calculator._calculate_basic_metrics(dates, equity)
        assert metrics["total_return"] == 0.0
        assert metrics["volatility"] == 0.0

    def test_calculate_risk_metrics(self):
        """Test risk metrics calculation."""
        calculator = PerformanceMetrics()

        dates = pd.date_range("2024-01-01", periods=100, freq="D")
        # Simulate some price data with volatility
        returns = np.random.normal(0.001, 0.02, 99)  # Daily returns
        equity = 100 * np.exp(np.cumsum(np.insert(returns, 0, 0)))

        risk_metrics = calculator._calculate_risk_metrics(equity)

        assert "max_drawdown" in risk_metrics
        assert "max_drawdown_duration" in risk_metrics
        assert "calmar_ratio" in risk_metrics
        assert "sortino_ratio" in risk_metrics
        assert risk_metrics["max_drawdown"] >= 0

    def test_calculate_trade_level_metrics(self):
        """Test trade-level metrics calculation."""
        calculator = PerformanceMetrics()

        trades = pd.DataFrame(
            {
                "entry_date": pd.date_range("2024-01-01", periods=5, freq="D"),
                "exit_date": pd.date_range("2024-01-02", periods=5, freq="D"),
                "entry_price": [100, 101, 102, 103, 104],
                "exit_price": [102, 100, 105, 101, 106],
                "quantity": [100, 100, 100, 100, 100],
                "side": ["long", "short", "long", "short", "long"],
            }
        )

        trade_metrics = calculator._calculate_trade_level_metrics(trades)

        assert "total_trades" in trade_metrics
        assert "win_rate" in trade_metrics
        assert "profit_factor" in trade_metrics
        assert "avg_trade_return" in trade_metrics

    def test_calculate_trade_level_metrics_empty_trades(self):
        """Test trade-level metrics with no trades."""
        calculator = PerformanceMetrics()

        trades = pd.DataFrame(
            columns=[
                "entry_date",
                "exit_date",
                "entry_price",
                "exit_price",
                "quantity",
                "side",
            ]
        )

        trade_metrics = calculator._calculate_trade_level_metrics(trades)

        assert trade_metrics["total_trades"] == 0
        assert trade_metrics["win_rate"] == 0.0

    def test_calculate_trade_level_metrics_missing_columns(self):
        """Test trade-level metrics with missing columns."""
        calculator = PerformanceMetrics()

        # Missing required columns
        trades = pd.DataFrame(
            {
                "entry_date": pd.date_range("2024-01-01", periods=2, freq="D"),
                "exit_price": [102, 100],
            }
        )

        with pytest.raises(MissingColumnError):
            calculator._calculate_trade_level_metrics(trades)

    def test_calculate_performance_metrics_with_benchmark(self):
        """Test performance metrics calculation with benchmark data."""
        calculator = PerformanceMetrics()

        strategy_dates = pd.date_range("2024-01-01", periods=50, freq="D")
        strategy_equity = 100 + np.cumsum(np.random.normal(0.01, 0.05, 50))
        benchmark_dates = pd.date_range("2024-01-01", periods=50, freq="D")
        benchmark_equity = 100 + np.cumsum(np.random.normal(0.005, 0.03, 50))

        metrics = calculator.calculate_performance_metrics(
            strategy_dates, strategy_equity, benchmark_dates, benchmark_equity
        )

        assert metrics is not None
        assert "beta" in metrics
        assert "alpha" in metrics
        assert "correlation" in metrics
        assert "information_ratio" in metrics

    def test_calculate_performance_metrics_different_frequencies(self):
        """Test metrics calculation with different frequencies."""
        calculator = PerformanceMetrics()

        # Test hourly frequency
        dates = pd.date_range("2024-01-01", periods=24, freq="H")
        equity = 100 + np.cumsum(np.random.normal(0.001, 0.01, 24))

        metrics = calculator.calculate_performance_metrics(dates, equity)
        assert metrics is not None

    def test_calculate_performance_metrics_invalid_frequency(self):
        """Test metrics calculation with invalid frequency."""
        calculator = PerformanceMetrics()

        # Create data with irregular frequency
        dates = pd.to_datetime(
            ["2024-01-01", "2024-01-03", "2024-01-05", "2024-01-06"]
        )  # Irregular gaps
        equity = np.array([100, 102, 101, 103])

        with pytest.raises(InvalidFrequencyError):
            calculator.calculate_performance_metrics(dates, equity)

    def test_calculate_performance_metrics_with_transactions(self):
        """Test metrics calculation with transaction data."""
        calculator = PerformanceMetrics()

        dates = pd.date_range("2024-01-01", periods=50, freq="D")
        equity = 100 + np.cumsum(np.random.normal(0.01, 0.05, 50))

        # Create some mock transaction data
        transactions = pd.DataFrame(
            {
                "date": dates[::10],  # Every 10 days
                "type": ["deposit", "withdrawal", "deposit", "withdrawal"],
                "amount": [1000, -500, 2000, -300],
            }
        )

        metrics = calculator.calculate_performance_metrics(
            dates, equity, transactions=transactions
        )
        assert metrics is not None

    def test_calculate_portfolio_metrics(self):
        """Test portfolio-level metrics calculation."""
        calculator = PerformanceMetrics()

        returns = np.random.normal(0.001, 0.02, 100)

        portfolio_metrics = calculator._calculate_portfolio_metrics(returns)

        assert portfolio_metrics is not None
        assert "portfolio_volatility" in portfolio_metrics
        assert "portfolio_var" in portfolio_metrics
        assert "portfolio_skew" in portfolio_metrics
        assert "portfolio_kurtosis" in portfolio_metrics

    def test_calculate_attribution_analysis(self):
        """Test attribution analysis calculation."""
        calculator = PerformanceMetrics()

        # Mock sector returns data
        sector_returns = pd.DataFrame(
            {
                "technology": np.random.normal(0.02, 0.05, 252),
                "healthcare": np.random.normal(0.01, 0.03, 252),
                "finance": np.random.normal(0.015, 0.04, 252),
            }
        )

        weights = np.array([0.4, 0.3, 0.3])

        attribution = calculator._calculate_attribution_analysis(
            sector_returns, weights
        )

        assert attribution is not None
        assert "contribution" in attribution
        assert "attribution_pct" in attribution

    def test_validate_data_length_mismatch(self):
        """Test data validation with length mismatches."""
        calculator = PerformanceMetrics()

        dates = pd.date_range("2024-01-01", periods=10, freq="D")
        equity = np.array([100, 105, 102])  # Only 3 points vs 10 dates

        with pytest.raises(MetricsCalculationError):
            calculator.calculate_performance_metrics(dates, equity)

    def test_validate_data_duplicate_dates(self):
        """Test data validation with duplicate dates."""
        calculator = PerformanceMetrics()

        dates = pd.to_datetime(["2024-01-01", "2024-01-01", "2024-01-02", "2024-01-02"])
        equity = np.array([100, 101, 102, 103])

        with pytest.raises(MetricsCalculationError):
            calculator.calculate_performance_metrics(dates, equity)

    def test_calculate_rolling_metrics(self):
        """Test rolling metrics calculation."""
        calculator = PerformanceMetrics()

        returns = np.random.normal(0.001, 0.02, 252)

        rolling_metrics = calculator._calculate_rolling_metrics(returns, window=30)

        assert rolling_metrics is not None
        assert isinstance(rolling_metrics, dict)
        assert "rolling_sharpe" in rolling_metrics
        assert "rolling_max_dd" in rolling_metrics

    def test_calculate_scenario_analysis(self):
        """Test scenario analysis calculation."""
        calculator = PerformanceMetrics()

        dates = pd.date_range("2024-01-01", periods=252, freq="D")

        # Simulate different market scenarios
        bull_market_equity = 100 * (1 + np.cumsum(np.random.uniform(0.001, 0.005, 252)))
        bear_market_equity = 100 * (
            1 + np.cumsum(np.random.uniform(-0.005, -0.001, 252))
        )

        bull_metrics = calculator.calculate_performance_metrics(
            dates, bull_market_equity
        )
        bear_metrics = calculator.calculate_performance_metrics(
            dates, bear_market_equity
        )

        assert bull_metrics is not None
        assert bear_metrics is not None

    def test_calculate_performance_metrics_with_commission_impact(self):
        """Test metrics calculation considering commission impact."""
        calculator = PerformanceMetrics()

        dates = pd.date_range("2024-01-01", periods=50, freq="D")
        equity = 100 + np.cumsum(np.random.normal(0.01, 0.05, 50))

        # Mock commission data
        commissions = np.random.uniform(0, 0.001, 50)  # Per period commission

        metrics = calculator.calculate_performance_metrics(
            dates, equity, commissions=commissions
        )

        assert metrics is not None
        # Commission-adjusted return should be lower than gross return
        assert "net_return" in metrics
        assert "gross_return" in metrics
        assert metrics["net_return"] <= metrics["gross_return"]

    def test_calculate_performance_metrics_library_import_error(self):
        """Test metrics calculation when libraries are not available."""
        calculator = PerformanceMetrics()

        # Mock library unavailability
        import quantchain.backtesting.performance_metrics as pm

        original_quantstats = pm.QUANTSTATS_AVAILABLE
        original_empyrical = pm.EMPYRICAL_AVAILABLE

        pm.QUANTSTATS_AVAILABLE = False
        pm.EMPYRICAL_AVAILABLE = False

        try:
            # Should fall back to basic calculations
            dates = pd.date_range("2024-01-01", periods=10, freq="D")
            equity = np.array([100, 105, 102, 108, 110, 107, 112, 115, 113, 118])

            metrics = calculator.calculate_performance_metrics(dates, equity)
            assert metrics is not None
            assert "total_return" in metrics

        finally:
            # Restore original values
            pm.QUANTSTATS_AVAILABLE = original_quantstats
            pm.EMPYRICAL_AVAILABLE = original_empyrical

    def test_export_metrics_to_csv(self):
        """Test exporting metrics to CSV."""
        calculator = PerformanceMetrics()

        dates = pd.date_range("2024-01-01", periods=10, freq="D")
        equity = np.array([100, 105, 102, 108, 110, 107, 112, 115, 113, 118])

        metrics = calculator.calculate_performance_metrics(dates, equity)

        # Test export functionality
        from tempfile import NamedTemporaryFile

        with NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            temp_file = f.name

        try:
            calculator.export_metrics_to_csv(metrics, temp_file)

            # Verify file was created and has content
            import os

            assert os.path.exists(temp_file)
            assert os.path.getsize(temp_file) > 0
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)

    def test_generate_performance_report(self):
        """Test performance report generation."""
        calculator = PerformanceMetrics()

        dates = pd.date_range("2024-01-01", periods=50, freq="D")
        equity = 100 + np.cumsum(np.random.normal(0.01, 0.05, 50))

        metrics = calculator.calculate_performance_metrics(dates, equity)

        report = calculator.generate_performance_report(metrics)

        assert isinstance(report, str)
        assert len(report) > 0
        assert "Performance Summary" in report

    def test_calculate_advanced_risk_metrics(self):
        """Test advanced risk metrics calculation."""
        calculator = PerformanceMetrics()

        returns = np.random.normal(0.001, 0.02, 252)

        advanced_risk = calculator._calculate_advanced_risk_metrics(returns)

        assert advanced_risk is not None
        assert "conditional_value_at_risk" in advanced_risk
        assert "expected_shortfall" in advanced_risk
        assert "pain_index" in advanced_risk

    def test_calculate_performance_metrics_with_custom_config(self):
        """Test metrics calculation with custom configuration."""
        config = {
            "risk_free_rate": 0.02,
            "benchmark_period": 252,
            "rolling_window": 30,
            "confidence_level": 0.95,
        }

        calculator = PerformanceMetrics(config=config)

        dates = pd.date_range("2024-01-01", periods=50, freq="D")
        equity = 100 + np.cumsum(np.random.normal(0.01, 0.05, 50))

        metrics = calculator.calculate_performance_metrics(dates, equity)
        assert metrics is not None

    def test_calculate_performance_metrics_with_starting_capital(self):
        """Test metrics calculation with specified starting capital."""
        calculator = PerformanceMetrics()

        dates = pd.date_range("2024-01-01", periods=50, freq="D")
        equity = 100 + np.cumsum(np.random.normal(0.01, 0.05, 50))

        metrics = calculator.calculate_performance_metrics(
            dates, equity, starting_capital=10000
        )

        assert metrics is not None
        # Check if starting capital is properly accounted for
        assert "absolute_return" in metrics
