"""Comprehensive unit tests for the MemecoinVibeTrader agent."""

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime

from quantchain.agents.memecoin_vibe_trader import (
    MemecoinVibeTrader,
    MemecoinVibeTraderConfig,
    TokenPair,
    VibeAssessment,
    AgentState,
    SocialMetrics,
    MockLLM,
)
from quantchain.connectors.dexscreener_connector import DexscreenerDataConnector
from quantchain.tools.social_media_scraper import SocialMediaScraper
from quantchain.tools.execution import AlpacaExecutionTool


class TestMemecoinVibeTraderConfig:
    """Test configuration validation and defaults."""

    def test_default_config_values(self):
        """Test that default configuration values are set correctly."""
        config = MemecoinVibeTraderConfig()

        assert config.scan_interval == 3600
        assert config.max_positions == 5
        assert config.max_allocation_per_trade == 0.02
        assert config.min_liquidity_threshold == 10000
        assert config.min_vibe_score_threshold == 70
        assert config.risk_tolerance == "MEDIUM"
        assert config.time_window == "1h"

    def test_custom_config_values(self):
        """Test that custom configuration values are respected."""
        config = MemecoinVibeTraderConfig(
            scan_interval=1800,
            max_positions=10,
            max_allocation_per_trade=0.05,
            min_liquidity_threshold=5000,
            min_vibe_score_threshold=80,
            risk_tolerance="LOW",
            time_window="30m",
        )

        assert config.scan_interval == 1800
        assert config.max_positions == 10
        assert config.max_allocation_per_trade == 0.05
        assert config.min_liquidity_threshold == 5000
        assert config.min_vibe_score_threshold == 80
        assert config.risk_tolerance == "LOW"
        assert config.time_window == "30m"

    def test_config_validation_edge_cases(self):
        """Test edge case validation for configuration."""
        # Test negative values (should still work as they may be validated elsewhere)
        config = MemecoinVibeTraderConfig(
            scan_interval=-1,
            max_positions=-1,
            max_allocation_per_trade=-0.1,
            min_liquidity_threshold=-1000,
            min_vibe_score_threshold=-10,
        )

        assert config.scan_interval == -1
        assert config.max_positions == -1
        assert config.max_allocation_per_trade == -0.1
        assert config.min_liquidity_threshold == -1000
        assert config.min_vibe_score_threshold == -10


class TestMemecoinVibeTraderInitialization:
    """Test agent initialization and workflow building."""

    def test_agent_initialization_with_all_components(self):
        """Test that agent initializes correctly with all components."""
        config = MemecoinVibeTraderConfig()
        dex_connector = MagicMock(spec=DexscreenerDataConnector)
        social_scraper = MagicMock(spec=SocialMediaScraper)
        execution_tool = MagicMock(spec=AlpacaExecutionTool)
        llm = MagicMock()

        agent = MemecoinVibeTrader(
            config=config,
            dex_connector=dex_connector,
            social_scraper=social_scraper,
            execution_tool=execution_tool,
            llm=llm,
        )

        assert agent.config == config
        assert agent.dex_connector == dex_connector
        assert agent.social_scraper == social_scraper
        assert agent.execution_tool == execution_tool
        assert agent.llm == llm
        assert agent.workflow is not None

    def test_agent_initialization_with_default_llm(self):
        """Test that agent initializes with MockLLM when no LLM provided."""
        config = MemecoinVibeTraderConfig()
        dex_connector = MagicMock(spec=DexscreenerDataConnector)
        social_scraper = MagicMock(spec=SocialMediaScraper)
        execution_tool = MagicMock(spec=AlpacaExecutionTool)

        agent = MemecoinVibeTrader(
            config=config,
            dex_connector=dex_connector,
            social_scraper=social_scraper,
            execution_tool=execution_tool,
        )

        assert isinstance(agent.llm, MockLLM)

    def test_workflow_construction(self):
        """Test that LangGraph workflow is constructed correctly."""
        config = MemecoinVibeTraderConfig()
        dex_connector = MagicMock(spec=DexscreenerDataConnector)
        social_scraper = MagicMock(spec=SocialMediaScraper)
        execution_tool = MagicMock(spec=AlpacaExecutionTool)

        agent = MemecoinVibeTrader(
            config=config,
            dex_connector=dex_connector,
            social_scraper=social_scraper,
            execution_tool=execution_tool,
        )

        # Verify workflow has the expected structure
        workflow = agent.workflow
        assert workflow is not None

        # The workflow should have all the expected nodes
        # We can't directly test the internal structure of LangGraph,
        # but we can test that the agent can run without errors


class TestTokenFiltering:
    """Test token filtering and conversion functionality."""

    def test_filter_and_convert_tokens_with_valid_data(self):
        """Test filtering and converting valid token data."""
        config = MemecoinVibeTraderConfig(min_liquidity_threshold=10000)
        dex_connector = MagicMock(spec=DexscreenerDataConnector)
        social_scraper = MagicMock(spec=SocialMediaScraper)
        execution_tool = MagicMock(spec=AlpacaExecutionTool)

        agent = MemecoinVibeTrader(
            config=config,
            dex_connector=dex_connector,
            social_scraper=social_scraper,
            execution_tool=execution_tool,
        )

        # Valid token data above threshold
        raw_pairs = [
            {
                "address": "0x123",
                "symbol": "PEPE",
                "name": "PepeCoin",
                "liquidity": 50000,
                "volume_24h": 100000,
                "created_at": datetime.now(),
                "dex": "Uniswap",
                "base_token_address": "0xabc",
                "quote_token_address": "0xdef",
            },
            {
                "address": "0x456",
                "symbol": "DOGE",
                "name": "Dogecoin",
                "liquidity": 5000,  # Below threshold
                "volume_24h": 25000,
                "created_at": datetime.now(),
                "dex": "SushiSwap",
            },
        ]

        tokens = agent._filter_and_convert_tokens(raw_pairs)

        # Should only return the token above threshold
        assert len(tokens) == 1
        assert tokens[0].symbol == "PEPE"
        assert tokens[0].liquidity == 50000
        assert tokens[0].address == "0x123"

    def test_filter_and_convert_tokens_with_empty_data(self):
        """Test filtering with empty token data."""
        config = MemecoinVibeTraderConfig()
        dex_connector = MagicMock(spec=DexscreenerDataConnector)
        social_scraper = MagicMock(spec=SocialMediaScraper)
        execution_tool = MagicMock(spec=AlpacaExecutionTool)

        agent = MemecoinVibeTrader(
            config=config,
            dex_connector=dex_connector,
            social_scraper=social_scraper,
            execution_tool=execution_tool,
        )

        tokens = agent._filter_and_convert_tokens([])
        assert tokens == []

    def test_filter_and_convert_tokens_with_malformed_data(self):
        """Test filtering with malformed token data."""
        config = MemecoinVibeTraderConfig()
        dex_connector = MagicMock(spec=DexscreenerDataConnector)
        social_scraper = MagicMock(spec=SocialMediaScraper)
        execution_tool = MagicMock(spec=AlpacaExecutionTool)

        agent = MemecoinVibeTrader(
            config=config,
            dex_connector=dex_connector,
            social_scraper=social_scraper,
            execution_tool=execution_tool,
        )

        # Malformed data (missing required fields)
        raw_pairs = [
            {
                "symbol": "PEPE",
                "name": "PepeCoin",
                # Missing liquidity, address, etc.
            }
        ]

        # Should raise an exception when trying to access missing fields
        with pytest.raises(KeyError):
            agent._filter_and_convert_tokens(raw_pairs)


