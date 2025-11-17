"""
Comprehensive tests for the backtesting engine module.
"""

from datetime import datetime
from unittest.mock import Mock, patch

import numpy as np
import pandas as pd
import pytest

from quantchain.backtesting.engine import (
    BacktestConfig,
    BacktestEngine,
    BacktestExecutionError,
    MetricsResult,
)


@pytest.mark.unit
class TestBacktestConfig:
    """Test cases for BacktestConfig class."""

    def test_backtest_config_init_default(self):
        """Test BacktestConfig initialization with default values."""
        config = BacktestConfig()

        assert config.initial_capital == 100000.0
        assert config.commission == 0.001
        assert config.slippage == 0.0005
        assert config.position_size == 0.1
        assert config.stop_loss_pct == 0.05
        assert config.take_profit_pct == 0.1
        assert config.max_open_positions == 10

    def test_backtest_config_init_custom(self):
        """Test BacktestConfig initialization with custom values."""
        config = BacktestConfig(
            initial_capital=50000.0,
            commission=0.002,
            slippage=0.001,
            position_size=0.2,
            stop_loss_pct=0.03,
            take_profit_pct=0.15,
            max_open_positions=5,
        )

        assert config.initial_capital == 50000.0
        assert config.commission == 0.002
        assert config.slippage == 0.001
        assert config.position_size == 0.2
        assert config.stop_loss_pct == 0.03
        assert config.take_profit_pct == 0.15
        assert config.max_open_positions == 5

    def test_backtest_config_validation_initial_capital_negative(self):
        """Test validation for negative initial capital."""
        with pytest.raises(ValueError, match="Initial capital must be positive"):
            BacktestConfig(initial_capital=-1000.0)

    def test_backtest_config_validation_initial_capital_zero(self):
        """Test validation for zero initial capital."""
        with pytest.raises(ValueError, match="Initial capital must be positive"):
            BacktestConfig(initial_capital=0.0)

    def test_backtest_config_validation_commission_negative(self):
        """Test validation for negative commission."""
        with pytest.raises(ValueError, match="Commission must be non-negative"):
            BacktestConfig(commission=-0.001)

    def test_backtest_config_validation_slippage_negative(self):
        """Test validation for negative slippage."""
        with pytest.raises(ValueError, match="Slippage must be non-negative"):
            BacktestConfig(slippage=-0.001)

    def test_backtest_config_validation_position_size_negative(self):
        """Test validation for negative position size."""
        with pytest.raises(ValueError, match="Position size must be positive"):
            BacktestConfig(position_size=-0.1)

    def test_backtest_config_validation_position_size_zero(self):
        """Test validation for zero position size."""
        with pytest.raises(ValueError, match="Position size must be positive"):
            BacktestConfig(position_size=0.0)

    def test_backtest_config_validation_stop_loss_pct_zero(self):
        """Test validation for zero stop loss percentage."""
        with pytest.raises(
            ValueError, match="Stop loss percentage must be between 0 and 1"
        ):
            BacktestConfig(stop_loss_pct=0.0)

    def test_backtest_config_validation_stop_loss_pct_one(self):
        """Test validation for stop loss percentage of 1."""
        with pytest.raises(
            ValueError, match="Stop loss percentage must be between 0 and 1"
        ):
            BacktestConfig(stop_loss_pct=1.0)

    def test_backtest_config_validation_take_profit_pct_negative(self):
        """Test validation for negative take profit percentage."""
        with pytest.raises(ValueError, match="Take profit percentage must be positive"):
            BacktestConfig(take_profit_pct=-0.1)

    def test_backtest_config_validation_take_profit_pct_zero(self):
        """Test validation for zero take profit percentage."""
        with pytest.raises(ValueError, match="Take profit percentage must be positive"):
            BacktestConfig(take_profit_pct=0.0)

    def test_backtest_config_validation_max_open_positions_negative(self):
        """Test validation for negative max open positions."""
        with pytest.raises(ValueError, match="Max open positions must be positive"):
            BacktestConfig(max_open_positions=-5)

    def test_backtest_config_validation_max_open_positions_zero(self):
        """Test validation for zero max open positions."""
        with pytest.raises(ValueError, match="Max open positions must be positive"):
            BacktestConfig(max_open_positions=0)


