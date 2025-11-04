"""
Failing tests for Backtesting.py library integration.
Following TDD principles - these tests will fail initially.
"""

import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock

from quantchain.backtesting.backtestingpy_engine import (
    BacktestingPyEngine,
    StrategyAdapter,
    BacktestingPyError,
    ConversionError,
)
from quantchain.backtesting.engine import BacktestConfig, BacktestResult


@pytest.mark.requires_backtestingpy
@pytest.mark.unit
class TestBacktestingPyEngine:
    """Test BacktestingPyEngine class."""

    def test_engine_initialization(self, default_backtest_config):
        """Test BacktestingPyEngine can be initialized with configuration."""
        # Patch Backtesting.py imports
        with patch(
            "quantchain.backtesting.backtestingpy_engine.Backtest"
        ) as mock_backtest:
            engine = BacktestingPyEngine(default_backtest_config)

            assert engine.config == default_backtest_config
            mock_backtest.assert_called_once()

    def test_engine_initialization_default_config(self):
        """Test BacktestingPyEngine can be initialized with default config."""
        from quantchain.backtesting.engine import BacktestConfig

        with patch(
            "quantchain.backtesting.backtestingpy_engine.Backtest"
        ) as mock_backtest:
            engine = BacktestingPyEngine()

            assert isinstance(engine.config, BacktestConfig)
            mock_backtest.assert_called_once()

    def test_engine_run_with_strategy(self, sample_ohlcv_data, default_backtest_config):
        """Test engine can run a backtest with strategy."""
        with patch(
            "quantchain.backtesting.backtestingpy_engine.Backtest"
        ) as mock_backtest:
            # Mock Backtest instance
            mock_bt_instance = MagicMock()
            mock_bt_instance.run.return_value = pd.Series([100000, 101000, 102000])
            mock_backtest.return_value = mock_bt_instance

            engine = BacktestingPyEngine(default_backtest_config)

            # Create mock strategy
            mock_strategy = MagicMock()

            # Run backtest
            result = engine.run(
                mock_strategy, sample_ohlcv_data, default_backtest_config
            )

            # Should have called Backtest.run
            mock_bt_instance.run.assert_called_once()

            # Should return BacktestResult
            assert result is not None
            assert hasattr(result, "equity_curve")
            assert hasattr(result, "trade_log")
            assert hasattr(result, "metrics")

    def test_engine_get_results(self, sample_ohlcv_data, default_backtest_config):
        """Test engine can get results after backtest."""
        with patch(
            "quantchain.backtesting.backtestingpy_engine.Backtest"
        ) as mock_backtest:
            # Mock Backtest instance
            mock_bt_instance = MagicMock()
            mock_bt_instance.run.return_value = pd.Series([100000, 101000, 102000])
            mock_bt_instance._results = {
                "equity": pd.Series([100000, 101000, 102000]),
                "trades": pd.DataFrame(),
            }
            mock_backtest.return_value = mock_bt_instance

            engine = BacktestingPyEngine(default_backtest_config)
            mock_strategy = MagicMock()

            # Run backtest first
            engine.run(mock_strategy, sample_ohlcv_data, default_backtest_config)

            # Get results
            results = engine.get_results()

            assert results is not None
            assert hasattr(results, "equity_curve")

    def test_engine_get_equity_curve(self, sample_ohlcv_data, default_backtest_config):
        """Test engine can get equity curve after backtest."""
        with patch(
            "quantchain.backtesting.backtestingpy_engine.Backtest"
        ) as mock_backtest:
            # Mock Backtest instance
            mock_bt_instance = MagicMock()
            mock_equity = pd.Series([100000, 101000, 102000])
            mock_bt_instance.run.return_value = mock_equity
            mock_backtest.return_value = mock_bt_instance

            engine = BacktestingPyEngine(default_backtest_config)
            mock_strategy = MagicMock()

            # Run backtest first
            engine.run(mock_strategy, sample_ohlcv_data, default_backtest_config)

            # Get equity curve
            equity_curve = engine.get_equity_curve()

            assert isinstance(equity_curve, pd.Series)
            assert len(equity_curve) == 3
            assert equity_curve.iloc[0] == 100000

    def test_engine_config_to_backtesting_params(self, default_backtest_config):
        """Test configuration conversion to Backtesting.py parameters."""
        with patch(
            "quantchain.backtesting.backtestingpy_engine.Backtest"
        ) as mock_backtest:
            config_with_params = BacktestConfig(
                initial_cash=150000.0,
                commission_rate=0.002,  # 0.2%
                slippage_rate=0.0005,  # 0.05%
                trade_on_close=True,
                hedging=False,
                exclusive_orders=True,
            )

            engine = BacktestingPyEngine(config_with_params)

            # Verify engine was created successfully
            assert engine is not None

            # Check Backtest was called with correct parameters
            mock_backtest.assert_called_once()
            call_args = mock_backtest.call_args

            # Should pass cash
            assert call_args[1]["cash"] == 150000.0

            # Should pass commission
            assert call_args[1]["commission"] == 0.002

            # Should pass trade_on_close
            assert call_args[1]["trade_on_close"] is True

            # Should pass hedging
            assert call_args[1]["hedging"] is False

            # Should pass exclusive_orders
            assert call_args[1]["exclusive_orders"] is True