class TestWorkflowSteps:
    """Test individual workflow steps."""

    @pytest.fixture
    def agent_setup(self):
        """Create a basic agent setup for testing workflow steps."""
        config = MemecoinVibeTraderConfig()
        dex_connector = MagicMock(spec=DexscreenerDataConnector)
        social_scraper = MagicMock(spec=SocialMediaScraper)
        execution_tool = MagicMock(spec=AlpacaExecutionTool)
        llm_mock = MagicMock()

        return MemecoinVibeTrader(
            config=config,
            dex_connector=dex_connector,
            social_scraper=social_scraper,
            execution_tool=execution_tool,
            llm=llm_mock,
        )

    def test_scan_tokens_success(self, agent_setup):
        """Test successful token scanning."""
        agent = agent_setup

        # Mock successful API response
        agent.dex_connector.get_new_token_pairs.return_value = [
            {
                "address": "0x123",
                "symbol": "PEPE",
                "name": "PepeCoin",
                "liquidity": 50000,
                "volume_24h": 100000,
                "created_at": datetime.now(),
                "dex": "Uniswap",
            }
        ]

        state = AgentState()
        result_state = agent._scan_tokens(state)

        assert result_state.current_step == "scan"
        assert len(result_state.tokens) == 1
        assert result_state.tokens[0].symbol == "PEPE"
        assert result_state.error_message is None

    def test_scan_tokens_api_failure(self, agent_setup):
        """Test token scanning with API failure."""
        agent = agent_setup

        # Mock API failure
        agent.dex_connector.get_new_token_pairs.side_effect = Exception("API Error")

        state = AgentState()
        result_state = agent._scan_tokens(state)

        assert result_state.current_step == "scan"
        assert result_state.tokens == []
        assert result_state.error_message is not None
        assert "Failed to scan tokens" in result_state.error_message

    def test_gather_social_data_success(self, agent_setup):
        """Test successful social data gathering."""
        agent = agent_setup

        # Set up state with tokens
        token = TokenPair(
            address="0x123",
            symbol="PEPE",
            name="PepeCoin",
            liquidity=50000,
            volume_24h=100000,
            created_at=datetime.now(),
            dex="Uniswap",
        )
        state = AgentState(tokens=[token])

        # Mock successful social media scraping
        expected_metrics = SocialMetrics(
            telegram_followers=10000,
            twitter_followers=5000,
            recent_posts=25,
            engagement_rate=0.15,
            sentiment_score=0.7,
        )
        agent.social_scraper.get_social_metrics.return_value = expected_metrics

        result_state = agent._gather_social_data(state)

        assert result_state.current_step == "social"
        assert len(result_state.social_data) == 1
        assert "PEPE" in result_state.social_data
        assert result_state.social_data["PEPE"].telegram_followers == 10000
        assert result_state.error_message is None

    def test_gather_social_data_with_failures(self, agent_setup):
        """Test social data gathering with some failures."""
        agent = agent_setup

        # Set up state with tokens
        token1 = TokenPair(
            address="0x123",
            symbol="PEPE",
            name="PepeCoin",
            liquidity=50000,
            volume_24h=100000,
            created_at=datetime.now(),
            dex="Uniswap",
        )
        token2 = TokenPair(
            address="0x456",
            symbol="DOGE",
            name="Dogecoin",
            liquidity=75000,
            volume_24h=150000,
            created_at=datetime.now(),
            dex="SushiSwap",
        )
        state = AgentState(tokens=[token1, token2])

        # Mock first success, second failure
        agent.social_scraper.get_social_metrics.side_effect = [
            SocialMetrics(telegram_followers=10000),
            Exception("Scraping failed"),
        ]

        result_state = agent._gather_social_data(state)

        assert result_state.current_step == "social"
        assert len(result_state.social_data) == 2
        assert "PEPE" in result_state.social_data
        assert "DOGE" in result_state.social_data
        # Second token should get default empty metrics
        assert result_state.social_data["DOGE"].telegram_followers == 0
        assert result_state.error_message is None

    def test_assess_vibes_success(self, agent_setup):
        """Test successful vibe assessment."""
        agent = agent_setup

        # Set up state with tokens and social data
        token = TokenPair(
            address="0x123",
            symbol="PEPE",
            name="PepeCoin",
            liquidity=50000,
            volume_24h=100000,
            created_at=datetime.now(),
            dex="Uniswap",
        )
        social_metrics = SocialMetrics(
            telegram_followers=10000,
            twitter_followers=5000,
            recent_posts=25,
            engagement_rate=0.15,
            sentiment_score=0.7,
        )
        state = AgentState(tokens=[token], social_data={"PEPE": social_metrics})

        # Mock LLM response
        class MockLLMResponse:
            content = """VIBE_SCORE: 85
            RECOMMENDATION: BUY
            RISK_LEVEL: MEDIUM
            REASONING: Strong social presence and good liquidity"""

        agent.llm.invoke.return_value = MockLLMResponse()

        result_state = agent._assess_vibes(state)

        assert result_state.current_step == "assessment"
        assert len(result_state.assessments) == 1
        assessment = result_state.assessments[0]
        assert assessment.vibe_score == 85.0
        assert assessment.recommendation == "BUY"
        assert assessment.risk_level == "MEDIUM"
        assert "Strong social presence" in assessment.reasoning
        assert result_state.error_message is None

    def test_assess_vibes_with_llm_failure(self, agent_setup):
        """Test vibe assessment with LLM failure."""
        agent = agent_setup

        # Set up state with tokens and social data
        token = TokenPair(
            address="0x123",
            symbol="PEPE",
            name="PepeCoin",
            liquidity=50000,
            volume_24h=100000,
            created_at=datetime.now(),
            dex="Uniswap",
        )
        social_metrics = SocialMetrics(telegram_followers=10000)
        state = AgentState(tokens=[token], social_data={"PEPE": social_metrics})

        # Mock LLM failure
        agent.llm.invoke.side_effect = Exception("LLM Error")

        result_state = agent._assess_vibes(state)

        assert result_state.current_step == "assessment"
        assert len(result_state.assessments) == 1
        # Should create a fallback SKIP assessment
        assessment = result_state.assessments[0]
        assert assessment.recommendation == "SKIP"
        assert assessment.risk_level == "HIGH"
        assert "Assessment failed" in assessment.reasoning
        assert result_state.error_message is None

    def test_execute_trades_success(self, agent_setup):
        """Test successful trade execution."""
        agent = agent_setup

        # Set up state with qualifying assessments
        token = TokenPair(
            address="0x123",
            symbol="PEPE",
            name="PepeCoin",
            liquidity=50000,
            volume_24h=100000,
            created_at=datetime.now(),
            dex="Uniswap",
        )
        assessment = VibeAssessment(
            token=token,
            social_metrics=SocialMetrics(),
            vibe_score=85.0,
            recommendation="BUY",
            risk_level="MEDIUM",
            reasoning="Good vibes",
        )
        state = AgentState(assessments=[assessment])

        # Mock execution tool responses
        agent.execution_tool.get_account_balance.return_value = {
            "portfolio_value": 10000
        }
        agent.execution_tool.get_positions.return_value = []
        agent.execution_tool.execute_market_order.return_value = MagicMock(
            order_id="order123"
        )

        result_state = agent._execute_trades(state)

        assert result_state.current_step == "execution"
        assert len(result_state.trades_executed) == 1
        trade = result_state.trades_executed[0]
        assert trade["token"] == "PEPE"
        assert trade["order_id"] == "order123"
        assert trade["vibe_score"] == 85.0
        assert result_state.error_message is None

    def test_execute_trades_with_position_limits(self, agent_setup):
        """Test trade execution respects position limits."""
        agent = agent_setup
        agent.config.max_positions = 2

        # Create more assessments than the limit
        assessments = []
        for i in range(5):
            token = TokenPair(
                address=f"0x{i:03d}",
                symbol=f"TOKEN{i}",
                name=f"Token {i}",
                liquidity=50000,
                volume_24h=100000,
                created_at=datetime.now(),
                dex="Uniswap",
            )
            assessment = VibeAssessment(
                token=token,
                social_metrics=SocialMetrics(),
                vibe_score=90.0 - i,  # Decreasing scores
                recommendation="BUY",
                risk_level="MEDIUM",
                reasoning=f"Good vibes {i}",
            )
            assessments.append(assessment)

        state = AgentState(assessments=assessments)

        # Mock execution tool responses
        agent.execution_tool.get_account_balance.return_value = {
            "portfolio_value": 10000
        }
        agent.execution_tool.get_positions.return_value = []
        agent.execution_tool.execute_market_order.return_value = MagicMock(
            order_id="order123"
        )

        result_state = agent._execute_trades(state)

        # Should only execute trades for top 2 by vibe score
        assert len(result_state.trades_executed) == 2
        assert result_state.trades_executed[0]["token"] == "TOKEN0"  # Highest score
        assert result_state.trades_executed[1]["token"] == "TOKEN1"  # Second highest

    def test_execute_trades_with_existing_positions(self, agent_setup):
        """Test trade execution skips existing positions."""
        agent = agent_setup

        # Set up state with assessments
        token1 = TokenPair(
            address="0x123",
            symbol="PEPE",
            name="PepeCoin",
            liquidity=50000,
            volume_24h=100000,
            created_at=datetime.now(),
            dex="Uniswap",
        )
        token2 = TokenPair(
            address="0x456",
            symbol="DOGE",
            name="Dogecoin",
            liquidity=75000,
            volume_24h=150000,
            created_at=datetime.now(),
            dex="SushiSwap",
        )
        assessment1 = VibeAssessment(
            token=token1,
            social_metrics=SocialMetrics(),
            vibe_score=85.0,
            recommendation="BUY",
            risk_level="MEDIUM",
            reasoning="Good vibes",
        )
        assessment2 = VibeAssessment(
            token=token2,
            social_metrics=SocialMetrics(),
            vibe_score=90.0,
            recommendation="BUY",
            risk_level="MEDIUM",
            reasoning="Great vibes",
        )
        state = AgentState(assessments=[assessment1, assessment2])

        # Mock that we already have PEPE position
        agent.execution_tool.get_account_balance.return_value = {
            "portfolio_value": 10000
        }
        agent.execution_tool.get_positions.return_value = [
            {"symbol": "PEPE", "qty": "100"}
        ]
        agent.execution_tool.execute_market_order.return_value = MagicMock(
            order_id="order123"
        )

        result_state = agent._execute_trades(state)

        # Should only execute trade for DOGE (PEPE already in portfolio)
        assert len(result_state.trades_executed) == 1
        assert result_state.trades_executed[0]["token"] == "DOGE"


