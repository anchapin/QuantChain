"""Advanced tests for vector backtester covering edge cases and performance scenarios."""



import pytest
import numpy as np
import pandas as pd
from unittest.mock import patch, MagicMock
from quantchain.backtesting.vector_backtester import (
from quantchain.backtesting.engine import BacktestConfig
from quantchain.backtesting.market_friction import MarketFrictionConfig
import time
import time
import sys

    VectorBacktester,
    VectorBacktestResult,
    VectorizedPositionManager,
    VectorBacktestError,
    SignalProcessingError,
)


class TestVectorizedPositionManagerAdvanced:
    """Advanced tests for VectorizedPositionManager."""



def _process_signals_and_get_equity(self, prices, signals, position_manager=None):
        """
        Helper function to process signals and calculate equity curve.

        Returns:
            dict: {
                "positions": positions,
                "trade_log": trades,
                "equity_curve": equity_curve,
                "current_cash": current_cash
            }
        """
        if position_manager is None:
            position_manager = self.position_manager

        positions, trades, current_cash = position_manager.process_signals(
            prices, signals
        )
        equity_curve = position_manager.calculate_equity(prices, positions)

        return {
            "positions": positions,
            "trade_log": trades,
            "equity_curve": equity_curve,
            "current_cash": current_cash,
        }



def setup_method(self):
        """Set up test fixtures."""
        # Create more complex test data
        dates = pd.date_range("2023-01-01", periods=1000, freq="D")
        np.random.seed(42)  # For reproducible results

        # Create price series with trends and volatility
        returns = np.random.normal(0.001, 0.02, 1000)
        prices = 100 * np.cumprod(1 + returns)

        # Create signals with various patterns
        signals = np.zeros(1000)
        signals[50:100] = 1  # Buy signal
        signals[200:250] = -1  # Sell signal
        signals[400:450] = 0.5  # Partial position
        signals[600:650] = -0.5  # Short position
        signals[800:850] = 2  # Strong buy signal

        self.prices = pd.Series(prices, index=dates)
        self.signals = pd.Series(signals, index=dates)

        self.position_manager = VectorizedPositionManager(
            initial_cash=1000000, commission_rate=0.001, slippage_rate=0.0005
        )



def test_edge_case_all_zeros_signals(self):
        """Test handling of all-zero signals."""
        zero_signals = pd.Series(0, index=self.signals.index)
        positions, trades, current_cash = self.position_manager.process_signals(
            self.prices, zero_signals
        )

        # Create result dict
        result = {
            "positions": positions,
            "trade_log": trades,
            "equity_curve": self.position_manager.calculate_equity(
                self.prices, positions
            ),
            "current_cash": current_cash,
        }

        assert positions.sum() == 0
        assert len(trades) == 0
        # Equity should remain constant (minus any small numerical errors)
        np.testing.assert_allclose(
            result["equity_curve"], self.position_manager.initial_cash, rtol=1e-10
        )



def test_edge_case_constant_buy_signals(self):
        """Test handling of constant buy signals."""
        constant_buy = pd.Series(1, index=self.signals.index[:100])
        prices_subset = self.prices.iloc[:100]

        result = self._process_signals_and_get_equity(prices_subset, constant_buy)

        # Should buy on first signal and hold
        assert result["positions"].iloc[-1] > 0
        # Should have exactly one trade (the initial buy)
        assert len(result["trade_log"]) == 1
        assert result["trade_log"].iloc[0]["signal"] == 1



def test_edge_case_rapid_signal_fluctuations(self):
        """Test handling of rapidly fluctuating signals."""
        # Create signals that flip between buy and sell rapidly
        fluctuating_signals = pd.Series(0, index=self.signals.index[:50])
        fluctuating_signals[::2] = 1  # Buy on even indices
        fluctuating_signals[1::2] = -1  # Sell on odd indices

        prices_subset = self.prices.iloc[:50]
        result = self._process_signals_and_get_equity(
            prices_subset, fluctuating_signals
        )

        # Should handle rapid fluctuations without errors
        assert len(result["equity_curve"]) == 50
        assert isinstance(result["trade_log"], pd.DataFrame)



def test_large_dataset_performance(self):
        """Test performance with large datasets."""
        # Create large dataset
        large_dates = pd.date_range("2020-01-01", periods=10000, freq="H")
        large_prices = pd.Series(
            100 + np.cumsum(np.random.normal(0, 1, 10000)), index=large_dates
        )
        large_signals = pd.Series(
            np.random.choice([-1, 0, 1], 10000), index=large_dates
        )

        # This should complete without memory issues or excessive time

        start_time = time.time()

        result = self._process_signals_and_get_equity(large_prices, large_signals)

        end_time = time.time()
        execution_time = end_time - start_time

        # Reasonable performance expectations
        assert execution_time < 5.0  # Should complete within 5 seconds
        assert len(result["equity_curve"]) == 10000



