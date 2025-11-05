"""
Pytest configuration and shared fixtures for backtesting tests.
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime
from unittest.mock import MagicMock

from quantchain.backtesting.engine import BacktestConfig


@pytest.fixture
def sample_ohlcv_data():
    """Generate sample OHLCV data for testing."""
    np.random.seed(42)  # For reproducible data

    # Generate 500 days of price data
    dates = pd.date_range(start="2023-01-01", periods=500, freq="D")

    # Generate price series with some trend and volatility
    initial_price = 100.0
    returns = np.random.normal(0.0005, 0.02, 500)  # Daily returns
    prices = [initial_price]

    prices.extend(prices[-1] * (1 + ret) for ret in returns[1:])
    prices = np.array(prices)

    # Generate OHLCV from close prices
    high = prices * (1 + np.abs(np.random.normal(0, 0.01, 500)))
    low = prices * (1 - np.abs(np.random.normal(0, 0.01, 500)))
    open_price = np.roll(prices, 1)
    open_price[0] = prices[0]
    volume = np.random.randint(100000, 1000000, 500)

    return pd.DataFrame(
        {
            "open": open_price,
            "high": high,
            "low": low,
            "close": prices,
            "volume": volume,
        },
        index=dates,
    )


@pytest.fixture
def sample_multibar_data():
    """Generate multi-symbol OHLCV data for testing."""
    np.random.seed(123)

    dates = pd.date_range(start="2023-01-01", periods=100, freq="D")
    symbols = ["AAPL", "GOOGL", "MSFT"]

    data_frames = []
    for symbol in symbols:
        initial_price = np.random.uniform(50, 200)
        returns = np.random.normal(0.0005, 0.02, 100)
        prices = [initial_price]

        prices.extend(prices[-1] * (1 + ret) for ret in returns[1:])
        prices = np.array(prices)

        high = prices * (1 + np.abs(np.random.normal(0, 0.01, 100)))
        low = prices * (1 - np.abs(np.random.normal(0, 0.01, 100)))
        open_price = np.roll(prices, 1)
        open_price[0] = prices[0]
        volume = np.random.randint(100000, 1000000, 100)

        df = pd.DataFrame(
            {
                "open": open_price,
                "high": high,
                "low": low,
                "close": prices,
                "volume": volume,
                "symbol": symbol,
            },
            index=dates,
        )

        data_frames.append(df)

    return pd.concat(data_frames)


@pytest.fixture
def mock_data_connector():
    """Create mock data connector for testing."""
    mock_connector = MagicMock()

    # Mock get_historical_data method
    mock_connector.get_historical_data.return_value = pd.DataFrame(
        {
            "open": [100, 101, 102],
            "high": [101, 102, 103],
            "low": [99, 100, 101],
            "close": [100, 101, 102],
            "volume": [1000, 1100, 1200],
        },
        index=pd.date_range("2023-01-01", periods=3, freq="D"),
    )

    # Mock get_market_data method
    mock_connector.get_market_data.return_value = {
        "timestamp": datetime.now(),
        "open": 100.0,
        "high": 101.0,
        "low": 99.0,
        "close": 100.5,
        "volume": 1500,
    }

    return mock_connector


@pytest.fixture
def default_backtest_config():
    """Default backtest configuration for testing."""
    return BacktestConfig(
        initial_cash=100000.0,
        commission_rate=0.001,
        slippage_model="fixed",
        slippage_rate=0.0001,
        latency_model="fixed",
        latency_ms=10.0,
        start_date=None,
        end_date=None,
        data_frequency="1d",
    )


@pytest.fixture
def sample_trades():
    """Generate sample trade data for metrics testing."""
    trades = [
        {
            "timestamp": datetime(2023, 1, 2),
            "symbol": "AAPL",
            "side": "buy",
            "quantity": 100,
            "price": 100.0,
            "commission": 1.0,
            "pnl": 0.0,
        },
        {
            "timestamp": datetime(2023, 1, 5),
            "symbol": "AAPL",
            "side": "sell",
            "quantity": 100,
            "price": 105.0,
            "commission": 1.05,
            "pnl": 500.0 - 1.05,  # Profit
        },
        {
            "timestamp": datetime(2023, 1, 10),
            "symbol": "GOOGL",
            "side": "buy",
            "quantity": 50,
            "price": 150.0,
            "commission": 0.75,
            "pnl": 0.0,
        },
        {
            "timestamp": datetime(2023, 1, 15),
            "symbol": "GOOGL",
            "side": "sell",
            "quantity": 50,
            "price": 145.0,
            "commission": 0.725,
            "pnl": -250.0 - 0.725,  # Loss
        },
    ]

    return pd.DataFrame(trades)


@pytest.fixture
def winning_trades():
    """Generate only winning trades for testing."""
    trades = [
        {
            "timestamp": datetime(2023, 1, 2),
            "symbol": "AAPL",
            "side": "buy",
            "quantity": 100,
            "price": 100.0,
            "commission": 1.0,
            "pnl": 0.0,
        },
        {
            "timestamp": datetime(2023, 1, 5),
            "symbol": "AAPL",
            "side": "sell",
            "quantity": 100,
            "price": 110.0,
            "commission": 1.1,
            "pnl": 1000.0 - 1.1,
        },
        {
            "timestamp": datetime(2023, 1, 10),
            "symbol": "MSFT",
            "side": "buy",
            "quantity": 80,
            "price": 200.0,
            "commission": 1.6,
            "pnl": 0.0,
        },
        {
            "timestamp": datetime(2023, 1, 15),
            "symbol": "MSFT",
            "side": "sell",
            "quantity": 80,
            "price": 220.0,
            "commission": 1.76,
            "pnl": 1600.0 - 1.76,
        },
    ]

    return pd.DataFrame(trades)


@pytest.fixture
def sample_equity_curve():
    """Generate sample equity curve for testing."""
    np.random.seed(456)

    # Generate equity curve with some growth and drawdowns
    dates = pd.date_range(start="2023-01-01", periods=252, freq="D")  # Trading days
    initial_equity = 100000.0

    # Generate daily returns with some trend
    daily_returns = np.random.normal(0.0008, 0.015, 252)  # Slight positive drift

    # Create equity series
    equity = [initial_equity]
    equity.extend(equity[-1] * (1 + ret) for ret in daily_returns)
    return pd.Series(equity[1:], index=dates)


@pytest.fixture
def volatile_equity_curve():
    """Generate volatile equity curve with significant drawdowns."""
    np.random.seed(789)

    dates = pd.date_range(start="2023-01-01", periods=252, freq="D")
    initial_equity = 100000.0

    # Generate more volatile returns
    daily_returns = np.random.normal(0.0002, 0.025, 252)

    # Add a significant drawdown period
    daily_returns[100:120] = np.random.normal(-0.02, 0.01, 20)

    equity = [initial_equity]
    equity.extend(equity[-1] * (1 + ret) for ret in daily_returns)
    return pd.Series(equity[1:], index=dates)


@pytest.fixture
def mock_strategy():
    """Create mock trading strategy for testing."""
    strategy = MagicMock()

    # Mock strategy methods
    strategy.init.return_value = None
    strategy.next.side_effect = [
        "buy",  # First bar
        None,  # Second bar (hold)
        None,  # Third bar (hold)
        "sell",  # Fourth bar
        None,  # Rest (hold)
    ]

    return strategy


@pytest.fixture
def simple_buy_hold_strategy():
    """Simple buy-and-hold strategy for testing."""

    class BuyHoldStrategy:
        def __init__(self):
            self.bought = False

        def init(self):
            self.bought = False

        def next(self, bar):
            if not self.bought:
                self.bought = True
                return "buy"
            return None

    return BuyHoldStrategy()


@pytest.fixture
def moving_average_strategy():
    """Simple moving average crossover strategy for testing."""

    class MovingAverageStrategy:
        def __init__(self, short_window=10, long_window=20):
            self.short_window = short_window
            self.long_window = long_window
            self.price_history = []
            self.position = False

        def init(self):
            self.price_history = []
            self.position = False

        def next(self, bar):
            close_price = bar.get("close", 0)
            self.price_history.append(close_price)

            if len(self.price_history) < self.long_window:
                return None

            short_ma = np.mean(self.price_history[-self.short_window:])
            long_ma = np.mean(self.price_history[-self.long_window:])

            # Golden cross - short MA crosses above long MA
            if not self.position and short_ma > long_ma:
                self.position = True
                return "buy"

            # Death cross - short MA crosses below long MA
            elif self.position and short_ma < long_ma:
                self.position = False
                return "sell"

            return None

    return MovingAverageStrategy()


@pytest.fixture
def sample_benchmark_returns():
    """Generate sample benchmark returns for testing."""
    np.random.seed(321)

    dates = pd.date_range(start="2023-01-01", periods=252, freq="D")
    daily_returns = np.random.normal(0.0005, 0.012, 252)  # Market-like returns

    benchmark_series = pd.Series(1.0, index=dates)
    for i, ret in enumerate(daily_returns):
        if i == 0:
            benchmark_series.iloc[i] = 1 + ret
        else:
            benchmark_series.iloc[i] = benchmark_series.iloc[i - 1] * (1 + ret)

    return benchmark_series.pct_change().dropna()


def generate_synthetic_market_data(
    start_date="2023-01-01",
    periods=100,
    symbols=None,
    initial_price=100.0,
    trend=0.0005,
    volatility=0.02,
    volume_base=500000,
):
    if symbols is None:
        symbols = ["AAPL"]
    """
    Helper function to generate synthetic market data.

    Args:
        start_date: Start date for the data
        periods: Number of periods to generate
        symbols: List of symbols to generate data for
        initial_price: Initial price for all symbols
        trend: Daily trend (positive for uptrend)
        volatility: Daily volatility
        volume_base: Base volume for generation

    Returns:
        pd.DataFrame with OHLCV data
    """
    if symbols is None:
        symbols = ["AAPL"]
    np.random.seed(int(datetime.now().timestamp()))  # Random seed

    dates = pd.date_range(start=start_date, periods=periods, freq="D")
    all_data = []

    for symbol in symbols:
        # Generate price series
        returns = np.random.normal(trend, volatility, periods)
        prices = [initial_price]

        prices.extend(prices[-1] * (1 + ret) for ret in returns[1:])
        prices = np.array(prices)

        # Generate OHLCV
        high = prices * (1 + np.abs(np.random.normal(0, 0.01, periods)))
        low = prices * (1 - np.abs(np.random.normal(0, 0.01, periods)))
        open_price = np.roll(prices, 1)
        open_price[0] = prices[0]
        volume = np.random.normal(volume_base, volume_base * 0.2, periods).astype(int)

        df = pd.DataFrame(
            {
                "open": open_price,
                "high": high,
                "low": low,
                "close": prices,
                "volume": volume,
                "symbol": symbol,
            },
            index=dates,
        )

        all_data.append(df)

    return pd.concat(all_data, ignore_index=False)


# Helper function for creating test bars
def create_test_bar(
    timestamp=None,
    open_price=100.0,
    high_price=101.0,
    low_price=99.0,
    close_price=100.5,
    volume=1000,
    symbol="TEST",
):
    """Create a single test bar dictionary."""
    return {
        "timestamp": timestamp or datetime.now(),
        "open": open_price,
        "high": high_price,
        "low": low_price,
        "close": close_price,
        "volume": volume,
        "symbol": symbol,
    }


# Note: pytest_plugins and pytest_configure moved to root conftest.py
# See: https://docs.pytest.org/en/stable/deprecations.html
# #pytest-plugins-in-non-top-level-conftest-files
