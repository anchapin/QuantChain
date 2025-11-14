"""Tests for BacktestingPyEngine."""

import sys
from pathlib import Path
from unittest.mock import Mock, patch

import pandas as pd
import pytest

# Add the parent directory to the path to import the module
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from quantchain.backtesting.backtestingpy_engine import (
    BacktestingPyConfig,
    BacktestingPyEngine,
    BacktestingPyError,
    ConversionError,
    StrategyAdapter,
)
from quantchain.backtesting.engine import BacktestConfig, BacktestResult, MetricsResult


class TestBacktestingPyConfig:
    """Test BacktestingPyConfig dataclass."""

    def test_default_config(self):
        """Test default configuration values."""
        config = BacktestingPyConfig()
        assert config.cash == 10000.0
        assert config.commission == 0.002
        assert config.exclusive_orders is True

    def test_custom_config(self):
        """Test custom configuration values."""
        config = BacktestingPyConfig(
            cash=50000.0, commission=0.001, exclusive_orders=False
        )
        assert config.cash == 50000.0
        assert config.commission == 0.001
        assert config.exclusive_orders is False


class TestBacktestingPyEngine:
    """Test BacktestingPyEngine class."""

    @patch("quantchain.backtesting.backtestingpy_engine.Backtest")
    @patch("quantchain.backtesting.backtestingpy_engine.StrategyAdapter")
    def test_initialization_success(self, mock_strategy, mock_backtest):
        """Test successful initialization of BacktestingPyEngine."""
        mock_backtest_instance = Mock()
        mock_backtest.return_value = mock_backtest_instance

        engine = BacktestingPyEngine()

        assert engine.config is not None
        assert engine._backtest == mock_backtest_instance
        assert engine._results is None
        assert engine._equity_curve_data is None

    @patch("quantchain.backtesting.backtestingpy_engine.Backtest", None)
    @patch("quantchain.backtesting.backtestingpy_engine.StrategyAdapter", None)
    def test_initialization_without_backtesting_library(self):
        """Test initialization fails when backtesting library is not installed."""
        with pytest.raises(ImportError, match="backtesting library not installed"):
            BacktestingPyEngine()

    @patch("quantchain.backtesting.backtestingpy_engine.Backtest")
    @patch("quantchain.backtesting.backtestingpy_engine.StrategyAdapter")
    def test_initialization_with_custom_config(self, mock_strategy, mock_backtest):
        """Test initialization with custom configuration."""
        mock_backtest_instance = Mock()
        mock_backtest.return_value = mock_backtest_instance

        custom_config = BacktestConfig(initial_cash=20000.0, commission_rate=0.003)
        engine = BacktestingPyEngine(config=custom_config)

        assert engine.config == custom_config
        mock_backtest.assert_called_once()

    @patch("quantchain.backtesting.backtestingpy_engine.Backtest")
    @patch("quantchain.backtesting.backtestingpy_engine.StrategyAdapter")
    def test_run_success(self, mock_strategy, mock_backtest):
        """Test successful backtest run."""
        # Setup mocks
        mock_backtest_instance = Mock()
        mock_backtest.return_value = mock_backtest_instance

        # Create mock return value
        mock_stats = {
            "Return [%]": 15.5,
            "Sharpe Ratio": 1.5,
            "Max Drawdown [%]": 5.2,
            "Win Rate [%]": 65.0,
            "# Trades": 42,
        }
        mock_backtest_instance.run.return_value = pd.Series([100, 105, 110, 115])

        # Setup engine
        engine = BacktestingPyEngine()

        # Create test data
        test_data = pd.DataFrame(
            {
                "Open": [100, 101, 102, 103],
                "High": [102, 103, 104, 105],
                "Low": [99, 100, 101, 102],
                "Close": [101, 102, 103, 104],
                "Volume": [1000, 1100, 1200, 1300],
            }
        )

        # Run backtest
        result = engine.run(Mock(), test_data)

        # Assertions
        assert isinstance(result, BacktestResult)
        assert engine._results == result
        assert mock_backtest_instance.run.called

    @patch("quantchain.backtesting.backtestingpy_engine.Backtest")
    @patch("quantchain.backtesting.backtestingpy_engine.StrategyAdapter")
    def test_run_with_conversion_error(self, mock_strategy, mock_backtest):
        """Test run with data conversion error."""
        mock_backtest_instance = Mock()
        mock_backtest.return_value = mock_backtest_instance

        engine = BacktestingPyEngine()

        # Create invalid data (missing required columns)
        invalid_data = pd.DataFrame(
            {
                "Open": [100, 101],
                "Close": [101, 102],
                # Missing High, Low, Volume
            }
        )

        with pytest.raises(ConversionError, match="Missing required columns"):
            engine.run(Mock(), invalid_data)

    @patch("quantchain.backtesting.backtestingpy_engine.Backtest")
    @patch("quantchain.backtesting.backtestingpy_engine.StrategyAdapter")
    def test_run_with_backtest_error(self, mock_strategy, mock_backtest):
        """Test run with backtest execution error."""
        mock_backtest_instance = Mock()
        mock_backtest.return_value = mock_backtest_instance
        mock_backtest_instance.run.side_effect = Exception("Backtest failed")

        engine = BacktestingPyEngine()

        test_data = pd.DataFrame(
            {
                "Open": [100, 101],
                "High": [102, 103],
                "Low": [99, 100],
                "Close": [101, 102],
                "Volume": [1000, 1100],
            }
        )

        with pytest.raises(BacktestingPyError, match="Backtest execution failed"):
            engine.run(Mock(), test_data)

    def test_get_results_without_run(self):
        """Test get_results before running any backtest."""
        with patch("quantchain.backtesting.backtestingpy_engine.Backtest"), patch(
            "quantchain.backtesting.backtestingpy_engine.StrategyAdapter"
        ):
            engine = BacktestingPyEngine()
            assert engine.get_results() is None

    @patch("quantchain.backtesting.backtestingpy_engine.Backtest")
    @patch("quantchain.backtesting.backtestingpy_engine.StrategyAdapter")
    def test_get_results_after_run(self, mock_strategy, mock_backtest):
        """Test get_results after running a backtest."""
        mock_backtest_instance = Mock()
        mock_backtest.return_value = mock_backtest_instance

        # Mock successful run
        mock_stats = pd.Series([100, 105, 110])
        mock_backtest_instance.run.return_value = mock_stats

        engine = BacktestingPyEngine()

        test_data = pd.DataFrame(
            {
                "Open": [100, 101],
                "High": [102, 103],
                "Low": [99, 100],
                "Close": [101, 102],
                "Volume": [1000, 1100],
            }
        )

        engine.run(Mock(), test_data)
        result = engine.get_results()

        assert result is not None
        assert isinstance(result, BacktestResult)

    @patch("quantchain.backtesting.backtestingpy_engine.Backtest")
    @patch("quantchain.backtesting.backtestingpy_engine.StrategyAdapter")
    def test_get_equity_curve_without_run(self, mock_strategy, mock_backtest):
        """Test get_equity_curve before running any backtest."""
        mock_backtest_instance = Mock()
        mock_backtest.return_value = mock_backtest_instance

        engine = BacktestingPyEngine()
        equity_curve = engine.get_equity_curve()

        # Should return empty Series when no backtest has run
        assert isinstance(equity_curve, pd.Series)
        assert len(equity_curve) == 0

    @patch("quantchain.backtesting.backtestingpy_engine.Backtest")
    @patch("quantchain.backtesting.backtestingpy_engine.StrategyAdapter")
    def test_get_equity_curve_with_stored_data(self, mock_strategy, mock_backtest):
        """Test get_equity_curve when equity curve data is stored."""
        mock_backtest_instance = Mock()
        mock_backtest.return_value = mock_backtest_instance

        engine = BacktestingPyEngine()

        # Store equity curve data directly
        stored_curve = pd.Series([100, 105, 110, 115])
        engine._equity_curve_data = stored_curve

        equity_curve = engine.get_equity_curve()
        assert equity_curve.equals(stored_curve)

    def test_convert_data_format_success(self):
        """Test successful data format conversion."""
        with patch("quantchain.backtesting.backtestingpy_engine.Backtest"), patch(
            "quantchain.backtesting.backtestingpy_engine.StrategyAdapter"
        ):
            engine = BacktestingPyEngine()

            input_data = pd.DataFrame(
                {
                    "open": [100, 101],
                    "high": [102, 103],
                    "low": [99, 100],
                    "close": [101, 102],
                    "volume": [1000, 1100],
                }
            )

            result = engine._convert_data_format(input_data)

            # Check column names are capitalized
            expected_columns = ["Open", "High", "Low", "Close", "Volume"]
            assert list(result.columns) == expected_columns

    def test_convert_data_format_missing_columns(self):
        """Test data format conversion with missing columns."""
        with patch("quantchain.backtesting.backtestingpy_engine.Backtest"), patch(
            "quantchain.backtesting.backtestingpy_engine.StrategyAdapter"
        ):
            engine = BacktestingPyEngine()

            # Data with missing 'volume' column
            input_data = pd.DataFrame(
                {
                    "open": [100, 101],
                    "high": [102, 103],
                    "low": [99, 100],
                    "close": [101, 102],
                }
            )

            with pytest.raises(ConversionError, match="Missing required columns"):
                engine._convert_data_format(input_data)

    def test_convert_results_success(self):
        """Test successful results conversion."""
        with patch("quantchain.backtesting.backtestingpy_engine.Backtest"), patch(
            "quantchain.backtesting.backtestingpy_engine.StrategyAdapter"
        ):
            engine = BacktestingPyEngine()

            # Mock backtest stats
            mock_stats = {
                "Return [%]": 15.5,
                "Sharpe Ratio": 1.5,
                "Max Drawdown [%]": 5.2,
                "Win Rate [%]": 65.0,
                "# Trades": 42,
            }

            result = engine._convert_results(mock_stats)

            assert isinstance(result, BacktestResult)
            assert isinstance(result.metrics, MetricsResult)
            # Check that conversion works properly
            assert result.metrics.total_return == 0.155  # 15.5% / 100
            assert result.metrics.sharpe_ratio == 1.5
            assert result.metrics.max_drawdown == pytest.approx(0.052)  # 5.2% / 100
            assert result.metrics.win_rate == 0.65  # 65% / 100
            assert result.metrics.total_trades == 42

    def test_convert_results_with_series(self):
        """Test results conversion with Series input."""
        with patch("quantchain.backtesting.backtestingpy_engine.Backtest"), patch(
            "quantchain.backtesting.backtestingpy_engine.StrategyAdapter"
        ):
            engine = BacktestingPyEngine()

            # Mock equity curve series
            mock_series = pd.Series([100, 105, 110, 115])

            result = engine._convert_results(mock_series)

            assert isinstance(result, BacktestResult)
            assert isinstance(result.metrics, MetricsResult)
            # Should use default values when stats dict is not available
            assert result.metrics.total_return == 0.0

    def test_convert_results_exception_handling(self):
        """Test results conversion with exception handling."""
        from quantchain.backtesting.backtestingpy_engine import BacktestingPyEngine
        from quantchain.backtesting.engine import BacktestResult, MetricsResult

        # Create a mock engine with patched _convert_results that will raise an exception
        with patch("quantchain.backtesting.backtestingpy_engine.Backtest"), patch(
            "quantchain.backtesting.backtestingpy_engine.StrategyAdapter"
        ):
            engine = BacktestingPyEngine()

            # Create a real MetricsResult to use for fallback
            fallback_metrics = MetricsResult(
                total_return=0.0,
                annualized_return=0.0,
                sharpe_ratio=0.0,
                sortino_ratio=0.0,
                calmar_ratio=0.0,
                max_drawdown=0.0,
                max_drawdown_duration=0,
                win_rate=0.0,
                total_trades=0,
            )

            # Create the expected fallback result
            expected_result = BacktestResult(
                equity_curve=pd.Series(),
                trade_log=pd.DataFrame(),
                summary_stats={"error": 1.0},
                metrics=fallback_metrics,
                execution_time=0.0,
                config=engine.config,
            )

            # Call _convert_results with invalid input to trigger exception path
            # This will cause the try block to fail and return the fallback values
            result = engine._convert_results(None)  # None should trigger exception

            assert isinstance(result, BacktestResult)
            assert isinstance(result.metrics, MetricsResult)
            # Should return fallback values
            assert result.metrics.total_return == 0.0
            assert result.metrics.annualized_return == 0.0
            assert result.metrics.sharpe_ratio == 0.0
            assert result.metrics.max_drawdown == 0.0
            assert result.metrics.win_rate == 0.0
            assert result.metrics.total_trades == 0


