"""
Tests for LangGraph adapter for agent backtesting.
"""

import pytest
from datetime import datetime
import pandas as pd
from unittest.mock import Mock, patch, mock_open

# Import classes that will be implemented
from quantchain.backtesting.langgraph_adapter import (
    LangGraphBacktestAdapter,
    AgentStrategy,
    AgentState,
    DeterministicLLMWrapper,
    ReasoningEntry,
    bar_to_agent_state,
    agent_state_to_signal,
    capture_reasoning,
    PositionManager,
    AgentExecutionError,
    TimeoutError,
    SignalConversionError,
    PositionError,
)


class TestLangGraphBacktestAdapter:
    """Test LangGraph backtest adapter."""

    def test_initialization(self):
        """Test adapter initialization."""
        mock_graph = Mock()
        config = {"deterministic": True}

        adapter = LangGraphBacktestAdapter(mock_graph, config)

        assert adapter.agent_graph == mock_graph
        assert adapter.config == config
        assert adapter.reasoning_log == []

    def test_create_strategy(self):
        """Test strategy creation."""
        mock_graph = Mock()
        adapter = LangGraphBacktestAdapter(mock_graph)
        initial_state = {"cash": 100000}

        strategy = adapter.create_strategy(initial_state)

        assert isinstance(strategy, AgentStrategy)
        assert strategy.adapter == adapter
        assert strategy.current_state.cash == 100000

    def test_set_deterministic_llm(self):
        """Test deterministic LLM configuration."""
        mock_graph = Mock()
        adapter = LangGraphBacktestAdapter(mock_graph)

        deterministic_responses = {
            "price > 100": "BUY",
            "price < 90": "SELL",
            "default": "HOLD",
        }

        adapter.set_deterministic_llm(deterministic_responses)

        assert hasattr(adapter, "deterministic_responses")
        assert adapter.deterministic_responses == deterministic_responses

    def test_get_reasoning_log(self):
        """Test reasoning log retrieval."""
        mock_graph = Mock()
        adapter = LangGraphBacktestAdapter(mock_graph)

        # Add some test entries to reasoning log
        entry = {
            "timestamp": datetime.now(),
            "step": 1,
            "decision": "BUY",
            "confidence": 0.8,
        }
        adapter.reasoning_log.append(entry)

        log = adapter.get_reasoning_log()

        assert len(log) == 1
        assert log[0] == entry

    def test_reset_state(self):
        """Test state reset."""
        mock_graph = Mock()
        adapter = LangGraphBacktestAdapter(mock_graph)

        # Add some state
        adapter.reasoning_log.append({"test": "data"})
        adapter.current_state = {"cash": 50000}

        adapter.reset_state()

        assert len(adapter.reasoning_log) == 0
        assert adapter.current_state == {}