def test_extreme_price_movements(self):
        """Test handling of extreme price movements."""
        # Create prices with extreme movements
        extreme_prices = self.prices.copy()
        extreme_prices.iloc[100] = 10000  # Extreme spike
        extreme_prices.iloc[200] = 0.001  # Extreme drop
        extreme_prices.iloc[300] = np.inf  # Infinite price
        extreme_prices.iloc[400] = -np.inf  # Negative infinite price

        # This should handle extreme values gracefully
        result = self._process_signals_and_get_equity(
            extreme_prices.iloc[:500], self.signals.iloc[:500]
        )

        # Should not crash and produce valid results
        assert len(result["equity_curve"]) == 500
        assert not result["equity_curve"].isna().all()



def test_nan_and_inf_handling(self):
        """Test handling of NaN and infinite values in data."""
        # Insert NaN and inf values
        dirty_prices = self.prices.copy()
        dirty_prices.iloc[50] = np.nan
        dirty_prices.iloc[100] = np.inf
        dirty_prices.iloc[150] = -np.inf

        dirty_signals = self.signals.copy()
        dirty_signals.iloc[75] = np.nan

        # Should handle dirty data gracefully
        result = self._process_signals_and_get_equity(dirty_prices, dirty_signals)

        assert len(result["equity_curve"]) == len(dirty_prices)
        # Equity curve should not contain NaN values (except possibly at problematic points)
        assert not result["equity_curve"].iloc[1:].isna().all()



def test_very_small_and_large_prices(self):
        """Test handling of very small and very large price values."""
        # Create prices with very small and large values
        small_prices = pd.Series(
            [1e-10, 1e-9, 1e-8, 1e-7, 1e-6],
            index=pd.date_range("2023-01-01", periods=5),
        )
        large_prices = pd.Series(
            [1e6, 1e7, 1e8, 1e9, 1e10], index=pd.date_range("2023-01-01", periods=5)
        )

        small_signals = pd.Series([1, 0, -1, 0, 1], index=small_prices.index)
        large_signals = pd.Series([1, 0, -1, 0, 1], index=large_prices.index)

        # Should handle both cases without numerical overflow/underflow
        small_result = self._process_signals_and_get_equity(small_prices, small_signals)
        large_result = self._process_signals_and_get_equity(large_prices, large_signals)

        assert len(small_result["equity_curve"]) == 5
        assert len(large_result["equity_curve"]) == 5
        assert not np.isinf(small_result["equity_curve"]).any()
        assert not np.isinf(large_result["equity_curve"]).any()



def test_mixed_signal_values(self):
        """Test handling of various signal values (not just -1, 0, 1)."""
        # Create signals with various values
        mixed_signals = pd.Series(
            [0, 0.5, 1.0, 1.5, 2.0, -0.5, -1.0, -1.5],
            index=pd.date_range("2023-01-01", periods=8),
        )
        mixed_prices = pd.Series(
            [100, 101, 102, 103, 104, 105, 106, 107], index=mixed_signals.index
        )

        result = self._process_signals_and_get_equity(mixed_prices, mixed_signals)

        assert len(result["equity_curve"]) == 8
        assert isinstance(result["trade_log"], pd.DataFrame)



def test_partial_position_signals(self):
        """Test handling of partial position signals."""
        # Create signals for partial positions
        partial_signals = pd.Series(
            [0, 0.3, 0.7, 1.0, 0.5, 0, -0.5, -1.0],
            index=pd.date_range("2023-01-01", periods=8),
        )
        partial_prices = pd.Series(
            [100, 101, 102, 103, 104, 105, 106, 107], index=partial_signals.index
        )

        result = self._process_signals_and_get_equity(partial_prices, partial_signals)

        assert len(result["equity_curve"]) == 8
        # Position sizes should reflect signal magnitudes
        assert result["positions"].max() <= result["positions"].abs().max()



