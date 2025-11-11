# FinRL Integration with QuantChain

This guide explains how to use QuantChain's FinRL adapter to test reinforcement learning agents within the QuantChain backtesting framework.

## Overview

The FinRL adapter provides a bridge between QuantChain's realistic backtesting engine and FinRL's reinforcement learning environment. This allows you to:

- Train RL agents with realistic market frictions (slippage, commission, latency)
- Use QuantChain's data connectors with FinRL agents
- Leverage QuantChain's performance metrics for RL evaluation
- Combine LLM-based strategies with RL approaches

## Quick Start

### Basic Usage

```python
from quantchain.backtesting import FinRLAdapter

# Create the environment
env = FinRLAdapter(
    symbol="AAPL",
    start_date="2020-01-01",
    end_date="2023-12-31",
    initial_balance=100000,
    data_connector="alpaca",
    market_friction_config={
        "commission": 0.001,
        "slippage": 0.0005,
        "latency_ms": 50
    }
)

# Reset environment
obs = env.reset()

# Execute actions
for i in range(1000):
    action = env.action_space.sample()  # Replace with your agent
    obs, reward, done, info = env.step(action)
    
    if done:
        break

# Get performance metrics
metrics = env.get_performance_metrics()
print(f"Total Return: {metrics['total_return']:.2%}")
print(f"Sharpe Ratio: {metrics['sharpe_ratio']:.2f}")
```

### Training with FinRL Agents

```python
from finrl.agents.stablebaselines3 import DRLAgent
from quantchain.backtesting import FinRLAdapter

# Create environment
env = FinRLAdapter(
    symbol="BTC/USD",
    start_date="2021-01-01",
    end_date="2022-12-31",
    initial_balance=100000,
    market_friction_config={
        "commission": 0.001,
        "slippage": 0.001,
        "latency_ms": 100  # Higher for crypto
    }
)

# Setup agent
agent = DRLAgent(env)

# Get model (PPO example)
model_ppo = agent.get_model("ppo")

# Train the agent
trained_ppo = agent.train_model(
    model=model_ppo,
    total_timesteps=100000,
    eval_env=env
)

# Evaluate performance
result = agent.evaluate(trained_ppo)
```

## Configuration Options

### Environment Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `symbol` | str | Required | Trading symbol (e.g., "AAPL", "BTC/USD") |
| `start_date` | str | Required | Backtest start date (YYYY-MM-DD) |
| `end_date` | str | Required | Backtest end date (YYYY-MM-DD) |
| `initial_balance` | float | 100000 | Starting portfolio balance |
| `data_connector` | str | "alpaca" | QuantChain data connector to use |
| `observation_features` | List[str] | None | Custom features for observation space |
| `reward_strategy` | str | "risk_adjusted_return" | Reward calculation method |

### Market Friction Configuration

```python
market_friction_config = {
    "commission": 0.001,      # Commission rate (0.1%)
    "slippage": 0.0005,       # Slippage rate (0.05%)
    "latency_ms": 50,         # Simulated latency in milliseconds
    "min_order_size": 0.01    # Minimum order size
}
```

### Observation Features

Default observation features include:
- Market data: OHLCV
- Technical indicators: RSI, MACD, Bollinger Bands
- Portfolio state: balance, position, P&L
- Custom features can be added as needed

```python
custom_features = [
    'open', 'high', 'low', 'close', 'volume',
    'rsi', 'macd',
    'balance', 'position', 'total_value',
    'pnl_ratio'
]

env = FinRLAdapter(
    symbol="SPY",
    start_date="2020-01-01",
    end_date="2023-12-31",
    observation_features=custom_features
)
```

## Reward Strategies

### Available Strategies

1. **Simple Return** (`"simple_return"`):
   - Basic percentage return
   - Simple and intuitive

2. **Risk-Adjusted Return** (`"risk_adjusted_return"`):
   - Sharpe ratio-like reward
   - Balances return and volatility
   - Default strategy

3. **Log Return** (`"log_return"`):
   - Logarithmic returns
   - Better for continuous compounding

### Custom Reward Function

You can implement custom reward logic by extending the adapter:

```python
class CustomFinRLAdapter(FinRLAdapter):
    def _calculate_reward(self):
        # Custom reward calculation
        base_reward = super()._calculate_reward()
        
        # Add custom logic
        if self.position > 0 and self.market_data.iloc[self.current_step]['rsi'] < 30:
            # Bonus for contrarian positions
            base_reward += 0.01
            
        return base_reward
```

## Advanced Usage

### Multi-Asset Environment

```python
class MultiAssetFinRLAdapter:
    def __init__(self, symbols, **kwargs):
        self.environments = {
            symbol: FinRLAdapter(symbol=symbol, **kwargs)
            for symbol in symbols
        }
        
    def reset(self):
        observations = {}
        for symbol, env in self.environments.items():
            observations[symbol] = env.reset()
        return observations
```

