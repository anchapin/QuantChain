# QuantChain

A financial framework for building quantitative trading agents using LangGraph and modern AI technologies.

## Features

- **Agentic Framework**: Built on LangGraph for stateful agent reasoning and memory
- **Multiple LLM Support**: OpenAI, Anthropic, and local LLMs via vLLM/Ollama with GPU acceleration
- **RAG System**: Vector-based market data caching and retrieval-augmented generation
- **Reflective Performance Analysis**: Agent self-analysis and strategy optimization
- **Comprehensive Data Connectors**: Alpaca, Alpha Vantage, Polygon.io, Dexscreener, CCXT
- **Backtesting Engine**: Vector-based backtesting with FinRL integration
- **Production Ready**: Docker deployment, GPU support, secure API key management

## Installation

### Prerequisites

- Python 3.9+
- Git
- (Optional) CUDA-compatible GPU for LLM acceleration

### Setup

1. Clone the repository:
```bash
git clone https://github.com/anchapin/QuantChain.git
cd QuantChain
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. (Optional) Install additional dependencies for specific features:
```bash
# For backtesting
pip install backtesting

# For LLM serving
pip install vllm ollama

# For data connectors
pip install alpaca-py ccxt

# For web dashboard
pip install streamlit plotly
```

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
pytest --cov=quantchain --cov-report=term
```

Current test coverage: **100%**

### Security & CI/CD

- GitHub Actions workflows are pinned to commit SHAs for security
- Pre-commit hooks enforce code quality on commits
- Automated testing, linting, and type checking on all PRs

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
from quantchain.core import MarketDataRAG, create_llm_provider

# Initialize RAG system
llm = create_llm_provider("ollama", model="llama2:7b")
rag = MarketDataRAG(llm)  # Simplified for example

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

## Disclaimer

This software is for educational and research purposes. Use at your own risk. Not financial advice.
