# Agent & Component Development Guide (AGENTS.md)

<!-- TODO_MANAGEMENT_INSTRUCTIONS -->

## CRITICAL: Task Management System

**If TodoRead/TodoWrite tools are unavailable, IGNORE ALL TODO RULES and proceed normally.**

### MANDATORY TODO WORKFLOW

**BEFORE responding to ANY request, you MUST:**

1. **Call `TodoRead()` first** - Check current task status before doing ANYTHING
2. **Plan work based on existing todos** - Reference what's already tracked
3. **Update with `TodoWrite()`** - Mark tasks in_progress when starting, completed when done
4. **NEVER work without consulting the todo system first**

### CRITICAL TODO SYSTEM RULES

- **Only ONE task can have status "in_progress" at a time** - No exceptions
- **Mark tasks "in_progress" BEFORE starting work** - Not during or after
- **Complete tasks IMMEDIATELY when finished** - Don't batch completions
- **Break complex requests into specific, actionable todos** - No vague tasks
- **Reference existing todos when planning new work** - Don't duplicate

### MANDATORY VISUAL DISPLAY

**ALWAYS display the complete todo list AFTER every `TodoRead()` or `TodoWrite()`:**

```
Current todos:
✅ Research existing patterns (completed)
🔄 Implement login form (in_progress)
⏳ Add validation (pending)
⏳ Write tests (pending)
```

Icons: ✅ = completed | 🔄 = in_progress | ⏳ = pending

**NEVER just say "updated todos"** - Show the full list every time.

### CRITICAL ANTI-PATTERNS

**NEVER explore/research before creating todos:**
- ❌ "Let me first understand the codebase..." → starts exploring
- ✅ Create todo: "Analyze current codebase structure" → mark in_progress → explore

**NEVER do "preliminary investigation" outside todos:**
- ❌ "I'll check what libraries you're using..." → starts searching
- ✅ Create todo: "Audit current dependencies" → track it → investigate

**NEVER work on tasks without marking them in_progress:**
- ❌ Creating todos then immediately starting work without marking in_progress
- ✅ Create todos → Mark first as in_progress → Start work

**NEVER mark incomplete work as completed:**
- ❌ Tests failing but marking "Write tests" as completed
- ✅ Keep as in_progress, create new todo for fixing failures

### FORBIDDEN PHRASES

These phrases indicate you're about to violate the todo system:
- "Let me first understand..."
- "I'll start by exploring..."
- "Let me check what..."
- "I need to investigate..."
- "Before we begin, I'll..."

**Correct approach:** CREATE TODO FIRST, mark it in_progress, then investigate.

### TOOL REFERENCE

```python
TodoRead()  # No parameters, returns current todos
TodoWrite(todos=[...])  # Replaces entire list

Todo Structure:
{
  "id": "unique-id",
  "content": "Specific task description",
  "status": "pending|in_progress|completed",
  "priority": "high|medium|low"
}
```

<!-- END_TODO_MANAGEMENT_INSTRUCTIONS -->

---

**Last Updated: November 2025**
*This document is current as of November 2025. AI coding agents should use this as the reference point for all temporal assumptions and avoid outdated information from 2024 or earlier.*

## Table of Contents