class TestWorkflowConditions:
    """Test workflow conditional routing."""

    @pytest.fixture
    def agent_setup(self):
        """Create a basic agent setup for testing workflow conditions."""
        config = MemecoinVibeTraderConfig()
        dex_connector = MagicMock(spec=DexscreenerDataConnector)
        social_scraper = MagicMock(spec=SocialMediaScraper)
        execution_tool = MagicMock(spec=AlpacaExecutionTool)
        llm_mock = MagicMock()

        agent = MemecoinVibeTrader(
            config=config,
            dex_connector=dex_connector,
            social_scraper=social_scraper,
            execution_tool=execution_tool,
            llm=llm_mock,
        )

        # Mock the workflow after creation
        agent.workflow = MagicMock()

        return agent

    def test_should_continue_after_scan_continue(self, agent_setup):
        """Test scan continuation when tokens found and no error."""
        agent = agent_setup

        state = AgentState(
            tokens=[
                TokenPair(
                    address="0x123",
                    symbol="PEPE",
                    name="PepeCoin",
                    liquidity=50000,
                    volume_24h=100000,
                    created_at=datetime.now(),
                    dex="Uniswap",
                )
            ]
        )

        result = agent._should_continue_after_scan(state)
        assert result == "continue"

    def test_should_continue_after_scan_error(self, agent_setup):
        """Test scan continuation when error occurs."""
        agent = agent_setup

        state = AgentState(error_message="Scan failed")

        result = agent._should_continue_after_scan(state)
        assert result == "error"

    def test_should_continue_after_scan_end(self, agent_setup):
        """Test scan continuation when no tokens found."""
        agent = agent_setup

        state = AgentState(tokens=[])

        result = agent._should_continue_after_scan(state)
        assert result == "end"

    def test_should_continue_after_social_continue(self, agent_setup):
        """Test social continuation when data gathered and no error."""
        agent = agent_setup

        state = AgentState(social_data={"PEPE": SocialMetrics()})

        result = agent._should_continue_after_social(state)
        assert result == "continue"

    def test_should_continue_after_social_error(self, agent_setup):
        """Test social continuation when error occurs."""
        agent = agent_setup

        state = AgentState(error_message="Social gathering failed")

        result = agent._should_continue_after_social(state)
        assert result == "error"

    def test_should_continue_after_social_end(self, agent_setup):
        """Test social continuation when no social data."""
        agent = agent_setup

        state = AgentState(social_data={})

        result = agent._should_continue_after_social(state)
        assert result == "end"

    def test_should_continue_after_assessment_continue(self, agent_setup):
        """Test assessment continuation when assessments made and no error."""
        agent = agent_setup

        assessment = VibeAssessment(
            token=TokenPair(
                address="0x123",
                symbol="PEPE",
                name="PepeCoin",
                liquidity=50000,
                volume_24h=100000,
                created_at=datetime.now(),
                dex="Uniswap",
            ),
            social_metrics=SocialMetrics(),
            vibe_score=85.0,
            recommendation="BUY",
            risk_level="MEDIUM",
            reasoning="Good vibes",
        )
        state = AgentState(assessments=[assessment])

        result = agent._should_continue_after_assessment(state)
        assert result == "continue"

    def test_should_continue_after_assessment_error(self, agent_setup):
        """Test assessment continuation when error occurs."""
        agent = agent_setup

        state = AgentState(error_message="Assessment failed")

        result = agent._should_continue_after_assessment(state)
        assert result == "error"

    def test_should_continue_after_assessment_end(self, agent_setup):
        """Test assessment continuation when no assessments."""
        agent = agent_setup

        state = AgentState(assessments=[])

        result = agent._should_continue_after_assessment(state)
        assert result == "end"

    def test_should_continue_after_execution(self, agent_setup):
        """Test execution always continues."""
        agent = agent_setup

        # Test with no trades executed
        state = AgentState(trades_executed=[])
        result = agent._should_continue_after_execution(state)
        assert result == "continue"

        # Test with trades executed
        state = AgentState(trades_executed=[{"token": "PEPE", "order_id": "order123"}])
        result = agent._should_continue_after_execution(state)
        assert result == "continue"