@pytest.mark.requires_backtestingpy
@pytest.mark.unit
class TestStrategyAdapter:
    """Test StrategyAdapter class for Backtesting.py integration."""

    def test_strategy_adapter_initialization(self):
        """Test StrategyAdapter can be initialized with strategy."""
        mock_strategy = MagicMock()

        with patch(
            "quantchain.backtesting.backtestingpy_engine.Strategy"
        ) as mock_bt_strategy:
            adapter = StrategyAdapter(mock_strategy)

            assert adapter.strategy == mock_strategy
            mock_bt_strategy.assert_called_once()

    def test_strategy_adapter_init_method(self):
        """Test StrategyAdapter init method."""
        mock_strategy = MagicMock()

        with patch("quantchain.backtesting.backtestingpy_engine.Strategy") as _:
            adapter = StrategyAdapter(mock_strategy)

            # Call init method
            adapter.init()

            # Should call strategy.init
            mock_strategy.init.assert_called_once()

    def test_strategy_adapter_next_method(self):
        """Test StrategyAdapter next method converts bar data correctly."""
        mock_strategy = MagicMock()
        mock_strategy.next.return_value = "buy"

        with patch("quantchain.backtesting.backtestingpy_engine.Strategy") as _:
            adapter = StrategyAdapter(mock_strategy)

            # Mock Backtesting.py data interface
            mock_data = MagicMock()
            mock_data.Close = 100.5
            mock_data.Open = 100.0
            mock_data.High = 101.0
            mock_data.Low = 99.0
            mock_data.Volume = 1000

            # Call next method
            adapter.next(mock_data.i)

            # Should convert Backtesting.py data to dict format
            mock_strategy.next.assert_called_once()
            call_args = mock_strategy.next.call_args[0][0]

            assert isinstance(call_args, dict)
            assert "close" in call_args
            assert "open" in call_args
            assert "high" in call_args
            assert "low" in call_args
            assert "volume" in call_args
            assert call_args["close"] == 100.5
            assert call_args["open"] == 100.0
            assert call_args["high"] == 101.0
            assert call_args["low"] == 99.0
            assert call_args["volume"] == 1000

    def test_strategy_adapter_no_signal(self):
        """Test StrategyAdapter handles no signal correctly."""
        mock_strategy = MagicMock()
        mock_strategy.next.return_value = None

        with patch("quantchain.backtesting.backtestingpy_engine.Strategy") as _:
            adapter = StrategyAdapter(mock_strategy)

            mock_data = MagicMock()
            mock_data.Close = 100.5

            signal = adapter.next(mock_data.i)

            # Should return None when strategy returns None
            assert signal is None

    def test_strategy_adapter_buy_signal(self):
        """Test StrategyAdapter handles buy signal correctly."""
        mock_strategy = MagicMock()
        mock_strategy.next.return_value = "buy"

        with patch("quantchain.backtesting.backtestingpy_engine.Strategy") as _:
            adapter = StrategyAdapter(mock_strategy)

            mock_data = MagicMock()
            mock_data.Close = 100.5

            # Should return percentage position for Backtesting.py
            signal = adapter.next(mock_data.i)

            # In Backtesting.py, buy signal should be position size (0-1)
            assert 0 < signal <= 1

    def test_strategy_adapter_sell_signal(self):
        """Test StrategyAdapter handles sell signal correctly."""
        mock_strategy = MagicMock()
        mock_strategy.next.return_value = "sell"

        with patch("quantchain.backtesting.backtestingpy_engine.Strategy") as _:
            adapter = StrategyAdapter(mock_strategy)

            mock_data = MagicMock()
            mock_data.Close = 100.5

            # Should return percentage position for Backtesting.py
            signal = adapter.next(mock_data.i)

            # In Backtesting.py, sell signal should be negative position size
            assert -1 <= signal < 0


