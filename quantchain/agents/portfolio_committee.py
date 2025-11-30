"""Portfolio Committee Coordinator - Coordinates debate and final decision making."""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from .base import (
    AgentAnalysis,
    AgentArgument,
    AgentRole,
    BaseSpecializedAgent,
    ConsensusResult,
    RecommendationType,
)


@dataclass
class DebateRound:
    """Represents a round in the agent debate."""

    round_number: int
    presenting_agent: AgentRole
    argument: AgentArgument
    responding_agents: List[AgentRole]
    timestamp: datetime


@dataclass
class DebateSession:
    """Complete debate session between agents."""

    symbol: str
    initial_analyses: Dict[AgentRole, AgentAnalysis]
    debate_rounds: List[DebateRound]
    final_consensus: ConsensusResult
    session_duration: float  # Duration in seconds
    participant_agents: List[AgentRole]
    dissenting_opinions: List[AgentRole] = field(default_factory=list)


@dataclass
class CommitteeConfig:
    """Configuration for portfolio committee."""

    max_debate_rounds: int = 3
    consensus_threshold: float = 70.0  # Minimum consensus score to proceed
    voting_weights: Dict[AgentRole, float] = field(
        default_factory=lambda: {
            AgentRole.FUNDAMENTALS: 0.25,
            AgentRole.SENTIMENT: 0.20,
            AgentRole.TECHNICAL: 0.25,
            AgentRole.RISK_MANAGER: 0.30,
        }
    )
    enable_dispute_resolution: bool = True
    tie_breaker_role: AgentRole = AgentRole.RISK_MANAGER


