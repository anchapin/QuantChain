# QuantChain Examples

This directory contains ready-to-run example scripts demonstrating the QuantChain "Agent Zoo" - pre-built trading and analysis agents designed to lower the barrier to entry for new users.

## Introduction

The examples showcase the three main agent types from the Agent Zoo:
- **Memecoin Vibe Trader**: Scans DEXs for new tokens, analyzes social sentiment, and executes trades based on AI "vibe" assessment
- **Chart Reader Agent**: Performs multimodal technical analysis using vision models to identify chart patterns
- **Smart Contract Auditor**: Audits Solidity contracts for security vulnerabilities and analyzes tokenomics

## Prerequisites

- Python 3.10+
- Required dependencies from `requirements.txt`
- API keys for desired services (see [Configuration Guide](#configuration-guide))
- Optional dependencies for specific agents:
  - Chart Reader Agent: `pandas`, `matplotlib`, `mplfinance`

## Quick Start Guide

1. **Copy and configure your environment:**
   ```bash
   cp config.example.yaml config.yaml
   cp examples/.env.example .env
   ```

2. **Edit `.env` to add your API keys:**
   - Required for trading: `ALPACA_API_KEY`, `ALPACA_API_SECRET`
   - Required for LLM: `OPENAI_API_KEY` or `ANTHROPIC_API_KEY`
   - Required for contract audit: `ETHERSCAN_API_KEY`

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   # For Chart Reader Agent:
   pip install pandas matplotlib mplfinance
   ```

4. **Run your first example:**
   ```bash
   python examples/memecoin_vibe_trader_example.py
   ```

## Available Examples

| Agent Name | Description | Script | Required API Keys | Difficulty |
|------------|-------------|---------|-------------------|------------|
| Memecoin Vibe Trader | AI-driven memecoin trading with social sentiment analysis | `memecoin_vibe_trader_example.py` | Alpaca, LLM | Beginner |
| Chart Reader Agent | Multimodal technical analysis using vision models | `chart_reader_example.py` | Alpaca, Vision LLM | Intermediate |
| Smart Contract Auditor | Security vulnerability scanning and tokenomics analysis | `smart_contract_auditor_example.py` | Blockchain Explorer, LLM | Advanced |

### Memecoin Vibe Trader

The Memecoin Vibe Trader demonstrates:
- Automated scanning of DEXs for new tokens
- Social media sentiment analysis
- AI-powered "vibe" assessment using LLMs
- Risk-aware position sizing and portfolio management

**Use Case**: Ideal for traders interested in emerging cryptocurrency trends with automated risk management.

### Chart Reader Agent

The Chart Reader Agent showcases:
- Technical indicator calculation (SMA, EMA, RSI, MACD, Bollinger Bands)
- Chart pattern recognition (head and shoulders, triangles, flags, etc.)
- Multimodal vision-based analysis
- Multi-timeframe analysis consolidation

**Use Case**: Perfect for technical analysts who want to combine traditional indicators with AI-powered pattern recognition.

### Smart Contract Auditor

The Smart Contract Auditor provides:
- Automated vulnerability scanning (reentrancy, access control, arithmetic errors)
- Tokenomics analysis and financial metrics
- Contract source code retrieval and analysis
- Investment recommendations based on security and financial scores

**Use Case**: Essential for DeFi investors and developers who need to assess contract security before investing or integrating.

## Configuration Guide

### Main Configuration

Copy `config.example.yaml` to `config.yaml` and customize:

```yaml
llm:
  provider: openai  # or anthropic, ollama
  model: gpt-4  # or claude-3-opus, llama2:7b
  temperature: 0.7
  max_tokens: 1000

data:
  default_provider: alpaca
  cache_enabled: true
  cache_dir: ./data/cache

trading:
  default_broker: alpaca
  paper_trading: true  # IMPORTANT: Keep true for testing
  max_position_size: 0.1
  initial_cash: 100000.0
```

### Example-Specific Configurations

Example configurations are provided in the `config_examples/` directory:

- `memecoin_trader.yaml` - Optimized for memecoin trading with higher risk settings
- `chart_reader.yaml` - Configured for technical analysis with vision model settings
- `contract_auditor.yaml` - Set up for security analysis with blockchain explorer settings

To use an example configuration:
```bash
cp examples/config_examples/memecoin_trader.yaml config.yaml
```

## Safety and Disclaimers

⚠️ **IMPORTANT SAFETY WARNINGS:**

1. **Always use paper trading mode** when testing (set `paper_trading: true` in config)
2. **Never use real funds** without thorough testing and understanding
3. **Educational purposes only** - these examples are for learning and research
4. **Not financial advice** - always do your own research before investing
5. **Smart Contract Auditor limitations** - automated audits are not a substitute for professional security audits

## Next Steps

- **Main Documentation**: `/docs/` for detailed guides
- **Agent Specifications**: `/specs/agents/` for technical details
- **Contributing Guidelines**: See the main repository README
- **Community Resources**: Join our Discord and follow on Twitter

## Troubleshooting

### Common Issues

1. **Missing API Keys**
   ```
   Error: API key not found in environment variables
   ```
   Solution: Ensure all required keys are in your `.env` file

2. **Dependency Conflicts**
   ```
   ImportError: No module named 'pandas'
   ```
   Solution: Install missing dependencies with `pip install pandas matplotlib mplfinance`

3. **GPU Requirements for Local LLMs**
   ```
   Error: CUDA out of memory
   ```
   Solution: Use smaller models or switch to cloud-based LLMs

4. **Rate Limiting**
   ```
   Error: API rate limit exceeded
   ```
   Solution: Wait and retry, or upgrade your API plan

### Getting Help

- Check the logs in `./logs/` for detailed error messages
- Review the configuration files for missing settings
- Open an issue on GitHub with error details and configuration

## Contributing to Examples

We welcome contributions to improve these examples! Please:

1. Fork the repository
2. Create a feature branch
3. Add your improvements with clear documentation
4. Submit a pull request with details of changes

Examples of valuable contributions:
- Additional example agents
- Improved error handling
- Additional documentation
- Performance optimizations
- New integration examples
