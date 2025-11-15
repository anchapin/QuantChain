"""Tests for FinRL adapter module."""

import pytest
import pandas as pd
import numpy as np
from unittest.mock import Mock, patch

try:
    from quantchain.backtesting.finrl_adapter import (
        FinRLAdapter,
        FinRLAdapterError,
        FinRLConnectionError,
        FinRLDataError,
        get_connector,
    )
    from quantchain.backtesting.market_friction import MarketFrictionSimulator
    from quantchain.backtesting.performance_metrics import PerformanceMetrics
    FINRL_ADAPTER_AVAILABLE = True
except ImportError as e:
    FINRL_ADAPTER_AVAILABLE = False
    print(f"Import error: {e}")

pytestmark = pytest.mark.skipif(
    not FINRL_ADAPTER_AVAILABLE, reason="FinRL adapter not available"
)


class TestFinRLAdapter:
    """Tests for FinRL Adapter functionality."""

    def test_finrl_adapter_error_inheritance(self) -> None:
        """Test that FinRL adapter errors are properly inherited."""
        assert issubclass(FinRLAdapterError, Exception)
        assert issubclass(FinRLConnectionError, FinRLAdapterError)
        assert issubclass(FinRLDataError, FinRLAdapterError)

    def test_market_friction_simulator_initialization(self) -> None:
        """Test market friction simulator initialization."""
        simulator = MarketFrictionSimulator()
        assert simulator.commission_rate == 0.001
        assert simulator.slippage_rate == 0.0005

    def test_market_friction_calculate_slippage(self) -> None:
        """Test slippage calculation."""
        simulator = MarketFrictionSimulator()
        simulator.slippage_rate = 0.001

        # Test buy side
        buy_price = simulator.calculate_slippage(100.0, 10, "buy")
        assert buy_price > 100.0  # Price increases when buying

        # Test sell side
        sell_price = simulator.calculate_slippage(100.0, 10, "sell")
        assert sell_price < 100.0  # Price decreases when selling

    def test_market_friction_calculate_commission(self) -> None:
        """Test commission calculation."""
        simulator = MarketFrictionSimulator()
        simulator.commission_rate = 0.002

        commission = simulator.calculate_commission(1000.0, 10)
        assert commission == 20.0  # 1000 * 10 * 0.002

    def test_performance_metrics_initialization(self) -> None:
        """Test performance metrics initialization."""
        metrics = PerformanceMetrics()
        assert metrics.total_return == 0.0
        assert metrics.sharpe_ratio == 0.0
        assert metrics.max_drawdown == 0.0

    def test_performance_metrics_calculate_total_return(self) -> None:
        """Test total return calculation."""
        metrics = PerformanceMetrics()
        metrics.initial_value = 1000.0
        metrics.current_value = 1200.0

        total_return = metrics.calculate_total_return()
        assert total_return == 0.2  # 20% return

    def test_performance_metrics_calculate_returns(self) -> None:
        """Test returns calculation from series."""
        metrics = PerformanceMetrics()
        equity_curve = pd.Series([1000, 1050, 1100, 1150, 1200])

        returns = metrics.calculate_returns(equity_curve)
        assert len(returns) == 4
        assert all(r > 0 for r in returns)  # All positive returns

    def test_performance_metrics_calculate_sharpe(self) -> None:
        """Test Sharpe ratio calculation."""
        metrics = PerformanceMetrics()
        returns = pd.Series([0.01, 0.02, 0.015, 0.025, 0.005])
        risk_free_rate = 0.02

        sharpe = metrics.calculate_sharpe(returns, risk_free_rate)
        assert isinstance(sharpe, float)

    def test_performance_metrics_calculate_max_drawdown(self) -> None:
        """Test maximum drawdown calculation."""
        metrics = PerformanceMetrics()
        equity_curve = pd.Series([1000, 1200, 1100, 1300, 900, 1100])

        max_drawdown = metrics.calculate_max_drawdown(equity_curve)
        assert isinstance(max_drawdown, float)
        assert max_drawdown > 0  # Should have some drawdown

    @patch("quantchain.backtesting.finrl_adapter.get_connector")
    def test_finrl_adapter_init_minimal(
        self, mock_get_connector
    ) -> None:
        """Test FinRL adapter minimal initialization."""
        mock_connector = Mock()
        mock_get_connector.return_value = mock_connector

        adapter = FinRLAdapter()
        assert adapter is not None

    def test_get_connector_invalid(self) -> None:
        """Test getting invalid connector."""
        with pytest.raises(ValueError):
            get_connector("invalid")

    @patch("quantchain.backtesting.finrl_adapter.get_connector")
    @patch("quantchain.backtesting.finrl_adapter.PerformanceMetrics")
    @patch("quantchain.backtesting.finrl_adapter.MarketFrictionSimulator")
    def test_finrl_adapter_init_with_params(
        self, mock_friction, mock_metrics, mock_get_connector
    ) -> None:
        """Test FinRL adapter initialization with parameters."""
        mock_connector = Mock()
        mock_get_connector.return_value = mock_connector

        adapter = FinRLAdapter()
        assert adapter is not None
        mock_get_connector.assert_called_once()

    def test_get_connector_with_missing_source(self) -> None:
        """Test getting connector with missing source."""
        with pytest.raises(ImportError):
            get_connector("missing_source")

    def test_get_connector_with_empty_source(self) -> None:
        """Test getting connector with empty source."""
        with pytest.raises(ValueError):
            get_connector("")
