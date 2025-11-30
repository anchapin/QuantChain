"""Comprehensive tests for Backtesting.py Engine."""

from unittest.mock import Mock, patch

import numpy as np
import pandas as pd
import pytest

from quantchain.backtesting.backtestingpy_engine import BacktestingPyEngine
from quantchain.backtesting.engine import BacktestConfig, BacktestResult, MetricsResult


@pytest.mark.unit
class TestBacktestingPyEngine:
    """Test BacktestingPyEngine class."""

    @patch("quantchain.backtesting.backtestingpy_engine._BACKTESTING_AVAILABLE", True)
    @patch("quantchain.backtesting.backtestingpy_engine.Backtest")
    @patch("quantchain.backtesting.backtestingpy_engine.Strategy")
    def test_engine_initialization_with_backtesting_available(
        self, mock_strategy, mock_backtest
    ):
        """Test engine initialization when backtesting.py is available."""
        # Mock the Backtest constructor
        mock_backtest_instance = Mock()
        mock_backtest.return_value = mock_backtest_instance

        config = BacktestConfig(initial_capital=100000, commission=0.001)
        engine = BacktestingPyEngine(config)

        assert engine.config == config
        assert engine._backtest == mock_backtest_instance
        assert engine._results is None
        assert engine._equity_curve_data is None

        # Verify Backtest was called with correct parameters
        mock_backtest.assert_called_once()
        call_args = mock_backtest.call_args
        assert call_args[1]["cash"] == 100000
        assert call_args[1]["commission"] == 0.001
        assert call_args[1]["exclusive_orders"] is True

    @patch("quantchain.backtesting.backtestingpy_engine._BACKTESTING_AVAILABLE", False)
    def test_engine_initialization_without_backtesting(self):
        """Test engine initialization when backtesting.py is not available."""
        with pytest.raises(ImportError, match="backtesting.py library not installed"):
            BacktestingPyEngine()

    @patch("quantchain.backtesting.backtestingpy_engine._BACKTESTING_AVAILABLE", True)
    @patch("quantchain.backtesting.backtestingpy_engine.Backtest")
    @patch("quantchain.backtesting.backtestingpy_engine.Strategy")
    def test_engine_initialization_backtest_failure(self, mock_strategy, mock_backtest):
        """Test engine initialization when Backtest constructor fails."""
        mock_backtest.side_effect = Exception("Backtest initialization failed")

        with pytest.raises(
            ImportError, match="Failed to initialize backtesting.py engine"
        ):
            BacktestingPyEngine()

    @patch("quantchain.backtesting.backtestingpy_engine._BACKTESTING_AVAILABLE", True)
    @patch("quantchain.backtesting.backtestingpy_engine.Backtest")
    @patch("quantchain.backtesting.backtestingpy_engine.Strategy")
    def test_engine_default_initialization(self, mock_strategy, mock_backtest):
        """Test engine initialization with default configuration."""
        mock_backtest_instance = Mock()
        mock_backtest.return_value = mock_backtest_instance

        engine = BacktestingPyEngine()

        assert engine.config.initial_capital == 100000.0
        assert engine.config.commission == 0.001
        assert engine.config.slippage == 0.0005

    @patch("quantchain.backtesting.backtestingpy_engine._BACKTESTING_AVAILABLE", True)
    @patch("quantchain.backtesting.backtestingpy_engine.Backtest")
    @patch("quantchain.backtesting.backtestingpy_engine.Strategy")
    def test_convert_data_format_lowercase_columns(self, mock_strategy, mock_backtest):
        """Test data format conversion with lowercase columns."""
        mock_backtest_instance = Mock()
        mock_backtest.return_value = mock_backtest_instance

        engine = BacktestingPyEngine()

        # Test with lowercase columns
        data = pd.DataFrame(
            {
                "open": [100, 101, 102],
                "high": [102, 103, 104],
                "low": [99, 100, 101],
                "close": [101, 102, 103],
                "volume": [1000, 1100, 1200],
            }
        )

        result = engine._convert_data_format(data)

        # Should convert to proper case
        expected_columns = ["Open", "High", "Low", "Close", "Volume"]
        assert list(result.columns) == expected_columns

    @patch("quantchain.backtesting.backtestingpy_engine._BACKTESTING_AVAILABLE", True)
    @patch("quantchain.backtesting.backtestingpy_engine.Backtest")
    @patch("quantchain.backtesting.backtestingpy_engine.Strategy")
    def test_convert_data_format_uppercase_columns(self, mock_strategy, mock_backtest):
        """Test data format conversion with mixed case columns."""
        mock_backtest_instance = Mock()
        mock_backtest.return_value = mock_backtest_instance

        engine = BacktestingPyEngine()

        # Test with mixed case columns
        data = pd.DataFrame(
            {
                "Open": [100, 101, 102],
                "HIGH": [102, 103, 104],
                "Low": [99, 100, 101],
                "Close": [101, 102, 103],
                "Volume": [1000, 1100, 1200],
            }
        )

        result = engine._convert_data_format(data)

        # Should convert to proper case
        expected_columns = ["Open", "High", "Low", "Close", "Volume"]
        assert list(result.columns) == expected_columns

    @patch("quantchain.backtesting.backtestingpy_engine._BACKTESTING_AVAILABLE", True)
    @patch("quantchain.backtesting.backtestingpy_engine.Backtest")
    @patch("quantchain.backtesting.backtestingpy_engine.Strategy")
    def test_convert_data_format_missing_columns(self, mock_strategy, mock_backtest):
        """Test data format conversion with missing required columns."""
        mock_backtest_instance = Mock()
        mock_backtest.return_value = mock_backtest_instance

        engine = BacktestingPyEngine()

        # Test with missing column
        data = pd.DataFrame(
            {
                "open": [100, 101, 102],
                "high": [102, 103, 104],
                "close": [101, 102, 103],  # Missing 'low' and 'volume'
            }
        )

        with pytest.raises(
            ValueError, match="Missing required columns: \\['low', 'volume'\\]"
        ):
            engine._convert_data_format(data)

    @patch("quantchain.backtesting.backtestingpy_engine._BACKTESTING_AVAILABLE", True)
    @patch("quantchain.backtesting.backtestingpy_engine.Backtest")
    @patch("quantchain.backtesting.backtestingpy_engine.Strategy")
    def test_convert_data_format_timestamp_index(self, mock_strategy, mock_backtest):
        """Test data format conversion with timestamp column."""
        mock_backtest_instance = Mock()
        mock_backtest.return_value = mock_backtest_instance

        engine = BacktestingPyEngine()

        # Test with timestamp column
        dates = ["2023-01-01", "2023-01-02", "2023-01-03"]
        data = pd.DataFrame(
            {
                "timestamp": dates,
                "open": [100, 101, 102],
                "high": [102, 103, 104],
                "low": [99, 100, 101],
                "close": [101, 102, 103],
                "volume": [1000, 1100, 1200],
            }
        )

        result = engine._convert_data_format(data)

        assert isinstance(result.index, pd.DatetimeIndex)
        assert "timestamp" not in result.columns
        assert len(result) == 3

    @patch("quantchain.backtesting.backtestingpy_engine._BACKTESTING_AVAILABLE", True)
    @patch("quantchain.backtesting.backtestingpy_engine.Backtest")
    @patch("quantchain.backtesting.backtestingpy_engine.Strategy")
    def test_convert_data_format_date_index(self, mock_strategy, mock_backtest):
        """Test data format conversion with date column."""
        mock_backtest_instance = Mock()
        mock_backtest.return_value = mock_backtest_instance

        engine = BacktestingPyEngine()

        # Test with date column
        dates = ["2023-01-01", "2023-01-02", "2023-01-03"]
        data = pd.DataFrame(
            {
                "date": dates,
                "open": [100, 101, 102],
                "high": [102, 103, 104],
                "low": [99, 100, 101],
                "close": [101, 102, 103],
                "volume": [1000, 1100, 1200],
            }
        )

        result = engine._convert_data_format(data)

        assert isinstance(result.index, pd.DatetimeIndex)
        assert "date" not in result.columns
        assert len(result) == 3

    @patch("quantchain.backtesting.backtestingpy_engine._BACKTESTING_AVAILABLE", True)
    @patch("quantchain.backtesting.backtestingpy_engine.Backtest")
    @patch("quantchain.backtesting.backtestingpy_engine.Strategy")
    def test_convert_data_format_default_dates(self, mock_strategy, mock_backtest):
        """Test data format conversion with default date generation."""
        mock_backtest_instance = Mock()
        mock_backtest.return_value = mock_backtest_instance

        engine = BacktestingPyEngine()

        # Test without date/timestamp columns
        data = pd.DataFrame(
            {
                "open": [100, 101, 102],
                "high": [102, 103, 104],
                "low": [99, 100, 101],
                "close": [101, 102, 103],
                "volume": [1000, 1100, 1200],
            }
        )

        result = engine._convert_data_format(data)

        assert isinstance(result.index, pd.DatetimeIndex)
        assert len(result) == 3
        # Should generate consecutive dates ending around now
        assert (result.index[1] - result.index[0]).days == 1

    @patch("quantchain.backtesting.backtestingpy_engine._BACKTESTING_AVAILABLE", True)
    @patch("quantchain.backtesting.backtestingpy_engine.Backtest")
    @patch("quantchain.backtesting.backtestingpy_engine.Strategy")
    def test_get_performance_metrics(self, mock_strategy, mock_backtest):
        """Test performance metrics extraction."""
        mock_backtest_instance = Mock()
        mock_backtest.return_value = mock_backtest_instance

        engine = BacktestingPyEngine()

        # Mock stats from backtesting.py
        stats = {
            "Return [%]": 15.5,
            "Return (Ann.) [%]": 12.3,
            "Sharpe Ratio": 1.45,
            "Sortino Ratio": 1.89,
            "Calmar Ratio": 0.95,
            "Max Drawdown [%]": -5.2,
            "Max Drawdown Duration": 45,
            "Win Rate [%]": 62.5,
            "Profit Factor": 1.8,
            "Recovery Factor": 2.1,
            "# Trades": 125,
            "Avg. Trade [%]": 0.12,
            "Avg. Winning Trade [%]": 2.5,
            "Avg. Losing Trade [%]": -1.8,
            "Best Trade [%]": 8.2,
            "Worst Trade [%]": -4.1,
            "Avg. Drawdown [%]": -1.2,
        }

        metrics = engine._get_performance_metrics(stats)

        assert isinstance(metrics, MetricsResult)
        assert metrics.total_return == pytest.approx(0.155)
        assert metrics.return_pct == 15.5
        assert metrics.annualized_return == pytest.approx(0.123)
        assert metrics.sharpe_ratio == pytest.approx(1.45)
        assert metrics.sortino_ratio == pytest.approx(1.89)
        assert metrics.calmar_ratio == pytest.approx(0.95)
        assert metrics.max_drawdown == pytest.approx(-0.052)
        assert metrics.max_drawdown_pct == -5.2
        assert metrics.max_drawdown_duration == 45
        assert metrics.win_rate == pytest.approx(0.625)
        assert metrics.win_rate_pct == 62.5
        assert metrics.profit_factor == pytest.approx(1.8)
        assert metrics.recovery_factor == pytest.approx(2.1)
        assert metrics.total_trades == 125
        assert metrics.avg_trade == pytest.approx(0.0012)
        assert metrics.avg_win_pct == 2.5
        assert metrics.avg_loss_pct == -1.8
        assert metrics.largest_win == pytest.approx(0.082)
        assert metrics.largest_loss == pytest.approx(-0.041)
        assert metrics.avg_drawdown == pytest.approx(-0.012)
        assert metrics.avg_drawdown_pct == -1.2

    @patch("quantchain.backtesting.backtestingpy_engine._BACKTESTING_AVAILABLE", True)
    @patch("quantchain.backtesting.backtestingpy_engine.Backtest")
    @patch("quantchain.backtesting.backtestingpy_engine.Strategy")
    def test_get_performance_metrics_missing_values(self, mock_strategy, mock_backtest):
        """Test performance metrics extraction with missing values."""
        mock_backtest_instance = Mock()
        mock_backtest.return_value = mock_backtest_instance

        engine = BacktestingPyEngine()

        # Test with missing/empty stats
        stats = {}

        metrics = engine._get_performance_metrics(stats)

        # Should default to 0 for missing values
        assert metrics.total_return == 0.0
        assert metrics.sharpe_ratio == 0.0
        assert metrics.total_trades == 0

    @patch("quantchain.backtesting.backtestingpy_engine._BACKTESTING_AVAILABLE", True)
    @patch("quantchain.backtesting.backtestingpy_engine.Backtest")
    @patch("quantchain.backtesting.backtestingpy_engine.Strategy")
    def test_analyze_portfolio_composition(self, mock_strategy, mock_backtest):
        """Test portfolio composition analysis."""
        mock_backtest_instance = Mock()
        mock_backtest.return_value = mock_backtest_instance

        engine = BacktestingPyEngine()

        # Test with portfolio data
        portfolio = {"AAPL": 5000, "GOOGL": 3000, "MSFT": 2000}

        composition = engine._analyze_portfolio_composition(portfolio)

        expected_composition = {
            "AAPL": 50.0,  # 5000/10000 * 100
            "GOOGL": 30.0,  # 3000/10000 * 100
            "MSFT": 20.0,  # 2000/10000 * 100
        }
        assert composition == expected_composition

    @patch("quantchain.backtesting.backtestingpy_engine._BACKTESTING_AVAILABLE", True)
    @patch("quantchain.backtesting.backtestingpy_engine.Backtest")
    @patch("quantchain.backtesting.backtestingpy_engine.Strategy")
    def test_analyze_portfolio_composition_empty(self, mock_strategy, mock_backtest):
        """Test portfolio composition analysis with empty portfolio."""
        mock_backtest_instance = Mock()
        mock_backtest.return_value = mock_backtest_instance

        engine = BacktestingPyEngine()

        # Test with empty portfolio
        portfolio = {}

        composition = engine._analyze_portfolio_composition(portfolio)

        assert composition == {}

    @patch("quantchain.backtesting.backtestingpy_engine._BACKTESTING_AVAILABLE", True)
    @patch("quantchain.backtesting.backtestingpy_engine.Backtest")
    @patch("quantchain.backtesting.backtestingpy_engine.Strategy")
    def test_calculate_risk_metrics(self, mock_strategy, mock_backtest):
        """Test risk metrics calculation."""
        mock_backtest_instance = Mock()
        mock_backtest.return_value = mock_backtest_instance

        engine = BacktestingPyEngine()

        # Create sample returns data
        returns = pd.Series([0.01, -0.005, 0.02, -0.01, 0.015, -0.008])

        risk_metrics = engine._calculate_risk_metrics(returns)

        assert isinstance(risk_metrics, dict)
        assert "volatility" in risk_metrics
        assert "var_95" in risk_metrics
        assert "var_99" in risk_metrics
        assert "skewness" in risk_metrics
        assert "kurtosis" in risk_metrics

        # Check that values are reasonable
        assert risk_metrics["volatility"] > 0
        assert isinstance(risk_metrics["var_95"], float)
        assert isinstance(risk_metrics["var_99"], float)

    @patch("quantchain.backtesting.backtestingpy_engine._BACKTESTING_AVAILABLE", True)
    @patch("quantchain.backtesting.backtestingpy_engine.Backtest")
    @patch("quantchain.backtesting.backtestingpy_engine.Strategy")
    def test_calculate_risk_metrics_empty(self, mock_strategy, mock_backtest):
        """Test risk metrics calculation with empty returns."""
        mock_backtest_instance = Mock()
        mock_backtest.return_value = mock_backtest_instance

        engine = BacktestingPyEngine()

        # Test with empty returns
        returns = pd.Series([], dtype=float)

        risk_metrics = engine._calculate_risk_metrics(returns)

        expected_metrics = {
            "volatility": 0.0,
            "var_95": 0.0,
            "var_99": 0.0,
            "skewness": 0.0,
            "kurtosis": 0.0,
        }
        assert risk_metrics == expected_metrics

    @patch("quantchain.backtesting.backtestingpy_engine._BACKTESTING_AVAILABLE", True)
    @patch("quantchain.backtesting.backtestingpy_engine.Backtest")
    @patch("quantchain.backtesting.backtestingpy_engine.Strategy")
    def test_calculate_risk_metrics_with_nan(self, mock_strategy, mock_backtest):
        """Test risk metrics calculation with NaN values."""
        mock_backtest_instance = Mock()
        mock_backtest.return_value = mock_backtest_instance

        engine = BacktestingPyEngine()

        # Test with NaN values
        returns = pd.Series([0.01, np.nan, 0.02, -0.01, np.nan, -0.008])

        risk_metrics = engine._calculate_risk_metrics(returns)

        # Should handle NaN values by dropping them
        assert isinstance(risk_metrics, dict)
        assert risk_metrics["volatility"] > 0

    @patch("quantchain.backtesting.backtestingpy_engine._BACKTESTING_AVAILABLE", True)
    @patch("quantchain.backtesting.backtestingpy_engine.Backtest")
    @patch("quantchain.backtesting.backtestingpy_engine.Strategy")
    def test_run_backtest_success(self, mock_strategy, mock_backtest):
        """Test successful backtest execution."""
        mock_backtest_instance = Mock()
        mock_backtest.return_value = mock_backtest_instance

        # Mock the run method
        mock_stats = {
            "Return [%]": 10.5,
            "Sharpe Ratio": 1.2,
            "Max Drawdown [%]": -3.5,
            "Win Rate [%]": 58.0,
            "# Trades": 50,
        }
        mock_backtest_instance.run.return_value = mock_stats

        # Mock equity curve and trades
        mock_equity_curve = pd.DataFrame({"equity": [100000, 105000, 110000]})
        mock_trades = pd.DataFrame({"entry_time": [], "exit_time": []})
        mock_backtest_instance._equity_curve = mock_equity_curve
        mock_backtest_instance._trades = mock_trades

        engine = BacktestingPyEngine()

        # Create test data
        data = pd.DataFrame(
            {
                "open": [100, 101, 102],
                "high": [102, 103, 104],
                "low": [99, 100, 101],
                "close": [101, 102, 103],
                "volume": [1000, 1100, 1200],
            }
        )

        # Create mock strategy
        mock_strategy_instance = Mock()
        mock_strategy_instance.init = Mock()
        mock_strategy_instance.next = Mock()

        with patch(
            "quantchain.backtesting.backtestingpy_engine.Backtest"
        ) as mock_backtest_class:
            mock_backtest_class.return_value = mock_backtest_instance

            result = engine.run_backtest(data, mock_strategy_instance)

            assert isinstance(result, BacktestResult)
            assert result.equity_curve.equals(mock_equity_curve)
            assert result.trade_log.equals(mock_trades)
            assert result.summary_stats == mock_stats
            assert isinstance(result.metrics, MetricsResult)
            assert result.execution_time > 0
            assert result.config == engine.config

    @patch("quantchain.backtesting.backtestingpy_engine._BACKTESTING_AVAILABLE", True)
    @patch("quantchain.backtesting.backtestingpy_engine.Backtest")
    @patch("quantchain.backtesting.backtestingpy_engine.Strategy")
    def test_run_backtest_data_conversion_error(self, mock_strategy, mock_backtest):
        """Test backtest execution with data conversion error."""
        mock_backtest_instance = Mock()
        mock_backtest.return_value = mock_backtest_instance

        engine = BacktestingPyEngine()

        # Create invalid data (missing columns)
        data = pd.DataFrame(
            {
                "open": [100, 101, 102],
                "close": [101, 102, 103],
                # Missing high, low, volume
            }
        )

        mock_strategy_instance = Mock()

        with pytest.raises(ValueError, match="Failed to convert data format"):
            engine.run_backtest(data, mock_strategy_instance)

    @patch("quantchain.backtesting.backtestingpy_engine._BACKTESTING_AVAILABLE", True)
    @patch("quantchain.backtesting.backtestingpy_engine.Backtest")
    @patch("quantchain.backtesting.backtestingpy_engine.Strategy")
    def test_run_backtest_strategy_missing_methods(self, mock_strategy, mock_backtest):
        """Test backtest execution with strategy missing required methods."""
        mock_backtest_instance = Mock()
        mock_backtest.return_value = mock_backtest_instance

        engine = BacktestingPyEngine()

        # Create valid data
        data = pd.DataFrame(
            {
                "open": [100, 101, 102],
                "high": [102, 103, 104],
                "low": [99, 100, 101],
                "close": [101, 102, 103],
                "volume": [1000, 1100, 1200],
            }
        )

        # Create strategy missing required methods
        mock_strategy_instance = Mock()
        del mock_strategy_instance.init  # Remove required method

        with pytest.raises(AttributeError, match="Strategy must have 'init' method"):
            engine.run_backtest(data, mock_strategy_instance)

    @patch("quantchain.backtesting.backtestingpy_engine._BACKTESTING_AVAILABLE", True)
    @patch("quantchain.backtesting.backtestingpy_engine.Backtest")
    @patch("quantchain.backtesting.backtestingpy_engine.Strategy")
    def test_run_backtest_execution_error(self, mock_strategy, mock_backtest):
        """Test backtest execution with runtime error."""
        mock_backtest_instance = Mock()
        mock_backtest.return_value = mock_backtest_instance
        mock_backtest_instance.run.side_effect = Exception("Backtest execution failed")

        engine = BacktestingPyEngine()

        # Create valid data
        data = pd.DataFrame(
            {
                "open": [100, 101, 102],
                "high": [102, 103, 104],
                "low": [99, 100, 101],
                "close": [101, 102, 103],
                "volume": [1000, 1100, 1200],
            }
        )

        # Create valid strategy
        mock_strategy_instance = Mock()
        mock_strategy_instance.init = Mock()
        mock_strategy_instance.next = Mock()

        with pytest.raises(RuntimeError, match="Backtest execution failed"):
            engine.run_backtest(data, mock_strategy_instance)

    @patch("quantchain.backtesting.backtestingpy_engine._BACKTESTING_AVAILABLE", True)
    @patch("quantchain.backtesting.backtestingpy_engine.Backtest")
    @patch("quantchain.backtesting.backtestingpy_engine.Strategy")
    def test_get_results_none_initially(self, mock_strategy, mock_backtest):
        """Test getting results before running backtest."""
        mock_backtest_instance = Mock()
        mock_backtest.return_value = mock_backtest_instance

        engine = BacktestingPyEngine()

        results = engine.get_results()

        assert results is None

    @patch("quantchain.backtesting.backtestingpy_engine._BACKTESTING_AVAILABLE", True)
    @patch("quantchain.backtesting.backtestingpy_engine.Backtest")
    @patch("quantchain.backtesting.backtestingpy_engine.Strategy")
    def test_get_results_after_run(self, mock_strategy, mock_backtest):
        """Test getting results after running backtest."""
        mock_backtest_instance = Mock()
        mock_backtest.return_value = mock_backtest_instance

        # Mock backtest execution
        mock_stats = {"Return [%]": 10.5}
        mock_backtest_instance.run.return_value = mock_stats
        mock_backtest_instance._equity_curve = pd.DataFrame()
        mock_backtest_instance._trades = pd.DataFrame()

        engine = BacktestingPyEngine()

        # Create test data and strategy
        data = pd.DataFrame(
            {
                "open": [100, 101, 102],
                "high": [102, 103, 104],
                "low": [99, 100, 101],
                "close": [101, 102, 103],
                "volume": [1000, 1100, 1200],
            }
        )

        mock_strategy_instance = Mock()
        mock_strategy_instance.init = Mock()
        mock_strategy_instance.next = Mock()

        with patch(
            "quantchain.backtesting.backtestingpy_engine.Backtest"
        ) as mock_backtest_class:
            mock_backtest_class.return_value = mock_backtest_instance

            # Run backtest
            result = engine.run_backtest(data, mock_strategy_instance)

            # Store the result in engine
            engine._results = result

            # Get results
            results = engine.get_results()

            assert results is not None
            assert results == result

    @patch("quantchain.backtesting.backtestingpy_engine._BACKTESTING_AVAILABLE", True)
    @patch("quantchain.backtesting.backtestingpy_engine.Backtest")
    @patch("quantchain.backtesting.backtestingpy_engine.Strategy")
    def test_get_equity_curve_none_initially(self, mock_strategy, mock_backtest):
        """Test getting equity curve before running backtest."""
        mock_backtest_instance = Mock()
        mock_backtest.return_value = mock_backtest_instance

        engine = BacktestingPyEngine()

        equity_curve = engine.get_equity_curve()

        assert equity_curve is None

    @patch("quantchain.backtesting.backtestingpy_engine._BACKTESTING_AVAILABLE", True)
    @patch("quantchain.backtesting.backtestingpy_engine.Backtest")
    @patch("quantchain.backtesting.backtestingpy_engine.Strategy")
    def test_get_equity_curve_after_run(self, mock_strategy, mock_backtest):
        """Test getting equity curve after running backtest."""
        mock_backtest_instance = Mock()
        mock_backtest.return_value = mock_backtest_instance

        engine = BacktestingPyEngine()

        # Create mock equity curve
        mock_equity_curve = pd.Series([100000, 105000, 110000])
        engine._equity_curve_data = mock_equity_curve

        equity_curve = engine.get_equity_curve()

        assert equity_curve is not None
        assert equity_curve.equals(mock_equity_curve)


