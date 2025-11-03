# QuantChain

A financial framework for building quantitative trading agents using LangGraph and modern AI technologies.

## Features

- **Agentic Framework**: Built on LangGraph for stateful agent reasoning and memory
- **Multiple LLM Support**: Local LLMs via vLLM/Ollama, with GPU acceleration support
- **Comprehensive Data Connectors**: Alpaca, Alpha Vantage, Polygon.io, Dexscreener, CCXT
- **Backtesting Engine**: Vector-based backtesting with FinRL integration
- **Production Ready**: Docker deployment, GPU support, secure API key management

## Installation

### Prerequisites

- Python 3.8+
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

## Development

This project follows Test-Driven Development (TDD) and Specification-Driven Development (SDD):

1. Create specifications in `/specs/` before implementation
2. Write failing tests in `/tests/` before code
3. Implement code to make tests pass
4. Maintain 80%+ test coverage

### Code Quality

```bash
# Format code
black .

# Lint code
flake8 quantchain tests

# Type check
mypy quantchain

# Run tests
pytest --cov=quantchain
```

## Usage

```python
from quantchain import agents, core

# Load configuration
config = core.get_config('config.yaml')

# Initialize an agent
agent = agents.zoo.MemecoinVibeTrader(config)

# Run backtest
results = agent.backtest(start_date='2024-01-01', end_date='2024-12-31')
print(f"Final balance: ${results.final_balance}")
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
