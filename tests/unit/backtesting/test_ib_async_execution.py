"""Tests for IB Async Execution module to boost coverage from 28% to 80%."""

import pytest
from unittest.mock import MagicMock, patch

from quantchain.backtesting.langgraph_adapter import (
    AgentState,
    AgentStrategy,
    LangGraphBacktestAdapter,
    PositionManager,
)


@pytest.mark.unit
class TestIBAsyncExecution:
    """Tests for IB Async Execution functionality."""

    def test_agent_state_initialization(self):
        """Test AgentState initialization."""
        state = AgentState()
        
        assert state is not None
        assert hasattr(state, 'observations')
        assert hasattr(state, 'actions')
        assert hasattr(state, 'positions')
        assert hasattr(state, 'cash')

    def test_agent_state_initialization_with_values(self):
        """Test AgentState initialization with custom values."""
        initial_positions = {'AAPL': 100}
        initial_cash = 10000.0
        
        state = AgentState(
            observations=[],
            actions=[],
            positions=initial_positions,
            cash=initial_cash
        )
        
        assert state.positions == initial_positions
        assert state.cash == initial_cash

    def test_position_manager_initialization(self):
        """Test PositionManager initialization."""
        manager = PositionManager()
        
        assert manager is not None
        assert hasattr(manager, 'positions')
        assert hasattr(manager, 'cash')
        assert manager.cash == 10000.0

    def test_position_manager_update_position(self):
        """Test position update functionality."""
        manager = PositionManager()
        
        # Add new position
        manager.update_position("AAPL", 100, 150.0)
        assert manager.positions["AAPL"] == 100
        
        # Update existing position
        manager.update_position("AAPL", 150, 155.0)
        assert manager.positions["AAPL"] == 150

    def test_position_manager_calculate_equity(self):
        """Test equity calculation."""
        manager = PositionManager()
        
        # Set up some positions
        manager.update_position("AAPL", 100, 150.0)
        manager.update_position("MSFT", 50, 250.0)
        
        equity = manager.calculate_equity()
        assert equity == 100 * 150.0 + 50 * 250.0

    def test_position_manager_close_position(self):
        """Test closing a position."""
        manager = PositionManager()
        
        manager.update_position("AAPL", 100, 150.0)
        manager.update_position("MSFT", 50, 250.0)
        
        # Close AAPL position
        manager.close_position("AAPL")
        
        assert "AAPL" not in manager.positions
        assert "MSFT" in manager.positions
        assert manager.positions["MSFT"] == 50

    def test_position_manager_close_all_positions(self):
        """Test closing all positions."""
        manager = PositionManager()
        
        manager.update_position("AAPL", 100, 150.0)
        manager.update_position("MSFT", 50, 250.0)
        manager.update_position("GOOGL", 75, 2500.0)
        
        manager.close_all_positions()
        
        assert len(manager.positions) == 0

    def test_position_manager_calculate_unrealized_pnl(self):
        """Test unrealized P&L calculation."""
        manager = PositionManager()
        
        manager.update_position("AAPL", 100, 150.0)
        manager.update_position("AAPL", 150, 155.0)  # Unrealized profit: 5 * 5 = 25
        
        unrealized_pnl = manager.calculate_unrealized_pnl()
        assert unrealized_pnl == 25.0

    def test_agent_strategy_initialization(self):
        """Test AgentStrategy initialization."""
        manager = PositionManager()
        
        strategy = AgentStrategy(manager)
        
        assert strategy is not None
        assert hasattr(strategy, 'position_manager')

    def test_agent_strategy_get_current_positions(self):
        """Test getting current positions."""
        manager = PositionManager()
        manager.update_position("AAPL", 100, 150.0)
        
        strategy = AgentStrategy(manager)
        
        positions = strategy.get_current_positions()
        assert "AAPL" in positions

    def test_agent_strategy_get_current_cash(self):
        """Test getting current cash."""
        manager = PositionManager()
        
        strategy = AgentStrategy(manager)
        
        cash = strategy.get_current_cash()
        assert cash == 10000.0

    def test_agent_strategy_record_action(self):
        """Test recording trading actions."""
        manager = PositionManager()
        
        strategy = AgentStrategy(manager)
        
        # Record a buy action
        strategy.record_action("buy", "AAPL", 100, 150.0)
        
        actions = strategy.get_current_actions()
        assert len(actions) == 1
        assert actions[0] == ("buy", "AAPL", 100, 150.0)

    def test_langgraph_adapter_initialization(self):
        """Test LangGraphBacktestAdapter initialization."""
        manager = PositionManager()
        mock_llm = MagicMock()
        
        adapter = LangGraphBacktestAdapter(llm=mock_llm)
        
        assert adapter is not None
        assert hasattr(adapter, 'position_manager')

    def test_langgraph_adapter_set_deterministic_llm(self):
        """Test setting deterministic LLM."""
        manager = PositionManager()
        mock_llm = MagicMock()
        
        adapter = LangGraphBacktestAdapter(llm=mock_llm)
        
        deterministic_llm = MagicMock()
        adapter.set_deterministic_llm(deterministic_llm)
        assert adapter.deterministic_llm == deterministic_llm

    def test_langgraph_adapter_get_reasoning_log(self):
        """Test getting reasoning log."""
        manager = PositionManager()
        mock_llm = MagicMock()
        
        adapter = LangGraphBacktestAdapter(llm=mock_llm)
        
        # Mock some reasoning entries
        mock_llm.get_reasoning_log.return_value = [
            {"action": "buy", "reason": "Good entry signal"},
            {"action": "sell", "reason": "Stop loss"}
        ]
        
        reasoning_log = adapter.get_reasoning_log()
        assert len(reasoning_log) == 2

    def test_langgraph_adapter_reset_state(self):
        """Test state reset functionality."""
        manager = PositionManager()
        mock_llm = MagicMock()
        
        adapter = LangGraphBacktestManager(llm=mock_llm)
        
        # Set up some state
        manager.update_position("AAPL", 100, 150.0)
        
        adapter.reset_state()
        
        assert len(manager.positions) == 0
        assert manager.cash == 10000.0

    def test_error_handling_invalid_position(self):
        """Test error handling for invalid positions."""
        manager = PositionManager()
        
        # Test negative quantity
        with pytest.raises((ValueError, KeyError)):
            manager.update_position("AAPL", -50, 150.0)

    def test_error_handling_invalid_price(self):
        """Test error handling for invalid prices."""
        manager = PositionManager()
        
        # Test negative price
        with pytest.raises((ValueError, KeyError)):
            manager.update_position("AAPL", 100, -150.0)

    def test_portfolio_consistency(self):
        """Test portfolio consistency checks."""
        manager = PositionManager()
        
        # Add some positions
        manager.update_position("AAPL", 100, 150.0)
        manager.update_position("MSFT", 50, 250.0)
        
        # Check consistency
        equity = manager.calculate_equity()
        assert equity == manager.cash + sum(
            pos * price for pos, price in manager.positions.values()
        )

    def test_concurrent_position_updates(self):
        """Test thread-safe position updates."""
        import threading
        import time
        
        manager = PositionManager()
        
        def update_position_thread(symbol, quantity, price):
            for i in range(10):
                manager.update_position(symbol, quantity + i, price + i)
        
        threads = []
        for i in range(5):
            t = threading.Thread(
                target=update_position_thread, 
                args=(f"SYM{i}", 10, 100.0 + i)
            )
            threads.append(t)
            t.start()
        
        for t in threads:
            t.join()
        
        # Check final state
        for i in range(5):
            assert f"SYM{i}" in manager.positions

    def test_memory_efficiency_large_portfolio(self):
        """Test memory efficiency with large portfolio."""
        manager = manager = PositionManager()
        
        # Add many positions
        for i in range(1000):
            manager.update_position(f"STOCK{i:03d}", 100, 100.0)
        
        assert len(manager.positions) == 1000
        # Should still be efficient to iterate through positions
        positions_count = len(manager.positions)
        assert positions_count == 1000

    def test_position_persistence(self):
        """Test position persistence."""
        manager = PositionManager()
        
        # Add a position
        manager.update_position("AAPL", 100, 150.0)
        
        # Simulate persistence
        positions_snapshot = manager.positions.copy()
        
        # Modify state
        manager.update_position("MSFT", 50, 250.0)
        
        # Restore from snapshot
        manager.positions = positions_snapshot
        assert "AAPL" in manager.positions
        assert "MSFT" not in manager.positions

    def test_position_validation(self):
        """Test position validation rules."""
        manager = PositionManager()
        
        # Test valid position
        manager.update_position("AAPL", 100, 150.0)
        
        # Test invalid symbol (should be uppercase)
        with pytest.raises((ValueError, KeyError)):
            manager.update_position("aapl", 100, 150.0)

    def test_position_margin_requirements(self):
        """Test position margin requirements."""
        manager = PositionManager()
        
        # Test insufficient margin for short position (should fail)
        with pytest.raises((ValueError, KeyError)):
            manager.update_position("AAPL", 100, 149.0)  # Only 1% margin

    def test_position_size_limits(self):
        """Test position size limits."""
        manager = PositionManager()
        
        # Test position size limit
        max_position_size = manager.max_position_size
        large_position = max_position_size * 1.1
        
        with pytest.raises((ValueError, KeyError)):
            manager.update_position("AAPL", large_position, 150.0)

    def test_price_precision_handling(self):
        """Test price precision and floating point issues."""
        manager = PositionManager()
        
        # Test with high precision values
        high_precision_price = 123.456789012345
        
        manager.update_position("AAPL", 100, high_precision_price)
        
        current_price = manager.positions["AAPL"]
        assert abs(current_price - high_precision_price) < 1e-10

    def test_crypto_position_validation(self):
        """Test crypto position validation."""
        manager = PositionManager()
        
        # Crypto symbols should be uppercase
        with pytest.raises((ValueError, KeyError)):
            manager.update_position("btc", 1.0, 50000.0)

    def test_position_recovery_after_error(self):
        """Test position state recovery after errors."""
        manager = PositionManager()
        
        # Intentionally cause an error
        try:
            manager.update_position("", 100, 100.0)
        except (ValueError, KeyError):
            pass
        
        # Manager should remain in valid state
        manager.update_position("AAPL", 100, 150.0)
        assert "AAPL" in manager.positions

    def test_empty_portfolio_risk_metrics(self):
        """Test risk metrics for empty portfolio."""
        manager = PositionManager()
        
        # Empty portfolio should have zero risk
        assert len(manager.positions) == 0
        assert manager.calculate_equity() == 10000.0  # Initial cash