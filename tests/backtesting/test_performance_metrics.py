"""Tests for performance metrics calculation."""

import pytest
import numpy as np
import pandas as pd
from unittest.mock import patch, MagicMock

from quantchain.backtesting.performance_metrics import (
    PerformanceMetrics,
    InsufficientDataError,
    InvalidFrequencyError,
    MissingColumnError,
    MetricsCalculationError,
    LibraryImportError,
    QUANTSTATS_AVAILABLE,
    EMPYRICAL_AVAILABLE,
)


class TestPerformanceMetrics:
    """Test cases for PerformanceMetrics class."""

    def setup_method(self):
        """Set up test fixtures."""
        # Sample equity curve data
        dates = pd.date_range("2023-01-01", periods=100, freq="D")
        self.equity_curve = pd.Series(
            data=np.cumprod(1 + np.random.normal(0.001, 0.02, 100)),
            index=dates,
            name="portfolio_value",
        )

        # Sample benchmark returns
        self.benchmark_returns = pd.Series(
            data=np.random.normal(0.0005, 0.015, 100), index=dates, name="benchmark"
        )

        # Sample trade log
        self.trade_log = pd.DataFrame(
            {
                "entry_time": pd.date_range("2023-01-01", periods=10, freq="D"),
                "exit_time": pd.date_range("2023-01-02", periods=10, freq="D"),
                "symbol": ["AAPL"] * 10,
                "side": ["buy"] * 5 + ["sell"] * 5,
                "quantity": [100] * 10,
                "entry_price": np.random.uniform(100, 200, 10),
                "exit_price": np.random.uniform(100, 200, 10),
                "pnl": np.random.uniform(-1000, 1000, 10),
                "commission": [1.0] * 10,
            }
        )

    def test_initialization_default(self):
        """Test default initialization."""
        metrics = PerformanceMetrics()

        assert metrics.benchmark_returns is None
        assert metrics.risk_free_rate == 0.02

    def test_initialization_with_params(self):
        """Test initialization with parameters."""
        metrics = PerformanceMetrics(
            benchmark_returns=self.benchmark_returns, risk_free_rate=0.03
        )

        assert metrics.benchmark_returns.equals(self.benchmark_returns)
        assert metrics.risk_free_rate == 0.03

    def test_calculate_returns_success(self):
        """Test successful returns calculation."""
        metrics = PerformanceMetrics()
        returns = metrics.calculate_returns(self.equity_curve)

        assert isinstance(returns, pd.Series)
        assert len(returns) == len(self.equity_curve) - 1
        assert returns.name == "portfolio_value"
        # Returns should be percentage changes
        assert not returns.isna().any()

    def test_calculate_returns_insufficient_data(self):
        """Test returns calculation with insufficient data."""
        metrics = PerformanceMetrics()
        short_equity = self.equity_curve.head(1)

        with pytest.raises(
            InsufficientDataError, match="Equity curve must have at least 2 points"
        ):
            metrics.calculate_returns(short_equity)

    def test_calculate_total_return(self):
        """Test total return calculation."""
        metrics = PerformanceMetrics()
        total_return = metrics.calculate_total_return(self.equity_curve)

        assert isinstance(total_return, float)
        expected_return = (self.equity_curve.iloc[-1] / self.equity_curve.iloc[0]) - 1
        assert abs(total_return - expected_return) < 1e-10

    def test_calculate_total_return_empty_curve(self):
        """Test total return calculation with empty curve."""
        metrics = PerformanceMetrics()
        empty_curve = pd.Series([], dtype="float64")

        with pytest.raises(
            InsufficientDataError, match="Equity curve must have at least 1 point"
        ):
            metrics.calculate_total_return(empty_curve)

    def test_calculate_annualized_return(self):
        """Test annualized return calculation."""
        metrics = PerformanceMetrics()
        ann_return = metrics.calculate_annualized_return(self.equity_curve)

        assert isinstance(ann_return, float)
        # Should be positive for upward trending equity curve
        # or negative for downward trending

    def test_calculate_volatility(self):
        """Test volatility calculation."""
        metrics = PerformanceMetrics()
        vol = metrics.calculate_volatility(self.equity_curve)

        assert isinstance(vol, float)
        assert vol >= 0  # Volatility should be non-negative

    def test_calculate_sharpe_ratio_without_benchmark(self):
        """Test Sharpe ratio calculation without benchmark."""
        metrics = PerformanceMetrics(risk_free_rate=0.02)
        sharpe = metrics.calculate_sharpe_ratio(self.equity_curve)

        assert isinstance(sharpe, float)
        # Can be negative if returns are poor

    def test_calculate_sharpe_ratio_with_benchmark(self):
        """Test Sharpe ratio calculation with benchmark."""
        metrics = PerformanceMetrics(
            benchmark_returns=self.benchmark_returns, risk_free_rate=0.02
        )
        sharpe = metrics.calculate_sharpe_ratio(self.equity_curve)

        assert isinstance(sharpe, float)

    def test_calculate_max_drawdown(self):
        """Test maximum drawdown calculation."""
        metrics = PerformanceMetrics()
        max_dd_result = metrics.calculate_max_drawdown(self.equity_curve)

        # Should return a dictionary with drawdown metrics
        assert isinstance(max_dd_result, dict)

        # Extract max drawdown value for assertion
        if 'max_drawdown' in max_dd_result:
            max_dd = max_dd_result['max_drawdown']
            assert isinstance(max_dd, (float, np.floating))
            assert max_dd >= -1  # Drawdown shouldn't exceed -100%

    def test_calculate_max_drawdown_duration(self):
        """Test maximum drawdown duration calculation."""
        metrics = PerformanceMetrics()
        max_dd_duration = metrics.calculate_max_drawdown_duration(self.equity_curve)

        assert isinstance(max_dd_duration, int)
        assert max_dd_duration >= 0

    def test_calculate_calmar_ratio(self):
        """Test Calmar ratio calculation."""
        metrics = PerformanceMetrics()
        calmar = metrics.calculate_calmar_ratio(self.equity_curve)

        assert isinstance(calmar, float)
        # Can be negative if max drawdown is positive

    def test_calculate_sortino_ratio(self):
        """Test Sortino ratio calculation."""
        metrics = PerformanceMetrics()
        sortino = metrics.calculate_sortino_ratio(self.equity_curve)

        assert isinstance(sortino, float)

    def test_calculate_win_rate(self):
        """Test win rate calculation from trade log."""
        metrics = PerformanceMetrics()
        win_rate = metrics.calculate_win_rate(self.trade_log)

        assert isinstance(win_rate, float)
        assert 0 <= win_rate <= 1

    def test_calculate_win_rate_missing_pnl_column(self):
        """Test win rate calculation with missing P&L column."""
        metrics = PerformanceMetrics()
        incomplete_log = self.trade_log.drop(columns=["pnl"])

        with pytest.raises(MissingColumnError, match="Required column 'pnl' not found"):  # Should raise MissingColumnError for missing column
            metrics.calculate_win_rate(incomplete_log)

    def test_calculate_profit_factor(self):
        """Test profit factor calculation."""
        metrics = PerformanceMetrics()
        profit_factor = metrics.calculate_profit_factor(self.trade_log)

        assert isinstance(profit_factor, float)
        assert profit_factor >= 0

    def test_calculate_profit_factor_no_winning_trades(self):
        """Test profit factor calculation with no winning trades."""
        metrics = PerformanceMetrics()
        losing_log = self.trade_log.copy()
        losing_log["pnl"] = -abs(losing_log["pnl"])  # Make all P&L negative

        profit_factor = metrics.calculate_profit_factor(losing_log)
        assert profit_factor == 0

    def test_calculate_profit_factor_no_losing_trades(self):
        """Test profit factor calculation with no losing trades."""
        metrics = PerformanceMetrics()
        winning_log = self.trade_log.copy()
        winning_log["pnl"] = abs(winning_log["pnl"])  # Make all P&L positive

        profit_factor = metrics.calculate_profit_factor(winning_log)
        assert profit_factor == float("inf")

    def test_calculate_average_trade(self):
        """Test average trade calculation."""
        metrics = PerformanceMetrics()
        avg_trade = metrics.calculate_average_trade(self.trade_log)

        assert isinstance(avg_trade, float)

    def test_calculate_total_trades(self):
        """Test total trades calculation."""
        metrics = PerformanceMetrics()
        total_trades = metrics.calculate_total_trades(self.trade_log)

        assert isinstance(total_trades, int)
        assert total_trades == len(self.trade_log)

    def test_calculate_average_win(self):
        """Test average winning trade calculation."""
        metrics = PerformanceMetrics()
        avg_win = metrics.calculate_average_win(self.trade_log)

        assert isinstance(avg_win, float)
        # Should be None or positive if there are winning trades

    def test_calculate_average_loss(self):
        """Test average losing trade calculation."""
        metrics = PerformanceMetrics()
        avg_loss = metrics.calculate_average_loss(self.trade_log)

        assert isinstance(avg_loss, float)
        # Should be None or negative if there are losing trades

    def test_calculate_largest_win(self):
        """Test largest winning trade calculation."""
        metrics = PerformanceMetrics()
        largest_win = metrics.calculate_largest_win(self.trade_log)

        assert isinstance(largest_win, float)

    def test_calculate_largest_loss(self):
        """Test largest losing trade calculation."""
        metrics = PerformanceMetrics()
        largest_loss = metrics.calculate_largest_loss(self.trade_log)

        assert isinstance(largest_loss, float)

    def test_calculate_win_loss_ratio(self):
        """Test win/loss ratio calculation."""
        metrics = PerformanceMetrics()
        win_loss_ratio = metrics.calculate_win_loss_ratio(self.trade_log)

        assert isinstance(win_loss_ratio, float)
        assert win_loss_ratio >= 0

    def test_calculate_var(self):
        """Test Value at Risk calculation."""
        metrics = PerformanceMetrics()
        var_95 = metrics.calculate_var(self.equity_curve, confidence_level=0.95)

        assert isinstance(var_95, float)
        # VaR should be negative (representing a loss)

    def test_calculate_var_invalid_confidence(self):
        """Test VaR calculation with invalid confidence level."""
        metrics = PerformanceMetrics()

        with pytest.raises(
            ValueError, match="Confidence level must be between 0 and 1"
        ):
            metrics.calculate_var(self.equity_curve, confidence_level=1.5)

    def test_calculate_cvar(self):
        """Test Conditional Value at Risk calculation."""
        metrics = PerformanceMetrics()
        cvar_95 = metrics.calculate_cvar(self.equity_curve, confidence_level=0.95)

        assert isinstance(cvar_95, float)
        # CVaR should be negative (representing a loss)
        # CVaR should be more negative than VaR
        var_95 = metrics.calculate_var(self.equity_curve, confidence_level=0.95)
        assert cvar_95 <= var_95

    def test_calculate_beta_with_benchmark(self):
        """Test beta calculation with benchmark."""
        metrics = PerformanceMetrics(benchmark_returns=self.benchmark_returns)
        beta = metrics.calculate_beta(self.equity_curve)

        assert isinstance(beta, float)
        # Beta can be positive or negative

    def test_calculate_beta_without_benchmark(self):
        """Test beta calculation without benchmark."""
        metrics = PerformanceMetrics()

        with pytest.raises(
            ValueError, match="Benchmark returns required for beta calculation"
        ):
            metrics.calculate_beta(self.equity_curve)

    def test_calculate_alpha_with_benchmark(self):
        """Test alpha calculation with benchmark."""
        metrics = PerformanceMetrics(
            benchmark_returns=self.benchmark_returns, risk_free_rate=0.02
        )
        alpha = metrics.calculate_alpha(self.equity_curve)

        assert isinstance(alpha, float)
        # Alpha can be positive or negative

    def test_calculate_alpha_without_benchmark(self):
        """Test alpha calculation without benchmark."""
        metrics = PerformanceMetrics()

        with pytest.raises(
            ValueError, match="Benchmark returns required for alpha calculation"
        ):
            metrics.calculate_alpha(self.equity_curve)

    def test_calculate_information_ratio_with_benchmark(self):
        """Test information ratio calculation with benchmark."""
        metrics = PerformanceMetrics(benchmark_returns=self.benchmark_returns)
        ir = metrics.calculate_information_ratio(self.equity_curve)

        assert isinstance(ir, float)
        # Information ratio can be positive or negative

    def test_calculate_information_ratio_without_benchmark(self):
        """Test information ratio calculation without benchmark."""
        metrics = PerformanceMetrics()

        with pytest.raises(
            ValueError, match="Benchmark returns required for information ratio"
        ):
            metrics.calculate_information_ratio(self.equity_curve)

    @patch("quantchain.backtesting.performance_metrics.QUANTSTATS_AVAILABLE", True)
    @patch("quantchain.backtesting.performance_metrics.qs")
    def test_calculate_quantstats_metrics_with_library(self, mock_qs):
        """Test QuantStats metrics calculation with library available."""
        mock_qs.reports.metrics.return_value = {
            "Sharpe Ratio": 1.5,
            "Max Drawdown": -0.1,
            "Volatility": 0.2,
        }

        metrics = PerformanceMetrics()
        quantstats_metrics = metrics.calculate_quantstats_metrics(self.equity_curve)

        assert isinstance(quantstats_metrics, dict)
        assert "Sharpe Ratio" in quantstats_metrics

    @patch("quantchain.backtesting.performance_metrics.QUANTSTATS_AVAILABLE", False)
    def test_calculate_quantstats_metrics_without_library(self):
        """Test QuantStats metrics calculation without library."""
        metrics = PerformanceMetrics()

        with pytest.raises(
            LibraryImportError, match="QuantStats library is not available"
        ):
            metrics.calculate_quantstats_metrics(self.equity_curve)

    @patch("quantchain.backtesting.performance_metrics.EMPYRICAL_AVAILABLE", True)
    @patch("quantchain.backtesting.performance_metrics.empyrical")
    def test_calculate_empyrical_metrics_with_library(self, mock_empyrical):
        """Test Empyrical metrics calculation with library available."""
        mock_empyrical.sharpe_ratio.return_value = 1.2
        mock_empyrical.max_drawdown.return_value = -0.15
        mock_empyrical.annual_volatility.return_value = 0.25

        metrics = PerformanceMetrics()
        returns = metrics.calculate_returns(self.equity_curve)
        empyrical_metrics = metrics.calculate_empyrical_metrics(returns)

        assert isinstance(empyrical_metrics, dict)
        assert "sharpe_ratio" in empyrical_metrics

    @patch("quantchain.backtesting.performance_metrics.EMPYRICAL_AVAILABLE", False)
    def test_calculate_empyrical_metrics_without_library(self):
        """Test Empyrical metrics calculation without library."""
        metrics = PerformanceMetrics()
        returns = metrics.calculate_returns(self.equity_curve)

        with pytest.raises(
            LibraryImportError, match="Empyrical library is not available"
        ):
            metrics.calculate_empyrical_metrics(returns)

    def test_calculate_comprehensive_metrics(self):
        """Test comprehensive metrics calculation."""
        metrics = PerformanceMetrics(benchmark_returns=self.benchmark_returns)
        comprehensive = metrics.calculate_comprehensive_metrics(
            self.equity_curve, self.trade_log
        )

        assert isinstance(comprehensive, dict)

        # Check for key metric categories
        expected_keys = [
            "return_metrics",
            "risk_metrics",
            "trade_metrics",
        ]

        for key in expected_keys:
            assert key in comprehensive
            assert isinstance(comprehensive[key], dict)

    def test_calculate_comprehensive_metrics_without_trade_log(self):
        """Test comprehensive metrics calculation without trade log."""
        metrics = PerformanceMetrics()
        comprehensive = metrics.calculate_comprehensive_metrics(self.equity_curve)

        assert isinstance(comprehensive, dict)
        assert "return_metrics" in comprehensive
        assert "risk_metrics" in comprehensive
        assert "trade_metrics" not in comprehensive

    def test_generate_metrics_report(self):
        """Test metrics report generation."""
        metrics = PerformanceMetrics()
        report = metrics.generate_metrics_report(self.equity_curve, self.trade_log)

        assert isinstance(report, str)
        assert len(report) > 0
        # Should contain metric names
        assert "Total Return" in report
        assert "Sharpe Ratio" in report

    def test_calculate_rolling_metrics(self):
        """Test rolling metrics calculation."""
        metrics = PerformanceMetrics()
        rolling_metrics = metrics.calculate_rolling_metrics(
            self.equity_curve, window=30
        )

        assert isinstance(rolling_metrics, pd.DataFrame)
        assert len(rolling_metrics) > 0
        # Should have columns for different rolling metrics
        expected_columns = ["rolling_return", "rolling_volatility", "rolling_sharpe"]
        for col in expected_columns:
            assert col in rolling_metrics.columns

    def test_calculate_rolling_metrics_window_too_large(self):
        """Test rolling metrics with window larger than data."""
        metrics = PerformanceMetrics()
        short_equity = self.equity_curve.head(10)

        with pytest.raises(
            ValueError, match="Window size cannot be larger than data length"
        ):
            metrics.calculate_rolling_metrics(short_equity, window=20)

    def test_calculate_metrics_by_period(self):
        """Test metrics calculation by period."""
        metrics = PerformanceMetrics()
        monthly_metrics = metrics.calculate_metrics_by_period(
            self.equity_curve, period="M"  # Monthly
        )

        assert isinstance(monthly_metrics, pd.DataFrame)
        assert len(monthly_metrics) > 0

    def test_calculate_metrics_by_invalid_period(self):
        """Test metrics calculation with invalid period."""
        metrics = PerformanceMetrics()

        with pytest.raises(ValueError, match="Invalid period"):
            metrics.calculate_metrics_by_period(self.equity_curve, period="X")

    def test_compare_strategies(self):
        """Test strategy comparison metrics."""
        # Create second equity curve
        equity_curve_2 = pd.Series(
            data=np.cumprod(1 + np.random.normal(0.0005, 0.025, 100)),
            index=self.equity_curve.index,
            name="strategy_2",
        )

        metrics = PerformanceMetrics()
        comparison = metrics.compare_strategies(self.equity_curve, equity_curve_2)

        assert isinstance(comparison, dict)
        assert "strategy_1" in comparison
        assert "strategy_2" in comparison
        assert "winner" in comparison
