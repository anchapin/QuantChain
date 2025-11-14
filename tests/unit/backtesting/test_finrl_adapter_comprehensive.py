"""Comprehensive tests for FinRL adapter."""

import datetime
from unittest.mock import Mock, patch

import numpy as np
import pandas as pd
import pytest

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
class TestFinRLAdapterComprehensive:
    """Comprehensive test cases for FinRLAdapter class."""

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

    def test_adapter_initialization(self, adapter):
        """Test adapter initialization with all parameters."""
        assert adapter.symbol == "AAPL"
        assert adapter.initial_balance == 100000
        assert adapter.reward_strategy == "simple_return"
        assert adapter.balance == 100000
        assert adapter.position == 0.0
        assert adapter.current_step == 0

    def test_setup_data_connector_success(self):
        """Test successful data connector setup."""
        with patch(
            "quantchain.backtesting.finrl_adapter.get_connector"
        ) as mock_get_connector:
            mock_connector = Mock()
            mock_data = pd.DataFrame(
                {"close": [100, 101, 102], "volume": [1000, 1100, 1200]}
            )
            mock_connector.get_historical_data.return_value = mock_data
            mock_get_connector.return_value = mock_connector

            adapter = FinRLAdapter(
                symbol="AAPL",
                start_date="2023-01-01",
                end_date="2023-01-03",
                data_connector="alpaca",
            )

            mock_get_connector.assert_called_once_with("alpaca")
            assert not adapter.market_data.empty

    def test_setup_data_connector_failure(self):
        """Test data connector setup failure."""
        with patch(
            "quantchain.backtesting.finrl_adapter.get_connector"
        ) as mock_get_connector:
            mock_get_connector.side_effect = Exception("Connection failed")

            with pytest.raises(Exception):
                FinRLAdapter(
                    symbol="AAPL",
                    start_date="2023-01-01",
                    end_date="2023-01-03",
                    data_connector="alpaca",
                )

    def test_setup_market_friction_default(self, adapter):
        """Test market friction setup with default configuration."""
        assert adapter.market_friction is not None

    def test_setup_market_friction_custom(self, mock_data_connector):
        """Test market friction setup with custom configuration."""
        config = {"commission": 0.002, "slippage": 0.001, "latency_ms": 100}

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

    def test_setup_observation_spaces_default(self, adapter):
        """Test default observation and action spaces."""
        # Check observation space
        assert adapter.observation_space is not None
        expected_features = [
            "open",
            "high",
            "low",
            "close",
            "volume",
            "rsi",
            "macd",
            "macd_signal",
            "macd_histogram",
            "bb_upper",
            "bb_middle",
            "bb_lower",
            "balance",
            "position",
            "position_value",
            "total_value",
            "pnl_ratio",
            "action_history",
        ]
        assert adapter.observation_features == expected_features

        # Check action space
        assert adapter.action_space is not None
        assert adapter.action_space.shape == (2,)

    def test_setup_observation_spaces_custom(self, mock_data_connector):
        """Test custom observation features."""
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

    def test_add_technical_indicators(self, adapter):
        """Test technical indicators are added to market data."""
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

    def test_reset(self, adapter):
        """Test environment reset."""
        # Simulate some changes first
        adapter.balance = 50000
        adapter.position = 10
        adapter.current_step = 50

        # Reset
        observation = adapter.reset()

        # Check state is reset
        assert adapter.balance == 100000
        assert adapter.position == 0.0
        assert adapter.current_step == 0
        assert adapter.done == False
        assert len(observation) == len(adapter.observation_features)

    def test_step_hold_action(self, adapter):
        """Test step with hold action."""
        action = [0, 0.5]  # Hold action

        obs, reward, done, info = adapter.step(action)

        assert len(obs) == len(adapter.observation_features)
        assert isinstance(reward, float)
        assert isinstance(done, bool)
        assert isinstance(info, dict)
        assert "balance" in info
        assert "position" in info

    def test_step_buy_action(self, adapter):
        """Test step with buy action."""
        action = [1, 0.5]  # Buy 50% of available balance

        initial_balance = adapter.balance
        obs, reward, done, info = adapter.step(action)

        # Should have bought some position
        assert adapter.position > 0
        assert adapter.balance < initial_balance

    def test_step_sell_action(self, adapter):
        """Test step with sell action."""
        # First buy to have position
        adapter.position = 10
        adapter.balance = 50000

        action = [2, 0.5]  # Sell 50% of position

        obs, reward, done, info = adapter.step(action)

        # Should have sold some position
        assert adapter.position < 10

    def test_execute_action_buy_insufficient_balance(self, adapter):
        """Test buy action with insufficient balance."""
        adapter.balance = 100  # Very low balance
        action = [1, 1.0]  # Buy 100% of available balance

        adapter._execute_action(1, 1.0)

        # Should not have bought anything
        assert adapter.position == 0

    def test_execute_action_sell_no_position(self, adapter):
        """Test sell action with no position."""
        adapter.position = 0
        action = [2, 0.5]  # Sell 50% of position

        adapter._execute_action(2, 0.5)

        # Should remain with no position
        assert adapter.position == 0

    def test_get_observation(self, adapter):
        """Test observation generation."""
        obs = adapter._get_observation()

        assert isinstance(obs, np.ndarray)
        assert len(obs) == len(adapter.observation_features)
        assert obs.dtype == np.float32

    def test_calculate_reward_simple_return(self, adapter):
        """Test reward calculation with simple return strategy."""
        adapter.last_total_value = 100000
        adapter.total_value = 101000
        adapter.transaction_costs = 100

        reward = adapter._calculate_reward()

        # Expected: 1% return - transaction cost penalty
        expected = 0.01 - (100 * 0.1)
        assert abs(reward - expected) < 0.01

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
            assert abs(reward - expected) < 0.01

    def test_render(self, adapter, capsys):
        """Test environment rendering."""
        adapter.render()

        captured = capsys.readouterr()
        assert "Step:" in captured.out
        assert "Balance:" in captured.out
        assert "Position:" in captured.out
        assert "Total Value:" in captured.out

    def test_get_performance_metrics(self, adapter):
        """Test performance metrics calculation."""
        # Add some portfolio history
        adapter.portfolio_values = [100000, 101000, 102000, 103000]

        metrics = adapter.get_performance_metrics()

        assert isinstance(metrics, dict)
        assert "total_return" in metrics
        assert "transaction_costs" in metrics
        assert "final_balance" in metrics
        assert "final_position" in metrics
        assert "total_trades" in metrics

    def test_step_done_condition(self, adapter):
        """Test step when environment is done."""
        adapter.current_step = adapter.max_steps
        adapter.done = True

        obs, reward, done, info = adapter.step([0, 0.5])

        assert done is True

    def test_observation_nan_handling(self, adapter):
        """Test handling of NaN values in observation."""
        # Add NaN to market data
        adapter.market_data.iloc[0, 0] = np.nan

        obs = adapter._get_observation()

        # NaN values should be replaced with 0
        assert not np.any(np.isnan(obs))

    def test_get_connector_alpaca(self):
        """Test getting Alpaca connector."""
        with patch("quantchain.backtesting.finrl_adapter.AlpacaDataConnector") as mock_connector:
            get_connector("alpaca", api_key="test", api_secret="test")
            mock_connector.assert_called_once_with(api_key="test", api_secret="test")

    def test_get_connector_polygon(self):
        """Test getting Polygon connector."""
        with patch("quantchain.backtesting.finrl_adapter.PolygonDataConnector") as mock_connector:
            get_connector("polygon", api_key="test")
            mock_connector.assert_called_once_with(api_key="test")

    def test_get_connector_ccxt(self):
        """Test getting CCXT connector."""
        with patch("quantchain.backtesting.finrl_adapter.CCXTDataConnector") as mock_connector:
            get_connector("ccxt", api_key=None, api_secret=None, exchange="binance")
            mock_connector.assert_called_once_with(api_key=None, api_secret=None, exchange="binance")

    def test_get_connector_invalid(self):
        """Test getting invalid connector."""
        with pytest.raises(ValueError, match="Unknown connector"):
            get_connector("invalid")

    def test_adapter_edge_cases(self, mock_data_connector):
        """Test edge cases in adapter behavior."""
        with patch(
            "quantchain.backtesting.finrl_adapter.get_connector",
            return_value=mock_data_connector,
        ):
            # Test with very short date range
            adapter = FinRLAdapter(
                symbol="AAPL",
                start_date="2023-01-01",
                end_date="2023-01-02",
                initial_balance=1000,
            )

            # Should handle gracefully
            obs = adapter.reset()
            assert obs is not None

    def test_parameter_validation_dates(self, mock_data_connector):
        """Test date parameter validation."""
        with patch(
            "quantchain.backtesting.finrl_adapter.get_connector",
            return_value=mock_data_connector,
        ):
            # Should handle valid date formats
            adapter = FinRLAdapter(
                symbol="AAPL",
                start_date="2023-01-01",
                end_date="2023-01-31",
                initial_balance=100000,
            )

            assert adapter.start_date == datetime.datetime(2023, 1, 1)
            assert adapter.end_date == datetime.datetime(2023, 1, 31)