class PortfolioCommitteeAgent(BaseSpecializedAgent):
    """Coordinates multi-agent debate and makes final portfolio decisions."""

    def __init__(
        self,
        config: Any,
        llm_provider: Any,
        specialized_agents: Optional[Dict[AgentRole, BaseSpecializedAgent]] = None,
    ):
        """Initialize the portfolio committee agent.

        Args:
            config: QuantChain configuration
            llm_provider: LLM provider for coordination
            specialized_agents: Dictionary of specialized agents
        """
        super().__init__(config, llm_provider, AgentRole.PORTFOLIO_COMMITTEE)
        self.specialized_agents = specialized_agents or {}
        self.logger = logging.getLogger(__name__)

        # Configuration
        self.committee_config = CommitteeConfig(
            max_debate_rounds=self.agent_config.get("max_debate_rounds", 3),
            consensus_threshold=self.agent_config.get("consensus_threshold", 70.0),
            voting_weights=self.agent_config.get(
                "voting_weights",
                {
                    "fundamentals_analyst": 0.25,
                    "sentiment_expert": 0.20,
                    "technical_analyst": 0.25,
                    "risk_manager": 0.30,
                },
            ),
            enable_dispute_resolution=self.agent_config.get(
                "enable_dispute_resolution", True
            ),
        )

    def analyze(self, symbol: str, **kwargs: Any) -> AgentAnalysis:
        """Coordinate multi-agent analysis and debate for a symbol.

        Args:
            symbol: Trading symbol to analyze
            **kwargs: Additional analysis parameters

        Returns:
            AgentAnalysis with committee recommendation
        """
        try:
            self.logger.info(f"Starting portfolio committee analysis for {symbol}")

            # Step 1: Gather individual agent analyses
            initial_analyses = self._gather_agent_analyses(symbol, **kwargs)

            if not initial_analyses:
                return self._create_base_analysis(
                    symbol=symbol,
                    recommendation=RecommendationType.HOLD,
                    confidence_score=0.0,
                    reasoning="No agent analyses available for committee decision",
                    data_sources=["committee_coordination"],
                    metadata={"committee_available": False},
                )

            # Step 2: Conduct debate if needed
            debate_result = self._conduct_debate(symbol, initial_analyses, **kwargs)

            # Step 3: Generate final committee recommendation
            final_recommendation = self._generate_committee_recommendation(
                debate_result
            )

            return self._create_base_analysis(
                symbol=symbol,
                recommendation=final_recommendation.final_recommendation,
                confidence_score=final_recommendation.consensus_score,
                reasoning=final_recommendation.final_reasoning,
                data_sources=["committee_coordination", "multi_agent_debate"],
                metadata={
                    "committee_available": True,
                    "initial_analyses": {
                        role.value: analysis.to_dict()
                        for role, analysis in initial_analyses.items()
                    },
                    "debate_result": debate_result.__dict__,
                    "final_consensus": final_recommendation.to_dict(),
                    "participating_agents": [
                        role.value for role in initial_analyses.keys()
                    ],
                },
            )

        except Exception as e:
            self.logger.error(
                f"Error in portfolio committee analysis for {symbol}: {str(e)}"
            )
            return self._create_base_analysis(
                symbol=symbol,
                recommendation=RecommendationType.HOLD,
                confidence_score=0.0,
                reasoning=f"Committee analysis failed: {str(e)}",
                data_sources=["error"],
            )

    def create_argument(self, context: Dict[str, Any]) -> AgentArgument:
        """Portfolio committee doesn't create arguments - it coordinates them.

        Args:
            context: Context including other agents' analyses

        Returns:
            Neutral argument as committee is coordinator, not participant
        """
        return AgentArgument(
            agent_role=self.role,
            argument_type="neutral",
            target_agent=None,
            reasoning="Portfolio committee coordinates debate, does not participate in arguments",
            evidence=[],
            confidence_impact=0.0,
        )

    def _gather_agent_analyses(
        self, symbol: str, **kwargs: Any
    ) -> Dict[AgentRole, AgentAnalysis]:
        """Gather analyses from all specialized agents.

        Args:
            symbol: Trading symbol
            **kwargs: Additional analysis parameters

        Returns:
            Dictionary of agent analyses by role
        """
        analyses = {}

        for role, agent in self.specialized_agents.items():
            try:
                self.logger.info(f"Getting analysis from {role.value} for {symbol}")
                analysis = agent.analyze(symbol, **kwargs)
                analyses[role] = analysis
                self.logger.info(
                    f"Received {role.value} analysis: {analysis.recommendation.value} ({analysis.confidence_score:.1f}%)"
                )
            except Exception as e:
                self.logger.error(
                    f"Error getting analysis from {role.value} for {symbol}: {str(e)}"
                )
                # Continue with other agents
                continue

        return analyses

    def _conduct_debate(
        self,
        symbol: str,
        initial_analyses: Dict[AgentRole, AgentAnalysis],
        **kwargs: Any,
    ) -> DebateSession:
        """Conduct structured debate between agents.

        Args:
            symbol: Trading symbol
            initial_analyses: Initial agent analyses
            **kwargs: Additional parameters

        Returns:
            DebateSession result
        """
        self.logger.info(f"Starting agent debate for {symbol}")

        debate_rounds = []
        arguments = []

        # Create context for agents to create arguments
        context = {
            "symbol": symbol,
            "other_analyses": {
                role: analysis
                for role, analysis in initial_analyses.items()
                if role != AgentRole.PORTFOLIO_COMMITTEE
            },
            **kwargs,
        }

        # Round 1: Initial arguments from each agent
        for role, analysis in initial_analyses.items():
            if (
                role in self.specialized_agents
                and role != AgentRole.PORTFOLIO_COMMITTEE
            ):
                agent = self.specialized_agents[role]
                context[f"{role.value}_analysis"] = analysis

                try:
                    argument = agent.create_argument(context)
                    if argument:
                        arguments.append(argument)
                        debate_rounds.append(
                            DebateRound(
                                round_number=1,
                                presenting_agent=role,
                                argument=argument,
                                responding_agents=list(initial_analyses.keys()),
                                timestamp=datetime.now(),
                            )
                        )
                except Exception as e:
                    self.logger.error(
                        f"Error getting argument from {role.value}: {str(e)}"
                    )

        # Additional rounds for debate and refinement (simplified)
        # In a full implementation, this would involve multi-round exchanges
        for round_num in range(2, min(self.committee_config.max_debate_rounds + 1, 4)):
            # Simplified: agents can respond to previous arguments
            # In practice, this would be more sophisticated with structured exchanges
            pass

        # Generate consensus
        consensus = self._generate_consensus(initial_analyses, arguments)

        debate_session = DebateSession(
            symbol=symbol,
            initial_analyses=initial_analyses,
            debate_rounds=debate_rounds,
            final_consensus=consensus,
            session_duration=1.0,  # Simplified - would measure actual time
            participant_agents=list(initial_analyses.keys()),
        )

        self.logger.info(
            f"Completed debate for {symbol}. Consensus: {consensus.final_recommendation.value}"
        )

        return debate_session

    def _generate_consensus(
        self, analyses: Dict[AgentRole, AgentAnalysis], arguments: List[AgentArgument]
    ) -> ConsensusResult:
        """Generate final consensus from agent analyses and arguments.

        Args:
            analyses: Agent analyses
            arguments: Debate arguments

        Returns:
            ConsensusResult
        """
        # Weight voting based on agent roles and confidence scores
        votes = {
            RecommendationType.BUY: 0.0,
            RecommendationType.SELL: 0.0,
            RecommendationType.HOLD: 0.0,
        }
        agent_weights = {}

        for role, analysis in analyses.items():
            # Get voting weight for this agent role
            weight = self.committee_config.voting_weights.get(role, 0.25)

            # Adjust weight by confidence score
            adjusted_weight = weight * (analysis.confidence_score / 100.0)
            agent_weights[role] = adjusted_weight

            # Add weighted vote
            votes[analysis.recommendation] += adjusted_weight

        # Determine final recommendation
        final_recommendation = max(votes.keys(), key=lambda k: votes[k])
        total_weight = sum(votes.values())

        # Calculate consensus score (percentage of total weight for winning recommendation)
        if total_weight > 0:
            consensus_score = (votes[final_recommendation] / total_weight) * 100
        else:
            consensus_score = 0

        # Calculate confidence based on consensus and argument alignment
        confidence_score = self._calculate_confidence_score(
            analyses, arguments, consensus_score
        )

        # Identify dissenting opinions
        dissenting_opinions = [
            role
            for role, analysis in analyses.items()
            if analysis.recommendation != final_recommendation
        ]

        # Generate final reasoning
        final_reasoning = self._generate_consensus_reasoning(
            analyses, arguments, final_recommendation, consensus_score
        )

        # Risk assessment (summary from risk manager if available)
        risk_assessment = {}
        if AgentRole.RISK_MANAGER in analyses:
            risk_analysis = analyses[AgentRole.RISK_MANAGER]
            risk_assessment = risk_analysis.metadata.get("risk_assessment", {})

        return ConsensusResult(
            final_recommendation=final_recommendation,
            consensus_score=consensus_score,
            confidence_score=confidence_score,
            participating_agents=list(analyses.keys()),
            arguments=arguments,
            dissenting_opinions=dissenting_opinions,
            final_reasoning=final_reasoning,
            risk_assessment=risk_assessment,
        )

    def _calculate_confidence_score(
        self,
        analyses: Dict[AgentRole, AgentAnalysis],
        arguments: List[AgentArgument],
        consensus_score: float,
    ) -> float:
        """Calculate overall confidence score.

        Args:
            analyses: Agent analyses
            arguments: Debate arguments
            consensus_score: Consensus score

        Returns:
            Confidence score (0-100)
        """
        # Base confidence from consensus
        confidence = consensus_score * 0.6  # 60% weight to consensus

        # Factor in average confidence from agents
        avg_agent_confidence = sum(
            analysis.confidence_score for analysis in analyses.values()
        ) / len(analyses)
        confidence += avg_agent_confidence * 0.3  # 30% weight to agent confidence

        # Factor in argument strength
        if arguments:
            avg_argument_strength = sum(
                abs(arg.confidence_impact) for arg in arguments
            ) / len(arguments)
            confidence += (
                min(avg_argument_strength, 20) * 0.1
            )  # 10% weight to arguments

        return min(100, max(0, confidence))

    def _generate_consensus_reasoning(
        self,
        analyses: Dict[AgentRole, AgentAnalysis],
        arguments: List[AgentArgument],
        final_recommendation: RecommendationType,
        consensus_score: float,
    ) -> str:
        """Generate reasoning for the consensus decision.

        Args:
            analyses: Agent analyses
            arguments: Debate arguments
            final_recommendation: Final recommendation
            consensus_score: Consensus score

        Returns:
            Reasoning string
        """
        reasoning_parts = []

        # Summarize agent positions
        buy_agents = [
            role.value
            for role, analysis in analyses.items()
            if analysis.recommendation == RecommendationType.BUY
        ]
        sell_agents = [
            role.value
            for role, analysis in analyses.items()
            if analysis.recommendation == RecommendationType.SELL
        ]
        hold_agents = [
            role.value
            for role, analysis in analyses.items()
            if analysis.recommendation == RecommendationType.HOLD
        ]

        if buy_agents:
            reasoning_parts.append(f"BUY arguments from: {', '.join(buy_agents)}")
        if sell_agents:
            reasoning_parts.append(f"SELL arguments from: {', '.join(sell_agents)}")
        if hold_agents:
            reasoning_parts.append(f"HOLD arguments from: {', '.join(hold_agents)}")

        # Add consensus information
        reasoning_parts.append(f"Consensus score: {consensus_score:.1f}%")

        # Add key supporting arguments
        supporting_args = [arg for arg in arguments if arg.argument_type == "support"]
        if supporting_args:
            reasoning_parts.append(
                f"Key supporting factors: {len(supporting_args)} agents support this decision"
            )

        # Add opposing arguments if significant
        opposing_args = [arg for arg in arguments if arg.argument_type == "oppose"]
        if opposing_args and len(opposing_args) >= 2:
            reasoning_parts.append(
                f"Significant opposition: {len(opposing_args)} agents oppose this decision"
            )

        # Add risk consideration
        if AgentRole.RISK_MANAGER in analyses:
            risk_analysis = analyses[AgentRole.RISK_MANAGER]
            risk_level = risk_analysis.metadata.get("risk_assessment", {}).get(
                "risk_level", "UNKNOWN"
            )
            reasoning_parts.append(f"Risk assessment: {risk_level}")

        return "; ".join(reasoning_parts)

    def _generate_committee_recommendation(
        self, debate_result: DebateSession
    ) -> ConsensusResult:
        """Generate the final committee recommendation from debate results.

        Args:
            debate_result: Complete debate session result

        Returns:
            Final ConsensusResult
        """
        # The consensus is already generated in the debate result
        return debate_result.final_consensus
