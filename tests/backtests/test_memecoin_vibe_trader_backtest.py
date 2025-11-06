"""Backtest tests for MemecoinVibeTrader agent."""

import pytest
from unittest.mock import MagicMock
from datetime import datetime, timedelta

from quantchain.agents.memecoin_vibe_trader import (
    MemecoinVibeTrader,
    MemecoinVibeTraderConfig,
    SocialMetrics,
)
from quantchain.connectors.dexscreener_connector import DexscreenerDataConnector
from quantchain.tools.social_media_scraper import SocialMediaScraper
from quantchain.tools.execution import AlpacaExecutionTool


class TestMemecoinVibeTrader:
    """Test suite for MemecoinVibeTrader agent backtesting."""

    @pytest.fixture
    def mock_dex_connector(self) -> MagicMock:
        """Create a mock DexscreenerDataConnector."""
        mock_connector = MagicMock(spec=DexscreenerDataConnector)

        # Mock to return a specific "hyped" token
        mock_connector.get_new_token_pairs.return_value = [
            {
                "address": "0x1234567890123456789012345678901234567890",
                "symbol": "HYPED",
                "name": "HypeToken",
                "liquidity": 50000.0,  # Above $10k threshold
                "volume_24h": 100000.0,
                "created_at": datetime.now() - timedelta(minutes=30),
                "dex": "Uniswap",
                "base_token_address": "0x1234567890123456789012345678901234567890",
                "quote_token_address": "0xA0b86a33E6441F8d9C1E1a5a9C8dF5b6c3D2A1B4",
            }
        ]

        return mock_connector

    @pytest.fixture
    def mock_social_scraper(self) -> MagicMock:
        """Create a mock SocialMediaScraper."""
        mock_scraper = MagicMock(spec=SocialMediaScraper)

        # Mock to return strong social metrics
        mock_scraper.get_social_metrics.return_value = SocialMetrics(
            telegram_followers=15000,
            twitter_followers=25000,
            recent_posts=150,
            engagement_rate=0.085,
            sentiment_score=0.75,
        )

        return mock_scraper

    @pytest.fixture
    def mock_execution_tool(self) -> MagicMock:
        """Create a mock AlpacaExecutionTool."""
        mock_tool = MagicMock(spec=AlpacaExecutionTool)

        # Mock account balance for position sizing
        mock_tool.get_account_balance.return_value = {
            "portfolio_value": 10000.0,
            "cash": 10000.0,
        }

        # Mock empty current positions
        mock_tool.get_positions.return_value = []

        # Mock successful order execution
        mock_order = MagicMock()
        mock_order.order_id = "test_order_123"
        mock_tool.execute_market_order.return_value = mock_order

        return mock_tool

    @pytest.fixture
    def mock_llm(self) -> MagicMock:
        """Create a mock LLM that returns deterministic responses."""
        mock_llm = MagicMock()

        # Create a response mock that will be returned by invoke
        response_mock = MagicMock()
        response_mock.content = """VIBE_SCORE: 85
RECOMMENDATION: BUY
RISK_LEVEL: MEDIUM
REASONING: Strong community presence with high social engagement.
Token shows excellent momentum and viral potential."""

        # Set up invoke to return the response mock
        mock_llm.invoke.return_value = response_mock
        return mock_llm

    @pytest.fixture
    def trader_config(self) -> MemecoinVibeTraderConfig:
        """Create a test configuration for the trader."""
        return MemecoinVibeTraderConfig(
            scan_interval=3600,
            max_positions=5,
            max_allocation_per_trade=0.02,  # 2% per trade
            min_liquidity_threshold=10000.0,
            min_vibe_score_threshold=70.0,
            risk_tolerance="MEDIUM",
            time_window="1h",
        )

    @pytest.fixture
    def memecoin_trader(
        self,
        trader_config: MemecoinVibeTraderConfig,
        mock_dex_connector: MagicMock,
        mock_social_scraper: MagicMock,
        mock_execution_tool: MagicMock,
        mock_llm: MagicMock,
    ) -> MemecoinVibeTrader:
        """Create a fully configured MemecoinVibeTrader with mocked dependencies."""
        return MemecoinVibeTrader(
            config=trader_config,
            dex_connector=mock_dex_connector,
            social_scraper=mock_social_scraper,
            execution_tool=mock_execution_tool,
            llm=mock_llm,
        )

    def test_memecoin_trader_identifies_and_trades_target(
        self,
        memecoin_trader: MemecoinVibeTrader,
        mock_dex_connector: MagicMock,
        mock_social_scraper: MagicMock,
        mock_execution_tool: MagicMock,
        mock_llm: MagicMock,
    ) -> None:
        """Test that the memecoin trader identifies and trades a high-vibe token."""
        # Arrange: The fixtures are already set up to simulate a profitable opportunity

        # Act: Run one complete trading cycle
        results = memecoin_trader.run_cycle()

        # Assert: Verify the complete workflow executed successfully
        assert results["success"] is True, "Trading cycle should complete successfully"
        assert results["tokens_scanned"] == 1, "Should scan exactly one token"
        assert results["assessments_made"] == 1, "Should make exactly one assessment"
        assert results["trades_executed"] == 1, "Should execute exactly one trade"
        assert results["error_message"] is None, "Should have no error messages"
        assert len(results["trades"]) == 1, "Should have one trade in results"

        # Verify the specific trade details
        trade = results["trades"][0]
        assert trade["token"] == "HYPED", "Trade should be for HYPED token"
        assert trade["vibe_score"] == 85, "Trade should have correct vibe score"
        assert (
            trade["order_id"] == "test_order_123"
        ), "Trade should have correct order ID"
        assert "timestamp" in trade, "Trade should have timestamp"

        # Verify that all components were called with correct data
        mock_dex_connector.get_new_token_pairs.assert_called_once_with(time_window="1h")
        mock_social_scraper.get_social_metrics.assert_called_once_with(
            "HYPED", "0x1234567890123456789012345678901234567890"
        )
        mock_execution_tool.get_account_balance.assert_called_once()
        mock_execution_tool.get_positions.assert_called_once()
        mock_execution_tool.execute_market_order.assert_called_once()

        # Verify order execution parameters
        order_call = mock_execution_tool.execute_market_order.call_args
        assert (
            order_call.kwargs["symbol"] == "HYPED/USD"
        ), "Should use correct symbol format"
        assert order_call.kwargs["side"] == "buy", "Should place a buy order"
        assert order_call.kwargs["quantity"] > 0, "Should have positive quantity"

        # Verify LLM was called for assessment
        assert mock_llm.invoke.called, "LLM should be invoked for token assessment"

    def test_memecoin_trader_skips_low_vibe_tokens(
        self,
        trader_config: MemecoinVibeTraderConfig,
        mock_dex_connector: MagicMock,
        mock_social_scraper: MagicMock,
        mock_execution_tool: MagicMock,
    ) -> None:
        """Test that tokens with low vibe scores are skipped."""
        # Setup mock LLM that returns low vibe score (below 70 threshold)
        low_vibe_llm = MagicMock()

        response_mock = MagicMock()
        response_mock.content = """VIBE_SCORE: 45
RECOMMENDATION: SKIP
RISK_LEVEL: HIGH
REASONING: Low social engagement and poor community metrics."""

        low_vibe_llm.invoke.return_value = response_mock

        mock_trader = MemecoinVibeTrader(
            config=trader_config,
            dex_connector=mock_dex_connector,
            social_scraper=mock_social_scraper,
            execution_tool=mock_execution_tool,
            llm=low_vibe_llm,
        )

        # Act
        results = mock_trader.run_cycle()

        # Assert
        assert results["success"] is True, "Should complete successfully"
        assert results["tokens_scanned"] == 1, "Should still scan the token"
        assert results["assessments_made"] == 1, "Should still assess the token"
        assert results["trades_executed"] == 0, "Should not execute trade for low vibe"
        assert len(results["trades"]) == 0, "Should have no trades in results"

        # Verify order was not executed
        mock_execution_tool.execute_market_order.assert_not_called()

    def test_memecoin_trader_respects_position_limits(
        self,
        mock_dex_connector: MagicMock,
        mock_social_scraper: MagicMock,
        mock_execution_tool: MagicMock,
    ) -> None:
        """Test that the trader respects maximum position limits."""
        # Create a configuration with max 1 position
        config = MemecoinVibeTraderConfig(
            max_positions=1,
            max_allocation_per_trade=0.02,
            min_liquidity_threshold=10000.0,
            min_vibe_score_threshold=70.0,
        )

        # Mock to return 3 high-vibe tokens
        mock_dex_connector.get_new_token_pairs.return_value = [
            {
                "address": f"0x{i:040d}",
                "symbol": f"TOKEN{i}",
                "name": f"Token {i}",
                "liquidity": 50000.0,
                "volume_24h": 100000.0,
                "created_at": datetime.now() - timedelta(minutes=30),
                "dex": "Uniswap",
                "base_token_address": f"0x{i:040d}",
                "quote_token_address": "0xA0b86a33E6441F8d9C1E1a5a9C8dF5b6c3D2A1B4",
            }
            for i in range(3)
        ]

        # Mock social scraper to return different metrics for each token
        call_count = 0

        def mock_get_social_metrics(symbol: str, address: str) -> SocialMetrics:
            nonlocal call_count
            call_count += 1
            return SocialMetrics(
                telegram_followers=10000 + call_count * 1000,
                twitter_followers=15000 + call_count * 1000,
                recent_posts=100 + call_count * 10,
                engagement_rate=0.07 + call_count * 0.01,
                sentiment_score=0.6 + call_count * 0.05,
            )

        mock_social_scraper.get_social_metrics = mock_get_social_metrics

        # Mock LLM to return different vibe scores
        mock_llm = MagicMock()
        call_count = 0

        def mock_invoke(prompt: str) -> MagicMock:
            nonlocal call_count
            call_count += 1
            response_mock = MagicMock()
            response_mock.content = f"""VIBE_SCORE: {80 + call_count * 5}
RECOMMENDATION: BUY
RISK_LEVEL: MEDIUM
REASONING: High potential token with strong metrics."""
            return response_mock

        mock_llm.invoke = mock_invoke

        # Create trader with mocked dependencies
        trader = MemecoinVibeTrader(
            config=config,
            dex_connector=mock_dex_connector,
            social_scraper=mock_social_scraper,
            execution_tool=mock_execution_tool,
            llm=mock_llm,
        )

        # Act
        results = trader.run_cycle()

        # Assert
        assert results["success"] is True, "Should complete successfully"
        assert results["tokens_scanned"] == 3, "Should scan all 3 tokens"
        assert results["assessments_made"] == 3, "Should assess all 3 tokens"
        assert (
            results["trades_executed"] == 1
        ), "Should only execute 1 trade (respecting max_positions)"
        assert len(results["trades"]) == 1, "Should have exactly 1 trade in results"

    def test_memecoin_trader_handles_empty_token_list(
        self,
        trader_config: MemecoinVibeTraderConfig,
        mock_dex_connector: MagicMock,
        mock_social_scraper: MagicMock,
        mock_execution_tool: MagicMock,
        mock_llm: MagicMock,
    ) -> None:
        """Test behavior when no new tokens are found."""
        # Mock to return empty list
        mock_dex_connector.get_new_token_pairs.return_value = []

        trader = MemecoinVibeTrader(
            config=trader_config,
            dex_connector=mock_dex_connector,
            social_scraper=mock_social_scraper,
            execution_tool=mock_execution_tool,
            llm=mock_llm,
        )

        # Act
        results = trader.run_cycle()

        # Assert
        assert (
            results["success"] is True
        ), "Should complete successfully even with no tokens"
        assert results["tokens_scanned"] == 0, "Should scan zero tokens"
        assert results["assessments_made"] == 0, "Should make zero assessments"
        assert results["trades_executed"] == 0, "Should execute zero trades"
        assert len(results["trades"]) == 0, "Should have no trades"

        # Verify no component calls were made
        mock_social_scraper.get_social_metrics.assert_not_called()
        mock_llm.invoke.assert_not_called()
        mock_execution_tool.execute_market_order.assert_not_called()

    def test_memecoin_trader_handles_component_failures_gracefully(
        self,
        trader_config: MemecoinVibeTraderConfig,
        mock_dex_connector: MagicMock,
        mock_social_scraper: MagicMock,
        mock_execution_tool: MagicMock,
        mock_llm: MagicMock,
    ) -> None:
        """Test that the trader handles component failures gracefully."""
        # Mock social scraper to raise an exception
        mock_social_scraper.get_social_metrics.side_effect = Exception(
            "Social API error"
        )

        trader = MemecoinVibeTrader(
            config=trader_config,
            dex_connector=mock_dex_connector,
            social_scraper=mock_social_scraper,
            execution_tool=mock_execution_tool,
            llm=mock_llm,
        )

        # Act
        results = trader.run_cycle()

        # Assert: Agent should still work with default social metrics
        assert (
            results["success"] is True
        ), "Should still complete successfully despite error"
        assert results["tokens_scanned"] == 1, "Should still scan tokens"
        assert (
            results["assessments_made"] == 1
        ), "Should still make assessment (with defaults)"
        assert (
            results["trades_executed"] == 1
        ), "Should execute trade using default social metrics"
        assert len(results["trades"]) == 1, "Should have one trade in results"

    def test_memecoin_trader_position_sizing_calculation(
        self,
        trader_config: MemecoinVibeTraderConfig,
        mock_dex_connector: MagicMock,
        mock_social_scraper: MagicMock,
        mock_execution_tool: MagicMock,
        mock_llm: MagicMock,
    ) -> None:
        """Test position sizing based on portfolio value."""
        # Set up specific portfolio value
        mock_execution_tool.get_account_balance.return_value = {
            "portfolio_value": 50000.0,
            "cash": 50000.0,
        }

        trader = MemecoinVibeTrader(
            config=trader_config,
            dex_connector=mock_dex_connector,
            social_scraper=mock_social_scraper,
            execution_tool=mock_execution_tool,
            llm=mock_llm,
        )

        # Act
        trader.run_cycle()

        # Assert: Should allocate 2% of $50,000 = $1,000 per trade
        # The price estimation is volume_24h / (liquidity * 10) = 100000 / (50000 * 10)
        # = 100000 / 500000 = 0.2
        # So expected quantity = $1,000 / $0.2 = 5,000
        order_call = mock_execution_tool.execute_market_order.call_args
        expected_quantity = 1000.0 / 0.2  # $1,000 / estimated $0.20 price

        # The exact quantity depends on the price estimation
        assert order_call.kwargs["quantity"] > 0, "Should calculate positive quantity"
        assert order_call.kwargs["quantity"] == expected_quantity, (
            f"Should calculate correct quantity, got {order_call.kwargs['quantity']}, "
            f"expected {expected_quantity}"
        )