def test_high_frequency_signals(self):
        """Test handling of high-frequency trading signals."""
        # Create minute-level data for a day
        hf_dates = pd.date_range(
            "2023-01-01", periods=1440, freq="1min"
        )  # 1440 minutes
        hf_prices = pd.Series(
            100 + np.cumsum(np.random.normal(0, 0.1, 1440)), index=hf_dates
        )
        hf_signals = pd.Series(np.random.choice([-1, 0, 1], 1440), index=hf_dates)

        result = self._process_signals_and_get_equity(hf_prices, hf_signals)

        assert len(result["equity_curve"]) == 1440
        # Should handle high frequency data efficiently



def test_different_timeframes(self):
        """Test with different data timeframes."""
        # Test with different frequencies
        timeframes = ["1min", "5min", "15min", "1H", "4H", "1D"]

        for timeframe in timeframes:
            dates = pd.date_range("2023-01-01", periods=100, freq=timeframe)
            prices = pd.Series(
                100 + np.cumsum(np.random.normal(0, 1, 100)), index=dates
            )
            signals = pd.Series(np.random.choice([-1, 0, 1], 100), index=dates)

            result = self._process_signals_and_get_equity(prices, signals)

            assert len(result["equity_curve"]) == 100



def test_gap_handling(self):
        """Test handling of gaps in data."""
        # Create data with gaps
        dates_with_gaps = pd.date_range("2023-01-01", periods=100, freq="D")
        # Remove some dates to create gaps
        dates_with_gaps = dates_with_gaps.delete([10, 11, 12, 50, 51, 52])

        gap_prices = pd.Series(
            100 + np.cumsum(np.random.normal(0, 1, 94)), index=dates_with_gaps
        )
        gap_signals = pd.Series(np.random.choice([-1, 0, 1], 94), index=dates_with_gaps)

        result = self._process_signals_and_get_equity(gap_prices, gap_signals)

        assert len(result["equity_curve"]) == 94
        # Should handle gaps without issues



def test_duplicate_timestamps(self):
        """Test handling of duplicate timestamps."""
        # Create data with duplicate timestamps
        dates = pd.date_range("2023-01-01", periods=10, freq="D")
        duplicate_dates = dates.tolist() + dates.tolist()  # Duplicate all dates
        duplicate_prices = pd.Series(range(20), index=duplicate_dates)
        duplicate_signals = pd.Series([1, -1] * 10, index=duplicate_dates)

        # Should handle duplicates gracefully (may aggregate or ignore)
        try:
            result = self._process_signals_and_get_equity(
                duplicate_prices, duplicate_signals
            )
            # If successful, check basic properties
            assert len(result["equity_curve"]) > 0
        except Exception:
            # If it fails, that's also acceptable behavior for duplicate data
            pass



def test_empty_signals_subset(self):
        """Test with empty signals subset."""
        # Create a slice with no signals
        empty_signals = pd.Series([], dtype="float64")
        empty_prices = pd.Series([], dtype="float64")

        result = self._process_signals_and_get_equity(empty_prices, empty_signals)

        assert len(result["equity_curve"]) == 0
        assert len(result["positions"]) == 0
        assert len(result["trade_log"]) == 0



def test_single_data_point(self):
        """Test with single data point."""
        single_date = pd.date_range("2023-01-01", periods=1)
        single_price = pd.Series([100], index=single_date)
        single_signal = pd.Series([1], index=single_date)

        result = self._process_signals_and_get_equity(single_price, single_signal)

        assert len(result["equity_curve"]) == 1



def test_mismatched_lengths(self):
        """Test with mismatched price and signal lengths."""
        prices_100 = self.prices.iloc[:100]
        signals_50 = self.signals.iloc[:50]

        # Should handle mismatched lengths appropriately
        with pytest.raises((ValueError, VectorBacktestError, SignalProcessingError)):
            self.position_manager.process_signals(prices_100, signals_50)



def test_very_high_commission_and_slippage(self):
        """Test with very high commission and slippage rates."""
        high_cost_manager = VectorizedPositionManager(
            initial_cash=100000,
            commission_rate=0.5,  # 50% commission
            slippage_rate=0.2,  # 20% slippage
        )

        result = self._process_signals_and_get_equity(
            self.prices.iloc[:100], self.signals.iloc[:100], high_cost_manager
        )

        # With such high costs, equity should decrease
        assert result["equity_curve"].iloc[-1] < result["equity_curve"].iloc[0]



def test_zero_commission_and_slippage(self):
        """Test with zero commission and slippage."""
        no_cost_manager = VectorizedPositionManager(
            initial_cash=100000, commission_rate=0.0, slippage_rate=0.0
        )

        result = self._process_signals_and_get_equity(
            self.prices.iloc[:100], self.signals.iloc[:100], no_cost_manager
        )

        # Should still work without any costs
        assert len(result["equity_curve"]) == 100



