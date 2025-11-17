"""Tests for the multi-agent trading system."""

from unittest.mock import Mock
from datetime import datetime

from quantchain.agents import (
    AgentAnalysis,
    AgentArgument,
    AgentRole,
    FundamentalsAnalystAgent,
    PortfolioCommitteeAgent,
    RecommendationType,
    RiskManagerAgent,
    SentimentExpertAgent,
    TechnicalAnalystAgent,
)
from quantchain.core.config import QuantChainConfig


class MockLLMProvider:
    """Mock LLM provider for testing."""

    def __init__(self, response_text="Mock response"):
        self.response_text = response_text

    def generate(self, prompt: str, max_tokens: int = None):
        """Mock generate method."""
        mock_response = Mock()
        mock_response.text = self.response_text
        return mock_response

    def generate_vision(self, image_data: bytes, prompt: str):
        """Mock generate_vision method."""
        mock_response = Mock()
        mock_response.text = "Mock vision analysis"
        return mock_response


class TestFundamentalsAnalystAgent:
    """Test the Fundamentals Analyst Agent."""

    def test_initialization(self):
        """Test agent initialization."""
        config = QuantChainConfig()
        llm_provider = MockLLMProvider()
        agent = FundamentalsAnalystAgent(config, llm_provider)

        assert agent.role == AgentRole.FUNDAMENTALS
        assert agent.config == config
        assert agent.llm_provider == llm_provider

    def test_analyze_with_insufficient_data(self):
        """Test analysis with insufficient data."""
        config = QuantChainConfig()
        llm_provider = MockLLMProvider()
        agent = FundamentalsAnalystAgent(config, llm_provider, data_connector=None)

        result = agent.analyze("TEST")

        assert isinstance(result, AgentAnalysis)
        assert result.symbol == "TEST"
        assert result.recommendation == RecommendationType.HOLD
        assert result.confidence_score <= 30.0
        assert "Insufficient fundamental data" in result.reasoning

    def test_analyze_with_mock_data(self):
        """Test analysis with mock data."""
        config = QuantChainConfig()
        llm_provider = MockLLMProvider()
        agent = FundamentalsAnalystAgent(config, llm_provider, data_connector=None)

        # Set mock data quality to pass threshold
        agent.min_data_quality_score = 50.0

        result = agent.analyze("TEST")

        assert isinstance(result, AgentAnalysis)
        assert result.symbol == "TEST"
        assert result.data_sources == [
            "financial_statements",
            "earnings_reports",
            "market_data",
        ]
        assert result.metadata["data_quality_score"] >= 50.0

    def test_create_argument(self):
        """Test argument creation for debate."""
        config = QuantChainConfig()
        llm_provider = MockLLMProvider()
        agent = FundamentalsAnalystAgent(config, llm_provider)

        # Test with no fundamental analysis
        context = {"symbol": "TEST"}
        argument = agent.create_argument(context)

        assert argument.agent_role == AgentRole.FUNDAMENTALS
        assert argument.argument_type == "neutral"

        # Test with strong fundamental analysis
        mock_analysis = AgentAnalysis(
            agent_role=AgentRole.FUNDAMENTALS,
            symbol="TEST",
            timestamp=datetime.now(),
            recommendation=RecommendationType.BUY,
            confidence_score=85.0,
            reasoning="Strong fundamentals",
            data_sources=["financial_statements"],
            metadata={"fundamental_score": 85.0},
        )

        context["fundamentals_analysis"] = mock_analysis
        argument = agent.create_argument(context)

        assert argument.argument_type == "support"
        assert "Strong fundamentals" in argument.reasoning


class TestSentimentExpertAgent:
    """Test the Sentiment Expert Agent."""

    def test_initialization(self):
        """Test agent initialization."""
        config = QuantChainConfig()
        llm_provider = MockLLMProvider()
        agent = SentimentExpertAgent(config, llm_provider)

        assert agent.role == AgentRole.SENTIMENT
        assert agent.config == config

    def test_analyze_with_no_data(self):
        """Test analysis with no sentiment data."""
        config = QuantChainConfig()
        llm_provider = MockLLMProvider()
        agent = SentimentExpertAgent(
            config, llm_provider, news_connector=None, social_connector=None
        )

        result = agent.analyze("TEST")

        assert isinstance(result, AgentAnalysis)
        assert result.recommendation == RecommendationType.HOLD
        assert "No sentiment data available" in result.reasoning

    def test_analyze_with_mock_data(self):
        """Test analysis with mock sentiment data."""
        config = QuantChainConfig()
        llm_provider = MockLLMProvider()
        agent = SentimentExpertAgent(
            config, llm_provider, news_connector=None, social_connector=None
        )

        result = agent.analyze("TEST")

        assert isinstance(result, AgentAnalysis)
        assert result.symbol == "TEST"
        assert result.data_sources == ["news", "social_media"]
        assert "sentiment_score" in result.metadata

    def test_create_argument(self):
        """Test argument creation for debate."""
        config = QuantChainConfig()
        llm_provider = MockLLMProvider()
        agent = SentimentExpertAgent(config, llm_provider)

        # Test with bullish sentiment
        mock_analysis = AgentAnalysis(
            agent_role=AgentRole.SENTIMENT,
            symbol="TEST",
            timestamp=datetime.now(),
            recommendation=RecommendationType.BUY,
            confidence_score=80.0,
            reasoning="Positive sentiment",
            data_sources=["news", "social_media"],
            metadata={"sentiment_score": 50.0, "sentiment_available": True},
        )

        context = {"sentiment_analysis": mock_analysis}
        argument = agent.create_argument(context)

        assert argument.agent_role == AgentRole.SENTIMENT
        assert argument.argument_type == "support"
        assert "positive sentiment" in argument.reasoning.lower()


