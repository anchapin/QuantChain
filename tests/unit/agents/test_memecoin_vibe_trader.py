"""Comprehensive unit tests for the MemecoinVibeTrader agent."""

from datetime import datetime
from typing import Any
from unittest.mock import MagicMock, patch
import pytest
from alpaca.data import TimeFrame
from quantchain.agents.memecoin_vibe_trader import (
    AgentState,
    MemecoinVibeTrader,
    MemecoinVibeTraderConfig,
    MockLLM,
    SocialMetrics,
    TokenPair,
    VibeAssessment,
)
from quantchain.connectors.dexscreener_connector import DexscreenerDataConnector
from quantchain.tools.execution import AlpacaExecutionTool
from quantchain.tools.social_media_scraper import SocialMediaScraper


class TestMemecoinVibeTraderConfig:
    """Test configuration validation and defaults."""

    def test_default_config_values(self) -> None:
        """Test default configuration values."""
        config = MemecoinVibeTraderConfig()

        assert config.trading_pairs == ["BTC/USD", "ETH/USD", "SOL/USD"]
        assert config.timeframe == "1h"
        assert config.min_vibe_score == 7.0
        assert config.max_position_size == 0.05
        assert config.stop_loss_pct == 0.05
        assert config.take_profit_pct == 0.15

    def test_custom_config_values(self) -> None:
        """Test custom configuration values."""
        custom_pairs = ["DOGE/USD", "SHIB/USD"]
        config = MemecoinVibeTraderConfig(
            trading_pairs=custom_pairs,
            timeframe="15m",
            min_vibe_score=8.0,
            max_position_size=0.1
        )

        assert config.trading_pairs == custom_pairs
        assert config.timeframe == "15m"
        assert config.min_vibe_score == 8.0
        assert config.max_position_size == 0.1

    def test_invalid_timeframe(self) -> None:
        """Test handling of invalid timeframe."""
        with pytest.raises(ValueError, match="Timeframe 'invalid' is not supported"):
            MemecoinVibeTraderConfig(timeframe="invalid")

    def test_invalid_vibe_score(self) -> None:
        """Test handling of invalid vibe score."""
        with pytest.raises(ValueError, match="Vibe score must be between 0 and 10"):
            MemecoinVibeTraderConfig(min_vibe_score=-1.0)

        with pytest.raises(ValueError, match="Vibe score must be between 0 and 10"):
            MemecoinVibeTraderConfig(min_vibe_score=11.0)


class TestTokenPair:
    """Test TokenPair data class."""

    def test_token_pair_creation(self) -> None:
        """Test TokenPair creation."""
        token_pair = TokenPair(
            base_token="DOGE",
            quote_token="USD",
            address="0x1234",
            chain="ethereum"
        )

        assert token_pair.base_token == "DOGE"
        assert token_pair.quote_token == "USD"
        assert token_pair.address == "0x1234"
        assert token_pair.chain == "ethereum"

    def test_token_pair_symbol(self) -> None:
        """Test TokenPair symbol property."""
        token_pair = TokenPair(
            base_token="DOGE",
            quote_token="USD",
            address="0x1234",
            chain="ethereum"
        )

        assert token_pair.symbol == "DOGE/USD"


class TestSocialMetrics:
    """Test SocialMetrics data class."""

    def test_social_metrics_creation(self) -> None:
        """Test SocialMetrics creation."""
        now = datetime.now()
        metrics = SocialMetrics(
            mentions=1000,
            sentiment_score=8.5,
            trending_score=7.0,
            volume_change=15.5,
            last_updated=now
        )

        assert metrics.mentions == 1000
        assert metrics.sentiment_score == 8.5
        assert metrics.trending_score == 7.0
        assert metrics.volume_change == 15.5
        assert metrics.last_updated == now


class TestVibeAssessment:
    """Test VibeAssessment data class."""

    def test_vibe_assessment_creation(self) -> None:
        """Test VibeAssessment creation."""
        assessment = VibeAssessment(
            token_pair=TokenPair("DOGE", "USD", "0x1234", "ethereum"),
            vibe_score=8.5,
            social_metrics=SocialMetrics(1000, 8.5, 7.0, 15.5, datetime.now()),
            technical_indicators={"rsi": 65, "macd": 0.5},
            recommendation="BUY",
            confidence=0.85
        )

        assert assessment.token_pair.symbol == "DOGE/USD"
        assert assessment.vibe_score == 8.5
        assert assessment.recommendation == "BUY"
        assert assessment.confidence == 0.85


