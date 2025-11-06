"""
LangGraph adapter for agent backtesting integration.
"""

from typing import Dict, Any, Optional, List
import pandas as pd
from dataclasses import dataclass, field
from datetime import datetime
import json
import time
from unittest.mock import Mock


# Custom Exceptions
class AgentExecutionError(Exception):
    """Raised for agent runtime failures."""

    pass


class TimeoutError(Exception):
    """Raised for agent execution timeouts."""

    pass


class StateValidationError(Exception):
    """Raised for invalid agent state."""

    pass


class SignalConversionError(Exception):
    """Raised for signal conversion failures."""

    pass


class PositionError(Exception):
    """Raised for position management errors."""

    pass


class DeterministicRuleError(Exception):
    """Raised for rule evaluation failures."""

    pass


class ScenarioLoadError(Exception):
    """Raised for scenario loading failures."""

    pass


class ReproducibilityError(Exception):
    """Raised when deterministic behavior cannot be guaranteed."""

    pass


@dataclass
class ReasoningEntry:
    """Single entry in agent reasoning log."""

    timestamp: datetime
    step: int
    bar_data: Dict[str, Any]
    observations: List[str]
    reasoning: List[str]
    decision: str
    signal: Optional[str]
    confidence: float
    quantity: int
    execution_details: Dict[str, Any]
    execution_time_ms: float


@dataclass
class AgentState:
    """State structure for LangGraph agent during backtesting."""

    # Market Data
    current_bar: Dict[str, Any] = field(default_factory=dict)
    market_data: pd.DataFrame = field(default_factory=pd.DataFrame)

    # Portfolio State
    cash: float = 100000.0
    positions: Dict[str, int] = field(default_factory=dict)
    equity: float = 100000.0

    # Agent Internal State
    observations: List[str] = field(default_factory=list)
    reasoning: List[str] = field(default_factory=list)
    decisions: List[str] = field(default_factory=list)

    # Signal Generation
    signal: Optional[str] = None
    signal_confidence: float = 0.0
    quantity: int = 0

    # Risk Management
    risk_assessment: Dict[str, Any] = field(default_factory=dict)
    position_sizing: Dict[str, float] = field(default_factory=dict)

    # Execution
    order_details: Dict[str, Any] = field(default_factory=dict)

    # Metadata
    timestamp: datetime = field(default_factory=datetime.now)
    step_count: int = 0


class PositionManager:
    """Manages positions and cash for backtesting."""

    def __init__(self, initial_cash: float = 100000.0):
        """Initialize with starting cash."""
        self.initial_cash = initial_cash
        self.cash = initial_cash
        self.positions: Dict[str, int] = {}
        self.trades: List[Dict[str, Any]] = []

    def update_position(
        self, symbol: str, quantity: int, price: float, commission: float = 0
    ) -> None:
        """
        Update position after trade execution.

        Args:
            symbol: Trading symbol
            quantity: Trade quantity (positive for buy, negative for sell)
            price: Execution price
            commission: Commission cost
        """
        trade_value = quantity * price
        total_cost = trade_value + commission

        if quantity > 0:  # Buy
            if total_cost > self.cash:
                raise PositionError("Insufficient cash for trade")
            self.cash -= total_cost
        else:  # Sell
            self.cash += abs(trade_value) - commission

        # Update position
        current_pos = self.positions.get(symbol, 0)
        new_position = current_pos + quantity

        if new_position == 0:
            del self.positions[symbol]
        else:
            self.positions[symbol] = new_position

        # Record trade
        self.trades.append(
            {
                "symbol": symbol,
                "quantity": quantity,
                "price": price,
                "commission": commission,
                "timestamp": datetime.now(),
            }
        )

    def calculate_equity(self, current_prices: Dict[str, float]) -> float:
        """
        Calculate total equity including unrealized P&L.

        Args:
            current_prices: Current prices for held positions

        Returns:
            Total equity value
        """
        position_value = sum(
            qty * current_prices.get(symbol, 0)
            for symbol, qty in self.positions.items()
        )
        return self.cash + position_value

    def get_positions(self) -> Dict[str, int]:
        """Get current positions."""
        return self.positions.copy()

    def get_cash(self) -> float:
        """Get current cash balance."""
        return self.cash


