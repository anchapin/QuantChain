"""Tests for FinRL Adapter"""

# from datetime import datetime, timedelta
from unittest.mock import Mock, patch

import numpy as np
import pandas as pd
import pytest

from quantchain.backtesting.finrl_adapter import FinRLAdapter


class TestFinRLAdapter:
    """Test suite for FinRLAdapter class."""

    @pytest.fixture
    def mock_market_data(self):
        """Create mock market data for testing."""
        dates = pd.date_range(start="2020-01-01", end="2020-01-31", freq="D")
        n_days = len(dates)

        # Generate synthetic price data
        np.random.seed(42)
        base_price = 100
        returns = np.random.normal(0.001, 0.02, n_days)
        prices = base_price * (1 + np.cumsum(returns))

        data = {
            "open": prices * (1 + np.random.normal(0, 0.005, n_days)),
            "high": prices * (1 + np.abs(np.random.normal(0, 0.01, n_days))),
            "low": prices * (1 - np.abs(np.random.normal(0, 0.01, n_days))),
            "close": prices,
            "volume": np.random.randint(100000, 1000000, n_days),
        }

        return pd.DataFrame(data, index=dates)

    @pytest.fixture
    def mock_connector(self, mock_market_data):
        """Create mock data connector."""
        connector = Mock()
        connector.get_historical_data.return_value = mock_market_data
        return connector

    @pytest.fixture
    def adapter(self, mock_connector, mock_market_data):
        """Create FinRL adapter instance for testing."""
        # Ensure the mock returns the DataFrame
        mock_connector.get_historical_data.return_value = mock_market_data

        with patch(
            "quantchain.backtesting.finrl_adapter.get_connector",
            return_value=mock_connector,
        ):
            adapter = FinRLAdapter(
                symbol="TEST",
                start_date="2020-01-01",
                end_date="2020-01-31",
                initial_balance=100000,
                market_friction_config={"commission": 0.001, "slippage": 0.0005},
            )
            return adapter

    def test_adapter_initialization(self, adapter):
        """Test adapter initialization."""
        assert adapter.symbol == "TEST"
        assert adapter.initial_balance == 100000
        assert adapter.balance == 100000
        assert adapter.position == 0
        assert adapter.total_value == 100000
        assert not adapter.done

    def test_observation_space(self, adapter):
        """Test observation space setup."""
        assert adapter.observation_space is not None
        assert hasattr(adapter.observation_space, "shape")
        assert len(adapter.observation_features) == adapter.observation_space.shape[0]

    def test_action_space(self, adapter):
        """Test action space setup."""
        assert adapter.action_space is not None
        assert adapter.action_space.shape == (2,)
        assert adapter.action_space.low[0] == 0
        assert adapter.action_space.high[0] == 2
        assert adapter.action_space.low[1] == 0
        assert adapter.action_space.high[1] == 1

    def test_reset(self, adapter):
        """Test environment reset."""
        # Perform some actions first
        adapter.step([1, 0.5])
        adapter.step([2, 0.25])

        # Reset and verify state
        obs = adapter.reset()

        assert adapter.current_step == 0
        assert not adapter.done
        assert adapter.balance == adapter.initial_balance
        assert adapter.position == 0
        assert adapter.total_value == adapter.initial_balance

        assert isinstance(obs, np.ndarray)
        assert obs.shape == adapter.observation_space.shape

    def test_step_hold(self, adapter):
        """Test step with hold action."""
        initial_state = adapter._get_observation()
        initial_balance = adapter.balance

        obs, reward, done, info = adapter.step([0, 0])

        assert isinstance(obs, np.ndarray)
        assert isinstance(reward, float)
        assert isinstance(done, bool)
        assert isinstance(info, dict)

        # Hold shouldn't change balance significantly (just minor fees)
        assert abs(adapter.balance - initial_balance) < 100

        assert "balance" in info
        assert "position" in info
        assert "total_value" in info

    def test_step_buy(self, adapter):
        """Test step with buy action."""
        initial_balance = adapter.balance
        initial_position = adapter.position

        obs, reward, done, info = adapter.step([1, 0.5])  # Buy with 50% of balance

        assert adapter.position > initial_position
        assert adapter.balance < initial_balance
        assert adapter.transaction_costs > 0

    def test_step_sell(self, adapter):
        """Test step with sell action."""
        # First buy some shares
        adapter.step([1, 0.5])

        initial_balance = adapter.balance
        initial_position = adapter.position

        # Now sell half
        obs, reward, done, info = adapter.step([2, 0.5])

        assert adapter.position < initial_position
        assert adapter.balance > initial_balance

    def test_observation_features(self, adapter):
        """Test observation extraction."""
        obs = adapter._get_observation()

        assert len(obs) == len(adapter.observation_features)

        # Check that all features are numeric (including numpy types)
        assert all(isinstance(x, (int, float, np.floating)) for x in obs)

    def test_reward_calculation(self, adapter):
        """Test reward calculation strategies."""
        # Test simple return
        adapter.reward_strategy = "simple_return"
        reward = adapter._calculate_reward()
        assert isinstance(reward, float)

        # Test log return
        adapter.reward_strategy = "log_return"
        reward = adapter._calculate_reward()
        assert isinstance(reward, float)

        # Test risk adjusted return
        adapter.reward_strategy = "risk_adjusted_return"
        reward = adapter._calculate_reward()
        assert isinstance(reward, float)

    def test_market_friction_integration(self, adapter):
        """Test that market frictions are applied."""
        initial_balance = adapter.balance

        # Buy and sell to incur costs
        adapter.step([1, 0.5])  # Buy
        adapter.step([2, 0.5])  # Sell

        # Should have transaction costs
        assert adapter.transaction_costs > 0

        # Balance should be less than initial due to frictions
        assert adapter.balance < initial_balance

    def test_performance_metrics(self, adapter):
        """Test performance metrics calculation."""
        # Perform some trades
        for _ in range(5):
            action = np.random.choice([0, 1, 2])
            amount = np.random.random()
            adapter.step([action, amount])

        metrics = adapter.get_performance_metrics()

        assert isinstance(metrics, dict)
        assert "total_return" in metrics
        assert "transaction_costs" in metrics
        assert "final_balance" in metrics
        assert "final_position" in metrics

    def test_done_condition(self, adapter):
        """Test environment done condition."""
        adapter.max_steps = 5
        adapter.current_step = 4

        obs, reward, done, info = adapter.step([0, 0])

        assert done
        assert adapter.current_step == 5

    def test_render(self, adapter, capsys):
        """Test render method."""
        adapter.render(mode="human")
        captured = capsys.readouterr()

        assert "Step:" in captured.out
        assert "Balance:" in captured.out
        assert "Position:" in captured.out

    def test_technical_indicators(self, adapter):
        """Test technical indicators are calculated."""
        data = adapter.market_data

        assert "rsi" in data.columns
        assert "macd" in data.columns
        assert "macd_signal" in data.columns
        assert "bb_upper" in data.columns
        assert "bb_middle" in data.columns
        assert "bb_lower" in data.columns

    def test_portfolio_value_tracking(self, adapter):
        """Test portfolio value is tracked correctly."""
        initial_value = adapter.total_value

        # Buy some shares
        adapter.step([1, 0.5])

        # Portfolio value should change (but not drastically)
        assert adapter.total_value != initial_value

    def test_custom_observation_features(self, mock_connector):
        """Test custom observation features configuration."""
        custom_features = ["open", "close", "balance", "position"]

        with patch(
            "quantchain.backtesting.finrl_adapter.get_connector",
            return_value=mock_connector,
        ):
            adapter = FinRLAdapter(
                symbol="TEST",
                start_date="2020-01-01",
                end_date="2020-01-31",
                observation_features=custom_features,
            )

            assert adapter.observation_features == custom_features
            assert adapter.observation_space.shape == (len(custom_features),)

    def test_market_friction_config(self, mock_connector):
        """Test custom market friction configuration."""
        custom_friction = {"commission": 0.002, "slippage": 0.001, "latency_ms": 100}

        with patch(
            "quantchain.backtesting.finrl_adapter.get_connector",
            return_value=mock_connector,
        ):
            adapter = FinRLAdapter(
                symbol="TEST",
                start_date="2020-01-01",
                end_date="2020-01-31",
                market_friction_config=custom_friction,
            )

            assert adapter.market_friction.config.commission_model.rate == 0.002
            assert adapter.market_friction.config.slippage_model.base_rate == 0.001

    def test_edge_cases(self, adapter):
        """Test edge cases and error handling."""
        # Test with empty action
        with pytest.raises((IndexError, ValueError)):
            adapter.step([])

        # Test with invalid action values
        # These should be handled gracefully by the adapter
        adapter.step([5, 0])  # Invalid action type
        adapter.step([1, 2])  # Invalid amount > 1

    def test_integration_with_finrl_agents(self, adapter):
        """Test compatibility with FinRL agents pattern."""
        # This test verifies the adapter follows FinRL's gym interface

        # Reset should work
        obs = adapter.reset()
        assert isinstance(obs, np.ndarray)

        # Multiple steps should work
        for _ in range(5):
            action = adapter.action_space.sample()
            obs, reward, done, info = adapter.step(action)

            assert obs.shape == adapter.observation_space.shape
            assert isinstance(reward, float)
            assert isinstance(done, bool)
            assert isinstance(info, dict)

            if done:
                break
