"""Enhanced tests for BacktestEngine to improve code coverage."""

import pytest
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

try:
    from quantchain.backtesting.engine import (
        BacktestEngine,
        BacktestConfig,
        BacktestResult,
        MetricsResult,
    )
    ENGINE_AVAILABLE = True
except ImportError as e:
    ENGINE_AVAILABLE = False
    print(f"Import error: {e}")

pytestmark = pytest.mark.skipif(
    not ENGINE_AVAILABLE, reason="Backtesting engine not available"
)


class TestBacktestEngineEnhanced:
    """Enhanced tests for BacktestEngine to cover missing code paths."""

    @pytest.fixture
    def mock_config(self) -> BacktestConfig:
        """Create mock backtesting configuration."""
        return BacktestConfig(
            initial_capital=10000.0,
            commission=0.001,
            slippage=0.0005,
        )

    @pytest.fixture
    def sample_data(self) -> pd.DataFrame:
        """Create sample price data."""
        dates = pd.date_range(start="2023-01-01", periods=100, freq="D")
        np.random.seed(42)
        prices = 100 + np.cumsum(np.random.randn(100) * 0.01)

        df = pd.DataFrame({
            "open": prices,
            "high": prices * 1.01,
            "low": prices * 0.99,
            "close": prices,
            "volume": np.random.randint(1000, 10000, 100),
        })
        df.index = dates
        return df

    def test_position_value_calculation(self, mock_config, sample_data) -> None:
        """Test position value calculation."""
        engine = BacktestEngine(mock_config)

        # Add a position
        engine.open_positions["TEST"] = {
            "quantity": 10,
            "avg_price": 100.0,
        }

        # Calculate position value
        value = engine._calculate_position_value("TEST", 105.0)
        assert value == 1050.0  # 10 * 105

        # Test with non-existent position
        value = engine._calculate_position_value("NON_EXISTENT", 105.0)
        assert value == 0.0

    def test_portfolio_value_calculation(self, mock_config, sample_data) -> None:
        """Test total portfolio value calculation."""
        engine = BacktestEngine(mock_config)

        # Add positions
        engine.open_positions["TEST1"] = {
            "quantity": 10,
            "avg_price": 100.0,
        }
        engine.open_positions["TEST2"] = {
            "quantity": 5,
            "avg_price": 200.0,
        }

        # Current prices
        prices = {
            "TEST1": 105.0,
            "TEST2": 210.0,
        }

        # Calculate portfolio value
        value = engine._get_total_portfolio_value(prices)
        expected = engine.current_capital + (10 * 105.0) + (5 * 210.0)
        assert value == expected

    def test_trade_execution_buy(self, mock_config, sample_data) -> None:
        """Test buy trade execution."""
        engine = BacktestEngine(mock_config)

        timestamp = datetime.now()
        result = engine._execute_trade(
            "TEST", "buy", 10, 100.0, timestamp
        )

        assert result["success"] is True
        assert result["symbol"] == "TEST"
        assert result["side"] == "buy"
        assert result["quantity"] == 10
        assert result["price"] > 100.0  # Price includes slippage
        assert result["commission"] > 0  # Commission is charged

        # Check position was created
        assert "TEST" in engine.open_positions
        assert engine.open_positions["TEST"]["quantity"] == 10

    def test_trade_execution_sell(self, mock_config, sample_data) -> None:
        """Test sell trade execution."""
        engine = BacktestEngine(mock_config)

        # First create a position
        timestamp = datetime.now()
        engine.open_positions["TEST"] = {
            "quantity": 10,
            "avg_price": 100.0,
            "total_cost": 1000.0,
        }

        # Now sell it
        result = engine._execute_trade(
            "TEST", "sell", 10, 105.0, timestamp
        )

        assert result["success"] is True
        assert result["symbol"] == "TEST"
        assert result["side"] == "sell"
        assert result["quantity"] == 10
        assert result["price"] < 105.0  # Price includes slippage
        assert result["commission"] > 0  # Commission is charged
        assert "realized_pnl" in result
        assert result["realized_pnl"] > 0  # Profit from this trade

        # Position should be closed
        assert "TEST" not in engine.open_positions

    def test_trade_execution_insufficient_capital(self, mock_config, sample_data) -> None:
        """Test trade execution with insufficient capital."""
        engine = BacktestEngine(mock_config)

        timestamp = datetime.now()
        result = engine._execute_trade(
            "TEST", "buy", 1000000, 100.0, timestamp  # Too expensive
        )

        assert result["success"] is False
        assert "error" in result
        assert result["error"] == "Insufficient capital"

        # No position should be created
        assert "TEST" not in engine.open_positions

    def test_trade_execution_invalid_side(self, mock_config, sample_data) -> None:
        """Test trade execution with invalid side."""
        engine = BacktestEngine(mock_config)

        timestamp = datetime.now()
        result = engine._execute_trade(
            "TEST", "invalid", 10, 100.0, timestamp
        )

        assert result["success"] is False
        assert "error" in result
        assert result["error"] == "Invalid side"

    def test_stop_loss_execution(self, mock_config, sample_data) -> None:
        """Test stop loss condition execution."""
        engine = BacktestEngine(mock_config)

        # Create a position with stop loss
        timestamp = datetime.now()
        engine.open_positions["TEST"] = {
            "quantity": 10,
            "avg_price": 100.0,
            "total_cost": 1000.0,
            "stop_loss": 95.0,  # 5% below entry
            "take_profit": 110.0,  # 10% above entry
            "open_time": timestamp
        }

        # Current price is below stop loss
        current_prices = {"TEST": 94.0}
        trades = engine._check_stops(current_prices, datetime.now())

        # Should execute a stop loss trade
        assert len(trades) == 1
        assert trades[0]["reason"] == "stop_loss"
        assert trades[0]["success"] is True

    def test_take_profit_execution(self, mock_config, sample_data) -> None:
        """Test take profit condition execution."""
        engine = BacktestEngine(mock_config)

        # Create a position with take profit
        timestamp = datetime.now()
        engine.open_positions["TEST"] = {
            "quantity": 10,
            "avg_price": 100.0,
            "total_cost": 1000.0,
            "stop_loss": 95.0,  # 5% below entry
            "take_profit": 110.0,  # 10% above entry
            "open_time": timestamp
        }

        # Current price is above take profit
        current_prices = {"TEST": 111.0}
        trades = engine._check_stops(current_prices, datetime.now())

        # Should execute a take profit trade
        assert len(trades) == 1
        assert trades[0]["reason"] == "take_profit"
        assert trades[0]["success"] is True

    def test_metrics_calculation_no_data(self, mock_config) -> None:
        """Test metrics calculation with no equity curve data."""
        engine = BacktestEngine(mock_config)

        # Empty equity curve
        engine.equity_curve = []
        metrics = engine._calculate_metrics()

        # Should return default metrics
        assert isinstance(metrics, MetricsResult)
        assert metrics.total_return == 0.0
        assert metrics.sharpe_ratio == 0.0

    def test_metrics_calculation_with_data(self, mock_config) -> None:
        """Test metrics calculation with equity curve data."""
        engine = BacktestEngine(mock_config)

        # Create sample equity curve
        engine.equity_curve = [
            {"timestamp": datetime(2023, 1, 1), "portfolio_value": 10000},
            {"timestamp": datetime(2023, 1, 2), "portfolio_value": 10500},
            {"timestamp": datetime(2023, 1, 3), "portfolio_value": 9500},
            {"timestamp": datetime(2023, 1, 4), "portfolio_value": 11000},
        ]

        # Create sample closed trades
        engine.closed_trades = [
            {"realized_pnl": 500.0},
            {"realized_pnl": -500.0},
            {"realized_pnl": 1500.0},
        ]

        metrics = engine._calculate_metrics()

        # Should calculate metrics correctly
        assert isinstance(metrics, MetricsResult)
        assert metrics.total_return > 0  # Overall profit
        assert metrics.total_trades == 3
        assert metrics.win_rate == 2/3  # 2 winners out of 3 trades

    def test_backtest_with_date_range(self, mock_config, sample_data) -> None:
        """Test backtest with specific date range."""
        engine = BacktestEngine(mock_config)

        # Simple buy-and-hold strategy
        class SimpleStrategy:
            def initialize(self, config):
                pass

            def process_bar(self, timestamp, data):
                if not hasattr(self, '_bought'):
                    self._bought = True
                    return {"symbol": "TEST", "side": "buy", "quantity": 10}
                return None

        strategy = SimpleStrategy()

        # Run backtest with date range
        start_date = datetime(2023, 1, 10)
        end_date = datetime(2023, 1, 30)

        result = engine.run_backtest(
            sample_data, strategy, start_date=start_date, end_date=end_date
        )

        assert isinstance(result, BacktestResult)
        # Check that data was filtered by date range
        assert len(result.equity_curve) < len(sample_data)

    def test_backtest_max_positions_limit(self, mock_config, sample_data) -> None:
        """Test that max open positions limit is respected."""
        # Set a low limit for testing
        config = BacktestConfig(
            initial_capital=10000.0,
            commission=0.001,
            slippage=0.0005,
            max_open_positions=2,  # Only allow 2 positions
        )

        engine = BacktestEngine(config)

        # Strategy that tries to buy many different symbols
        class ManySymbolsStrategy:
            def initialize(self, config):
                self.counter = 0

            def process_bar(self, timestamp, data):
                self.counter += 1
                # Try to buy a new symbol each time
                return {"symbol": f"SYMBOL{self.counter}", "side": "buy", "quantity": 1}

        strategy = ManySymbolsStrategy()
        result = engine.run_backtest(sample_data, strategy)

        # Count buy trades
        buy_trades = [
            trade for _, trade in result.trade_log.iterrows()
            if trade['side'] == 'buy'
        ]

        # Should not exceed max_open_positions
        assert len(buy_trades) <= config.max_open_positions