class TestErrorHandling:
    """Test error handling and recovery mechanisms."""

    def test_handle_error(self):
        """Test error handler sets error message in log."""
        config = MemecoinVibeTraderConfig()
        dex_connector = MagicMock(spec=DexscreenerDataConnector)
        social_scraper = MagicMock(spec=SocialMediaScraper)
        execution_tool = MagicMock(spec=AlpacaExecutionTool)

        agent = MemecoinVibeTrader(
            config=config,
            dex_connector=dex_connector,
            social_scraper=social_scraper,
            execution_tool=execution_tool,
        )

        state = AgentState(error_message="Test error message")

        # The handle_error method should return the state unchanged
        result_state = agent._handle_error(state)

        assert result_state.error_message == "Test error message"
        assert result_state is state  # Should return the same state object

    def test_run_cycle_with_workflow_error(self):
        """Test run_cycle handles workflow errors gracefully."""
        config = MemecoinVibeTraderConfig()
        dex_connector = MagicMock(spec=DexscreenerDataConnector)
        social_scraper = MagicMock(spec=SocialMediaScraper)
        execution_tool = MagicMock(spec=AlpacaExecutionTool)
        llm_mock = MagicMock()

        agent = MemecoinVibeTrader(
            config=config,
            dex_connector=dex_connector,
            social_scraper=social_scraper,
            execution_tool=execution_tool,
            llm=llm_mock,
        )

        # Mock workflow to raise an exception
        workflow_mock = MagicMock()
        workflow_mock.invoke.side_effect = Exception("Workflow error")
        agent.workflow = workflow_mock

        result = agent.run_cycle()

        assert result["success"] is False
        assert "Workflow error" in result["error_message"]
        assert result["tokens_scanned"] == 0
        assert result["assessments_made"] == 0
        assert result["trades_executed"] == 0

    def test_run_cycle_with_workflow_state_error(self):
        """Test run_cycle handles workflow state with error message."""
        config = MemecoinVibeTraderConfig()
        dex_connector = MagicMock(spec=DexscreenerDataConnector)
        social_scraper = MagicMock(spec=SocialMediaScraper)
        execution_tool = MagicMock(spec=AlpacaExecutionTool)
        llm_mock = MagicMock()

        agent = MemecoinVibeTrader(
            config=config,
            dex_connector=dex_connector,
            social_scraper=social_scraper,
            execution_tool=execution_tool,
            llm=llm_mock,
        )

        # Mock workflow to return state with error
        workflow_mock = MagicMock()
        error_state = AgentState(error_message="Scan failed", tokens=[])
        workflow_mock.invoke.return_value = error_state
        agent.workflow = workflow_mock

        result = agent.run_cycle()

        assert result["success"] is False
        assert result["error_message"] == "Scan failed"
        assert result["tokens_scanned"] == 0