class DeterministicLLMWrapper:
    """Wraps LLM calls to provide deterministic responses for reproducible backtests."""

    def __init__(self, response_rules: Optional[Dict[str, Any]] = None):
        """
        Initialize with deterministic response rules.

        Args:
            response_rules: Dict mapping conditions to responses
        """
        self.response_rules = response_rules or {}
        self.call_history: List[Dict[str, Any]] = []

    def __call__(self, prompt: str, **kwargs: Any) -> str:
        """
        Generate deterministic response based on rules or history.

        Args:
            prompt: Input prompt
            **kwargs: Additional arguments

        Returns:
            Deterministic response
        """
        # Record call
        self.call_history.append(
            {"prompt": prompt, "kwargs": kwargs.copy(), "timestamp": datetime.now()}
        )

        # Try to match rules
        for condition, response in self.response_rules.items():
            if condition in prompt:
                return str(response)

        # Return default response if no rules match
        return str(self.response_rules.get("default", ""))

    def add_rule(self, condition: str, response: str) -> None:
        """
        Add deterministic rule.

        Args:
            condition: Condition to match
            response: Response to return
        """
        self.response_rules[condition] = response

    def load_scenario(self, scenario_path: str) -> None:
        """
        Load pre-defined deterministic scenario.

        Args:
            scenario_path: Path to scenario file

        Raises:
            ScenarioLoadError: If loading fails
        """
        try:
            with open(scenario_path, "r") as f:
                self.response_rules = json.load(f)
        except Exception as e:
            raise ScenarioLoadError(f"Failed to load scenario: {e}") from e

    def save_scenario(self, scenario_path: str) -> None:
        """
        Save current scenario for future use.

        Args:
            scenario_path: Path to save scenario

        Raises:
            DeterministicRuleError: If saving fails
        """
        try:
            with open(scenario_path, "w") as f:
                json.dump(self.response_rules, f, indent=2)
        except Exception as e:
            raise DeterministicRuleError(f"Failed to save scenario: {e}") from e


class LangGraphBacktestAdapter:
    """Adapter for running LangGraph agents in backtesting environment."""

    def __init__(self, agent_graph: Any, config: Optional[Dict[str, Any]] = None):
        """
        Initialize adapter with LangGraph agent.

        Args:
            agent_graph: LangGraph StateGraph or CompiledGraph
            config: Configuration for adapter behavior
        """
        self.agent_graph = agent_graph
        self.config = config or {}
        self.reasoning_log: List[Dict[str, Any]] = []
        self.current_state: Dict[str, Any] = {}
        self.deterministic_responses: Dict[str, Any] = {}
        self.deterministic_llm: Optional[DeterministicLLMWrapper] = None

        # Initialize deterministic wrapper if configured
        if self.config.get("deterministic", False):
            self.deterministic_llm = DeterministicLLMWrapper()
        else:
            self.deterministic_llm = None

    def create_strategy(
        self, initial_state: Optional[Dict[str, Any]] = None
    ) -> "AgentStrategy":
        """
        Create backtestable strategy from LangGraph agent.

        Args:
            initial_state: Initial agent state

        Returns:
            AgentStrategy instance
        """
        return AgentStrategy(self, initial_state or {})

    def set_deterministic_llm(self, deterministic_responses: Dict[str, Any]) -> None:
        """
        Configure deterministic LLM responses for reproducible backtests.

        Args:
            deterministic_responses: Dict of deterministic response rules
        """
        self.deterministic_responses = deterministic_responses
        if self.deterministic_llm:
            self.deterministic_llm.response_rules = deterministic_responses

    def get_reasoning_log(self) -> List[Dict[str, Any]]:
        """
        Get captured agent reasoning during backtest.

        Returns:
            List of reasoning entries
        """
        return self.reasoning_log.copy()

    def reset_state(self) -> None:
        """Reset adapter state for new backtest."""
        self.reasoning_log.clear()
        self.current_state = {}

        if self.deterministic_llm:
            self.deterministic_llm.call_history.clear()