@pytest.mark.unit
class TestMetricsResult:
    """Test cases for MetricsResult class."""

    def test_metrics_result_init_default(self):
        """Test MetricsResult initialization with default values."""
        result = MetricsResult()

        assert result.total_return == 0.0
        assert result.return_pct == 0.0
        assert result.annualized_return == 0.0
        assert result.sharpe_ratio == 0.0
        assert result.sortino_ratio == 0.0
        assert result.calmar_ratio == 0.0
        assert result.max_drawdown == 0.0
        assert result.max_drawdown_pct == 0.0
        assert result.max_drawdown_duration == 0
        assert result.win_rate == 0.0
        assert result.win_rate_pct == 0.0
        assert result.profit_factor == 0.0
        assert result.recovery_factor == 0.0
        assert result.total_trades == 0
        assert result.avg_trade == 0.0
        assert result.avg_win_pct == 0.0
        assert result.avg_loss_pct == 0.0
        assert result.largest_win == 0.0
        assert result.largest_loss == 0.0
        assert result.avg_drawdown == 0.0
        assert result.avg_drawdown_pct == 0.0
        assert result.var_95 == 0.0
        assert result.var_99 == 0.0
        assert result.skewness == 0.0
        assert result.kurtosis == 0.0

    def test_metrics_result_init_custom(self):
        """Test MetricsResult initialization with custom values."""
        result = MetricsResult(
            total_return=10000.0,
            return_pct=10.0,
            annualized_return=12.0,
            sharpe_ratio=1.5,
            total_trades=50,
        )

        assert result.total_return == 10000.0
        assert result.return_pct == 10.0
        assert result.annualized_return == 12.0
        assert result.sharpe_ratio == 1.5
        assert result.total_trades == 50