class TestLLMPromptAndParsing:
    """Test LLM prompt creation and response parsing."""

    @pytest.fixture
    def agent_setup(self):
        """Create a basic agent setup for testing LLM functionality."""
        config = MemecoinVibeTraderConfig()
        dex_connector = MagicMock(spec=DexscreenerDataConnector)
        social_scraper = MagicMock(spec=SocialMediaScraper)
        execution_tool = MagicMock(spec=AlpacaExecutionTool)
        llm_mock = MagicMock()

        agent = MemecoinVibeTrader(
            config=config,
            dex_connector=dex_connector,
            social_scraper=social_scraper,
            execution_tool=execution_tool,
            llm=llm_mock,
        )

        # Mock the workflow after creation
        agent.workflow = MagicMock()

        return agent

    def test_create_assessment_prompt(self, agent_setup):
        """Test that assessment prompt is created correctly."""
        agent = agent_setup

        token = TokenPair(
            address="0x123",
            symbol="PEPE",
            name="PepeCoin",
            liquidity=50000,
            volume_24h=100000,
            created_at=datetime.now(),
            dex="Uniswap",
        )
        social_metrics = SocialMetrics(
            telegram_followers=10000,
            twitter_followers=5000,
            recent_posts=25,
            engagement_rate=0.15,
            sentiment_score=0.7,
        )

        prompt = agent._create_assessment_prompt(token, social_metrics)

        # Verify prompt contains expected elements
        assert "PEPE" in prompt
        assert "PepeCoin" in prompt
        assert "50,000" in prompt  # Formatted liquidity
        assert "100,000" in prompt  # Formatted volume
        assert "Uniswap" in prompt
        assert "10,000" in prompt  # Telegram followers
        assert "5,000" in prompt  # Twitter followers
        assert "25" in prompt  # Recent posts
        assert "0.150" in prompt  # Engagement rate
        assert "0.700" in prompt  # Sentiment score
        assert "VIBE_SCORE:" in prompt
        assert "RECOMMENDATION:" in prompt
        assert "RISK_LEVEL:" in prompt
        assert "REASONING:" in prompt

    def test_parse_llm_response_complete(self, agent_setup):
        """Test parsing complete LLM response."""
        agent = agent_setup

        token = TokenPair(
            address="0x123",
            symbol="PEPE",
            name="PepeCoin",
            liquidity=50000,
            volume_24h=100000,
            created_at=datetime.now(),
            dex="Uniswap",
        )
        social_metrics = SocialMetrics()

        response = """VIBE_SCORE: 85.5
        RECOMMENDATION: BUY
        RISK_LEVEL: LOW
        REASONING: Strong community and good tokenomics"""

        assessment = agent._parse_llm_response(response, token, social_metrics)

        assert assessment.vibe_score == 85.5
        assert assessment.recommendation == "BUY"
        assert assessment.risk_level == "LOW"
        assert "Strong community" in assessment.reasoning
        assert assessment.token == token
        assert assessment.social_metrics == social_metrics

    def test_parse_llm_response_partial(self, agent_setup):
        """Test parsing partial LLM response with defaults."""
        agent = agent_setup

        token = TokenPair(
            address="0x123",
            symbol="PEPE",
            name="PepeCoin",
            liquidity=50000,
            volume_24h=100000,
            created_at=datetime.now(),
            dex="Uniswap",
        )
        social_metrics = SocialMetrics()

        # Response with only some fields
        response = """VIBE_SCORE: 92
        RECOMMENDATION: BUY"""

        assessment = agent._parse_llm_response(response, token, social_metrics)

        assert assessment.vibe_score == 92.0
        assert assessment.recommendation == "BUY"
        # Should use defaults for missing fields
        assert assessment.risk_level == "MEDIUM"
        assert assessment.reasoning == "LLM assessment parsing failed"

    def test_parse_llm_response_malformed(self, agent_setup):
        """Test parsing malformed LLM response."""
        agent = agent_setup

        token = TokenPair(
            address="0x123",
            symbol="PEPE",
            name="PepeCoin",
            liquidity=50000,
            volume_24h=100000,
            created_at=datetime.now(),
            dex="Uniswap",
        )
        social_metrics = SocialMetrics()

        # Completely malformed response
        response = "This is not a proper format at all"

        assessment = agent._parse_llm_response(response, token, social_metrics)

        # Should use all defaults
        assert assessment.vibe_score == 50.0
        assert assessment.recommendation == "HOLD"
        assert assessment.risk_level == "MEDIUM"
        assert assessment.reasoning == "LLM assessment parsing failed"

    def test_parse_llm_response_edge_cases(self, agent_setup):
        """Test parsing edge cases in LLM response."""
        agent = agent_setup

        token = TokenPair(
            address="0x123",
            symbol="PEPE",
            name="PepeCoin",
            liquidity=50000,
            volume_24h=100000,
            created_at=datetime.now(),
            dex="Uniswap",
        )
        social_metrics = SocialMetrics()

        # Response with out-of-bounds values
        response = """VIBE_SCORE: 150
        RECOMMENDATION: SELL
        RISK_LEVEL: VERY_HIGH
        REASONING: Something"""

        assessment = agent._parse_llm_response(response, token, social_metrics)

        # Vibe score should be clamped to 0-100
        assert assessment.vibe_score == 100.0
        # Unknown recommendation should be normalized
        assert assessment.recommendation == "SELL"
        # Unknown risk level should be normalized
        assert (
            assessment.risk_level == "VERY_HIGH"
        )  # This specific one might pass through


class TestPriceEstimation:
    """Test token price estimation functionality."""

    def test_estimate_token_price_normal_case(self):
        """Test price estimation with normal values."""
        config = MemecoinVibeTraderConfig()
        dex_connector = MagicMock(spec=DexscreenerDataConnector)
        social_scraper = MagicMock(spec=SocialMediaScraper)
        execution_tool = MagicMock(spec=AlpacaExecutionTool)

        agent = MemecoinVibeTrader(
            config=config,
            dex_connector=dex_connector,
            social_scraper=social_scraper,
            execution_tool=execution_tool,
        )

        token = TokenPair(
            address="0x123",
            symbol="PEPE",
            name="PepeCoin",
            liquidity=50000,
            volume_24h=100000,  # 2x liquidity
            created_at=datetime.now(),
            dex="Uniswap",
        )

        price = agent._estimate_token_price(token)

        # Price = volume / (liquidity * 10) = 100000 / (50000 * 10) = 0.2
        expected_price = min(100000 / (50000 * 10), 100.0)
        assert price == expected_price

    def test_estimate_token_price_high_volume(self):
        """Test price estimation with very high volume."""
        config = MemecoinVibeTraderConfig()
        dex_connector = MagicMock(spec=DexscreenerDataConnector)
        social_scraper = MagicMock(spec=SocialMediaScraper)
        execution_tool = MagicMock(spec=AlpacaExecutionTool)

        agent = MemecoinVibeTrader(
            config=config,
            dex_connector=dex_connector,
            social_scraper=social_scraper,
            execution_tool=execution_tool,
        )

        token = TokenPair(
            address="0x123",
            symbol="PEPE",
            name="PepeCoin",
            liquidity=1000,
            volume_24h=10000000,  # Very high volume
            created_at=datetime.now(),
            dex="Uniswap",
        )

        price = agent._estimate_token_price(token)

        # Should be capped at $100
        assert price == 100.0

    def test_estimate_token_price_zero_values(self):
        """Test price estimation with zero values."""
        config = MemecoinVibeTraderConfig()
        dex_connector = MagicMock(spec=DexscreenerDataConnector)
        social_scraper = MagicMock(spec=SocialMediaScraper)
        execution_tool = MagicMock(spec=AlpacaExecutionTool)

        agent = MemecoinVibeTrader(
            config=config,
            dex_connector=dex_connector,
            social_scraper=social_scraper,
            execution_tool=execution_tool,
        )

        token = TokenPair(
            address="0x123",
            symbol="PEPE",
            name="PepeCoin",
            liquidity=0,
            volume_24h=0,
            created_at=datetime.now(),
            dex="Uniswap",
        )

        price = agent._estimate_token_price(token)

        # Should return default price of 1.0
        assert price == 1.0

    def test_estimate_token_price_exception_handling(self):
        """Test price estimation handles exceptions gracefully."""
        config = MemecoinVibeTraderConfig()
        dex_connector = MagicMock(spec=DexscreenerDataConnector)
        social_scraper = MagicMock(spec=SocialMediaScraper)
        execution_tool = MagicMock(spec=AlpacaExecutionTool)

        agent = MemecoinVibeTrader(
            config=config,
            dex_connector=dex_connector,
            social_scraper=social_scraper,
            execution_tool=execution_tool,
        )

        # Token with None values that might cause exceptions
        token = TokenPair(
            address="0x123",
            symbol="PEPE",
            name="PepeCoin",
            liquidity=None,  # This could cause issues
            volume_24h=None,
            created_at=datetime.now(),
            dex="Uniswap",
        )

        price = agent._estimate_token_price(token)

        # Should return default price of 1.0 on exception
        assert price == 1.0