@pytest.mark.unit
class TestBacktestingPyEngineIntegration:
    """Integration tests for BacktestingPyEngine."""

    @patch("quantchain.backtesting.backtestingpy_engine._BACKTESTING_AVAILABLE", True)
    @patch("quantchain.backtesting.backtestingpy_engine.Backtest")
    @patch("quantchain.backtesting.backtestingpy_engine.Strategy")
    def test_full_workflow(self, mock_strategy, mock_backtest):
        """Test complete backtesting workflow."""
        mock_backtest_instance = Mock()
        mock_backtest.return_value = mock_backtest_instance

        # Mock complete backtest execution
        mock_stats = {
            "Return [%]": 15.5,
            "Sharpe Ratio": 1.45,
            "Max Drawdown [%]": -5.2,
            "Win Rate [%]": 62.5,
            "# Trades": 125,
        }
        mock_backtest_instance.run.return_value = mock_stats
        mock_equity_curve = pd.DataFrame({"equity": [100000, 105000, 110000, 115500]})
        mock_trades = pd.DataFrame({"entry_time": [1, 2], "exit_time": [3, 4]})
        mock_backtest_instance._equity_curve = mock_equity_curve
        mock_backtest_instance._trades = mock_trades

        # Create engine with custom config
        config = BacktestConfig(
            initial_capital=200000, commission=0.002, slippage=0.001
        )
        engine = BacktestingPyEngine(config)

        # Create test data
        data = pd.DataFrame(
            {
                "open": [100, 101, 102, 103],
                "high": [102, 103, 104, 105],
                "low": [99, 100, 101, 102],
                "close": [101, 102, 103, 104],
                "volume": [1000, 1100, 1200, 1300],
            }
        )

        # Create mock strategy
        mock_strategy_instance = Mock()
        mock_strategy_instance.init = Mock()
        mock_strategy_instance.next = Mock()

        with patch(
            "quantchain.backtesting.backtestingpy_engine.Backtest"
        ) as mock_backtest_class:
            mock_backtest_class.return_value = mock_backtest_instance

            # Run backtest
            result = engine.run_backtest(data, mock_strategy_instance)

            # Verify results
            assert isinstance(result, BacktestResult)
            assert result.config == config
            assert result.metrics.total_return == 0.155
            assert result.metrics.sharpe_ratio == 1.45
            assert result.metrics.total_trades == 125

            # Test getting stored results
            engine._results = result
            stored_results = engine.get_results()
            assert stored_results == result

            # Test equity curve
            engine._equity_curve_data = mock_equity_curve["equity"]
            equity_curve = engine.get_equity_curve()
            assert equity_curve is not None


