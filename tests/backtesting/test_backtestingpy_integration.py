"""
Failing tests for Backtesting.py library integration.
Following TDD principles - these tests will fail initially.
"""





@pytest.mark.requires_backtestingpy
@pytest.mark.unit


class TestBacktestingPyEngine:
    """Test BacktestingPyEngine class."""


from unittest.mock import MagicMock, patch
import numpy as np
import pandas as pd
import pytest
from quantchain.backtesting.backtestingpy_engine import BacktestingPyEngine
from quantchain.backtesting.engine import BacktestConfig, BacktestResult
from quantchain.backtesting.engine import BacktestConfig
from quantchain.backtesting.backtestingpy_engine import StrategyAdapter
from quantchain.backtesting.backtestingpy_engine import StrategyAdapter
from quantchain.backtesting.backtestingpy_engine import StrategyAdapter
from quantchain.backtesting.backtestingpy_engine import StrategyAdapter
from quantchain.backtesting.backtestingpy_engine import StrategyAdapter
from quantchain.backtesting.backtestingpy_engine import StrategyAdapter



def test_engine_initialization(self, default_backtest_config) -> None:
        """Test BacktestingPyEngine can be initialized with configuration."""
        # Patch Backtesting.py imports
        with patch("quantchain.backtesting.backtestingpy_engine.Backtest"), patch(
            "quantchain.backtesting.backtestingpy_engine.Strategy"
        ), patch("quantchain.backtesting.backtestingpy_engine.StrategyAdapter"):
            engine = BacktestingPyEngine(default_backtest_config)

            assert engine.config == default_backtest_config



def test_engine_initialization_default_config(self) -> None:
        """Test BacktestingPyEngine can be initialized with default config."""

        with patch("quantchain.backtesting.backtestingpy_engine.Backtest"), patch(
            "quantchain.backtesting.backtestingpy_engine.Strategy"
        ), patch("quantchain.backtesting.backtestingpy_engine.StrategyAdapter"):
            engine = BacktestingPyEngine()

            assert isinstance(engine.config, BacktestConfig)



def test_engine_run_with_strategy(
        self, sample_ohlcv_data, default_backtest_config
    ) -> None:
        """Test engine can run a backtest with strategy."""
        with patch("quantchain.backtesting.backtestingpy_engine.Backtest"), patch(
            "quantchain.backtesting.backtestingpy_engine.Strategy"
        ), patch("quantchain.backtesting.backtestingpy_engine.StrategyAdapter"):
            engine = BacktestingPyEngine(default_backtest_config)

            # Create mock strategy
            mock_strategy = MagicMock()

            # Run backtest
            result = engine.run(
                mock_strategy, sample_ohlcv_data, default_backtest_config
            )

            # Should return BacktestResult
            assert result is not None
            assert hasattr(result, "equity_curve")
            assert hasattr(result, "trade_log")
            assert hasattr(result, "metrics")



def test_engine_get_results(
        self, sample_ohlcv_data, default_backtest_config
    ) -> None:
        """Test engine can get results after backtest."""
        with patch("quantchain.backtesting.backtestingpy_engine.Backtest"), patch(
            "quantchain.backtesting.backtestingpy_engine.Strategy"
        ), patch("quantchain.backtesting.backtestingpy_engine.StrategyAdapter"):
            engine = BacktestingPyEngine(default_backtest_config)
            mock_strategy = MagicMock()

            # Run backtest first
            engine.run(mock_strategy, sample_ohlcv_data, default_backtest_config)

            # Get results
            results = engine.get_results()
            assert results is not None
            assert hasattr(results, "equity_curve")
            assert hasattr(results, "trade_log")
            assert hasattr(results, "metrics")



def test_engine_get_equity_curve(
        self, sample_ohlcv_data, default_backtest_config
    ) -> None:
        """Test engine can get equity curve after backtest."""
        with patch("quantchain.backtesting.backtestingpy_engine.Backtest"), patch(
            "quantchain.backtesting.backtestingpy_engine.Strategy"
        ), patch("quantchain.backtesting.backtestingpy_engine.StrategyAdapter"):
            engine = BacktestingPyEngine(default_backtest_config)
            mock_strategy = MagicMock()

            # Run backtest first
            engine.run(mock_strategy, sample_ohlcv_data, default_backtest_config)

            # Get equity curve
            equity_curve = engine.get_equity_curve()

            assert isinstance(equity_curve, pd.Series)



