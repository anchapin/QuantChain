# QuantChain Context for Gemini

## Project Overview
**QuantChain** is a financial framework for building quantitative trading agents using **LangGraph** and modern AI technologies (LLMs). It features a RAG system for market data, multiple LLM support (OpenAI, Anthropic, Local), and a comprehensive backtesting engine.

## Technology Stack
*   **Core:** Python 3.10+ (3.12 recommended)
*   **AI/Agents:** LangGraph, LangChain, OpenAI, Anthropic, Ollama, vLLM
*   **Data/Vector DB:** ChromaDB, Sentence Transformers, Pandas, NumPy
*   **Financial:** Alpaca-py, CCXT, Backtesting.py, FinRL, QuantStats
*   **Web/UI:** Streamlit, Plotly
*   **Infrastructure:** Docker, Docker Compose, Nginx, PostgreSQL, Redis

## Key Directory Structure
*   `quantchain/` - Main package source code.
    *   `agents/` - Trading agent implementations.
    *   `core/` - Core framework (Agent Engine, RAG, LLM Providers).
    *   `connectors/` - Data source connectors (Alpaca, Dexscreener).
    *   `tools/` - Utility functions and execution tools.
    *   `backtesting/` - Backtesting engine integration.
*   `tests/` - Test suite (Unit, Integration, Slow).
*   `docs/` - Detailed documentation (Deployment, Setup, etc.).
*   `examples/` - Usage examples and configurations.
*   `specs/` - Design specifications (SDD).

## Common Development Tasks

### 1. Environment Setup
*   **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    # or specific groups
    pip install -r requirements-dev.txt
    ```
*   **Configuration:**
    Copy `config.example.yaml` to `config.yaml` and `.env.example` to `.env`.

### 2. Testing (`pytest`)
*   **Run All Tests:**
    ```bash
    pytest
    ```
*   **Run Unit Tests (Fast):**
    ```bash
    pytest -m unit
    ```
*   **Run Integration Tests:**
    ```bash
    pytest -m integration
    ```
*   **Run with Coverage:**
    ```bash
    pytest --cov=quantchain --cov-report=term-missing
    ```
*   **Run in Parallel (Recommended):**
    ```bash
    pytest -n auto
    ```

### 3. Linting & Formatting
*   **Format Code:**
    ```bash
    black .
    ```
*   **Lint:**
    ```bash
    flake8 --max-line-length=88 quantchain tests
    ```
*   **Type Check:**
    ```bash
    mypy quantchain
    ```
*   **Pre-commit:**
    ```bash
    pre-commit run --all-files
    ```

### 4. Running the Application
*   **Docker (GPU):**
    ```bash
    docker compose -f docker-compose.gpu.yml up --build
    ```
*   **Docker (CPU):**
    ```bash
    docker compose up --build
    ```
*   **Local Agent Example:**
    ```bash
    python examples/memecoin_vibe_trader_example.py
    ```

## Architecture Highlights
*   **Agent Engine:** Built on LangGraph for stateful, cyclic reasoning.
*   **RAG System:** Uses ChromaDB to cache and retrieve market data for context-aware decision making.
*   **Connectors:** Standardized `DataFeedInterface` and `TradingExecutionInterface` allow swapping providers (e.g., Alpaca vs. Paper Trading).
*   **Tutorial Mode:** A specialized mode for human learning with feedback loops.

## Development Conventions
*   **Testing:** Aim for >80% coverage. Use `pytest` markers (`@pytest.mark.unit`, etc.).
*   **SDD:** Create specifications in `specs/` before implementing complex features.
*   **CI/CD:** GitHub Actions validate all PRs (Lint, Test, Type Check).
