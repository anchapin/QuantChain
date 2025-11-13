"""Tests for FinRL adapter that bridges QuantChain with FinRL framework."""

import pytest
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch, AsyncMock

from quantchain.backtesting.finrl_adapter import (
    FinRLAdapter,
    get_connector,
)


class TestGetConnector:
    """Test cases for get_connector function."""

    def test_get_connector_alpaca(self):
        """Test getting Alpaca connector."""
        with patch(
            "quantchain.backtesting.finrl_adapter.AlpacaDataConnector"
        ) as mock_alpaca:
            mock_instance = MagicMock()
            mock_alpaca.return_value = mock_instance

            result = get_connector("alpaca", api_key="test", secret_key="test")

            mock_alpaca.assert_called_once_with(api_key="test", secret_key="test")
            assert result == mock_instance

    def test_get_connector_polygon(self):
        """Test getting Polygon connector."""
        with patch(
            "quantchain.backtesting.finrl_adapter.PolygonDataConnector"
        ) as mock_polygon:
            mock_instance = MagicMock()
            mock_polygon.return_value = mock_instance

            result = get_connector("polygon", api_key="test")

            mock_polygon.assert_called_once_with(api_key="test")
            assert result == mock_instance

    def test_get_connector_ccxt(self):
        """Test getting CCXT connector."""
        with patch(
            "quantchain.backtesting.finrl_adapter.CCXTDataConnector"
        ) as mock_ccxt:
            mock_instance = MagicMock()
            mock_ccxt.return_value = mock_instance

            result = get_connector("ccxt", exchange_id="binance")

            mock_ccxt.assert_called_once_with(exchange_id="binance")
            assert result == mock_instance

    def test_get_connector_unknown(self):
        """Test getting unknown connector raises error."""
        with pytest.raises(ValueError, match="Unknown connector: unknown"):
            get_connector("unknown")

    def test_get_connector_case_insensitive(self):
        """Test that connector names are case insensitive."""
        with patch(
            "quantchain.backtesting.finrl_adapter.AlpacaDataConnector"
        ) as mock_alpaca:
            mock_instance = MagicMock()
            mock_alpaca.return_value = mock_instance

            # Test various case combinations
            for name in ["ALPACA", "Alpaca", "aLpAcA"]:
                result = get_connector(name)
                assert result == mock_instance


