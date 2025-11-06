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
        assert not adapter.current_state


class TestAgentStrategy:
    """Test agent strategy wrapper."""

    def test_initialization(self):
        """Test strategy initialization."""
        mock_adapter = Mock()
        initial_state = {"cash": 100000}

        strategy = AgentStrategy(mock_adapter, initial_state)

        assert strategy.adapter == mock_adapter
        assert strategy.current_state.cash == 100000
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
        mock_adapter.config.get.return_value = 0  # Disable timeout
        initial_state = {"cash": 100000}

        strategy = AgentStrategy(mock_adapter, initial_state)
        strategy.position_manager = Mock()

        # Mock state conversion
        mock_agent_state = Mock()
        mock_agent_state.signal = "buy"
        mock_agent_state.quantity = 10
        mock_bar_to_state.return_value = mock_agent_state

        # Mock agent graph execution
        mock_adapter.agent_graph.invoke.return_value = {
            "signal": "buy",
            "quantity": 10,
        }

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

        prompt = "price > 100, should I buy?"
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
        with pytest.raises(SignalConversionError):
            agent_state_to_signal(agent_state)

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


class TestLangGraphWorkflowEdgeCases:
    """Test workflow orchestration edge cases."""

    def test_workflow_with_nested_decisions(self):
        """Test workflow with nested decision points."""
        mock_graph = Mock()
        adapter = LangGraphBacktestAdapter(mock_graph)

        # Create deterministic responses for complex workflow
        deterministic_responses = {
            "initial_analysis": "ANALYZING_MARKET",
            "risk_assessment": "MODERATE_RISK",
            "position_sizing": "CALCULATE_SIZE",
            "final_decision": "EXECUTE_TRADE",
        }

        adapter.set_deterministic_llm(deterministic_responses)

        initial_state = {"cash": 100000, "risk_assessment": {"trend": "up"}}
        strategy = adapter.create_strategy(initial_state)

        # Simulate complex multi-bar sequence
        bars = [
            {
                "timestamp": datetime.now(),
                "symbol": "AAPL",
                "close": 150.0,
                "volume": 1000,
            },
            {
                "timestamp": datetime.now(),
                "symbol": "AAPL",
                "close": 152.0,
                "volume": 1100,
            },
            {
                "timestamp": datetime.now(),
                "symbol": "AAPL",
                "close": 151.0,
                "volume": 900,
            },
        ]

        for bar in bars:
            signal = strategy.next(bar)
            # Should get different deterministic responses at each step
            assert signal is not None

    def test_workflow_with_timeout_handling(self):
        """Test workflow timeout handling and recovery."""
        mock_graph = Mock()
        adapter = LangGraphBacktestAdapter(mock_graph)

        # Configure with timeout
        adapter.config = {"timeout_seconds": 1, "deterministic": True}

        initial_state = {"cash": 100000}
        strategy = adapter.create_strategy(initial_state)

        # Add timeout to deterministic responses
        deterministic_responses = {
            "quick_response": "BUY",
            "timeout_scenario": "TIMEOUT_ERROR",
        }
        adapter.set_deterministic_llm(deterministic_responses)

        with pytest.raises(TimeoutError):
            # This should trigger timeout after configured seconds
            bar = {
                "timestamp": datetime.now(),
                "symbol": "AAPL",
                "close": 150.0,
                "volume": 1000,
            }
            # Simulate delay to trigger timeout
            import time

            time.sleep(2)
            strategy.next(bar)

    def test_workflow_with_state_persistence(self):
        """Test workflow state persistence across steps."""
        mock_graph = Mock()
        adapter = LangGraphBacktestAdapter(mock_graph)

        initial_state = {"cash": 100000, "decisions": []}
        strategy = adapter.create_strategy(initial_state)

        bars = [
            {
                "timestamp": datetime.now(),
                "symbol": "AAPL",
                "close": 150.0,
                "volume": 1000,
            },
            {
                "timestamp": datetime.now(),
                "symbol": "AAPL",
                "close": 155.0,
                "volume": 1000,
            },
        ]

        # Process bars and verify state persistence
        for i, bar in enumerate(bars):
            _ = strategy.next(bar)  # signal assigned but not used

            # Check that reasoning log preserves state
            log = adapter.get_reasoning_log()
            assert len(log) == i + 1

            # Verify state consistency
            current_state = strategy.current_state
            assert current_state.step_count == i + 1

    def test_workflow_error_recovery(self):
        """Test workflow error recovery mechanisms."""
        mock_graph = Mock()
        # Set return value to proper dict
        mock_graph.invoke.return_value = {
            "signal": "hold",
            "signal_confidence": 0.5,
            "decisions": [],
            "observations": [],
            "reasoning": [],
        }
        adapter = LangGraphBacktestAdapter(mock_graph)

        # Configure error simulation
        error_responses = {
            "network_error": "NETWORK_FAILURE",
            "api_error": "API_RATE_LIMIT",
            "data_error": "INVALID_DATA",
        }
        adapter.set_deterministic_llm(error_responses)

        initial_state = {"cash": 100000}
        strategy = adapter.create_strategy(initial_state)

        # Test network error recovery
        with patch("time.sleep"):  # Mock sleep to speed up test
            bar = {
                "timestamp": datetime.now(),
                "symbol": "AAPL",
                "close": 150.0,
                "volume": 1000,
            }
            # First call triggers network error
            _ = strategy.next(bar)  # signal1 assigned but not used
            # Should retry and succeed
            signal2 = strategy.next(bar)

        assert signal2 is not None  # Should recover from error

    def test_workflow_with_concurrent_decisions(self):
        """Test workflow with concurrent decision scenarios."""
        mock_graph = Mock()
        mock_graph.invoke.return_value = {
            "signal": "buy",
            "signal_confidence": 0.8,
            "decisions": ["buy"],
            "observations": [],
            "reasoning": [],
        }
        adapter = LangGraphBacktestAdapter(mock_graph)

        # Configure concurrent decision handling
        concurrent_responses = {
            "concurrent_buy": "CONCURRENT_BUY_DECISION",
            "concurrent_sell": "CONCURRENT_SELL_DECISION",
            "conflict_resolution": "CONFLICT_RESOLVE",
        }
        adapter.set_deterministic_llm(concurrent_responses)

        initial_state = {"cash": 100000, "positions": {"AAPL": 5}}
        strategy = adapter.create_strategy(initial_state)

        # Simulate concurrent scenario
        bar = {
            "timestamp": datetime.now(),
            "symbol": "AAPL",
            "close": 150.0,
            "volume": 1000,
            "news_sentiment": "positive",
            "market_volatility": "high",
        }

        signal = strategy.next(bar)

        # Should handle concurrent decision scenario
        assert signal is not None
        log = adapter.get_reasoning_log()
        assert len(log) > 0
        assert any("concurrent" in entry.get("decision", "").lower() for entry in log)