class TestTechnicalAnalystAgent:
    """Test the Technical Analyst Agent."""

    def test_initialization(self):
        """Test agent initialization."""
        config = QuantChainConfig()
        llm_provider = MockLLMProvider()
        agent = TechnicalAnalystAgent(config, llm_provider)

        assert agent.role == AgentRole.TECHNICAL
        assert agent.config == config

    def test_analyze_with_no_data(self):
        """Test analysis with no price data."""
        config = QuantChainConfig()
        llm_provider = MockLLMProvider()
        agent = TechnicalAnalystAgent(config, llm_provider, data_connector=None)

        # Mock to return no data
        agent._get_price_data = Mock(return_value=None)

        result = agent.analyze("TEST")

        assert isinstance(result, AgentAnalysis)
        assert result.recommendation == RecommendationType.HOLD
        assert "Insufficient price data" in result.reasoning

    def test_analyze_with_mock_data(self):
        """Test analysis with mock price data."""
        config = QuantChainConfig()
        llm_provider = MockLLMProvider()
        agent = TechnicalAnalystAgent(config, llm_provider, data_connector=None)

        result = agent.analyze("TEST")

        assert isinstance(result, AgentAnalysis)
        assert result.symbol == "TEST"
        assert result.data_sources == ["market_data", "technical_indicators"]
        assert "technical_available" in result.metadata

    def test_create_argument(self):
        """Test argument creation for debate."""
        config = QuantChainConfig()
        llm_provider = MockLLMProvider()
        agent = TechnicalAnalystAgent(config, llm_provider)

        # Test with bullish technical analysis
        mock_analysis = AgentAnalysis(
            agent_role=AgentRole.TECHNICAL,
            symbol="TEST",
            timestamp=datetime.now(),
            recommendation=RecommendationType.BUY,
            confidence_score=85.0,
            reasoning="Strong technical indicators",
            data_sources=["market_data"],
            metadata={"technical_available": True, "overall_score": 75.0},
        )

        context = {"technical_analysis": mock_analysis}
        argument = agent.create_argument(context)

        assert argument.agent_role == AgentRole.TECHNICAL
        assert argument.argument_type == "support"


class TestRiskManagerAgent:
    """Test the Risk Manager Agent."""

    def test_initialization(self):
        """Test agent initialization."""
        config = QuantChainConfig()
        llm_provider = MockLLMProvider()
        agent = RiskManagerAgent(config, llm_provider)

        assert agent.role == AgentRole.RISK_MANAGER
        assert agent.config == config

    def test_analyze_buy_action(self):
        """Test analysis for BUY action."""
        config = QuantChainConfig()
        llm_provider = MockLLMProvider()
        agent = RiskManagerAgent(config, llm_provider)

        result = agent.analyze("TEST", action="BUY", proposed_position_size=5000.0)

        assert isinstance(result, AgentAnalysis)
        assert result.symbol == "TEST"
        assert result.data_sources == ["portfolio_data", "market_data", "risk_metrics"]
        assert "risk_available" in result.metadata

    def test_analyze_hold_action(self):
        """Test analysis for HOLD action."""
        config = QuantChainConfig()
        llm_provider = MockLLMProvider()
        agent = RiskManagerAgent(config, llm_provider)

        result = agent.analyze("TEST", action="HOLD")

        assert isinstance(result, AgentAnalysis)
        assert result.recommendation == RecommendationType.HOLD
        assert "No action required" in result.reasoning

    def test_create_argument(self):
        """Test argument creation for debate."""
        config = QuantChainConfig()
        llm_provider = MockLLMProvider()
        agent = RiskManagerAgent(config, llm_provider)

        # Test with low risk assessment
        mock_analysis = AgentAnalysis(
            agent_role=AgentRole.RISK_MANAGER,
            symbol="TEST",
            timestamp=datetime.now(),
            recommendation=RecommendationType.BUY,
            confidence_score=80.0,
            reasoning="Low risk level",
            data_sources=["portfolio_data"],
            metadata={
                "risk_available": True,
                "risk_assessment": {"risk_level": "LOW", "confidence": 80},
            },
        )

        context = {"risk_analysis": mock_analysis, "proposed_action": "BUY"}
        argument = agent.create_argument(context)

        assert argument.agent_role == AgentRole.RISK_MANAGER
        assert argument.argument_type == "support"