@pytest.mark.requires_backtestingpy
@pytest.mark.integration
class TestBacktestingPyIntegration:
    """Integration tests for Backtesting.py wrapper."""

    def test_backtestingpy_strategy_execution(
        self, sample_ohlcv_data, default_backtest_config
    ):
        """Test complete strategy execution using Backtesting.py."""
        with patch(
            "quantchain.backtesting.backtestingpy_engine.Backtest"
        ) as mock_backtest:
            # Mock Backtest execution
            mock_bt_instance = MagicMock()
            mock_equity = pd.Series([100000, 101000, 102000, 103000])
            mock_bt_instance.run.return_value = mock_equity
            mock_bt_instance._results = {
                "equity": mock_equity,
                "trades": pd.DataFrame(
                    {
                        "EntryTime": pd.date_range("2023-01-01", periods=2, freq="D"),
                        "ExitTime": pd.date_range("2023-01-02", periods=2, freq="D"),
                        "EntryPrice": [100.0, 101.0],
                        "ExitPrice": [101.0, 102.0],
                        "Size": [10, 10],
                        "PnL": [100.0 - 1.0, 100.0 - 1.02],  # Including commission
                    }
                ),
            }
            mock_backtest.return_value = mock_bt_instance

            engine = BacktestingPyEngine(default_backtest_config)

            # Create simple strategy
            simple_strategy = MagicMock()
            simple_strategy.init.return_value = None
            simple_strategy.next.side_effect = ["buy", None, "sell", None]

            result = engine.run(
                simple_strategy, sample_ohlcv_data[:4], default_backtest_config
            )

            # Should have executed strategy
            assert result is not None
            assert len(result.equity_curve) == 4
            assert len(result.trade_log) >= 2  # At least buy and sell

            # Should have converted Backtesting.py results
            assert isinstance(result.equity_curve, pd.Series)
            assert isinstance(result.trade_log, pd.DataFrame)

    def test_backtestingpy_commission_integration(self, sample_ohlcv_data):
        """Test commission parameter passes through to Backtesting.py."""
        config_with_commission = BacktestConfig(
            initial_cash=100000.0,
            commission_rate=0.005,  # 0.5% commission
            slippage_rate=0.0,  # No slippage for clean test
        )

        with patch(
            "quantchain.backtesting.backtestingpy_engine.Backtest"
        ) as mock_backtest:
            mock_bt_instance = MagicMock()
            mock_bt_instance.run.return_value = pd.Series([100000, 95000, 95000])
            mock_backtest.return_value = mock_bt_instance

            engine = BacktestingPyEngine(config_with_commission)

            mock_strategy = MagicMock()
            mock_strategy.init.return_value = None
            mock_strategy.next.side_effect = ["buy", "sell", None]

            engine.run(mock_strategy, sample_ohlcv_data[:3], config_with_commission)

            # Should pass commission to Backtesting.py
            mock_backtest.assert_called_once()
            call_args = mock_backtest.call_args
            assert call_args[1]["commission"] == 0.005

    def test_backtestingpy_slippage_integration(self, sample_ohlcv_data):
        """Test slippage parameter passes through to Backtesting.py."""
        config_with_slippage = BacktestConfig(
            initial_cash=100000.0,
            commission_rate=0.0,  # No commission for clean test
            slippage_rate=0.001,  # 0.1% slippage
        )

        with patch(
            "quantchain.backtesting.backtestingpy_engine.Backtest"
        ) as mock_backtest:
            mock_bt_instance = MagicMock()
            mock_bt_instance.run.return_value = pd.Series([100000, 99000, 99000])
            mock_backtest.return_value = mock_bt_instance

            engine = BacktestingPyEngine(config_with_slippage)

            mock_strategy = MagicMock()
            mock_strategy.init.return_value = None
            mock_strategy.next.side_effect = ["buy", "sell", None]

            engine.run(mock_strategy, sample_ohlcv_data[:3], config_with_slippage)

            # Should pass slippage as spread to Backtesting.py
            mock_backtest.assert_called_once()
            call_args = mock_backtest.call_args
            # In Backtesting.py, slippage is implemented as spread
            assert call_args[1]["spread"] == 0.001

    def test_backtestingpy_results_conversion(
        self, sample_ohlcv_data, default_backtest_config
    ):
        """Test Backtesting.py results conversion to BacktestResult format."""
        with patch(
            "quantchain.backtesting.backtestingpy_engine.Backtest"
        ) as mock_backtest:
            # Mock Backtesting.py results
            mock_equity = pd.Series([100000, 101000, 100500, 102000])
            mock_trades = pd.DataFrame(
                {
                    "EntryTime": pd.date_range("2023-01-01", periods=2, freq="D"),
                    "ExitTime": pd.date_range("2023-01-02", periods=2, freq="D"),
                    "EntryPrice": [100.0, 99.5],
                    "ExitPrice": [101.0, 102.0],
                    "Size": [10, 10],
                    "PnL": [1000.0 - 2.0, 2500.0 - 2.0],  # Including commission
                }
            )

            mock_bt_instance = MagicMock()
            mock_bt_instance.run.return_value = mock_equity
            mock_bt_instance._results = {"equity": mock_equity, "trades": mock_trades}
            mock_backtest.return_value = mock_bt_instance

            engine = BacktestingPyEngine(default_backtest_config)

            mock_strategy = MagicMock()
            result = engine.run(
                mock_strategy, sample_ohlcv_data[:4], default_backtest_config
            )

            # Should convert results correctly
            assert isinstance(result, BacktestResult)
            assert len(result.equity_curve) == 4
            assert len(result.trade_log) == 2

            # Check trade log conversion
            expected_columns = [
                "timestamp",
                "symbol",
                "side",
                "quantity",
                "price",
                "pnl",
            ]
            for col in expected_columns:
                assert col in result.trade_log.columns

    def test_backtestingpy_optimization_support(self, sample_ohlcv_data):
        """Test Backtesting.py optimization parameter support."""
        config_with_optimization = BacktestConfig(
            initial_cash=100000.0,
            commission_rate=0.001,
            additional_params={
                "optimization": True,
                "constraint": lambda x: x >= 5,  # Minimum 5 trades
                "maximize": "Sharpe Ratio",
            },
        )

        with patch(
            "quantchain.backtesting.backtestingpy_engine.Backtest"
        ) as mock_backtest:
            mock_bt_instance = MagicMock()
            mock_bt_instance.optimize.return_value = pd.Series([100000, 101000, 102000])
            mock_bt_instance._results = {"equity": pd.Series([100000, 101000, 102000])}
            mock_backtest.return_value = mock_bt_instance

            engine = BacktestingPyEngine(config_with_optimization)

            mock_strategy = MagicMock()

            # Test optimization mode
            result = engine.run(
                mock_strategy, sample_ohlcv_data[:3], config_with_optimization
            )

            # Should call optimize instead of run when optimization is enabled
            mock_bt_instance.optimize.assert_called_once()

            # Should still return valid BacktestResult
            assert result is not None
            assert isinstance(result, BacktestResult)

    def test_backtestingpy_error_handling(
        self, sample_ohlcv_data, default_backtest_config
    ):
        """Test Backtesting.py error handling."""
        with patch(
            "quantchain.backtesting.backtestingpy_engine.Backtest"
        ) as mock_backtest:
            # Mock Backtesting.py error
            mock_bt_instance = MagicMock()
            mock_bt_instance.run.side_effect = Exception(
                "Backtesting.py execution failed"
            )
            mock_backtest.return_value = mock_bt_instance

            engine = BacktestingPyEngine(default_backtest_config)

            mock_strategy = MagicMock()

            # Should handle Backtesting.py errors gracefully
            with pytest.raises(
                BacktestingPyError, match="Backtesting.py execution failed"
            ):
                engine.run(mock_strategy, sample_ohlcv_data, default_backtest_config)

    def test_backtestingpy_conversion_error(
        self, sample_ohlcv_data, default_backtest_config
    ):
        """Test error handling during results conversion."""
        with patch(
            "quantchain.backtesting.backtestingpy_engine.Backtest"
        ) as mock_backtest:
            # Mock invalid Backtesting.py results
            mock_bt_instance = MagicMock()
            mock_bt_instance.run.return_value = "invalid_result"  # Not a Series
            mock_bt_instance._results = {"equity": "invalid_result"}
            mock_backtest.return_value = mock_bt_instance

            engine = BacktestingPyEngine(default_backtest_config)

            mock_strategy = MagicMock()

            # Should handle conversion errors gracefully
            with pytest.raises(
                ConversionError, match="Failed to convert Backtesting.py results"
            ):
                engine.run(mock_strategy, sample_ohlcv_data, default_backtest_config)


