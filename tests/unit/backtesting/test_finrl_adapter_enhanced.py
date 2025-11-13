"""Enhanced tests for FinRL adapter to reach 80% coverage."""

import pytest
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

# Check if finrl_adapter is available
try:
    from quantchain.backtesting.finrl_adapter import (
        FinRLAdapter,
        FinRLAdapterError,
        FinRLConnectionError,
        FinRLDataError,
        get_connector,
        GYMNASIUM_AVAILABLE,
        MarketFrictionSimulator,
        PerformanceMetrics,
        AlpacaDataConnector,
        CCXTDataConnector,
        PolygonDataConnector,
    )
    FINRL_ADAPTER_AVAILABLE = True
except ImportError as e:
    FINRL_ADAPTER_AVAILABLE = False
    print(f"Import error: {e}")

pytestmark = pytest.mark.skipif(
    not FINRL_ADAPTER_AVAILABLE, reason="FinRL adapter not available"
)


@pytest.fixture
def mock_market_data():
    """Create mock market data for testing."""
    dates = pd.date_range(start="2023-01-01", end="2023-01-10", freq="D")
    return pd.DataFrame({
        "open": np.random.uniform(100, 110, len(dates)),
        "high": np.random.uniform(110, 120, len(dates)),
        "low": np.random.uniform(90, 100, len(dates)),
        "close": np.random.uniform(100, 110, len(dates)),
        "volume": np.random.randint(1000, 10000, len(dates)),
    }, index=dates)


@pytest.fixture
def mock_config():
    """Create mock configuration."""
    return {
        "initial_cash": 100000,
        "commission": 0.001,
        "slippage": 0.0001,
        "symbol": "AAPL",
    }


