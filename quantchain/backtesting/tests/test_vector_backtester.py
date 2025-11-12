# Auto-generated test file for vector_backtester.py
# Generated using Z.AI GLM-4.6 API

import sys
from pathlib import Path

import pytest

# Add the parent directory to the path to import the module
sys.path.insert(0, str(Path(__file__).parent.parent))


import pandas as pd
import pytest
from engine import BacktestConfig
from vector_backtester import (
    SignalProcessingError,
    VectorBacktester,
    VectorBacktestResult,
    VectorizedPositionManager,
)


@pytest.fixture
def sample_prices():
    """Fixture providing sample price data."""
    dates = pd.date_range("2023-01-01", periods=10, freq="D")
    return pd.Series(
        [100.0, 101.0, 102.0, 103.0, 104.0, 105.0, 104.0, 103.0, 102.0, 101.0],
        index=dates,
        name="close",
    )


@pytest.fixture
def sample_signals():
    """Fixture providing sample trading signals."""
    dates = pd.date_range("2023-01-01", periods=10, freq="D")
    return pd.Series([0, 1, 0, 0, -1, 0, 1, 0, 0, -1], index=dates, name="signal")


@pytest.fixture
def sample_data():
    """Fixture providing sample OHLCV data."""
    dates = pd.date_range("2023-01-01", periods=10, freq="D")
    return pd.DataFrame(
        {
            "open": [
                99.0,
                100.0,
                101.0,
                102.0,
                103.0,
                104.0,
                105.0,
                104.0,
                103.0,
                102.0,
            ],
            "high": [
                101.0,
                102.0,
                103.0,
                104.0,
                105.0,
                106.0,
                106.0,
                105.0,
                104.0,
                103.0,
            ],
            "low": [98.0, 99.0, 100.0, 101.0, 102.0, 103.0, 103.0, 102.0, 101.0, 100.0],
            "close": [
                100.0,
                101.0,
                102.0,
                103.0,
                104.0,
                105.0,
                104.0,
                103.0,
                102.0,
                101.0,
            ],
            "volume": [1000, 1100, 1200, 1300, 1400, 1500, 1400, 1300, 1200, 1100],
        },
        index=dates,
    )


@pytest.fixture
def default_config():
    """Fixture providing default backtest configuration."""
    return BacktestConfig(
        initial_cash=100000.0,
        commission_rate=0.001,
        slippage_rate=0.0005,
        latency_ms=10,
    )