@pytest.mark.unit
class TestBacktestEngine:
    """Test cases for BacktestEngine class."""

    def test_backtest_engine_init(self):
        """Test BacktestEngine initialization."""
        config = BacktestConfig(initial_capital=100000.0)
        engine = BacktestEngine(config)

        assert engine.config == config
        assert engine.current_capital == 100000.0
        assert engine.open_positions == {}
        assert engine.closed_trades == []
        assert engine.current_datetime is None
        assert engine.equity_curve == []

    def test_backtest_engine_reset_state(self):
        """Test resetting engine state."""
        config = BacktestConfig(initial_capital=100000.0)
        engine = BacktestEngine(config)

        # Modify state
        engine.current_capital = 90000.0
        engine.open_positions = {"AAPL": {"quantity": 10}}
        engine.closed_trades = [{"symbol": "GOOG"}]
        engine.current_datetime = datetime.now()
        engine.equity_curve = [{"timestamp": datetime.now(), "value": 90000.0}]

        # Reset state
        engine._reset_state()

        assert engine.current_capital == 100000.0
        assert engine.open_positions == {}
        assert engine.closed_trades == []
        assert engine.current_datetime is None
        assert engine.equity_curve == []

    def test_calculate_position_value_no_position(self):
        """Test calculating position value when no position exists."""
        config = BacktestConfig()
        engine = BacktestEngine(config)

        value = engine._calculate_position_value("AAPL", 150.0)
        assert value == 0.0

    def test_calculate_position_value_existing_position(self):
        """Test calculating position value for existing position."""
        config = BacktestConfig()
        engine = BacktestEngine(config)

        # Add position
        engine.open_positions["AAPL"] = {"quantity": 10}

        value = engine._calculate_position_value("AAPL", 150.0)
        assert value == 1500.0

    def test_get_total_portfolio_value_empty(self):
        """Test calculating total portfolio value with no positions."""
        config = BacktestConfig(initial_capital=100000.0)
        engine = BacktestEngine(config)

        total_value = engine._get_total_portfolio_value({})
        assert total_value == 100000.0

    def test_get_total_portfolio_value_with_positions(self):
        """Test calculating total portfolio value with open positions."""
        config = BacktestConfig(initial_capital=100000.0)
        engine = BacktestEngine(config)

        # Add positions
        engine.open_positions = {"AAPL": {"quantity": 10}, "GOOG": {"quantity": 5}}
        prices = {"AAPL": 150.0, "GOOG": 100.0}

        total_value = engine._get_total_portfolio_value(prices)
        assert total_value == 100000.0 + (10 * 150.0) + (5 * 100.0)

    def test_execute_trade_buy_success(self):
        """Test successful buy trade execution."""
        config = BacktestConfig(
            initial_capital=100000.0, commission=0.001, slippage=0.0005
        )
        engine = BacktestEngine(config)

        timestamp = datetime.now()
        result = engine._execute_trade("AAPL", "buy", 10, 150.0, timestamp)

        assert result["success"] is True
        assert result["symbol"] == "AAPL"
        assert result["side"] == "buy"
        assert result["quantity"] == 10
        assert result["price"] == 150.0 * (1 + 0.0005)  # Price with slippage
        assert result["commission"] == 10 * 150.0 * 0.001
        assert result["timestamp"] == timestamp

        # Check position was created
        assert "AAPL" in engine.open_positions
        assert engine.open_positions["AAPL"]["quantity"] == 10

    def test_execute_trade_buy_insufficient_capital(self):
        """Test buy trade execution with insufficient capital."""
        config = BacktestConfig(
            initial_capital=1000.0, commission=0.001, slippage=0.0005
        )
        engine = BacktestEngine(config)

        timestamp = datetime.now()
        result = engine._execute_trade("AAPL", "buy", 100, 150.0, timestamp)

        assert result["success"] is False
        assert "error" in result
        assert "AAPL" not in engine.open_positions

    def test_execute_trade_sell_success(self):
        """Test successful sell trade execution."""
        config = BacktestConfig(
            initial_capital=100000.0, commission=0.001, slippage=0.0005
        )
        engine = BacktestEngine(config)

        # First create a position
        timestamp = datetime.now()
        engine._execute_trade("AAPL", "buy", 10, 150.0, timestamp)

        # Now sell it
        sell_result = engine._execute_trade("AAPL", "sell", 5, 160.0, timestamp)

        assert sell_result["success"] is True
        assert sell_result["symbol"] == "AAPL"
        assert sell_result["side"] == "sell"
        assert sell_result["quantity"] == 5
        assert sell_result["price"] == 160.0 * (1 - 0.0005)  # Price with slippage

        # Check position was reduced
        assert engine.open_positions["AAPL"]["quantity"] == 5

    def test_execute_trade_sell_no_position(self):
        """Test sell trade execution with no position."""
        config = BacktestConfig(initial_capital=100000.0)
        engine = BacktestEngine(config)

        timestamp = datetime.now()
        result = engine._execute_trade("AAPL", "sell", 10, 150.0, timestamp)

        assert result["success"] is False
        assert "error" in result

    def test_execute_trade_sell_insufficient_quantity(self):
        """Test sell trade execution with insufficient quantity."""
        config = BacktestConfig(initial_capital=100000.0)
        engine = BacktestEngine(config)

        # Create a small position
        timestamp = datetime.now()
        engine._execute_trade("AAPL", "buy", 5, 150.0, timestamp)

        # Try to sell more than we have
        result = engine._execute_trade("AAPL", "sell", 10, 150.0, timestamp)

        assert result["success"] is False
        assert "error" in result

    def test_execute_trade_add_to_existing_position(self):
        """Test adding to an existing position."""
        config = BacktestConfig(
            initial_capital=100000.0, commission=0.001, slippage=0.0005
        )
        engine = BacktestEngine(config)

        timestamp = datetime.now()

        # First buy
        engine._execute_trade("AAPL", "buy", 10, 150.0, timestamp)
        first_avg_price = engine.open_positions["AAPL"]["avg_price"]

        # Add more at different price
        engine._execute_trade("AAPL", "buy", 5, 160.0, timestamp)
        second_avg_price = engine.open_positions["AAPL"]["avg_price"]

        # Check position was updated
        assert engine.open_positions["AAPL"]["quantity"] == 15
        assert second_avg_price != first_avg_price
        # Weighted average should be a valid positive number
        assert second_avg_price > 0

    def test_execute_trade_close_position_complete(self):
        """Test closing a position completely."""
        config = BacktestConfig(
            initial_capital=100000.0, commission=0.001, slippage=0.0005
        )
        engine = BacktestEngine(config)

        timestamp = datetime.now()

        # Create position
        engine._execute_trade("AAPL", "buy", 10, 150.0, timestamp)

        # Close it completely
        result = engine._execute_trade("AAPL", "sell", 10, 160.0, timestamp)

        assert result["success"] is True
        assert "AAPL" not in engine.open_positions
        assert len(engine.closed_trades) == 1

    def test_execute_trade_stop_loss_check(self):
        """Test that stop loss levels are set correctly."""
        config = BacktestConfig(initial_capital=100000.0, stop_loss_pct=0.05)
        engine = BacktestEngine(config)

        timestamp = datetime.now()
        engine._execute_trade("AAPL", "buy", 10, 150.0, timestamp)

        position = engine.open_positions["AAPL"]
        expected_stop_loss = 150.0 * (1 - 0.05)  # 142.5
        assert position["stop_loss"] == expected_stop_loss

    def test_execute_trade_take_profit_check(self):
        """Test that take profit levels are set correctly."""
        config = BacktestConfig(initial_capital=100000.0, take_profit_pct=0.1)
        engine = BacktestEngine(config)

        timestamp = datetime.now()
        engine._execute_trade("AAPL", "buy", 10, 150.0, timestamp)

        position = engine.open_positions["AAPL"]
        expected_take_profit = 150.0 * (1 + 0.1)  # 165.0
        assert position["take_profit"] == expected_take_profit


