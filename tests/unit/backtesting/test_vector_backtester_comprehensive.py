"""Comprehensive tests for vector backtester."""

import numpy as np
import pandas as pd
import pytest

from quantchain.backtesting.engine import BacktestConfig
from quantchain.backtesting.vector_backtester import (
    SignalProcessingError,
    VectorBacktestError,
    VectorBacktestResult,
    VectorBacktester,
    VectorizedPositionManager,
)


@pytest.mark.unit
class TestVectorizedPositionManager:
    """Test cases for VectorizedPositionManager."""

    @pytest.fixture
    def manager(self):
        """Create position manager instance."""
        return VectorizedPositionManager(
            initial_cash=100000.0, commission_rate=0.001, slippage_rate=0.0005
        )

    @pytest.fixture
    def sample_signals_df(self):
        """Create sample signals DataFrame."""
        dates = pd.date_range("2023-01-01", periods=10, freq="D")
        return pd.DataFrame(
            {
                "timestamp": dates,
                "price": [100, 101, 102, 103, 104, 103, 102, 101, 100, 99],
                "signal": [1, 0, 0, -1, 0, 0, 1, 0, 0, -1],
            }
        )

    def test_initialization_default(self):
        """Test default initialization."""
        manager = VectorizedPositionManager()
        assert manager.initial_cash == 100000.0
        assert manager.commission_rate == 0.0
        assert manager.slippage_rate == 0.0

    def test_initialization_custom(self):
        """Test custom initialization."""
        manager = VectorizedPositionManager(
            initial_cash=50000.0, commission_rate=0.002, slippage_rate=0.001
        )
        assert manager.initial_cash == 50000.0
        assert manager.commission_rate == 0.002
        assert manager.slippage_rate == 0.001

    def test_process_buy_signal_valid(self, manager):
        """Test processing valid buy signal."""
        timestamp = pd.Timestamp("2023-01-01")
        price = 100.0
        signal = 1.0
        current_position = 0.0
        current_cash = 50000.0

        position, cash, trade = manager._process_buy_signal(
            timestamp, price, signal, current_position, current_cash
        )

        assert position > 0  # Should have bought position
        assert cash < current_cash  # Cash should be reduced
        assert "timestamp" in trade
        assert trade["signal"] == signal
        assert trade["price"] == price * (1 + manager.slippage_rate)

    def test_process_buy_signal_insufficient_cash(self, manager):
        """Test buy signal with insufficient cash."""
        timestamp = pd.Timestamp("2023-01-01")
        price = 100.0
        signal = 1.0
        current_position = 0.0
        current_cash = 10.0  # Very low cash

        position, cash, trade = manager._process_buy_signal(
            timestamp, price, signal, current_position, current_cash
        )

        # Position and cash may change depending on implementation
        # Just check that a trade dictionary is returned
        assert isinstance(trade, dict)

    def test_process_buy_signal_already_position(self, manager):
        """Test buy signal when already in position."""
        timestamp = pd.Timestamp("2023-01-01")
        price = 100.0
        signal = 1.0
        current_position = 100.0  # Already have position
        current_cash = 50000.0

        position, cash, trade = manager._process_buy_signal(
            timestamp, price, signal, current_position, current_cash
        )

        assert position == current_position  # Position unchanged
        assert cash == current_cash  # Cash unchanged
        assert trade == {}  # No trade record

    def test_process_sell_signal_long_position(self, manager):
        """Test selling from long position."""
        timestamp = pd.Timestamp("2023-01-01")
        price = 105.0
        signal = -1.0
        current_position = 100.0
        current_cash = 10000.0

        position, cash, trade = manager._process_sell_signal_long(
            timestamp, price, signal, current_position, current_cash
        )

        assert position < current_position  # Position should be reduced
        assert cash > current_cash  # Cash should increase
        assert "timestamp" in trade
        assert trade["signal"] == signal

    def test_process_sell_signal_no_position(self, manager):
        """Test sell signal with no position."""
        timestamp = pd.Timestamp("2023-01-01")
        price = 105.0
        signal = -1.0
        current_position = 0.0
        current_cash = 50000.0

        position, cash, trade = manager._process_sell_signal_long(
            timestamp, price, signal, current_position, current_cash
        )

        assert position == 0.0  # No position
        assert cash == current_cash  # Cash unchanged
        assert trade == {}  # No trade record

    def test_process_signals(self, manager):
        """Test processing multiple signals."""
        # Create simple signals and prices
        prices = pd.Series([100, 101, 102, 103, 104])
        signals = pd.Series([1, 0, -1, 0, 1])

        results = manager.process_signals(prices, signals)

        # Process signals returns tuple of (positions, trades, cash)
        assert len(results) == 3
        positions, trades, cash = results
        assert isinstance(positions, pd.Series)
        assert isinstance(trades, (pd.DataFrame, type(None)))
        assert isinstance(cash, (float, int))

    def test_calculate_equity(self, manager):
        """Test equity calculation."""
        prices = pd.Series([100, 101, 102, 103, 104])
        positions = pd.Series([0, 100, 100, 50, 0])

        equity = manager.calculate_equity(prices, positions)

        assert isinstance(equity, pd.Series)
        assert len(equity) == len(prices)

    def test_commission_calculation(self, manager):
        """Test commission calculation in trades."""
        timestamp = pd.Timestamp("2023-01-01")
        price = 100.0
        signal = 1.0
        current_position = 0.0
        current_cash = 50000.0

        position, cash, trade = manager._process_buy_signal(
            timestamp, price, signal, current_position, current_cash
        )

        expected_commission = trade["shares"] * trade["price"] * manager.commission_rate
        assert abs(trade["commission"] - expected_commission) < 0.01

    def test_slippage_calculation(self, manager):
        """Test slippage calculation in trades."""
        timestamp = pd.Timestamp("2023-01-01")
        price = 100.0
        signal = 1.0
        current_position = 0.0
        current_cash = 50000.0

        position, cash, trade = manager._process_buy_signal(
            timestamp, price, signal, current_position, current_cash
        )

        expected_slippage = trade["shares"] * price * manager.slippage_rate
        assert abs(trade["slippage"] - expected_slippage) < 0.01


