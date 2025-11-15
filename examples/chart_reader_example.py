"""Example script demonstrating the Chart Reader Agent with multimodal analysis.

This example shows how to set up and run the Chart Reader Agent that:
1. Fetches historical price data for a specified symbol
2. Calculates technical indicators (SMA, EMA, RSI, MACD, Bollinger Bands)
3. Renders candlestick charts with indicators
4. Uses vision models to identify chart patterns
5. Generates consolidated trading recommendations

Requirements:
- Alpaca API keys for data (set ALPACA_API_KEY and ALPACA_API_SECRET in .env)
- Vision-enabled LLM (OpenAI GPT-4 Vision recommended)
- Additional dependencies: pip install pandas matplotlib mplfinance
"""

import argparse
import importlib.util
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

# Add project root to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from quantchain.agents.chart_reader_agent import (
    ChartReaderAgent,
    ChartReaderAgentConfig,
)
from quantchain.connectors.alpaca_connector import AlpacaDataConnector
from quantchain.core.config import QuantChainConfig, get_config
from quantchain.core.llm_providers import AnthropicProvider, OpenAIProvider


def check_dependencies() -> bool:
    """Check if required dependencies for chart rendering are installed.

    Returns:
        bool: True if all dependencies are available, False otherwise
    """
    missing_deps = []

    # Check if pandas is available
    if not importlib.util.find_spec("pandas"):
        missing_deps.append("pandas")

    # Check if matplotlib is available
    if not importlib.util.find_spec("matplotlib"):
        missing_deps.append("matplotlib")

    # Check if mplfinance is available
    if not importlib.util.find_spec("mplfinance"):
        missing_deps.append("mplfinance")

    if missing_deps:
        print("Missing required dependencies for chart rendering:")
        for dep in missing_deps:
            print(f"  - {dep}")
        print("\nInstall with: pip install " + " ".join(missing_deps))
        return False

    return True


def load_configuration() -> "QuantChainConfig":
    """Load QuantChain configuration and validate requirements.

    Returns:
        QuantChainConfig: The loaded configuration object

    Raises:
        ValueError: If required configuration is missing
    """
    try:
        config = get_config()
    except Exception as e:
        raise ValueError(f"Failed to load configuration: {e}") from e

    # Validate Alpaca API keys (required for data)
    if not os.getenv("ALPACA_API_KEY") or not os.getenv("ALPACA_API_SECRET"):
        raise ValueError(
            "Alpaca API keys are required for data access.\n"
            "Set ALPACA_API_KEY and ALPACA_API_SECRET in your .env file."
        )

    # Validate LLM provider configuration
    if not hasattr(config, "llm") or not config.llm:
        raise ValueError("LLM configuration not found in config.yaml")

    return config


def initialize_agent(config: "QuantChainConfig") -> ChartReaderAgent:
    """Initialize the Chart Reader Agent with all required components.

    Args:
        config: QuantChain configuration object

    Returns:
        ChartReaderAgent: Initialized agent instance

    Raises:
        ValueError: If initialization fails
    """
    try:
        # Create agent configuration with technical analysis settings
        agent_config = ChartReaderAgentConfig(
            timeframes=["15m", "1h", "4h", "1d"],
            patterns_enabled=[
                "head_and_shoulders",
                "double_top",
                "double_bottom",
                "triangle",
                "flag",
                "pennant",
                "wedge",
                "channel",
            ],
            indicators_enabled=[
                "SMA",
                "EMA",
                "RSI",
                "MACD",
                "Bollinger_Bands",
                "Volume",
            ],
            min_pattern_confidence=70.0,
            min_confluence_score=60.0,
            vision_model_provider=getattr(config.llm, "provider", "openai"),
            vision_model_name=getattr(config.llm, "model", "gpt-4-vision-preview"),
            chart_width=800,
            chart_height=600,
        )

        # Initialize Alpaca data connector
        data_connector = AlpacaDataConnector(
            api_key=os.getenv("ALPACA_API_KEY"),
            api_secret=os.getenv("ALPACA_API_SECRET"),
            base_url=os.getenv(
                "ALPACA_DATA_URL",
                "https://data.alpaca.markets" if os.getenv("ALPACA_API_KEY") else None,
            ),
        )

        # Initialize vision-enabled LLM provider
        llm_provider = None
        provider_name = getattr(config.llm, "provider", "openai").lower()

        if provider_name == "openai":
            if not os.getenv("OPENAI_API_KEY"):
                raise ValueError("OPENAI_API_KEY required for OpenAI Vision model")
            llm_provider = OpenAIProvider(
                api_key=os.getenv("OPENAI_API_KEY"),
                model=getattr(config.llm, "model", "gpt-4-vision-preview"),
                temperature=getattr(config.llm, "temperature", 0.3),
                max_tokens=getattr(config.llm, "max_tokens", 2000),
            )

        elif provider_name == "anthropic":
            if not os.getenv("ANTHROPIC_API_KEY"):
                raise ValueError(
                    "ANTHROPIC_API_KEY required for Anthropic Vision model"
                )
            llm_provider = AnthropicProvider(
                api_key=os.getenv("ANTHROPIC_API_KEY"),
                model=getattr(config.llm, "model", "claude-3-opus-20240229"),
                temperature=getattr(config.llm, "temperature", 0.3),
                max_tokens=getattr(config.llm, "max_tokens", 2000),
            )

        else:
            raise ValueError(
                f"LLM provider '{provider_name}' does not support vision capabilities. "
                "Use OpenAI or Anthropic for chart analysis."
            )

        # Create and return the agent
        agent = ChartReaderAgent(
            config=agent_config,
            data_connector=data_connector,
            llm_provider=llm_provider,
        )

        return agent

    except Exception as e:
        raise ValueError(f"Failed to initialize agent: {e}") from e