@pytest.mark.unit
class TestBacktestEngineIntegration:
    """Integration tests for BacktestEngine."""

    def test_multiple_trades_sequence(self):
        """Test a sequence of multiple trades."""
        config = BacktestConfig(
            initial_capital=100000.0, commission=0.001, slippage=0.0005
        )
        engine = BacktestEngine(config)

        timestamp = datetime.now()

        # Buy AAPL
        result1 = engine._execute_trade("AAPL", "buy", 10, 150.0, timestamp)
        assert result1["success"] is True

        # Buy GOOG
        result2 = engine._execute_trade("GOOG", "buy", 5, 100.0, timestamp)
        assert result2["success"] is True

        # Partial sell AAPL
        result3 = engine._execute_trade("AAPL", "sell", 5, 160.0, timestamp)
        assert result3["success"] is True

        # Sell GOOG completely
        result4 = engine._execute_trade("GOOG", "sell", 5, 110.0, timestamp)
        assert result4["success"] is True

        # Check final state
        assert len(engine.open_positions) == 1  # Only AAPL left
        assert engine.open_positions["AAPL"]["quantity"] == 5
        assert len(engine.closed_trades) == 1  # GOOG trade closed

    def test_portfolio_value_calculation(self):
        """Test portfolio value calculation with multiple positions."""
        config = BacktestConfig(initial_capital=100000.0)
        engine = BacktestEngine(config)

        timestamp = datetime.now()

        # Make some trades
        engine._execute_trade("AAPL", "buy", 10, 150.0, timestamp)
        engine._execute_trade("GOOG", "buy", 5, 100.0, timestamp)
        engine._execute_trade("AAPL", "sell", 2, 160.0, timestamp)

        # Calculate portfolio value
        prices = {"AAPL": 155.0, "GOOG": 105.0}
        portfolio_value = engine._get_total_portfolio_value(prices)

        # Expected: remaining cash + value of open positions
        expected_aapl_value = 8 * 155.0  # Remaining AAPL shares
        expected_goog_value = 5 * 105.0  # All GOOG shares
        expected_total = (
            engine.current_capital + expected_aapl_value + expected_goog_value
        )

        assert portfolio_value == expected_total

    def test_reset_and_reuse(self):
        """Test resetting engine and reusing for new backtest."""
        config = BacktestConfig(initial_capital=100000.0)
        engine = BacktestEngine(config)

        timestamp = datetime.now()

        # Run first backtest
        engine._execute_trade("AAPL", "buy", 10, 150.0, timestamp)
        assert len(engine.open_positions) == 1
        assert engine.current_capital < 100000.0

        # Reset
        engine._reset_state()

        # Verify reset
        assert len(engine.open_positions) == 0
        assert engine.current_capital == 100000.0
        assert len(engine.closed_trades) == 0

        # Run second backtest
        engine._execute_trade("GOOG", "buy", 5, 100.0, timestamp)
        assert len(engine.open_positions) == 1
        assert "GOOG" in engine.open_positions