class TestAgentStrategy:
    """Test agent strategy wrapper."""

    def test_initialization(self):
        """Test strategy initialization."""
        mock_adapter = Mock()
        initial_state = {"cash": 100000}

        strategy = AgentStrategy(mock_adapter, initial_state)

        assert strategy.adapter == mock_adapter
        assert strategy.current_state == initial_state
        assert isinstance(strategy.position_manager, PositionManager)

    def test_init(self):
        """Test strategy initialization with cash and positions."""
        mock_adapter = Mock()
        initial_state = {"cash": 100000}

        strategy = AgentStrategy(mock_adapter, initial_state)

        strategy.init(100000, {"AAPL": 10})

        assert strategy.position_manager.get_cash() == 100000
        assert strategy.position_manager.get_positions() == {"AAPL": 10}

    @patch("quantchain.backtesting.langgraph_adapter.bar_to_agent_state")
    def test_next(self, mock_bar_to_state):
        """Test processing next bar."""
        mock_adapter = Mock()
        initial_state = {"cash": 100000}

        strategy = AgentStrategy(mock_adapter, initial_state)
        strategy.position_manager = Mock()

        # Mock state conversion
        mock_agent_state = Mock()
        mock_agent_state.signal = "buy"
        mock_agent_state.quantity = 10
        mock_bar_to_state.return_value = mock_agent_state

        # Mock agent graph execution
        mock_agent_state_copy = Mock()
        mock_adapter.agent_graph.invoke.return_value = mock_agent_state_copy

        bar = {
            "timestamp": datetime.now(),
            "symbol": "AAPL",
            "close": 150.0,
            "volume": 1000,
        }

        signal = strategy.next(bar)

        # Verify state conversion was called
        mock_bar_to_state.assert_called_once()

        # Verify agent graph was invoked
        mock_adapter.agent_graph.invoke.assert_called_once()

        # Return the processed signal
        assert signal is not None

    def test_get_current_positions(self):
        """Test getting current positions."""
        mock_adapter = Mock()
        strategy = AgentStrategy(mock_adapter)
        strategy.position_manager = Mock()
        strategy.position_manager.get_positions.return_value = {"AAPL": 10, "GOOGL": 5}

        positions = strategy.get_current_positions()

        assert positions == {"AAPL": 10, "GOOGL": 5}
        strategy.position_manager.get_positions.assert_called_once()

    def test_get_current_cash(self):
        """Test getting current cash."""
        mock_adapter = Mock()
        strategy = AgentStrategy(mock_adapter)
        strategy.position_manager = Mock()
        strategy.position_manager.get_cash.return_value = 50000.0

        cash = strategy.get_current_cash()

        assert cash == 50000.0
        strategy.position_manager.get_cash.assert_called_once()


class TestAgentState:
    """Test agent state data structure."""

    def test_default_initialization(self):
        """Test default state initialization."""
        state = AgentState()

        assert state.current_bar == {}
        assert isinstance(state.market_data, pd.DataFrame)
        assert len(state.market_data) == 0
        assert state.cash == 100000.0
        assert state.positions == {}
        assert state.equity == 100000.0
        assert state.observations == []
        assert state.reasoning == []
        assert state.decisions == []
        assert state.signal is None
        assert state.signal_confidence == 0.0
        assert state.quantity == 0
        assert state.risk_assessment == {}
        assert state.position_sizing == {}
        assert state.order_details == {}
        assert isinstance(state.timestamp, datetime)
        assert state.step_count == 0

    def test_custom_initialization(self):
        """Test custom state initialization."""
        custom_time = datetime(2023, 1, 1, 12, 0, 0)

        state = AgentState(
            cash=50000.0,
            positions={"AAPL": 10},
            equity=55000.0,
            signal="buy",
            signal_confidence=0.8,
            quantity=5,
            timestamp=custom_time,
            step_count=5,
        )

        assert state.cash == 50000.0
        assert state.positions == {"AAPL": 10}
        assert state.equity == 55000.0
        assert state.signal == "buy"
        assert state.signal_confidence == 0.8
        assert state.quantity == 5
        assert state.timestamp == custom_time
        assert state.step_count == 5