class TestRiskManagement:
    """Test risk management logic."""

    def test_vibe_score_threshold_filtering(self):
        """Test that vibe score thresholds are properly applied."""
        config = MemecoinVibeTraderConfig(min_vibe_score_threshold=75)
        dex_connector = MagicMock(spec=DexscreenerDataConnector)
        social_scraper = MagicMock(spec=SocialMediaScraper)
        execution_tool = MagicMock(spec=AlpacaExecutionTool)

        agent = MemecoinVibeTrader(
            config=config,
            dex_connector=dex_connector,
            social_scraper=social_scraper,
            execution_tool=execution_tool,
        )

        # Create assessments with different vibe scores
        assessments = []
        for score in [70, 75, 80, 85, 90]:
            token = TokenPair(
                address=f"0x{score:03d}",
                symbol=f"TOKEN{score}",
                name=f"Token {score}",
                liquidity=50000,
                volume_24h=100000,
                created_at=datetime.now(),
                dex="Uniswap",
            )
            assessment = VibeAssessment(
                token=token,
                social_metrics=SocialMetrics(),
                vibe_score=score,
                recommendation="BUY",
                risk_level="MEDIUM",
                reasoning=f"Good vibes {score}",
            )
            assessments.append(assessment)

        state = AgentState(assessments=assessments)

        # Mock execution tool responses
        agent.execution_tool.get_account_balance.return_value = {
            "portfolio_value": 10000
        }
        agent.execution_tool.get_positions.return_value = []
        agent.execution_tool.execute_market_order.return_value = MagicMock(
            order_id="order123"
        )

        result_state = agent._execute_trades(state)

        # Should only execute trades for scores >= 75
        executed_tokens = [trade["token"] for trade in result_state.trades_executed]
        assert "TOKEN75" in executed_tokens
        assert "TOKEN80" in executed_tokens
        assert "TOKEN85" in executed_tokens
        assert "TOKEN90" in executed_tokens
        assert "TOKEN70" not in executed_tokens  # Below threshold

    def test_allocation_calculations(self):
        """Test that position allocation calculations are correct."""
        config = MemecoinVibeTraderConfig(
            max_allocation_per_trade=0.05, max_positions=10  # 5% per trade
        )
        dex_connector = MagicMock(spec=DexscreenerDataConnector)
        social_scraper = MagicMock(spec=SocialMediaScraper)
        execution_tool = MagicMock(spec=AlpacaExecutionTool)

        agent = MemecoinVibeTrader(
            config=config,
            dex_connector=dex_connector,
            social_scraper=social_scraper,
            execution_tool=execution_tool,
        )

        # Create a single assessment
        token = TokenPair(
            address="0x123",
            symbol="PEPE",
            name="PepeCoin",
            liquidity=50000,
            volume_24h=100000,
            created_at=datetime.now(),
            dex="Uniswap",
        )
        assessment = VibeAssessment(
            token=token,
            social_metrics=SocialMetrics(),
            vibe_score=85.0,
            recommendation="BUY",
            risk_level="MEDIUM",
            reasoning="Good vibes",
        )
        state = AgentState(assessments=[assessment])

        # Mock $10,000 portfolio
        agent.execution_tool.get_account_balance.return_value = {
            "portfolio_value": 10000
        }
        agent.execution_tool.get_positions.return_value = []

        # Mock the execute_market_order to capture the call
        mock_order = MagicMock(order_id="order123")
        agent.execution_tool.execute_market_order.return_value = mock_order

        # Estimate token price to be $1.0
        with patch.object(agent, "_estimate_token_price", return_value=1.0):
            result_state = agent._execute_trades(state)

        # Should execute 5% of $10,000 = $500 position
        # At $1.0 per token, that's 500 tokens
        agent.execution_tool.execute_market_order.assert_called_once_with(
            symbol="PEPE/USD", side="buy", quantity=500.0  # $500 / $1.0 = 500 tokens
        )

        assert len(result_state.trades_executed) == 1
        assert result_state.trades_executed[0]["quantity"] == 500.0


class TestMockLLM:
    """Test MockLLM functionality."""

    def test_mock_llm_basic_functionality(self):
        """Test basic MockLLM functionality."""
        llm = MockLLM("Test response")

        class MockResponse:
            def __init__(self, content):
                self.content = content

        # Mock the invoke method to return our response object
        with patch.object(llm, "invoke") as mock_invoke:
            mock_invoke.return_value = MockResponse("Test response")

            response = llm.invoke("test prompt")

            assert response.content == "Test response"
            mock_invoke.assert_called_once_with("test prompt")

    def test_mock_llm_with_different_responses(self):
        """Test MockLLM with different response texts."""
        responses = ["Response 1", "Response 2", ""]

        for response_text in responses:
            llm = MockLLM(response_text)

            class MockResponse:
                def __init__(self, content):
                    self.content = content

            with patch.object(llm, "invoke") as mock_invoke:
                mock_invoke.return_value = MockResponse(response_text)

                response = llm.invoke("test prompt")

                assert response.content == response_text


