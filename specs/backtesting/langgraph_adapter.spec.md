# LangGraph Adapter Specification

## Overview
Defines integration between LangGraph agents and the backtesting engine, enabling agent-based strategy backtesting with deterministic execution.

## Core Components

### LangGraphBacktestAdapter
```python
from typing import Dict, Any, Optional, List, Callable
import pandas as pd
from dataclasses import dataclass, field
from datetime import datetime

class LangGraphBacktestAdapter:
    """Adapter for running LangGraph agents in backtesting environment."""
    
    def __init__(self, agent_graph: Any, config: Dict[str, Any] = None):
        """
        Initialize adapter with LangGraph agent.
        
        Args:
            agent_graph: LangGraph StateGraph or CompiledGraph
            config: Configuration for adapter behavior
        """
        self.agent_graph = agent_graph
        self.config = config or {}
        self.reasoning_log: List[Dict[str, Any]] = []
    
    def create_strategy(self, initial_state: Optional[Dict[str, Any]] = None) -> 'AgentStrategy':
        """Create backtestable strategy from LangGraph agent."""
        pass
    
    def set_deterministic_llm(self, deterministic_responses: Dict[str, Any]):
        """Configure deterministic LLM responses for reproducible backtests."""
        pass
    
    def get_reasoning_log(self) -> List[Dict[str, Any]]:
        """Get captured agent reasoning during backtest."""
        pass
    
    def reset_state(self):
        """Reset adapter state for new backtest."""
        pass
```

### AgentStrategy
```python
class AgentStrategy:
    """Strategy implementation that wraps LangGraph agent for backtesting."""
    
    def __init__(self, adapter: LangGraphBacktestAdapter, 
                 initial_state: Dict[str, Any] = None):
        """Initialize strategy with adapter and initial state."""
        self.adapter = adapter
        self.current_state = initial_state or {}
        self.position_manager = PositionManager()
    
    def init(self, initial_cash: float, positions: Dict[str, int] = None):
        """Initialize strategy with starting capital and positions."""
        pass
    
    def next(self, bar: Dict[str, Any]) -> Optional[str]:
        """Process next bar and return trading signal."""
        pass
    
    def get_current_positions(self) -> Dict[str, int]:
        """Get current positions."""
        pass
    
    def get_current_cash(self) -> float:
        """Get current cash balance."""
        pass
```

### AgentState (Dataclass)
```python
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
```

### DeterministicLLMWrapper
```python
class DeterministicLLMWrapper:
    """Wraps LLM calls to provide deterministic responses for reproducible backtests."""
    
    def __init__(self, response_rules: Dict[str, Any] = None):
        """
        Initialize with deterministic response rules.
        
        Args:
            response_rules: Dict mapping conditions to responses
        """
        self.response_rules = response_rules or {}
        self.call_history: List[Dict[str, Any]] = []
    
    def __call__(self, prompt: str, **kwargs) -> str:
        """Generate deterministic response based on rules or history."""
        pass
    
    def add_rule(self, condition: str, response: str):
        """Add deterministic rule."""
        pass
    
    def load_scenario(self, scenario_path: str):
        """Load pre-defined deterministic scenario."""
        pass
    
    def save_scenario(self, scenario_path: str):
        """Save current scenario for future use."""
        pass
```

## State Conversion

### Bar to AgentState
```python
def bar_to_agent_state(bar: Dict[str, Any], current_state: AgentState, 
                       position_manager: 'PositionManager') -> AgentState:
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
    new_state.current_bar = bar
    new_state.timestamp = bar.get('timestamp', datetime.now())
    new_state.step_count = current_state.step_count + 1
    
    # Update portfolio state
    new_state.positions = position_manager.get_positions()
    new_state.cash = position_manager.get_cash()
    new_state.equity = position_manager.calculate_equity(bar.get('close', 0))
    
    return new_state
```

### AgentState to Trading Signal
```python
def agent_state_to_signal(agent_state: AgentState) -> Optional[str]:
    """
    Convert AgentState backtest decision to trading signal.
    
    Args:
        agent_state: Agent state after processing
    
    Returns:
        Optional[str]: Trading signal ('buy', 'sell', 'hold', or None)
    """
    signal = agent_state.signal
    
    # Validate signal
    if signal not in ['buy', 'sell', 'hold']:
        return None
    
    # Validate quantity
    if agent_state.quantity <= 0:
        return None
    
    # Additional validation based on position limits
    if signal == 'buy' and agent_state.cash <= 0:
        return None
    
    if signal == 'sell':
        symbol = agent_state.current_bar.get('symbol')
        current_position = agent_state.positions.get(symbol, 0)
        if current_position <= 0:
            return None
    
    return signal
```

## Reasoning Log Capture

### Log Structure
```python
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
```

### Logging Integration
```python
def capture_reasoning(agent_state: AgentState, execution_time: float):
    """Capture agent reasoning and decisions for analysis."""
    entry = ReasoningEntry(
        timestamp=agent_state.timestamp,
        step=agent_state.step_count,
        bar_data=agent_state.current_bar.copy(),
        observations=agent_state.observations.copy(),
        reasoning=agent_state.reasoning.copy(),
        decision=agent_state.decisions[-1] if agent_state.decisions else None,
        signal=agent_state.signal,
        confidence=agent_state.signal_confidence,
        quantity=agent_state.quantity,
        execution_details=agent_state.order_details.copy(),
        execution_time_ms=execution_time
    )
    
    # Add to reasoning log
    return entry
```

## Agent Integration Patterns