class TestDeterministicLLMWrapper:
    """Test deterministic LLM wrapper."""

    def test_initialization(self):
        """Test wrapper initialization."""
        response_rules = {"condition1": "response1", "condition2": "response2"}

        wrapper = DeterministicLLMWrapper(response_rules)

        assert wrapper.response_rules == response_rules
        assert wrapper.call_history == []

    def test_call_with_rule_match(self):
        """Test calling with matching rule."""
        response_rules = {"price > 100": "BUY", "price < 90": "SELL"}
        wrapper = DeterministicLLMWrapper(response_rules)

        prompt = "Current price is 105. Should I buy or sell?"
        response = wrapper(prompt)

        # Should match first rule
        assert response == "BUY"
        assert len(wrapper.call_history) == 1

    def test_call_no_rule_match(self):
        """Test calling with no matching rule."""
        response_rules = {"price > 100": "BUY", "price < 90": "SELL"}
        wrapper = DeterministicLLMWrapper(response_rules)

        prompt = "Current price is 95. Should I buy or sell?"
        response = wrapper(prompt)

        # Should use default behavior
        assert response is not None or response == ""
        assert len(wrapper.call_history) == 1

    def test_add_rule(self):
        """Test adding new rule."""
        wrapper = DeterministicLLMWrapper()

        wrapper.add_rule("volume > 1000", "BUY_STRONG")

        assert "volume > 1000" in wrapper.response_rules
        assert wrapper.response_rules["volume > 1000"] == "BUY_STRONG"

    def test_load_scenario(self):
        """Test loading scenario from file."""
        wrapper = DeterministicLLMWrapper()

        # Mock file loading
        with patch(
            "builtins.open", mock_open(read_data='{"test_rule": "test_response"}')
        ):
            with patch("json.load", return_value={"test_rule": "test_response"}):
                wrapper.load_scenario("test_scenario.json")

        assert "test_rule" in wrapper.response_rules

    def test_save_scenario(self):
        """Test saving scenario to file."""
        response_rules = {"test_rule": "test_response"}
        wrapper = DeterministicLLMWrapper(response_rules)

        # Mock file saving
        with patch("builtins.open", mock_open()):
            with patch("json.dump") as mock_dump:
                wrapper.save_scenario("test_scenario.json")

                mock_dump.assert_called_once()


class TestStateConversion:
    """Test state conversion functions."""

    def test_bar_to_agent_state(self):
        """Test converting bar to agent state."""
        bar = {
            "timestamp": datetime(2023, 1, 1, 12, 0, 0),
            "symbol": "AAPL",
            "close": 150.0,
            "volume": 1000,
        }

        current_state = AgentState()
        current_state.step_count = 5

        position_manager = Mock()
        position_manager.get_positions.return_value = {"AAPL": 10}
        position_manager.get_cash.return_value = 50000.0
        position_manager.calculate_equity.return_value = 65000.0

        new_state = bar_to_agent_state(bar, current_state, position_manager)

        assert new_state.current_bar == bar
        assert new_state.timestamp == bar["timestamp"]
        assert new_state.step_count == 6  # incremented
        assert new_state.positions == {"AAPL": 10}
        assert new_state.cash == 50000.0
        assert new_state.equity == 65000.0

    def test_agent_state_to_signal(self):
        """Test converting agent state to signal."""
        # Valid buy signal
        agent_state = AgentState()
        agent_state.signal = "buy"
        agent_state.quantity = 10
        agent_state.cash = 10000.0
        agent_state.current_bar = {"symbol": "AAPL"}

        signal = agent_state_to_signal(agent_state)
        assert signal == "buy"

        # Valid sell signal
        agent_state.signal = "sell"
        agent_state.positions = {"AAPL": 10}

        signal = agent_state_to_signal(agent_state)
        assert signal == "sell"

        # Invalid signal
        agent_state.signal = "invalid"
        signal = agent_state_to_signal(agent_state)
        assert signal is None

        # Insufficient cash for buy
        agent_state.signal = "buy"
        agent_state.cash = 0.0
        signal = agent_state_to_signal(agent_state)
        assert signal is None

        # No position for sell
        agent_state.signal = "sell"
        agent_state.positions = {}
        signal = agent_state_to_signal(agent_state)
        assert signal is None


class TestReasoningCapture:
    """Test reasoning log capture."""

    def test_capture_reasoning(self):
        """Test capturing reasoning entry."""
        agent_state = AgentState()
        agent_state.timestamp = datetime(2023, 1, 1, 12, 0, 0)
        agent_state.step_count = 5
        agent_state.current_bar = {"symbol": "AAPL", "close": 150.0}
        agent_state.observations = ["Price is high"]
        agent_state.reasoning = ["Consider buying"]
        agent_state.decisions = ["Buy 10 shares"]
        agent_state.signal = "buy"
        agent_state.signal_confidence = 0.8
        agent_state.quantity = 10
        agent_state.order_details = {"order_id": 123}

        execution_time = 50.0

        entry = capture_reasoning(agent_state, execution_time)

        assert isinstance(entry, ReasoningEntry)
        assert entry.timestamp == agent_state.timestamp
        assert entry.step == 5
        assert entry.bar_data == agent_state.current_bar
        assert entry.observations == ["Price is high"]
        assert entry.reasoning == ["Consider buying"]
        assert entry.decision == "Buy 10 shares"
        assert entry.signal == "buy"
        assert entry.confidence == 0.8
        assert entry.quantity == 10
        assert entry.execution_details == agent_state.order_details
        assert entry.execution_time_ms == execution_time