def analyze_symbol(
    agent: ChartReaderAgent,
    symbol: str,
    save_output: bool = False
) -> Dict[str, Any]:
    """Analyze a symbol and display the results.

    Args:
        agent: Initialized ChartReaderAgent instance
        symbol: Stock/crypto symbol to analyze
        save_output: Whether to save detailed results to JSON

    Returns:
        Dict: Analysis results
    """
    print(f"\nAnalyzing {symbol}...")
    print("-" * 50)

    try:
        # Generate trading recommendation
        results = agent.generate_trading_recommendation(symbol)

        # Display summary
        _display_summary(symbol, results)

        # Display analysis by timeframe
        _display_timeframe_analysis(results)

        # Display technical indicators summary
        _display_technical_indicators(results)

        # Save results if requested
        if save_output:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{symbol}_analysis_{timestamp}.json"
            with open(filename, "w") as f:
                json.dump(results, f, indent=2)
            print(f"\nResults saved to {filename}")

        return results

    except Exception as e:
        print(f"Error analyzing {symbol}: {e}")
        return {}


def _display_summary(symbol: str, results: Dict[str, Any]) -> None:
    """Display the summary of analysis results."""
    print(f"Symbol: {symbol}")
    print(f"Recommendation: {results['recommendation']}")
    print(f"Confidence: {results['confidence']:.1f}%")

    if "entry_price" in results:
        print(f"Entry Price: ${results['entry_price']:.2f}")
    if "stop_loss" in results:
        print(f"Stop Loss: ${results['stop_loss']:.2f}")
    if "take_profit" in results:
        print(f"Take Profit: ${results['take_profit']:.2f}")


def _display_timeframe_analysis(results: Dict[str, Any]) -> None:
    """Display analysis by timeframe."""
    if "timeframe_analysis" not in results:
        return

    print("\nTimeframe Analysis:")
    for timeframe, analysis in results["timeframe_analysis"].items():
        print(f"\n{timeframe}:")
        print(f"  Signal: {analysis.get('signal', 'N/A')}")
        print(f"  Confidence: {analysis.get('confidence', 0):.1f}%")

        if "patterns_found" in analysis and analysis["patterns_found"]:
            print("  Patterns:")
            for pattern in analysis["patterns_found"]:
                print(
                    f"    - {pattern['name']} "
                    f"({pattern['confidence']:.1f}% confidence)"
                )


def _display_technical_indicators(results: Dict[str, Any]) -> None:
    """Display technical indicators summary."""
    if "indicator_summary" not in results:
        return

    print("\nTechnical Indicators:")
    for indicator, signal in results["indicator_summary"].items():
        print(f"  {indicator}: {signal}")


def main() -> None:
    """Main execution function for the Chart Reader Agent example."""
    # Parse command line arguments

    parser = argparse.ArgumentParser(description="Chart Reader Agent Example")
    parser.add_argument(
        "symbol", nargs="?", default="AAPL", help="Symbol to analyze (default: AAPL)"
    )
    parser.add_argument(
        "--save", action="store_true", help="Save detailed analysis to JSON file"
    )
    args = parser.parse_args()

    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    logger = logging.getLogger(__name__)

    try:
        # Check dependencies
        if not check_dependencies():
            sys.exit(1)

        # Load configuration
        logger.info("Loading configuration...")
        config = load_configuration()
        logger.info("Configuration loaded successfully")

        # Initialize agent
        logger.info("Initializing Chart Reader Agent...")
        agent = initialize_agent(config)
        logger.info("Agent initialized successfully")

        # Analyze the symbol
        results = analyze_symbol(agent, args.symbol, args.save)

        if results:
            # Print important safety information
            print("\n" + "=" * 50)
            print("IMPORTANT NOTES")
            print("=" * 50)
            print("• This is technical analysis for educational purposes")
            print("• Not financial advice - always do your own research")
            print("• Consider multiple timeframes and risk factors")
            print("• Past performance does not guarantee future results")

    except Exception as e:
        logger.error(f"Error running Chart Reader Agent: {str(e)}")
        print(f"\nError: {str(e)}")
        print("\nTroubleshooting:")
        print("1. Ensure all required API keys are set in .env file")
        print("2. Check that config.yaml exists and is valid")
        print("3. Verify required dependencies are installed")
        print("4. Check the symbol is valid and supported by Alpaca")
        sys.exit(1)


if __name__ == "__main__":
    main()