### Standard Agent Template
```python
def create_standard_trading_agent() -> Any:
    """
    Create standard LangGraph agent with observe -> decide -> risk -> execute pattern.
    
    Returns:
        LangGraph StateGraph configured for trading
    """
    from langgraph.graph import StateGraph
    
    # Define the agent workflow
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("observe", observe_market)
    workflow.add_node("analyze", analyze_data)
    workflow.add_node("decide", make_decision)
    workflow.add_node("risk", assess_risk)
    workflow.add_node("execute", execute_trade)
    
    # Define edges
    workflow.set_entry_point("observe")
    workflow.add_edge("observe", "analyze")
    workflow.add_edge("analyze", "decide")
    workflow.add_edge("decide", "risk")
    workflow.add_edge("risk", "execute")
    workflow.add_edge("execute", "__end__")
    
    return workflow.compile()
```

### Node Implementation Examples
```python
def observe_market(state: AgentState) -> AgentState:
    """Observe market data and record observations."""
    bar = state.current_bar
    
    observations = []
    observations.append(f"Price: {bar.get('close', 'N/A')}")
    observations.append(f"Volume: {bar.get('volume', 'N/A')}")
    
    # Technical indicators would be calculated here
    # rsi = calculate_rsi(state.market_data)
    # observations.append(f"RSI: {rsi:.2f}")
    
    state.observations.extend(observations)
    return state

def analyze_data(state: AgentState) -> AgentState:
    """Analyze market data and generate insights."""
    reasoning = []
    
    # Example reasoning logic
    current_price = state.current_bar.get('close', 0)
    volume = state.current_bar.get('volume', 0)
    
    if volume > 0:
        reasoning.append("High volume indicates strong interest")
    else:
        reasoning.append("Low volume suggests weak conviction")
    
    state.reasoning.extend(reasoning)
    return state

def make_decision(state: AgentState) -> AgentState:
    """Make trading decision based on analysis."""
    # This would typically use LLM for decision making
    # For backtesting, we use deterministic rules
    
    price = state.current_bar.get('close', 0)
    current_position = state.positions.get(state.current_bar.get('symbol'), 0)
    
    # Simple rule-based decision for demonstration
    if current_position == 0 and price > 100:  # Simple buy condition
        state.signal = 'buy'
        state.quantity = 10
        state.signal_confidence = 0.7
    elif current_position > 0 and price < 90:  # Simple sell condition
        state.signal = 'sell'
        state.quantity = current_position
        state.signal_confidence = 0.8
    else:
        state.signal = 'hold'
        state.quantity = 0
        state.signal_confidence = 0.5
    
    state.decisions.append(f"Decision: {state.signal}")
    return state

def assess_risk(state: AgentState) -> AgentState:
    """Assess risk and adjust position sizing."""
    risk_assessment = {
        'portfolio_risk': 0.15,  # 15% max portfolio risk
        'position_risk': 0.05,  # 5% max position risk
        'correlation_risk': 0.02
    }
    
    state.risk_assessment = risk_assessment
    
    # Adjust quantity based on risk
    if state.signal == 'buy':
        max_position_value = state.equity * risk_assessment['position_risk']
        price = state.current_bar.get('close', 1)
        max_quantity = int(max_position_value / price)
        state.quantity = min(state.quantity, max_quantity)
    
    return state

def execute_trade(state: AgentState) -> AgentState:
    """Execute trade with order details."""
    if state.signal in ['buy', 'sell']:
        state.order_details = {
            'symbol': state.current_bar.get('symbol'),
            'side': state.signal,
            'quantity': state.quantity,
            'order_type': 'market',
            'timestamp': state.timestamp
        }
    
    return state
```

## Position Management

### PositionManager
```python
class PositionManager:
    """Manages positions and cash for backtesting."""
    
    def __init__(self, initial_cash: float = 100000.0):
        """Initialize with starting cash."""
        self.initial_cash = initial_cash
        self.cash = initial_cash
        self.positions: Dict[str, int] = {}
        self.trades: List[Dict[str, Any]] = []
    
    def update_position(self, symbol: str, quantity: int, price: float, 
                        commission: float = 0):
        """Update position after trade execution."""
        trade_value = quantity * price
        total_cost = trade_value + commission
        
        if quantity > 0:  # Buy
            if total_cost > self.cash:
                raise ValueError("Insufficient cash for trade")
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
        self.trades.append({
            'symbol': symbol,
            'quantity': quantity,
            'price': price,
            'commission': commission,
            'timestamp': datetime.now()
        })
    
    def calculate_equity(self, current_prices: Dict[str, float]) -> float:
        """Calculate total equity including unrealized P&L."""
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
```

## Error Handling

### Agent Errors
- `AgentExecutionError` for agent runtime failures
- `TimeoutError` for agent execution timeouts
- `StateValidationError` for invalid agent state

### Integration Errors
- `SignalConversionError` for signal conversion failures
- `PositionError` for position management errors
- `ConfigurationError` for adapter configuration issues

### Deterministic Execution
- `DeterministicRuleError` for rule evaluation failures
- `ScenarioLoadError` for scenario loading failures
- `ReproducibilityError` when deterministic behavior cannot be guaranteed

## Performance Requirements

- Agent execution time < 100ms per bar for simple agents
- Reasoning log storage < 1MB for 10K bars
- Position updates < 1ms per trade
- State conversion < 10ms per bar

## Dependencies
- langgraph >= 0.2.0
- langchain-core >= 0.3.0
- pandas >= 2.0.0
- pydantic >= 2.0.0
- typing extensions
