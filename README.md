# QuantChain

A financial framework for building quantitative trading agents using LangGraph and modern AI technologies.

## Features

- **Agentic Framework**: Built on LangGraph for stateful agent reasoning and memory
- **Multiple LLM Support**: OpenAI, Anthropic, and local LLMs via vLLM/Ollama with GPU acceleration
- **RAG System**: Vector-based market data caching and retrieval-augmented generation
- **Reflective Performance Analysis**: Agent self-analysis and strategy optimization
- **Comprehensive Data Connectors**: Alpaca, Alpha Vantage, Polygon.io, Dexscreener, CCXT
- **Backtesting Engine**: Vector-based backtesting with FinRL integration
- **Tutorial Mode**: Human learning-focused trading simulation with educational feedback and mistake tracking
- **Paper Trading**: Risk-free strategy testing with realistic market simulation
- **Production Ready**: Docker deployment, GPU support, secure API key management

## Installation

### Prerequisites

- Python 3.10+ (3.12 recommended)
- Git
- Docker & Docker Compose v2
- (Optional) CUDA-compatible GPU for LLM acceleration

### Quick Start with Docker (Recommended)

1. **Clone the repository:**
```bash
git clone https://github.com/anchapin/QuantChain.git
cd QuantChain
```

2. **Setup Docker environment:**
   - **For GPU support:** See [Environment Setup Guide](docs/environment-setup.md#1-install-nvidia-container-toolkit-linux)
   - **For CPU only:** Skip GPU setup and proceed to step 3

3. **Configure environment:**
```bash
cp config.example.yaml config.yaml
cp .env.example .env
# Edit .env with your API keys
```

4. **Run with GPU support:**
```bash
docker compose -f docker-compose.gpu.yml up --build -d
```

5. **Run with CPU only:**
```bash
docker compose up --build -d
```

For detailed setup instructions, troubleshooting, and alternative configurations, see the [Environment Setup Guide](docs/environment-setup.md).

### Local Development Setup

For detailed local development setup instructions, see the [Environment Setup Guide](docs/environment-setup.md#local-development-setup).

**Quick start:**
```bash
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
pip install -r requirements.txt
```

## Hardware Requirements

QuantChain supports a wide range of hardware configurations. See [Hardware Requirements Matrix](docs/hardware-requirements.md) for detailed recommendations:

| Model Size | VRAM Required | Recommended GPU |
|-------------|---------------|-----------------|
| Small (7B) | 5-8GB | RTX 3060+ |
| Medium (34B) | 15-25GB | RTX 3080+ |
| Large (70B) | 35-45GB | RTX 3090+ |

### Quick Recommendations
- **Budget Setup**: RTX 3060 12GB, 32GB RAM, 1TB NVMe SSD
- **Mid-Range**: RTX 3080/4080 16GB, 64GB RAM, 2TB NVMe SSD  
- **Professional**: RTX 3090/4090 24GB, 128GB RAM, 4TB NVMe SSD

For complete hardware guidance and cloud alternatives, see [Deployment Guide](docs/environment-setup.md).

## Configuration

Copy the example configuration file and modify as needed:

```bash
cp config.example.yaml config.yaml
# Edit config.yaml with your settings
```

### Environment Variables

Set the following environment variables for API access:

```bash
export ALPACA_API_KEY="your_alpaca_key"
export ALPACA_API_SECRET="your_alpaca_secret"
export ALPHA_VANTAGE_API_KEY="your_alpha_vantage_key"

# Optional: Tutorial mode settings
export QUANTCHAIN_TUTORIAL_ENABLED="true"
export QUANTCHAIN_TUTORIAL_FEEDBACK_LEVEL="detailed"
```

### Tutorial Mode Configuration

Enable tutorial mode in your `config.yaml`:

```yaml
# Tutorial mode for human learning-focused trading simulation
# Different from paper trading - provides educational feedback and mistake tracking
tutorial:
  enabled: true
  session_duration: 3600  # 1 hour
  learning_objectives:
    - "Understand market drivers"
    - "Practice risk management"
    - "Learn from mistakes"
  feedback_level: detailed  # basic, detailed, comprehensive
  track_mistakes: true
  analyze_market_drivers: true
  confidence_threshold: 0.75
  max_mistakes_per_session: 10
```

## Project Structure

```
quantchain/
├── agents/           # Trading agent implementations
│   └── zoo/         # Pre-built agent collection
├── tools/           # Utility functions and components
├── connectors/      # Data source connectors
├── backtesting/     # Backtesting engine
└── core/           # Core framework components

tests/               # Test suites
specs/               # Component specifications
examples/            # Sample agents and configurations
docs/               # Documentation
```

## Agents

QuantChain includes pre-built trading agents that demonstrate different trading strategies and use cases.

### Memecoin Vibe Trader

An autonomous trading agent that identifies promising memecoin opportunities by combining on-chain data analysis with social media sentiment and LLM-based "vibe" assessment.

**Features:**
- Scans new token pairs on DEXs using Dexscreener
- Gathers social media metrics from Telegram and Twitter
- Uses LLM to assess token "vibe" and make trading recommendations
- Executes trades via Alpaca with risk management

**Usage:**
```python
from quantchain.agents.memecoin_vibe_trader import MemecoinVibeTrader, MemecoinVibeTraderConfig
from quantchain.connectors.dexscreener_connector import DexscreenerDataConnector
from quantchain.tools.social_media_scraper import SocialMediaScraper
from quantchain.tools.execution import AlpacaExecutionTool

# Initialize components
config = MemecoinVibeTraderConfig(
    min_vibe_score_threshold=70,
    max_positions=5,
    max_allocation_per_trade=0.02
)

dex_connector = DexscreenerDataConnector()
social_scraper = SocialMediaScraper()
execution_tool = AlpacaExecutionTool.from_credentials(
    api_key="your_api_key",
    api_secret="your_api_secret"
)

# Create and run agent
agent = MemecoinVibeTrader(config, dex_connector, social_scraper, execution_tool)
results = agent.run_cycle()

print(f"Scanned {results['tokens_scanned']} tokens, executed {results['trades_executed']} trades")
```

**Configuration Options:**
- `scan_interval`: Time between scans (default: 3600 seconds)
- `max_positions`: Maximum number of concurrent positions (default: 5)
- `max_allocation_per_trade`: Max portfolio allocation per trade (default: 2%)
- `min_liquidity_threshold`: Minimum liquidity required (default: $10,000)
- `min_vibe_score_threshold`: Minimum vibe score for trades (default: 70)

## Data Connectors

QuantChain provides a standardized interface for connecting to various data sources for market data:

### Alpaca Connector
- **Markets**: Stocks (US equities) and Cryptocurrencies
- **Features**: Historical data, real-time quotes, market status, symbol information
- **Timeframes**: 1Min, 5Min, 15Min, 1H, 4H, 1D, 1W, 1M
- **Authentication**: Requires Alpaca API key and secret

```python
from quantchain.connectors import AlpacaDataConnector

connector = AlpacaDataConnector(
    api_key="your_api_key",
    api_secret="your_api_secret",
    use_paper=True  # Use paper trading for testing
)

# Get historical data
data = connector.get_historical_data("AAPL", "1D", start_date, end_date)

# Get real-time quote
quote = connector.get_quote("AAPL")
```

### Dexscreener Connector
- **Markets**: DEX cryptocurrency pairs (Uniswap, PancakeSwap, etc.)
- **Features**: Real-time token data, trending pairs, pair search
- **Note**: Provides current price data, not historical data
- **Authentication**: No API key required (public API)

```python
from quantchain.connectors import DexscreenerDataConnector

connector = DexscreenerDataConnector()

# Get real-time data for a token pair
data = connector.get_real_time_data("WETH/USDC:0x123...")

# Get trending pairs
trending = connector.get_trending_pairs(limit=10)
```

### Standardized Interface
All connectors implement the `DataFeedInterface` providing consistent methods:
- `get_historical_data(symbol, timeframe, start_date, end_date)`
- `get_real_time_data(symbol)`
- `get_quote(symbol)`
- `get_available_symbols(market=None)`
- `get_symbol_info(symbol)`
- `is_market_open(market=None)`

## Trading Execution

QuantChain provides a unified trading execution interface supporting both live and paper trading across multiple brokers.

### Alpaca Execution
- **Markets**: US Equities and Cryptocurrencies
- **Features**: Market/limit/stop orders, position management, account info, order history
- **Paper Trading**: Full simulation with paper money and real market data
- **Live Trading**: Real money execution with proper risk controls

```python
from quantchain.tools import create_execution_interface
from quantchain.core.config import get_config

# Load configuration (supports both paper and live trading)
config = get_config("config.json")

# Create execution interface (automatically handles paper/live based on config)
executor = create_execution_interface(config)

# Place a market order
from quantchain.tools import OrderRequest, OrderSide, OrderType

order = OrderRequest(
    symbol="AAPL",
    side=OrderSide.BUY,
    order_type=OrderType.MARKET,
    quantity=10
)
result = executor.place_order(order)

# Get account information
account = executor.get_account()
print(f"Portfolio Value: ${account.portfolio_value}")

# Get current positions
positions = executor.get_positions()
for pos in positions:
    print(f"{pos.symbol}: {pos.quantity} shares, P&L: ${pos.unrealized_pnl}")
```

### Paper Trading Engine
- **Features**: Realistic order simulation with slippage, commissions, and fill models
- **Scenarios**: Customizable market conditions for strategy testing
- **Performance Tracking**: Win rate, Sharpe ratio, max drawdown calculations

```python
from quantchain.tools import PaperTradingExecutor

# Create paper trading executor
executor = PaperTradingExecutor(
    initial_cash=100000.0,
    commission_per_trade=1.0,
    slippage_model=FixedSlippage(slippage_percent=0.1)
)

# Set market prices for testing
executor.set_market_price("AAPL", 150.0)

# Place orders and track performance
order = OrderRequest(symbol="AAPL", side=OrderSide.BUY, order_type=OrderType.MARKET, quantity=100)
result = executor.place_order(order)

# Get performance metrics
metrics = executor.get_performance_metrics()
print(f"Total Return: {metrics.total_return:.2f}%")
```

### Tutorial Mode
- **Learning-Focused Simulation**: Educational feedback and mistake tracking for skill development
- **Market Driver Analysis**: Explains underlying market factors and decision context
- **Mistake Tracking**: Identifies, categorizes, and analyzes trading mistakes with learning recommendations
- **Confidence Metrics**: Tracks confidence building and readiness assessment for live trading
- **Session-Based Learning**: Manages training sessions with clear objectives and progress tracking

```python
from quantchain.tools import TutorialExecutor
from quantchain.core.config import get_config

# Create tutorial executor
config = get_config("config.yaml")
tutorial_executor = TutorialExecutor(
    initial_cash=100000.0,
    config=config,
    learning_objectives=[
        "Understand market drivers",
        "Practice risk management"
    ]
)

# Start tutorial session
session = tutorial_executor.start_tutorial_session(
    symbols=["AAPL", "MSFT"],
    duration=3600
)

# Make trades with feedback
order = OrderRequest(
    symbol="AAPL",
    side=OrderSide.BUY,
    order_type=OrderType.MARKET,
    quantity=10
)
result = tutorial_executor.place_order(order)

# Get tutorial feedback
feedback = tutorial_executor.get_tutorial_feedback()
print(f"Decision quality: {feedback.decision_quality}")
print(f"Market drivers: {feedback.market_drivers}")

# End session and get report
report = tutorial_executor.end_tutorial_session()
print(f"Confidence score: {report['final_feedback'].confidence_score}")
print(f"Mistakes: {len(report['final_feedback'].mistakes)}")
print(f"Ready for live trading: {report['ready_for_live']}")
```

#### Tutorial Mode vs. Paper Trading vs. Live Trading

| Feature | Tutorial Mode | Paper Trading | Live Trading |
|----------|----------------|----------------|--------------|
| **Primary Goal** | Human Learning & Education | Strategy Validation | Real Profit |
| **Feedback Level** | Detailed Educational | Basic Performance | None |
| **Mistake Tracking** | Yes, with Learning Points | No | No |
| **Market Driver Analysis** | Yes, with Explanations | No | No |
| **Confidence Metrics** | Yes, with Readiness Assessment | No | No |
| **Risk Management** | Educational Focus | Realistic Simulation | Real Risk |
| **Market Data** | Simulated | Real | Real |
| **Execution Delay** | None | Realistic | Real |
| **Cost** | Free (Learning) | Free (Simulation) | Real Commissions |

### Standardized Interface
All execution interfaces implement the `TradingExecutionInterface`:
- `place_order(order)` - Submit buy/sell orders
- `cancel_order(order_id)` - Cancel pending orders
- `get_order(order_id)` - Get order status
- `get_account()` - Account balances and info
- `get_positions()` - Current holdings
- `get_order_history()` - Historical orders
- `is_market_open()` - Market status checks

## Core Components

### Agent Engine (`quantchain.core.agent_engine`)
The central agent framework using LangGraph for stateful reasoning loops, memory management, and tool integration.

### LLM Providers (`quantchain.core.llm_providers`)
Model-agnostic LLM support with providers for:
- OpenAI GPT models
- Anthropic Claude models
- Local Ollama models
- vLLM served models

### RAG System (`quantchain.core.rag_system`)
Vector-based retrieval-augmented generation for market data caching using ChromaDB and sentence transformers.

### Reflection Engine (`quantchain.core.reflection`)
Performance analysis and insights generation for continuous agent improvement.

## Development

This project follows Test-Driven Development (TDD) and Specification-Driven Development (SDD):

1. Create specifications in `/specs/` before implementation
2. Write failing tests in `/tests/` before code
3. Implement code to make tests pass
4. Maintain 80%+ test coverage

### Pre-commit Hooks

Install pre-commit hooks to automatically run quality checks:

```bash
pre-commit install
```

The hooks will run black, flake8, and mypy on each commit.

### Code Quality

```bash
# Format code
black .

# Lint code
flake8 --max-line-length=88 quantchain tests

# Type check
mypy quantchain

# Run tests with coverage
pytest --cov=quantchain --cov-report=html --cov-report=term

# Run tests in parallel (3-4x faster on multi-core machines)  
pytest -n auto --cov=quantchain --cov-report=html --cov-report=term

# Run only unit tests in parallel
pytest -m unit -n auto --cov=quantchain --cov-report=html --cov-report=term

# Run only integration tests in parallel
pytest -m integration -n auto --cov=quantchain --cov-report=html --cov-report=term

# Run tests without slow tests (faster for PRs)
pytest -m "not slow" -n auto --cov=quantchain --cov-report=html --cov-report=term

# Run tests with intelligent caching for even faster subsequent runs
pytest --cache-show -n auto --cov=quantchain --cov-report=html --cov-report=term

# Run specific test file in parallel
pytest tests/core/test_config.py -n auto --cov=quantchain --cov-report=term

# Generate coverage report without running tests
pytest --cov=quantchain --cov-report=html --cov-fail-under=80
```

### Testing Framework Features

The QuantChain testing framework includes:

#### 🚀 **Parallel Execution**
- **pytest-xdist**: Automatic multi-core test execution
- **5 workers** by default on most systems
- **3-4x faster** test execution on multi-core machines
- **Load balancing** for optimal test distribution

#### 💾 **Intelligent Caching**
- **pytest cache**: Avoids redundant test execution
- **Dependency caching** in CI/CD pipelines
- **Smart cache invalidation** based on code changes
- **Faster feedback cycles** during development

#### 📊 **Comprehensive Coverage**
- **82% test coverage** achieved (exceeds 80% requirement)
- **636 passing tests**, 12 skipped
- **HTML coverage reports** with detailed line-by-line analysis
- **Coverage guards** on CI to maintain quality standards

#### 🏷️ **Test Categorization**
- **Unit tests**: Fast, isolated tests with mocked dependencies
- **Integration tests**: Component interaction tests  
- **Slow tests**: Performance-intensive tests (backtesting, complex scenarios)
- **Selective execution**: Run only specific test categories when needed

#### 🛠️ **Developer Tools**
- **pytest-mock**: Comprehensive mocking support
- **pytest-cov**: Coverage reporting and HTML output
- **pytest-timeout**: Prevents hung tests
- **Rich fixtures**: Shared test data and setup utilities

Current test coverage: **82%**

### Security & CI/CD

- GitHub Actions workflows are pinned to commit SHAs for security
- Pre-commit hooks enforce code quality on commits
- Automated testing, linting, and type checking on all PRs
- **Parallel test execution** splits tests into fast unit tests and slower integration tests
- **Dependency caching** speeds up CI runs by 30-60 seconds
- **Test categorization** using markers: `unit`, `integration`, `slow`, `requires_backtestingpy`

#### Test Markers
- `@pytest.mark.unit`: Fast, isolated tests with mocked dependencies
- `@pytest.mark.integration`: Component interaction tests (can be slower)
- `@pytest.mark.slow`: Performance-intensive tests (backtesting, complex scenarios)  
- `@pytest.mark.requires_backtestingpy`: Tests requiring Backtesting.py library

## Usage

### Basic Agent Usage

```python
from quantchain.core import QuantChainAgent, get_config

# Load configuration
config = get_config('config.yaml')

# Initialize an agent
agent = QuantChainAgent(config)

# Run agent with input
response = agent.run({"query": "Analyze AAPL stock trends"})
print(f"Agent response: {response.final_answer}")

# Generate performance reflection
report = agent.reflect()
print(f"Insights: {report.insights}")
```

### Advanced Usage with RAG

```python
from quantchain.core import MarketDataRAG, ChromaVectorStore, SentenceTransformerProvider

# Initialize RAG system components
vector_store = ChromaVectorStore(persist_directory="./data/market_data")
embedding_provider = SentenceTransformerProvider(model_name="all-MiniLM-L6-v2")
rag = MarketDataRAG(vector_store, embedding_provider)

# Store market data
from quantchain.core import MarketData
from datetime import datetime

data = MarketData(
    symbol="AAPL",
    timestamp=datetime.now(),
    data_type="price",
    content={"price": 150.0, "volume": 1000000}
)
rag.store_market_data(data)

# Query with RAG augmentation
augmented_prompt = rag.generate_augmented_prompt(
    "What are the current market conditions?",
    "AAPL price and volume analysis"
)
```

## Contributing

1. Follow the development workflow in `AGENTS.md`
2. Create specifications before implementing features
3. Write comprehensive tests
4. Maintain code quality standards
5. Submit pull requests with detailed descriptions

## License

MIT License - see LICENSE file for details.

## Security

QuantChain includes a comprehensive security module for managing API credentials:

- **Secure API Key Management**: Environment variables and .env file support
- **Credential Validation**: Format validation for major financial services
- **Production Ready**: Support for cloud secret managers (AWS, GCP, Vault)

See `quantchain/core/security.py` for implementation details.

## Disclaimer

This software is for educational and research purposes. Use at your own risk. Not financial advice.
