"""Factory for creating trading execution interfaces."""

from ..core.config import QuantChainConfig
from ..core.exceptions import AuthenticationError, ConfigurationError
from .trading_execution import TradingExecutionInterface
from ..connectors.alpaca_execution import AlpacaExecutionConnector
from .paper_trading import PaperTradingExecutor
from .tutorial_mode import TutorialExecutor


def create_execution_interface(config: QuantChainConfig) -> TradingExecutionInterface:
    """Create the appropriate trading execution interface based on configuration.

    Args:
        config: QuantChain configuration object

    Returns:
        TradingExecutionInterface implementation

    Raises:
        ConfigurationError: When broker configuration is invalid
        AuthenticationError: When API keys are missing for live brokers
    """
    broker = config.get("trading.default_broker", "alpaca")
    paper_trading = config.get("trading.paper_trading", True)
    tutorial_mode = config.get("tutorial.enabled", False)
    
    # Tutorial mode takes precedence
    if tutorial_mode or broker == "tutorial":
        # Get tutorial configuration
        initial_cash = config.get("trading.initial_cash", 100000.0)
        
        # Tutorial mode configuration options
        tutorial_config = {
            "learning_objectives": config.get("tutorial.learning_objectives", []),
            "session_duration": config.get("tutorial.session_duration", 3600),
            "feedback_level": config.get("tutorial.feedback_level", "detailed"),
            "track_mistakes": config.get("tutorial.track_mistakes", True),
            "analyze_market_drivers": config.get("tutorial.analyze_market_drivers", True),
            "commission_per_trade": config.get("trading.commission_per_trade", 0.0),
            "commission_per_share": config.get("trading.commission_per_share", 0.0),
        }
        
        return TutorialExecutor(initial_cash=initial_cash, config=config, **tutorial_config)

    if broker == "alpaca":
        # Get API credentials
        api_key = config.get_api_key("alpaca")
        api_secret = config.get_api_key("alpaca_secret")

        # For paper trading, check for credentials or raise proper error
        if not api_key or not api_secret:
            if paper_trading:
                raise AuthenticationError(
                    "Alpaca API credentials required for paper trading. "
                    "Set ALPACA_API_KEY and ALPACA_API_SECRET environment variables, "
                    "or configure them in your config file."
                )
            else:
                raise AuthenticationError(
                    "Alpaca API key and secret required for live trading. "
                    "Set ALPACA_API_KEY and ALPACA_API_SECRET environment variables."
                )

        # At this point, both api_key and api_secret are guaranteed to be strings
        assert api_key is not None
        assert api_secret is not None

        return AlpacaExecutionConnector(
            api_key=api_key, api_secret=api_secret, use_paper=paper_trading
        )

    elif broker == "paper":
        # Standalone paper trading - ignore paper_trading flag
        return PaperTradingExecutor()

    else:
        raise ConfigurationError(
            f"Unsupported broker: {broker}. Supported: alpaca, paper, tutorial"
        )
