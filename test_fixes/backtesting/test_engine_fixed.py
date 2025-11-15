"""Tests for backtesting engine module."""

import pytest
import numpy as np
import pandas as pd
from unittest.mock import Mock, patch
from datetime import datetime, timedelta

try:
    from quantchain.backtesting.engine import (
        BacktestingEngine,
        BacktestExecutionError,
        BacktestConfig,
        BacktestResult,
    )
    ENGINE_AVAILABLE = True
except ImportError as e:
    ENGINE_AVAILABLE = False
    print(f"Import error: {e}")

pytestmark = pytest.mark.skipif(
    not ENGINE_AVAILABLE, reason="Backtesting engine not available"
)


class TestBacktestingEngine:
    """Tests for BacktestingEngine."""

    @pytest.fixture
    def mock_config(self) -> BacktestConfig:
        """Create mock backtesting configuration."""
        return BacktestConfig(
            initial_capital=10000.0,
            commission_rate=0.001,
            slippage_rate=0.0005,
        )

    @pytest.fixture
    def sample_data(self) -> pd.DataFrame:
        """Create sample price data."""
        dates = pd.date_range(start="2023-01-01", periods=100, freq="D")
        np.random.seed(42)
        prices = 100 + np.cumsum(np.random.randn(100) * 0.01)

        return pd.DataFrame({
            "date": dates,
            "open": prices,
            "high": prices * 1.01,
            "low": prices * 0.99,
            "close": prices,
            "volume": np.random.randint(1000, 10000, 100),
        })

    def test_backtesting_engine_initialization(self, mock_config) -> None:
        """Test backtesting engine initialization."""
        engine = BacktestingEngine(mock_config)
        assert engine.config == mock_config
        assert engine.current_capital == mock_config.initial_capital

    def test_backtesting_engine_run_backtest(self, mock_config, sample_data) -> None:
        """Test running a backtest."""
        engine = BacktestingEngine(mock_config)

        # Mock a simple strategy
        def strategy(data):
            # Buy on day 1, sell on day 2
            if len(data) < 2:
                return []

            return [
                {
                    "date": data.iloc[0]["date"],
                    "action": "buy",
                    "symbol": "TEST",
                    "quantity": 10,
                    "price": data.iloc[0]["close"],
                },
                {
                    "date": data.iloc[1]["date"],
                    "action": "sell",
                    "symbol": "TEST",
                    "quantity": 10,
                    "price": data.iloc[1]["close"],
                }
            ]

        result = engine.run_backtest(sample_data, strategy)
        assert isinstance(result, BacktestResult)
        assert result.initial_capital == mock_config.initial_capital
        assert len(result.trades) >= 2

    def test_backtesting_engine_invalid_strategy(self, mock_config, sample_data) -> None:
        """Test backtesting with invalid strategy."""
        engine = BacktestingEngine(mock_config)

        # Invalid strategy that raises an exception
        def invalid_strategy(data):
            raise ValueError("Test error")

        with pytest.raises(BacktestExecutionError):
            engine.run_backtest(sample_data, invalid_strategy)

    def test_backtesting_engine_insufficient_capital(self, mock_config, sample_data) -> None:
        """Test backtesting with insufficient capital for a trade."""
        engine = BacktestingEngine(mock_config)

        # Strategy that tries to buy more than possible
        def over_buy_strategy(data):
            if len(data) < 1:
                return []

            return [
                {
                    "date": data.iloc[0]["date"],
                    "action": "buy",
                    "symbol": "TEST",
                    "quantity": 1000000,  # Too many shares
                    "price": data.iloc[0]["close"],
                }
            ]

        with pytest.raises(BacktestExecutionError):
            engine.run_backtest(sample_data, over_buy_strategy)


class TestBacktestConfig:
    """Tests for BacktestConfig."""

    def test_backtest_config_initialization(self) -> None:
        """Test backtest configuration initialization."""
        config = BacktestConfig(
            initial_capital=10000.0,
            commission_rate=0.001,
            slippage_rate=0.0005,
        )

        assert config.initial_capital == 10000.0
        assert config.commission_rate == 0.001
        assert config.slippage_rate == 0.0005

    def test_backtest_config_default_values(self) -> None:
        """Test backtest configuration with default values."""
        config = BacktestConfig()

        assert config.initial_capital == 10000.0
        assert config.commission_rate == 0.001
        assert config.slippage_rate == 0.0005


class TestBacktestResult:
    """Tests for BacktestResult."""

    @pytest.fixture
    def sample_result(self) -> BacktestResult:
        """Create a sample backtest result."""
        trades = [
            {
                "date": datetime(2023, 1, 1),
                "action": "buy",
                "symbol": "TEST",
                "quantity": 10,
                "price": 100.0,
            },
            {
                "date": datetime(2023, 1, 2),
                "action": "sell",
                "symbol": "TEST",
                "quantity": 10,
                "price": 105.0,
            }
        ]

        equity_curve = pd.Series([
            10000.0,  # Initial
            9000.0,   # After buying 10 shares at 100
            10050.0,  # After selling 10 shares at 105
        ], index=pd.date_range(start="2023-01-01", periods=3))

        return BacktestResult(
            initial_capital=10000.0,
            final_capital=10050.0,
            trades=trades,
            equity_curve=equity_curve,
        )

    def test_backtest_result_initialization(self, sample_result) -> None:
        """Test backtest result initialization."""
        assert sample_result.initial_capital == 10000.0
        assert sample_result.final_capital == 10050.0
        assert len(sample_result.trades) == 2
        assert len(sample_result.equity_curve) == 3

    def test_backtest_result_calculate_return(self, sample_result) -> None:
        """Test return calculation."""
        total_return = sample_result.calculate_total_return()
        expected_return = (10050.0 - 10000.0) / 10000.0
        assert abs(total_return - expected_return) < 1e-6

    def test_backtest_result_calculate_sharpe(self, sample_result) -> None:
        """Test Sharpe ratio calculation."""
        sharpe = sample_result.calculate_sharpe(risk_free_rate=0.02)
        assert isinstance(sharpe, float)

    def test_backtest_result_calculate_max_drawdown(self, sample_result) -> None:
        """Test maximum drawdown calculation."""
        max_drawdown = sample_result.calculate_max_drawdown()
        assert isinstance(max_drawdown, float)