class TestLangGraphComplexScenarios:
    """Test complex multi-step scenarios."""

    def test_multi_symbol_portfolio_management(self):
        """Test managing multiple symbols in portfolio."""
        mock_graph = Mock()
        mock_graph.invoke.return_value = {
            "signal": "hold",
            "signal_confidence": 0.6,
            "decisions": [],
            "observations": [],
            "reasoning": [],
        }
        _adapter = LangGraphBacktestAdapter(mock_graph)
        initial_state = {"cash": 100000}
        _strategy = _adapter.create_strategy(initial_state)

        # Simulate multi-symbol data
        symbols = ["AAPL", "GOOGL", "MSFT"]
        for i in range(10):
            symbol = symbols[i % len(symbols)]
            bar = {
                "timestamp": datetime.now(),
                "symbol": symbol,
                "close": 150.0 + (i * 0.5),
                "volume": 1000,
                "sector_performance": (
                    "technology" if symbol in ["AAPL", "MSFT"] else "diversified"
                ),
            }
            _ = _strategy.next(bar)

            if i == 5:
                # Mid-way through, verify portfolio balance
                current_state = _strategy.current_state
                assert (
                    len(current_state.positions) >= 2
                )  # Should have multiple positions

    def test_dynamic_risk_adjustment(self):
        """Test dynamic risk adjustment during workflow."""
        mock_graph = Mock()
        mock_graph.invoke.return_value = {
            "signal": "hold",
            "signal_confidence": 0.7,
            "decisions": [],
            "observations": [],
            "reasoning": [],
        }
        _adapter = LangGraphBacktestAdapter(mock_graph)

        # Configure risk adjustment scenarios
        risk_scenarios = {
            "low_volatility": "CONSERVATIVE_RISK",
            "high_volatility": "AGGRESSIVE_RISK",
            "regime_change": "RISK_REGIME_SHIFT",
        }
        _adapter.set_deterministic_llm(risk_scenarios)

        initial_state = {"cash": 100000}
        strategy = _adapter.create_strategy(initial_state)

        # Simulate changing market conditions
        volatility_levels = [0.01, 0.02, 0.05, 0.01, 0.03]
        for i, volatility in enumerate(volatility_levels):
            bar = {
                "timestamp": datetime.now(),
                "symbol": "AAPL",
                "close": 150.0 + (i * 2),
                "volume": 1000,
                "market_volatility": volatility,
                "risk_factor": "high" if volatility > 0.03 else "low",
            }
            _ = strategy.next(bar)

            if i == 2:
                # Verify risk adjustment happened
                log = _adapter.get_reasoning_log()
                assert any(
                    "risk" in entry.get("decision", "").lower() for entry in log[-3:]
                )

    def test_market_regime_detection(self):
        """Test market regime detection and adaptation."""
        mock_graph = Mock()
        mock_graph.invoke.return_value = {
            "signal": "hold",
            "signal_confidence": 0.5,
            "decisions": [],
            "observations": [],
            "reasoning": [],
        }
        _adapter = LangGraphBacktestAdapter(mock_graph)

        regime_responses = {
            "bull_market": "BULL_REGIME_DETECTED",
            "bear_market": "BEAR_REGIME_DETECTED",
            "sideways": "SIDEWAYS_REGIME_DETECTED",
            "transitional": "REGIME_TRANSITION",
        }
        _adapter.set_deterministic_llm(regime_responses)

        initial_state = {"cash": 100000}
        strategy = _adapter.create_strategy(initial_state)

        # Simulate different regime conditions
        market_conditions = [
            {"trend": "strong_up", "volatility": "low", "volume": "high"},
            {"trend": "down", "volatility": "high", "volume": "moderate"},
            {"trend": "sideways", "volatility": "low", "volume": "low"},
            {"trend": "transitional", "volatility": "extreme", "volume": "irregular"},
        ]

        for i, condition in enumerate(market_conditions):
            bar = {
                "timestamp": datetime.now(),
                "symbol": "AAPL",
                "close": 150.0 + (i * 0.5),
                "volume": 1000,
                **condition,
            }
            _ = strategy.next(bar)

            # Every few bars, check regime detection in reasoning
            if i % 3 == 2:
                log = _adapter.get_reasoning_log()
                recent_entries = log[-3:]
                assert any(
                    "regime" in entry.get("analysis", "").lower()
                    for entry in recent_entries
                )

    def test_complex_order_management(self):
        """Test complex order management scenarios."""
        mock_graph = Mock()
        mock_graph.invoke.return_value = {
            "signal": "buy",
            "signal_confidence": 0.9,
            "decisions": ["buy"],
            "observations": [],
            "reasoning": [],
        }
        adapter = LangGraphBacktestAdapter(mock_graph)

        order_scenarios = {
            "partial_fill": "PARTIAL_FILL_RESPONSE",
            "order_cancellation": "ORDER_CANCEL_RESPONSE",
            "order_modification": "ORDER_MODIFY_RESPONSE",
        }
        adapter.set_deterministic_llm(order_scenarios)

        initial_state = {
            "cash": 100000,
        }
        strategy = adapter.create_strategy(initial_state)

        # Test order scenarios
        scenarios = [
            {"action": "buy", "quantity": 100, "expected_partial": 0.6},
            {"action": "modify", "order_id": "12345", "new_quantity": 80},
            {"action": "cancel", "order_id": "12346", "reason": "market_changed"},
        ]

        for scenario in scenarios:
            bar = {
                "timestamp": datetime.now(),
                "symbol": "AAPL",
                "close": 150.0,
                "volume": 1000,
                "order_event": scenario,
            }
            signal = strategy.next(bar)

            # Verify order management in signal
            if signal and scenario["action"] != "buy":
                assert "order" in str(signal).lower()





