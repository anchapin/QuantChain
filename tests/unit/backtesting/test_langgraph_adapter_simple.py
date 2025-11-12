"""Tests for LangGraph adapter."""

from datetime import datetime, timezone
from unittest.mock import Mock

import pytest

try:
    from quantchain.backtesting.langgraph_adapter import (
        AgentExecutionError,
        AgentState,
        BacktestConfig,
        BacktestResult,
        DeterministicRuleError,
        LangGraphBacktester,
        PositionError,
        ScenarioLoadError,
        SignalConversionError,
        StateValidationError,
        TimeoutError,
    )

    LANGGRAPH_ADAPTER_AVAILABLE = True
except ImportError as e:
    LANGGRAPH_ADAPTER_AVAILABLE = False
    print(f"Import error: {e}")

pytestmark = pytest.mark.skipif(
    not LANGGRAPH_ADAPTER_AVAILABLE, reason="LangGraph adapter not available"
)


class TestBacktestConfig:
    """Test cases for BacktestConfig."""

    def test_initialization_default(self):
        """Test default initialization."""
        config = BacktestConfig()
        assert config.start_date is None
        assert config.end_date is None
        assert config.initial_balance == 100000
        assert config.commission_rate == 0.001

    def test_initialization_with_values(self):
        """Test initialization with values."""
        start_date = datetime(2023, 1, 1, tzinfo=timezone.utc)
        end_date = datetime(2023, 12, 31, tzinfo=timezone.utc)

        config = BacktestConfig(
            start_date=start_date,
            end_date=end_date,
            initial_balance=500000,
        )

        assert config.start_date == start_date
        assert config.end_date == end_date
        assert config.initial_balance == 500000

    def test_to_dict(self):
        """Test conversion to dictionary."""
        config = BacktestConfig(
            initial_balance=500000,
        )

        result = config.to_dict()
        assert isinstance(result, dict)
        assert result["initial_balance"] == 500000

    def test_from_dict(self):
        """Test creation from dictionary."""
        data = {
            "initial_balance": 500000,
        }

        config = BacktestConfig.from_dict(data)
        assert config.initial_balance == 500000


class TestAgentState:
    """Test cases for AgentState."""

    def test_initialization(self):
        """Test state initialization."""
        state = AgentState()

        assert isinstance(state.data, dict)
        assert isinstance(state.positions, dict)
        assert isinstance(state.signals, list)
        assert state.current_step == 0

    def test_initialization_with_values(self):
        """Test initialization with values."""
        state = AgentState(
            data={"test": "data"},
            positions={"AAPL": 100},
            current_step=5,
            balance=100000,
        )

        assert state.data["test"] == "data"
        assert state.positions["AAPL"] == 100
        assert state.current_step == 5
        assert state.balance == 100000

    def test_update_position(self):
        """Test position update."""
        state = AgentState()

        # Add new position
        state.update_position("AAPL", 100)
        assert state.positions["AAPL"] == 100

        # Update existing position
        state.update_position("AAPL", 150)
        assert state.positions["AAPL"] == 150

    def test_add_signal(self):
        """Test signal addition."""
        state = AgentState()

        signal = {"symbol": "AAPL", "action": "buy"}
        state.add_signal(signal)

        assert len(state.signals) == 1
        assert state.signals[0] == signal

    def test_to_dict(self):
        """Test conversion to dictionary."""
        state = AgentState(
            balance=100000,
            equity=105000,
        )

        result = state.to_dict()
        assert isinstance(result, dict)
        assert result["balance"] == 100000
        assert result["equity"] == 105000

    def test_from_dict(self):
        """Test creation from dictionary."""
        data = {
            "balance": 100000,
            "equity": 105000,
        }

        state = AgentState.from_dict(data)
        assert state.balance == 100000
        assert state.equity == 105000


class TestBacktestResult:
    """Test cases for BacktestResult."""

    def test_initialization(self):
        """Test result initialization."""
        result = BacktestResult(
            initial_balance=100000,
            final_balance=110000,
            total_return=0.1,
            sharpe_ratio=1.5,
        )

        assert result.initial_balance == 100000
        assert result.final_balance == 110000
        assert result.total_return == 0.1
        assert result.sharpe_ratio == 1.5

    def test_to_dict(self):
        """Test conversion to dictionary."""
        result = BacktestResult(
            initial_balance=100000,
            final_balance=110000,
            total_return=0.1,
        )

        data = result.to_dict()

        assert isinstance(data, dict)
        assert data["initial_balance"] == 100000
        assert data["final_balance"] == 110000
        assert data["total_return"] == 0.1


@pytest.mark.skipif(
    not LANGGRAPH_ADAPTER_AVAILABLE, reason="LangGraph adapter not available"
)
class TestLangGraphBacktester:
    """Test cases for LangGraphBacktester."""

    @pytest.fixture
    def mock_config(self):
        """Create mock configuration."""
        return BacktestConfig(
            initial_balance=100000,
            commission_rate=0.001,
        )

    @pytest.fixture
    def backtester(self, mock_config):
        """Create backtester instance."""
        return LangGraphBacktester(config=mock_config)

    def test_initialization(self, backtester, mock_config):
        """Test backtester initialization."""
        assert backtester.config == mock_config
        assert isinstance(backtester.nodes, dict)
        assert isinstance(backtester.edges, list)
        assert backtester.state is None

    def test_add_node(self, backtester):
        """Test adding a node."""
        mock_node = Mock()
        backtester.add_node("test_node", mock_node)

        assert "test_node" in backtester.nodes
        assert backtester.nodes["test_node"] == mock_node

    def test_add_edge(self, backtester):
        """Test adding an edge."""
        backtester.add_edge("node1", "node2")

        assert ("node1", "node2") in backtester.edges

    def test_remove_node(self, backtester):
        """Test removing a node."""
        mock_node = Mock()
        backtester.add_node("test_node", mock_node)
        backtester.remove_node("test_node")

        assert "test_node" not in backtester.nodes


class TestLangGraphExceptions:
    """Test cases for LangGraph adapter exceptions."""

    def test_agent_execution_error(self):
        """Test AgentExecutionError."""
        error = AgentExecutionError("Agent failed")
        assert str(error) == "Agent failed"

    def test_timeout_error(self):
        """Test TimeoutError."""
        error = TimeoutError("Execution timed out")
        assert str(error) == "Execution timed out"

    def test_state_validation_error(self):
        """Test StateValidationError."""
        error = StateValidationError("Invalid state")
        assert str(error) == "Invalid state"

    def test_signal_conversion_error(self):
        """Test SignalConversionError."""
        error = SignalConversionError("Conversion failed")
        assert str(error) == "Conversion failed"

    def test_position_error(self):
        """Test PositionError."""
        error = PositionError("Position error")
        assert str(error) == "Position error"

    def test_deterministic_rule_error(self):
        """Test DeterministicRuleError."""
        error = DeterministicRuleError("Rule error")
        assert str(error) == "Rule error"

    def test_scenario_load_error(self):
        """Test ScenarioLoadError."""
        error = ScenarioLoadError("Load error")
        assert str(error) == "Load error"