### Custom Data Connectors

```python
# Use custom connector with specific configuration
env = FinRLAdapter(
    symbol="ETH/USD",
    start_date="2021-01-01",
    end_date="2022-12-31",
    data_connector="ccxt",
    connector_kwargs={
        "exchange": "binance",
        "timeframe": "1h",
        "limit": 1000
    }
)
```

### Integration with LLM Agents

```python
from quantchain.agents import LLMAgent
from quantchain.backtesting import FinRLAdapter

# Create environment
env = FinRLAdapter(
    symbol="TSLA",
    start_date="2020-01-01",
    end_date="2023-12-31"
)

# Create hybrid agent
class HybridAgent:
    def __init__(self, rl_model, llm_agent):
        self.rl_model = rl_model
        self.llm_agent = llm_agent
        
    def predict(self, observation):
        # Get RL prediction
        rl_action, _ = self.rl_model.predict(observation)
        
        # Get LLM recommendation
        llm_recommendation = self.llm_agent.analyze_market(observation)
        
        # Combine predictions
        if llm_recommendation["confidence"] > 0.8:
            return llm_recommendation["action"]
        else:
            return rl_action
```

## Performance Optimization

### Vectorized Environments

```python
from stable_baselines3.common.vec_env import SubprocVecEnv

def make_env(symbol, rank):
    def _init():
        env = FinRLAdapter(
            symbol=symbol,
            start_date="2020-01-01",
            end_date="2023-12-31"
        )
        env.seed(rank)
        return env
    return _init

# Create vectorized environment
n_envs = 4
env = SubprocVecEnv([make_env("AAPL", i) for i in range(n_envs)])
```

### Caching Data

```python
import pickle

# Cache expensive data fetches
cache_file = "market_data_cache.pkl"

try:
    with open(cache_file, 'rb') as f:
        cached_data = pickle.load(f)
    env.market_data = cached_data
except FileNotFoundError:
    # Fetch and cache data
    env._setup_data_connector("alpaca")
    with open(cache_file, 'wb') as f:
        pickle.dump(env.market_data, f)
```

## Best Practices

### 1. Data Preparation
- Use sufficient historical data (at least 2 years)
- Ensure data quality and handle missing values
- Consider including dividend and corporate action data

### 2. Market Friction Modeling
- Use realistic commission rates
- Model slippage based on volume and volatility
- Include latency for your specific LLM/inference setup

### 3. Training Strategy
- Use walk-forward optimization for robustness
- Include out-of-sample testing
- Monitor for overfitting

### 4. Risk Management
- Implement position sizing limits
- Use stop-loss mechanisms
- Monitor maximum drawdown

## Troubleshooting

### Common Issues

1. **Data Fetching Errors**
   ```
   Solution: Check connector configuration and API keys
   ```

2. **Memory Issues with Large Datasets**
   ```
   Solution: Use smaller date ranges or implement batching
   ```

3. **Slow Training**
   ```
   Solution: Use vectorized environments and GPU acceleration
   ```

4. **Unrealistic Performance**
   ```
   Solution: Check market friction parameters and ensure they're realistic
   ```

### Debug Mode

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

env = FinRLAdapter(
    symbol="SPY",
    start_date="2020-01-01",
    end_date="2020-12-31",
    debug=True
)
```

## Examples

### Example 1: Simple Momentum Strategy

```python
class MomentumAgent:
    def __init__(self, lookback=20):
        self.lookback = lookback
        
    def predict(self, observation):
        # Extract recent prices from observation
        prices = observation[:self.lookback]
        
        # Calculate momentum
        momentum = (prices[-1] - prices[0]) / prices[0]
        
        if momentum > 0.02:
            return [1, 0.5]  # Buy with 50% of balance
        elif momentum < -0.02:
            return [2, 0.5]  # Sell 50% of position
        else:
            return [0, 0]    # Hold
```

### Example 2: Mean Reversion Strategy

```python
class MeanReversionAgent:
    def __init__(self, window=20, threshold=2):
        self.window = window
        self.threshold = threshold
        
    def predict(self, observation):
        # Extract RSI from observation
        rsi_index = observation_features.index('rsi')
        rsi = observation[rsi_index]
        
        if rsi > 70:
            return [2, 0.3]  # Overbought - sell
        elif rsi < 30:
            return [1, 0.3]  # Oversold - buy
        else:
            return [0, 0]    # Hold
```

## References

- [FinRL Documentation](https://github.com/AI4Finance-Foundation/FinRL)
- [QuantChain Backtesting Guide](backtesting.md)
- [OpenAI Gym Documentation](https://gym.openai.com/docs/)