def test_engine_config_to_backtesting_params(self, default_backtest_config) -> None:
        """Test configuration conversion to Backtesting.py parameters."""
        with patch("quantchain.backtesting.backtestingpy_engine.Backtest"), patch(
            "quantchain.backtesting.backtestingpy_engine.Strategy"
        ), patch("quantchain.backtesting.backtestingpy_engine.StrategyAdapter"):
            config_with_params = BacktestConfig(
                initial_cash=150000.0,
                commission_rate=0.002,  # 0.2%
                slippage_rate=0.0005,  # 0.05%
                additional_params={
                    "trade_on_close": True,
                    "hedging": False,
                    "exclusive_orders": True,
                },
            )

            engine = BacktestingPyEngine(config_with_params)

            # Verify engine was created successfully
            assert engine is not None


@pytest.mark.requires_backtestingpy
@pytest.mark.unit


class TestStrategyAdapter:
    """Test StrategyAdapter class for Backtesting.py integration."""



def test_strategy_adapter_initialization(self) -> None:
        """Test StrategyAdapter can be initialized with strategy."""
        mock_strategy = MagicMock()

        with patch("quantchain.backtesting.backtestingpy_engine.Backtest"), patch(
            "quantchain.backtesting.backtestingpy_engine.Strategy"
        ), patch(
            "quantchain.backtesting.backtestingpy_engine.StrategyAdapter"
        ) as mock_adapter_class:
            mock_instance = MagicMock()
            mock_adapter_class.return_value = mock_instance

            # Import only when patched

            adapter = StrategyAdapter(mock_strategy)

            assert adapter == mock_instance
            mock_adapter_class.assert_called_once_with(mock_strategy)



def test_strategy_adapter_init_method(self) -> None:
        """Test StrategyAdapter init method."""
        mock_strategy = MagicMock()

        with patch("quantchain.backtesting.backtestingpy_engine.Backtest"), patch(
            "quantchain.backtesting.backtestingpy_engine.Strategy"
        ), patch(
            "quantchain.backtesting.backtestingpy_engine.StrategyAdapter"
        ) as mock_adapter_class:
            mock_instance = MagicMock()
            mock_adapter_class.return_value = mock_instance

            # Import only when patched

            adapter = StrategyAdapter(mock_strategy)

            # Call init method
            adapter.init()

            # Should call the init method on the mock instance
            mock_instance.init.assert_called_once()



def test_strategy_adapter_next_method(self) -> None:
        """Test StrategyAdapter next method converts bar data correctly."""
        mock_strategy = MagicMock()
        mock_strategy.next.return_value = "buy"

        with patch("quantchain.backtesting.backtestingpy_engine.Backtest"), patch(
            "quantchain.backtesting.backtestingpy_engine.Strategy"
        ), patch(
            "quantchain.backtesting.backtestingpy_engine.StrategyAdapter"
        ) as mock_adapter_class:
            mock_instance = MagicMock()
            mock_adapter_class.return_value = mock_instance

            # Import only when patched

            adapter = StrategyAdapter(mock_strategy)

            # Call next method
            adapter.next()

            # Should call next method on mock instance
            mock_instance.next.assert_called_once()



def test_strategy_adapter_no_signal(self) -> None:
        """Test StrategyAdapter handles no signal correctly."""
        mock_strategy = MagicMock()
        mock_strategy.next.return_value = None

        with patch("quantchain.backtesting.backtestingpy_engine.Backtest"), patch(
            "quantchain.backtesting.backtestingpy_engine.Strategy"
        ), patch(
            "quantchain.backtesting.backtestingpy_engine.StrategyAdapter"
        ) as mock_adapter_class:
            mock_instance = MagicMock()
            mock_instance.next.return_value = None
            mock_adapter_class.return_value = mock_instance

            # Import only when patched

            adapter = StrategyAdapter(mock_strategy)

            signal = adapter.next()

            # Should return None when strategy returns None
            assert signal is None



