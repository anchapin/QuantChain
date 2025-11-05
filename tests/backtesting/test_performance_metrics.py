"""
Tests for performance metrics calculation using QuantStats and Empyrical.
"""

import pytest
from datetime import datetime
import pandas as pd
from unittest.mock import patch

# Import classes that will be implemented
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
from quantchain.backtesting.engine import BacktestResult, BacktestConfig


class TestReturnCalculations:
    """Test return calculation methods."""

    def test_calculate_returns_basic(self):
        """Test basic returns calculation."""
        metrics = PerformanceMetrics()

        # Create sample equity curve
        dates = pd.date_range("2023-01-01", periods=10, freq="D")
        equity_values = [
            100000,
            101000,
            102000,
            101500,
            103000,
            104500,
            103500,
            105000,
            106000,
            107000,
        ]
        equity_curve = pd.Series(equity_values, index=dates)

        returns = metrics.calculate_returns(equity_curve)

        assert len(returns) == 9  # One less than equity curve
        assert isinstance(returns, pd.Series)
        assert returns.index[0] == dates[1]  # Starts from second date

        # Check first return calculation
        expected_first_return = (101000 - 100000) / 100000
        assert abs(returns.iloc[0] - expected_first_return) < 1e-10

    def test_calculate_returns_insufficient_data(self):
        """Test returns calculation with insufficient data."""
        metrics = PerformanceMetrics()

        # Single point
        equity_curve = pd.Series([100000], index=[datetime(2023, 1, 1)])
        with pytest.raises(InsufficientDataError):
            metrics.calculate_returns(equity_curve)

        # Empty data
        equity_curve = pd.Series([], dtype=float)
        with pytest.raises(InsufficientDataError):
            metrics.calculate_returns(equity_curve)

    def test_calculate_total_return(self):
        """Test total return calculation."""
        metrics = PerformanceMetrics()

        # Create equity curve
        dates = pd.date_range("2023-01-01", periods=5, freq="D")
        equity_values = [100000, 105000, 103000, 107000, 110000]
        equity_curve = pd.Series(equity_values, index=dates)

        total_return = metrics.calculate_total_return(equity_curve)
        expected = (110000 - 100000) / 100000

        assert abs(total_return - expected) < 1e-10

    def test_calculate_annualized_return(self):
        """Test annualized return calculation."""
        metrics = PerformanceMetrics()

        # Create equity curve over known period
        dates = pd.date_range("2023-01-01", periods=5, freq="D")
        equity_values = [100000, 101000, 102000, 103000, 104000]
        equity_curve = pd.Series(equity_values, index=dates)

        returns = metrics.calculate_returns(equity_curve)
        annual_return = metrics.calculate_annualized_return(returns)

        assert isinstance(annual_return, float)
        assert annual_return > 0  # Positive returns should give positive annual return


class TestRiskMetrics:
    """Test risk metric calculations."""

    def test_calculate_sharpe_ratio(self):
        """Test Sharpe ratio calculation."""
        metrics = PerformanceMetrics(risk_free_rate=0.02)

        # Create predictable returns
        returns = pd.Series([0.01, 0.015, -0.005, 0.02, 0.01, 0.008, -0.002, 0.012])
        sharpe = metrics.calculate_sharpe_ratio(returns)

        assert isinstance(sharpe, float)

        # Test with zero volatility
        zero_vol_returns = pd.Series([0.01] * 10)
        sharpe_zero_vol = metrics.calculate_sharpe_ratio(zero_vol_returns)
        assert sharpe_zero_vol == 0.0

        # Test with empty returns
        empty_returns = pd.Series([], dtype=float)
        sharpe_empty = metrics.calculate_sharpe_ratio(empty_returns)
        assert sharpe_empty == 0.0

    def test_calculate_sortino_ratio(self):
        """Test Sortino ratio calculation."""
        metrics = PerformanceMetrics(risk_free_rate=0.02)

        # Create mixed returns
        returns = pd.Series([0.01, 0.015, -0.005, 0.02, 0.01, 0.008, -0.002, 0.012])
        sortino = metrics.calculate_sortino_ratio(returns)

        assert isinstance(sortino, float)

        # Test with no downside returns
        positive_returns = pd.Series([0.01, 0.015, 0.02, 0.01, 0.008, 0.012])
        sortino_no_downside = metrics.calculate_sortino_ratio(positive_returns)
        assert sortino_no_downside == float("inf")

        # Test with empty returns
        empty_returns = pd.Series([], dtype=float)
        sortino_empty = metrics.calculate_sortino_ratio(empty_returns)
        assert sortino_empty == 0.0

    def test_calculate_max_drawdown(self):
        """Test maximum drawdown calculation."""
        metrics = PerformanceMetrics()

        # Create equity curve with clear drawdown
        dates = pd.date_range("2023-01-01", periods=10, freq="D")
        equity_values = [
            100000,
            105000,
            110000,
            108000,
            105000,  # Drawdown starts
            103000,
            102000,
            104000,
            106000,
            108000,
        ]  # Recovery
        equity_curve = pd.Series(equity_values, index=dates)

        drawdown_info = metrics.calculate_max_drawdown(equity_curve)

        assert "max_drawdown" in drawdown_info
        assert "max_drawdown_duration" in drawdown_info
        assert "max_drawdown_start" in drawdown_info
        assert "max_drawdown_end" in drawdown_info

        assert drawdown_info["max_drawdown"] > 0
        assert drawdown_info["max_drawdown_duration"] >= 0

        # Test with insufficient data
        single_point = pd.Series([100000], index=[datetime(2023, 1, 1)])
        dd_single = metrics.calculate_max_drawdown(single_point)
        assert dd_single["max_drawdown"] == 0.0
        assert dd_single["max_drawdown_duration"] == 0