@pytest.mark.unit
class TestFinRLAdapterEnhanced:
    """Enhanced tests for FinRL adapter functionality."""

    def test_get_connector_alpaca(self):
        """Test get_connector with Alpaca."""
        with patch("quantchain.backtesting.finrl_adapter.AlpacaDataConnector") as mock_connector:
            mock_connector.return_value = Mock()
            connector = get_connector("alpaca", api_key="test", secret_key="test")
            assert connector is not None
            mock_connector.assert_called_once()

    def test_get_connector_ccxt(self):
        """Test get_connector with CCXT."""
        with patch("quantchain.backtesting.finrl_adapter.CCXTDataConnector") as mock_connector:
            mock_connector.return_value = Mock()
            connector = get_connector("ccxt", exchange="binance")
            assert connector is not None
            mock_connector.assert_called_once()

    def test_get_connector_polygon(self):
        """Test get_connector with Polygon."""
        with patch("quantchain.backtesting.finrl_adapter.PolygonDataConnector") as mock_connector:
            mock_connector.return_value = Mock()
            connector = get_connector("polygon", api_key="test")
            assert connector is not None
            mock_connector.assert_called_once()

    def test_get_connector_invalid(self):
        """Test get_connector with invalid source."""
        with pytest.raises(FinRLConnectionError):
            get_connector("invalid_source")

    @patch("quantchain.backtesting.finrl_adapter.AlpacaDataConnector")
    def test_finrl_adapter_initialization(self, mock_alpaca):
        """Test FinRLAdapter initialization."""
        mock_alpaca.return_value = Mock()
        
        adapter = FinRLAdapter(
            connector_type="alpaca",
            symbol="AAPL",
            start_date="2023-01-01",
            end_date="2023-01-10",
            initial_cash=100000,
        )
        
        assert adapter.symbol == "AAPL"
        assert adapter.initial_cash == 100000
        assert adapter.current_step == 0

    @patch("quantchain.backtesting.finrl_adapter.AlpacaDataConnector")
    def test_finrl_adapter_reset(self, mock_alpaca):
        """Test FinRLAdapter reset method."""
        mock_alpaca.return_value = Mock()
        adapter = FinRLAdapter(
            connector_type="alpaca",
            symbol="AAPL",
            start_date="2023-01-01",
            end_date="2023-01-10",
        )
        
        # Mock the data
        adapter.data = mock_market_data()
        
        obs, info = adapter.reset()
        assert adapter.current_step == 0
        assert obs is not None
        assert info is not None

    @patch("quantchain.backtesting.finrl_adapter.AlpacaDataConnector")
    def test_finrl_adapter_step(self, mock_alpaca):
        """Test FinRLAdapter step method."""
        mock_alpaca.return_value = Mock()
        adapter = FinRLAdapter(
            connector_type="alpaca",
            symbol="AAPL",
            start_date="2023-01-01",
            end_date="2023-01-10",
        )
        
        # Mock the data
        adapter.data = mock_market_data()
        adapter.current_step = 0
        
        action = 1  # Buy
        obs, reward, terminated, truncated, info = adapter.step(action)
        
        assert isinstance(obs, (np.ndarray, list))
        assert isinstance(reward, (int, float))
        assert isinstance(terminated, bool)
        assert isinstance(truncated, bool)
        assert isinstance(info, dict)

    @patch("quantchain.backtesting.finrl_adapter.AlpacaDataConnector")
    def test_finrl_adapter_action_space(self, mock_alpaca):
        """Test FinRLAdapter action space."""
        mock_alpaca.return_value = Mock()
        adapter = FinRLAdapter(
            connector_type="alpaca",
            symbol="AAPL",
            start_date="2023-01-01",
            end_date="2023-01-10",
        )
        
        if GYMNASIUM_AVAILABLE:
            assert hasattr(adapter, 'action_space')
            assert hasattr(adapter, 'observation_space')

    @patch("quantchain.backtesting.finrl_adapter.AlpacaDataConnector")
    def test_finrl_adapter_portfolio_metrics(self, mock_alpaca):
        """Test portfolio metrics calculation."""
        mock_alpaca.return_value = Mock()
        adapter = FinRLAdapter(
            connector_type="alpaca",
            symbol="AAPL",
            start_date="2023-01-01",
            end_date="2023-01-10",
            initial_cash=100000,
        )
        
        adapter.data = mock_market_data()
        adapter.portfolio["cash"] = 50000
        adapter.portfolio["shares"] = 100
        
        total_value = adapter._get_portfolio_value()
        assert isinstance(total_value, (int, float))
        assert total_value > 0

    @patch("quantchain.backtesting.finrl_adapter.AlpacaDataConnector")
    def test_finrl_adapter_transaction_costs(self, mock_alpaca):
        """Test transaction cost calculation."""
        mock_alpaca.return_value = Mock()
        adapter = FinRLAdapter(
            connector_type="alpaca",
            symbol="AAPL",
            commission=0.001,
            slippage=0.0001,
        )
        
        # Test buy transaction
        cost = adapter._calculate_transaction_cost(100, 100, "buy")
        assert isinstance(cost, (int, float))
        assert cost >= 0
        
        # Test sell transaction
        cost = adapter._calculate_transaction_cost(100, 100, "sell")
        assert isinstance(cost, (int, float))
        assert cost >= 0

    @patch("quantchain.backtesting.finrl_adapter.AlpacaDataConnector")
    def test_finrl_adapter_edge_cases(self, mock_alpaca):
        """Test edge cases and error handling."""
        mock_alpaca.return_value = Mock()
        
        # Test with invalid dates
        with pytest.raises(FinRLDataError):
            adapter = FinRLAdapter(
                connector_type="alpaca",
                symbol="AAPL",
                start_date="invalid_date",
                end_date="2023-01-10",
            )
        
        # Test with empty data
        adapter = FinRLAdapter(
            connector_type="alpaca",
            symbol="AAPL",
            start_date="2023-01-01",
            end_date="2023-01-01",  # Same date (might result in no data)
        )
        adapter.data = pd.DataFrame()  # Empty data
        
        with pytest.raises(FinRLDataError):
            adapter.reset()

    @patch("quantchain.backtesting.finrl_adapter.AlpacaDataConnector")
    def test_finrl_adapter_observation_format(self, mock_alpaca):
        """Test observation format and features."""
        mock_alpaca.return_value = Mock()
        adapter = FinRLAdapter(
            connector_type="alpaca",
            symbol="AAPL",
            start_date="2023-01-01",
            end_date="2023-01-10",
        )
        
        adapter.data = mock_market_data()
        adapter.current_step = 0
        
        obs = adapter._get_observation()
        assert isinstance(obs, (np.ndarray, list))
        if GYMNASIUM_AVAILABLE:
            assert len(obs) == adapter.observation_space.shape[0]

    @patch("quantchain.backtesting.finrl_adapter.AlpacaDataConnector")
    def test_finrl_adapter_reward_calculation(self, mock_alpaca):
        """Test reward calculation logic."""
        mock_alpaca.return_value = Mock()
        adapter = FinRLAdapter(
            connector_type="alpaca",
            symbol="AAPL",
            start_date="2023-01-01",
            end_date="2023-01-10",
            initial_cash=100000,
        )
        
        adapter.data = mock_market_data()
        adapter.current_step = 0
        prev_value = 100000
        
        # Mock transaction
        adapter.portfolio["shares"] = 100
        adapter.last_portfolio_value = prev_value
        
        reward = adapter._calculate_reward()
        assert isinstance(reward, (int, float))

    @patch("quantchain.backtesting.finrl_adapter.MarketFrictionSimulator")
    @patch("quantchain.backtesting.finrl_adapter.AlpacaDataConnector")
    def test_finrl_adapter_with_market_friction(self, mock_alpaca, mock_friction):
        """Test FinRLAdapter with market friction enabled."""
        mock_alpaca.return_value = Mock()
        mock_friction.return_value = Mock()
        
        adapter = FinRLAdapter(
            connector_type="alpaca",
            symbol="AAPL",
            start_date="2023-01-01",
            end_date="2023-01-10",
            enable_market_friction=True,
        )
        
        assert adapter.market_friction is not None
        
        # Test with friction simulation
        adapter.market_friction.calculate_slippage.return_value = 0.1
        adapter.market_friction.calculate_commission.return_value = 1.0

    @patch("quantchain.backtesting.finrl_adapter.PerformanceMetrics")
    @patch("quantchain.backtesting.finrl_adapter.AlpacaDataConnector")
    def test_finrl_adapter_performance_metrics(self, mock_alpaca, mock_metrics):
        """Test performance metrics integration."""
        mock_alpaca.return_value = Mock()
        mock_metrics.return_value = Mock()
        
        adapter = FinRLAdapter(
            connector_type="alpaca",
            symbol="AAPL",
            start_date="2023-01-01",
            end_date="2023-01-10",
        )
        
        adapter.data = mock_market_data()
        adapter.trade_history = [{"price": 100, "shares": 10, "type": "buy"}]
        
        # Test metrics calculation
        metrics = adapter.calculate_performance_metrics()
        assert metrics is not None

    @patch("quantchain.backtesting.finrl_adapter.AlpacaDataConnector")
    def test_finrl_adapter_action_validation(self, mock_alpaca):
        """Test action validation."""
        mock_alpaca.return_value = Mock()
        adapter = FinRLAdapter(
            connector_type="alpaca",
            symbol="AAPL",
            start_date="2023-01-01",
            end_date="2023-01-10",
        )
        
        # Test invalid action
        with pytest.raises(ValueError):
            adapter._validate_action(999)  # Invalid action
        
        # Test valid action range
        valid_actions = [0, 1, 2]  # Hold, Buy, Sell
        for action in valid_actions:
            assert adapter._validate_action(action) is True

    @patch("quantchain.backtesting.finrl_adapter.AlpacaDataConnector")
    def test_finrl_adapter_data_handling(self, mock_alpaca):
        """Test data handling and preprocessing."""
        mock_alpaca.return_value = Mock()
        adapter = FinRLAdapter(
            connector_type="alpaca",
            symbol="AAPL",
            start_date="2023-01-01",
            end_date="2023-01-10",
        )
        
        # Test data preprocessing
        raw_data = mock_market_data()
        processed_data = adapter._preprocess_data(raw_data)
        assert isinstance(processed_data, pd.DataFrame)
        assert not processed_data.empty

    @patch("quantchain.backtesting.finrl_adapter.AlpacaDataConnector")
    def test_finrl_adapter_save_load_state(self, mock_alpaca):
        """Test saving and loading adapter state."""
        mock_alpaca.return_value = Mock()
        adapter = FinRLAdapter(
            connector_type="alpaca",
            symbol="AAPL",
            start_date="2023-01-01",
            end_date="2023-01-10",
        )
        
        adapter.data = mock_market_data()
        adapter.current_step = 5
        adapter.portfolio = {"cash": 50000, "shares": 100}
        
        # Test save state
        state = adapter.save_state()
        assert isinstance(state, dict)
        assert "current_step" in state
        assert "portfolio" in state
        
        # Test load state
        new_adapter = FinRLAdapter(
            connector_type="alpaca",
            symbol="AAPL",
            start_date="2023-01-01",
            end_date="2023-01-10",
        )
        new_adapter.load_state(state)
        assert new_adapter.current_step == state["current_step"]
        assert new_adapter.portfolio == state["portfolio"]

    @patch("quantchain.backtesting.finrl_adapter.AlpacaDataConnector")
    def test_finrl_adapter_render(self, mock_alpaca):
        """Test rendering functionality."""
        mock_alpaca.return_value = Mock()
        adapter = FinRLAdapter(
            connector_type="alpaca",
            symbol="AAPL",
            start_date="2023-01-01",
            end_date="2023-01-10",
        )
        
        adapter.data = mock_market_data()
        adapter.portfolio = {"cash": 50000, "shares": 100}
        
        # Test render method (should not raise errors)
        adapter.render()  # Should not raise exceptions
        adapter.render(mode="human")  # With mode parameter

    @patch("quantchain.backtesting.finrl_adapter.AlpacaDataConnector")
    def test_finrl_adapter_close(self, mock_alpaca):
        """Test cleanup on close."""
        mock_alpaca.return_value = Mock()
        adapter = FinRLAdapter(
            connector_type="alpaca",
            symbol="AAPL",
            start_date="2023-01-01",
            end_date="2023-01-10",
        )
        
        # Test close method
        adapter.close()  # Should not raise exceptions

    @patch("quantchain.backtesting.finrl_adapter.AlpacaDataConnector")
    def test_finrl_adapter_seed(self, mock_alpaca):
        """Test random seed functionality."""
        mock_alpaca.return_value = Mock()
        adapter = FinRLAdapter(
            connector_type="alpaca",
            symbol="AAPL",
            start_date="2023-01-01",
            end_date="2023-01-10",
        )
        
        # Test seed method
        adapter.seed(42)  # Should not raise exceptions