@pytest.mark.integration
class TestBacktestingPyPerformance:
    """Performance tests for Backtesting.py integration."""

    @pytest.mark.slow
    @pytest.mark.requires_backtestingpy
    def test_backtestingpy_performance_large_dataset(self):
        """Test Backtesting.py performance with large dataset."""
        # Create large dataset
        large_data = pd.DataFrame(
            {
                "open": np.random.uniform(90, 110, 10000),
                "high": np.random.uniform(100, 120, 10000),
                "low": np.random.uniform(80, 100, 10000),
                "close": np.random.uniform(90, 110, 10000),
                "volume": np.random.randint(100000, 1000000, 10000),
            },
            index=pd.date_range("2020-01-01", periods=10000, freq="1min"),
        )

        config = BacktestConfig(initial_cash=100000.0)

        with patch(
            "quantchain.backtesting.backtestingpy_engine.Backtest"
        ) as mock_backtest:
            mock_bt_instance = MagicMock()
            mock_bt_instance.run.return_value = pd.Series(
                np.random.uniform(90000, 110000, 10000)
            )
            mock_backtest.return_value = mock_bt_instance

            engine = BacktestingPyEngine(config)

            mock_strategy = MagicMock()
            mock_strategy.next.return_value = None  # No trading for performance test

            import time

            start_time = time.time()

            result = engine.run(mock_strategy, large_data, config)

            execution_time = time.time() - start_time

            # Should complete within reasonable time (adjust threshold as needed)
            assert execution_time < 10.0  # 10 seconds max
            assert result is not None
            assert len(result.equity_curve) == 10000
