"""
Comprehensive tests for Portfolio Committee to improve coverage from 28% to 90%+.
Tests all debate logic, consensus building, and coordination features.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta

try:
    from quantchain.agents.portfolio_committee import (
        PortfolioCommitteeAgent,
        DebateRound,
        DebateSession,
        CommitteeConfig,
    )
    from quantchain.agents.base import (
        AgentAnalysis,
        AgentArgument,
        AgentRole,
        RecommendationType,
        ConsensusResult,
    )
    PORTFOLIO_COMMITTEE_AVAILABLE = True
except ImportError as e:
    PORTFOLIO_COMMITTEE_AVAILABLE = False
    print(f"Portfolio committee module not available: {e}")


@pytest.mark.skipif(not PORTFOLIO_COMMITTEE_AVAILABLE, reason="Portfolio committee not available")
@pytest.mark.unit
class TestDebateRound:
    """Test DebateRound dataclass for comprehensive coverage."""

    def test_debate_round_creation(self):
        """Test DebateRound creation with all fields."""
        timestamp = datetime.now()
        argument = AgentArgument(
            agent_role=AgentRole.TECHNICAL,
            argument_type="support",
            target_agent=None,
            reasoning="Strong technical indicators support this position",
            evidence=["RSI shows oversold conditions", "MACD bullish crossover"],
            confidence_impact=15.0,
        )

        round_obj = DebateRound(
            round_number=1,
            presenting_agent=AgentRole.TECHNICAL,
            argument=argument,
            responding_agents=[AgentRole.FUNDAMENTALS, AgentRole.RISK_MANAGER],
            timestamp=timestamp,
        )

        assert round_obj.round_number == 1
        assert round_obj.presenting_agent == AgentRole.TECHNICAL
        assert round_obj.argument == argument
        assert round_obj.responding_agents == [AgentRole.FUNDAMENTALS, AgentRole.RISK_MANAGER]
        assert round_obj.timestamp == timestamp

    def test_debate_round_different_agents(self):
        """Test DebateRound with different presenting agents."""
        agents = [
            AgentRole.FUNDAMENTALS,
            AgentRole.TECHNICAL,
            AgentRole.RISK_MANAGER,
            AgentRole.SENTIMENT,
        ]

        for agent_role in agents:
            timestamp = datetime.now()
            argument = AgentArgument(
                agent_role=agent_role,
                argument_type="support",
                target_agent=None,
                reasoning=f"Support from {agent_role.value} perspective",
                evidence=[],
                confidence_impact=10.0,
            )

            round_obj = DebateRound(
                round_number=1,
                presenting_agent=agent_role,
                argument=argument,
                responding_agents=[],
                timestamp=timestamp,
            )

            assert round_obj.presenting_agent == agent_role

    def test_debate_round_different_argument_types(self):
        """Test DebateRound with different argument types."""
        argument_types = ["support", "oppose", "neutral"]
        timestamp = datetime.now()

        for arg_type in argument_types:
            argument = AgentArgument(
                agent_role=AgentRole.TECHNICAL,
                argument_type=arg_type,
                target_agent=None,
                reasoning=f"Argument of type {arg_type}",
                evidence=[],
                confidence_impact=5.0,
            )

            round_obj = DebateRound(
                round_number=1,
                presenting_agent=AgentRole.TECHNICAL,
                argument=argument,
                responding_agents=[AgentRole.FUNDAMENTALS],
                timestamp=timestamp,
            )

            assert round_obj.argument.argument_type == arg_type

    def test_debate_round_no_responding_agents(self):
        """Test DebateRound with no responding agents."""
        timestamp = datetime.now()
        argument = AgentArgument(
            agent_role=AgentRole.RISK_MANAGER,
            argument_type="oppose",
            target_agent=None,
            reasoning="Risk assessment opposes this trade",
            evidence=["High volatility", "Concentrated position"],
            confidence_impact=-20.0,
        )

        round_obj = DebateRound(
            round_number=3,
            presenting_agent=AgentRole.RISK_MANAGER,
            argument=argument,
            responding_agents=[],
            timestamp=timestamp,
        )

        assert round_obj.responding_agents == []


@pytest.mark.skipif(not PORTFOLIO_COMMITTEE_AVAILABLE, reason="Portfolio committee not available")
@pytest.mark.unit
class TestCommitteeConfig:
    """Test CommitteeConfig dataclass for comprehensive coverage."""

    def test_committee_config_creation_default(self):
        """Test CommitteeConfig creation with default values."""
        config = CommitteeConfig()

        assert config.max_debate_rounds == 3
        assert config.consensus_threshold == 70.0
        assert AgentRole.FUNDAMENTALS in config.voting_weights
        assert AgentRole.TECHNICAL in config.voting_weights
        assert AgentRole.RISK_MANAGER in config.voting_weights
        assert AgentRole.SENTIMENT in config.voting_weights
        assert sum(config.voting_weights.values()) == pytest.approx(1.0)

    def test_committee_config_creation_custom(self):
        """Test CommitteeConfig creation with custom values."""
        custom_weights = {
            AgentRole.FUNDAMENTALS: 0.4,
            AgentRole.TECHNICAL: 0.3,
            AgentRole.RISK_MANAGER: 0.2,
            AgentRole.SENTIMENT: 0.1,
        }

        config = CommitteeConfig(
            max_debate_rounds=5,
            consensus_threshold=80.0,
            voting_weights=custom_weights,
        )

        assert config.max_debate_rounds == 5
        assert config.consensus_threshold == 80.0
        assert config.voting_weights == custom_weights

    def test_committee_config_extreme_values(self):
        """Test CommitteeConfig with extreme values."""
        config = CommitteeConfig(
            max_debate_rounds=10,  # Many rounds
            consensus_threshold=95.0,  # Very high threshold
        )

        assert config.max_debate_rounds == 10
        assert config.consensus_threshold == 95.0

    def test_committee_config_minimal_values(self):
        """Test CommitteeConfig with minimal values."""
        config = CommitteeConfig(
            max_debate_rounds=1,  # Single round
            consensus_threshold=50.0,  # Low threshold
        )

        assert config.max_debate_rounds == 1
        assert config.consensus_threshold == 50.0


@pytest.mark.skipif(not PORTFOLIO_COMMITTEE_AVAILABLE, reason="Portfolio committee not available")
@pytest.mark.unit
class TestDebateSession:
    """Test DebateSession dataclass for comprehensive coverage."""

    def test_debate_session_creation_complete(self):
        """Test DebateSession creation with all fields."""
        # Create initial analyses
        initial_analyses = {
            AgentRole.FUNDAMENTALS: AgentAnalysis(
                agent_role=AgentRole.FUNDAMENTALS,
                symbol="AAPL",
                timestamp=datetime.now(),
                recommendation=RecommendationType.BUY,
                confidence_score=75.0,
                reasoning="Strong fundamentals",
                data_sources=["financial_data"],
                metadata={}
            ),
            AgentRole.TECHNICAL: AgentAnalysis(
                agent_role=AgentRole.TECHNICAL,
                symbol="AAPL",
                timestamp=datetime.now(),
                recommendation=RecommendationType.HOLD,
                confidence_score=60.0,
                reasoning="Mixed technical signals",
                data_sources=["market_data"],
                metadata={}
            ),
        }

        # Create debate rounds
        timestamp = datetime.now()
        argument = AgentArgument(
            agent_role=AgentRole.FUNDAMENTALS,
            argument_type="support",
            target_agent=None,
            reasoning="Strong fundamentals support BUY",
            evidence=["Low P/E ratio", "High ROE"],
            confidence_impact=15.0,
        )

        debate_rounds = [
            DebateRound(
                round_number=1,
                presenting_agent=AgentRole.FUNDAMENTALS,
                argument=argument,
                responding_agents=[AgentRole.TECHNICAL, AgentRole.RISK_MANAGER],
                timestamp=timestamp,
            )
        ]

        # Create consensus result
        consensus = ConsensusResult(
            final_recommendation=RecommendationType.BUY,
            consensus_score=78.0,
            confidence_score=75.0,
            participating_agents=[AgentRole.FUNDAMENTALS, AgentRole.TECHNICAL],
            arguments=[],
            dissenting_opinions=[AgentRole.TECHNICAL],
            final_reasoning="Strong fundamentals outweigh technical concerns",
            risk_assessment={"level": "moderate"}
        )

        session = DebateSession(
            symbol="AAPL",
            initial_analyses=initial_analyses,
            debate_rounds=debate_rounds,
            final_consensus=consensus,
            session_duration=45.5,
            participant_agents=[AgentRole.FUNDAMENTALS, AgentRole.TECHNICAL],
            dissenting_opinions=[AgentRole.TECHNICAL],
        )

        assert session.symbol == "AAPL"
        assert len(session.initial_analyses) == 2
        assert len(session.debate_rounds) == 1
        assert session.final_consensus == consensus
        assert session.session_duration == 45.5
        assert session.participant_agents == [AgentRole.FUNDAMENTALS, AgentRole.TECHNICAL]
        assert session.dissenting_opinions == [AgentRole.TECHNICAL]

    def test_debate_session_creation_minimal(self):
        """Test DebateSession creation with minimal data."""
        consensus = ConsensusResult(
            final_recommendation=RecommendationType.HOLD,
            consensus_score=50.0,
            confidence_score=50.0,
            participating_agents=[],
            arguments=[],
            dissenting_opinions=[],
            final_reasoning="Unable to reach strong consensus",
            risk_assessment={}
        )

        session = DebateSession(
            symbol="BTC",
            initial_analyses={},
            debate_rounds=[],
            final_consensus=consensus,
            session_duration=0.0,
            participant_agents=[],
            dissenting_opinions=[],
        )

        assert session.symbol == "BTC"
        assert len(session.initial_analyses) == 0
        assert len(session.debate_rounds) == 0
        assert session.session_duration == 0.0
        assert len(session.participant_agents) == 0

    def test_debate_session_all_participants(self):
        """Test DebateSession with all possible participants."""
        consensus = ConsensusResult(
            final_recommendation=RecommendationType.SELL,
            consensus_score=85.0,
            confidence_score=90.0,
            participating_agents=list(AgentRole),
            arguments=[],
            dissenting_opinions=[],
            final_reasoning="All agents agree on SELL",
            risk_assessment={"level": "high"}
        )

        session = DebateSession(
            symbol="MEME",
            initial_analyses={},
            debate_rounds=[],
            final_consensus=consensus,
            session_duration=120.0,
            participant_agents=list(AgentRole),
            dissenting_opinions=[],
        )

        assert len(session.participant_agents) == len(AgentRole)
        assert len(session.final_consensus.participant_agreement) == len(AgentRole)

    def test_debate_session_multiple_dissenting_opinions(self):
        """Test DebateSession with multiple dissenting opinions."""
        consensus = ConsensusResult(
            final_recommendation=RecommendationType.HOLD,
            consensus_score=45.0,  # Low consensus
            confidence_score=30.0,
            participating_agents=[AgentRole.FUNDAMENTALS, AgentRole.TECHNICAL, AgentRole.RISK_MANAGER, AgentRole.SENTIMENT],
            arguments=[],
            dissenting_opinions=[AgentRole.TECHNICAL, AgentRole.RISK_MANAGER],
            final_reasoning="Mixed signals create uncertainty",
            risk_assessment={"level": "high"}
        )

        session = DebateSession(
            symbol="ETH",
            initial_analyses={},
            debate_rounds=[],
            final_consensus=consensus,
            session_duration=60.0,
            participant_agents=[AgentRole.FUNDAMENTALS, AgentRole.TECHNICAL, AgentRole.RISK_MANAGER, AgentRole.SENTIMENT],
            dissenting_opinions=[AgentRole.TECHNICAL, AgentRole.RISK_MANAGER],
        )

        assert len(session.dissenting_opinions) == 2
        assert session.final_consensus.consensus_score == 45.0


@pytest.mark.skipif(not PORTFOLIO_COMMITTEE_AVAILABLE, reason="Portfolio committee not available")
@pytest.mark.unit
class TestPortfolioCommitteeAgent:
    """Test PortfolioCommitteeAgent for comprehensive coverage."""

    def test_agent_initialization_default_config(self):
        """Test agent initialization with default configuration."""
        config = {}
        mock_llm = Mock()

        agent = PortfolioCommitteeAgent(config, mock_llm)

        assert agent.role == AgentRole.PORTFOLIO_COMMITTEE
        assert isinstance(agent.config, CommitteeConfig)
        assert agent.config.max_debate_rounds == 3
        assert agent.config.consensus_threshold == 70.0

    def test_agent_initialization_custom_config(self):
        """Test agent initialization with custom configuration."""
        config = {
            "portfolio_committee": {
                "max_debate_rounds": 5,
                "consensus_threshold": 80.0,
            }
        }
        mock_llm = Mock()

        agent = PortfolioCommitteeAgent(config, mock_llm)

        assert agent.config.max_debate_rounds == 5
        assert agent.config.consensus_threshold == 80.0

    def test_analyze_with_no_agents(self):
        """Test analyze when no other agents are available."""
        config = {}
        mock_llm = Mock()
        agent = PortfolioCommitteeAgent(config, mock_llm)

        with patch.object(agent, '_gather_agent_analyses', return_value={}):
            result = agent.analyze("AAPL")

            assert result.recommendation == RecommendationType.HOLD
            assert "No agent analyses available" in result.reasoning

    def test_analyze_with_single_agent(self):
        """Test analyze when only one agent provides analysis."""
        config = {}
        mock_llm = Mock()
        agent = PortfolioCommitteeAgent(config, mock_llm)

        single_analysis = AgentAnalysis(
            agent_role=AgentRole.FUNDAMENTALS,
            symbol="AAPL",
            timestamp=datetime.now(),
            recommendation=RecommendationType.BUY,
            confidence_score=80.0,
            reasoning="Strong fundamentals",
            data_sources=["financial_data"],
            metadata={}
        )

        with patch.object(agent, '_gather_agent_analyses', return_value={AgentRole.FUNDAMENTALS: single_analysis}):
            # analyze calls _conduct_debate even for single agent
            with patch.object(agent, '_conduct_debate') as mock_debate:
                mock_consensus_result = ConsensusResult(
                    final_recommendation=RecommendationType.BUY,
                    consensus_score=80.0,
                    confidence_score=80.0,
                    participating_agents=[AgentRole.FUNDAMENTALS],
                    arguments=[],
                    dissenting_opinions=[],
                    final_reasoning="Based on single agent analysis",
                    risk_assessment={"level": "low"}
                )
                mock_debate_session = DebateSession(
                    symbol="AAPL",
                    initial_analyses={AgentRole.FUNDAMENTALS: single_analysis},
                    debate_rounds=[],
                    final_consensus=mock_consensus_result,
                    session_duration=10.0,
                    participant_agents=[AgentRole.FUNDAMENTALS]
                )
                mock_debate.return_value = mock_debate_session

                result = agent.analyze("AAPL")

                assert result.recommendation == RecommendationType.BUY
                assert result.confidence_score == 80.0

    def test_analyze_with_multiple_agents(self):
        """Test analyze with multiple agents."""
        config = {}
        mock_llm = Mock()
        agent = PortfolioCommitteeAgent(config, mock_llm)

        analyses = {
            AgentRole.FUNDAMENTALS: AgentAnalysis(
                agent_role=AgentRole.FUNDAMENTALS,
                symbol="AAPL",
                timestamp=datetime.now(),
                recommendation=RecommendationType.BUY,
                confidence_score=75.0,
                reasoning="Strong fundamentals",
                data_sources=["financial_data"],
                metadata={}
            ),
            AgentRole.TECHNICAL: AgentAnalysis(
                agent_role=AgentRole.TECHNICAL,
                symbol="AAPL",
                timestamp=datetime.now(),
                recommendation=RecommendationType.BUY,
                confidence_score=70.0,
                reasoning="Bullish technical indicators",
                data_sources=["market_data"],
                metadata={}
            ),
        }

        with patch.object(agent, '_gather_agent_analyses', return_value=analyses):
            with patch.object(agent, '_conduct_debate') as mock_debate:
                mock_consensus_result = ConsensusResult(
                    final_recommendation=RecommendationType.BUY,
                    consensus_score=85.0,
                    confidence_score=85.0,
                    participating_agents=[AgentRole.FUNDAMENTALS, AgentRole.TECHNICAL],
                    arguments=[],
                    dissenting_opinions=[],
                    final_reasoning="All agents agree on BUY",
                    risk_assessment={"level": "low"}
                )
                mock_debate_session = DebateSession(
                    symbol="AAPL",
                    initial_analyses=analyses,
                    debate_rounds=[],
                    final_consensus=mock_consensus_result,
                    session_duration=10.0,
                    participant_agents=[AgentRole.FUNDAMENTALS, AgentRole.TECHNICAL]
                )
                mock_debate.return_value = mock_debate_session

                result = agent.analyze("AAPL")

                assert result.recommendation == RecommendationType.BUY
                assert result.confidence_score == 85.0

    def test_analyze_exception_handling(self):
        """Test analyze with exception handling."""
        config = {}
        mock_llm = Mock()
        agent = PortfolioCommitteeAgent(config, mock_llm)

        with patch.object(agent, '_gather_agent_analyses', side_effect=Exception("Agent communication error")):
            result = agent.analyze("AAPL")

            assert result.recommendation == RecommendationType.HOLD
            assert result.confidence_score == 0.0
            assert "Committee analysis failed" in result.reasoning

    def test_create_argument(self):
        """Test create_argument method."""
        config = {}
        mock_llm = Mock()
        agent = PortfolioCommitteeAgent(config, mock_llm)

        context = {
            "symbol": "AAPL",
            "committee_analysis": Mock(),
            "other_analyses": {}
        }

        # Portfolio committee implementation returns a neutral argument directly
        # It does not call any internal helper for this that we need to mock usually,
        # but if we want to verify output:
        result = agent.create_argument(context)
        
        assert isinstance(result, AgentArgument)
        assert result.argument_type == "neutral"
        assert "does not participate" in result.reasoning

    def test_gather_agent_analyses(self):
        """Test _gather_agent_analyses method."""
        config = {}
        mock_llm = Mock()
        agent = PortfolioCommitteeAgent(config, mock_llm)
        
        # Mock specialized agents
        agent.specialized_agents = {
            AgentRole.FUNDAMENTALS: Mock(),
            AgentRole.TECHNICAL: Mock(),
        }
        
        # Mock analyze return values
        agent.specialized_agents[AgentRole.FUNDAMENTALS].analyze.return_value = Mock(recommendation=RecommendationType.BUY, confidence_score=80.0)
        agent.specialized_agents[AgentRole.TECHNICAL].analyze.return_value = Mock(recommendation=RecommendationType.SELL, confidence_score=60.0)

        result = agent._gather_agent_analyses("AAPL")

        assert len(result) == 2
        assert AgentRole.FUNDAMENTALS in result
        assert AgentRole.TECHNICAL in result

    def test_conduct_debate(self):
        """Test _conduct_debate method."""
        config = {"portfolio_committee": {"max_debate_rounds": 2}}
        mock_llm = Mock()
        agent = PortfolioCommitteeAgent(config, mock_llm)
        
        # Mock specialized agents
        mock_agent = Mock()
        mock_agent.create_argument.return_value = AgentArgument(
            agent_role=AgentRole.FUNDAMENTALS,
            argument_type="support",
            target_agent=None,
            reasoning="test",
            evidence=[],
            confidence_impact=10
        )
        agent.specialized_agents = {AgentRole.FUNDAMENTALS: mock_agent}

        analyses = {
            AgentRole.FUNDAMENTALS: Mock(spec=AgentAnalysis, recommendation=RecommendationType.BUY, confidence_score=80.0, metadata={}),
        }

        result = agent._conduct_debate("AAPL", analyses)
        
        assert isinstance(result, DebateSession)
        assert result.symbol == "AAPL"

    def test_all_methods_exist(self):
        """Test that all expected methods exist."""
        config = {}
        mock_llm = Mock()
        agent = PortfolioCommitteeAgent(config, mock_llm)

        # Check that all expected methods exist
        expected_methods = [
            'analyze',
            'create_argument',
            '_gather_agent_analyses',
            '_conduct_debate',
            '_generate_consensus',
            '_generate_committee_recommendation',
        ]

        for method_name in expected_methods:
            assert hasattr(agent, method_name), f"Missing method: {method_name}"
            assert callable(getattr(agent, method_name)), f"Method not callable: {method_name}"


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v", "--tb=short"])

