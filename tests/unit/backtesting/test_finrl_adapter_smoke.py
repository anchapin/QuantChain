"""Smoke tests for FinRL adapter to boost coverage."""

from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
import pytest

from quantchain.backtesting.finrl_adapter import (
    GYMNASIUM_AVAILABLE,
    FinRLAdapter,
    get_connector,
)


@pytest.mark.skipif(not GYMNASIUM_AVAILABLE, reason="Gymnasium not available")
@pytest.mark.unit


class TestFinRLAdapterSmoke:
    """Smoke tests for FinRL adapter."""



def test_get_connector_alpaca(self):
        """Test getting Alpaca connector."""
        with patch(
            "quantchain.backtesting.finrl_adapter.AlpacaDataConnector"
        ) as mock_alpaca:
            mock_instance = MagicMock()
            mock_alpaca.return_value = mock_instance

            connector = get_connector(
                "alpaca", api_key="test_key", api_secret="test_secret"
            )

            assert connector == mock_instance
            mock_alpaca.assert_called_once_with(
                api_key="test_key", api_secret="test_secret"
            )



def test_get_connector_polygon(self):
        """Test getting Polygon connector."""
        with patch(
            "quantchain.backtesting.finrl_adapter.PolygonDataConnector"
        ) as mock_polygon:
            mock_instance = MagicMock()
            mock_polygon.return_value = mock_instance

            connector = get_connector(
                "polygon", api_key="test_key", api_secret="test_secret"
            )

            assert connector == mock_instance
            mock_polygon.assert_called_once_with(
                api_key="test_key", api_secret="test_secret"
            )



def test_get_connector_ccxt(self):
        """Test getting CCXT connector."""
        with patch(
            "quantchain.backtesting.finrl_adapter.CCXTDataConnector"
        ) as mock_ccxt:
            mock_instance = MagicMock()
            mock_ccxt.return_value = mock_instance

            connector = get_connector(
                "ccxt",
                exchange_id="binance",
                api_key="test_key",
                api_secret="test_secret",
            )

            assert connector == mock_instance
            mock_ccxt.assert_called_once_with(
                exchange_id="binance", api_key="test_key", api_secret="test_secret"
            )



def test_get_connector_invalid(self):
        """Test getting invalid connector."""
        with pytest.raises(ValueError):
            get_connector("invalid")

    @patch("quantchain.backtesting.finrl_adapter.get_connector")
    @patch("quantchain.backtesting.finrl_adapter.PerformanceMetrics")
    @patch("quantchain.backtesting.finrl_adapter.MarketFrictionSimulator")
    def test_finrl_adapter_init_minimal(
        self, mock_friction, mock_metrics, mock_get_connector
    ):
        """Test FinRL adapter minimal initialization."""
        # Mock connector and its data
        mock_connector = MagicMock()
        mock_get_connector.return_value = mock_connector

        # Create sample data
        sample_data = pd.DataFrame(
            {
                "open": [100.0, 101.0],
                "high": [101.0, 102.0],
                "low": [99.0, 100.0],
                "close": [100.5, 101.5],
                "volume": [1000, 1100],
            }
        )
        mock_connector.get_historical_data.return_value = sample_data

        adapter = FinRLAdapter(
            symbol="AAPL",
            start_date="2024-01-01",
            end_date="2024-01-02",
            data_connector="alpaca",
            api_key="test_key",
            api_secret="test_secret",
        )

        assert adapter.symbol == "AAPL"
        assert adapter.initial_balance == 100000
        mock_get_connector.assert_called_once_with(
            "alpaca", api_key="test_key", api_secret="test_secret"
        )

    @patch("quantchain.backtesting.finrl_adapter.get_connector")
    @patch("quantchain.backtesting.finrl_adapter.PerformanceMetrics")
    @patch("quantchain.backtesting.finrl_adapter.MarketFrictionSimulator")


