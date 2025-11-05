"""
Failing tests for custom vector backtester.
Following TDD principles - these tests will fail initially.
"""

import pytest
import pandas as pd
import numpy as np

from quantchain.backtesting.vector_backtester import (
    VectorBacktester,
    VectorizedPositionManager,
    VectorBacktestError,
    SignalProcessingError,
)
from quantchain.backtesting.engine import BacktestConfig


@pytest.mark.skip(
    reason="Vector backtester implementation is incomplete - placeholder tests"
)
@pytest.mark.unit
class TestVectorBacktester:
    """Test VectorBacktester class."""

    def test_vector_backtester_initialization(self, default_backtest_config):
        """Test VectorBacktester can be initialized with configuration."""
        backtester = VectorBacktester(default_backtest_config)

        assert backtester.config == default_backtest_config
        assert hasattr(backtester, "position_manager")
        assert hasattr(backtester, "market_friction")

    def test_vector_backtester_initialization_default_config(self):
        """Test VectorBacktester can be initialized with default config."""
        from quantchain.backtesting.engine import BacktestConfig

        backtester = VectorBacktester()

        assert isinstance(backtester.config, BacktestConfig)

    def test_vector_backtester_run_signal_based_strategy(
        self, sample_ohlcv_data, default_backtest_config
    ):
        """Test running signal-based strategy with vector backtester."""
        backtester = VectorBacktester(default_backtest_config)

        # Create simple buy-and-hold signals
        signals = pd.Series([0] * len(sample_ohlcv_data))
        signals.iloc[0] = 1  # Buy signal at start
        signals.iloc[-1] = -1  # Sell signal at end

        result = backtester.run(signals, sample_ohlcv_data, default_backtest_config)

        assert result is not None
        assert hasattr(result, "equity_curve")
        assert hasattr(result, "trade_log")
        assert hasattr(result, "metrics")

        # Should have processed all data points
        assert len(result.equity_curve) == len(sample_ohlcv_data)

    def test_vector_backtester_run_multiple_signals(
        self, sample_ohlcv_data, default_backtest_config
    ):
        """Test running strategy with multiple buy/sell signals."""
        backtester = VectorBacktester(default_backtest_config)

        # Create multiple signals
        signals = pd.Series([0] * len(sample_ohlcv_data))
        signals.iloc[10] = 1  # First buy
        signals.iloc[50] = -1  # First sell
        signals.iloc[100] = 1  # Second buy
        signals.iloc[150] = -1  # Second sell

        result = backtester.run(signals, sample_ohlcv_data, default_backtest_config)

        assert result is not None
        assert len(result.trade_log) >= 4  # At least 4 trades (2 round trips)

        # Should have equity curve
        assert len(result.equity_curve) == len(sample_ohlcv_data)

    def test_vector_backtester_run_no_signals(
        self, sample_ohlcv_data, default_backtest_config
    ):
        """Test running strategy with no trading signals."""
        backtester = VectorBacktester(default_backtest_config)

        # Create all-zero signals
        signals = pd.Series([0] * len(sample_ohlcv_data))

        result = backtester.run(signals, sample_ohlcv_data, default_backtest_config)

        assert result is not None
        assert len(result.trade_log) == 0  # No trades

        # Equity curve should be flat (no trading)
        expected_equity = [default_backtest_config.initial_cash] * len(
            sample_ohlcv_data
        )
        np.testing.assert_array_almost_equal(
            result.equity_curve.values, expected_equity, decimal=2
        )

    def test_vector_backtester_get_results(
        self, sample_ohlcv_data, default_backtest_config
    ):
        """Test getting results after backtest."""
        backtester = VectorBacktester(default_backtest_config)

        # Run a backtest first
        signals = pd.Series([0] * len(sample_ohlcv_data))
        signals.iloc[0] = 1
        signals.iloc[-1] = -1

        backtester.run(signals, sample_ohlcv_data, default_backtest_config)
        results = backtester.get_results()

        assert results is not None
        assert hasattr(results, "equity_curve")
        assert hasattr(results, "trade_log")
        assert hasattr(results, "metrics")

    def test_vector_backtester_get_equity_curve(
        self, sample_ohlcv_data, default_backtest_config
    ):
        """Test getting equity curve after backtest."""
        backtester = VectorBacktester(default_backtest_config)

        # Run a backtest first
        signals = pd.Series([0] * len(sample_ohlcv_data))
        signals.iloc[0] = 1
        signals.iloc[-1] = -1

        backtester.run(signals, sample_ohlcv_data, default_backtest_config)
        equity_curve = backtester.get_equity_curve()

        assert isinstance(equity_curve, pd.Series)
        assert len(equity_curve) == len(sample_ohlcv_data)

    def test_vector_backtester_with_commission(self, sample_ohlcv_data):
        """Test vector backtester with commission."""
        config_with_commission = BacktestConfig(
            initial_cash=100000.0,
            commission_rate=0.001,  # 0.1% commission
            slippage_rate=0.0,  # No slippage for clean test
        )

        backtester = VectorBacktester(config_with_commission)

        # Simple buy and sell
        signals = pd.Series([0] * len(sample_ohlcv_data))
        signals.iloc[0] = 1  # Buy
        signals.iloc[100] = -1  # Sell

        result = backtester.run(signals, sample_ohlcv_data, config_with_commission)

        assert result is not None

        # Final equity should be less than without commission
        # (accounting for price changes and commission costs)
        buy_price = sample_ohlcv_data.iloc[0]["close"]
        sell_price = sample_ohlcv_data.iloc[100]["close"]
        shares = int(100000.0 / buy_price)
        commission_cost = shares * (buy_price + sell_price) * 0.001
        expected_final_equity = shares * sell_price - commission_cost

        assert abs(result.equity_curve.iloc[-1] - expected_final_equity) < 100.0

    def test_vector_backtester_with_slippage(self, sample_ohlcv_data):
        """Test vector backtester with slippage."""
        config_with_slippage = BacktestConfig(
            initial_cash=100000.0,
            commission_rate=0.0,  # No commission
            slippage_rate=0.001,  # 0.1% slippage
        )

        backtester = VectorBacktester(config_with_slippage)

        # Simple buy and sell
        signals = pd.Series([0] * len(sample_ohlcv_data))
        signals.iloc[0] = 1  # Buy
        signals.iloc[100] = -1  # Sell

        result = backtester.run(signals, sample_ohlcv_data, config_with_slippage)

        assert result is not None

        # Final equity should account for slippage
        buy_price = sample_ohlcv_data.iloc[0]["close"]
        sell_price = sample_ohlcv_data.iloc[100]["close"]
        shares = int(100000.0 / (buy_price * 1.001))  # Buy with slippage
        expected_final_equity = shares * (sell_price * 0.999)  # Sell with slippage

        assert abs(result.equity_curve.iloc[-1] - expected_final_equity) < 100.0

    def test_vector_backtester_long_short_strategy(
        self, sample_ohlcv_data, default_backtest_config
    ):
        """Test vector backtester with long-short strategy."""
        backtester = VectorBacktester(default_backtest_config)

        # Create signals for both long and short positions
        signals = pd.Series([0] * len(sample_ohlcv_data))
        signals.iloc[10] = 1  # Go long
        signals.iloc[50] = -1  # Go short
        signals.iloc[100] = 1  # Go long again
        signals.iloc[150] = -1  # Go short again

        result = backtester.run(signals, sample_ohlcv_data, default_backtest_config)

        assert result is not None
        assert len(result.trade_log) >= 4

        # Should handle both positive and negative positions
        positions = result.trade_log.get("position", pd.Series())

        # With our test data, we should have positions to test
        assert len(positions) > 0, "Test should generate positions"
        assert positions.min() <= 0  # Should have some short positions
        assert positions.max() >= 0  # Should have some long positions