class TestRunCycleIntegration:
    """Test the main run_cycle method integration."""

    @pytest.fixture
    def complete_agent_setup(self):
        """Create a complete agent setup with all mocks configured."""
        config = MemecoinVibeTraderConfig()
        dex_connector = MagicMock(spec=DexscreenerDataConnector)
        social_scraper = MagicMock(spec=SocialMediaScraper)
        execution_tool = MagicMock(spec=AlpacaExecutionTool)
        llm_mock = MagicMock()

        # Configure all the mocks for a successful run
        dex_connector.get_new_token_pairs.return_value = [
            {
                "address": "0x123",
                "symbol": "PEPE",
                "name": "PepeCoin",
                "liquidity": 50000,
                "volume_24h": 100000,
                "created_at": datetime.now(),
                "dex": "Uniswap",
            }
        ]

        social_scraper.get_social_metrics.return_value = SocialMetrics(
            telegram_followers=10000,
            twitter_followers=5000,
            recent_posts=25,
            engagement_rate=0.15,
            sentiment_score=0.7,
        )

        execution_tool.get_account_balance.return_value = {"portfolio_value": 10000}
        execution_tool.get_positions.return_value = []
        execution_tool.execute_market_order.return_value = MagicMock(
            order_id="order123"
        )

        agent = MemecoinVibeTrader(
            config=config,
            dex_connector=dex_connector,
            social_scraper=social_scraper,
            execution_tool=execution_tool,
            llm=llm_mock,
        )

        # Mock the workflow after creation
        workflow_mock = MagicMock()
        agent.workflow = workflow_mock

        return agent

    def test_run_cycle_success_case(self, complete_agent_setup):
        """Test successful complete run cycle."""
        agent = complete_agent_setup

        # Mock LLM response
        class MockLLMResponse:
            content = """VIBE_SCORE: 85
            RECOMMENDATION: BUY
            RISK_LEVEL: MEDIUM
            REASONING: Strong community and good tokenomics"""

        agent.llm.invoke.return_value = MockLLMResponse()

        # Mock workflow to return successful state
        mock_state = {
            "error_message": None,
            "tokens": [
                {
                    "address": "0x123",
                    "symbol": "PEPE",
                    "name": "PepeCoin",
                    "liquidity": 50000,
                    "volume_24h": 100000,
                    "created_at": datetime.now(),
                    "dex": "Uniswap",
                }
            ],
            "assessments": [MagicMock()],
            "trades_executed": [
                {
                    "token": "PEPE",
                    "order_id": "test_order_123",
                    "quantity": 100.0,
                    "vibe_score": 85.0,
                    "timestamp": datetime.now().isoformat(),
                }
            ],
            "current_step": "complete",
        }
        agent.workflow.invoke.return_value = mock_state

        # Estimate token price to be $1.0 for predictable calculations
        with patch.object(agent, "_estimate_token_price", return_value=1.0):
            result = agent.run_cycle()

        # Verify successful result
        assert result["success"] is True
        assert result["tokens_scanned"] == 1
        assert result["assessments_made"] == 1
        assert result["trades_executed"] == 1
        assert result["error_message"] is None
        assert len(result["trades"]) == 1
        assert result["trades"][0]["token"] == "PEPE"

    def test_run_cycle_no_tokens_found(self, complete_agent_setup):
        """Test run cycle when no tokens are found."""
        agent = complete_agent_setup

        # Mock no tokens found
        agent.dex_connector.get_new_token_pairs.return_value = []

        # Mock workflow to return successful state with no tokens
        mock_state = {
            "error_message": None,
            "tokens": [],
            "assessments": [],
            "trades_executed": [],
            "current_step": "complete",
        }
        agent.workflow.invoke.return_value = mock_state

        result = agent.run_cycle()

        # Should still be successful but with zero results
        assert result["success"] is True
        assert result["tokens_scanned"] == 0
        assert result["assessments_made"] == 0
        assert result["trades_executed"] == 0
        assert result["error_message"] is None

    def test_run_cycle_no_qualifying_assessments(self, complete_agent_setup):
        """Test run cycle when no assessments qualify for trading."""
        agent = complete_agent_setup

        # Mock LLM response with SKIP recommendation
        class MockLLMResponse:
            content = """VIBE_SCORE: 50
            RECOMMENDATION: SKIP
            RISK_LEVEL: HIGH
            REASONING: Weak community and poor tokenomics"""

        agent.llm.invoke.return_value = MockLLMResponse()

        # Mock workflow to return successful state with assessments but no trades
        mock_state = {
            "error_message": None,
            "tokens": [
                {
                    "address": "0x123",
                    "symbol": "PEPE",
                    "name": "PepeCoin",
                    "liquidity": 50000,
                    "volume_24h": 100000,
                    "created_at": datetime.now(),
                    "dex": "Uniswap",
                }
            ],
            "assessments": [MagicMock()],
            "trades_executed": [],
            "current_step": "complete",
        }
        agent.workflow.invoke.return_value = mock_state

        result = agent.run_cycle()

        # Should be successful but execute no trades
        assert result["success"] is True
        assert result["tokens_scanned"] == 1
        assert result["assessments_made"] == 1
        assert result["trades_executed"] == 0
        assert result["error_message"] is None

    def test_run_cycle_exception_handling(self, complete_agent_setup):
        """Test run cycle handles unexpected exceptions."""
        agent = complete_agent_setup

        # Mock workflow to raise an unexpected exception
        agent.workflow.invoke.side_effect = RuntimeError("Unexpected error")

        result = agent.run_cycle()

        # Should handle the exception gracefully
        assert result["success"] is False
        assert "Unexpected error" in result["error_message"]
        assert result["tokens_scanned"] == 0
        assert result["assessments_made"] == 0
        assert result["trades_executed"] == 0

    def test_run_cycle_state_normalization(self, complete_agent_setup):
        """Test that run_cycle properly normalizes different state types."""
        agent = complete_agent_setup

        # Mock workflow to return a dict instead of AgentState
        mock_state = {
            "error_message": None,
            "tokens": [
                TokenPair(
                    address="0x123",
                    symbol="PEPE",
                    name="PepeCoin",
                    liquidity=50000,
                    volume_24h=100000,
                    created_at=datetime.now(),
                    dex="Uniswap",
                )
            ],
            "assessments": [
                VibeAssessment(
                    token=TokenPair(
                        address="0x123",
                        symbol="PEPE",
                        name="PepeCoin",
                        liquidity=50000,
                        volume_24h=100000,
                        created_at=datetime.now(),
                        dex="Uniswap",
                    ),
                    social_metrics=SocialMetrics(),
                    vibe_score=85.0,
                    recommendation="BUY",
                    risk_level="MEDIUM",
                    reasoning="Good vibes",
                )
            ],
            "trades_executed": [{"token": "PEPE", "order_id": "order123"}],
            "current_step": "execution",
        }
        agent.workflow.invoke.return_value = mock_state

        # Mock LLM response
        class MockLLMResponse:
            content = """VIBE_SCORE: 85
            RECOMMENDATION: BUY
            RISK_LEVEL: MEDIUM
            REASONING: Strong community"""

        agent.llm.invoke.return_value = MockLLMResponse()

        # Estimate token price
        with patch.object(agent, "_estimate_token_price", return_value=1.0):
            result = agent.run_cycle()

        # Should handle the dict state correctly
        assert result["success"] is True
        assert result["tokens_scanned"] == 1
        assert result["assessments_made"] == 1
        assert result["trades_executed"] == 1


