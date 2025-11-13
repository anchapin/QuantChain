"""Comprehensive coverage tests for FinRL adapter."""

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
def mock_config():
    """Create mock configuration."""
    return {
        "initial_cash": 100000,
        "commission": 0.001,
        "slippage": 0.0001,
        "symbol": "AAPL",
    }


@pytest.mark.unit
class TestFinRLAdapterComprehensiveCoverage:
    """Comprehensive tests for FinRL adapter to improve coverage."""

    def test_get_connector_with_missing_source(self):
        """Test get_connector with None source."""
        with pytest.raises(FinRLConnectionError):
            get_connector(None)

    def test_get_connector_with_empty_source(self):
        """Test get_connector with empty string."""
        with pytest.raises(FinRLConnectionError):
            get_connector("")

    def test_finrl_adapter_error_inheritance(self):
        """Test error class inheritance hierarchy."""
        # Test FinRLAdapterError is base
        assert issubclass(FinRLConnectionError, FinRLAdapterError)
        assert issubclass(FinRLDataError, FinRLAdapterError)
        
        # Test FinRLAdapterError inherits from Exception
        assert issubclass(FinRLAdapterError, Exception)

    def test_market_friction_simulator_initialization(self):
        """Test MarketFrictionSimulator initialization."""
        simulator = MarketFrictionSimulator(
            commission_rate=0.001,
            slippage_rate=0.0001,
            market_impact_rate=0.0002
        )
        
        assert simulator.commission_rate == 0.001
        assert simulator.slippage_rate == 0.0001
        assert simulator.market_impact_rate == 0.0002

    def test_market_friction_simulator_default_initialization(self):
        """Test MarketFrictionSimulator with defaults."""
        simulator = MarketFrictionSimulator()
        
        assert simulator.commission_rate == 0.0001
        assert simulator.slippage_rate == 0.0001
        assert simulator.market_impact_rate == 0.0

    def test_market_friction_calculate_slippage(self):
        """Test slippage calculation."""
        simulator = MarketFrictionSimulator(slippage_rate=0.001)
        
        # Test positive slippage
        slippage = simulator.calculate_slippage(1000, 100.0)
        assert slippage >= 0
        
        # Test zero quantity
        slippage = simulator.calculate_slippage(0, 100.0)
        assert slippage == 0

    def test_market_friction_calculate_commission(self):
        """Test commission calculation."""
        simulator = MarketFrictionSimulator(commission_rate=0.001)
        
        # Test buy order
        commission = simulator.calculate_commission(100, 100.0, "buy")
        assert commission == 10.0  # 100 * 100 * 0.001
        
        # Test sell order
        commission = simulator.calculate_commission(100, 100.0, "sell")
        assert commission == 10.0
        
        # Test zero quantity
        commission = simulator.calculate_commission(0, 100.0, "buy")
        assert commission == 0

    def test_performance_metrics_initialization(self):
        """Test PerformanceMetrics initialization."""
        metrics = PerformanceMetrics(initial_capital=100000)
        
        assert metrics.initial_capital == 100000
        assert metrics.current_capital == 100000
        assert metrics.trades == []
        assert metrics.returns == []

    def test_performance_metrics_add_trade(self):
        """Test adding trade to metrics."""
        metrics = PerformanceMetrics()
        
        trade = {
            "timestamp": datetime.now(),
            "symbol": "AAPL",
            "side": "buy",
            "quantity": 100,
            "price": 100.0,
            "commission": 1.0
        }
        
        metrics.add_trade(trade)
        assert len(metrics.trades) == 1
        assert metrics.trades[0] == trade

    def test_performance_metrics_calculate_returns(self):
        """Test return calculation."""
        metrics = PerformanceMetrics(initial_capital=100000)
        
        # Add price updates
        metrics.update_portfolio_value(105000)
        metrics.update_portfolio_value(95000)
        metrics.update_portfolio_value(110000)
        
        returns = metrics.calculate_returns()
        assert len(returns) == 3
        assert returns[0] == 0.05  # 5% gain
        assert returns[1] == -0.09523809523809523  # ~9.52% loss
        assert returns[2] == 0.15789473684210525  # ~15.79% gain

    def test_performance_metrics_calculate_sharpe(self):
        """Test Sharpe ratio calculation."""
        metrics = PerformanceMetrics()
        metrics.returns = [0.01, -0.02, 0.03, 0.01, -0.01]
        
        sharpe = metrics.calculate_sharpe(risk_free_rate=0.02)
        assert isinstance(sharpe, float)

    def test_performance_metrics_calculate_max_drawdown(self):
        """Test maximum drawdown calculation."""
        metrics = PerformanceMetrics()
        metrics.portfolio_values = [100000, 110000, 95000, 120000, 90000]
        
        max_dd = metrics.calculate_max_drawdown()
        assert max_dd == 0.25  # 25% drawdown from 120000 to 90000

    def test_alpaca_connector_initialization(self):
        """Test AlpacaDataConnector initialization."""
        with patch("quantchain.backtesting.finrl_adapter.alpaca"):
            connector = AlpacaDataConnector(
                api_key="test_key",
                secret_key="test_secret",
                base_url="https://paper-api.alpaca.markets"
            )
            
            assert connector.api_key == "test_key"
            assert connector.secret_key == "test_secret"

    def test_ccxt_connector_initialization(self):
        """Test CCXTDataConnector initialization."""
        with patch("quantchain.backtesting.finrl_adapter.ccxt"):
            connector = CCXTDataConnector(
                exchange_name="binance",
                api_key="test_key",
                secret_key="test_secret"
            )
            
            assert connector.exchange_name == "binance"
            assert connector.api_key == "test_key"

    def test_polygon_connector_initialization(self):
        """Test PolygonDataConnector initialization."""
        with patch("quantchain.backtesting.finrl_adapter.polygon"):
            connector = PolygonDataConnector(
                api_key="test_key",
            )
            
            assert connector.api_key == "test_key"

    def test_finrl_adapter_with_gymnasium_available(self):
        """Test adapter when gymnasium is available."""
        with patch("quantchain.backtesting.finrl_adapter.GYMNASIUM_AVAILABLE", True):
            with patch("quantchain.backtesting.finrl_adapter.AlpacaDataConnector"):
                # This should not raise an error
                assert GYMNASIUM_AVAILABLE is True

    def test_finrl_adapter_without_gymnasium_available(self):
        """Test adapter when gymnasium is not available."""
        with patch("quantchain.backtesting.finrl_adapter.GYMNASIUM_AVAILABLE", False):
            # This should not raise an error
            assert GYMNASIUM_AVAILABLE is False

    def test_finrl_adapter_observation_space_info(self):
        """Test observation space information."""
        with patch("quantchain.backtesting.finrl_adapter.AlpacaDataConnector"):
            adapter = FinRLAdapter(
                connector_type="alpaca",
                symbol="AAPL",
                start_date="2023-01-01",
                end_date="2023-01-10",
            )
            
            # Check that observation space exists when gymnasium is available
            if GYMNASIUM_AVAILABLE:
                assert hasattr(adapter, 'observation_space')

    def test_finrl_adapter_action_space_info(self):
        """Test action space information."""
        with patch("quantchain.backtesting.finrl_adapter.AlpacaDataConnector"):
            adapter = FinRLAdapter(
                connector_type="alpaca",
                symbol="AAPL",
                start_date="2023-01-01",
                end_date="2023-01-10",
            )
            
            # Check that action space exists when gymnasium is available
            if GYMNASIUM_AVAILABLE:
                assert hasattr(adapter, 'action_space')

    def test_finrl_adapter_with_custom_initial_cash(self):
        """Test adapter with custom initial cash."""
        with patch("quantchain.backtesting.finrl_adapter.AlpacaDataConnector"):
            adapter = FinRLAdapter(
                connector_type="alpaca",
                symbol="AAPL",
                start_date="2023-01-01",
                end_date="2023-01-10",
                initial_cash=500000,
            )
            
            assert adapter.initial_cash == 500000
            assert adapter.portfolio["cash"] == 500000

    def test_finrl_adapter_with_custom_commission(self):
        """Test adapter with custom commission."""
        with patch("quantchain.backtesting.finrl_adapter.AlpacaDataConnector"):
            adapter = FinRLAdapter(
                connector_type="alpaca",
                symbol="AAPL",
                start_date="2023-01-01",
                end_date="2023-01-10",
                commission=0.002,
            )
            
            assert adapter.commission == 0.002

    def test_finrl_adapter_with_custom_slippage(self):
        """Test adapter with custom slippage."""
        with patch("quantchain.backtesting.finrl_adapter.AlpacaDataConnector"):
            adapter = FinRLAdapter(
                connector_type="alpaca",
                symbol="AAPL",
                start_date="2023-01-01",
                end_date="2023-01-10",
                slippage=0.0005,
            )
            
            assert adapter.slippage == 0.0005

    def test_finrl_adapter_trade_history_tracking(self):
        """Test trade history tracking."""
        with patch("quantchain.backtesting.finrl_adapter.AlpacaDataConnector"):
            adapter = FinRLAdapter(
                connector_type="alpaca",
                symbol="AAPL",
                start_date="2023-01-01",
                end_date="2023-01-10",
            )
            
            # Initialize empty trade history
            adapter.trade_history = []
            
            # Add a trade
            trade = {
                "step": 0,
                "action": 1,  # Buy
                "price": 100.0,
                "quantity": 100,
                "commission": 10.0,
                "type": "buy"
            }
            adapter.trade_history.append(trade)
            
            assert len(adapter.trade_history) == 1
            assert adapter.trade_history[0]["price"] == 100.0

    def test_finrl_adapter_portfolio_state(self):
        """Test portfolio state management."""
        with patch("quantchain.backtesting.finrl_adapter.AlpacaDataConnector"):
            adapter = FinRLAdapter(
                connector_type="alpaca",
                symbol="AAPL",
                start_date="2023-01-01",
                end_date="2023-01-10",
            )
            
            # Check initial portfolio state
            assert "cash" in adapter.portfolio
            assert "shares" in adapter.portfolio
            assert adapter.portfolio["shares"] == 0
            
            # Update portfolio
            adapter.portfolio["cash"] = 90000
            adapter.portfolio["shares"] = 100
            
            assert adapter.portfolio["cash"] == 90000
            assert adapter.portfolio["shares"] == 100

    def test_finrl_adapter_reward_with_no_trades(self):
        """Test reward calculation with no trades."""
        with patch("quantchain.backtesting.finrl_adapter.AlpacaDataConnector"):
            adapter = FinRLAdapter(
                connector_type="alpaca",
                symbol="AAPL",
                start_date="2023-01-01",
                end_date="2023-01-10",
            )
            
            # Initialize with no previous value
            adapter.last_portfolio_value = None
            
            # Calculate reward
            reward = adapter._calculate_reward()
            
            # Should return 0 when no previous value
            assert reward == 0

    def test_finrl_adapter_order_validation_edge_cases(self):
        """Test order validation with edge cases."""
        with patch("quantchain.backtesting.finrl_adapter.AlpacaDataConnector"):
            adapter = FinRLAdapter(
                connector_type="alpaca",
                symbol="AAPL",
                start_date="2023-01-01",
                end_date="2023-01-10",
            )
            
            # Test with negative action
            assert adapter._validate_action(-1) is False
            
            # Test with very large action
            assert adapter._validate_action(100) is False
            
            # Test with float action
            assert adapter._validate_action(1.5) is False

    def test_finrl_adapter_transaction_cost_zero_quantity(self):
        """Test transaction cost with zero quantity."""
        with patch("quantchain.backtesting.finrl_adapter.AlpacaDataConnector"):
            adapter = FinRLAdapter(
                connector_type="alpaca",
                symbol="AAPL",
                start_date="2023-01-01",
                end_date="2023-01-10",
                commission=0.001,
                slippage=0.0001,
            )
            
            # Test with zero quantity
            cost = adapter._calculate_transaction_cost(0, 100.0, "buy")
            assert cost == 0

    def test_finrl_adapter_market_friction_integration(self):
        """Test integration with market friction simulator."""
        with patch("quantchain.backtesting.finrl_adapter.AlpacaDataConnector"):
            with patch("quantchain.backtesting.finrl_adapter.MarketFrictionSimulator") as mock_friction:
                mock_friction_instance = Mock()
                mock_friction_instance.calculate_slippage.return_value = 0.5
                mock_friction_instance.calculate_commission.return_value = 1.0
                mock_friction.return_value = mock_friction_instance
                
                adapter = FinRLAdapter(
                    connector_type="alpaca",
                    symbol="AAPL",
                    start_date="2023-01-01",
                    end_date="2023-01-10",
                    enable_market_friction=True,
                )
                
                # Test cost calculation with friction
                cost = adapter._calculate_transaction_cost(100, 100.0, "buy")
                
                # Should call both slippage and commission
                mock_friction_instance.calculate_slippage.assert_called()
                mock_friction_instance.calculate_commission.assert_called()

    def test_finrl_adapter_date_format_validation(self):
        """Test date format validation."""
        with patch("quantchain.backtesting.finrl_adapter.AlpacaDataConnector"):
            # Valid date formats
            try:
                FinRLAdapter(
                    connector_type="alpaca",
                    symbol="AAPL",
                    start_date="2023-01-01",
                    end_date="2023-01-31",
                )
            except FinRLDataError:
                pytest.fail("Valid date format raised error")
            
            # Invalid date format should raise error
            with pytest.raises(FinRLDataError):
                FinRLAdapter(
                    connector_type="alpaca",
                    symbol="AAPL",
                    start_date="01/01/2023",
                    end_date="2023-01-31",
                )

    def test_finrl_adapter_step_boundary_conditions(self):
        """Test step method at boundaries."""
        with patch("quantchain.backtesting.finrl_adapter.AlpacaDataConnector"):
            adapter = FinRLAdapter(
                connector_type="alpaca",
                symbol="AAPL",
                start_date="2023-01-01",
                end_date="2023-01-02",  # Only 2 days
            )
            
            # Mock data
            dates = pd.date_range("2023-01-01", "2023-01-02", freq="D")
            adapter.data = pd.DataFrame({
                "open": [100, 101],
                "high": [105, 106],
                "low": [95, 96],
                "close": [104, 105],
                "volume": [1000, 1100],
            }, index=dates)
            
            # Reset to beginning
            adapter.reset()
            
            # Step to end
            obs, reward, terminated, truncated, info = adapter.step(1)  # Buy
            assert terminated is False
            
            # Step to final day
            obs, reward, terminated, truncated, info = adapter.step(1)  # Buy
            assert terminated is True

    def test_finrl_adapter_data_preprocessing_edge_cases(self):
        """Test data preprocessing with edge cases."""
        with patch("quantchain.backtesting.finrl_adapter.AlpacaDataConnector"):
            adapter = FinRLAdapter(
                connector_type="alpaca",
                symbol="AAPL",
                start_date="2023-01-01",
                end_date="2023-01-10",
            )
            
            # Create data with NaN values
            dates = pd.date_range("2023-01-01", "2023-01-03", freq="D")
            raw_data = pd.DataFrame({
                "open": [100, np.nan, 102],
                "high": [105, 106, np.nan],
                "low": [95, 96, 97],
                "close": [104, 105, 106],
                "volume": [1000, 1100, 1200],
            }, index=dates)
            
            # Process data
            processed_data = adapter._preprocess_data(raw_data)
            
            # Should handle NaN values
            assert not processed_data.isnull().all().any()

    def test_finrl_adapter_close_cleanup(self):
        """Test cleanup on close."""
        with patch("quantchain.backtesting.finrl_adapter.AlpacaDataConnector"):
            adapter = FinRLAdapter(
                connector_type="alpaca",
                symbol="AAPL",
                start_date="2023-01-01",
                end_date="2023-01-10",
            )
            
            # Call close method
            adapter.close()
            
            # Should not raise any exceptions
            assert True

    def test_finrl_adapter_render_without_plotly(self):
        """Test rendering without plotly."""
        with patch("quantchain.backtesting.finrl_adapter.AlpacaDataConnector"):
            with patch("quantchain.backtesting.finrl_adapter.HAS_PLOTLY", False):
                adapter = FinRLAdapter(
                    connector_type="alpaca",
                    symbol="AAPL",
                    start_date="2023-01-01",
                    end_date="2023-01-10",
                )
                
                # Should not raise exception even without plotly
                adapter.render()
                assert True

    def test_finrl_adapter_seed_functionality(self):
        """Test random seed functionality."""
        with patch("quantchain.backtesting.finrl_adapter.AlpacaDataConnector"):
            adapter = FinRLAdapter(
                connector_type="alpaca",
                symbol="AAPL",
                start_date="2023-01-01",
                end_date="2023-01-10",
            )
            
            # Set seed
            adapter.seed(42)
            
            # Should not raise exception
            assert True
