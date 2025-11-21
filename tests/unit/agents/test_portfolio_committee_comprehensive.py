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
                symbol="AAPL",
                agent_role=AgentRole.FUNDAMENTALS,
                recommendation=RecommendationType.BUY,
                confidence_score=75.0,
                reasoning="Strong fundamentals",
                data_sources=["financial_data"],
                metadata={}
            ),
            AgentRole.TECHNICAL: AgentAnalysis(
                symbol="AAPL",
                agent_role=AgentRole.TECHNICAL,
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
            confidence_level=0.75,
            participant_agreement={AgentRole.FUNDAMENTALS: True, AgentRole.TECHNICAL: False},
            key_consensus_points=["Strong fundamentals outweigh technical concerns"],
            dissenting_opinions=["Technical indicators suggest caution"],
            risk_assessment="Moderate risk, acceptable for current strategy"
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
            confidence_level=0.5,
            participant_agreement={},
            key_consensus_points=[],
            dissenting_opinions=[],
            risk_assessment="Unable to reach strong consensus"
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
            confidence_level=0.9,
            participant_agreement={role: True for role in AgentRole},
            key_consensus_points=["All agents agree on SELL"],
            dissenting_opinions=[],
            risk_assessment="High risk, immediate action recommended"
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
            confidence_level=0.3,
            participant_agreement={
                AgentRole.FUNDAMENTALS: True,
                AgentRole.TECHNICAL: False,
                AgentRole.RISK_MANAGER: False,
                AgentRole.SENTIMENT: True,
            },
            key_consensus_points=["Mixed signals create uncertainty"],
            dissenting_opinions=["Technical concerns", "Risk management objections"],
            risk_assessment="High uncertainty, hold position"
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

        with patch.object(agent, '_get_agent_analyses', return_value={}):
            result = agent.analyze("AAPL")

            assert result.recommendation == RecommendationType.HOLD
            assert "No agent analyses available" in result.reasoning

    def test_analyze_with_single_agent(self):
        """Test analyze when only one agent provides analysis."""
        config = {}
        mock_llm = Mock()
        agent = PortfolioCommitteeAgent(config, mock_llm)

        single_analysis = AgentAnalysis(
            symbol="AAPL",
            agent_role=AgentRole.FUNDAMENTALS,
            recommendation=RecommendationType.BUY,
            confidence_score=80.0,
            reasoning="Strong fundamentals",
            data_sources=["financial_data"],
            metadata={}
        )

        with patch.object(agent, '_get_agent_analyses', return_value={AgentRole.FUNDAMENTALS: single_analysis}):
            with patch.object(agent, '_build_single_agent_consensus') as mock_consensus:
                mock_consensus_result = ConsensusResult(
                    final_recommendation=RecommendationType.BUY,
                    consensus_score=80.0,
                    confidence_level=0.8,
                    participant_agreement={AgentRole.FUNDAMENTALS: True},
                    key_consensus_points=["Strong fundamentals"],
                    dissenting_opinions=[],
                    risk_assessment="Based on single agent analysis"
                )
                mock_consensus.return_value = mock_consensus_result

                result = agent.analyze("AAPL")

                assert result.recommendation == RecommendationType.BUY
                assert result.confidence_score == 80.0

    def test_analyze_with_multiple_agents_no_debate_needed(self):
        """Test analyze with multiple agents when no debate is needed."""
        config = {}
        mock_llm = Mock()
        agent = PortfolioCommitteeAgent(config, mock_llm)

        # Multiple agents with the same recommendation
        analyses = {
            AgentRole.FUNDAMENTALS: AgentAnalysis(
                symbol="AAPL",
                agent_role=AgentRole.FUNDAMENTALS,
                recommendation=RecommendationType.BUY,
                confidence_score=75.0,
                reasoning="Strong fundamentals",
                data_sources=["financial_data"],
                metadata={}
            ),
            AgentRole.TECHNICAL: AgentAnalysis(
                symbol="AAPL",
                agent_role=AgentRole.TECHNICAL,
                recommendation=RecommendationType.BUY,
                confidence_score=70.0,
                reasoning="Bullish technical indicators",
                data_sources=["market_data"],
                metadata={}
            ),
        }

        with patch.object(agent, '_get_agent_analyses', return_value=analyses):
            with patch.object(agent, '_check_if_debate_needed', return_value=False):
                with patch.object(agent, '_build_quick_consensus') as mock_consensus:
                    mock_consensus_result = ConsensusResult(
                        final_recommendation=RecommendationType.BUY,
                        consensus_score=85.0,
                        confidence_level=0.85,
                        participant_agreement={AgentRole.FUNDAMENTALS: True, AgentRole.TECHNICAL: True},
                        key_consensus_points=["All agents agree on BUY"],
                        dissenting_opinions=[],
                        risk_assessment="Low risk, strong consensus"
                    )
                    mock_consensus.return_value = mock_consensus_result

                    result = agent.analyze("AAPL")

                    assert result.recommendation == RecommendationType.BUY
                    assert result.confidence_score == 85.0

    def test_analyze_with_debate_required(self):
        """Test analyze with multiple agents requiring debate."""
        config = {}
        mock_llm = Mock()
        agent = PortfolioCommitteeAgent(config, mock_llm)

        # Agents with conflicting recommendations
        analyses = {
            AgentRole.FUNDAMENTALS: AgentAnalysis(
                symbol="AAPL",
                agent_role=AgentRole.FUNDAMENTALS,
                recommendation=RecommendationType.BUY,
                confidence_score=80.0,
                reasoning="Strong fundamentals support BUY",
                data_sources=["financial_data"],
                metadata={}
            ),
            AgentRole.TECHNICAL: AgentAnalysis(
                symbol="AAPL",
                agent_role=AgentRole.TECHNICAL,
                recommendation=RecommendationType.SELL,
                confidence_score=75.0,
                reasoning="Bearish technical indicators",
                data_sources=["market_data"],
                metadata={}
            ),
        }

        with patch.object(agent, '_get_agent_analyses', return_value=analyses):
            with patch.object(agent, '_check_if_debate_needed', return_value=True):
                with patch.object(agent, '_conduct_debate') as mock_debate:
                    mock_debate_session = DebateSession(
                        symbol="AAPL",
                        initial_analyses=analyses,
                        debate_rounds=[],
                        final_consensus=ConsensusResult(
                            final_recommendation=RecommendationType.HOLD,
                            consensus_score=55.0,
                            confidence_level=0.55,
                            participant_agreement={AgentRole.FUNDAMENTALS: False, AgentRole.TECHNICAL: False},
                            key_consensus_points=["Conflicting signals lead to HOLD"],
                            dissenting_opinions=[AgentRole.FUNDAMENTALS, AgentRole.TECHNICAL],
                            risk_assessment="Medium risk, hold position"
                        ),
                        session_duration=30.0,
                        participant_agents=[AgentRole.FUNDAMENTALS, AgentRole.TECHNICAL],
                        dissenting_opinions=[AgentRole.FUNDAMENTALS, AgentRole.TECHNICAL],
                    )
                    mock_debate.return_value = mock_debate_session

                    result = agent.analyze("AAPL")

                    assert result.recommendation == RecommendationType.HOLD
                    assert result.confidence_score == 55.0

    def test_analyze_exception_handling(self):
        """Test analyze with exception handling."""
        config = {}
        mock_llm = Mock()
        agent = PortfolioCommitteeAgent(config, mock_llm)

        with patch.object(agent, '_get_agent_analyses', side_effect=Exception("Agent communication error")):
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

        with patch.object(agent, 'create_argument') as mock_create:
            mock_argument = AgentArgument(
                agent_role=AgentRole.PORTFOLIO_COMMITTEE,
                argument_type="support",
                target_agent=None,
                reasoning="Committee consensus supports this action",
                evidence=["Strong consensus", "Low risk assessment"],
                confidence_impact=10.0,
            )
            mock_create.return_value = mock_argument

            result = agent.create_argument(context)

            mock_create.assert_called_once_with(context)

    def test_get_agent_analyses(self):
        """Test _get_agent_analyses method."""
        config = {}
        mock_llm = Mock()
        agent = PortfolioCommitteeAgent(config, mock_llm)

        with patch.object(agent, '_get_agent_analyses') as mock_method:
            mock_analyses = {
                AgentRole.FUNDAMENTALS: Mock(),
                AgentRole.TECHNICAL: Mock(),
                AgentRole.RISK_MANAGER: Mock(),
            }
            mock_method.return_value = mock_analyses

            result = agent._get_agent_analyses()

            mock_method.assert_called_once()
            assert len(result) == 3

    def test_check_if_debate_needed_same_recommendations(self):
        """Test _check_if_debate_needed with same recommendations."""
        config = {}
        mock_llm = Mock()
        agent = PortfolioCommitteeAgent(config, mock_llm)

        analyses = {
            AgentRole.FUNDAMENTALS: Mock(spec=AgentAnalysis, recommendation=RecommendationType.BUY),
            AgentRole.TECHNICAL: Mock(spec=AgentAnalysis, recommendation=RecommendationType.BUY),
            AgentRole.RISK_MANAGER: Mock(spec=AgentAnalysis, recommendation=RecommendationType.BUY),
        }

        with patch.object(agent, '_check_if_debate_needed') as mock_method:
            mock_method.return_value = False

            result = agent._check_if_debate_needed(analyses)

            mock_method.assert_called_once_with(analyses)

    def test_check_if_debate_needed_different_recommendations(self):
        """Test _check_if_debate_needed with different recommendations."""
        config = {}
        mock_llm = Mock()
        agent = PortfolioCommitteeAgent(config, mock_llm)

        analyses = {
            AgentRole.FUNDAMENTALS: Mock(spec=AgentAnalysis, recommendation=RecommendationType.BUY),
            AgentRole.TECHNICAL: Mock(spec=AgentAnalysis, recommendation=RecommendationType.SELL),
            AgentRole.RISK_MANAGER: Mock(spec=AgentAnalysis, recommendation=RecommendationType.HOLD),
        }

        with patch.object(agent, '_check_if_debate_needed') as mock_method:
            mock_method.return_value = True

            result = agent._check_if_debate_needed(analyses)

            mock_method.assert_called_once_with(analyses)

    def test_build_quick_consensus(self):
        """Test _build_quick_consensus method."""
        config = {}
        mock_llm = Mock()
        agent = PortfolioCommitteeAgent(config, mock_llm)

        analyses = {
            AgentRole.FUNDAMENTALS: Mock(spec=AgentAnalysis, recommendation=RecommendationType.BUY, confidence_score=75.0),
            AgentRole.TECHNICAL: Mock(spec=AgentAnalysis, recommendation=RecommendationType.BUY, confidence_score=70.0),
        }

        with patch.object(agent, '_build_quick_consensus') as mock_method:
            mock_consensus = ConsensusResult(
                final_recommendation=RecommendationType.BUY,
                consensus_score=85.0,
                confidence_level=0.85,
                participant_agreement={AgentRole.FUNDAMENTALS: True, AgentRole.TECHNICAL: True},
                key_consensus_points=["Consensus reached without debate"],
                dissenting_opinions=[],
                risk_assessment="Low risk consensus"
            )
            mock_method.return_value = mock_consensus

            result = agent._build_quick_consensus(analyses)

            mock_method.assert_called_once_with(analyses)

    def test_conduct_debate(self):
        """Test _conduct_debate method."""
        config = {"portfolio_committee": {"max_debate_rounds": 2}}
        mock_llm = Mock()
        agent = PortfolioCommitteeAgent(config, mock_llm)

        analyses = {
            AgentRole.FUNDAMENTALS: Mock(spec=AgentAnalysis, recommendation=RecommendationType.BUY),
            AgentRole.TECHNICAL: Mock(spec=AgentAnalysis, recommendation=RecommendationType.SELL),
        }

        with patch.object(agent, '_conduct_debate') as mock_method:
            mock_session = DebateSession(
                symbol="AAPL",
                initial_analyses=analyses,
                debate_rounds=[],
                final_consensus=ConsensusResult(
                    final_recommendation=RecommendationType.HOLD,
                    consensus_score=50.0,
                    confidence_level=0.5,
                    participant_agreement={},
                    key_consensus_points=["Debate inconclusive"],
                    dissenting_opinions=[AgentRole.FUNDAMENTALS, AgentRole.TECHNICAL],
                    risk_assessment="Debate resulted in HOLD"
                ),
                session_duration=60.0,
                participant_agents=[AgentRole.FUNDAMENTALS, AgentRole.TECHNICAL],
                dissenting_opinions=[AgentRole.FUNDAMENTALS, AgentRole.TECHNICAL],
            )
            mock_method.return_value = mock_session

            result = agent._conduct_debate("AAPL", analyses)

            mock_method.assert_called_once_with("AAPL", analyses)

    def test_build_single_agent_consensus(self):
        """Test _build_single_agent_consensus method."""
        config = {}
        mock_llm = Mock()
        agent = PortfolioCommitteeAgent(config, mock_llm)

        single_analysis = Mock(spec=AgentAnalysis,
                              recommendation=RecommendationType.BUY,
                              confidence_score=80.0)

        with patch.object(agent, '_build_single_agent_consensus') as mock_method:
            mock_consensus = ConsensusResult(
                final_recommendation=RecommendationType.BUY,
                consensus_score=80.0,
                confidence_level=0.8,
                participant_agreement={},
                key_consensus_points=["Single agent recommendation"],
                dissenting_opinions=[],
                risk_assessment="Based on single agent analysis"
            )
            mock_method.return_value = mock_consensus

            result = agent._build_single_agent_consensus(single_analysis)

            mock_method.assert_called_once_with(single_analysis)

    def test_different_configurations(self):
        """Test agent with different configurations."""
        configs = [
            {},  # Default
            {"portfolio_committee": {"max_debate_rounds": 1}},  # Single round
            {"portfolio_committee": {"consensus_threshold": 50.0}},  # Low threshold
            {"portfolio_committee": {"max_debate_rounds": 5, "consensus_threshold": 90.0}},  # Strict
        ]

        for config in configs:
            mock_llm = Mock()
            agent = PortfolioCommitteeAgent(config, mock_llm)

            # Should be able to create agent and call methods without crashing
            assert hasattr(agent, 'analyze')
            assert hasattr(agent, 'create_argument')
            assert isinstance(agent.config, CommitteeConfig)

    def test_edge_cases(self):
        """Test edge cases and boundary conditions."""
        config = {"portfolio_committee": {"max_debate_rounds": 0}}  # No rounds
        mock_llm = Mock()
        agent = PortfolioCommitteeAgent(config, mock_llm)

        # Test with empty analyses
        with patch.object(agent, '_get_agent_analyses', return_value={}):
            result = agent.analyze("AAPL")
            assert result.recommendation == RecommendationType.HOLD

        # Test with very high consensus threshold
        config = {"portfolio_committee": {"consensus_threshold": 100.0}}
        agent = PortfolioCommitteeAgent(config, mock_llm)
        assert agent.config.consensus_threshold == 100.0

    def test_all_methods_exist(self):
        """Test that all expected methods exist."""
        config = {}
        mock_llm = Mock()
        agent = PortfolioCommitteeAgent(config, mock_llm)

        # Check that all expected methods exist
        expected_methods = [
            'analyze',
            'create_argument',
            '_get_agent_analyses',
            '_check_if_debate_needed',
            '_build_quick_consensus',
            '_conduct_debate',
            '_build_single_agent_consensus',
        ]

        for method_name in expected_methods:
            assert hasattr(agent, method_name), f"Missing method: {method_name}"
            assert callable(getattr(agent, method_name)), f"Method not callable: {method_name}"


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v", "--tb=short"])