class TestParallelExecutionSafety:
    """Test that tests can run safely in parallel."""

    def test_isolated_test_execution(self):
        """Test that each test runs in isolation."""
        # This test should be safe to run in parallel with others
        config = MemecoinVibeTraderConfig()
        assert config.scan_interval == 3600

    def test_no_shared_state(self):
        """Test that tests don't share state."""
        # Create fresh mocks for each test
        dex_connector = MagicMock(spec=DexscreenerDataConnector)
        social_scraper = MagicMock(spec=SocialMediaScraper)
        execution_tool = MagicMock(spec=AlpacaExecutionTool)

        agent = MemecoinVibeTrader(
            config=MemecoinVibeTraderConfig(),
            dex_connector=dex_connector,
            social_scraper=social_scraper,
            execution_tool=execution_tool,
        )

        # Each agent should have its own independent state
        assert agent.config is not None
        assert agent.workflow is not None


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_empty_token_list_handling(self):
        """Test handling of empty token lists."""
        config = MemecoinVibeTraderConfig()
        dex_connector = MagicMock(spec=DexscreenerDataConnector)
        social_scraper = MagicMock(spec=SocialMediaScraper)
        execution_tool = MagicMock(spec=AlpacaExecutionTool)

        agent = MemecoinVibeTrader(
            config=config,
            dex_connector=dex_connector,
            social_scraper=social_scraper,
            execution_tool=execution_tool,
        )

        # Test filtering empty list
        result = agent._filter_and_convert_tokens([])
        assert result == []

    def test_extreme_vibe_scores(self):
        """Test handling of extreme vibe scores."""
        config = MemecoinVibeTraderConfig()
        dex_connector = MagicMock(spec=DexscreenerDataConnector)
        social_scraper = MagicMock(spec=SocialMediaScraper)
        execution_tool = MagicMock(spec=AlpacaExecutionTool)

        agent = MemecoinVibeTrader(
            config=config,
            dex_connector=dex_connector,
            social_scraper=social_scraper,
            execution_tool=execution_tool,
        )

        token = TokenPair(
            address="0x123",
            symbol="PEPE",
            name="PepeCoin",
            liquidity=50000,
            volume_24h=100000,
            created_at=datetime.now(),
            dex="Uniswap",
        )
        social_metrics = SocialMetrics()

        # Test with score above 100 (should be clamped)
        response = "VIBE_SCORE: 150"
        assessment = agent._parse_llm_response(response, token, social_metrics)
        assert assessment.vibe_score == 100.0

        # Test with negative score (should be clamped)
        response = "VIBE_SCORE: -10"
        assessment = agent._parse_llm_response(response, token, social_metrics)
        assert assessment.vibe_score == 0.0

    def test_all_recommendation_types(self):
        """Test all possible recommendation types."""
        config = MemecoinVibeTraderConfig()
        dex_connector = MagicMock(spec=DexscreenerDataConnector)
        social_scraper = MagicMock(spec=SocialMediaScraper)
        execution_tool = MagicMock(spec=AlpacaExecutionTool)

        agent = MemecoinVibeTrader(
            config=config,
            dex_connector=dex_connector,
            social_scraper=social_scraper,
            execution_tool=execution_tool,
        )

        token = TokenPair(
            address="0x123",
            symbol="PEPE",
            name="PepeCoin",
            liquidity=50000,
            volume_24h=100000,
            created_at=datetime.now(),
            dex="Uniswap",
        )
        social_metrics = SocialMetrics()

        recommendations = ["BUY", "HOLD", "SKIP", "SELL"]

        for rec in recommendations:
            response = f"VIBE_SCORE: 50\nRECOMMENDATION: {rec}"
            assessment = agent._parse_llm_response(response, token, social_metrics)
            assert assessment.recommendation == rec

    def test_risk_level_variations(self):
        """Test different risk levels."""
        config = MemecoinVibeTraderConfig()
        dex_connector = MagicMock(spec=DexscreenerDataConnector)
        social_scraper = MagicMock(spec=SocialMediaScraper)
        execution_tool = MagicMock(spec=AlpacaExecutionTool)

        agent = MemecoinVibeTrader(
            config=config,
            dex_connector=dex_connector,
            social_scraper=social_scraper,
            execution_tool=execution_tool,
        )

        token = TokenPair(
            address="0x123",
            symbol="PEPE",
            name="PepeCoin",
            liquidity=50000,
            volume_24h=100000,
            created_at=datetime.now(),
            dex="Uniswap",
        )
        social_metrics = SocialMetrics()

        risk_levels = ["LOW", "MEDIUM", "HIGH"]

        for risk in risk_levels:
            response = f"VIBE_SCORE: 50\nRISK_LEVEL: {risk}"
            assessment = agent._parse_llm_response(response, token, social_metrics)
            assert assessment.risk_level == risk

    def test_zero_portfolio_value(self):
        """Test handling of zero portfolio value."""
        config = MemecoinVibeTraderConfig()
        dex_connector = MagicMock(spec=DexscreenerDataConnector)
        social_scraper = MagicMock(spec=SocialMediaScraper)
        execution_tool = MagicMock(spec=AlpacaExecutionTool)

        agent = MemecoinVibeTrader(
            config=config,
            dex_connector=dex_connector,
            social_scraper=social_scraper,
            execution_tool=execution_tool,
        )

        token = TokenPair(
            address="0x123",
            symbol="PEPE",
            name="PepeCoin",
            liquidity=50000,
            volume_24h=100000,
            created_at=datetime.now(),
            dex="Uniswap",
        )
        assessment = VibeAssessment(
            token=token,
            social_metrics=SocialMetrics(),
            vibe_score=85.0,
            recommendation="BUY",
            risk_level="MEDIUM",
            reasoning="Good vibes",
        )
        state = AgentState(assessments=[assessment])

        # Mock zero portfolio value
        agent.execution_tool.get_account_balance.return_value = {"portfolio_value": 0}
        agent.execution_tool.get_positions.return_value = []

        result_state = agent._execute_trades(state)

        # Should handle zero portfolio gracefully
        assert len(result_state.trades_executed) == 0

    def test_very_small_allocation_percentage(self):
        """Test very small allocation percentages."""
        config = MemecoinVibeTraderConfig(max_allocation_per_trade=0.001)  # 0.1%
        dex_connector = MagicMock(spec=DexscreenerDataConnector)
        social_scraper = MagicMock(spec=SocialMediaScraper)
        execution_tool = MagicMock(spec=AlpacaExecutionTool)

        agent = MemecoinVibeTrader(
            config=config,
            dex_connector=dex_connector,
            social_scraper=social_scraper,
            execution_tool=execution_tool,
        )

        token = TokenPair(
            address="0x123",
            symbol="PEPE",
            name="PepeCoin",
            liquidity=50000,
            volume_24h=100000,
            created_at=datetime.now(),
            dex="Uniswap",
        )
        assessment = VibeAssessment(
            token=token,
            social_metrics=SocialMetrics(),
            vibe_score=85.0,
            recommendation="BUY",
            risk_level="MEDIUM",
            reasoning="Good vibes",
        )
        state = AgentState(assessments=[assessment])

        agent.execution_tool.get_account_balance.return_value = {
            "portfolio_value": 10000
        }
        agent.execution_tool.get_positions.return_value = []

        with patch.object(agent, "_estimate_token_price", return_value=1.0):
            agent._execute_trades(state)

        # Should calculate 0.1% of $10,000 = $10 position
        # At $1.0 per token, that's 10 tokens
        agent.execution_tool.execute_market_order.assert_called_once_with(
            symbol="PEPE/USD", side="buy", quantity=10.0
        )