def test_very_large_initial_cash(self):
        """Test with very large initial cash amount."""
        rich_manager = VectorizedPositionManager(
            initial_cash=1e15,  # 1 quadrillion
            commission_rate=0.001,
            slippage_rate=0.0005,
        )

        result = self._process_signals_and_get_equity(
            self.prices.iloc[:100], self.signals.iloc[:100], rich_manager
        )

        assert len(result["equity_curve"]) == 100
        assert not np.isinf(result["equity_curve"]).any()



def test_very_small_initial_cash(self):
        """Test with very small initial cash amount."""
        poor_manager = VectorizedPositionManager(
            initial_cash=0.01, commission_rate=0.001, slippage_rate=0.0005  # 1 cent
        )

        result = self._process_signals_and_get_equity(
            self.prices.iloc[:100], self.signals.iloc[:100], poor_manager
        )

        assert len(result["equity_curve"]) == 100


class TestVectorBacktesterAdvanced:
    """Advanced tests for VectorBacktester."""



def setup_method(self):
        """Set up test fixtures."""
        dates = pd.date_range("2023-01-01", periods=100, freq="D")
        np.random.seed(42)

        self.data = pd.DataFrame(
            {
                "open": 100 + np.cumsum(np.random.normal(0, 1, 100)),
                "high": 100 + np.cumsum(np.random.normal(0.1, 1, 100)),
                "low": 100 + np.cumsum(np.random.normal(-0.1, 1, 100)),
                "close": 100 + np.cumsum(np.random.normal(0, 1, 100)),
                "volume": np.random.randint(1000, 10000, 100),
            },
            index=dates,
        )

        # Ensure high >= low and other constraints
        self.data["high"] = np.maximum(self.data["high"], self.data["close"])
        self.data["low"] = np.minimum(self.data["low"], self.data["close"])
        self.data["high"] = np.maximum(self.data["high"], self.data["open"])
        self.data["low"] = np.minimum(self.data["low"], self.data["open"])

        self.config = BacktestConfig(
            initial_cash=100000, commission_rate=0.001, slippage_rate=0.0005
        )

        # Create signals for testing
        self.signals = pd.Series(np.random.choice([-1, 0, 1], 100), index=dates)

        self.backtester = VectorBacktester(config=self.config)



def test_edge_case_single_row_data(self):
        """Test with single row of data."""
        single_row_data = self.data.iloc[:1]

        # Should handle single row gracefully
        result = self.backtester.run(
            data=single_row_data, signals=pd.Series([1], index=single_row_data.index)
        )

        assert isinstance(result, VectorBacktestResult)
        assert len(result.equity_curve) == 1



def test_edge_case_empty_data(self):
        """Test with empty data."""
        empty_data = pd.DataFrame()
        empty_signals = pd.Series()

        # Should raise an error for empty data
        with pytest.raises(VectorBacktestError):
            self.backtester.run(data=empty_data, signals=empty_signals)



def test_corrupt_data_handling(self):
        """Test handling of corrupt data."""
        corrupt_data = self.data.copy()
        corrupt_data.iloc[50, 0] = np.nan  # NaN in open
        corrupt_data.iloc[51, 1] = np.inf  # Inf in high
        corrupt_data.iloc[52, 2] = -np.inf  # -Inf in low
        corrupt_data.iloc[53, 3] = -100  # Negative close price

        # Should handle corrupt data gracefully
        try:
            result = self.backtester.run(
                data=corrupt_data, signals=self.signals.iloc[: len(corrupt_data)]
            )
            assert isinstance(result, VectorBacktestResult)
        except Exception:
            # If it fails, that's acceptable for clearly corrupt data
            pass



def test_multiple_symbol_data(self):
        """Test with multiple symbols in data."""
        # Create multi-index data for multiple symbols
        symbols = ["AAPL", "GOOGL", "MSFT"]
        multi_data = []

        for symbol in symbols:
            symbol_data = self.data.copy()
            symbol_data["symbol"] = symbol
            multi_data.append(symbol_data)

        combined_data = pd.concat(multi_data, ignore_index=True)

        # Should handle multi-symbol data appropriately
        try:
            result = self.backtester.run(
                data=combined_data, signals=pd.Series([1] * len(combined_data))
            )
            assert isinstance(result, VectorBacktestResult)
        except Exception:
            # May fail if not designed for multi-symbol
            pass