class TestTradeBasedMetrics:
    """Test trade-based metric calculations."""

    def test_calculate_win_rate(self):
        """Test win rate calculation."""
        metrics = PerformanceMetrics()

        # Create trade log with P&L
        trades = pd.DataFrame({"pnl": [100, -50, 75, -25, 200, -100, 50]})

        win_rate = metrics.calculate_win_rate(trades)
        expected = 4 / 7  # 4 winning trades out of 7
        assert abs(win_rate - expected) < 1e-10

        # Test with empty trades
        empty_trades = pd.DataFrame({"pnl": []})
        win_rate_empty = metrics.calculate_win_rate(empty_trades)
        assert win_rate_empty == 0.0

        # Test with missing pnl column
        trades_no_pnl = pd.DataFrame({"quantity": [100, 200]})
        with pytest.raises(MissingColumnError):
            metrics.calculate_win_rate(trades_no_pnl)

    def test_calculate_profit_factor(self):
        """Test profit factor calculation."""
        metrics = PerformanceMetrics()

        # Create trade log with P&L
        trades = pd.DataFrame({"pnl": [100, -50, 75, -25, 200, -100, 50]})

        profit_factor = metrics.calculate_profit_factor(trades)

        gross_profit = 100 + 75 + 200 + 50  # 425
        gross_loss = abs(-50 + -25 + -100)  # 175
        expected = gross_profit / gross_loss

        assert abs(profit_factor - expected) < 1e-10

        # Test with no losses
        no_loss_trades = pd.DataFrame({"pnl": [100, 50, 75]})
        pf_no_loss = metrics.calculate_profit_factor(no_loss_trades)
        assert pf_no_loss == float("inf")

        # Test with empty trades
        empty_trades = pd.DataFrame({"pnl": []})
        pf_empty = metrics.calculate_profit_factor(empty_trades)
        assert pf_empty == 0.0


