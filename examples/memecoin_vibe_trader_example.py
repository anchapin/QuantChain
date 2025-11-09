"""Example script demonstrating the Memecoin Vibe Trader agent.

This example shows how to set up and run the Memecoin Vibe Trader that:
1. Scans Dexscreener for new tokens
2. Analyzes social sentiment from various platforms
3. Uses LLM to assess "vibe" and make trading decisions
4. Executes trades via Alpaca with proper risk management

Requirements:
- Alpaca API keys for trading (set ALPACA_API_KEY and ALPACA_API_SECRET in .env)
- LLM provider key (OPENAI_API_KEY or ANTHROPIC_API_KEY in .env)
- Optional: Social media API keys for enhanced sentiment analysis
"""

import logging
import os
import sys
from pathlib import Path

# Add project root to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from quantchain.agents.memecoin_vibe_trader import (
    MemecoinVibeTrader,
    MemecoinVibeTraderConfig,
)
from quantchain.connectors.dexscreener_connector import DexscreenerDataConnector
from quantchain.tools.social_media_scraper import SocialMediaScraper
from quantchain.tools.execution import AlpacaExecutionTool
from quantchain.core.config import get_config, QuantChainConfig
from quantchain.core.llm_providers import (
    OpenAIProvider,
    AnthropicProvider,
    OllamaProvider,
)


def load_configuration() -> "QuantChainConfig":
    """Load QuantChain configuration and validate required API keys.

    Returns:
        QuantChainConfig: The loaded configuration object

    Raises:
        ValueError: If required API keys are missing
    """
    try:
        config = get_config()
    except Exception as e:
        raise ValueError(f"Failed to load configuration: {e}")

    # Validate required API keys
    required_keys = {
        "ALPACA_API_KEY": "Alpaca trading API key",
        "ALPACA_API_SECRET": "Alpaca trading API secret",
    }

    missing_keys = []
    for key, description in required_keys.items():
        if not os.getenv(key):
            missing_keys.append(f"{key} ({description})")

    if missing_keys:
        raise ValueError(
            f"Missing required environment variables:\n"
            + "\n".join(f"  - {key}" for key in missing_keys)
            + "\n\nPlease set these in your .env file."
        )

    # Check for LLM provider configuration
    if not hasattr(config, "llm") or not config.llm:
        raise ValueError("LLM configuration not found in config.yaml")

    return config