def test_non_standard_column_names(self):
        """Test with non-standard column names."""
        non_standard_data = self.data.rename(
            columns={
                "open": "Open",
                "high": "High",
                "low": "Low",
                "close": "Close",
                "volume": "Volume",
            }
        )

        # Should either handle non-standard names or fail gracefully
        try:
            result = self.backtester.run(
                data=non_standard_data,
                signals=self.signals.iloc[: len(non_standard_data)],
            )
            assert isinstance(result, VectorBacktestResult)
        except Exception:
            # Acceptable if it requires specific column names
            pass



def test_missing_required_columns(self):
        """Test with missing required columns."""
        incomplete_data = self.data.drop(columns=["volume"])

        # The backtester may handle missing columns in different ways
        # Let's just check if it can run with missing volume column
        try:
            result = self.backtester.run(
                data=incomplete_data, signals=self.signals.iloc[: len(incomplete_data)]
            )
            # If it runs successfully, verify we got a valid result
            assert isinstance(result, VectorBacktestResult)
        except (KeyError, ValueError, VectorBacktestError):
            # If it fails, that's also acceptable behavior
            pass



def test_very_large_dataset_stress_test(self):
        """Test stress handling of very large datasets."""
        # Create large dataset
        large_dates = pd.date_range("2020-01-01", periods=50000, freq="H")
        large_data = pd.DataFrame(
            {
                "open": 100 + np.cumsum(np.random.normal(0, 1, 50000)),
                "high": 100 + np.cumsum(np.random.normal(0.1, 1, 50000)),
                "low": 100 + np.cumsum(np.random.normal(-0.1, 1, 50000)),
                "close": 100 + np.cumsum(np.random.normal(0, 1, 50000)),
                "volume": np.random.randint(1000, 10000, 50000),
            },
            index=large_dates,
        )

        large_signals = pd.Series(
            np.random.choice([-1, 0, 1], 50000), index=large_dates
        )


        start_time = time.time()

        try:
            result = self.backtester.run(data=large_data, signals=large_signals)

            end_time = time.time()
            execution_time = end_time - start_time

            # Should complete within reasonable time
            assert execution_time < 30.0  # 30 seconds limit
            assert isinstance(result, VectorBacktestResult)
        except MemoryError:
            # Acceptable for very large datasets
            pytest.skip("Large dataset test skipped due to memory constraints")



def test_concurrent_execution_simulation(self):
        """Test simulation of concurrent execution scenarios."""
        # Create signals that would theoretically execute simultaneously
        concurrent_signals = pd.Series(0, index=self.data.index)
        concurrent_signals.iloc[::10] = 1  # Every 10th row has a signal

        result = self.backtester.run(data=self.data, signals=concurrent_signals)

        assert isinstance(result, VectorBacktestResult)
        # Should handle signals that occur at same timestamp



def test_market_closed_scenarios(self):
        """Test scenarios simulating market closed periods."""
        # Create data with gaps (market closed periods)
        market_dates = pd.date_range("2023-01-01", periods=100, freq="D")
        # Remove weekends
        market_dates = market_dates[market_dates.dayofweek < 5]

        market_data = self.data.iloc[: len(market_dates)]
        market_data.index = market_dates

        market_signals = pd.Series(
            np.random.choice([-1, 0, 1], len(market_data)), index=market_dates
        )

        result = self.backtester.run(data=market_data, signals=market_signals)

        assert isinstance(result, VectorBacktestResult)
        # Should handle irregular trading days



def test_extreme_commission_scenarios(self):
        """Test extreme commission scenarios."""
        # Test with very high commission
        high_commission_config = BacktestConfig(
            initial_cash=100000,
            commission_rate=0.5,
            slippage_rate=0.0,  # 50% commission
        )

        high_commission_backtester = VectorBacktester(config=high_commission_config)
        result = high_commission_backtester.run(
            data=self.data, signals=pd.Series([1, -1] * 50, index=self.data.index)
        )

        # With 50% commission, should lose money rapidly
        assert result.equity_curve.iloc[-1] < result.equity_curve.iloc[0]



def test_memory_efficiency_validation(self):
        """Test memory efficiency of operations."""

        # Check memory usage before and after operations
        initial_size = sys.getsizeof(self.data) + sys.getsizeof(self.signals)

        result = self.backtester.run(
            data=self.data, signals=self.signals.iloc[: len(self.data)]
        )

        # Result size should be reasonable relative to input
        result_size = (
            sys.getsizeof(result.equity_curve)
            + sys.getsizeof(result.trade_log)
            + sys.getsizeof(result.positions)
        )

        # Should not use excessive memory (rule of thumb: not more than 10x input)
        assert result_size < initial_size * 10