class TestQuantStatsIntegration:
    """Test QuantStats integration."""

    @pytest.mark.skipif(not QUANTSTATS_AVAILABLE, reason="QuantStats not available")
    @patch("quantchain.backtesting.performance_metrics.qs")
    def test_generate_tear_sheet_basic(self, mock_qs):
        """Test basic tear sheet generation."""
        mock_qs.reports.metrics.return_value = {"sharpe": 1.5, "max_drawdown": -0.1}

        metrics = PerformanceMetrics()

        # Create mock backtest result
        dates = pd.date_range("2023-01-01", periods=10, freq="D")
        equity_curve = pd.Series(
            [
                100000,
                101000,
                102000,
                103000,
                104000,
                105000,
                106000,
                107000,
                108000,
                109000,
            ],
            index=dates,
        )
        trades = pd.DataFrame({"pnl": [1000, 500, -200, 800]})
        config = BacktestConfig()

        # Create a minimal MetricsResult
        from quantchain.backtesting.engine import MetricsResult

        mock_metrics = MetricsResult(
            total_return=0.09,
            annualized_return=0.09,
            sharpe_ratio=1.5,
            sortino_ratio=1.2,
            calmar_ratio=0.8,
            max_drawdown=0.02,
            max_drawdown_duration=5,
        )

        result = BacktestResult(
            equity_curve=equity_curve,
            trade_log=trades,
            summary_stats={"total_return": 0.09},
            metrics=mock_metrics,
            execution_time=1.0,
            config=config,
        )

        tear_sheet = metrics.generate_tear_sheet(result)

        assert "basic_stats" in tear_sheet
        mock_qs.reports.metrics.assert_called_once()

    @pytest.mark.skipif(not QUANTSTATS_AVAILABLE, reason="QuantStats not available")
    @patch("quantchain.backtesting.performance_metrics.qs")
    def test_generate_tear_sheet_with_save(self, mock_qs):
        """Test tear sheet generation with save."""
        mock_qs.reports.metrics.return_value = {"sharpe": 1.5}

        metrics = PerformanceMetrics()

        dates = pd.date_range("2023-01-01", periods=5, freq="D")
        equity_curve = pd.Series([100000, 101000, 102000, 103000, 104000], index=dates)
        trades = pd.DataFrame({"pnl": [1000, 500]})
        config = BacktestConfig()

        # Create a minimal MetricsResult
        from quantchain.backtesting.engine import MetricsResult

        mock_metrics = MetricsResult(
            total_return=0.04,
            annualized_return=0.04,
            sharpe_ratio=1.5,
            sortino_ratio=1.2,
            calmar_ratio=0.8,
            max_drawdown=0.02,
            max_drawdown_duration=5,
        )

        result = BacktestResult(
            equity_curve=equity_curve,
            trade_log=trades,
            summary_stats={"total_return": 0.04},
            metrics=mock_metrics,
            execution_time=1.0,
            config=config,
        )

        save_path = "/tmp/test_tear_sheet.html"
        metrics.generate_tear_sheet(result, save_path)

        mock_qs.reports.html.assert_called_once()

    def test_generate_tear_sheet_no_quantstats(self):
        """Test tear sheet generation without QuantStats installed."""
        metrics = PerformanceMetrics()

        dates = pd.date_range("2023-01-01", periods=5, freq="D")
        equity_curve = pd.Series([100000, 101000, 102000, 103000, 104000], index=dates)
        trades = pd.DataFrame({"pnl": [1000, 500]})
        config = BacktestConfig()

        # Create a minimal MetricsResult
        from quantchain.backtesting.engine import MetricsResult

        mock_metrics = MetricsResult(
            total_return=0.04,
            annualized_return=0.04,
            sharpe_ratio=1.5,
            sortino_ratio=1.2,
            calmar_ratio=0.8,
            max_drawdown=0.02,
            max_drawdown_duration=5,
        )

        result = BacktestResult(
            equity_curve=equity_curve,
            trade_log=trades,
            summary_stats={"total_return": 0.04},
            metrics=mock_metrics,
            execution_time=1.0,
            config=config,
        )

        # Mock import error
        with patch(
            "quantchain.backtesting.performance_metrics.QUANTSTATS_AVAILABLE", False
        ):
            with pytest.raises(LibraryImportError):
                metrics.generate_tear_sheet(result)