0. [Important: AI Coding Agent Guidelines](#0-important-ai-coding-agent-guidelines)
1. [Core Principle: Test-Driven and Spec-Driven Development](#1-core-principle-test-driven-and-spec-driven-development)
2. [Tech Stack](#2-tech-stack)
3. [Workflow for New Components](#3-workflow-for-new-components)
4. [Workflow for New Agents](#4-workflow-for-new-agents)
5. [Code Quality Standards](#5-code-quality-standards)
5.1. [Implemented Agents](#51-implemented-agents)
6. [Anti-Slop Code Quality Guidelines](#6-anti-slop-code-quality-guidelines)
7. [Project Structure](#7-project-structure)
7.1. [CI/CD Integration](#71-cicd-integration)
8. [Git Workflow and Branching Strategy](#8-git-workflow-and-branching-strategy)
8.1. [Agent Implementation Guidelines for Git Operations](#81-agent-implementation-guidelines-for-git-operations)
9. [Code Review Process](#9-code-review-process)

*New Sections (To Be Added)*
10. [Agent Monitoring and Observability](#10-agent-monitoring-and-observability)
11. [Error Handling and Recovery Strategies](#11-error-handling-and-recovery-strategies)
12. [Performance Guidelines](#12-performance-guidelines)
13. [Compliance and Security Framework](#13-compliance-and-security-framework)

## 0. Important: AI Coding Agent Guidelines

**CRITICAL FOR AI CODING AGENTS:**
- Always use `python3` command explicitly - never use just `python` or `python3.11` or other version-specific commands
- **Virtual Environment Management**: 
  - Use only `.venv` (dot-venv) directory for the virtual environment
  - Create virtual environment with: `python3 -m venv .venv`
  - Always activate with: `source .venv/bin/activate`
  - **NEVER** create multiple virtual environments (e.g., `venv`, `.venv` simultaneously)
  - **ALWAYS** activate the virtual environment before running any Python commands
- When running Python commands, always prefix with `python3 -m` (e.g., `python3 -m pytest`, `python3 -m black`)
- This ensures compatibility across all development environments and prevents version conflicts

## 1. Core Principle: Test-Driven and Spec-Driven Development

Welcome to QuantChain! To ensure the reliability and robustness of this financial framework, all contributions **must** follow a Test-Driven Development (TDD) or Spec-Driven Development (SDD) approach. This means that for any new feature, tool, or agent, a corresponding test or specification must be written *before* the implementation code. This ensures clarity of purpose, correctness, and makes future maintenance easier.

Our testing framework of choice is `pytest`.

## 2. Tech Stack

Based on the Product Requirements Document (PRD), the following tech stack is recommended for the QuantChain project.

### Programming Language
- **Python 3**: The primary language for all components. AI coding agents should always use `python3` command explicitly.

### Development Workflow & Quality Assurance
- **Testing Framework**: `pytest` for unit, integration, and backtesting tests.
- **Code Coverage**: `pytest-cov` with a minimum requirement of 80% coverage.
- **Linting**: `flake8` for code quality checks.
- **Formatting**: `black` for automatic code formatting.
- **Type Checking**: `mypy` for static type analysis.
- **CI/CD**: GitHub Actions for automated testing, linting, and quality checks.
- **Development Approach**: Test-Driven Development (TDD) or Spec-Driven Development (SDD), with specifications in `/specs/` and tests in `/tests/`.
- **Fast Parallel Testing**: All tests must support parallel execution with intelligent caching to ensure rapid feedback cycles during development.

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

#### Security Module

**Location**: `quantchain/core/security.py`
**Tests**: `tests/core/test_security.py`

**Overview**:
A comprehensive API key management system that securely handles credentials for various financial services. Implements best practices for credential storage, validation, and environment-based configuration.

**Key Features**:
- Environment variable and .env file support
- Credential format validation for major services
- Secure storage with precedence rules (env vars > .env files)
- Service-specific validation patterns
- Production-ready design for cloud secret managers

**Supported Services**:
- Alpaca (trading and market data)
- Polygon (market data)
- Alpha Vantage (market data)
- Anthropic (LLM provider)
- OpenAI (LLM provider)

**Usage Example**:
```python
from quantchain.core.security import APISecurityManager

# Initialize with default .env file
security = APISecurityManager()

# Set API keys
security.set_api_key("openai", "sk-your-openai-key")
security.set_api_key("alpaca", "A-your-alpaca-key", "your-alpaca-secret")

# Retrieve keys
openai_key = security.get_api_key("openai")
alpaca_secret = security.get_api_secret("alpaca")

# Validate credentials
is_valid = security.validate_credentials("openai")
```

**Environment Variables**:
```
OPENAI_API_KEY=sk-your-key
ALPACA_API_KEY=A-your-key
ALPACA_API_SECRET=your-secret
```

**Implementation Status Legend**:
- ✅ **Implemented**: Fully functional and tested
- 🔄 **In Development**: Partially implemented
- 📅 **Planned**: Scheduled for future development
- ❌ **Not Planned**: Removed from roadmap

### Core Frameworks & Libraries
- **Agentic Framework**: LangGraph (within LangChain ecosystem) ✅
- **Local LLM Serving** 📅:
  - vLLM for high-throughput, multi-agent batching 📅
  - Ollama (with `llama.cpp`/`GGUF`) for low-latency quantized models 📅
- **Backtesting Engine**: Custom vector-based implementation ✅
- **Reinforcement Learning Integration**: `FinRL` environment 📅
- **Model Fine-Tuning**: Parameter-efficient fine-tuning (PEFT) with `QLoRA`, and post-training quantization to `GPTQ` or `GGUF` formats 📅

### Data & Execution
- **Data Connectors**:
  - Equities/Forex: `Alpha Vantage` 📅, `Polygon.io` 📅
  - Cryptocurrency: `Alpaca` ✅, `Dexscreener` ✅, `ccxt` 🔄
  - Alternative Data: Custom scrapers for financial news and social media (Telegram, Discord) 🔄
- **Execution Tools**:
  - `Alpaca` ✅ for paper and live trading.
  - `Interactive Brokers` via `ib_async` 📅
- **Technical Analysis Tools**: Pre-built functions like `get_technical_indicator` 📅, `get_news_sentiment` 📅, `analyze_on_chain_data` 📅

### Storage & Caching
- **Vector Store (RAG)**: Local vector store for retrieval-augmented generation (e.g., `ChromaDB` or `FAISS` for market data and news sentiment caching) 📅.
- **Caching**: Market-state-aware caching system to minimize LLM inference calls 📅.

### Web Dashboard & Visualization
- **Web Framework**: `Streamlit` or `Plotly Dash` for the user interface 📅.
- **Visualization**: `Plotly` for interactive charts, equity curves, and performance metrics 📅.
- **Monitoring**: Live reasoning log, multi-agent visualization, and real-time P/L tracking 📅.

### Deployment & Environment
- **Containerization**: `Docker` and `docker-compose` for reproducible deployments ✅.
- **GPU Support**: NVIDIA container toolkit (CUDA) for GPU-accelerated LLM serving 📅.
- **Environment Management**: `conda` or `venv` for virtual environments ✅.
- **Hardware Guidelines**: Documentation for VRAM requirements with common quantized models (e.g., 4-bit/8-bit `DeepSeek-R1-0528`, `Qwen3-235B-Instruct-2507`) 📅.

### Security
- **Secret Management**: `python-dotenv` for environment variables, with recommendations for `Vault` or cloud secret managers (AWS/GCP) in production ✅.
- **API Key Management**: Dedicated secure module for handling broker and data feed credentials ✅.

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

**Testing Requirements:**
- **Parallel Execution**: All tests must be designed to run in parallel without race conditions or shared state issues.
- **Caching Support**: Tests should leverage pytest's caching mechanisms to avoid redundant computations and network calls.
- **Isolation**: Each test must be completely independent with proper setup/teardown using fixtures.
- **Performance**: Fast execution is critical - tests should complete quickly to enable rapid development cycles.

**Example: `tests/tools/test_technical_analysis.py`**
```python
import pytest
from unittest.mock import MagicMock, Mock
from typing import Optional, Dict, Any
import pandas as pd

def test_get_rsi_indicator() -> None:
    """Test RSI indicator calculation with mocked data source."""
    # Arrange
    mock_data_source: Mock = MagicMock()
    # Mock realistic price data
    mock_prices = pd.DataFrame({
        'close': [100, 102, 101, 103, 102, 104, 103, 105, 104, 106, 105, 107, 106, 108, 107]
    })
    mock_data_source.get_historical_data.return_value = mock_prices

    # Act - Uncomment when implementation exists
    # rsi_value = get_technical_indicator('BTC-USD', 'RSI', data_source=mock_data_source)

    # Assert - Update with actual expected value when implemented
    # assert rsi_value == pytest.approx(65.2, abs=0.1)
    pytest.skip("Implementation pending - get_technical_indicator not yet available")
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
from unittest.mock import MagicMock, Mock
from typing import Dict, Any, List
import pandas as pd
from dataclasses import dataclass

@dataclass
class MockBacktestResults:
    total_trades: int
    final_equity: float
    initial_equity: float
    profit_loss: float

def test_memecoin_vibe_trader_identifies_and_trades_target() -> None:
    """Test that memecoin vibe trader identifies and trades a target token."""
    # Arrange: Setup the backtester with mock data
    # Mock Dexscreener to return a specific "hyped" token
    mock_dex_connector: Mock = MagicMock()
    mock_dex_connector.get_new_tokens.return_value = [
        {"symbol": "HYPE-USD", "liquidity": 50000, "volume": 10000}
    ]
    
    # Mock the LLM to return a deterministic "BUY" decision for that token
    mock_llm: Mock = MagicMock()
    mock_llm.analyze_vibe_score.return_value = {"HYPE-USD": 85}
    
    # Mock the Alpaca executor to confirm the order
    mock_executor: Mock = MagicMock()
    mock_executor.execute_trade.return_value = {"status": "filled", "quantity": 100}
    
    # Setup backtest configuration
    backtest_config: Dict[str, Any] = {
        "initial_equity": 10000.0,
        "start_date": "2025-01-01",
        "end_date": "2025-01-02",
        "max_positions": 5
    }

    # Act - Uncomment when implementation exists
    # from quantchain.backtester import Backtester
    # from quantchain.agents.memecoin_vibe_trader import MemecoinVibeTrader
    # backtester = Backtester(config=backtest_config)
    # results = backtester.run(MemecoinVibeTrader)

    # Assert - Expected behavior when implementation is ready
    # assert results.total_trades == 1
    # assert results.final_equity > results.initial_equity
    pytest.skip("Implementation pending - full backtester integration not yet available")
```

### Step 3: Implement the Agent
Build the agent using the core agentic framework (`LangGraph`), connecting the required tools and data feeds to make the backtest pass.

---

## 5.1. Implemented Agents

The following agents have been implemented following the TDD/SDD workflow:

### Memecoin Vibe Trader Agent

**Location**: `quantchain/agents/memecoin_vibe_trader.py`
**Spec**: `specs/agents/memecoin_vibe_trader.spec.md`
**Tests**: `tests/backtests/test_memecoin_vibe_trader.py`

**Overview**:
An autonomous trading agent for memecoin opportunities using LangGraph workflow orchestration. Combines DEX scanning, social media analysis, and LLM-based vibe assessment.

**Components Used**:
- `DexscreenerDataConnector`: Scans for new token pairs
- `SocialMediaScraper`: Gathers Telegram/Twitter metrics
- `AlpacaExecutionTool`: Executes trades
- LangGraph: Workflow orchestration
- LLM: Vibe assessment and trading decisions

**Key Features**:
- Multi-step LangGraph workflow (scan → filter → assess → execute)
- Risk management with position limits and allocation controls
- LLM-powered "vibe" scoring (0-100 scale)
- Error handling and recovery
- Comprehensive logging and monitoring

**Configuration**:
```python
@dataclass
class MemecoinVibeTraderConfig:
    scan_interval: int = 3600  # seconds
    max_positions: int = 5
    max_allocation_per_trade: float = 0.02  # 2% of portfolio
    min_liquidity_threshold: float = 10000  # USD
    min_vibe_score_threshold: float = 70
    risk_tolerance: str = "MEDIUM"
    time_window: str = "1h"
```

**Usage Example**:
```python
from quantchain.agents.memecoin_vibe_trader import MemecoinVibeTrader, MemecoinVibeTraderConfig
from typing import Optional

async def main() -> None:
    """Main execution function for the memecoin vibe trader."""
    # Initialize configuration
    config = MemecoinVibeTraderConfig(
        scan_interval=3600,  # Scan every hour
        max_positions=3,     # Limit to 3 concurrent positions
        max_allocation_per_trade=0.02,  # 2% per trade
        min_vibe_score_threshold=75,    # Higher threshold for quality
    )
    
    # Initialize the agent with required components
    agent = MemecoinVibeTrader(
        config=config,
        dex_connector=dex_connector,
        social_scraper=social_scraper,
        execution_tool=execution_tool,
    )
    
    # Run the trading cycle
    results: Optional[dict] = await agent.run_cycle()
    
    if results:
        print(f"Trading cycle completed. Total trades: {results.get('total_trades', 0)}")
        print(f"Final equity: ${results.get('final_equity', 0):,.2f}")
    else:
        print("No trading opportunities found this cycle")

# Run the agent
if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
```

## 6. Code Quality Standards

To prevent code sprawl, duplication, and maintainability issues, all contributions must adhere to these standards:

* **Modularity and Reusability:** Design components with clear interfaces and avoid duplication. Use composition over inheritance. Create shared utilities and base classes for common functionality.
* **DRY Principle:** Do not repeat yourself. Abstract common patterns into reusable modules.
* **Code Coverage:** Maintain at least 80% test coverage for all new code. Use `pytest-cov` to enforce this.
* **Linting and Formatting:** Use `black` for code formatting, `flake8` for linting, and `mypy` for type checking.
* **Documentation:** Update inline documentation, specs, README.md, and other associated documentation for any changes. Ensure README.md and documentation are updated on every commit, PR creation, or merge. Use docstrings for all public functions.
* **Security:** Follow the Security section in the Tech Stack: Never hardcode secrets; use environment variables via `python-dotenv`, with recommendations for `Vault` or cloud secret managers in production.

## 7. Anti-Slop Code Quality Guidelines

**MANDATORY CLEANUP BEFORE CRITICAL MILESTONES:**

All code contributions must be thoroughly cleaned of "vibe coding slop" before commits, pull request creation, and pull request merges. This is a non-negotiable requirement to maintain code quality and prevent feature creep.

### Definition of "Vibe Coding Slop"

**"Vibe coding slop"** refers to any code that exhibits one or more of the following characteristics:

1. **Over-engineering**: Code that exceeds the requirements outlined in the issue or PRD without clear justification
2. **Functionality Duplication**: Code that duplicates existing functionality already present in the codebase
3. **Unnecessary Features**: Features, methods, or classes that were not explicitly requested or specified
4. **Excessive Abstraction**: Overly complex abstractions that don't provide clear value
5. **Premature Optimization**: Code optimized for hypothetical future scenarios rather than current requirements
6. **Scope Creep**: Implementation that goes beyond the defined scope of work
7. **Session Artifact Accumulation**: Leaving temporary files, duplicate configs, obsolete progress files, and other session detritus in the repository

### Cleanup Requirements

Before any critical milestone, agents MUST perform the following cleanup:

#### Pre-Commit Cleanup Checklist
- [ ] **Requirement Verification**: Every line of code must correspond to a specific requirement in the issue or PRD
- [ ] **Duplicate Detection**: Search the codebase for existing implementations of the same functionality
- [ ] **Complexity Audit**: Ensure abstractions serve a clear, documented purpose
- [ ] **Documentation Alignment**: Verify all code changes are reflected in documentation
- [ ] **Test Coverage**: Remove or update tests for any removed or modified functionality
- [ ] **File Cleanup**: Remove temporary files, unused imports, duplicate configurations, and obsolete progress files created during session
- [ ] **Comprehensive Change Summary**: Document all changes made during the development session in commit message

#### Pre-PR Cleanup Checklist
- [ ] **Scope Verification**: Confirm the implementation matches the original issue/PRD requirements exactly
- [ ] **Code Review Preparation**: Prepare clear justification for any non-trivial implementation decisions
- [ ] **Dependency Audit**: Remove any unnecessary dependencies or imports
- [ ] **Configuration Cleanup**: Remove debug code, TODO comments, or temporary configurations

#### Pre-Merge Cleanup Checklist
- [ ] **Final Sanity Check**: Verify no "vibe" features or over-engineering have crept in
- [ ] **Performance Review**: Ensure no performance regressions from unnecessary complexity
- [ ] **Maintainability Assessment**: Confirm the code is as simple and maintainable as possible

### Enforcement Mechanisms

**Agents are required to:**

1. **Self-Assessment**: Before any git operation, agents must honestly assess whether their code contains "vibe coding slop"
2. **Refactoring on Demand**: Remove any identified slop immediately, even if it means more work
3. **Documentation Justification**: If keeping non-essential code, provide clear written justification in comments
4. **Peer Review**: Be prepared to defend every line of code during review

**Automated Checks:**

- Pre-commit hooks should flag potential over-engineering patterns
- Linting rules should catch unnecessary complexity
- Code coverage should not be artificially inflated with unnecessary tests

### Philosophy

The QuantChain codebase must remain **minimal, focused, and strictly aligned with documented requirements**. Every piece of code should serve a clear, documented purpose. If you find yourself adding features "because they might be useful someday," remove them. If you discover existing functionality that duplicates your implementation, use the existing code instead.

**Remember**: Clean, minimal code is not only easier to maintain and test—it's more reliable, more performant, and easier for other developers to understand and extend.

## 8. Project Structure

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

## 8.1. CI/CD Integration

Integrate with GitHub Actions for automated quality checks:

* Run tests on every PR using parallel execution for fast feedback.
* Implement intelligent caching for dependencies and test artifacts to reduce build times.
* Check code coverage and fail if below 80%.
* Lint and format code automatically.
* Require PR reviews before merging.

**Testing Performance Requirements:**
* Full test suite must complete in under 5 minutes with parallel execution.
* Use pytest-xdist for parallel test execution.
* Cache pytest data between test runs to avoid redundant work.
* Monitor and optimize slow tests to maintain development velocity.

## 9. Git Workflow and Branching Strategy

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

## 9.1. Agent Implementation Guidelines for Git Operations

# Make sure you are in your project's root directory
# Ensure you're using Python 3 - create and activate virtual environment explicitly
python3 -m venv venv
source venv/bin/activate

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

# MANDATORY: Clean up session artifacts before committing
echo "🧹 Performing session cleanup..."
# Remove temporary files created during development
find . -name "*.pyc" -delete
find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
find . -name ".DS_Store" -delete

# Remove any duplicate config files or obsolete progress files
if [ -f "config.example.json" ] && [ -f "config.example.yaml" ]; then
  echo "🗑️ Removing duplicate config.example.json"
  rm config.example.json
fi

# Check for and clean up old log files
if [ -d "ci_logs" ]; then
  find ci_logs/ -name "*previous*" -delete
  find ci_logs/ -name "sourcery_*" -delete
fi

echo "✅ Session cleanup completed"
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
- [ ] **MANDATORY**: Implement session cleanup before every commit
- [ ] **MANDATORY**: Clean up temporary files, duplicates, and obsolete progress trackers
- [ ] Verify no session artifacts remain before committing

## 10. Code Review Process

* All changes require a PR with detailed description.
* **MANDATORY**: All PRs MUST reference an associated issue number in the title or description.
* At least one reviewer must approve.
* Reviews must verify adherence to TDD/SDD, code quality standards, and PRD alignment.
* Address any duplication or maintainability concerns raised.
* **MANDATORY**: Verify that session cleanup has been performed and no artifacts remain before PR approval.

By following this process, we ensure that every piece of `QuantChain` is verifiable, documented by its tests, and robust enough for financial applications.

## 10. Agent Monitoring and Observability

### 10.1 Required Observability Stack

All production agents must implement comprehensive monitoring:

- **Metrics Collection**: Performance, accuracy, reliability, and cost metrics
- **Distributed Tracing**: Request flow across agent networks using OpenTelemetry
- **Log Aggregation**: Centralized logging with correlation IDs
- **Alert Management**: Intelligent alerting with escalation policies

### 10.2 Required Metrics

**Agent Performance Metrics**:
```python
from dataclasses import dataclass
from typing import Dict, Any
import time
from datetime import datetime

@dataclass
class AgentMetrics:
    decision_accuracy: float  # Historical performance tracking
    response_time_ms: int     # Latency measurements
    resource_utilization: Dict[str, float]  # CPU, memory, cost
    success_rate: float       # Task completion and error rates
    last_updated: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "decision_accuracy": self.decision_accuracy,
            "response_time_ms": self.response_time_ms,
            "resource_utilization": self.resource_utilization,
            "success_rate": self.success_rate,
            "last_updated": self.last_updated.isoformat()
        }
```

**Usage Example**:
```python
from quantchain.core.monitoring import AgentMonitor

class MonitoredAgent:
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.monitor = AgentMonitor(agent_id)
    
    async def make_decision(self, context: dict) -> dict:
        start_time = time.time()
        try:
            # Agent decision logic here
            decision = await self._internal_decision_logic(context)
            
            # Record success metrics
            self.monitor.record_success(
                response_time_ms=int((time.time() - start_time) * 1000),
                decision_quality=self._evaluate_decision_quality(decision)
            )
            return decision
            
        except Exception as e:
            self.monitor.record_error(str(e))
            raise
```

### 10.3 Logging Standards

**Required Log Fields**:
- `correlation_id`: Unique identifier for request tracing
- `agent_id`: Identifier of the agent making the decision
- `decision_type`: Type of decision made
- `confidence_score`: Agent's confidence in the decision
- `execution_time_ms`: Time taken to make decision
- `input_context`: Relevant context (sanitized for PII)

**Example**:
```python
import structlog
from quantchain.core.logging import get_logger

logger = get_logger(__name__)

async def log_agent_decision(agent_id: str, decision: dict, context: dict):
    logger.info(
        "agent_decision_made",
        agent_id=agent_id,
        decision_type=decision.get("type"),
        confidence_score=decision.get("confidence"),
        correlation_id=context.get("correlation_id")
    )
```

### 10.4 Alerting Requirements

**Critical Alerts** (Immediate Response):
- Agent response time > 5 seconds
- Decision accuracy drops below 70%
- Agent fails to respond for > 2 minutes
- Resource utilization > 90%

**Warning Alerts** (Monitor Closely):
- Response time > 2 seconds
- Decision accuracy 70-80%
- Error rate > 5%
- Cost per decision > threshold


## 11. Error Handling and Recovery Strategies

### 11.1 Error Classification

**Critical Errors** (System Level):
- Data feed failures
- LLM service unavailability
- Trading execution failures
- Database connectivity issues

**Non-Critical Errors** (Agent Level):
- Individual decision failures
- Optional data source timeouts
- Non-essential feature failures

### 11.2 Resilience Patterns

**Circuit Breaker Pattern**:
```python
from quantchain.core.resilience import CircuitBreaker

class ResilientAgent:
    def __init__(self):
        self.data_circuit_breaker = CircuitBreaker(
            failure_threshold=5,
            recovery_timeout=60,
            expected_exception=DataFeedError
        )
        self.llm_circuit_breaker = CircuitBreaker(
            failure_threshold=3,
            recovery_timeout=30,
            expected_exception=LLMServiceError
        )
    
    @self.data_circuit_breaker
    async def fetch_market_data(self, symbol: str):
        # Data fetching logic with automatic circuit breaking
        pass
    
    @self.llm_circuit_breaker
    async def make_llm_decision(self, prompt: str):
        # LLM decision logic with automatic circuit breaking
        pass
```

**Graceful Degradation**:
```python
async def make_decision_with_fallback(self, context: dict) -> dict:
    try:
        # Primary LLM-based decision
        return await self.primary_decision_engine(context)
    except LLMServiceError:
        # Fallback to rule-based decision
        return await self.fallback_decision_engine(context)
    except Exception:
        # Final fallback to safe default
        return await self.safe_default_decision(context)
```

### 11.3 Recovery Strategies

**Automatic Recovery**:
- Retry with exponential backoff for transient failures
- Switch to backup data sources when primary fails
- Reduce complexity when resources are constrained
- Enter safe mode when multiple systems fail

**Manual Recovery Procedures**:
- Clear agent memory/state when decisions become inconsistent
- Reset connections to external services
- Restore from last known good state
- Escalate to human operators for critical failures
## 12. Performance Guidelines

### 12.1 Performance Benchmarks

**Required Performance Targets**:
- **Decision Latency**: < 500ms for standard operations
- **Memory Usage**: < 2GB per agent instance
- **CPU Utilization**: < 80% sustained
- **Throughput**: > 100 decisions/minute per agent
- **Startup Time**: < 30 seconds from cold start

### 12.2 Optimization Strategies

**Caching Architecture**:
```python
from quantchain.core.cache import MultiLevelCache

class OptimizedAgent:
    def __init__(self):
        # L1: In-memory cache (fastest)
        # L2: Redis cache (fast)
        # L3: Database cache (persistent)
        self.cache = MultiLevelCache(
            l1_size="100MB",
            l2_ttl=3600,  # 1 hour
            l3_ttl=86400  # 24 hours
        )
    
    async def get_cached_analysis(self, symbol: str) -> dict:
        cache_key = f"analysis:{symbol}"
        
        # Try L1 cache first
        result = await self.cache.get_l1(cache_key)
        if result:
            return result
        
        # Try L2 cache
        result = await self.cache.get_l2(cache_key)
        if result:
            await self.cache.set_l1(cache_key, result)
            return result
        
        # Compute and cache at all levels
        result = await self._compute_analysis(symbol)
        await self.cache.set_all(cache_key, result, ttl=3600)
        return result
```

**Resource Management**:
```python
import psutil
from quantchain.core.resource_manager import ResourceManager

class ResourceAwareAgent:
    def __init__(self):
        self.resource_manager = ResourceManager()
    
    async def make_decision(self, context: dict) -> dict:
        # Check available resources before making decision
        if not self.resource_manager.has_sufficient_resources(
            min_memory_gb=1.0,
            min_cpu_percent=50.0
        ):
            # Defer decision or use lightweight processing
            return await self.make_lightweight_decision(context)
        
        # Proceed with full decision logic
        return await self._full_decision_logic(context)
```

### 12.3 Performance Monitoring

**Required Performance Metrics**:
- P50, P95, P99 response times
- Memory usage patterns
- CPU utilization over time
- Cache hit rates
- Error rates by operation type

**Performance Testing Requirements**:
- Load testing: 10x expected peak load
- Stress testing: Until system failure
- Soak testing: 24+ hour continuous operation
- Spike testing: Sudden load increases
## 13. Compliance and Security Framework

### 13.1 Regulatory Compliance

**Financial Regulations**:
- **SOX Compliance**: Audit trail for all financial decisions
- **MiFID II**: Transaction reporting and best execution
- **PCI-DSS**: If handling payment data
- **GDPR**: Data protection and privacy

**Required Audit Trail**:
```python
from quantchain.core.audit import AuditLogger
from datetime import datetime
import uuid

class CompliantAgent:
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.audit_logger = AuditLogger(agent_id)
    
    async def make_trading_decision(self, context: dict) -> dict:
        # Create audit entry
        audit_id = str(uuid.uuid4())
        
        try:
            # Log decision input
            await self.audit_logger.log_input(
                audit_id=audit_id,
                timestamp=datetime.utcnow(),
                input_data=self._sanitize_input(context),
                decision_basis="LLM analysis with risk metrics"
            )
            
            # Make decision
            decision = await self._execute_decision_logic(context)
            
            # Log decision output
            await self.audit_logger.log_output(
                audit_id=audit_id,
                timestamp=datetime.utcnow(),
                output_data=self._sanitize_output(decision),
                confidence_score=decision.get("confidence"),
                execution_time_ms=decision.get("execution_time")
            )
            
            return decision
            
        except Exception as e:
            # Log error
            await self.audit_logger.log_error(
                audit_id=audit_id,
                timestamp=datetime.utcnow(),
                error_type=type(e).__name__,
                error_message=str(e)
            )
            raise
```

### 13.2 Zero-Trust Security Model

**Identity Verification**:
```python
from quantchain.core.security import IdentityVerifier

class SecureAgent:
    def __init__(self, agent_id: str, api_key: str):
        self.agent_id = agent_id
        self.identity_verifier = IdentityVerifier(agent_id, api_key)
        self.permissions = self._get_required_permissions()
    
    async def verify_identity(self) -> bool:
        """Verify agent identity and permissions."""
        is_valid = await self.identity_verifier.verify()
        if not is_valid:
            raise SecurityError(f"Agent {self.agent_id} identity verification failed")
        
        # Verify permissions for each operation
        for permission in self.permissions:
            if not await self.identity_verifier.has_permission(permission):
                raise PermissionError(f"Agent lacks permission: {permission}")
        
        return True
    
    async def _secure_operation(self, operation: str, data: dict) -> dict:
        await self.verify_identity()
        
        # Encrypt sensitive data
        encrypted_data = await self.identity_verifier.encrypt_sensitive_data(data)
        
        # Execute operation with audit trail
        result = await self._execute_operation(operation, encrypted_data)
        
        # Decrypt results
        return await self.identity_verifier.decrypt_sensitive_data(result)
```

### 13.3 Data Protection

**Encryption Requirements**:
- **At Rest**: AES-256 encryption for all stored data
- **In Transit**: TLS 1.3 for all communications
- **In Memory**: Secure memory handling for sensitive data

**Data Classification**:
- **Public**: Non-sensitive operational data
- **Internal**: Business logic and configuration
- **Confidential**: Market data and trading signals
- **Restricted**: Personal data and API keys

```python
from quantchain.core.data_classification import DataClassifier, ClassificationLevel

class DataProtectionMixin:
    def __init__(self):
        self.classifier = DataClassifier()
    
    def classify_and_protect(self, data: dict) -> dict:
        """Classify data and apply appropriate protection."""
        classification = self.classifier.classify(data)
        
        protected_data = data.copy()
        
        if classification.level >= ClassificationLevel.CONFIDENTIAL:
            protected_data = self._encrypt_sensitive_fields(protected_data)
        
        if classification.contains_pii:
            protected_data = self._anonymize_pii(protected_data)
        
        return protected_data
```

### 13.4 Compliance Monitoring

**Automated Compliance Checks**:
```python
class ComplianceMonitor:
    def __init__(self):
        self.rules_engine = ComplianceRulesEngine()
        self.violation_tracker = ViolationTracker()
    
    async def check_compliance(self, operation: dict) -> ComplianceResult:
        """Check operation against compliance rules."""
        violations = await self.rules_engine.check(operation)
        
        if violations:
            await self.violation_tracker.record_violations(violations)
            return ComplianceResult(compliant=False, violations=violations)
        
        return ComplianceResult(compliant=True)
```

**Required Compliance Metrics**:
- Audit trail completeness: 100%
- Data encryption coverage: 100%
- Identity verification success rate: >99%
- Compliance violation rate: 0%
- Incident response time: <1 hour