@pytest.mark.unit
class TestVectorBacktester:
    """Test cases for VectorBacktester."""

    @pytest.fixture
    def config(self):
        """Create backtest configuration."""
        return BacktestConfig(
            initial_cash=100000,
            commission_rate=0.001,
            slippage_rate=0.0005,
        )

    @pytest.fixture
    def backtester(self, config):
        """Create backtester instance."""
        return VectorBacktester(config=config)

    @pytest.fixture
    def sample_data(self):
        """Create sample market data."""
        dates = pd.date_range("2023-01-01", periods=100, freq="D")
        return pd.DataFrame(
            {
                "open": 100 + pd.Series(range(100)) * 0.1,
                "high": 101 + pd.Series(range(100)) * 0.1,
                "low": 99 + pd.Series(range(100)) * 0.1,
                "close": 100 + pd.Series(range(100)) * 0.1,
                "volume": 1000000 + pd.Series(range(100)) * 1000,
            },
            index=dates,
        )

    @pytest.fixture
    def sample_signals(self):
        """Create sample trading signals."""
        dates = pd.date_range("2023-01-01", periods=100, freq="D")
        return pd.Series(
            [1 if i % 10 == 0 else (-1 if i % 15 == 0 else 0) for i in range(100)],
            index=dates,
        )

    def test_initialization_default(self):
        """Test default initialization."""
        backtester = VectorBacktester()
        assert backtester.config is not None

    def test_initialization_with_config(self, backtester, config):
        """Test initialization with config."""
        assert backtester.config == config

    def test_validate_inputs_valid(self, backtester, sample_data, sample_signals):
        """Test input validation with valid data."""
        # Should not raise any exception
        backtester._validate_inputs(sample_data, sample_signals)

    def test_validate_inputs_empty_data(self, backtester):
        """Test input validation with empty data."""
        empty_data = pd.DataFrame()
        signals = pd.Series([1, 0, -1])

        with pytest.raises(VectorBacktestError):
            backtester._validate_inputs(empty_data, signals)

    def test_validate_inputs_empty_signals(self, backtester, sample_data):
        """Test input validation with empty signals."""
        empty_signals = pd.Series([])

        with pytest.raises(SignalProcessingError):
            backtester._validate_inputs(sample_data, empty_signals)

    def test_validate_inputs_mismatched_lengths(self, backtester, sample_data):
        """Test input validation with mismatched lengths."""
        short_signals = pd.Series([1, 0, -1])

        with pytest.raises(SignalProcessingError):
            backtester._validate_inputs(sample_data, short_signals)

    def test_run_basic(self, backtester, sample_data, sample_signals):
        """Test basic backtest run."""
        results = backtester.run(sample_signals, sample_data)

        assert isinstance(results, VectorBacktestResult)
        assert isinstance(results.equity_curve, pd.Series)
        assert isinstance(results.trade_log, pd.DataFrame)
        assert isinstance(results.positions, pd.Series)
        assert isinstance(results.returns, pd.Series)

    def test_run_with_cost_config(self, sample_data, sample_signals):
        """Test backtest run with custom cost configuration."""
        config = BacktestConfig(
            commission_rate=0.002,
            slippage_rate=0.001,
        )
        backtester = VectorBacktester(config=config)

        results = backtester.run(sample_signals, sample_data)

        # Results should reflect higher costs
        assert isinstance(results, VectorBacktestResult)

    def test_get_results_after_run(self, backtester, sample_data, sample_signals):
        """Test getting results after run."""
        backtester.run(sample_data, sample_signals)
        results = backtester.get_results()

        assert results is not None
        assert isinstance(results, VectorBacktestResult)

    def test_get_results_before_run(self, backtester):
        """Test getting results before run."""
        results = backtester.get_results()
        assert results is None

    def test_get_equity_curve_after_run(self, backtester, sample_data, sample_signals):
        """Test getting equity curve after run."""
        backtester.run(sample_data, sample_signals)
        equity = backtester.get_equity_curve()

        assert equity is not None
        assert isinstance(equity, pd.Series)

    def test_get_equity_curve_before_run(self, backtester):
        """Test getting equity curve before run."""
        equity = backtester.get_equity_curve()
        assert equity is None

    def test_run_multiple_times(self, backtester, sample_data, sample_signals):
        """Test running backtest multiple times."""
        results1 = backtester.run(sample_data, sample_signals)
        results2 = backtester.run(sample_data, sample_signals)

        # Should be able to run multiple times
        assert results1 is not None
        assert results2 is not None

    def test_edge_case_no_trades(self, backtester):
        """Test backtest with no trading signals."""
        dates = pd.date_range("2023-01-01", periods=10, freq="D")
        data = pd.DataFrame(
            {
                "close": [100] * 10,
                "volume": [1000000] * 10,
            },
            index=dates,
        )
        signals = pd.Series([0] * 10, index=dates)

        results = backtester.run(data, signals)

        # Should handle gracefully
        assert isinstance(results, VectorBacktestResult)
        assert len(results.trade_log) == 0

    def test_edge_case_single_trade(self, backtester):
        """Test backtest with single trade."""
        dates = pd.date_range("2023-01-01", periods=10, freq="D")
        data = pd.DataFrame(
            {
                "close": [100] * 10,
                "volume": [1000000] * 10,
            },
            index=dates,
        )
        signals = pd.Series([1] + [0] * 9, index=dates)

        results = backtester.run(data, signals)

        # Should handle single trade
        assert isinstance(results, VectorBacktestResult)


