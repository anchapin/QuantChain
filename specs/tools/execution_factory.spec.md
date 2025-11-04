### Function: `create_execution_interface`

**Description:** Factory function to create the appropriate trading execution interface based on configuration settings. Supports both Alpaca (live/paper) and standalone paper trading modes.

**Signature:** `create_execution_interface(config: QuantChainConfig) -> TradingExecutionInterface`

**Parameters:**
- `config`: QuantChainConfig object containing trading configuration
  - `config.get("trading.default_broker")`: Broker to use ("alpaca", "paper")
  - `config.get("trading.paper_trading")`: Whether to use paper trading mode
  - `config.get_api_key("alpaca")`: Alpaca API key (when using Alpaca)
  - `config.get_api_key("alpaca_secret")`: Alpaca API secret (when using Alpaca)

**Returns:** TradingExecutionInterface implementation
  - `AlpacaExecutionConnector` when broker="alpaca" (with paper_trading flag)
  - `PaperTradingExecutor` when broker="paper"

**Raises:**
- `ConfigurationError`: When broker configuration is invalid
- `AuthenticationError`: When API keys are missing for live brokers
- `ValueError`: When unsupported broker is specified

### Configuration Examples

```python
# Alpaca paper trading (default)
config = {
    "trading": {
        "default_broker": "alpaca",
        "paper_trading": True
    }
}
executor = create_execution_interface(config)  # Returns AlpacaExecutionConnector(use_paper=True)

# Alpaca live trading
config = {
    "trading": {
        "default_broker": "alpaca",
        "paper_trading": False
    }
}
executor = create_execution_interface(config)  # Returns AlpacaExecutionConnector(use_paper=False)

# Standalone paper trading
config = {
    "trading": {
        "default_broker": "paper",
        "paper_trading": True  # Ignored for paper broker
    }
}
executor = create_execution_interface(config)  # Returns PaperTradingExecutor()
```

### Error Handling

**Invalid Broker:**
```python
config = {"trading": {"default_broker": "unsupported_broker"}}
# Raises: ConfigurationError("Unsupported broker: unsupported_broker")
```

**Missing API Keys for Live Trading:**
```python
config = {
    "trading": {
        "default_broker": "alpaca",
        "paper_trading": False
    }
}
# With no ALPACA_API_KEY env var
# Raises: AuthenticationError("Alpaca API key required for live trading")
```

### Integration Points

- **Config System**: Reads from `quantchain.core.config.QuantChainConfig`
- **API Keys**: Retrieves keys via `config.get_api_key()`
- **Error Types**: Uses standard QuantChain error classes
- **Interface**: Returns `TradingExecutionInterface` for polymorphism

### Testing Requirements

- Test all broker configurations (alpaca paper/live, paper)
- Test error conditions (missing keys, invalid broker)
- Test configuration overrides from environment variables
- Mock API key retrieval for security
- Integration tests with full config system</content>
</xai:function_call: create_file>
<parameter name="path">/home/anchapin/projects/QuantChain/specs/tools/execution_factory.spec.md