@pytest.mark.unit
class TestEdgeCases:
    """Test edge cases and error conditions."""

    @patch("quantchain.backtesting.backtestingpy_engine._BACKTESTING_AVAILABLE", True)
    @patch("quantchain.backtesting.backtestingpy_engine.Backtest")
    @patch("quantchain.backtesting.backtestingpy_engine.Strategy")
    def test_convert_data_format_copy(self, mock_strategy, mock_backtest):
        """Test that data conversion doesn't modify original DataFrame."""
        mock_backtest_instance = Mock()
        mock_backtest.return_value = mock_backtest_instance

        engine = BacktestingPyEngine()

        # Create original data
        original_data = pd.DataFrame(
            {
                "open": [100, 101],
                "high": [102, 103],
                "low": [99, 100],
                "close": [101, 102],
                "volume": [1000, 1100],
            }
        )

        # Convert data
        converted_data = engine._convert_data_format(original_data)

        # Verify original data is unchanged
        assert list(original_data.columns) == ["open", "high", "low", "close", "volume"]
        assert not isinstance(original_data.index, pd.DatetimeIndex)

        # Verify converted data is different
        assert list(converted_data.columns) == [
            "Open",
            "High",
            "Low",
            "Close",
            "Volume",
        ]

    @patch("quantchain.backtesting.backtestingpy_engine._BACKTESTING_AVAILABLE", True)
    @patch("quantchain.backtesting.backtestingpy_engine.Backtest")
    @patch("quantchain.backtesting.backtestingpy_engine.Strategy")
    def test_large_dataset_handling(self, mock_strategy, mock_backtest):
        """Test handling of large datasets."""
        mock_backtest_instance = Mock()
        mock_backtest.return_value = mock_backtest_instance

        engine = BacktestingPyEngine()

        # Create large dataset (1000 rows)
        n_rows = 1000
        data = pd.DataFrame(
            {
                "open": np.random.uniform(100, 200, n_rows),
                "high": np.random.uniform(200, 300, n_rows),
                "low": np.random.uniform(50, 100, n_rows),
                "close": np.random.uniform(100, 200, n_rows),
                "volume": np.random.randint(1000, 10000, n_rows),
            }
        )

        # Should handle large datasets without issues
        result = engine._convert_data_format(data)
        assert len(result) == n_rows
        assert isinstance(result.index, pd.DatetimeIndex)

    @patch("quantchain.backtesting.backtestingpy_engine._BACKTESTING_AVAILABLE", True)
    @patch("quantchain.backtesting.backtestingpy_engine.Backtest")
    @patch("quantchain.backtesting.backtestingpy_engine.Strategy")
    def test_single_row_data(self, mock_strategy, mock_backtest):
        """Test handling of single row data."""
        mock_backtest_instance = Mock()
        mock_backtest.return_value = mock_backtest_instance

        engine = BacktestingPyEngine()

        # Create single row data
        data = pd.DataFrame(
            {
                "open": [100],
                "high": [102],
                "low": [99],
                "close": [101],
                "volume": [1000],
            }
        )

        result = engine._convert_data_format(data)
        assert len(result) == 1
        assert isinstance(result.index, pd.DatetimeIndex)

    @patch("quantchain.backtesting.backtestingpy_engine._BACKTESTING_AVAILABLE", True)
    @patch("quantchain.backtesting.backtestingpy_engine.Backtest")
    @patch("quantchain.backtesting.backtestingpy_engine.Strategy")
    def test_extreme_values_in_data(self, mock_strategy, mock_backtest):
        """Test handling of extreme values in data."""
        mock_backtest_instance = Mock()
        mock_backtest.return_value = mock_backtest_instance

        engine = BacktestingPyEngine()

        # Create data with extreme values
        data = pd.DataFrame(
            {
                "open": [1e-10, 1e10],
                "high": [1e-10, 1e10],
                "low": [1e-10, 1e10],
                "close": [1e-10, 1e10],
                "volume": [1e-10, 1e10],
            }
        )

        # Should handle extreme values
        result = engine._convert_data_format(data)
        assert len(result) == 2
        assert not result.isnull().any().any()