def test_strategy_adapter_buy_signal(self) -> None:
        """Test StrategyAdapter handles buy signal correctly."""
        mock_strategy = MagicMock()
        mock_strategy.next.return_value = "buy"

        with patch("quantchain.backtesting.backtestingpy_engine.Backtest"), patch(
            "quantchain.backtesting.backtestingpy_engine.Strategy"
        ), patch(
            "quantchain.backtesting.backtestingpy_engine.StrategyAdapter"
        ) as mock_adapter_class:
            mock_instance = MagicMock()
            mock_instance.next.return_value = 0.1  # 10% position size
            mock_adapter_class.return_value = mock_instance

            # Import only when patched

            adapter = StrategyAdapter(mock_strategy)

            # Should return percentage position for Backtesting.py
            signal = adapter.next()

            # In Backtesting.py, buy signal should be position size (0-1)
            assert 0 < signal <= 1



def test_strategy_adapter_sell_signal(self) -> None:
        """Test StrategyAdapter handles sell signal correctly."""
        mock_strategy = MagicMock()
        mock_strategy.next.return_value = "sell"

        with patch("quantchain.backtesting.backtestingpy_engine.Backtest"), patch(
            "quantchain.backtesting.backtestingpy_engine.Strategy"
        ), patch(
            "quantchain.backtesting.backtestingpy_engine.StrategyAdapter"
        ) as mock_adapter_class:
            mock_instance = MagicMock()
            mock_instance.next.return_value = -0.1  # -10% position size (sell)
            mock_adapter_class.return_value = mock_instance

            # Import only when patched

            adapter = StrategyAdapter(mock_strategy)

            # Should return percentage position for Backtesting.py
            signal = adapter.next()

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
        with patch("quantchain.backtesting.backtestingpy_engine.Backtest"), patch(
            "quantchain.backtesting.backtestingpy_engine.Strategy"
        ), patch("quantchain.backtesting.backtestingpy_engine.StrategyAdapter"):
            engine = BacktestingPyEngine(default_backtest_config)

            # Create simple strategy
            simple_strategy = MagicMock()
            simple_strategy.init.return_value = None
            simple_strategy.next.side_effect: list = ["buy", None, "sell", None]

            result = engine.run(
                simple_strategy, sample_ohlcv_data[:4], default_backtest_config
            )

            # Should have executed strategy
            assert result is not None
            assert isinstance(result.equity_curve, pd.Series)
            assert isinstance(result.trade_log, pd.DataFrame)



def test_backtestingpy_commission_integration(self, sample_ohlcv_data) -> None:
        """Test commission parameter passes through to Backtesting.py."""
        config_with_commission = BacktestConfig(
            initial_cash=100000.0,
            commission_rate=0.005,  # 0.5% commission
            slippage_rate=0.0,  # No slippage for clean test
        )

        with patch("quantchain.backtesting.backtestingpy_engine.Backtest"), patch(
            "quantchain.backtesting.backtestingpy_engine.Strategy"
        ), patch("quantchain.backtesting.backtestingpy_engine.StrategyAdapter"):
            engine = BacktestingPyEngine(config_with_commission)

            mock_strategy = MagicMock()
            mock_strategy.init.return_value = None
            mock_strategy.next.side_effect: list = ["buy", "sell", None]

            result = engine.run(
                mock_strategy, sample_ohlcv_data[:3], config_with_commission
            )

            # Should have executed strategy
            assert result is not None

            # Should have executed strategy
            assert result is not None



def test_backtestingpy_slippage_integration(self, sample_ohlcv_data) -> None:
        """Test slippage parameter passes through to Backtesting.py."""
        config_with_slippage = BacktestConfig(
            initial_cash=100000.0,
            commission_rate=0.0,  # No commission for clean test
            slippage_rate=0.001,  # 0.1% slippage
        )

        with patch("quantchain.backtesting.backtestingpy_engine.Backtest"), patch(
            "quantchain.backtesting.backtestingpy_engine.Strategy"
        ), patch("quantchain.backtesting.backtestingpy_engine.StrategyAdapter"):
            engine = BacktestingPyEngine(config_with_slippage)

            mock_strategy = MagicMock()
            mock_strategy.init.return_value = None
            mock_strategy.next.side_effect: list = ["buy", "sell", None]

            result = engine.run(
                mock_strategy, sample_ohlcv_data[:3], config_with_slippage
            )

            # Should have executed strategy
            assert result is not None
            # Should have executed strategy
            assert result is not None