class TestPositionManager:
    """Test position management."""

    def test_initialization(self):
        """Test position manager initialization."""
        manager = PositionManager(100000.0)

        assert manager.initial_cash == 100000.0
        assert manager.cash == 100000.0
        assert manager.positions == {}
        assert manager.trades == []

    def test_update_position_buy(self):
        """Test updating position with buy trade."""
        manager = PositionManager(100000.0)

        manager.update_position("AAPL", 10, 150.0, 5.0)

        assert manager.cash == 100000.0 - (10 * 150.0 + 5.0)  # 84995.0
        assert manager.positions == {"AAPL": 10}
        assert len(manager.trades) == 1

        trade = manager.trades[0]
        assert trade["symbol"] == "AAPL"
        assert trade["quantity"] == 10
        assert trade["price"] == 150.0
        assert trade["commission"] == 5.0

    def test_update_position_sell(self):
        """Test updating position with sell trade."""
        manager = PositionManager(100000.0)

        # First buy
        manager.update_position("AAPL", 10, 150.0, 5.0)

        # Then sell
        manager.update_position("AAPL", -10, 160.0, 5.0)

        assert "AAPL" not in manager.positions  # Position closed
        assert len(manager.trades) == 2

        # Cash should increase by trade value minus commission
        expected_cash = 100000.0 - (10 * 150.0 + 5.0) + (10 * 160.0 - 5.0)
        assert manager.cash == expected_cash

    def test_calculate_equity(self):
        """Test equity calculation."""
        manager = PositionManager(100000.0)
        manager.update_position("AAPL", 10, 150.0, 5.0)
        manager.update_position("GOOGL", 5, 2500.0, 10.0)

        current_prices = {"AAPL": 155.0, "GOOGL": 2600.0}
        equity = manager.calculate_equity(current_prices)

        expected_position_value = (10 * 155.0) + (5 * 2600.0)
        expected_equity = manager.cash + expected_position_value

        assert equity == expected_equity

    def test_insufficient_cash_error(self):
        """Test error on insufficient cash."""
        manager = PositionManager(1000.0)

        with pytest.raises(PositionError):
            manager.update_position("AAPL", 10, 150.0, 5.0)  # Too expensive


class TestErrorHandling:
    """Test error handling."""

    def test_agent_execution_error(self):
        """Test agent execution error."""
        mock_graph = Mock()
        mock_graph.invoke.side_effect = Exception("Agent failed")

        adapter = LangGraphBacktestAdapter(mock_graph)
        initial_state = {"cash": 100000}
        strategy = adapter.create_strategy(initial_state)

        with pytest.raises(AgentExecutionError):
            strategy.next({"close": 150.0})

    def test_timeout_error(self):
        """Test timeout error."""
        mock_graph = Mock()
        mock_graph.invoke.side_effect = TimeoutError("Agent timeout")

        adapter = LangGraphBacktestAdapter(mock_graph)
        initial_state = {"cash": 100000}
        strategy = adapter.create_strategy(initial_state)

        with pytest.raises(TimeoutError):
            strategy.next({"close": 150.0})

    def test_signal_conversion_error(self):
        """Test signal conversion error."""
        agent_state = AgentState()
        agent_state.signal = "invalid_signal"

        with pytest.raises(SignalConversionError):
            agent_state_to_signal(agent_state)


if __name__ == "__main__":
    pytest.main([__file__])