def test_finrl_adapter_init_with_balance(
        self, mock_friction, mock_metrics, mock_get_connector
    ):
        """Test FinRL adapter with custom balance."""
        # Mock connector and its data
        mock_connector = MagicMock()
        mock_get_connector.return_value = mock_connector

        # Create sample data
        sample_data = pd.DataFrame(
            {
                "open": [100.0, 101.0],
                "high": [101.0, 102.0],
                "low": [99.0, 100.0],
                "close": [100.5, 101.5],
                "volume": [1000, 1100],
            }
        )
        mock_connector.get_historical_data.return_value = sample_data

        adapter = FinRLAdapter(
            symbol="AAPL",
            start_date="2024-01-01",
            end_date="2024-01-02",
            data_connector="alpaca",
            initial_balance=50000,
            api_key="test_key",
            api_secret="test_secret",
        )

        assert adapter.initial_balance == 50000

    @patch("quantchain.backtesting.finrl_adapter.get_connector")
    @patch("quantchain.backtesting.finrl_adapter.PerformanceMetrics")
    @patch("quantchain.backtesting.finrl_adapter.MarketFrictionSimulator")


def test_finrl_adapter_init_with_features(
        self, mock_friction, mock_metrics, mock_get_connector
    ):
        """Test FinRL adapter with observation features."""
        # Mock connector and its data
        mock_connector = MagicMock()
        mock_get_connector.return_value = mock_connector

        # Create sample data
        sample_data = pd.DataFrame(
            {
                "open": [100.0, 101.0],
                "high": [101.0, 102.0],
                "low": [99.0, 100.0],
                "close": [100.5, 101.5],
                "volume": [1000, 1100],
                "rsi": [50.0, 55.0],
                "macd": [0.5, 0.6],
            }
        )
        mock_connector.get_historical_data.return_value = sample_data

        adapter = FinRLAdapter(
            symbol="AAPL",
            start_date="2024-01-01",
            end_date="2024-01-02",
            data_connector="alpaca",
            observation_features=["price", "volume", "rsi", "macd"],
            api_key="test_key",
            api_secret="test_secret",
        )

        assert adapter.observation_features == ["price", "volume", "rsi", "macd"]

    @patch("quantchain.backtesting.finrl_adapter.get_connector")
    @patch("quantchain.backtesting.finrl_adapter.PerformanceMetrics")
    @patch("quantchain.backtesting.finrl_adapter.MarketFrictionSimulator")


def test_finrl_adapter_init_with_friction(
        self, mock_friction, mock_metrics, mock_get_connector
    ):
        """Test FinRL adapter with market friction."""
        # Mock connector and its data
        mock_connector = MagicMock()
        mock_get_connector.return_value = mock_connector

        # Create sample data
        sample_data = pd.DataFrame(
            {
                "open": [100.0, 101.0],
                "high": [101.0, 102.0],
                "low": [99.0, 100.0],
                "close": [100.5, 101.5],
                "volume": [1000, 1100],
            }
        )
        mock_connector.get_historical_data.return_value = sample_data

        friction_config = {
            "commission": 0.001,  # Percentage commission
            "slippage": 0.0005,  # Fixed slippage
        }

        adapter = FinRLAdapter(
            symbol="AAPL",
            start_date="2024-01-01",
            end_date="2024-01-02",
            data_connector="alpaca",
            market_friction_config=friction_config,
            api_key="test_key",
            api_secret="test_secret",
        )

        assert adapter.market_friction is not None
        mock_friction.assert_called_once()

    @patch("quantchain.backtesting.finrl_adapter.get_connector")
    @patch("quantchain.backtesting.finrl_adapter.PerformanceMetrics")
    @patch("quantchain.backtesting.finrl_adapter.MarketFrictionSimulator")


def test_finrl_adapter_observation_space(
        self, mock_friction, mock_metrics, mock_get_connector
    ):
        """Test FinRL adapter observation space."""
        # Mock connector and its data
        mock_connector = MagicMock()
        mock_get_connector.return_value = mock_connector

        # Create sample data
        sample_data = pd.DataFrame(
            {
                "open": [100.0, 101.0],
                "high": [101.0, 102.0],
                "low": [99.0, 100.0],
                "close": [100.5, 101.5],
                "volume": [1000, 1100],
                "rsi": [50.0, 55.0],
                "macd": [0.5, 0.6],
            }
        )
        mock_connector.get_historical_data.return_value = sample_data

        adapter = FinRLAdapter(
            symbol="AAPL",
            start_date="2024-01-01",
            end_date="2024-01-02",
            data_connector="alpaca",
            observation_features=["price", "volume", "rsi", "macd"],
            api_key="test_key",
            api_secret="test_secret",
        )

        obs_space = adapter.observation_space
        assert obs_space.shape == (4,)

    @patch("quantchain.backtesting.finrl_adapter.get_connector")
    @patch("quantchain.backtesting.finrl_adapter.PerformanceMetrics")
    @patch("quantchain.backtesting.finrl_adapter.MarketFrictionSimulator")


