"""Extended tests for FinRL adapter to increase coverage."""

import numpy as np
import pandas as pd
import pytest
from unittest.mock import Mock, patch, MagicMock

try:
    from quantchain.backtesting.finrl_adapter import (
        FinRLAdapter,
        FinRLAdapterError,
        FinRLConnectionError,
        FinRLDataError,
        get_connector,
    )

    FINRL_ADAPTER_AVAILABLE = True
except ImportError as e:
    FINRL_ADAPTER_AVAILABLE = False
    print(f"Import error: {e}")

pytestmark = pytest.mark.skipif(
    not FINRL_ADAPTER_AVAILABLE, reason="FinRL adapter not available"
)


@pytest.mark.unit
class TestFinRLAdapterExtended:
    """Extended test cases for FinRLAdapter class to improve coverage."""

    @pytest.fixture
    def mock_data_connector(self):
        """Mock data connector with realistic data."""
        connector = Mock()

        # Create realistic market data with deterministic values
        dates = pd.date_range("2023-01-01", periods=100, freq="1D")
        
        # Use deterministic price series
        prices = [100 + i * 0.1 for i in range(100)]  # Simple increasing price
        volumes = [1000000 + i * 10000 for i in range(100)]  # Increasing volume

        # Generate OHLC data from close prices
        data = pd.DataFrame(
            {
                "timestamp": dates,
                "open": prices,
                "high": [p * 1.02 for p in prices],
                "low": [p * 0.98 for p in prices],
                "close": prices,
                "volume": volumes,
            }
        )
        # Set timestamp as index for proper pandas operations
        data = data.set_index('timestamp')

        connector.get_historical_data.return_value = data
        return connector

    @pytest.fixture
    def adapter(self, mock_data_connector):
        """Create test adapter with mocked connector."""
        with patch(
            "quantchain.backtesting.finrl_adapter.get_connector",
            return_value=mock_data_connector,
        ):
            return FinRLAdapter(
                symbol="AAPL",
                start_date="2023-01-01",
                end_date="2023-04-10",
                initial_balance=100000,
                data_connector="alpaca",
                market_friction_config=None,
                observation_features=None,
                reward_strategy="simple_return",
            )

    def test_setup_market_friction_with_config(self, mock_data_connector):
        """Test market friction setup with custom configuration."""
        config = {
            "commission": 0.002,
            "slippage": 0.001,
            "latency_ms": 100
        }

        with patch(
            "quantchain.backtesting.finrl_adapter.get_connector",
            return_value=mock_data_connector,
        ):
            adapter = FinRLAdapter(
                symbol="AAPL",
                start_date="2023-01-01",
                end_date="2023-01-03",
                market_friction_config=config,
            )
            
            assert adapter.market_friction is not None
            assert adapter.market_friction.config.commission_model.rate == 0.002

    def test_setup_market_friction_default_config(self, mock_data_connector):
        """Test market friction setup with default configuration."""
        with patch(
            "quantchain.backtesting.finrl_adapter.get_connector",
            return_value=mock_data_connector,
        ):
            adapter = FinRLAdapter(
                symbol="AAPL",
                start_date="2023-01-01",
                end_date="2023-01-03",
                market_friction_config=None,
            )
            
            assert adapter.market_friction is not None

    def test_setup_performance_metrics(self, adapter):
        """Test performance metrics setup."""
        assert adapter.performance_metrics is not None
        assert hasattr(adapter.performance_metrics, 'calculate_all_metrics')

    def test_setup_spaces_custom_features(self, mock_data_connector):
        """Test custom observation spaces setup."""
        custom_features = ["close", "volume", "balance", "position"]

        with patch(
            "quantchain.backtesting.finrl_adapter.get_connector",
            return_value=mock_data_connector,
        ):
            adapter = FinRLAdapter(
                symbol="AAPL",
                start_date="2023-01-01",
                end_date="2023-01-03",
                observation_features=custom_features,
            )
            
            assert adapter.observation_features == custom_features
            assert adapter.observation_space.shape == (4,)
            assert adapter.action_space.shape == (2,)

    def test_add_technical_indicators(self, adapter):
        """Test technical indicators are added correctly."""
        # Check that technical indicators are present
        expected_indicators = [
            "rsi",
            "macd",
            "macd_signal",
            "macd_histogram",
            "bb_upper",
            "bb_middle",
            "bb_lower",
        ]

        for indicator in expected_indicators:
            assert indicator in adapter.market_data.columns

    def test_reset_environment(self, adapter):
        """Test environment reset functionality."""
        # Simulate some changes first
        adapter.balance = 50000
        adapter.position = 10
        adapter.current_step = 50
        adapter.done = True

        # Reset
        observation = adapter.reset(seed=42)  # Test with seed parameter

        # Check state is reset
        assert adapter.balance == 100000
        assert adapter.position == 0.0
        assert adapter.current_step == 0
        assert adapter.done == False
        assert len(observation) == len(adapter.observation_features)

    def test_step_with_buy_action(self, adapter):
        """Test step with buy action."""
        adapter.reset()
        
        # Action: [action_type(1=buy), amount(0.5=50%)]
        action = np.array([1, 0.5])
        initial_balance = adapter.balance

        obs, reward, done, truncated, info = adapter.step(action)

        # Should have bought some position
        assert adapter.position > 0
        assert adapter.balance < initial_balance
        assert len(obs) == len(adapter.observation_features)
        assert isinstance(reward, (int, float))
        assert isinstance(done, bool)
        assert isinstance(truncated, bool)
        assert isinstance(info, dict)

    def test_step_with_sell_action(self, adapter):
        """Test step with sell action."""
        adapter.reset()
        
        # First buy to have position
        adapter.position = 10
        adapter.balance = 50000

        # Action: [action_type(2=sell), amount(0.5=50%)]
        action = np.array([2, 0.5])

        obs, reward, done, truncated, info = adapter.step(action)

        # Should have sold some position
        assert adapter.position < 10
        assert len(obs) == len(adapter.observation_features)

    def test_step_with_hold_action(self, adapter):
        """Test step with hold action."""
        adapter.reset()
        
        # Action: [action_type(0=hold), amount]
        action = np.array([0, 0.5])  # amount doesn't matter for hold

        obs, reward, done, truncated, info = adapter.step(action)

        # Position and balance should remain unchanged (except for price changes)
        assert len(obs) == len(adapter.observation_features)
        assert isinstance(reward, (int, float))
        assert isinstance(done, bool)

    def test_execute_action_buy_insufficient_balance(self, adapter):
        """Test buy action with insufficient balance."""
        adapter.balance = 100  # Very low balance
        action_type = 1
        amount = 1.0  # Buy 100% of available balance

        adapter._execute_action(action_type, amount)

        # Should not have bought anything
        assert adapter.position == 0

    def test_execute_action_sell_no_position(self, adapter):
        """Test sell action with no position."""
        adapter.position = 0
        action_type = 2
        amount = 0.5

        adapter._execute_action(action_type, amount)

        # Should remain with no position
        assert adapter.position == 0

    def test_execute_action_invalid_type(self, adapter):
        """Test execute action with invalid type."""
        action_type = 99  # Invalid action type
        amount = 0.5

        # Should handle gracefully
        adapter._execute_action(action_type, amount)

    def test_get_observation(self, adapter):
        """Test observation generation."""
        obs = adapter._get_observation()

        assert isinstance(obs, np.ndarray)
        assert len(obs) == len(adapter.observation_features)
        assert obs.dtype == np.float32

    def test_get_observation_with_nan_values(self, adapter):
        """Test observation generation with NaN values."""
        # Add NaN to market data
        adapter.market_data.iloc[0, 0] = np.nan

        obs = adapter._get_observation()

        # NaN values should be replaced with 0
        assert not np.any(np.isnan(obs))

    def test_calculate_reward_simple_return(self, adapter):
        """Test reward calculation with simple return strategy."""
        adapter.reward_strategy = "simple_return"
        adapter.last_total_value = 100000
        adapter.total_value = 101000
        adapter.transaction_costs = 100

        reward = adapter._calculate_reward()

        # Expected: 1% return - transaction cost penalty
        expected = 0.01 - (100 * 0.1)  # 0.1 is cost factor
        assert abs(reward - expected) < 0.001

    def test_calculate_reward_log_return(self, mock_data_connector):
        """Test reward calculation with log return strategy."""
        with patch(
            "quantchain.backtesting.finrl_adapter.get_connector",
            return_value=mock_data_connector,
        ):
            adapter = FinRLAdapter(
                symbol="AAPL",
                start_date="2023-01-01",
                end_date="2023-01-03",
                reward_strategy="log_return",
            )

            adapter.last_total_value = 100000
            adapter.total_value = 101000

            reward = adapter._calculate_reward()

            # Expected: log(101000/100000)
            expected = np.log(101000 / 100000)
            assert abs(reward - expected) < 0.001

    def test_calculate_reward_sharpe_ratio(self, mock_data_connector):
        """Test reward calculation with Sharpe ratio strategy."""
        with patch(
            "quantchain.backtesting.finrl_adapter.get_connector",
            return_value=mock_data_connector,
        ):
            adapter = FinRLAdapter(
                symbol="AAPL",
                start_date="2023-01-01",
                end_date="2023-01-03",
                reward_strategy="sharpe_ratio",
            )

            # Add some portfolio values for Sharpe calculation
            adapter.portfolio_values = [100000, 101000, 102000, 103000]
            adapter.last_total_value = 101000
            adapter.total_value = 102000

            reward = adapter._calculate_reward()
            assert isinstance(reward, float)

    def test_calculate_reward_risk_adjusted(self, mock_data_connector):
        """Test reward calculation with risk-adjusted return strategy."""
        with patch(
            "quantchain.backtesting.finrl_adapter.get_connector",
            return_value=mock_data_connector,
        ):
            adapter = FinRLAdapter(
                symbol="AAPL",
                start_date="2023-01-01",
                end_date="2023-01-03",
                reward_strategy="risk_adjusted_return",
            )

            # Add some portfolio values for risk calculation
            adapter.portfolio_values = [100000, 101000, 102000]
            adapter.last_total_value = 101000
            adapter.total_value = 102000

            reward = adapter._calculate_reward()
            assert isinstance(reward, float)

    def test_render_mode_human(self, adapter, capsys):
        """Test environment rendering in human mode."""
        adapter.render(mode="human")

        captured = capsys.readouterr()
        assert "Step:" in captured.out
        assert "Balance:" in captured.out
        assert "Position:" in captured.out
        assert "Total Value:" in captured.out

    def test_get_performance_metrics(self, adapter):
        """Test performance metrics calculation."""
        # Add some portfolio history
        adapter.portfolio_values = [100000, 101000, 102000, 103000]
        adapter.transaction_costs = 500

        metrics = adapter.get_performance_metrics()

        assert isinstance(metrics, dict)
        assert "total_return" in metrics
        assert "transaction_costs" in metrics
        assert "final_balance" in metrics
        assert "final_position" in metrics
        assert "total_trades" in metrics

    def test_step_done_condition(self, adapter):
        """Test step when environment is done."""
        adapter.reset()
        adapter.current_step = adapter.max_steps
        adapter.done = True

        obs, reward, done, truncated, info = adapter.step([0, 0.5])

        assert done is True

    def test_close_method(self, adapter):
        """Test environment close method."""
        # Should not raise
        adapter.close()

    def test_seed_method(self, adapter):
        """Test seed method for reproducibility."""
        seed = 42
        result = adapter.seed(seed)
        
        # Result should be an array/list
        assert result is not None
