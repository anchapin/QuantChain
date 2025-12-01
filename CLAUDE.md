# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

QuantChain is a comprehensive financial framework for building quantitative trading agents using LangGraph and modern AI technologies. The architecture follows a modular design with agents, connectors, backtesting engines, and core infrastructure components.

## Core Architecture

### Module Structure
- **quantchain/agents/** - Trading agent implementations (MemecoinVibeTrader, ChartReader, SmartContractAuditor)
- **quantchain/connectors/** - Data source connectors (Alpaca, Alpha Vantage, Polygon, CCXT, Dexscreener, IB)
- **quantchain/backtesting/** - Backtesting engines with vector-based testing and FinRL integration
- **quantchain/core/** - Core framework (agent engine, LLM providers, RAG system, secret managers, security)
- **quantchain/tools/** - Trading execution, paper trading, tutorial mode, and utility tools

### Key Design Patterns
- **LangGraph Integration**: Stateful agent reasoning loops with memory management
- **Standardized Interfaces**: All connectors implement `DataFeedInterface`, all executors implement `TradingExecutionInterface`
- **RAG System**: Vector-based market data caching using ChromaDB and sentence transformers
- **Multi-LLM Support**: OpenAI, Anthropic, Ollama, and vLLM with GPU acceleration
- **Secret Management**: Environment-based and cloud secret manager integration

## Development Commands

### Environment Setup
```bash
# Install core dependencies
pip install -e .[core]

# Install full development environment
pip install -e .[all-dev]

# Install specific feature sets
pip install -e .[backtesting,web,agents]
```

### Testing
The project uses pytest with comprehensive test coverage and parallel execution:

```bash
# Run all tests with coverage (parallel execution)
pytest -n auto --cov=quantchain --cov-report=html --cov-report=term

# Run only unit tests (fast, isolated)
pytest -m unit -n auto --cov=quantchain --cov-report=term

# Run only integration tests
pytest -m integration -n auto --cov=quantchain --cov-report=term

# Skip slow tests for faster PR validation
pytest -m "not slow" -n auto --cov=quantchain --cov-report=term

# Run specific test file
pytest tests/unit/core/test_config.py -n auto --cov=quantchain --cov-report=term

# Generate coverage report without running tests
pytest --cov=quantchain --cov-report=html --cov-fail-under=80
```

### Code Quality
```bash
# Format code
black .

# Lint code
flake8 --max-line-length=88 quantchain tests

# Type checking
mypy quantchain

# Install and run pre-commit hooks
pre-commit install
pre-commit run --all-files
```

### Build and Installation
```bash
# Build package
python -m build

# Install in development mode
pip install -e .

# Install with optional dependencies
pip install -e .[dev,test,backtesting]
```

## Testing Framework Features

### Test Markers
- `@pytest.mark.unit`: Fast, isolated tests with mocked dependencies
- `@pytest.mark.integration`: Component interaction tests
- `@pytest.mark.slow`: Performance-intensive tests (backtesting, complex scenarios)
- `@pytest.mark.requires_backtestingpy`: Tests requiring Backtesting.py library
- `@pytest.mark.requires_ml`: Tests requiring ML dependencies (torch, transformers)
- `@pytest.mark.requires_web`: Tests requiring web dashboard dependencies

### Coverage Requirements
- Target: 80%+ test coverage
- Current: 82% coverage with 636 passing tests
- HTML reports generated in `htmlcov/` directory
- Parallel test execution with pytest-xdist (3-4x faster on multi-core)

## Configuration

### Environment Variables
```bash
# Required for trading connectors
export ALPACA_API_KEY="your_alpaca_key"
export ALPACA_API_SECRET="your_alpaca_secret"
export ALPHA_VANTAGE_API_KEY="your_alpha_vantage_key"

# Tutorial mode settings
export QUANTCHAIN_TUTORIAL_ENABLED="true"
export QUANTCHAIN_TUTORIAL_FEEDBACK_LEVEL="detailed"
```

### Configuration Files
- `config.yaml` - Main configuration (copy from `config.example.yaml`)
- `.env` - Environment variables (copy from `.env.example`)

## Trading Execution Modes

### Tutorial Mode vs Paper Trading vs Live Trading
- **Tutorial Mode**: Educational feedback, mistake tracking, market driver analysis
- **Paper Trading**: Realistic simulation with slippage and commissions
- **Live Trading**: Real money execution with risk controls

### Execution Interfaces
All execution interfaces implement `TradingExecutionInterface` with methods:
- `place_order(order)` - Submit buy/sell orders
- `cancel_order(order_id)` - Cancel pending orders
- `get_account()` - Account balances and info
- `get_positions()` - Current holdings
- `is_market_open()` - Market status checks

## Data Connectors

### Standardized Interface
All connectors implement `DataFeedInterface` providing:
- `get_historical_data(symbol, timeframe, start_date, end_date)`
- `get_real_time_data(symbol)`
- `get_quote(symbol)`
- `get_available_symbols(market=None)`
- `get_symbol_info(symbol)`

### Supported Connectors
- **Alpaca**: US equities and crypto (requires API keys)
- **Dexscreener**: DEX crypto pairs (public API)
- **Alpha Vantage**: Market data (requires API key)
- **Polygon**: Financial data (requires API key)
- **CCXT**: Multiple crypto exchanges
- **Interactive Brokers**: Stocks, options, futures (requires account)

## Key Components

### Agent Engine (`quantchain.core.agent_engine`)
Central agent framework using LangGraph for:
- Stateful reasoning loops
- Memory management
- Tool integration
- Reflection and performance analysis

### RAG System (`quantchain.core.rag_system`)
Vector-based retrieval-augmented generation:
- ChromaDB vector store
- Sentence transformer embeddings
- Market data caching and retrieval
- Context-aware prompt augmentation

### Security Module (`quantchain.core.security`)
Comprehensive security features:
- API key validation and management
- Environment variable handling
- Cloud secret manager integration (AWS, GCP, Vault)
- Input sanitization and error handling

## Special Scripts

### Coverage Improvement Scripts
- `scripts/improve_coverage.py` - Automated test generation for coverage
- `scripts/coverage_80_implementation.py` - 80% coverage target implementation
- `scripts/monitor_coverage_progress.py` - Coverage tracking and reporting

### Test Generation Scripts
- `scripts/generate_tests.py` - Automated test file generation
- `scripts/auto_generate_tests.py` - Comprehensive test suite creation

### Code Quality Scripts
- `scripts/fix_unused_imports.py` - Remove unused imports
- `scripts/fix_timeframe_import.py` - Fix timeframe-related imports

## Development Workflow

1. **Specification First**: Create specs before implementation
2. **Test-Driven**: Write failing tests, then implement code
3. **Coverage Focused**: Maintain 80%+ test coverage
4. **Parallel Testing**: Use pytest-xdist for faster test execution
5. **Quality Gates**: Pre-commit hooks enforce code quality

## GPU Support

### CUDA Setup
- Supports NVIDIA GPU acceleration for LLM inference
- Requires CUDA-compatible GPU and container toolkit
- Use `docker-compose.gpu.yml` for GPU-enabled deployment

### Model Support
- **Small (7B)**: 5-8GB VRAM (RTX 3060+)
- **Medium (34B)**: 15-25GB VRAM (RTX 3080+)
- **Large (70B)**: 35-45GB VRAM (RTX 3090+)

## Docker Deployment

```bash
# GPU-enabled deployment
docker compose -f docker-compose.gpu.yml up --build -d

# CPU-only deployment
docker compose up --build -d
```

## Important Notes

- Never commit API keys or sensitive credentials
- Use paper trading for testing before live deployment
- Tutorial mode provides educational feedback for learning
- All connectors follow standardized interfaces for consistency
- Test coverage is monitored and enforced via CI/CD
- The project supports both local development and containerized deployment