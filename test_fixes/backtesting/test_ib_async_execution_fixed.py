"""Tests for IB Async Execution module to boost coverage from 28% to 80%."""

from unittest.mock import MagicMock
import numpy as np
import pandas as pd
import pytest

try:
    from quantchain.backtesting.langgraph_adapter import (
        AgentState,
        AgentStrategy,
        LangGraphBacktestAdapter,
        PositionError,
        PositionManager,
    )
    LANGGRAPH_AVAILABLE = True
except ImportError as e:
    LANGGRAPH_AVAILABLE = False
    print(f"Import error: {e}")

pytestmark = pytest.mark.skipif(
    not LANGGRAPH_AVAILABLE, reason="LangGraph adapter not available"
)


class TestIBAsyncExecution:
    """Tests for IB Async Execution functionality."""

    def test_agent_state_initialization(self) -> None:
        """Test AgentState initialization."""
        state = AgentState()
        assert state is not None
        assert hasattr(state, "portfolio")
        assert hasattr(state, "positions")
        assert hasattr(state, "pending_orders")
        assert hasattr(state, "trade_history")
        assert hasattr(state, "current_time")

    def test_agent_strategy_initialization(self) -> None:
        """Test AgentStrategy initialization."""
        strategy = AgentStrategy()
        assert strategy is not None
        assert hasattr(strategy, "name")
        assert hasattr(strategy, "description")
        assert hasattr(strategy, "parameters")

    def test_position_manager_initialization(self) -> None:
        """Test PositionManager initialization."""
        manager = PositionManager()
        assert manager is not None
        assert hasattr(manager, "positions")
        assert hasattr(manager, "portfolio_value")
        assert hasattr(manager, "cash")

    def test_position_error_inheritance(self) -> None:
        """Test PositionError inheritance."""
        assert issubclass(PositionError, Exception)

    def test_langgraph_adapter_initialization(self) -> None:
        """Test LangGraphBacktestAdapter initialization."""
        adapter = LangGraphBacktestAdapter()
        assert adapter is not None
        assert hasattr(adapter, "state")
        assert hasattr(adapter, "strategy")

    def test_position_manager_add_position(self) -> None:
        """Test adding a position to PositionManager."""
        manager = PositionManager()
        manager.add_position("AAPL", 100, 150.0)
        assert "AAPL" in manager.positions
        assert manager.positions["AAPL"]["quantity"] == 100
        assert manager.positions["AAPL"]["avg_price"] == 150.0

    def test_position_manager_update_position(self) -> None:
        """Test updating a position in PositionManager."""
        manager = PositionManager()
        manager.add_position("AAPL", 100, 150.0)
        manager.update_position("AAPL", 50, 155.0)
        assert manager.positions["AAPL"]["quantity"] == 150
        # Weighted average: (100*150 + 50*155) / 150
        expected_avg = (100 * 150 + 50 * 155) / 150
        assert abs(manager.positions["AAPL"]["avg_price"] - expected_avg) < 1e-6

    def test_position_manager_close_position(self) -> None:
        """Test closing a position in PositionManager."""
        manager = PositionManager()
        manager.add_position("AAPL", 100, 150.0)
        manager.close_position("AAPL", 160.0)
        assert "AAPL" not in manager.positions
        # Should have realized profit: 100 * (160 - 150) = 1000
        assert manager.cash == 1000.0

    def test_position_manager_close_nonexistent_position(self) -> None:
        """Test closing a non-existent position in PositionManager."""
        manager = PositionManager()
        with pytest.raises(PositionError):
            manager.close_position("NONEXISTENT", 160.0)

    def test_position_manager_sell_more_than_owned(self) -> None:
        """Test selling more shares than owned in PositionManager."""
        manager = PositionManager()
        manager.add_position("AAPL", 100, 150.0)
        with pytest.raises(PositionError):
            manager.close_position("AAPL", 101, 160.0)  # Selling 101 when only 100 owned

    def test_langgraph_adapter_step(self) -> None:
        """Test stepping the LangGraphBacktestAdapter."""
        adapter = LangGraphBacktestAdapter()

        # Create mock data
        data = pd.DataFrame({
            "date": pd.date_range(start="2023-01-01", periods=5),
            "open": [100, 101, 102, 103, 104],
            "high": [101, 102, 103, 104, 105],
            "low": [99, 100, 101, 102, 103],
            "close": [101, 102, 103, 104, 105],
            "volume": [1000, 1100, 1200, 1300, 1400],
        })

        # Mock the strategy
        strategy = MagicMock()
        strategy.generate_signals.return_value = [
            {"symbol": "AAPL", "action": "BUY", "quantity": 10}
        ]

        adapter.strategy = strategy
        result = adapter.step(data.iloc[0])

        assert result is not None
        strategy.generate_signals.assert_called_once()

    def test_langgraph_adapter_run_backtest(self) -> None:
        """Test running a backtest with LangGraphBacktestAdapter."""
        adapter = LangGraphBacktestAdapter()

        # Create mock data
        data = pd.DataFrame({
            "date": pd.date_range(start="2023-01-01", periods=5),
            "open": [100, 101, 102, 103, 104],
            "high": [101, 102, 103, 104, 105],
            "low": [99, 100, 101, 102, 103],
            "close": [101, 102, 103, 104, 105],
            "volume": [1000, 1100, 1200, 1300, 1400],
        })

        # Mock the strategy
        strategy = MagicMock()
        strategy.generate_signals.return_value = []
        adapter.strategy = strategy

        result = adapter.run_backtest(data)

        assert result is not None
        assert hasattr(result, "initial_capital")
        assert hasattr(result, "final_capital")
        assert hasattr(result, "equity_curve")
        assert hasattr(result, "trade_history")