class TestEmpyricalIntegration:
    """Test Empyrical integration."""

    @pytest.mark.skipif(not EMPYRICAL_AVAILABLE, reason="Empyrical not available")
    @patch("quantchain.backtesting.performance_metrics.empyrical")
    def test_calculate_empyrical_metrics(self, mock_empyrical):
        """Test Empyrical metrics calculation."""
        # Mock Empyrical functions
        mock_empyrical.alpha.return_value = 0.05
        mock_empyrical.beta.return_value = 1.2
        mock_empyrical.information_ratio.return_value = 0.8
        mock_empyrical.value_at_risk.return_value = -0.02
        mock_empyrical.conditional_value_at_risk.return_value = -0.03
        mock_empyrical.omega_ratio.return_value = 1.5
        mock_empyrical.stats.skew.return_value = 0.1
        mock_empyrical.stats.kurtosis.return_value = 3.0

        metrics = PerformanceMetrics()

        # Create benchmark returns
        dates = pd.date_range("2023-01-01", periods=10, freq="D")
        benchmark_returns = pd.Series([0.01] * 9, index=dates[1:])
        metrics.benchmark_returns = benchmark_returns

        returns = pd.Series(
            [0.01, 0.015, -0.005, 0.02, 0.01, 0.008, -0.002, 0.012, 0.018],
            index=dates[1:],
        )

        emp_metrics = metrics.calculate_empyrical_metrics(returns)

        assert "alpha" in emp_metrics
        assert "beta" in emp_metrics
        assert "information_ratio" in emp_metrics
        assert "var_95" in emp_metrics
        assert "cvar_95" in emp_metrics
        assert "omega_ratio" in emp_metrics
        assert "skewness" in emp_metrics
        assert "kurtosis" in emp_metrics

        # Verify Empyrial functions were called
        mock_empyrical.alpha.assert_called_once()
        mock_empyrical.beta.assert_called_once()

    def test_calculate_empyrical_metrics_no_empyrical(self):
        """Test Empyrical metrics without library installed."""
        metrics = PerformanceMetrics()
        returns = pd.Series([0.01, 0.015, -0.005])

        # Mock import error
        with patch(
            "quantchain.backtesting.performance_metrics.EMPYRICAL_AVAILABLE", False
        ):
            with pytest.raises(LibraryImportError):
                metrics.calculate_empyrical_metrics(returns)


class TestComprehensiveMetrics:
    """Test comprehensive metrics calculation."""

    def test_calculate_all_metrics(self):
        """Test calculation of all metrics."""
        metrics = PerformanceMetrics()

        # Create sample data
        dates = pd.date_range("2023-01-01", periods=20, freq="D")
        equity_curve = pd.Series(
            [
                100000,
                101000,
                102500,
                101800,
                103200,
                104500,
                103800,
                105200,
                106500,
                105800,
                107200,
                108500,
                107800,
                109200,
                110500,
                109800,
                111200,
                112500,
                111800,
                113200,
            ],
            index=dates,
        )

        trades = pd.DataFrame(
            {
                "pnl": [1000, -500, 1200, -300, 800, -200, 1500, -400, 600],
                "entry_time": pd.date_range("2023-01-01", periods=9, freq="D"),
                "exit_time": pd.date_range("2023-01-02", periods=9, freq="D"),
            }
        )

        metrics_result = metrics.calculate_all_metrics(equity_curve, trades)

        # Check all expected fields are present
        required_fields = [
            "total_return",
            "annualized_return",
            "sharpe_ratio",
            "sortino_ratio",
            "calmar_ratio",
            "max_drawdown",
            "max_drawdown_duration",
            "volatility",
            "win_rate",
            "profit_factor",
            "total_trades",
            "winning_trades",
            "losing_trades",
            "avg_win",
            "avg_loss",
            "best_trade",
            "worst_trade",
        ]

        # All required fields should be present
        missing_fields = [
            field for field in required_fields if not hasattr(metrics_result, field)
        ]
        assert not missing_fields, f"Missing fields: {missing_fields}"

        # Validate logical constraints
        assert 0 <= metrics_result.win_rate <= 1
        assert metrics_result.profit_factor >= 0
        assert metrics_result.total_trades >= 0
        assert metrics_result.max_drawdown >= 0
        assert metrics_result.max_drawdown_duration >= 0


class TestErrorHandling:
    """Test error handling."""

    def test_invalid_frequency_error(self):
        """Test invalid frequency error."""
        metrics = PerformanceMetrics()

        dates = pd.date_range("2023-01-01", periods=10, freq="D")
        returns = pd.Series([0.01] * 9, index=dates[1:])

        with pytest.raises(InvalidFrequencyError):
            metrics.calculate_sharpe_ratio(returns, frequency="invalid")

    def test_metrics_calculation_error(self):
        """Test metrics calculation error."""
        metrics = PerformanceMetrics()

        # Create problematic data
        dates = pd.date_range("2023-01-01", periods=5, freq="D")
        equity_values = [100000, float("inf"), 102000, 103000, 104000]
        equity_curve = pd.Series(equity_values, index=dates)

        with pytest.raises(MetricsCalculationError):
            metrics.calculate_total_return(equity_curve)


if __name__ == "__main__":
    pytest.main([__file__])