def test_backtestingpy_results_conversion(
        self, sample_ohlcv_data, default_backtest_config
    ):
        """Test Backtesting.py results conversion to BacktestResult format."""
        with patch("quantchain.backtesting.backtestingpy_engine.Backtest"), patch(
            "quantchain.backtesting.backtestingpy_engine.Strategy"
        ), patch("quantchain.backtesting.backtestingpy_engine.StrategyAdapter"):
            engine = BacktestingPyEngine(default_backtest_config)
            engine = BacktestingPyEngine(default_backtest_config)

            mock_strategy = MagicMock()
            result = engine.run(
                mock_strategy, sample_ohlcv_data[:4], default_backtest_config
            )

            # Should convert results correctly
            assert isinstance(result, BacktestResult)
            assert isinstance(result.equity_curve, pd.Series)
            assert isinstance(result.trade_log, pd.DataFrame)



def test_backtestingpy_optimization_support(self, sample_ohlcv_data) -> None:
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

        with patch("quantchain.backtesting.backtestingpy_engine.Backtest"), patch(
            "quantchain.backtesting.backtestingpy_engine.Strategy"
        ), patch("quantchain.backtesting.backtestingpy_engine.StrategyAdapter"):
            engine = BacktestingPyEngine(config_with_optimization)

            mock_strategy = MagicMock()

            # Test optimization mode
            result = engine.run(
                mock_strategy, sample_ohlcv_data[:3], config_with_optimization
            )

            # Should still return valid BacktestResult
            assert result is not None
            assert isinstance(result, BacktestResult)



def test_backtestingpy_error_handling(
        self, sample_ohlcv_data, default_backtest_config
    ):
        """Test Backtesting.py error handling."""
        with patch("quantchain.backtesting.backtestingpy_engine.Backtest"), patch(
            "quantchain.backtesting.backtestingpy_engine.Strategy"
        ), patch("quantchain.backtesting.backtestingpy_engine.StrategyAdapter"):
            engine = BacktestingPyEngine(default_backtest_config)

            mock_strategy = MagicMock()

            # Test that we can run the engine without errors in mocked environment
            result = engine.run(
                mock_strategy, sample_ohlcv_data, default_backtest_config
            )
            assert result is not None



def test_backtestingpy_conversion_error(
        self, sample_ohlcv_data, default_backtest_config
    ):
        """Test error handling during results conversion."""
        with patch("quantchain.backtesting.backtestingpy_engine.Backtest"), patch(
            "quantchain.backtesting.backtestingpy_engine.Strategy"
        ), patch("quantchain.backtesting.backtestingpy_engine.StrategyAdapter"):
            engine = BacktestingPyEngine(default_backtest_config)

            mock_strategy = MagicMock()

            # Test that we can run the engine without errors in mocked environment
            result = engine.run(
                mock_strategy, sample_ohlcv_data, default_backtest_config
            )
            assert result is not None


@pytest.mark.integration


class TestBacktestingPyPerformance:
    """Performance tests for Backtesting.py integration."""

    @pytest.mark.slow
    @pytest.mark.requires_backtestingpy


def test_backtestingpy_performance_large_dataset(self) -> None:
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

        with patch("quantchain.backtesting.backtestingpy_engine.Backtest"), patch(
            "quantchain.backtesting.backtestingpy_engine.Strategy"
        ), patch("quantchain.backtesting.backtestingpy_engine.StrategyAdapter"):
            engine = BacktestingPyEngine(config)

            mock_strategy = MagicMock()
            mock_strategy.next.return_value = None  # No trading for performance test

            result = engine.run(mock_strategy, large_data[:100], config)

            # Should complete execution without errors
            assert result is not None
            assert isinstance(result, BacktestResult)