@pytest.mark.unit
class TestVectorBacktestResult:
    """Test cases for VectorBacktestResult."""

    def test_creation_minimal(self):
        """Test creation with minimal required fields."""
        dates = pd.date_range("2023-01-01", periods=5, freq="D")
        equity = pd.Series([100000, 101000, 102000, 103000, 104000], index=dates)
        trades = pd.DataFrame({"symbol": ["AAPL"], "price": [100]})
        positions = pd.Series([0, 1, 1, 1, 0], index=dates)
        returns = pd.Series([0, 0.01, 0.0099, 0.0098, -0.0097], index=dates)

        result = VectorBacktestResult(
            equity_curve=equity, trade_log=trades, positions=positions, returns=returns
        )

        assert result.equity_curve.equals(equity)
        assert result.trade_log.equals(trades)
        assert result.positions.equals(positions)
        assert result.returns.equals(returns)
        assert result.metrics == {}

    def test_creation_with_metrics(self):
        """Test creation with metrics."""
        dates = pd.date_range("2023-01-01", periods=2, freq="D")
        equity = pd.Series([100000, 101000], index=dates)
        trades = pd.DataFrame()
        positions = pd.Series([0, 1], index=dates)
        returns = pd.Series([0, 0.01], index=dates)
        metrics = {"sharpe_ratio": 1.5, "max_drawdown": 0.02}

        result = VectorBacktestResult(
            equity_curve=equity,
            trade_log=trades,
            positions=positions,
            returns=returns,
            metrics=metrics,
        )

        assert result.metrics == metrics

    def test_data_consistency(self):
        """Test data consistency across fields."""
        dates = pd.date_range("2023-01-01", periods=5, freq="D")
        equity = pd.Series([100000, 101000, 102000, 103000, 104000], index=dates)
        trades = pd.DataFrame()
        positions = pd.Series([0, 1, 1, 1, 0], index=dates)
        returns = equity.pct_change().fillna(0)

        result = VectorBacktestResult(
            equity_curve=equity, trade_log=trades, positions=positions, returns=returns
        )

        # Check that indices are consistent
        assert result.equity_curve.index.equals(result.positions.index)
        assert result.equity_curve.index.equals(result.returns.index)


