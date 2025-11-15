"""Basic tests for the FinRL adapter."""

import os
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import pandas as pd
import pytest
import numpy as np
from datetime import datetime, timedelta

# Add the parent directory to the path to import the module
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from alpaca.data import TimeFrame
from quantchain.backtesting.finrl_adapter import (
    FinRLAdapter,
    FinRLConfig,
    FinRLPortfolio,
    FinRLStrategy,
    FinRLResult,
    FinRLError
)


class TestFinRLAdapter:
    """Test basic functionality of the FinRL adapter."""

    def test_initialization_with_config(self):
        """Test adapter initialization with custom config."""
        config = FinRLConfig(
            initial_cash=100000,
            initial_position={},
            buy_cost_pct=0.001,
            sell_cost_pct=0.001,
            min_cost_pct=0.001
        )

        adapter = FinRLAdapter(config)
        assert adapter.config == config
        assert adapter.portfolio.initial_cash == 100000
        assert adapter.portfolio.initial_position == {}

    def test_initialization_with_default_config(self):
        """Test adapter initialization with default config."""
        adapter = FinRLAdapter()

        assert adapter.config is not None
        assert adapter.portfolio.initial_cash == 1000000
        assert adapter.portfolio.initial_position == {}

    @patch('quantchain.backtesting.finrl_adapter.pd.DataFrame')
    def test_reset(self, mock_dataframe):
        """Test resetting the adapter state."""
        mock_dataframe.return_value = Mock()

        adapter = FinRLAdapter()
        adapter.reset()

        # Should create new portfolio with initial values
        assert adapter.portfolio.initial_cash == 1000000
        assert adapter.portfolio.initial_position == {}

    @patch('quantchain.backtesting.finrl_adapter.pd.DataFrame')
    def test_trade_action_buy(self, mock_dataframe):
        """Test processing a buy action."""
        mock_dataframe.return_value = Mock()

        adapter = FinRLAdapter()
        adapter.reset()

        # Mock data for testing
        state = pd.DataFrame({
            'open': [100],
            'high': [105],
            'low': [95],
            'close': [102],
            'volume': [10000]
        })

        action = {'action': 1}  # Buy signal
        result = adapter.trade(state, action)

        assert isinstance(result, dict)
        assert 'status' in result
        assert 'amount' in result
        assert 'cost' in result

    @patch('quantchain.backtesting.finrl_adapter.pd.DataFrame')
    def test_trade_action_sell(self, mock_dataframe):
        """Test processing a sell action."""
        mock_dataframe.return_value = Mock()

        adapter = FinRLAdapter()
        adapter.reset()

        # Mock data for testing
        state = pd.DataFrame({
            'open': [100],
            'high': [105],
            'low': [95],
            'close': [102],
            'volume': [10000]
        })

        # First buy to have a position
        adapter.portfolio.positions = {'AAPL': 10}

        action = {'action': 2}  # Sell signal
        result = adapter.trade(state, action)

        assert isinstance(result, dict)
        assert 'status' in result
        assert 'amount' in result
        assert 'cost' in result

    @patch('quantchain.backtesting.finrl_adapter.pd.DataFrame')
    def test_trade_action_hold(self, mock_dataframe):
        """Test processing a hold action."""
        mock_dataframe.return_value = Mock()

        adapter = FinRLAdapter()
        adapter.reset()

        # Mock data for testing
        state = pd.DataFrame({
            'open': [100],
            'high': [105],
            'low': [95],
            'close': [102],
            'volume': [10000]
        })

        action = {'action': 0}  # Hold signal
        result = adapter.trade(state, action)

        assert isinstance(result, dict)
        assert 'status' in result
        assert result['status'] == 'hold'

    def test_get_state(self):
        """Test getting the current state."""
        adapter = FinRLAdapter()
        adapter.reset()

        # Create mock portfolio
        adapter.portfolio.portfolio_value = 100000
        adapter.portfolio.positions = {'AAPL': 10}
        adapter.portfolio.cash = 90000

        state = adapter.get_state()

        assert isinstance(state, dict)
        assert 'portfolio_value' in state
        assert 'cash' in state
        assert 'positions' in state


class TestFinRLConfig:
    """Test the FinRLConfig data class."""

    def test_default_values(self):
        """Test default config values."""
        config = FinRLConfig()

        assert config.initial_cash == 1000000
        assert config.initial_position == {}
        assert config.buy_cost_pct == 0.001
        assert config.sell_cost_pct == 0.001
        assert config.min_cost_pct == 0.001

    def test_custom_values(self):
        """Test custom config values."""
        config = FinRLConfig(
            initial_cash=500000,
            initial_position={'AAPL': 100},
            buy_cost_pct=0.002,
            sell_cost_pct=0.002,
            min_cost_pct=0.002
        )

        assert config.initial_cash == 500000
        assert config.initial_position == {'AAPL': 100}
        assert config.buy_cost_pct == 0.002
        assert config.sell_cost_pct == 0.002
        assert config.min_cost_pct == 0.002