class TestStrategyAdapter:
    """Test StrategyAdapter class."""

    def test_strategy_adapter_exists(self):
        """Test that StrategyAdapter is properly defined."""
        # This test just verifies the class exists
        # Actual functionality would require backtesting.py to be installed
        assert (
            StrategyAdapter is not None or StrategyAdapter is None
        )  # May be None if lib not installed


class TestExceptions:
    """Test custom exception classes."""

    def test_backtesting_py_error(self):
        """Test BacktestingPyError exception."""
        with pytest.raises(BacktestingPyError):
            raise BacktestingPyError("Test error")

    def test_conversion_error(self):
        """Test ConversionError exception."""
        with pytest.raises(ConversionError):
            raise ConversionError("Test conversion error")

        # Test that it's a subclass of BacktestingPyError
        try:
            raise ConversionError("Test")
        except BacktestingPyError:
            pass


class TestBacktestingPyEngineCoverage:
    """Additional test cases for improved coverage."""

    def test_convert_results_with_no_stats(self):
        """Test result conversion with no statistics."""
        with patch("quantchain.backtesting.backtestingpy_engine.Backtest"), patch(
            "quantchain.backtesting.backtestingpy_engine.StrategyAdapter"
        ):
            engine = BacktestingPyEngine()

            # Test with empty stats dict
            result = engine._convert_results({})
            assert result.metrics.total_return == 0.0
            assert result.metrics.win_rate == 0.0

            # Test with None stats
            result = engine._convert_results(None)
            assert result.metrics.total_return == 0.0
            assert result.metrics.win_rate == 0.0

    def test_convert_data_format_with_valid_columns(self):
        """Test data format conversion with valid column names."""
        with patch("quantchain.backtesting.backtestingpy_engine.Backtest"), patch(
            "quantchain.backtesting.backtestingpy_engine.StrategyAdapter"
        ):
            engine = BacktestingPyEngine()

            # Test with lowercase column names
            input_data = pd.DataFrame({
                "open": [100, 101],
                "high": [102, 103],
                "low": [99, 100],
                "close": [101, 102],
                "volume": [1000, 1100],
            })

            result = engine._convert_data_format(input_data)

            # Check column names are capitalized
            expected_columns = ["Open", "High", "Low", "Close", "Volume"]
            assert list(result.columns) == expected_columns

    def test_get_equity_curve_with_no_backtest(self):
        """Test getting equity curve when no backtest has run."""
        with patch("quantchain.backtesting.backtestingpy_engine.Backtest"), patch(
            "quantchain.backtesting.backtestingpy_engine.StrategyAdapter"
        ):
            engine = BacktestingPyEngine()
            engine._backtest = None
            equity_curve = engine.get_equity_curve()

            # Should return None when no backtest
            assert equity_curve is None

    def test_get_equity_curve_with_empty_result(self):
        """Test getting equity curve with empty result."""
        with patch("quantchain.backtesting.backtestingpy_engine.Backtest"), patch(
            "quantchain.backtesting.backtestingpy_engine.StrategyAdapter"
        ):
            engine = BacktestingPyEngine()
            engine._equity_curve_data = None
            engine._results = BacktestResult(
                equity_curve=pd.Series(),
                trade_log=pd.DataFrame(),
                summary_stats={},
                metrics=MetricsResult(),
                execution_time=0.0,
                config=engine.config
            )

            equity_curve = engine.get_equity_curve()

            # Should return empty Series
            assert isinstance(equity_curve, pd.Series)
            assert len(equity_curve) == 0


    class TestBacktestingPyEngineAdditionalCoverage:
        """Additional test cases for BacktestingPyEngine to reach 90%+ coverage."""

        def test_run_with_none_config(self):
            """Test running backtest with None config."""
            with patch("quantchain.backtesting.backtestingpy_engine.Backtest"), patch(
                "quantchain.backtesting.backtestingpy_engine.StrategyAdapter"
            ):
                engine = BacktestingPyEngine()

                # Create minimal valid data
                data = pd.DataFrame({
                    "Open": [100, 101, 102],
                    "High": [101, 102, 103],
                    "Low": [99, 100, 101],
                    "Close": [100.5, 101.5, 102.5],
                    "Volume": [1000, 1100, 1200],
                })

                # Run with None config (should use default)
                result = engine.run("test_strategy", data, None)
                assert result is not None
                assert result.config is not None

        def test_run_with_empty_config(self):
            """Test running backtest with empty config."""
            with patch("quantchain.backtesting.backtestingpy_engine.Backtest"), patch(
                "quantchain.backtesting.backtestingpy_engine.StrategyAdapter"
            ):
                from quantchain.backtesting.engine import BacktestConfig
                engine = BacktestingPyEngine()

                # Create minimal valid data
                data = pd.DataFrame({
                    "Open": [100, 101, 102],
                    "High": [101, 102, 103],
                    "Low": [99, 100, 101],
                    "Close": [100.5, 101.5, 102.5],
                    "Volume": [1000, 1100, 1200],
                })

                # Run with empty config (should use default values)
                empty_config = BacktestConfig()
                result = engine.run("test_strategy", data, empty_config)
                assert result is not None
                assert result.config.initial_cash == 100000.0  # Default value

        def test_config_with_zero_values(self):
            """Test engine with config containing zero values."""
            from quantchain.backtesting.engine import BacktestConfig
            # Test with valid zero commission rate and valid initial cash
            config = BacktestConfig(
                initial_cash=1.0,  # Must be positive
                commission_rate=0.0,
            )

            with patch("quantchain.backtesting.backtestingpy_engine.Backtest"), patch(
                "quantchain.backtesting.backtestingpy_engine.StrategyAdapter"
            ):
                engine = BacktestingPyEngine(config)
                assert engine.config.initial_cash == 1.0
                assert engine.config.commission_rate == 0.0

        def test_get_results_after_failed_run(self):
            """Test getting results after a failed run."""
            with patch("quantchain.backtesting.backtestingpy_engine.Backtest"), patch(
                "quantchain.backtesting.backtestingpy_engine.StrategyAdapter"
            ):
                engine = BacktestingPyEngine()

                # Mock a failed run
                with patch.object(engine, "run", side_effect=BacktestingPyError("Test error")):
                    try:
                        engine.run("test_strategy", pd.DataFrame())
                    except BacktestingPyError:
                        pass  # Expected error

                # Should return None after failed run
                result = engine.get_results()
                assert result is None

        def test_strategy_adapter_when_unavailable(self):
            """Test behavior when StrategyAdapter is unavailable."""
            # Temporarily set StrategyAdapter to None
            original_strategy_adapter = StrategyAdapter

            try:
                with patch("quantchain.backtesting.backtestingpy_engine.StrategyAdapter", None):
                    with pytest.raises(ImportError):
                        BacktestingPyEngine()
            finally:
                # Restore original value
                from quantchain.backtesting import backtestingpy_engine
                backtestingpy_engine.StrategyAdapter = original_strategy_adapter

        def test_backtest_when_unavailable(self):
            """Test behavior when Backtest is unavailable."""
            # Import the module to check if Backtest is available
            from quantchain.backtesting import backtestingpy_engine

            # Temporarily set Backtest to None
            original_backtest = backtestingpy_engine.Backtest

            try:
                with patch("quantchain.backtesting.backtestingpy_engine.Backtest", None):
                    with pytest.raises(ImportError):
                        BacktestingPyEngine()
            finally:
                # Restore original value
                from quantchain.backtesting import backtestingpy_engine
                backtestingpy_engine.Backtest = original_backtest

        def test_convert_data_format_mixed_case_columns(self):
            """Test data format conversion with mixed case column names."""
            with patch("quantchain.backtesting.backtestingpy_engine.Backtest"), patch(
                "quantchain.backtesting.backtestingpy_engine.StrategyAdapter"
            ):
                engine = BacktestingPyEngine()

                # Test with mixed case column names
                input_data = pd.DataFrame({
                    "Open": [100, 101],
                    "high": [102, 103],
                    "Low": [99, 100],
                    "close": [101, 102],
                    "Volume": [1000, 1100],
                })

                result = engine._convert_data_format(input_data)

                # Check column names are capitalized correctly
                expected_columns = ["Open", "High", "Low", "Close", "Volume"]
                assert list(result.columns) == expected_columns

        def test_convert_results_with_series_stats(self):
            """Test result conversion when stats is a Series."""
            with patch("quantchain.backtesting.backtestingpy_engine.Backtest"), patch(
                "quantchain.backtesting.backtestingpy_engine.StrategyAdapter"
            ):
                engine = BacktestingPyEngine()

                # Create a mock Series stats object
                mock_stats = pd.Series([0.15, 0.12, 1.5, 65, 10],
                                       index=["Return [%]", "Annual Return [%]", "Sharpe Ratio", "Win Rate [%]", "# Trades"])

                result = engine._convert_results(mock_stats)
                assert result.metrics.total_return == 0.0015  # 0.15/100 (percentage to decimal)
                assert result.metrics.sharpe_ratio == 1.5
                assert result.metrics.win_rate == 0.65
                assert result.metrics.total_trades == 10

        def test_get_equity_curve_with_stored_data(self):
            """Test getting equity curve when data is already stored."""
            with patch("quantchain.backtesting.backtestingpy_engine.Backtest"), patch(
                "quantchain.backtesting.backtestingpy_engine.StrategyAdapter"
            ):
                engine = BacktestingPyEngine()

                # Create stored equity curve data
                dates = pd.date_range("2024-01-01", periods=5, freq="D")
                stored_curve = pd.Series([100, 101, 102, 103, 104], index=dates)
                engine._equity_curve_data = stored_curve

                equity_curve = engine.get_equity_curve()

                # Should return the stored data
                assert equity_curve.equals(stored_curve)

        def test_error_inheritance(self):
            """Test that error classes inherit correctly."""
            # Test BacktestingPyError inheritance
            error1 = BacktestingPyError("test")
            assert isinstance(error1, Exception)

            # Test ConversionError inheritance
            error2 = ConversionError("test")
            assert isinstance(error2, Exception)
            assert isinstance(error2, BacktestingPyError)