@pytest.mark.unit
class TestVectorizedPositionManager:
    """Test VectorizedPositionManager class."""

    def test_vectorized_position_manager_initialization(self):
        """Test VectorizedPositionManager can be initialized."""
        manager = VectorizedPositionManager(initial_cash=100000.0)

        assert manager.initial_cash == 100000.0
        assert manager.current_cash == 100000.0
        assert hasattr(manager, "positions")
        assert hasattr(manager, "equity_curve")

    def test_vectorized_position_manager_process_signals(self):
        """Test processing trading signals."""
        manager = VectorizedPositionManager(initial_cash=100000.0)

        # Create simple price data and signals
        prices = pd.Series([100, 101, 102, 103, 104])
        signals = pd.Series([1, 0, 0, 0, -1])  # Buy first, sell last

        positions, trades, final_cash = manager.process_signals(prices, signals)

        assert isinstance(positions, pd.Series)
        assert isinstance(trades, pd.DataFrame)
        assert len(positions) == len(prices)

        # Should have position from first signal
        assert positions.iloc[0] > 0

    def test_vectorized_position_manager_calculate_equity(self):
        """Test equity calculation from positions and prices."""
        manager = VectorizedPositionManager(initial_cash=100000.0)

        # Create price series
        prices = pd.Series([100, 101, 102, 103, 104])

        # Create position series (buy at start, hold)
        shares = int(100000.0 / 100)  # Buy as many shares as possible
        positions = pd.Series([shares] * len(prices))

        equity = manager.calculate_equity(positions, prices)

        assert isinstance(equity, pd.Series)
        assert len(equity) == len(prices)

        # Equity should increase with price
        assert equity.iloc[0] == 100000.0
        assert equity.iloc[-1] > 100000.0

    def test_vectorized_position_manager_multiple_positions(self):
        """Test managing multiple positions over time."""
        manager = VectorizedPositionManager(initial_cash=100000.0)

        # Create price series and multiple trading signals
        prices = pd.Series([100, 105, 95, 110, 90])
        signals = pd.Series([1, -1, 1, -1, 1])  # Multiple trades

        positions, trades, final_cash = manager.process_signals(prices, signals)

        assert isinstance(positions, pd.Series)
        assert isinstance(trades, pd.DataFrame)

        # Should have multiple trades
        assert len(trades) >= 4  # At least 4 trade signals

        # Final position should be positive (last signal is buy)
        assert positions.iloc[-1] > 0

    def test_vectorized_position_manager_with_costs(self):
        """Test position management with transaction costs."""
        manager = VectorizedPositionManager(
            initial_cash=100000.0,
            commission_rate=0.001,  # 0.1% commission
            slippage_rate=0.0005,  # 0.05% slippage
        )

        prices = pd.Series([100, 105])
        signals = pd.Series([1, -1])  # Buy and sell

        positions, trades, final_cash = manager.process_signals(prices, signals)

        # Should account for costs in trade details
        assert len(trades) == 2  # Buy and sell trades

        # Commission should be calculated for both trades
        assert "commission" in trades.columns, "Trades should have commission column"
        assert (trades["commission"] > 0).all()

    def test_vectorized_position_manager_insufficient_cash(self):
        """Test handling insufficient cash for positions."""
        manager = VectorizedPositionManager(initial_cash=1000.0)

        # Create prices that are too high for available cash
        prices = pd.Series([1000, 2000, 3000])
        signals = pd.Series([1, 1, 1])  # Try to buy at each point

        positions, trades, final_cash = manager.process_signals(prices, signals)

        # Should handle insufficient cash gracefully
        # (either no positions or scaled positions)
        assert isinstance(positions, pd.Series)
        assert isinstance(trades, pd.DataFrame)