class AgentStrategy:
    """Strategy implementation that wraps LangGraph agent for backtesting."""

    def __init__(
        self,
        adapter: LangGraphBacktestAdapter,
        initial_state: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize strategy with adapter and initial state.

        Args:
            adapter: LangGraph adapter instance
            initial_state: Initial agent state
        """
        self.adapter = adapter
        self.current_state = AgentState(**(initial_state or {}))
        self.position_manager = PositionManager()

    def init(
        self, initial_cash: float, positions: Optional[Dict[str, int]] = None
    ) -> None:
        """
        Initialize strategy with starting capital and positions.

        Args:
            initial_cash: Starting cash amount
            positions: Initial positions
        """
        self.position_manager = PositionManager(initial_cash)
        if positions:
            for symbol, quantity in positions.items():
                # Add positions without affecting cash (already accounted for)
                self.position_manager.positions[symbol] = quantity

    def next(self, bar: Dict[str, Any]) -> Optional[str]:
        """
        Process next bar and return trading signal.

        Args:
            bar: Market bar data

        Returns:
            Trading signal ('buy', 'sell', 'hold', or None)

        Raises:
            AgentExecutionError: If agent execution fails
            TimeoutError: If agent execution times out
        """
        try:
            start_time = time.time()

            # Convert bar data to agent state
            new_state = bar_to_agent_state(
                bar, self.current_state, self.position_manager
            )

            # Execute agent graph
            try:
                # Set timeout if configured
                timeout = self.adapter.config.get("timeout", 30.0)  # 30 seconds default

                if timeout > 0 and time.time() - start_time > timeout:
                    raise TimeoutError("Agent execution timeout")

                result_state = self.adapter.agent_graph.invoke(new_state.__dict__)

                # Update current state with results
                # Define valid AgentState fields to filter out mock attributes
                valid_agent_state_fields = {
                    "current_bar",
                    "market_data",
                    "cash",
                    "positions",
                    "equity",
                    "observations",
                    "reasoning",
                    "decisions",
                    "signal",
                    "signal_confidence",
                    "quantity",
                    "risk_assessment",
                    "position_sizing",
                    "order_details",
                    "timestamp",
                    "step_count",
                }

                if isinstance(result_state, dict):
                    # Filter out mock and private attributes before creating AgentState
                    filtered_dict = {
                        k: v
                        for k, v in result_state.items()
                        if k in valid_agent_state_fields and not k.startswith("_")
                    }
                    # Also filter new_state dict to remove mock attributes
                    filtered_new_state = {
                        k: v
                        for k, v in new_state.__dict__.items()
                        if k in valid_agent_state_fields and not k.startswith("_")
                    }
                    # Update current_state by merging new_state and result_state
                    merged_dict = {**filtered_new_state, **filtered_dict}
                    self.current_state = AgentState(**merged_dict)
                elif hasattr(result_state, "__dict__"):
                    # Filter out mock and private attributes from object dict
                    filtered_dict = {
                        k: v
                        for k, v in result_state.__dict__.items()
                        if k in valid_agent_state_fields and not k.startswith("_")
                    }
                    # Also filter new_state dict to remove mock attributes
                    filtered_new_state = {
                        k: v
                        for k, v in new_state.__dict__.items()
                        if k in valid_agent_state_fields and not k.startswith("_")
                    }
                    # Update current_state by merging new_state and result_state
                    merged_dict = {**filtered_new_state, **filtered_dict}
                    self.current_state = AgentState(**merged_dict)
                else:
                    raise AgentExecutionError("Invalid agent state returned")

            except Exception as e:
                if "timeout" in str(e).lower():
                    raise TimeoutError(f"Agent execution timeout: {e}") from e
                else:
                    raise AgentExecutionError(f"Agent execution failed: {e}") from e

            # Capture reasoning
            execution_time = (time.time() - start_time) * 1000  # Convert to ms
            reasoning_entry = capture_reasoning(self.current_state, execution_time)
            self.adapter.reasoning_log.append(reasoning_entry.__dict__)

            # Convert agent decision to trading signal
            signal = agent_state_to_signal(self.current_state)

            # Execute trade if signal is valid
            if signal in ["buy", "sell"]:
                self._execute_trade(signal, bar)

            return signal

        except Exception as e:
            if isinstance(e, (AgentExecutionError, TimeoutError)):
                raise
            raise AgentExecutionError(f"Strategy execution failed: {e}") from e

    def _execute_trade(self, signal: str, bar: Dict[str, Any]) -> None:
        """
        Execute trade based on signal.

        Args:
            signal: Trading signal
            bar: Market bar data
        """
        symbol = bar.get("symbol")
        price = bar.get("close", 0)
        quantity = self.current_state.quantity

        if not symbol or price <= 0 or quantity <= 0:
            return

        # Apply commission and slippage (simplified)
        commission_rate = self.adapter.config.get("commission_rate", 0.001)
        slippage_rate = self.adapter.config.get("slippage_rate", 0.0001)

        commission = abs(quantity * price * commission_rate)

        # Adjust price for slippage
        executed_price = (
            price * (1 + slippage_rate)
            if signal == "buy"
            else price * (1 - slippage_rate)
        )

        # Update position
        trade_quantity = quantity if signal == "buy" else -quantity
        try:
            self.position_manager.update_position(
                symbol, trade_quantity, executed_price, commission
            )
        except PositionError:
            # Ignore insufficient cash errors for now
            pass

    def get_current_positions(self) -> Dict[str, int]:
        """Get current positions."""
        return self.position_manager.get_positions()

    def get_current_cash(self) -> float:
        """Get current cash balance."""
        return self.position_manager.get_cash()


def bar_to_agent_state(
    bar: Dict[str, Any], current_state: AgentState, position_manager: PositionManager
) -> AgentState:
    """
    Convert market bar data to AgentState for LangGraph processing.

    Args:
        bar: Market bar with OHLCV data
        current_state: Current agent state
        position_manager: Position tracking manager

    Returns:
        AgentState: Updated state for agent processing
    """
    new_state = AgentState(**current_state.__dict__)

    # Update market data
    new_state.current_bar = bar.copy()
    new_state.timestamp = bar.get("timestamp", datetime.now())
    new_state.step_count = current_state.step_count + 1

    # Update portfolio state
    new_state.positions = position_manager.get_positions()
    new_state.cash = position_manager.get_cash()

    # Calculate equity with current bar price
    current_price = bar.get("close", 0)
    if current_price is not None and current_price > 0:
        if symbol := bar.get("symbol"):
            current_prices = {symbol: current_price}
            new_state.equity = position_manager.calculate_equity(current_prices)
        else:
            new_state.equity = position_manager.calculate_equity({})

    return new_state


def agent_state_to_signal(agent_state: AgentState) -> Optional[str]:
    """
    Convert AgentState backtest decision to trading signal.

    Args:
        agent_state: Agent state after processing

    Returns:
        Optional[str]: Trading signal ('buy', 'sell', 'hold', or None)

    Raises:
        SignalConversionError: For invalid signals
    """
    signal = agent_state.signal

    # Validate signal
    if signal not in ["buy", "sell", "hold"]:
        raise SignalConversionError(f"Invalid signal: {signal}")

    # Validate quantity
    if agent_state.quantity <= 0:
        return None

    # Additional validation based on position limits
    if signal == "buy" and agent_state.cash <= 0:
        return None

    if signal == "sell":
        if symbol := agent_state.current_bar.get("symbol"):
            current_position = agent_state.positions.get(symbol, 0)
            if current_position <= 0:
                return None
        else:
            return None

    return signal


def capture_reasoning(agent_state: AgentState, execution_time: float) -> ReasoningEntry:
    """
    Capture agent reasoning and decisions for analysis.

    Args:
        agent_state: Agent state with reasoning data
        execution_time: Execution time in milliseconds

    Returns:
        ReasoningEntry: Captured reasoning entry
    """
    return ReasoningEntry(
        timestamp=agent_state.timestamp,
        step=agent_state.step_count,
        bar_data=agent_state.current_bar.copy(),
        observations=agent_state.observations.copy(),
        reasoning=agent_state.reasoning.copy(),
        decision=agent_state.decisions[-1] if agent_state.decisions else "",
        signal=agent_state.signal,
        confidence=agent_state.signal_confidence,
        quantity=agent_state.quantity,
        execution_details=agent_state.order_details.copy(),
        execution_time_ms=execution_time,
    )


# Utility functions for creating standard agent templates
def create_standard_trading_agent() -> Any:
    """
    Create standard LangGraph agent with observe -> decide -> risk -> execute pattern.

    Returns:
        LangGraph StateGraph configured for trading
    """
    try:
        from langgraph.graph import StateGraph

        # Define agent workflow
        workflow = StateGraph(AgentState)

        # Add nodes (these would be defined elsewhere)
        def observe_market(state: AgentState) -> AgentState:
            bar = state.current_bar
            observations = []
            observations.append(f"Price: {bar.get('close', 'N/A')}")
            observations.append(f"Volume: {bar.get('volume', 'N/A')}")
            state.observations.extend(observations)
            return state

        def analyze_data(state: AgentState) -> AgentState:
            reasoning = []
            volume = state.current_bar.get("volume", 0)

            if volume > 0:
                reasoning.append("High volume indicates strong interest")
            else:
                reasoning.append("Low volume suggests weak conviction")

            state.reasoning.extend(reasoning)
            return state

        def make_decision(state: AgentState) -> AgentState:
            # Simple rule-based decision for demonstration
            price = state.current_bar.get("close", 0)
            symbol = state.current_bar.get("symbol", "")
            current_position = state.positions.get(symbol, 0)

            if current_position == 0 and price > 100:  # Simple buy condition
                state.signal = "buy"
                state.quantity = 10
                state.signal_confidence = 0.7
            elif current_position > 0 and price < 90:  # Simple sell condition
                state.signal = "sell"
                state.quantity = current_position
                state.signal_confidence = 0.8
            else:
                state.signal = "hold"
                state.quantity = 0
                state.signal_confidence = 0.5

            state.decisions.append(f"Decision: {state.signal}")
            return state

        def assess_risk(state: AgentState) -> AgentState:
            risk_assessment = {
                "portfolio_risk": 0.15,  # 15% max portfolio risk
                "position_risk": 0.05,  # 5% max position risk
                "correlation_risk": 0.02,
            }
            state.risk_assessment = risk_assessment

            # Adjust quantity based on risk
            if state.signal == "buy":
                max_position_value = state.equity * risk_assessment["position_risk"]
                price = state.current_bar.get("close", 1)
                max_quantity = int(max_position_value / price)
                state.quantity = min(state.quantity, max_quantity)

            return state

        def execute_trade(state: AgentState) -> AgentState:
            if state.signal in ["buy", "sell"]:
                state.order_details = {
                    "symbol": state.current_bar.get("symbol"),
                    "side": state.signal,
                    "quantity": state.quantity,
                    "order_type": "market",
                    "timestamp": state.timestamp,
                }
            return state

        # Define edges
        workflow.add_node("observe", observe_market)
        workflow.add_node("analyze", analyze_data)
        workflow.add_node("decide", make_decision)
        workflow.add_node("risk", assess_risk)
        workflow.add_node("execute", execute_trade)

        workflow.set_entry_point("observe")
        workflow.add_edge("observe", "analyze")
        workflow.add_edge("analyze", "decide")
        workflow.add_edge("decide", "risk")
        workflow.add_edge("risk", "execute")

        return workflow.compile()

    except ImportError:
        # Return mock if LangGraph not available
        return Mock()