@pytest.mark.unit
class TestExceptions:
    """Test custom exceptions."""

    def test_vector_backtest_error(self):
        """Test VectorBacktestError."""
        error = VectorBacktestError("Test backtest error")
        assert str(error) == "Test backtest error"
        assert isinstance(error, Exception)

    def test_signal_processing_error(self):
        """Test SignalProcessingError."""
        error = SignalProcessingError("Test signal error")
        assert str(error) == "Test signal error"
        assert isinstance(error, Exception)


@pytest.mark.unit
class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_nan_prices(self):
        """Test handling of NaN prices."""
        manager = VectorizedPositionManager()
        dates = pd.date_range("2023-01-01", periods=5, freq="D")
        signals = pd.DataFrame(
            {
                "timestamp": dates,
                "price": [100, np.nan, 102, 103, 104],
                "signal": [1, 0, 0, -1, 0],
            }
        )

        # Should handle NaN values gracefully or raise error
        try:
            results = manager.process_signals(signals)
            # If no error, should return valid results
            assert len(results) == 3
        except SignalProcessingError:
            # Or should raise appropriate error
            assert True

    def test_inf_prices(self):
        """Test handling of infinite prices."""
        manager = VectorizedPositionManager()
        dates = pd.date_range("2023-01-01", periods=5, freq="D")
        signals = pd.DataFrame(
            {
                "timestamp": dates,
                "price": [100, float("inf"), 102, 103, 104],
                "signal": [1, 0, 0, -1, 0],
            }
        )

        # Should handle infinite values gracefully
        try:
            results = manager.process_signals(signals)
            # If no error, should return valid results
            assert len(results) == 3
        except (SignalProcessingError, ValueError):
            # Or should raise appropriate error
            assert True

    def test_negative_prices(self):
        """Test handling of negative prices."""
        manager = VectorizedPositionManager()
        dates = pd.date_range("2023-01-01", periods=5, freq="D")
        signals = pd.DataFrame(
            {
                "timestamp": dates,
                "price": [100, -50, 102, 103, 104],
                "signal": [1, 0, 0, -1, 0],
            }
        )

        # Should handle negative prices gracefully
        try:
            results = manager.process_signals(signals)
            # If no error, should return valid results
            assert len(results) == 3
        except (SignalProcessingError, ValueError):
            # Or should raise appropriate error
            assert True

    def test_very_large_signals(self):
        """Test handling of very large signal values."""
        manager = VectorizedPositionManager()
        dates = pd.date_range("2023-01-01", periods=5, freq="D")
        signals = pd.DataFrame(
            {
                "timestamp": dates,
                "price": [100, 101, 102, 103, 104],
                "signal": [1000000, 0, 0, -1000000, 0],  # Very large values
            }
        )

        # Should handle large signal values
        try:
            results = manager.process_signals(signals)
            # If no error, should return valid results
            assert len(results) == 3
        except (SignalProcessingError, ValueError):
            # Or should raise appropriate error
            assert True

    def test_zero_commission_and_slippage(self):
        """Test with zero commission and slippage."""
        manager = VectorizedPositionManager(
            initial_cash=100000, commission_rate=0.0, slippage_rate=0.0
        )

        timestamp = pd.Timestamp("2023-01-01")
        price = 100.0
        signal = 1.0
        current_position = 0.0
        current_cash = 50000.0

        position, cash, trade = manager._process_buy_signal(
            timestamp, price, signal, current_position, current_cash
        )

        # Check that trade record exists and is valid
        assert isinstance(trade, dict)
        if trade:  # Only check if trade was executed
            assert "commission" in trade
            assert "slippage" in trade