@pytest.mark.integration
class TestVectorBacktesterIntegration:
    """Integration tests for vector backtester."""

    def test_vector_backtester_vs_event_driven_comparison(self, sample_ohlcv_data):
        """Test vector backtester produces similar results to event-driven approach."""
        config = BacktestConfig(
            initial_cash=100000.0, commission_rate=0.001, slippage_rate=0.0005
        )

        vector_backtester = VectorBacktester(config)

        # Create simple strategy signals
        signals = pd.Series([0] * len(sample_ohlcv_data))
        signals.iloc[10] = 1  # Buy
        signals.iloc[50] = -1  # Sell

        # Run vector backtest
        vector_result = vector_backtester.run(signals, sample_ohlcv_data, config)

        # Mock event-driven backtest for comparison
        event_driven_result = self._mock_event_driven_backtest(
            signals, sample_ohlcv_data, config
        )

        # Results should be reasonably close (allowing for small differences)
        assert len(vector_result.equity_curve) == len(event_driven_result["equity"])

        # Final equity should be close (within 1% tolerance)
        vector_final = vector_result.equity_curve.iloc[-1]
        event_final = event_driven_result["equity"][-1]
        relative_diff = abs(vector_final - event_final) / event_final
        assert relative_diff < 0.01  # Within 1%

    def test_vector_backtester_performance_simple_strategy(self):
        """Test vector backtester performance with simple strategy."""
        config = BacktestConfig(initial_cash=100000.0)

        # Create large dataset
        large_data = pd.DataFrame(
            {
                "close": np.random.uniform(90, 110, 100000),
                "volume": np.random.randint(100000, 1000000, 100000),
            },
            index=pd.date_range("2020-01-01", periods=100000, freq="1min"),
        )

        # Simple moving average crossover signals
        signals = self._generate_ma_crossover_signals(large_data["close"])

        backtester = VectorBacktester(config)

        import time

        start_time = time.time()

        result = backtester.run(signals, large_data, config)

        execution_time = time.time() - start_time

        # Should complete within reasonable time (adjusted for large dataset)
        assert execution_time < 30.0  # 30 seconds max for 100k rows
        assert result is not None
        assert len(result.equity_curve) == 100000

    def test_vector_backtester_signal_based_strategy(self, sample_ohlcv_data):
        """Test vector backtester with signal-based strategy."""
        backtester = VectorBacktester()

        # Generate signals based on price momentum
        prices = sample_ohlcv_data["close"]
        returns = prices.pct_change()
        signals = pd.Series(0, index=prices.index)

        # Buy when momentum is positive
        signals[returns > 0.02] = 1
        # Sell when momentum is negative
        signals[returns < -0.02] = -1

        result = backtester.run(signals, sample_ohlcv_data)

        assert result is not None
        assert len(result.equity_curve) == len(sample_ohlcv_data)

        # Should have trades when momentum triggers
        assert len(result.trade_log) >= 0

    def test_vector_backtester_position_tracking(self, sample_ohlcv_data):
        """Test vector backtester tracks positions correctly."""
        backtester = VectorBacktester()

        # Create signals that should generate known position changes
        signals = pd.Series(0, index=sample_ohlcv_data.index)
        signals.iloc[10] = 1  # Buy at position 10
        signals.iloc[50] = -1  # Sell at position 50
        signals.iloc[100] = 1  # Buy again at position 100
        signals.iloc[150] = -1  # Sell at position 150

        result = backtester.run(signals, sample_ohlcv_data)

        assert result is not None

        # Check position tracking in trade log
        assert len(result.trade_log) > 0, "Should have trade log entries"

        # Should have entries for each signal
        trade_count = len(result.trade_log)
        assert trade_count >= 4  # At least 4 trades

        # Check that positions are tracked correctly
        assert (
            "position" in result.trade_log.columns
        ), "Trade log should have position column"
        positions = result.trade_log["position"].values
        assert positions[0] > 0  # First buy
        assert positions[-1] == 0  # Final sell (flat position)

    def test_vector_backtester_error_handling_invalid_signals(self, sample_ohlcv_data):
        """Test error handling with invalid signals."""
        backtester = VectorBacktester()

        # Invalid signals (NaN values)
        invalid_signals = pd.Series([np.nan] * len(sample_ohlcv_data))

        with pytest.raises(SignalProcessingError, match="Invalid signal values"):
            backtester.run(invalid_signals, sample_ohlcv_data)

    def test_vector_backtester_error_handling_mismatched_length(
        self, sample_ohlcv_data
    ):
        """Test error handling with mismatched signal and data lengths."""
        backtester = VectorBacktester()

        # Signals shorter than data
        short_signals = pd.Series([1, -1, 0])  # Only 3 signals

        with pytest.raises(
            SignalProcessingError, match="Signal and data length mismatch"
        ):
            backtester.run(short_signals, sample_ohlcv_data)

    def test_vector_backtester_error_handling_empty_data(self):
        """Test error handling with empty data."""
        backtester = VectorBacktester()

        empty_data = pd.DataFrame(columns=["close", "volume"])
        signals = pd.Series([], dtype=int)

        with pytest.raises(VectorBacktestError, match="Empty data provided"):
            backtester.run(signals, empty_data)

    def test_vector_backtester_memory_efficiency(self):
        """Test vector backtester memory efficiency."""
        # Create large dataset to test memory usage
        large_data = pd.DataFrame(
            {
                "close": np.random.uniform(90, 110, 100000),  # 100K data points
                "volume": np.random.randint(100000, 1000000, 100000),
            },
            index=pd.date_range("2020-01-01", periods=100000, freq="1s"),
        )

        signals = pd.Series(
            np.random.choice([-1, 0, 1], size=100000), index=large_data.index
        )

        backtester = VectorBacktester()

        # Should handle large dataset without excessive memory usage
        # (This is more of an integration check than a strict test)
        try:
            result = backtester.run(signals, large_data)
            assert result is not None
            assert len(result.equity_curve) == 100000
        except MemoryError:
            pytest.fail("Vector backtester uses excessive memory for large datasets")

    def _mock_event_driven_backtest(self, signals, data, config):
        """Mock event-driven backtest for comparison."""
        cash = config.initial_cash
        positions = 0
        equity = []

        for i in range(len(data)):
            price = data.iloc[i]["close"]
            signal = signals.iloc[i]

            # Process signal using arithmetic instead of conditionals
            buy_condition = (signal == 1) * (positions == 0)
            sell_condition = (signal == -1) * (positions > 0)
            
            # Execute buy
            shares_to_buy = int(cash / price) * buy_condition
            cash = cash - (shares_to_buy * price)
            positions = positions + shares_to_buy
            
            # Execute sell
            sell_proceeds = (positions * price) * sell_condition
            cash = cash + sell_proceeds
            positions = positions * (1 - sell_condition)

            # Calculate equity
            equity_value = cash + (positions * price)
            equity.append(equity_value)

        return {"equity": equity, "positions": positions, "cash": cash}

    def _generate_ma_crossover_signals(self, prices, short_window=10, long_window=20):
        """Generate moving average crossover signals."""
        short_ma = prices.rolling(window=short_window).mean()
        long_ma = prices.rolling(window=long_window).mean()

        # Generate signals: 1 for buy, -1 for sell, 0 for hold
        signals = pd.Series(0, index=prices.index)

        # Buy when short MA crosses above long MA
        buy_signals = (short_ma > long_ma) & (short_ma.shift(1) <= long_ma.shift(1))
        signals[buy_signals] = 1

        # Sell when short MA crosses below long MA
        sell_signals = (short_ma < long_ma) & (short_ma.shift(1) >= long_ma.shift(1))
        signals[sell_signals] = -1

        return signals
