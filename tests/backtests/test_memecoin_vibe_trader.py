import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta

from quantchain.agents.memecoin_vibe_trader import (
    MemecoinVibeTrader,
    MemecoinVibeTraderConfig,
    MockLLM,
)
from quantchain.tools.social_media_scraper import SocialMetrics


class TestMemecoinVibeTrader:
    """Backtest tests for Memecoin Vibe Trader Agent"""

    @pytest.fixture
    def mock_token_pairs(self) -> list:
        """Mock token pairs data"""
        return [
            {
                "address": "0x1234567890123456789012345678901234567890",
                "symbol": "VIBE",
                "name": "VibeCoin",
                "liquidity": 50000.0,
                "volume_24h": 100000.0,
                "created_at": datetime.now() - timedelta(hours=1),
                "dex": "uniswap",
            },
            {
                "address": "0x0987654321098765432109876543210987654321",
                "symbol": "MOON",
                "name": "MoonRocket",
                "liquidity": 25000.0,
                "volume_24h": 50000.0,
                "created_at": datetime.now() - timedelta(hours=2),
                "dex": "pancakeswap",
            },
        ]

    @pytest.fixture
    def mock_social_metrics(self) -> dict:
        """Mock social media metrics"""
        return {
            "telegram_followers": 5000,
            "twitter_followers": 10000,
            "recent_posts": 25,
            "engagement_rate": 0.15,
            "sentiment_score": 0.8,
        }

    @pytest.fixture
    def backtest_config(self) -> dict:
        """Mock backtest configuration"""
        return {
            "start_date": "2024-01-01",
            "end_date": "2024-01-02",
            "initial_balance": 10000.0,
            "agent_config": {
                "scan_interval": 3600,
                "max_positions": 5,
                "max_allocation_per_trade": 0.02,
                "min_liquidity_threshold": 10000.0,
                "min_vibe_score_threshold": 70.0,
                "risk_tolerance": "MEDIUM",
            },
        }

    def test_agent_identifies_and_trades_high_vibe_token(  # type: ignore
        self, mock_token_pairs, mock_social_metrics, backtest_config
    ) -> None:
        """Test that agent successfully identifies and trades a high-vibe token"""

        with patch(
            "quantchain.connectors.dexscreener_connector.DexscreenerDataConnector"
        ) as mock_dex_connector, patch(
            "quantchain.tools.social_media_scraper.SocialMediaScraper"
        ) as mock_social_scraper, patch(
            "quantchain.tools.execution.AlpacaExecutionTool"
        ) as mock_execution_tool:

            # Setup mocks
            mock_dex_instance = mock_dex_connector.return_value
            mock_dex_instance.get_new_token_pairs.return_value = mock_token_pairs

            # Create a mock that returns different social metrics for different tokens
            def mock_get_social_metrics(symbol, address):
                return SocialMetrics(**mock_social_metrics)

            mock_social_scraper.return_value.get_social_metrics.side_effect = (
                mock_get_social_metrics
            )

            # Create mock LLM with response
            mock_llm = MockLLM(
                """VIBE_SCORE: 85.0
    RECOMMENDATION: BUY
    RISK_LEVEL: MEDIUM
    REASONING: Strong social momentum and unique token name"""
            )

            mock_execution_tool_instance = MagicMock()
            mock_execution_tool_instance.execute_market_order.return_value = MagicMock(
                order_id="test_order_123"
            )
            mock_execution_tool_instance.get_account_balance.return_value = {
                "portfolio_value": 10000.0,
                "buying_power": 9500.0,
                "cash": 9500.0,
                "total_equity": 10000.0,
            }
            mock_execution_tool_instance.get_positions.return_value = []
            mock_execution_tool.return_value = mock_execution_tool_instance

            # Create agent
            config = MemecoinVibeTraderConfig(**backtest_config["agent_config"])
            agent = MemecoinVibeTrader(
                config=config,
                dex_connector=mock_dex_instance,
                social_scraper=mock_social_scraper.return_value,
                execution_tool=mock_execution_tool_instance,
                llm=mock_llm,
            )

            # Act
            results = agent.run_cycle()

            # Assert
            assert results["success"] is True
            assert results["tokens_scanned"] == 2
            assert results["assessments_made"] == 2
            assert len(results["trades"]) > 0
            assert mock_execution_tool_instance.execute_market_order.called

    def test_agent_skips_low_vibe_tokens(  # type: ignore
        self, mock_token_pairs, mock_social_metrics, backtest_config
    ) -> None:
        """Test that agent skips tokens with low vibe scores"""

        with patch(
            "quantchain.connectors.dexscreener_connector.DexscreenerDataConnector"
        ) as mock_dex_connector, patch(
            "quantchain.tools.social_media_scraper.SocialMediaScraper"
        ) as mock_social_scraper, patch(
            "quantchain.tools.execution.AlpacaExecutionTool"
        ) as mock_execution_tool:

            # Setup mocks
            mock_dex_instance = mock_dex_connector.return_value
            mock_dex_instance.get_new_token_pairs.return_value = mock_token_pairs

            # Mock social scraper to return consistent metrics
            def mock_get_social_metrics(symbol, address):  # type: ignore
                return SocialMetrics(**mock_social_metrics)

            mock_social_scraper.return_value.get_social_metrics.side_effect = (
                mock_get_social_metrics
            )

            # Create mock LLM that returns LOW vibe scores (below threshold of 70)
            mock_llm = MockLLM(
                """VIBE_SCORE: 45.0
    RECOMMENDATION: SKIP
    RISK_LEVEL: HIGH
    REASONING: Low social engagement and generic name"""
            )

            mock_execution_tool_instance = MagicMock()
            mock_execution_tool.return_value = mock_execution_tool_instance

            # Create agent
            config = MemecoinVibeTraderConfig(**backtest_config["agent_config"])
            agent = MemecoinVibeTrader(
                config=config,
                dex_connector=mock_dex_instance,
                social_scraper=mock_social_scraper.return_value,
                execution_tool=mock_execution_tool_instance,
                llm=mock_llm,
            )

            # Act
            results = agent.run_cycle()

            # Assert - no trades should be executed due to low vibe scores
            assert results["success"] is True
            assert results["tokens_scanned"] == 2  # Both tokens scanned
            assert results["assessments_made"] == 2  # Both tokens assessed
            assert len(results["trades"]) == 0  # No trades executed
            # Verify execution tool was never called to place orders
            assert not mock_execution_tool_instance.execute_market_order.called

    def test_agent_handles_dexscreener_api_failure(
        self, backtest_config
    ) -> None:  # type: ignore
        """Test that agent gracefully handles Dexscreener API failures"""

        with patch(
            "quantchain.connectors.dexscreener_connector.DexscreenerDataConnector"
        ) as mock_dex_connector, patch(
            "quantchain.tools.social_media_scraper.SocialMediaScraper"
        ) as mock_social_scraper, patch(
            "quantchain.tools.execution.AlpacaExecutionTool"
        ) as mock_execution_tool:

            mock_dex_instance = mock_dex_connector.return_value
            mock_dex_instance.get_new_token_pairs.side_effect = Exception(
                "API unavailable"
            )

            # Mock other components (though they shouldn't be called)
            mock_social_instance = mock_social_scraper.return_value
            mock_execution_instance = mock_execution_tool.return_value

            # Create agent
            config = MemecoinVibeTraderConfig(**backtest_config["agent_config"])
            agent = MemecoinVibeTrader(
                config=config,
                dex_connector=mock_dex_instance,
                social_scraper=mock_social_instance,
                execution_tool=mock_execution_instance,
            )

            # Act
            results = agent.run_cycle()

            # Assert - agent should handle API failure gracefully
            assert results["success"] is False  # Cycle failed due to API error
            assert "error_message" in results
            assert "API unavailable" in results["error_message"]
            assert (
                results["tokens_scanned"] == 0
            )  # No tokens scanned due to API failure
            assert results["assessments_made"] == 0  # No assessments made
            assert len(results["trades"]) == 0  # No trades executed

            # Verify downstream components were not called
            assert not mock_social_instance.get_social_metrics.called
            assert not mock_execution_instance.execute_market_order.called

    def test_agent_handles_social_scraping_failure(  # type: ignore
        self, mock_token_pairs, backtest_config
    ) -> None:
        """Test agent continues processing when social scraping fails for one token"""

        with patch(
            "quantchain.connectors.dexscreener_connector.DexscreenerDataConnector"
        ) as mock_dex_connector, patch(
            "quantchain.tools.social_media_scraper.SocialMediaScraper"
        ) as mock_social_scraper, patch(
            "quantchain.tools.execution.AlpacaExecutionTool"
        ) as mock_execution_tool:

            # Setup mocks
            mock_dex_instance = mock_dex_connector.return_value
            mock_dex_instance.get_new_token_pairs.return_value = mock_token_pairs

            # Setup mock to fail for first token but succeed for second
            mock_social_instance = mock_social_scraper.return_value
            mock_social_instance.get_social_metrics.side_effect = [
                Exception("Scraping failed for VIBE"),  # First token fails
                SocialMetrics(  # Second token succeeds
                    telegram_followers=1000,
                    twitter_followers=2000,
                    recent_posts=10,
                    engagement_rate=0.1,
                    sentiment_score=0.6,
                ),
            ]

            # Create mock LLM that gives high score only to tokens
            def mock_llm_factory():
                """Factory that creates an LLM with conditional responses"""

                class ConditionalMockLLM:
                    def invoke(self, prompt):
                        class MockResponse:
                            def __init__(self, content):
                                self.content = content

                        # Check if prompt indicates poor social metrics
                        if (
                            "Telegram Followers: 0" in prompt
                            or "Recent Posts: 0" in prompt
                        ):
                            # Failed social scraping - give low score
                            return MockResponse(
                                """VIBE_SCORE: 25.0
RECOMMENDATION: SKIP
RISK_LEVEL: HIGH
REASONING: No social metrics available"""
                            )
                        else:
                            # Good social metrics - give high score
                            return MockResponse(
                                """VIBE_SCORE: 85.0
RECOMMENDATION: BUY
RISK_LEVEL: MEDIUM
REASONING: Strong social momentum"""
                            )

                return ConditionalMockLLM()

            mock_llm = mock_llm_factory()

            mock_execution_tool_instance = MagicMock()
            mock_execution_tool_instance.execute_market_order.return_value = MagicMock(
                order_id="test_order_123"
            )
            mock_execution_tool_instance.get_account_balance.return_value = {
                "portfolio_value": 10000.0,
                "buying_power": 9500.0,
                "cash": 9500.0,
                "total_equity": 10000.0,
            }
            mock_execution_tool_instance.get_positions.return_value = []
            mock_execution_tool.return_value = mock_execution_tool_instance

            # Create agent
            config = MemecoinVibeTraderConfig(**backtest_config["agent_config"])
            agent = MemecoinVibeTrader(
                config=config,
                dex_connector=mock_dex_instance,
                social_scraper=mock_social_instance,
                execution_tool=mock_execution_tool_instance,
                llm=mock_llm,
            )

            # Act
            results = agent.run_cycle()

            # Assert - agent should continue processing despite failure for first token
            assert results["success"] is True  # Overall success despite partial failure
            assert results["tokens_scanned"] == 2  # Both tokens scanned
            assert (
                results["assessments_made"] == 2
            )  # Both tokens assessed (first one got SKIP assessment)
            assert (
                len(results["trades"]) == 1
            )  # One trade executed for successful token

            # Verify social scraper was called for both tokens
            assert mock_social_instance.get_social_metrics.call_count == 2
            # Verify execution happened for the successful token
            assert mock_execution_tool_instance.execute_market_order.called

    def test_agent_respects_risk_limits(
        self, mock_social_metrics, backtest_config
    ) -> None:  # type: ignore
        """Test that agent respects position limits and allocation constraints"""

        # Create multiple high-vibe tokens
        multiple_tokens = [
            {
                "address": "0x1234567890123456789012345678901234567890",
                "symbol": "VIBE1",
                "name": "VibeCoin1",
                "liquidity": 50000.0,
                "volume_24h": 100000.0,
                "created_at": datetime.now() - timedelta(hours=1),
                "dex": "uniswap",
            },
            {
                "address": "0x0987654321098765432109876543210987654321",
                "symbol": "VIBE2",
                "name": "VibeCoin2",
                "liquidity": 60000.0,
                "volume_24h": 120000.0,
                "created_at": datetime.now() - timedelta(hours=1),
                "dex": "uniswap",
            },
            {
                "address": "0xabcdefabcdefabcdefabcdefabcdefabcdefabcd",
                "symbol": "VIBE3",
                "name": "VibeCoin3",
                "liquidity": 70000.0,
                "volume_24h": 140000.0,
                "created_at": datetime.now() - timedelta(hours=1),
                "dex": "uniswap",
            },
        ]

        # Configure agent with strict limits: max 1 position, 1% allocation per trade
        strict_config = backtest_config.copy()
        strict_config["agent_config"]["max_positions"] = 1
        strict_config["agent_config"]["max_allocation_per_trade"] = 0.01

        with patch(
            "quantchain.connectors.dexscreener_connector.DexscreenerDataConnector"
        ) as mock_dex_connector, patch(
            "quantchain.tools.social_media_scraper.SocialMediaScraper"
        ) as mock_social_scraper, patch(
            "quantchain.tools.execution.AlpacaExecutionTool"
        ) as mock_execution_tool:

            # Setup mocks
            mock_dex_instance = mock_dex_connector.return_value
            mock_dex_instance.get_new_token_pairs.return_value = multiple_tokens

            # Mock social scraper to return consistent high metrics
            def mock_get_social_metrics(symbol, address):  # type: ignore
                return SocialMetrics(**mock_social_metrics)

            mock_social_scraper.return_value.get_social_metrics.side_effect = (
                mock_get_social_metrics
            )

            # Create mock LLM that returns HIGH vibe scores for all tokens
            mock_llm = MockLLM(
                """VIBE_SCORE: 90.0
    RECOMMENDATION: BUY
    RISK_LEVEL: LOW
    REASONING: Excellent social momentum and strong fundamentals"""
            )

            mock_execution_tool_instance = MagicMock()
            mock_execution_tool_instance.execute_market_order.return_value = MagicMock(
                order_id="test_order_123"
            )
            mock_execution_tool_instance.get_account_balance.return_value = {
                "portfolio_value": 10000.0,  # $10,000 portfolio
                "buying_power": 9500.0,
                "cash": 9500.0,
                "total_equity": 10000.0,
            }
            mock_execution_tool_instance.get_positions.return_value = []
            mock_execution_tool.return_value = mock_execution_tool_instance

            # Create agent with strict risk limits
            config = MemecoinVibeTraderConfig(**strict_config["agent_config"])
            agent = MemecoinVibeTrader(
                config=config,
                dex_connector=mock_dex_instance,
                social_scraper=mock_social_scraper.return_value,
                execution_tool=mock_execution_tool_instance,
                llm=mock_llm,
            )

            # Act
            results = agent.run_cycle()

            # Assert - only 1 trade should be executed despite 3 high-vibe tokens
            assert results["success"] is True
            assert results["tokens_scanned"] == 3  # All 3 tokens scanned
            assert results["assessments_made"] == 3  # All 3 tokens assessed
            assert (
                len(results["trades"]) == 1
            )  # Only 1 trade executed due to position limit

            # Verify only one execution call was made
            assert mock_execution_tool_instance.execute_market_order.call_count == 1

            # Verify the trade size respects allocation limit (1% of $10,000 = $100)
            call_args = mock_execution_tool_instance.execute_market_order.call_args
            executed_quantity = call_args[1]["quantity"]

            # Calculate the expected price based on the agent's pricing formula
            # For VIBE1: volume=100000, liquidity=50000 -> price = 0.2
            expected_price = 100000.0 / (50000.0 * 10)
            max_allowed_quantity = 100.0 / expected_price  # Allocation / expected price

            assert (
                executed_quantity <= max_allowed_quantity
            )  # Should not exceed allocation limit
