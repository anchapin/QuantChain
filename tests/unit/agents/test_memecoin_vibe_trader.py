"""
Unit tests for MemecoinVibeTrader agent.
"""

import unittest
from unittest.mock import MagicMock, patch

import pytest

from quantchain.agents.memecoin_vibe_trader import (
    AgentState,
    MemecoinVibeTrader,
    MemecoinVibeTraderConfig,
    SocialMetrics,
    TokenPair,
    VibeAssessment,
)
from quantchain.tools.social_media_scraper import SentimentScore


@pytest.mark.unit
class TestMemecoinVibeTrader(unittest.TestCase):
    """Test cases for MemecoinVibeTrader."""

    def setUp(self):
        """Set up test fixtures."""
        self.config = MemecoinVibeTraderConfig(
            trading_pairs=["BTC/USD", "ETH/USD"],
            min_vibe_score=7.0,
            max_position_size=0.1,
        )
        self.mock_scraper = MagicMock()
        self.mock_connector = MagicMock()
        self.mock_execution = MagicMock()
        self.mock_llm = MagicMock()

        self.agent = MemecoinVibeTrader(
            config=self.config,
            social_scraper=self.mock_scraper,
            data_connector=self.mock_connector,
            execution_tool=self.mock_execution,
            llm=self.mock_llm,
        )

    def test_initialization(self):
        """Test agent initialization."""
        self.assertEqual(self.agent.state, AgentState.INITIALIZED)
        self.assertEqual(self.agent.config.trading_pairs, ["BTC/USD", "ETH/USD"])
        self.assertEqual(self.agent.assessments, {})

    def test_start_stop_reset(self):
        """Test start, stop, and reset transitions."""
        self.agent.start()
        self.assertEqual(self.agent.state, AgentState.ACTIVE)

        self.agent.stop()
        self.assertEqual(self.agent.state, AgentState.STOPPED)

        self.agent.reset()
        self.assertEqual(self.agent.state, AgentState.INITIALIZED)
        self.assertEqual(self.agent.assessments, {})

    def test_assess_vibe_with_scraper(self):
        """Test vibe assessment with mocked scraper."""
        # Setup mock metrics
        mock_metrics = MagicMock()
        mock_metrics.post_count = 100
        mock_metrics.sentiment_distribution = {
            SentimentScore.VERY_POSITIVE: 50,
            SentimentScore.POSITIVE: 30,
            SentimentScore.NEUTRAL: 10,
            SentimentScore.NEGATIVE: 5,
            SentimentScore.VERY_NEGATIVE: 5,
        }
        self.mock_scraper.get_metrics.return_value = mock_metrics

        token_pair = TokenPair("BTC", "USD", "0x123", "ethereum")

        # Patch random to get deterministic technical indicators
        with patch("random.uniform") as mock_uniform:
            # RSI=20 (buy signal), MACD=0.1
            mock_uniform.side_effect = [20.0, 0.1]

            assessment = self.agent._assess_vibe(token_pair)

            self.assertIsInstance(assessment, VibeAssessment)
            self.assertEqual(assessment.token_pair, token_pair)
            self.assertEqual(assessment.recommendation, "BUY")
            self.assertGreater(assessment.vibe_score, 0)

            # Verify scraper was called
            self.mock_scraper.get_metrics.assert_called_with("BTC/USD")

    def test_assess_vibe_no_scraper(self):
        """Test vibe assessment without scraper (fallback)."""
        agent = MemecoinVibeTrader(config=self.config)
        token_pair = TokenPair("BTC", "USD", "0x123", "ethereum")

        assessment = agent._assess_vibe(token_pair)

        self.assertIsInstance(assessment, VibeAssessment)
        self.assertIsNotNone(assessment.social_metrics)

    def test_assess_vibe_scraper_error(self):
        """Test vibe assessment when scraper raises exception."""
        self.mock_scraper.get_metrics.side_effect = Exception("API Error")
        token_pair = TokenPair("BTC", "USD", "0x123", "ethereum")

        assessment = self.agent._assess_vibe(token_pair)

        # Should fallback to default metrics
        self.assertIsInstance(assessment, VibeAssessment)
        self.assertEqual(assessment.social_metrics.mentions, 0)

    def test_execute_decision_buy(self):
        """Test executing a BUY decision."""
        token_pair = TokenPair("BTC", "USD", "0x123", "ethereum")
        assessment = VibeAssessment(
            token_pair=token_pair,
            vibe_score=8.0,
            social_metrics=SocialMetrics(),
            technical_indicators={"rsi": 25},
            recommendation="BUY",
            confidence=0.8,
        )

        self.agent._execute_decision(assessment)

        self.mock_execution.place_order.assert_called_with(
            side="BUY", symbol="BTC/USD", quantity=self.config.max_position_size
        )

    def test_execute_decision_sell(self):
        """Test executing a SELL decision."""
        token_pair = TokenPair("BTC", "USD", "0x123", "ethereum")
        assessment = VibeAssessment(
            token_pair=token_pair,
            vibe_score=3.0,
            social_metrics=SocialMetrics(),
            technical_indicators={"rsi": 75},
            recommendation="SELL",
            confidence=0.8,
        )

        # Mock current position
        self.mock_execution.get_position.return_value = 1.0

        self.agent._execute_decision(assessment)

        self.mock_execution.place_order.assert_called_with(
            side="SELL", symbol="BTC/USD", quantity=1.0
        )

    def test_execute_decision_hold(self):
        """Test executing a HOLD decision."""
        token_pair = TokenPair("BTC", "USD", "0x123", "ethereum")
        assessment = VibeAssessment(
            token_pair=token_pair,
            vibe_score=5.0,
            social_metrics=SocialMetrics(),
            technical_indicators={"rsi": 50},
            recommendation="HOLD",
            confidence=0.5,
        )

        self.agent._execute_decision(assessment)

        self.mock_execution.place_order.assert_not_called()

    def test_execute_decision_no_execution_tool(self):
        """Test execution without execution tool."""
        agent = MemecoinVibeTrader(config=self.config)
        token_pair = TokenPair("BTC", "USD", "0x123", "ethereum")
        assessment = VibeAssessment(
            token_pair=token_pair,
            vibe_score=8.0,
            social_metrics=SocialMetrics(),
            technical_indicators={"rsi": 25},
            recommendation="BUY",
            confidence=0.8,
        )

        # Should not raise error
        agent._execute_decision(assessment)

    def test_run_cycle(self):
        """Test running a full cycle."""
        self.agent.start()

        with patch.object(self.agent, "_assess_vibe") as mock_assess:
            with patch.object(self.agent, "_execute_decision") as mock_execute:
                mock_assessment = MagicMock()
                mock_assess.return_value = mock_assessment

                self.agent.run_cycle()

                # Should be called for each pair in config
                self.assertEqual(mock_assess.call_count, 2)
                self.assertEqual(mock_execute.call_count, 2)
                mock_execute.assert_called_with(mock_assessment)

    def test_run_cycle_not_active(self):
        """Test run_cycle when agent is not active."""
        self.agent.stop()

        with patch.object(self.agent, "_assess_vibe") as mock_assess:
            self.agent.run_cycle()
            mock_assess.assert_not_called()

    def test_config_validation(self):
        """Test configuration validation."""
        with self.assertRaises(ValueError):
            MemecoinVibeTraderConfig(min_vibe_score=11.0)

        with self.assertRaises(ValueError):
            MemecoinVibeTraderConfig(timeframe="invalid")

    def test_mock_llm(self):
        """Test MockLLM functionality."""
        from quantchain.agents.memecoin_vibe_trader import MockLLM

        llm = MockLLM()
        response = llm.generate("test prompt")

        self.assertEqual(response.text, "Mock response for: test prompt")
        self.assertEqual(response.model, "test-model")
        self.assertGreater(response.usage.total_tokens, 0)