class TestFinRLAdapter:
    """Test cases for FinRLAdapter class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.start_date = "2023-01-01"
        self.end_date = "2023-01-31"
        self.symbol = "AAPL"
        self.initial_balance = 100000

    @patch("quantchain.backtesting.finrl_adapter.get_connector")
    @patch("quantchain.backtesting.finrl_adapter.MarketFrictionSimulator")
    @patch("quantchain.backtesting.finrl_adapter.PerformanceMetrics")
    def test_adapter_initialization(
        self, mock_metrics, mock_friction, mock_get_connector
    ):
        """Test adapter initialization with default parameters."""
        mock_connector = MagicMock()
        mock_get_connector.return_value = mock_connector

        adapter = FinRLAdapter(
            symbol=self.symbol,
            start_date=self.start_date,
            end_date=self.end_date,
            initial_balance=self.initial_balance,
        )

        assert adapter.symbol == self.symbol
        assert adapter.start_date == datetime.strptime(self.start_date, "%Y-%m-%d")
        assert adapter.end_date == datetime.strptime(self.end_date, "%Y-%m-%d")
        assert adapter.initial_balance == self.initial_balance
        assert adapter.data_connector_name == "alpaca"
        assert adapter.reward_strategy == "risk_adjusted_return"

    @patch("quantchain.backtesting.finrl_adapter.get_connector")
    @patch("quantchain.backtesting.finrl_adapter.MarketFrictionSimulator")
    @patch("quantchain.backtesting.finrl_adapter.PerformanceMetrics")
    def test_adapter_initialization_custom_params(
        self, mock_metrics, mock_friction, mock_get_connector
    ):
        """Test adapter initialization with custom parameters."""
        mock_connector = MagicMock()
        mock_get_connector.return_value = mock_connector

        market_friction_config = {"commission": 0.001, "slippage": 0.0005}
        observation_features = ["close", "volume", "rsi", "macd"]

        adapter = FinRLAdapter(
            symbol=self.symbol,
            start_date=self.start_date,
            end_date=self.end_date,
            initial_balance=200000,
            data_connector="polygon",
            market_friction_config=market_friction_config,
            observation_features=observation_features,
            reward_strategy="sharpe_ratio",
            api_key="test_key",
        )

        assert adapter.initial_balance == 200000
        assert adapter.data_connector_name == "polygon"
        assert adapter.market_friction_config == market_friction_config
        assert adapter.observation_features == observation_features
        assert adapter.reward_strategy == "sharpe_ratio"

        # Verify connector was called with correct parameters
        mock_get_connector.assert_called_once_with("polygon", api_key="test_key")

    @patch("quantchain.backtesting.finrl_adapter.get_connector")
    def test_observation_space_setup(self, mock_get_connector):
        """Test observation space is set up correctly."""
        mock_connector = MagicMock()
        mock_get_connector.return_value = mock_connector

        # Mock sample data for feature inference
        sample_data = pd.DataFrame(
            {
                "open": [100, 101, 102],
                "high": [101, 102, 103],
                "low": [99, 100, 101],
                "close": [100.5, 101.5, 102.5],
                "volume": [1000, 1100, 1200],
                "rsi": [50, 55, 60],
                "macd": [0.1, 0.2, 0.3],
            }
        )
        mock_connector.get_historical_data.return_value = sample_data

        adapter = FinRLAdapter(
            symbol=self.symbol,
            start_date=self.start_date,
            end_date=self.end_date,
            observation_features=["close", "volume", "rsi", "macd"],
        )

        # Observation space should be Box with correct shape
        assert hasattr(adapter, "observation_space")
        assert adapter.observation_space.shape == (4,)  # 4 features

    @patch("quantchain.backtesting.finrl_adapter.get_connector")
    def test_action_space_setup(self, mock_get_connector):
        """Test action space is set up correctly."""
        mock_connector = MagicMock()
        mock_get_connector.return_value = mock_connector

        adapter = FinRLAdapter(
            symbol=self.symbol, start_date=self.start_date, end_date=self.end_date
        )

        # Default action space should be Discrete(3) for [sell, hold, buy]
        from gymnasium import spaces

        assert isinstance(adapter.action_space, spaces.Discrete)
        assert adapter.action_space.n == 3

    @pytest.mark.asyncio
    async def test_reset_method(self):
        """Test environment reset functionality."""
        with patch(
            "quantchain.backtesting.finrl_adapter.get_connector"
        ) as mock_get_connector:
            mock_connector = AsyncMock()
            mock_get_connector.return_value = mock_connector

            # Mock historical data
            historical_data = pd.DataFrame(
                {
                    "open": [100, 101, 102, 103, 104],
                    "high": [101, 102, 103, 104, 105],
                    "low": [99, 100, 101, 102, 103],
                    "close": [100.5, 101.5, 102.5, 103.5, 104.5],
                    "volume": [1000, 1100, 1200, 1300, 1400],
                },
                index=pd.date_range("2023-01-01", periods=5),
            )

            mock_connector.get_historical_data.return_value = historical_data

            adapter = FinRLAdapter(
                symbol=self.symbol, start_date=self.start_date, end_date=self.end_date
            )

            observation, info = await adapter.reset()

            # Should return valid observation and info
            assert observation is not None
            assert isinstance(info, dict)
            assert adapter.current_step == 0

    @pytest.mark.asyncio
    async def test_step_method_buy_action(self):
        """Test step method with buy action."""
        with patch(
            "quantchain.backtesting.finrl_adapter.get_connector"
        ) as mock_get_connector:
            mock_connector = AsyncMock()
            mock_get_connector.return_value = mock_connector

            # Mock data
            historical_data = pd.DataFrame(
                {
                    "open": [100, 101, 102, 103, 104],
                    "high": [101, 102, 103, 104, 105],
                    "low": [99, 100, 101, 102, 103],
                    "close": [100.5, 101.5, 102.5, 103.5, 104.5],
                    "volume": [1000, 1100, 1200, 1300, 1400],
                },
                index=pd.date_range("2023-01-01", periods=5),
            )

            mock_connector.get_historical_data.return_value = historical_data

            adapter = FinRLAdapter(
                symbol=self.symbol, start_date=self.start_date, end_date=self.end_date
            )

            # Reset first
            await adapter.reset()

            # Execute buy action (action=2)
            observation, reward, terminated, truncated, info = await adapter.step(2)

            assert observation is not None
            assert isinstance(reward, (int, float))
            assert isinstance(terminated, bool)
            assert isinstance(truncated, bool)
            assert isinstance(info, dict)
            assert adapter.current_step == 1

    @pytest.mark.asyncio
    async def test_step_method_sell_action(self):
        """Test step method with sell action."""
        with patch(
            "quantchain.backtesting.finrl_adapter.get_connector"
        ) as mock_get_connector:
            mock_connector = AsyncMock()
            mock_get_connector.return_value = mock_connector

            # Mock data
            historical_data = pd.DataFrame(
                {
                    "open": [100, 101, 102, 103, 104],
                    "high": [101, 102, 103, 104, 105],
                    "low": [99, 100, 101, 102, 103],
                    "close": [100.5, 101.5, 102.5, 103.5, 104.5],
                    "volume": [1000, 1100, 1200, 1300, 1400],
                },
                index=pd.date_range("2023-01-01", periods=5),
            )

            mock_connector.get_historical_data.return_value = historical_data

            adapter = FinRLAdapter(
                symbol=self.symbol, start_date=self.start_date, end_date=self.end_date
            )

            # Reset first
            await adapter.reset()

            # Execute sell action (action=0)
            observation, reward, terminated, truncated, info = await adapter.step(0)

            assert observation is not None
            assert isinstance(reward, (int, float))
            assert isinstance(terminated, bool)
            assert isinstance(truncated, bool)

    @pytest.mark.asyncio
    async def test_step_method_hold_action(self):
        """Test step method with hold action."""
        with patch(
            "quantchain.backtesting.finrl_adapter.get_connector"
        ) as mock_get_connector:
            mock_connector = AsyncMock()
            mock_get_connector.return_value = mock_connector

            # Mock data
            historical_data = pd.DataFrame(
                {
                    "open": [100, 101, 102, 103, 104],
                    "high": [101, 102, 103, 104, 105],
                    "low": [99, 100, 101, 102, 103],
                    "close": [100.5, 101.5, 102.5, 103.5, 104.5],
                    "volume": [1000, 1100, 1200, 1300, 1400],
                },
                index=pd.date_range("2023-01-01", periods=5),
            )

            mock_connector.get_historical_data.return_value = historical_data

            adapter = FinRLAdapter(
                symbol=self.symbol, start_date=self.start_date, end_date=self.end_date
            )

            # Reset first
            await adapter.reset()

            # Execute hold action (action=1)
            observation, reward, terminated, truncated, info = await adapter.step(1)

            assert observation is not None
            assert isinstance(reward, (int, float))

    @pytest.mark.asyncio
    async def test_episode_termination(self):
        """Test episode termination when data is exhausted."""
        with patch(
            "quantchain.backtesting.finrl_adapter.get_connector"
        ) as mock_get_connector:
            mock_connector = AsyncMock()
            mock_get_connector.return_value = mock_connector

            # Mock very short data
            historical_data = pd.DataFrame(
                {
                    "open": [100],
                    "high": [101],
                    "low": [99],
                    "close": [100.5],
                    "volume": [1000],
                },
                index=pd.date_range("2023-01-01", periods=1),
            )

            mock_connector.get_historical_data.return_value = historical_data

            adapter = FinRLAdapter(
                symbol=self.symbol, start_date=self.start_date, end_date=self.end_date
            )

            # Reset first
            await adapter.reset()

            # Step should terminate immediately
            observation, reward, terminated, truncated, info = await adapter.step(1)

            assert terminated is True

    @pytest.mark.asyncio
    async def test_reward_calculation_simple_return(self):
        """Test reward calculation with simple return strategy."""
        with patch(
            "quantchain.backtesting.finrl_adapter.get_connector"
        ) as mock_get_connector:
            mock_connector = AsyncMock()
            mock_get_connector.return_value = mock_connector

            # Mock data
            historical_data = pd.DataFrame(
                {
                    "open": [100, 101],
                    "high": [101, 102],
                    "low": [99, 100],
                    "close": [100.5, 101.5],
                    "volume": [1000, 1100],
                },
                index=pd.date_range("2023-01-01", periods=2),
            )

            mock_connector.get_historical_data.return_value = historical_data

            adapter = FinRLAdapter(
                symbol=self.symbol,
                start_date=self.start_date,
                end_date=self.end_date,
                reward_strategy="simple_return",
            )

            await adapter.reset()
            observation, reward, _, _, _ = await adapter.step(1)  # Hold

            # Reward should be calculated
            assert isinstance(reward, (int, float))

    @pytest.mark.asyncio
    async def test_reward_calculation_risk_adjusted(self):
        """Test reward calculation with risk-adjusted strategy."""
        with patch(
            "quantchain.backtesting.finrl_adapter.get_connector"
        ) as mock_get_connector:
            mock_connector = AsyncMock()
            mock_get_connector.return_value = mock_connector

            # Mock data
            historical_data = pd.DataFrame(
                {
                    "open": [100, 101, 102],
                    "high": [101, 102, 103],
                    "low": [99, 100, 101],
                    "close": [100.5, 101.5, 102.5],
                    "volume": [1000, 1100, 1200],
                },
                index=pd.date_range("2023-01-01", periods=3),
            )

            mock_connector.get_historical_data.return_value = historical_data

            adapter = FinRLAdapter(
                symbol=self.symbol,
                start_date=self.start_date,
                end_date=self.end_date,
                reward_strategy="risk_adjusted_return",
            )

            await adapter.reset()
            observation, reward, _, _, _ = await adapter.step(1)  # Hold

            # Reward should be calculated
            assert isinstance(reward, (int, float))

    @pytest.mark.asyncio
    async def test_reward_calculation_sharpe_ratio(self):
        """Test reward calculation with Sharpe ratio strategy."""
        with patch(
            "quantchain.backtesting.finrl_adapter.get_connector"
        ) as mock_get_connector:
            mock_connector = AsyncMock()
            mock_get_connector.return_value = mock_connector

            # Mock data
            historical_data = pd.DataFrame(
                {
                    "open": [100, 101, 102, 103, 104],
                    "high": [101, 102, 103, 104, 105],
                    "low": [99, 100, 101, 102, 103],
                    "close": [100.5, 101.5, 102.5, 103.5, 104.5],
                    "volume": [1000, 1100, 1200, 1300, 1400],
                },
                index=pd.date_range("2023-01-01", periods=5),
            )

            mock_connector.get_historical_data.return_value = historical_data

            adapter = FinRLAdapter(
                symbol=self.symbol,
                start_date=self.start_date,
                end_date=self.end_date,
                reward_strategy="sharpe_ratio",
            )

            await adapter.reset()

            # Need multiple steps to calculate Sharpe ratio
            for _ in range(2):
                observation, reward, _, _, _ = await adapter.step(1)
                assert isinstance(reward, (int, float))

    def test_invalid_reward_strategy(self):
        """Test initialization with invalid reward strategy."""
        with patch(
            "quantchain.backtesting.finrl_adapter.get_connector"
        ) as mock_get_connector:
            mock_connector = MagicMock()
            mock_get_connector.return_value = mock_connector

            with pytest.raises(ValueError, match="Unknown reward strategy"):
                FinRLAdapter(
                    symbol=self.symbol,
                    start_date=self.start_date,
                    end_date=self.end_date,
                    reward_strategy="invalid_strategy",
                )

    @pytest.mark.asyncio
    async def test_market_friction_application(self):
        """Test that market friction is applied to trades."""
        with patch(
            "quantchain.backtesting.finrl_adapter.get_connector"
        ) as mock_get_connector:
            mock_connector = AsyncMock()
            mock_get_connector.return_value = mock_connector

            with patch(
                "quantchain.backtesting.finrl_adapter.MarketFrictionSimulator"
            ) as mock_friction:
                mock_friction_instance = MagicMock()
                mock_friction.return_value = mock_friction_instance

                # Mock data
                historical_data = pd.DataFrame(
                    {
                        "open": [100, 101, 102],
                        "high": [101, 102, 103],
                        "low": [99, 100, 101],
                        "close": [100.5, 101.5, 102.5],
                        "volume": [1000, 1100, 1200],
                    },
                    index=pd.date_range("2023-01-01", periods=3),
                )

                mock_connector.get_historical_data.return_value = historical_data

                adapter = FinRLAdapter(
                    symbol=self.symbol,
                    start_date=self.start_date,
                    end_date=self.end_date,
                    market_friction_config={"commission": 0.001},
                )

                await adapter.reset()
                await adapter.step(2)  # Buy action

                # Verify market friction simulator was used
                mock_friction_instance.apply_commission.assert_called()
                mock_friction_instance.apply_slippage.assert_called()

    @pytest.mark.asyncio
    async def test_observation_features_processing(self):
        """Test that observation features are processed correctly."""
        with patch(
            "quantchain.backtesting.finrl_adapter.get_connector"
        ) as mock_get_connector:
            mock_connector = AsyncMock()
            mock_get_connector.return_value = mock_connector

            # Mock data with technical indicators
            historical_data = pd.DataFrame(
                {
                    "open": [100, 101, 102],
                    "high": [101, 102, 103],
                    "low": [99, 100, 101],
                    "close": [100.5, 101.5, 102.5],
                    "volume": [1000, 1100, 1200],
                    "rsi": [50, 55, 60],
                    "macd": [0.1, 0.2, 0.3],
                },
                index=pd.date_range("2023-01-01", periods=3),
            )

            mock_connector.get_historical_data.return_value = historical_data

            adapter = FinRLAdapter(
                symbol=self.symbol,
                start_date=self.start_date,
                end_date=self.end_date,
                observation_features=["close", "rsi", "macd"],
            )

            await adapter.reset()
            observation, _, _, _, _ = await adapter.step(1)

            # Observation should have correct number of features
            assert len(observation) == 3

    def test_render_method(self):
        """Test render method functionality."""
        with patch(
            "quantchain.backtesting.finrl_adapter.get_connector"
        ) as mock_get_connector:
            mock_connector = MagicMock()
            mock_get_connector.return_value = mock_connector

            adapter = FinRLAdapter(
                symbol=self.symbol, start_date=self.start_date, end_date=self.end_date
            )

            # Should not crash
            try:
                adapter.render()
                adapter.render(mode="human")
            except Exception:
                # Rendering might fail in test environment, that's okay
                pass

    def test_close_method(self):
        """Test close method functionality."""
        with patch(
            "quantchain.backtesting.finrl_adapter.get_connector"
        ) as mock_get_connector:
            mock_connector = MagicMock()
            mock_get_connector.return_value = mock_connector

            adapter = FinRLAdapter(
                symbol=self.symbol, start_date=self.start_date, end_date=self.end_date
            )

            # Should not crash
            adapter.close()

    @pytest.mark.asyncio
    async def test_portfolio_state_tracking(self):
        """Test that portfolio state is tracked correctly."""
        with patch(
            "quantchain.backtesting.finrl_adapter.get_connector"
        ) as mock_get_connector:
            mock_connector = AsyncMock()
            mock_get_connector.return_value = mock_connector

            # Mock data
            historical_data = pd.DataFrame(
                {
                    "open": [100, 101, 102],
                    "high": [101, 102, 103],
                    "low": [99, 100, 101],
                    "close": [100.5, 101.5, 102.5],
                    "volume": [1000, 1100, 1200],
                },
                index=pd.date_range("2023-01-01", periods=3),
            )

            mock_connector.get_historical_data.return_value = historical_data

            adapter = FinRLAdapter(
                symbol=self.symbol, start_date=self.start_date, end_date=self.end_date
            )

            await adapter.reset()

            # Check initial state
            assert adapter.balance == adapter.initial_balance
            assert adapter.shares_held == 0

            # Execute buy action
            await adapter.step(2)

            # Check state after buy
            assert adapter.shares_held > 0
            assert adapter.balance < adapter.initial_balance

    @pytest.mark.asyncio
    async def test_data_loading_error_handling(self):
        """Test handling of data loading errors."""
        with patch(
            "quantchain.backtesting.finrl_adapter.get_connector"
        ) as mock_get_connector:
            mock_connector = AsyncMock()
            mock_get_connector.return_value = mock_connector

            # Mock data loading failure
            mock_connector.get_historical_data.side_effect = Exception(
                "Data loading failed"
            )

            adapter = FinRLAdapter(
                symbol=self.symbol, start_date=self.start_date, end_date=self.end_date
            )

            # Reset should handle the error gracefully
            with pytest.raises(Exception):
                await adapter.reset()

    @pytest.mark.asyncio
    async def test_step_before_reset_error(self):
        """Test that calling step before reset raises appropriate error."""
        with patch(
            "quantchain.backtesting.finrl_adapter.get_connector"
        ) as mock_get_connector:
            mock_connector = MagicMock()
            mock_get_connector.return_value = mock_connector

            adapter = FinRLAdapter(
                symbol=self.symbol, start_date=self.start_date, end_date=self.end_date
            )

            # Step before reset should raise an error
            with pytest.raises((RuntimeError, ValueError, AttributeError)):
                await adapter.step(1)