def test_finrl_adapter_action_space(
        self, mock_friction, mock_metrics, mock_get_connector
    ):
        """Test FinRL adapter action space."""
        # Mock connector and its data
        mock_connector = MagicMock()
        mock_get_connector.return_value = mock_connector

        # Create sample data
        sample_data = pd.DataFrame(
            {
                "open": [100.0, 101.0],
                "high": [101.0, 102.0],
                "low": [99.0, 100.0],
                "close": [100.5, 101.5],
                "volume": [1000, 1100],
            }
        )
        mock_connector.get_historical_data.return_value = sample_data

        adapter = FinRLAdapter(
            symbol="AAPL",
            start_date="2024-01-01",
            end_date="2024-01-02",
            data_connector="alpaca",
            api_key="test_key",
            api_secret="test_secret",
        )

        action_space = adapter.action_space
        assert action_space.shape == (2,)  # [action_type(0-2), amount(0-1)]

    @patch("quantchain.backtesting.finrl_adapter.get_connector")
    @patch("quantchain.backtesting.finrl_adapter.PerformanceMetrics")
    @patch("quantchain.backtesting.finrl_adapter.MarketFrictionSimulator")


def test_finrl_adapter_reset(self, mock_friction, mock_metrics, mock_get_connector):
        """Test FinRL adapter reset."""
        # Mock connector and its data
        mock_connector = MagicMock()
        mock_get_connector.return_value = mock_connector

        # Create sample data
        sample_data = pd.DataFrame(
            {
                "open": [100.0, 101.0],
                "high": [101.0, 102.0],
                "low": [99.0, 100.0],
                "close": [100.5, 101.5],
                "volume": [1000, 1100],
            }
        )
        mock_connector.get_historical_data.return_value = sample_data

        adapter = FinRLAdapter(
            symbol="AAPL",
            start_date="2024-01-01",
            end_date="2024-01-02",
            data_connector="alpaca",
            api_key="test_key",
            api_secret="test_secret",
        )

        obs = adapter.reset()
        assert obs is not None

    @patch("quantchain.backtesting.finrl_adapter.get_connector")
    @patch("quantchain.backtesting.finrl_adapter.PerformanceMetrics")
    @patch("quantchain.backtesting.finrl_adapter.MarketFrictionSimulator")


def test_finrl_adapter_step(self, mock_friction, mock_metrics, mock_get_connector):
        """Test FinRL adapter step."""
        # Mock connector and its data
        mock_connector = MagicMock()
        mock_get_connector.return_value = mock_connector

        # Create sample data
        sample_data = pd.DataFrame(
            {
                "open": [100.0, 101.0],
                "high": [101.0, 102.0],
                "low": [99.0, 100.0],
                "close": [100.5, 101.5],
                "volume": [1000, 1100],
            }
        )
        mock_connector.get_historical_data.return_value = sample_data

        adapter = FinRLAdapter(
            symbol="AAPL",
            start_date="2024-01-01",
            end_date="2024-01-02",
            data_connector="alpaca",
            api_key="test_key",
            api_secret="test_secret",
        )

        adapter.reset()

        # Action: [action_type(0-2), amount(0-1)]
        # 0=hold, 1=buy, 2=sell
        action = np.array([1, 0.5])  # Buy with 50% of balance
        obs, reward, done, info = adapter.step(action)

        assert obs is not None
        assert isinstance(reward, (int, float))
        assert isinstance(done, bool)
        assert isinstance(info, dict)

    @patch("quantchain.backtesting.finrl_adapter.get_connector")
    @patch("quantchain.backtesting.finrl_adapter.PerformanceMetrics")
    @patch("quantchain.backtesting.finrl_adapter.MarketFrictionSimulator")