def initialize_agent(config: "QuantChainConfig") -> MemecoinVibeTrader:
    """Initialize the Memecoin Vibe Trader with all required components.

    Args:
        config: QuantChain configuration object

    Returns:
        MemecoinVibeTrader: Initialized agent instance

    Raises:
        ValueError: If initialization fails
    """
    try:
        # Create agent configuration with sensible defaults
        agent_config = MemecoinVibeTraderConfig(
            scan_interval=3600,  # 1 hour between scans
            max_positions=5,
            max_allocation_per_trade=0.02,  # 2% of portfolio per trade
            min_liquidity_threshold=10000,  # $10,000 minimum liquidity
            min_vibe_score_threshold=70,  # Require high vibe score to trade
            risk_tolerance="MEDIUM",
            time_window="1h",  # Look for tokens from last hour
        )

        # Initialize data connector (no API key required for Dexscreener)
        dex_connector = DexscreenerDataConnector()

        # Initialize social media scraper with available credentials
        social_scraper = SocialMediaScraper(
            twitter_api_key=os.getenv("TWITTER_API_KEY"),
            twitter_api_secret=os.getenv("TWITTER_API_SECRET"),
            telegram_bot_token=os.getenv("TELEGRAM_BOT_TOKEN"),
        )

        # Initialize Alpaca execution tool
        execution_tool = AlpacaExecutionTool(
            api_key=os.getenv("ALPACA_API_KEY"),
            api_secret=os.getenv("ALPACA_API_SECRET"),
            paper_trading=(
                config.trading.paper_trading if hasattr(config, "trading") else True
            ),
            base_url=os.getenv("ALPACA_BASE_URL", "https://paper-api.alpaca.markets"),
        )

        # Initialize LLM provider based on configuration
        llm_provider = None
        if hasattr(config.llm, "provider"):
            provider_name = config.llm.provider.lower()

            if provider_name == "openai":
                if not os.getenv("OPENAI_API_KEY"):
                    raise ValueError("OPENAI_API_KEY required for OpenAI provider")
                llm_provider = OpenAIProvider(
                    api_key=os.getenv("OPENAI_API_KEY"),
                    model=config.llm.model or "gpt-4",
                    temperature=config.llm.temperature or 0.7,
                    max_tokens=config.llm.max_tokens or 500,
                )

            elif provider_name == "anthropic":
                if not os.getenv("ANTHROPIC_API_KEY"):
                    raise ValueError(
                        "ANTHROPIC_API_KEY required for Anthropic provider"
                    )
                llm_provider = AnthropicProvider(
                    api_key=os.getenv("ANTHROPIC_API_KEY"),
                    model=config.llm.model or "claude-3-opus-20240229",
                    temperature=config.llm.temperature or 0.7,
                    max_tokens=config.llm.max_tokens or 500,
                )

            elif provider_name == "ollama":
                llm_provider = OllamaProvider(
                    model=config.llm.model or "llama2:7b",
                    temperature=config.llm.temperature or 0.7,
                    max_tokens=config.llm.max_tokens or 500,
                )

            else:
                raise ValueError(f"Unsupported LLM provider: {provider_name}")

        # Create and return the agent
        agent = MemecoinVibeTrader(
            config=agent_config,
            dex_connector=dex_connector,
            social_scraper=social_scraper,
            execution_tool=execution_tool,
            llm=llm_provider,
        )

        return agent

    except Exception as e:
        raise ValueError(f"Failed to initialize agent: {e}")


def main() -> None:
    """Main execution function for the Memecoin Vibe Trader example."""
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    logger = logging.getLogger(__name__)

    try:
        # Load configuration
        logger.info("Loading configuration...")
        config = load_configuration()
        logger.info("Configuration loaded successfully")

        # Initialize agent
        logger.info("Initializing Memecoin Vibe Trader...")
        agent = initialize_agent(config)
        logger.info("Agent initialized successfully")

        # Run one trading cycle
        logger.info("Starting trading cycle...")
        results = agent.run_cycle()

        # Display results
        print("\n" + "=" * 50)
        print("MEMECOIN VIBE TRADER - CYCLE RESULTS")
        print("=" * 50)
        print(f"Success: {'Yes' if results['success'] else 'No'}")
        print(f"Tokens Scanned: {results['tokens_scanned']}")
        print(f"Assessments Made: {results['assessments_made']}")
        print(f"Trades Executed: {results['trades_executed']}")

        if results.get("error_message"):
            print(f"\nError: {results['error_message']}")

        if results.get("trades"):
            print("\nExecuted Trades:")
            for trade in results["trades"]:
                print(
                    f"  - {trade['token']}: {trade['quantity']} shares "
                    f"(Vibe Score: {trade['vibe_score']})"
                )

        # Print important safety information
        print("\n" + "=" * 50)
        print("SAFETY REMINDER")
        print("=" * 50)
        print("• This is running in PAPER TRADING mode")
        print("• No real money is being used")
        print("• Always do your own research before investing")
        print("• This is educational purposes only")

    except Exception as e:
        logger.error(f"Error running Memecoin Vibe Trader: {str(e)}")
        print(f"\nError: {str(e)}")
        print("\nTroubleshooting:")
        print("1. Ensure all required API keys are set in .env file")
        print("2. Check that config.yaml exists and is valid")
        print("3. Verify network connectivity")
        print("4. Review logs above for specific error details")
        sys.exit(1)


if __name__ == "__main__":
    main()
