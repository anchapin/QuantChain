# Tech Stack for QuantChain

Based on the Product Requirements Document (PRD) and AGENTS.md, the following tech stack is recommended for the QuantChain project.

## Programming Language
- **Python**: The primary language for all components, as specified in the PRD.

## Development Workflow & Quality Assurance
- **Testing Framework**: `pytest` for unit, integration, and backtesting tests.
- **Code Coverage**: `pytest-cov` with a minimum requirement of 80% coverage.
- **Linting**: `flake8` for code quality checks.
- **Formatting**: `black` for automatic code formatting.
- **Type Checking**: `mypy` for static type analysis.
- **CI/CD**: GitHub Actions for automated testing, linting, and quality checks.
- **Development Approach**: Test-Driven Development (TDD) or Spec-Driven Development (SDD), with specifications in `/specs/` and tests in `/tests/`.

## Core Frameworks & Libraries
- **Agentic Framework**: LangGraph (within LangChain ecosystem) for stateful agent reasoning, memory, and reflection.
- **Local LLM Serving**:
  - `vLLM` for high-throughput, multi-agent batching.
  - `Ollama` (with `llama.cpp`/`GGUF`) for low-latency quantized models.
- **Backtesting Engine**: `Backtesting.py` or a custom vector-based implementation.
- **Reinforcement Learning Integration**: `FinRL` environment for RL-based agent testing.
- **Model Fine-Tuning**: Parameter-efficient fine-tuning (PEFT) with `QLoRA`, and post-training quantization to `GPTQ` or `GGUF` formats.

## Data & Execution
- **Data Connectors**:
  - Equities/Forex: `Alpha Vantage`, `Polygon.io`
  - Cryptocurrency: `Alpaca` (WebSocket), `Dexscreener`, `ccxt`
  - Alternative Data: Custom scrapers for financial news and social media (Telegram, Discord)
- **Execution Tools**:
  - `Alpaca` for paper and live trading.
  - `Interactive Brokers` via `ib_async`.
- **Technical Analysis Tools**: Pre-built functions like `get_technical_indicator`, `get_news_sentiment`, `analyze_on_chain_data`.

## Storage & Caching
- **Vector Store (RAG)**: Local vector store for retrieval-augmented generation (e.g., `ChromaDB` or `FAISS` for market data and news sentiment caching).
- **Caching**: Market-state-aware caching system to minimize LLM inference calls.

## Web Dashboard & Visualization
- **Web Framework**: `Streamlit` or `Plotly Dash` for the user interface.
- **Visualization**: `Plotly` for interactive charts, equity curves, and performance metrics.
- **Monitoring**: Live reasoning log, multi-agent visualization, and real-time P/L tracking.

## Deployment & Environment
- **Containerization**: `Docker` and `docker-compose` for reproducible deployments.
- **GPU Support**: NVIDIA container toolkit (CUDA) for GPU-accelerated LLM serving.
- **Environment Management**: `conda` or `venv` for virtual environments.
- **Hardware Guidelines**: Documentation for VRAM requirements with common quantized models (e.g., 4-bit/8-bit `DeepSeek-R1-0528`, `Qwen3-235B-Instruct-2507`).

## Security
- **Secret Management**: `python-dotenv` for environment variables, with recommendations for `Vault` or cloud secret managers (AWS/GCP) in production.
- **API Key Management**: Dedicated secure module for handling broker and data feed credentials.

## Project Structure
- `/quantchain/`: Main source code
  - `/agents/`: Agent implementations
  - `/tools/`: Tool and data library components
  - `/connectors/`: Data feed connectors
  - `/backtesting/`: Backtesting engine
  - `/core/`: Core agent engine and shared utilities
- `/specs/`: Specification files for components and agents
- `/tests/`: Test suites (unit, integration, backtests)
- `/docs/`: Documentation
- `/examples/`: Sample agents and configurations

This tech stack ensures modularity, security, and ease of use while supporting the complex requirements of LLM-based trading agents.