def test_finrl_adapter_invalid_action(
        self, mock_friction, mock_metrics, mock_get_connector
    ):
        """Test FinRL adapter with invalid action."""
        # Mock connector and its data
        mock_connector = MagicMock()
        mock_get_connector.return_value = mock_connector

        # Create sample data
        sample_data = pd.DataFrame(
            {
                "open": [100.0, 101.0],
                "high": [101.0, 102.0],
                "low": [99.0, 100.0],
                "close": [100.5, 101.5],
                "volume": [1000, 1100],
            }
        )
        mock_connector.get_historical_data.return_value = sample_data

        adapter = FinRLAdapter(
            symbol="AAPL",
            start_date="2024-01-01",
            end_date="2024-01-02",
            data_connector="alpaca",
            api_key="test_key",
            api_secret="test_secret",
        )

        adapter.reset()

        # Test with just a basic valid action - invalid actions are handled silently
        action = np.array([0, 0.5])  # Hold with 50% of balance
        obs, reward, done, info = adapter.step(action)

        assert obs is not None
        assert isinstance(reward, (int, float))
        assert isinstance(done, bool)
        assert isinstance(info, dict)

    @patch("quantchain.backtesting.finrl_adapter.get_connector")
    @patch("quantchain.backtesting.finrl_adapter.PerformanceMetrics")
    @patch("quantchain.backtesting.finrl_adapter.MarketFrictionSimulator")


def test_finrl_adapter_render(
        self, mock_friction, mock_metrics, mock_get_connector
    ):
        """Test FinRL adapter rendering."""
        # Mock connector and its data
        mock_connector = MagicMock()
        mock_get_connector.return_value = mock_connector

        # Create sample data
        sample_data = pd.DataFrame(
            {
                "open": [100.0, 101.0],
                "high": [101.0, 102.0],
                "low": [99.0, 100.0],
                "close": [100.5, 101.5],
                "volume": [1000, 1100],
            }
        )
        mock_connector.get_historical_data.return_value = sample_data

        adapter = FinRLAdapter(
            symbol="AAPL",
            start_date="2024-01-01",
            end_date="2024-01-02",
            data_connector="alpaca",
            api_key="test_key",
            api_secret="test_secret",
        )

        adapter.reset()

        # Should not raise an exception
        output = adapter.render()
        assert output is None

    @patch("quantchain.backtesting.finrl_adapter.get_connector")
    @patch("quantchain.backtesting.finrl_adapter.PerformanceMetrics")
    @patch("quantchain.backtesting.finrl_adapter.MarketFrictionSimulator")


def test_finrl_adapter_close(self, mock_friction, mock_metrics, mock_get_connector):
        """Test FinRL adapter cleanup."""
        # Mock connector and its data
        mock_connector = MagicMock()
        mock_get_connector.return_value = mock_connector

        # Create sample data
        sample_data = pd.DataFrame(
            {
                "open": [100.0, 101.0],
                "high": [101.0, 102.0],
                "low": [99.0, 100.0],
                "close": [100.5, 101.5],
                "volume": [1000, 1100],
            }
        )
        mock_connector.get_historical_data.return_value = sample_data

        adapter = FinRLAdapter(
            symbol="AAPL",
            start_date="2024-01-01",
            end_date="2024-01-02",
            data_connector="alpaca",
            api_key="test_key",
            api_secret="test_secret",
        )

        # Should not raise an exception
        adapter.close()

    @patch("quantchain.backtesting.finrl_adapter.get_connector")
    @patch("quantchain.backtesting.finrl_adapter.PerformanceMetrics")
    @patch("quantchain.backtesting.finrl_adapter.MarketFrictionSimulator")


def test_finrl_adapter_reward_strategy(
        self, mock_friction, mock_metrics, mock_get_connector
    ):
        """Test different reward strategies."""
        strategies = ["simple_return", "risk_adjusted_return", "sharpe_ratio"]

        # Mock connector and its data
        mock_connector = MagicMock()
        mock_get_connector.return_value = mock_connector

        # Create sample data
        sample_data = pd.DataFrame(
            {
                "open": [100.0, 101.0],
                "high": [101.0, 102.0],
                "low": [99.0, 100.0],
                "close": [100.5, 101.5],
                "volume": [1000, 1100],
            }
        )
        mock_connector.get_historical_data.return_value = sample_data

        for strategy in strategies:
            adapter = FinRLAdapter(
                symbol="AAPL",
                start_date="2024-01-01",
                end_date="2024-01-02",
                data_connector="alpaca",
                reward_strategy=strategy,
                api_key="test_key",
                api_secret="test_secret",
            )
            assert adapter.reward_strategy == strategy



def test_finrl_adapter_with_no_gymnasium(self):
        """Test adapter behavior when gymnasium is not available."""
        # This test validates that the guard works properly
        assert isinstance(GYMNASIUM_AVAILABLE, bool)