class TestMockLLM:
    """Test MockLLM class."""

    def test_mock_llm_creation(self) -> None:
        """Test MockLLM creation."""
        mock_llm = MockLLM(model="test-model")
        assert mock_llm.model == "test-model"

    def test_mock_llm_generate(self) -> None:
        """Test MockLLM generate method."""
        mock_llm = MockLLM(model="test-model")
        response = mock_llm.generate("Test prompt")

        assert response.text == "Mock response for: Test prompt"
        assert response.model == "test-model"
        assert response.usage.prompt_tokens > 0
        assert response.usage.completion_tokens > 0
        assert response.usage.total_tokens > 0


class TestMemecoinVibeTrader:
    """Test MemecoinVibeTrader agent."""

    @pytest.fixture
    def config(self) -> MemecoinVibeTraderConfig:
        """Create a test configuration."""
        return MemecoinVibeTraderConfig(
            trading_pairs=["DOGE/USD", "SHIB/USD"],
            timeframe="15m"
        )

    @pytest.fixture
    def mock_social_scraper(self) -> MagicMock:
        """Create a mock social media scraper."""
        scraper = MagicMock(spec=SocialMediaScraper)
        # Return a SocialMediaMetrics object that matches what get_metrics returns
        from quantchain.tools.social_media_scraper import SocialMediaMetrics
        scraper.get_metrics.return_value = SocialMediaMetrics(
            platform="twitter",
            symbol="DOGE",
            post_count=1000,
            total_likes=5000,
            total_shares=1000,
            total_comments=2000,
            unique_authors=800
        )
        return scraper

    @pytest.fixture
    def mock_data_connector(self) -> MagicMock:
        """Create a mock data connector."""
        connector = MagicMock(spec=DexscreenerDataConnector)
        connector.get_historical_data.return_value = {
            "timestamp": [datetime.now()],
            "open": [0.1],
            "high": [0.12],
            "low": [0.09],
            "close": [0.11],
            "volume": [1000000]
        }
        return connector

    @pytest.fixture
    def mock_execution_tool(self) -> MagicMock:
        """Create a mock execution tool."""
        tool = MagicMock(spec=AlpacaExecutionTool)
        tool.place_order.return_value = {"order_id": "12345", "status": "filled"}
        # Add get_position method for SELL tests
        tool.get_position.return_value = 1000  # Mock position value
        return tool

    @pytest.fixture
    def mock_llm(self) -> MockLLM:
        """Create a mock LLM."""
        return MockLLM(model="test-model")

    def test_initialization(
        self,
        config: MemecoinVibeTraderConfig,
        mock_social_scraper: MagicMock,
        mock_data_connector: MagicMock,
        mock_execution_tool: MagicMock,
        mock_llm: MockLLM
    ) -> None:
        """Test MemecoinVibeTrader initialization."""
        trader = MemecoinVibeTrader(
            config=config,
            social_scraper=mock_social_scraper,
            data_connector=mock_data_connector,
            execution_tool=mock_execution_tool,
            llm=mock_llm
        )

        assert trader.config == config
        assert trader.social_scraper == mock_social_scraper
        assert trader.data_connector == mock_data_connector
        assert trader.execution_tool == mock_execution_tool
        assert trader.llm == mock_llm
        assert trader.state == AgentState.INITIALIZED

    def test_assess_vibe(
        self,
        config: MemecoinVibeTraderConfig,
        mock_social_scraper: MagicMock,
        mock_data_connector: MagicMock,
        mock_execution_tool: MagicMock,
        mock_llm: MockLLM
    ) -> None:
        """Test vibe assessment functionality."""
        trader = MemecoinVibeTrader(
            config=config,
            social_scraper=mock_social_scraper,
            data_connector=mock_data_connector,
            execution_tool=mock_execution_tool,
            llm=mock_llm
        )

        token_pair = TokenPair("DOGE", "USD", "0x1234", "ethereum")
        assessment = trader._assess_vibe(token_pair)

        assert assessment.token_pair == token_pair
        assert assessment.vibe_score >= 0
        assert assessment.vibe_score <= 10
        assert assessment.recommendation in ["BUY", "SELL", "HOLD"]
        assert 0 <= assessment.confidence <= 1

        # Check that social scraper was called
        mock_social_scraper.get_metrics.assert_called_with(token_pair.symbol)

    def test_execute_decision_buy(
        self,
        config: MemecoinVibeTraderConfig,
        mock_social_scraper: MagicMock,
        mock_data_connector: MagicMock,
        mock_execution_tool: MagicMock,
        mock_llm: MockLLM
    ) -> None:
        """Test executing a BUY decision."""
        trader = MemecoinVibeTrader(
            config=config,
            social_scraper=mock_social_scraper,
            data_connector=mock_data_connector,
            execution_tool=mock_execution_tool,
            llm=mock_llm
        )

        token_pair = TokenPair("DOGE", "USD", "0x1234", "ethereum")
        assessment = VibeAssessment(
            token_pair=token_pair,
            vibe_score=9.0,
            social_metrics=SocialMetrics(1000, 9.0, 8.0, 20.0, datetime.now()),
            technical_indicators={"rsi": 30, "macd": -0.2},
            recommendation="BUY",
            confidence=0.9
        )

        trader._execute_decision(assessment)

        # Check that execution tool was called with BUY order
        mock_execution_tool.place_order.assert_called_once()
        args, kwargs = mock_execution_tool.place_order.call_args
        assert kwargs["side"] == "BUY"
        assert kwargs["symbol"] == token_pair.symbol

    def test_execute_decision_sell(
        self,
        config: MemecoinVibeTraderConfig,
        mock_social_scraper: MagicMock,
        mock_data_connector: MagicMock,
        mock_execution_tool: MagicMock,
        mock_llm: MockLLM
    ) -> None:
        """Test executing a SELL decision."""
        trader = MemecoinVibeTrader(
            config=config,
            social_scraper=mock_social_scraper,
            data_connector=mock_data_connector,
            execution_tool=mock_execution_tool,
            llm=mock_llm
        )

        token_pair = TokenPair("DOGE", "USD", "0x1234", "ethereum")
        assessment = VibeAssessment(
            token_pair=token_pair,
            vibe_score=2.0,
            social_metrics=SocialMetrics(100, 2.0, 1.0, -5.0, datetime.now()),
            technical_indicators={"rsi": 80, "macd": 0.3},
            recommendation="SELL",
            confidence=0.8
        )

        # Set up mock execution tool to return position for SELL test
        mock_execution_tool.get_position.return_value = 1000

        trader._execute_decision(assessment)

        # Check that execution tool was called with SELL order
        mock_execution_tool.place_order.assert_called_once()
        args, kwargs = mock_execution_tool.place_order.call_args
        assert kwargs["side"] == "SELL"
        assert kwargs["symbol"] == token_pair.symbol

    def test_run_cycle(
        self,
        config: MemecoinVibeTraderConfig,
        mock_social_scraper: MagicMock,
        mock_data_connector: MagicMock,
        mock_execution_tool: MagicMock,
        mock_llm: MockLLM
    ) -> None:
        """Test running a single trading cycle."""
        trader = MemecoinVibeTrader(
            config=config,
            social_scraper=mock_social_scraper,
            data_connector=mock_data_connector,
            execution_tool=mock_execution_tool,
            llm=mock_llm
        )

        # Start the trader before running cycle
        trader.start()
        trader.run_cycle()

        # Verify that the trader has assessed each trading pair
        for pair_symbol in config.trading_pairs:
            # Check that social scraper was called for each pair
            print(f"Checking for call to get_metrics with {pair_symbol}")
            print(f"Actual calls: {mock_social_scraper.get_metrics.mock_calls}")
            mock_social_scraper.get_metrics.assert_any_call(pair_symbol)

    def test_state_transitions(
        self,
        config: MemecoinVibeTraderConfig,
        mock_social_scraper: MagicMock,
        mock_data_connector: MagicMock,
        mock_execution_tool: MagicMock,
        mock_llm: MockLLM
    ) -> None:
        """Test state transitions during operation."""
        trader = MemecoinVibeTrader(
            config=config,
            social_scraper=mock_social_scraper,
            data_connector=mock_data_connector,
            execution_tool=mock_execution_tool,
            llm=mock_llm
        )

        # Initial state
        assert trader.state == AgentState.INITIALIZED

        # Start trading
        trader.start()
        assert trader.state == AgentState.ACTIVE

        # Stop trading
        trader.stop()
        assert trader.state == AgentState.STOPPED

        # Reset state
        trader.reset()
        assert trader.state == AgentState.INITIALIZED