class TestVectorizedPositionManager:
    """Test cases for VectorizedPositionManager class."""

    def test_init_default_values(self):
        """Test initialization with default values."""
        manager = VectorizedPositionManager()

        assert manager.initial_cash == 100000.0
        assert manager.current_cash == 100000.0
        assert manager.commission_rate == 0.0
        assert manager.slippage_rate == 0.0
        assert manager.positions is None
        assert manager.equity_curve is None
        assert manager.trade_log is None

    def test_init_custom_values(self):
        """Test initialization with custom values."""
        manager = VectorizedPositionManager(
            initial_cash=50000.0, commission_rate=0.002, slippage_rate=0.001
        )

        assert manager.initial_cash == 50000.0
        assert manager.current_cash == 50000.0
        assert manager.commission_rate == 0.002
        assert manager.slippage_rate == 0.001

    def test_process_buy_signal_valid(self):
        """Test processing a valid buy signal."""
        manager = VectorizedPositionManager(
            initial_cash=10000.0, commission_rate=0.001, slippage_rate=0.0005
        )

        timestamp = pd.Timestamp("2023-01-01")
        price = 100.0
        signal = 1.0
        current_position = 0.0
        current_cash = 10000.0

        new_position, new_cash, trade = manager._process_buy_signal(
            timestamp, price, signal, current_position, current_cash
        )

        expected_price = price * (1 + 0.0005)  # 100.05
        expected_shares = current_cash / expected_price  # ~99.95
        expected_cost = expected_shares * expected_price
        expected_commission = expected_cost * 0.001
        expected_total_cost = expected_cost + expected_commission

        assert new_position == pytest.approx(expected_shares)
        assert new_cash == pytest.approx(current_cash - expected_total_cost)
        assert trade["timestamp"] == timestamp
        assert trade["signal"] == signal
        assert trade["price"] == pytest.approx(expected_price)
        assert trade["shares"] == pytest.approx(expected_shares)
        assert trade["commission"] == pytest.approx(expected_commission)

    def test_process_buy_signal_insufficient_cash(self):
        """Test buy signal with insufficient cash."""
        manager = VectorizedPositionManager(
            initial_cash=100.0, commission_rate=0.5, slippage_rate=0.1
        )

        timestamp = pd.Timestamp("2023-01-01")
        price = 100.0
        signal = 1.0
        current_position = 0.0
        current_cash = 100.0

        new_position, new_cash, trade = manager._process_buy_signal(
            timestamp, price, signal, current_position, current_cash
        )

        assert new_position == 0.0
        assert new_cash == 100.0
        assert trade == {}

    def test_process_buy_signal_already_in_position(self):
        """Test buy signal when already in position."""
        manager = VectorizedPositionManager()

        timestamp = pd.Timestamp("2023-01-01")
        price = 100.0
        signal = 1.0
        current_position = 10.0
        current_cash = 5000.0

        new_position, new_cash, trade = manager._process_buy_signal(
            timestamp, price, signal, current_position, current_cash
        )

        assert new_position == 10.0
        assert new_cash == 5000.0
        assert trade == {}

    def test_process_sell_signal_long_valid(self):
        """Test processing a valid sell signal for long position."""
        manager = VectorizedPositionManager(commission_rate=0.001, slippage_rate=0.0005)

        timestamp = pd.Timestamp("2023-01-01")
        price = 100.0
        signal = -1.0
        current_position = 10.0
        current_cash = 5000.0

        new_position, new_cash, trade = manager._process_sell_signal_long(
            timestamp, price, signal, current_position, current_cash
        )

        expected_price = price * (1 - 0.0005)  # 99.95
        expected_proceeds = current_position * expected_price
        expected_commission = expected_proceeds * 0.001
        expected_net_proceeds = expected_proceeds - expected_commission

        assert new_position == 0.0
        assert new_cash == pytest.approx(current_cash + expected_net_proceeds)
        assert trade["timestamp"] == timestamp
        assert trade["signal"] == signal
        assert trade["price"] == pytest.approx(expected_price)
        assert trade["shares"] == -current_position
        assert trade["commission"] == pytest.approx(expected_commission)

    def test_process_sell_signal_long_no_position(self):
        """Test sell signal with no position."""
        manager = VectorizedPositionManager()

        timestamp = pd.Timestamp("2023-01-01")
        price = 100.0
        signal = -1.0
        current_position = 0.0
        current_cash = 10000.0

        new_position, new_cash, trade = manager._process_sell_signal_long(
            timestamp, price, signal, current_position, current_cash
        )

        assert new_position == 0.0
        assert new_cash == 10000.0
        assert trade == {}

    def test_process_sell_signal_short_valid(self):
        """Test processing a valid sell signal for short position."""
        manager = VectorizedPositionManager(commission_rate=0.001, slippage_rate=0.0005)

        timestamp = pd.Timestamp("2023-01-01")
        price = 100.0
        signal = -1.0
        current_position = -10.0
        current_cash = 15000.0

        new_position, new_cash, trade = manager._process_sell_signal_short(
            timestamp, price, signal, current_position, current_cash
        )

        expected_price = price * (1 + 0.0005)  # 100.05
        expected_cost = abs(current_position) * expected_price
        expected_commission = expected_cost * 0.001
        expected_total_cost = expected_cost + expected_commission

        assert new_position == 0.0
        assert new_cash == pytest.approx(current_cash - expected_total_cost)
        assert trade["timestamp"] == timestamp
        assert trade["signal"] == signal
        assert trade["price"] == pytest.approx(expected_price)
        assert trade["shares"] == abs(current_position)
        assert trade["commission"] == pytest.approx(expected_commission)

    def test_process_sell_signal_short_insufficient_cash(self):
        """Test sell signal for short position with insufficient cash."""
        manager = VectorizedPositionManager(initial_cash=100.0)

        timestamp = pd.Timestamp("2023-01-01")
        price = 100.0
        signal = -1.0
        current_position = -10.0
        current_cash = 100.0

        new_position, new_cash, trade = manager._process_sell_signal_short(
            timestamp, price, signal, current_position, current_cash
        )

        assert new_position == -10.0
        assert new_cash == 100.0
        assert trade == {}

    def test_process_signals_length_mismatch(self):
        """Test process_signals with length mismatch."""
        manager = VectorizedPositionManager()

        prices = pd.Series([100.0, 101.0, 102.0])
        signals = pd.Series([1, 0])

        with pytest.raises(SignalProcessingError, match="Length mismatch"):
            manager.process_signals(prices, signals)

    def test_process_signals_valid(self, sample_prices, sample_signals):
        """Test process_signals with valid inputs."""
        manager = VectorizedPositionManager(
            initial_cash=10000.0, commission_rate=0.001, slippage_rate=0.0005
        )

        positions, trades, final_cash = manager.process_signals(
            sample_prices, sample_signals
        )

        assert isinstance(positions, pd.Series)
        assert len(positions) == len(sample_prices)
        assert isinstance(trades, pd.DataFrame)
        assert isinstance(final_cash, float)
        assert manager.positions is not None
        assert manager.trade_log is not None
        assert manager.current_cash == final_cash

    def test_process_signals_no_trades(self, sample_prices):
        """Test process_signals with no trading signals."""
        manager = VectorizedPositionManager()

        signals = pd.Series(0, index=sample_prices.index)

        positions, trades, final_cash = manager.process_signals(sample_prices, signals)

        assert (positions == 0).all()
        assert trades.empty
        assert final_cash == manager.initial_cash

    def test_process_signals_multiple_trades(self):
        """Test process_signals with multiple buy/sell cycles."""
        manager = VectorizedPositionManager(
            initial_cash=10000.0, commission_rate=0.001, slippage_rate=0.0005
        )

        dates = pd.date_range("2023-01-01", periods=6, freq="D")
        prices = pd.Series([100.0, 101.0, 102.0, 103.0, 104.0, 105.0], index=dates)
        signals = pd.Series([1, 0, -1, 1, 0, -1], index=dates)

        positions, trades, final_cash = manager.process_signals(prices, signals)

        assert len(trades) == 4  # 2 buys, 2 sells
        assert positions.iloc[0] > 0  # First buy
        assert positions.iloc[2] == 0  # First sell
        assert positions.iloc[3] > 0  # Second buy
        assert positions.iloc[5] == 0  # Second sell

    def test_calculate_equity_length_mismatch(self):
        """Test calculate_equity with length mismatch."""
        manager = VectorizedPositionManager()

        prices = pd.Series([100.0, 101.0, 102.0])
        positions = pd.Series([10.0, 0.0])

        with pytest.raises(SignalProcessingError, match="Length mismatch"):
            manager.calculate_equity(prices, positions)

    def test_calculate_equity_no_trades(self, sample_prices):
        """Test calculate_equity with no trades."""
        manager = VectorizedPositionManager(initial_cash=10000.0)

        positions = pd.Series(0.0, index=sample_prices.index)

        equity = manager.calculate_equity(sample_prices, positions)

        assert isinstance(equity, pd.Series)
        assert len(equity) == len(sample_prices)
        assert (equity == 10000.0).all()
        assert manager.equity_curve is not None

    def test_calculate_equity_with_trades(self, sample_prices):
        """Test calculate_equity with trades."""
        manager = VectorizedPositionManager(initial_cash=10000.0)

        # Simulate a trade log
        trade_log = pd.DataFrame(
            {
                "timestamp": [sample_prices.index[1], sample_prices.index[3]],
                "cash_after": [0.0, 10100.0],
                "signal": [1.0, -1.0],
                "price": [101.0, 103.0],
                "shares": [99.0, -99.0],
                "commission": [10.0, 10.0],
                "slippage": [5.0, 5.0],
                "cash_before": [10000.0, 0.0],
                "position": [99.0, 0.0],
            }
        )
        manager.trade_log = trade_log

        positions = pd.Series(
            [0.0, 99.0, 99.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            index=sample_prices.index,
        )

        equity = manager.calculate_equity(sample_prices, positions)

        assert isinstance(equity, pd.Series)
        assert len(equity) == len(sample_prices)
        assert equity.iloc[0] == 10000.0  # Initial cash
        assert equity.iloc[1] == pytest.approx(99.0 * 101.0)  # Position value after buy
        assert equity.iloc[3] == pytest.approx(10100.0)  # Cash after sell
        assert manager.equity_curve is not None


class TestVectorBacktester:
    """Test cases for VectorBacktester class."""

    def test_init_default_config(self):
        """Test initialization with default config."""
        backtester = VectorBacktester()

        assert backtester.config is not None
        assert backtester.position_manager is not None
        assert backtester.market_friction is not None
        assert backtester._result is None

    def test_init_custom_config(self, default_config):
        """Test initialization with custom config."""
        backtester = VectorBacktester(default_config)

        assert backtester.config == default_config
        assert backtester.position_manager.initial_cash == default_config.initial_cash
        assert (
            backtester.position_manager.commission_rate
            == default_config.commission_rate
        )
        assert backtester.position_manager.slippage_rate == default_config.slippage_rate

    def test_run_valid_inputs(self, sample_signals, sample_data, default_config):
        """Test run with valid inputs."""
        backtester = VectorBacktester(default_config)

        result = backtester.run(sample_signals, sample_data)

        assert isinstance(result, VectorBacktestResult)
        assert isinstance(result.equity_curve, pd.Series)
        assert isinstance(result.trade_log, pd.DataFrame)
        assert isinstance(result.positions, pd.Series)
        assert isinstance(result.returns, pd.Series)
        assert isinstance(result.metrics, dict)
        assert backtester._result == result

    def test_run_with_config_override(self, sample_signals, sample_data):
        """Test run with config override."""
        backtester = VectorBacktester()
        override_config = BacktestConfig(initial_cash=50000.0, commission_rate=0.002)

        backtester.run(sample_signals, sample_data, override_config)

        assert backtester.config == override_config
        assert backtester.position_manager.initial_cash == 50000.0
        assert backtester.position_manager.commission_rate == 0.002

    def test_run_missing_close_column(self, sample_signals, default_config):
        """Test run with data missing 'close' column."""
        backtester = VectorBacktester(default_config)

        # Create data missing close column
        data_missing_close = sample_data.drop(columns=["close"])

        with pytest.raises(ValueError, match="Missing required column 'close'"):
            backtester.run(sample_signals, data_missing_close)
