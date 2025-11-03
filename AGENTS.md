# Agent & Component Development Guide (AGENTS.md)

## 1. Core Principle: Test-Driven and Spec-Driven Development

Welcome to QuantChain! To ensure the reliability and robustness of this financial framework, all contributions **must** follow a Test-Driven Development (TDD) or Spec-Driven Development (SDD) approach. This means that for any new feature, tool, or agent, a corresponding test or specification must be written *before* the implementation code. This ensures clarity of purpose, correctness, and makes future maintenance easier.

Our testing framework of choice is `pytest`.

## 2. Tech Stack

Based on the Product Requirements Document (PRD), the following tech stack is recommended for the QuantChain project.

### Programming Language
- **Python**: The primary language for all components.

### Development Workflow & Quality Assurance
- **Testing Framework**: `pytest` for unit, integration, and backtesting tests.
- **Code Coverage**: `pytest-cov` with a minimum requirement of 80% coverage.
- **Linting**: `flake8` for code quality checks.
- **Formatting**: `black` for automatic code formatting.
- **Type Checking**: `mypy` for static type analysis.
- **CI/CD**: GitHub Actions for automated testing, linting, and quality checks.
- **Development Approach**: Test-Driven Development (TDD) or Spec-Driven Development (SDD), with specifications in `/specs/` and tests in `/tests/`.

### Core Frameworks & Libraries
- **Agentic Framework**: LangGraph (within LangChain ecosystem) for stateful agent reasoning, memory, and reflection.
- **Local LLM Serving**:
  - `vLLM` for high-throughput, multi-agent batching.
  - `Ollama` (with `llama.cpp`/`GGUF`) for low-latency quantized models.
- **Backtesting Engine**: `Backtesting.py` or a custom vector-based implementation.
- **Reinforcement Learning Integration**: `FinRL` environment for RL-based agent testing.
- **Model Fine-Tuning**: Parameter-efficient fine-tuning (PEFT) with `QLoRA`, and post-training quantization to `GPTQ` or `GGUF` formats.

### Data & Execution
- **Data Connectors**:
  - Equities/Forex: `Alpha Vantage`, `Polygon.io`
  - Cryptocurrency: `Alpaca` (WebSocket), `Dexscreener`, `ccxt`
  - Alternative Data: Custom scrapers for financial news and social media (Telegram, Discord)
- **Execution Tools**:
  - `Alpaca` for paper and live trading.
  - `Interactive Brokers` via `ib_async`.
- **Technical Analysis Tools**: Pre-built functions like `get_technical_indicator`, `get_news_sentiment`, `analyze_on_chain_data`.

### Storage & Caching
- **Vector Store (RAG)**: Local vector store for retrieval-augmented generation (e.g., `ChromaDB` or `FAISS` for market data and news sentiment caching).
- **Caching**: Market-state-aware caching system to minimize LLM inference calls.

### Web Dashboard & Visualization
- **Web Framework**: `Streamlit` or `Plotly Dash` for the user interface.
- **Visualization**: `Plotly` for interactive charts, equity curves, and performance metrics.
- **Monitoring**: Live reasoning log, multi-agent visualization, and real-time P/L tracking.

### Deployment & Environment
- **Containerization**: `Docker` and `docker-compose` for reproducible deployments.
- **GPU Support**: NVIDIA container toolkit (CUDA) for GPU-accelerated LLM serving.
- **Environment Management**: `conda` or `venv` for virtual environments.
- **Hardware Guidelines**: Documentation for VRAM requirements with common quantized models (e.g., 4-bit/8-bit `DeepSeek-R1-0528`, `Qwen3-235B-Instruct-2507`).

### Security
- **Secret Management**: `python-dotenv` for environment variables, with recommendations for `Vault` or cloud secret managers (AWS/GCP) in production.
- **API Key Management**: Dedicated secure module for handling broker and data feed credentials.

## 3. Workflow for New Components (Tools, Data Connectors, etc.)

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

## 4. Workflow for New Agents (from the Agent Zoo)

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

## 5. Code Quality Standards

To prevent code sprawl, duplication, and maintainability issues, all contributions must adhere to these standards:

* **Modularity and Reusability:** Design components with clear interfaces and avoid duplication. Use composition over inheritance. Create shared utilities and base classes for common functionality.
* **DRY Principle:** Do not repeat yourself. Abstract common patterns into reusable modules.
* **Code Coverage:** Maintain at least 80% test coverage for all new code. Use `pytest-cov` to enforce this.
* **Linting and Formatting:** Use `black` for code formatting, `flake8` for linting, and `mypy` for type checking.
* **Documentation:** Update inline documentation, specs, README.md, and other associated documentation for any changes. Ensure README.md and documentation are updated on every commit, PR creation, or merge. Use docstrings for all public functions.
* **Security:** Follow the Security section in the Tech Stack: Never hardcode secrets; use environment variables via `python-dotenv`, with recommendations for `Vault` or cloud secret managers in production.

## 6. Project Structure

To maintain organization and avoid sprawl:

* `/quantchain/` - Main source code
  * `/agents/` - Agent implementations
  * `/tools/` - Tool and data library components
  * `/connectors/` - Data feed connectors
  * `/backtesting/` - Backtesting engine
  * `/core/` - Core agent engine and shared utilities
* `/specs/` - Specification files for components and agents
* `/tests/` - Test suites, including unit, integration, and backtests
* `/docs/` - Documentation, including deployment guides
* `/examples/` - Sample agents and configurations

## 7. CI/CD Integration

Integrate with GitHub Actions for automated quality checks:

* Run tests on every PR.
* Check code coverage and fail if below 80%.
* Lint and format code automatically.
* Require PR reviews before merging.

## 8. Git Workflow and Branching Strategy

To maintain a clean and organized repository and prevent accidental commits to the main branch:

- **Branch Creation:** Always create feature branches for new work. Never commit directly to the `main` branch.
- **MANDATORY Branch Verification:** Before performing ANY git operation that modifies code (commit, merge, reset, rebase, etc.), agents MUST:
  1. **Always** execute: `git branch --show-current`
  2. **Verify** the result is NOT `main`
  3. **If** on `main`, the agent MUST:
     - Stop the operation immediately
     - Inform the user they are on main
     - Ask for explicit confirmation to create a feature branch
     - Create a feature branch with descriptive name before proceeding
  4. **Only** proceed with the git operation after confirming on a non-main branch

- **Feature Branch Naming Convention:** Use descriptive names following these patterns:
  - `feature/description-of-feature`
  - `issue-123-description`
  - `bugfix/description-of-bugfix`
  - `refactor/description-of-refactor`

- **Pull Requests:** Use pull requests for all changes to ensure code review and integration.
- **Agent Implementation Requirements:** All agents must implement the following mandatory checks:
  ```bash
  # Before ANY git operation that modifies code:
  CURRENT_BRANCH=$(git branch --show-current)
  if [ "$CURRENT_BRANCH" = "main" ]; then
    echo "ERROR: Cannot perform git operations on main branch"
    echo "Please create a feature branch first:"
    echo "git checkout -b feature/your-descriptive-name"
    exit 1
  fi
  ```

- **Automatic Protection:** CI/CD workflows should include checks that prevent direct merges to main without PR review.

## 8.1. Agent Implementation Guidelines for Git Operations

### Critical Safety Protocol for All Agents

**ALL agents MUST implement the following safety checks before ANY git operation that modifies code:**

#### Step 1: Mandatory Branch Verification
```bash
# This check MUST be performed before:
# - git commit
# - git merge
# - git reset --hard
# - git rebase
# - git push

CURRENT_BRANCH=$(git branch --show-current)
echo "Current branch: $CURRENT_BRANCH"

if [ "$CURRENT_BRANCH" = "main" ]; then
  echo "🚨 SAFETY ERROR: Cannot perform git operations on main branch"
  echo ""
  echo "Required actions:"
  echo "1. Create a feature branch:"
  echo "   git checkout -b feature/your-descriptive-name"
  echo "2. Or switch to existing feature branch:"
  echo "   git checkout feature/branch-name"
  echo ""
  echo "Operation cancelled for safety."
  exit 1
fi

echo "✅ Safety check passed - not on main branch"
```

#### Step 2: Feature Branch Validation
Before proceeding, validate the feature branch follows naming conventions:
```bash
# Check if branch name follows conventions
if [[ ! "$CURRENT_BRANCH" =~ ^(feature|issue|bugfix|refactor)/ ]]; then
  echo "⚠️  Warning: Branch name doesn't follow convention"
  echo "Expected: feature/, issue/, bugfix/, refactor/"
  echo "Consider renaming for consistency"
  read -p "Continue anyway? (y/N): " -n 1 -r
  echo
  if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    exit 1
  fi
fi
```

#### Step 3: Pre-Commit Validation
```bash
# Before commit, ensure working tree is clean and on proper branch
git status --porcelain
if [ $? -ne 0 ]; then
  echo "❌ Git status check failed"
  exit 1
fi

# Verify we're not about to commit to main
git rev-parse --abbrev-ref HEAD | grep -q main
if [ $? -eq 0 ]; then
  echo "🚨 SAFETY ERROR: Attempting to commit to main!"
  exit 1
fi
```

### Required Agent Behavior

1. **Automatic Prevention**: Agents must automatically refuse git operations on main without user intervention
2. **Clear Messaging**: Provide specific instructions for creating feature branches
3. **Logging**: All branch checks must be logged for audit purposes
4. **Fallback**: Always provide safe exit paths when branch checks fail

### Implementation Checklist for Agent Developers

- [ ] Implement mandatory branch check before all git operations
- [ ] Use exact error messages provided above for consistency
- [ ] Test the safety mechanism thoroughly
- [ ] Ensure no code paths bypass the main branch check
- [ ] Add logging for all branch verification attempts

## 9. Code Review Process

* All changes require a PR with detailed description.
* At least one reviewer must approve.
* Reviews must verify adherence to TDD/SDD, code quality standards, and PRD alignment.
* Address any duplication or maintainability concerns raised.

By following this process, we ensure that every piece of `QuantChain` is verifiable, documented by its tests, and robust enough for financial applications.
