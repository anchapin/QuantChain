# FinRL Adapter Specification

## Overview

The FinRL Adapter will integrate QuantChain's backtesting engine with the FinRL environment, allowing reinforcement learning-based agents to be tested within QuantChain. This adapter acts as a bridge between QuantChain's market friction modeling and FinRL's gym-style environment interface.

## Architecture

### Core Components

1. **FinRLAdapter Class**: Main adapter implementing gym-style environment interface
2. **Observation Space Handler**: Converts QuantChain market data to FinRL observations
3. **Action Space Handler**: Maps FinRL actions to QuantChain trade executions
4. **Reward Calculator**: Computes rewards based on QuantChain performance metrics
5. **Market Friction Integration**: Applies QuantChain's friction models to FinRL environment

## Interface Specification

### Class Definition

```python
class FinRLAdapter(gym.Env):
    """Adapter for integrating FinRL environments with QuantChain backtesting"""
    
    def __init__(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        initial_balance: float = 100000,
        market_friction_config: Optional[Dict] = None,
        **kwargs
    )
```

### Required Methods

#### reset()
- **Purpose**: Reset environment to initial state
- **Returns**: Initial observation
- **Implementation**:
  - Reset QuantChain backtester
  - Clear positions and balance
  - Return initial market observation

#### step(action)
- **Purpose**: Execute action and advance environment
- **Parameters**: 
  - `action`: Trading action (buy/sell/hold with amount)
- **Returns**: Tuple of (observation, reward, done, info)
- **Implementation**:
  - Convert FinRL action to QuantChain order
  - Apply market frictions (slippage, latency, fees)
  - Execute trade via QuantChain engine
  - Calculate reward based on performance
  - Return updated state

#### get_observation()
- **Purpose**: Get current market state as observation
- **Returns**: Numpy array of market data
- **Implementation**:
  - Extract price data, indicators, portfolio state
  - Format for FinRL agent input

#### get_reward()
- **Purpose**: Calculate reward for current step
- **Returns**: Float reward value
- **Implementation**:
  - Use QuantChain performance metrics
  - Consider risk-adjusted returns
  - Account for transaction costs

### Data Format Specifications

#### Observation Space
```
Shape: (n_features,)
Features:
- [0:4]: OHLCV data (open, high, low, close, volume)
- [4:10]: Technical indicators (RSI, MACD, Bollinger Bands, etc.)
- [10:15]: Portfolio state (cash, positions, PnL, etc.)
- [15:]: Additional features (news sentiment, market regime, etc.)
```

#### Action Space
```
Type: Discrete(3) for simple actions OR Box for continuous
Actions:
- 0: Hold
- 1: Buy (with amount determined by strategy)
- 2: Sell (with amount determined by strategy)
```

## Integration Requirements

### Market Friction Integration
The adapter must seamlessly integrate with QuantChain's market friction module:
- Transaction costs from `MarketFrictionModel`
- Slippage simulation for order execution
- Latency modeling for LLM inference time
- Position sizing constraints

### Data Connector Compatibility
- Support for existing QuantChain data connectors
- Real-time and historical data handling
- Multi-timeframe support

### Performance Metrics Integration
- Leverage existing `PerformanceMetrics` module
- Provide FinRL-compatible reward calculations
- Support custom reward functions

## Usage Example

```python
from quantchain.backtesting import FinRLAdapter
from finrl.agents.stablebaselines3 import DRLAgent

# Create FinRL environment
env = FinRLAdapter(
    symbol="AAPL",
    start_date="2020-01-01",
    end_date="2023-12-31",
    initial_balance=100000,
    market_friction_config={
        "commission": 0.001,
        "slippage": 0.0005,
        "latency_ms": 50
    }
)

# Train RL agent
agent = DRLAgent(env)
model = agent.get_model("ppo")
trained_model = agent.train_model(model, total_timesteps=100000)

# Backtest
results = agent.evaluate(trained_model)
```

## Testing Requirements

### Unit Tests
- Test observation space formatting
- Test action execution with market frictions
- Test reward calculation accuracy
- Test environment reset functionality

### Integration Tests
- Test with actual market data
- Test with various FinRL agents
- Test market friction impact on results
- Test performance against pure QuantChain backtesting

### Performance Tests
- Benchmark environment step execution time
- Memory usage monitoring with large datasets
- Concurrency testing for multiple environments

## Dependencies

### Required Packages
- `finrl>=0.3.0` - Core FinRL library
- `gym>=0.21.0` - OpenAI Gym interface
- `numpy>=1.21.0` - Numerical operations
- `pandas>=1.3.0` - Data manipulation

### QuantChain Dependencies
- `quantchain.backtesting.engine` - Core backtesting engine
- `quantchain.backtesting.market_friction` - Friction models
- `quantchain.backtesting.performance_metrics` - Performance tracking
- `quantchain.connectors` - Data connectors

## Implementation Phases

### Phase 1: Core Adapter
- Implement basic gym interface
- Simple observation/action spaces
- Basic market integration

### Phase 2: Market Friction Integration
- Add comprehensive friction models
- Advanced observation features
- Custom reward functions

### Phase 3: Advanced Features
- Multi-asset support
- Custom risk metrics
- Advanced visualization

## Success Criteria

1. **Compatibility**: Works with standard FinRL agents
2. **Accuracy**: Produces same results as native QuantChain backtesting
3. **Performance**: Handles 1M+ data points efficiently
4. **Extensibility**: Supports custom observation/action spaces
5. **Documentation**: Comprehensive API documentation and examples

## Edge Cases to Handle

1. **Market Hours**: Handle pre/post market data correctly
2. **Corporate Actions**: Splits, dividends, mergers
3. **Illiquid Markets**: Handle low volume scenarios
4. **Data Gaps**: Missing data periods
5. **Extreme Volatility**: Circuit breakers, trading halts