class TestFinRLPortfolio:
    """Test the FinRLPortfolio class."""

    def test_initialization(self):
        """Test portfolio initialization."""
        portfolio = FinRLPortfolio(
            initial_cash=100000,
            initial_position={'AAPL': 100}
        )

        assert portfolio.initial_cash == 100000
        assert portfolio.initial_position == {'AAPL': 100}
        assert portfolio.cash == 100000
        assert portfolio.positions == {'AAPL': 100}

    def test_reset(self):
        """Test resetting the portfolio."""
        portfolio = FinRLPortfolio(
            initial_cash=100000,
            initial_position={'AAPL': 100}
        )

        # Make some changes
        portfolio.cash = 50000
        portfolio.positions = {'GOOGL': 50}

        # Reset
        portfolio.reset()

        # Should return to initial values
        assert portfolio.cash == 100000
        assert portfolio.positions == {'AAPL': 100}

    def test_buy_stock(self):
        """Test buying stock."""
        portfolio = FinRLPortfolio(
            initial_cash=100000,
            initial_position={}
        )

        # Buy 10 shares at $100 each with 0.1% cost
        result = portfolio.buy_stock('AAPL', 10, 100, 0.001)

        assert result is True
        assert portfolio.cash == 100000 - 1000 - 1  # Cash - (shares * price) - cost
        assert portfolio.positions['AAPL'] == 10

    def test_sell_stock(self):
        """Test selling stock."""
        portfolio = FinRLPortfolio(
            initial_cash=100000,
            initial_position={'AAPL': 10}
        )

        # Sell 10 shares at $100 each with 0.1% cost
        result = portfolio.sell_stock('AAPL', 10, 100, 0.001)

        assert result is True
        assert portfolio.cash == 100000 + 1000 - 1  # Cash + (shares * price) - cost
        assert 'AAPL' not in portfolio.positions

    def test_buy_insufficient_cash(self):
        """Test buying with insufficient cash."""
        portfolio = FinRLPortfolio(
            initial_cash=100,
            initial_position={}
        )

        # Try to buy 10 shares at $100 each (need $1000 but only have $100)
        result = portfolio.buy_stock('AAPL', 10, 100, 0.001)

        assert result is False
        assert portfolio.cash == 100  # Cash unchanged
        assert 'AAPL' not in portfolio.positions

    def test_sell_insufficient_position(self):
        """Test selling with insufficient position."""
        portfolio = FinRLPortfolio(
            initial_cash=100000,
            initial_position={'AAPL': 5}
        )

        # Try to sell 10 shares but only have 5
        result = portfolio.sell_stock('AAPL', 10, 100, 0.001)

        assert result is False
        assert portfolio.cash == 100000  # Cash unchanged
        assert portfolio.positions['AAPL'] == 5  # Position unchanged

    def test_get_total_value(self):
        """Test getting total portfolio value."""
        portfolio = FinRLPortfolio(
            initial_cash=100000,
            initial_position={'AAPL': 10}
        )

        # Mock current price
        current_prices = {'AAPL': 100}

        total_value = portfolio.get_total_value(current_prices)

        assert total_value == 100000 + 10 * 100  # Cash + (shares * price)


class TestFinRLStrategy:
    """Test the FinRLStrategy class."""

    def test_initialization(self):
        """Test strategy initialization."""
        strategy = FinRLStrategy(strategy_type='dqn', params={'learning_rate': 0.001})

        assert strategy.strategy_type == 'dqn'
        assert strategy.params == {'learning_rate': 0.001}

    def test_predict_action(self):
        """Test predicting an action."""
        strategy = FinRLStrategy(strategy_type='dqn')

        # Mock state
        state = pd.DataFrame({
            'close': [100, 102, 101],
            'volume': [1000, 1200, 1100]
        })

        action = strategy.predict(state)

        assert isinstance(action, dict)
        assert 'action' in action


class TestFinRLResult:
    """Test the FinRLResult data class."""

    def test_result_creation(self):
        """Test creating a result."""
        result = FinRLResult(
            total_return=0.15,
            annualized_return=0.12,
            sharpe_ratio=1.5,
            max_drawdown=0.05,
            win_rate=0.6,
            total_trades=100
        )

        assert result.total_return == 0.15
        assert result.annualized_return == 0.12
        assert result.sharpe_ratio == 1.5
        assert result.max_drawdown == 0.05
        assert result.win_rate == 0.6
        assert result.total_trades == 100


class TestFinRLError:
    """Test the FinRLError exception."""

    def test_error_creation(self):
        """Test creating an error."""
        error = FinRLError("Test error message")

        assert str(error) == "Test error message"
