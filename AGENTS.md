# Agent & Component Development Guide (AGENTS.md)

## 1. Core Principle: Test-Driven and Spec-Driven Development

Welcome to QuantChain! To ensure the reliability and robustness of this financial framework, all contributions **must** follow a Test-Driven Development (TDD) or Spec-Driven Development (SDD) approach. This means that for any new feature, tool, or agent, a corresponding test or specification must be written *before* the implementation code. This ensures clarity of purpose, correctness, and makes future maintenance easier.

Our testing framework of choice is `pytest`.

## 2. Workflow for New Components (Tools, Data Connectors, etc.)

Components are the building blocks of our agents, as defined in the PRD (e.g., `get_technical_indicator`, `AlpacaDataConnector`).

### Step 1: Define the Specification
Before writing any code, create a simple specification file in the `/specs` directory. This is a markdown file that clearly defines the component's interface, inputs, expected outputs, and error handling.

**Example: `specs/tools/technical_analysis.spec.md`**
```markdown
### Function: `get_technical_indicator`

- **Signature:** `get_technical_indicator(symbol: str, indicator: str, time_period: str = '14d', data_source: object) -> float`
- **Description:** Calculates a specified technical indicator for a given symbol.
- **Parameters:**
  - `symbol`: The ticker symbol (e.g., 'BTC-USD').
  - `indicator`: The indicator to calculate (e.g., 'RSI').
  - `time_period`: The lookback period for the calculation.
  - `data_source`: An object that provides historical price data.
- **Returns:** A float representing the latest indicator value.
- **Raises:** `ValueError` if the indicator is unsupported, `DataSourceError` if data cannot be fetched.
```

### Step 2: Write the Failing Test
Create a test file in the `/tests` directory that implements the specification. Use `pytest` fixtures and mocking libraries (`pytest-mock`) to isolate the component. The test should fail because the implementation doesn't exist yet.

**Example: `tests/tools/test_technical_analysis.py`**
```python
import pytest
from unittest.mock import MagicMock
# from quantchain.tools.technical_analysis import get_technical_indicator # This will fail initially

def test_get_rsi_indicator():
    # Arrange
    mock_data_source = MagicMock()
    # Mock the return of a pandas DataFrame with price data
    mock_data_source.get_historical_data.return_value = ... # Mocked data that results in a known RSI

    # Act
    # rsi_value = get_technical_indicator('BTC-USD', 'RSI', data_source=mock_data_source)

    # Assert
    # assert rsi_value == 68.5 # Known expected value
    pass # Placeholder until implementation exists
```

### Step 3: Implement the Code
Now, write the implementation code in the main source directory (e.g., `/quantchain/tools/technical_analysis.py`) that makes your test pass.

### Step 4: Refactor
With the tests passing, you can confidently refactor your code for clarity, performance, and style without breaking its functionality.

## 3. Workflow for New Agents (from the Agent Zoo)

Agents are the high-level reasoning systems that use components to make trading decisions. Testing them involves integration tests and backtesting simulations.

### Step 1: Define the Agent's Logic Flow
In a spec file (`/specs/agents/`), outline the agent's reasoning loop, referencing the tools it will use.

**Example: `specs/agents/memecoin_vibe_trader.spec.md`**
```markdown
### Agent: Memecoin Vibe Trader

1.  **Scan:** Use `DexscreenerDataConnector` to find new token pairs created in the last hour.
2.  **Filter:** For each new token, use `SocialMediaScraper` tool to get follower counts and recent activity.
3.  **Analyze (Reason):** Pass the filtered list to the LLM. The prompt will ask the LLM to rank the tokens based on "vibe," a combination of name, recent social media velocity, and tokenomics (if available).
4.  **Execute:** If the top-ranked token meets a risk threshold (set by the `RiskManagerAgent`), use the `AlpacaExecutionTool` to place a small buy order.
```

### Step 2: Write the Backtest Specification
Create a backtest file in `/tests/backtests/`. This test will use the realistic backtesting engine (Component 4) with mocked data feeds and execution handlers. The goal is to verify the agent's end-to-end logic in a simulated environment.

**Example: `tests/backtests/test_memecoin_vibe_trader.py`**
```python
import pytest
# from quantchain.backtester import Backtester
# from quantchain.agents.memecoin_vibe_trader import MemecoinVibeTrader

def test_memecoin_vibe_trader_identifies_and_trades_target():
    # Arrange: Setup the backtester with mock data
    # Mock Dexscreener to return a specific "hyped" token
    # Mock the LLM to return a deterministic "BUY" decision for that token
    # Mock the Alpaca executor to confirm the order
    backtest_config = { ... }
    # backtester = Backtester(config=backtest_config)

    # Act
    # results = backtester.run(MemecoinVibeTrader)

    # Assert
    # assert results.total_trades == 1
    # assert results.final_equity > results.initial_equity
    pass # Placeholder
```

### Step 3: Implement the Agent
Build the agent using the core agentic framework (`LangGraph`), connecting the required tools and data feeds to make the backtest pass.

---

By following this process, we ensure that every piece of `QuantChain` is verifiable, documented by its tests, and robust enough for financial applications.