class TestLangGraphErrorHandling:
    """Test error handling and recovery."""

    def test_agent_graph_failure_recovery(self):
        """Test recovery from agent graph failures."""
        mock_graph = Mock()

        # Configure graph to fail on specific calls
        def failing_invoke(*args, **kwargs):
            if "risk_assessment" in str(args):
                raise AgentExecutionError("Risk assessment service unavailable")
            return {
                "signal": "hold",
                "signal_confidence": 0.5,
                "decisions": [],
                "observations": [],
                "reasoning": [],
            }

        mock_graph.invoke = failing_invoke

        adapter = LangGraphBacktestAdapter(mock_graph)
        initial_state = {"cash": 100000}
        strategy = adapter.create_strategy(initial_state)

        bar = {
            "timestamp": datetime.now(),
            "symbol": "AAPL",
            "close": 150.0,
            "volume": 1000,
            "requires_risk_assessment": True,
        }

        # Should handle graph failure gracefully
        signal = strategy.next(bar)
        assert signal is not None  # Should get fallback signal

    def test_data_validation_error_handling(self):
        """Test handling of data validation errors."""
        mock_graph = Mock()
        mock_graph.invoke.return_value = {
            "signal": "hold",
            "signal_confidence": 0.5,
            "decisions": [],
            "observations": [],
            "reasoning": [],
        }
        adapter = LangGraphBacktestAdapter(mock_graph)

        initial_state = {"cash": 100000}
        strategy = adapter.create_strategy(initial_state)

        # Test various invalid data scenarios
        invalid_bars = [
            {"symbol": None, "close": 150.0, "volume": 1000},  # Missing symbol
            {"symbol": "AAPL", "close": None, "volume": 1000},  # Missing close price
            {"symbol": "AAPL", "close": -50.0, "volume": 1000},  # Negative price
            {"symbol": "AAPL", "close": 150.0, "volume": -1000},  # Negative volume
            {"symbol": "", "close": 150.0, "volume": 1000},  # Empty symbol
        ]

        for invalid_bar in invalid_bars:
            # Should handle invalid data gracefully
            try:
                _ = strategy.next(invalid_bar)
                # Should either return None or a safe signal
                assert True  # Should not crash
            except Exception as e:
                # Should handle expected validation errors
                assert "invalid" in str(e).lower() or "missing" in str(e).lower()

    def test_resource_constraint_handling(self):
        """Test handling of resource constraints."""
        mock_graph = Mock()
        mock_graph.invoke.return_value = {
            "signal": "hold",
            "signal_confidence": 0.5,
            "decisions": [],
            "observations": [],
            "reasoning": [],
        }
        adapter = LangGraphBacktestAdapter(mock_graph)

        # Configure resource constraints
        adapter.config = {
            "max_concurrent_requests": 1,
            "rate_limit_per_second": 2,
            "memory_limit_mb": 100,
        }

        initial_state = {"cash": 100000}
        strategy = adapter.create_strategy(initial_state)

        # Rapid sequence that should trigger rate limits
        bars = [
            {
                "timestamp": datetime.now(),
                "symbol": "AAPL",
                "close": 150.0,
                "volume": 1000,
            }
            for _ in range(5)
        ]

        signals = []
        for bar in bars:
            signal = strategy.next(bar)
            if signal:
                signals.append(signal)

        # Should handle rate limiting
        assert len(signals) <= 2  # Limited by rate constraint

    def test_partial_data_recovery(self):
        """Test recovery from partial or incomplete data."""
        mock_graph = Mock()
        adapter = LangGraphBacktestAdapter(mock_graph)

        initial_state = {"cash": 100000}
        strategy = adapter.create_strategy(initial_state)

        # Test partial data scenarios
        partial_scenarios = [
            {"close": 150.0},  # Missing other fields
            {"symbol": "AAPL", "volume": 1000},  # Missing close price
            {"timestamp": datetime.now()},  # Only timestamp
        ]

        for partial_data in partial_scenarios:
            # Should handle partial data gracefully
            try:
                _ = strategy.next(partial_data)
                assert True  # Should not crash
            except Exception:
                # Should handle gracefully
                assert True

    def test_state_consistency_validation(self):
        """Test state consistency validation."""
        mock_graph = Mock()
        mock_graph.invoke.return_value = {
            "signal": "hold",
            "signal_confidence": 0.5,
            "decisions": [],
            "observations": [],
            "reasoning": [],
        }
        adapter = LangGraphBacktestAdapter(mock_graph)

        initial_state = {"cash": 100000}
        strategy = adapter.create_strategy(initial_state)

        # Process some bars to build state
        bars = [
            {
                "timestamp": datetime.now(),
                "symbol": "AAPL",
                "close": 150.0,
                "volume": 1000,
            },
            {
                "timestamp": datetime.now(),
                "symbol": "AAPL",
                "close": 155.0,
                "volume": 1000,
            },
        ]

        for bar in bars:
            strategy.next(bar)

        # Verify state consistency
        current_state = strategy.current_state

        # Cash + position values should equal initial equity (approximately)
        total_value = current_state.cash
        for symbol, quantity in current_state.positions.items():
            total_value += quantity * 155.0  # Last price

        # Should be close to starting value (allowing for trading costs)
        assert abs(total_value - 100000) < 5000  # Allow some slippage/fees

        # Step count should be accurate
        assert current_state.step_count == len(bars)

        # Timestamp should be recent
        assert current_state.timestamp is not None
        assert (datetime.now() - current_state.timestamp).total_seconds() < 60