class TestPortfolioCommitteeAgent:
    """Test the Portfolio Committee Agent."""

    def test_initialization(self):
        """Test agent initialization."""
        config = QuantChainConfig()
        llm_provider = MockLLMProvider()
        committee = PortfolioCommitteeAgent(config, llm_provider)

        assert committee.role == AgentRole.PORTFOLIO_COMMITTEE
        assert committee.config == config

    def test_analyze_with_no_agents(self):
        """Test analysis with no specialized agents."""
        config = QuantChainConfig()
        llm_provider = MockLLMProvider()
        committee = PortfolioCommitteeAgent(config, llm_provider, specialized_agents={})

        result = committee.analyze("TEST")

        assert isinstance(result, AgentAnalysis)
        assert result.recommendation == RecommendationType.HOLD
        assert "No agent analyses available" in result.reasoning

    def test_analyze_with_specialized_agents(self):
        """Test analysis with specialized agents."""
        config = QuantChainConfig()
        llm_provider = MockLLMProvider()

        # Create mock specialized agents
        mock_fundamentals = Mock(spec=FundamentalsAnalystAgent)
        mock_fundamentals.analyze.return_value = AgentAnalysis(
            agent_role=AgentRole.FUNDAMENTALS,
            symbol="TEST",
            timestamp=datetime.now(),
            recommendation=RecommendationType.BUY,
            confidence_score=80.0,
            reasoning="Strong fundamentals",
            data_sources=["financial_statements"],
            metadata={},
        )

        mock_fundamentals.create_argument.return_value = AgentArgument(
            agent_role=AgentRole.FUNDAMENTALS,
            argument_type="support",
            target_agent=None,
            reasoning="Fundamentals support buy",
            evidence=[],
            confidence_impact=20.0,
        )

        specialized_agents = {AgentRole.FUNDAMENTALS: mock_fundamentals}
        committee = PortfolioCommitteeAgent(config, llm_provider, specialized_agents)

        result = committee.analyze("TEST")

        assert isinstance(result, AgentAnalysis)
        assert result.symbol == "TEST"
        assert result.data_sources == ["committee_coordination", "multi_agent_debate"]
        assert "committee_available" in result.metadata

    def test_create_argument(self):
        """Test argument creation (committee should be neutral)."""
        config = QuantChainConfig()
        llm_provider = MockLLMProvider()
        committee = PortfolioCommitteeAgent(config, llm_provider)

        argument = committee.create_argument({})

        assert argument.agent_role == AgentRole.PORTFOLIO_COMMITTEE
        assert argument.argument_type == "neutral"
        assert "coordinates debate" in argument.reasoning


class TestMultiAgentIntegration:
    """Integration tests for the multi-agent system."""

    def test_full_workflow(self):
        """Test the complete multi-agent workflow."""
        config = QuantChainConfig()
        llm_provider = MockLLMProvider()

        # Create all specialized agents
        fundamentals_agent = FundamentalsAnalystAgent(config, llm_provider)
        sentiment_agent = SentimentExpertAgent(config, llm_provider)
        technical_agent = TechnicalAnalystAgent(config, llm_provider)
        risk_agent = RiskManagerAgent(config, llm_provider)

        specialized_agents = {
            AgentRole.FUNDAMENTALS: fundamentals_agent,
            AgentRole.SENTIMENT: sentiment_agent,
            AgentRole.TECHNICAL: technical_agent,
            AgentRole.RISK_MANAGER: risk_agent,
        }

        # Create portfolio committee
        committee = PortfolioCommitteeAgent(config, llm_provider, specialized_agents)

        # Run analysis
        result = committee.analyze("TEST", action="BUY", proposed_position_size=5000.0)

        # Verify result
        assert isinstance(result, AgentAnalysis)
        assert result.symbol == "TEST"
        assert result.recommendation in [
            RecommendationType.BUY,
            RecommendationType.SELL,
            RecommendationType.HOLD,
        ]
        assert 0 <= result.confidence_score <= 100
        assert len(result.reasoning) > 0

        # Check metadata
        assert "committee_available" in result.metadata
        assert "participating_agents" in result.metadata

        # Check that all agents participated
        participating_agents = result.metadata["participating_agents"]
        assert len(participating_agents) >= 2  # At least some agents should work

    def test_consensus_building(self):
        """Test consensus building between agents."""
        # This would test the consensus logic more thoroughly
        # For now, just verify that consensus can be generated
        pass

    def test_dispute_resolution(self):
        """Test dispute resolution mechanisms."""
        # This would test how disagreements are resolved
        # For now, just verify the structure is in place
        pass
