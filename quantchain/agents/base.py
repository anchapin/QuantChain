"""Base classes for QuantChain specialized trading agents."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Protocol

from ..core.config import QuantChainConfig
from ..core.llm_providers import LLMProvider


class AgentRole(Enum):
    """Roles for different agent types."""

    FUNDAMENTALS = "fundamentals_analyst"
    SENTIMENT = "sentiment_expert"
    TECHNICAL = "technical_analyst"
    RISK_MANAGER = "risk_manager"
    PORTFOLIO_COMMITTEE = "portfolio_committee"


class RecommendationType(Enum):
    """Trading recommendation types."""

    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


@dataclass
class AgentAnalysis:
    """Base class for agent analysis results."""

    agent_role: AgentRole
    symbol: str
    timestamp: datetime
    recommendation: RecommendationType
    confidence_score: float  # 0-100
    reasoning: str
    data_sources: List[str]
    metadata: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        return {
            "agent_role": self.agent_role.value,
            "symbol": self.symbol,
            "timestamp": self.timestamp.isoformat(),
            "recommendation": self.recommendation.value,
            "confidence_score": self.confidence_score,
            "reasoning": self.reasoning,
            "data_sources": self.data_sources,
            "metadata": self.metadata,
        }


@dataclass
class AgentArgument:
    """Represents an argument in the agent debate."""

    agent_role: AgentRole
    argument_type: str  # "support", "oppose", "neutral"
    target_agent: Optional[AgentRole]  # Which agent this argument targets
    reasoning: str
    evidence: List[str]
    confidence_impact: float  # -100 to 100 impact on confidence

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        return {
            "agent_role": self.agent_role.value,
            "argument_type": self.argument_type,
            "target_agent": self.target_agent.value if self.target_agent else None,
            "reasoning": self.reasoning,
            "evidence": self.evidence,
            "confidence_impact": self.confidence_impact,
        }


@dataclass
class ConsensusResult:
    """Final consensus result from portfolio committee."""

    final_recommendation: RecommendationType
    consensus_score: float  # 0-100, higher = more consensus
    confidence_score: float  # 0-100
    participating_agents: List[AgentRole]
    arguments: List[AgentArgument]
    dissenting_opinions: List[AgentRole]
    final_reasoning: str
    risk_assessment: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        return {
            "final_recommendation": self.final_recommendation.value,
            "consensus_score": self.consensus_score,
            "confidence_score": self.confidence_score,
            "participating_agents": [
                agent.value for agent in self.participating_agents
            ],
            "arguments": [arg.to_dict() for arg in self.arguments],
            "dissenting_opinions": [agent.value for agent in self.dissenting_opinions],
            "final_reasoning": self.final_reasoning,
            "risk_assessment": self.risk_assessment,
        }


class LLMInterface(Protocol):
    """Protocol for LLM interface."""

    def generate(self, prompt: str, max_tokens: Optional[int] = None) -> Any:
        """Generate text from LLM."""
        ...

    def generate_vision(self, image_data: bytes, prompt: str) -> Any:
        """Generate analysis from image data."""
        ...


class BaseSpecializedAgent(ABC):
    """Base class for specialized trading agents."""

    def __init__(
        self,
        config: QuantChainConfig,
        llm_provider: LLMProvider,
        role: AgentRole,
    ):
        """Initialize the specialized agent.

        Args:
            config: QuantChain configuration
            llm_provider: LLM provider for analysis
            role: Agent role in the system
        """
        self.config = config
        self.llm_provider = llm_provider
        self.role = role
        self.agent_config = config.get("agents", {}).get(role.value, {})

    @abstractmethod
    def analyze(self, symbol: str, **kwargs) -> AgentAnalysis:
        """Perform analysis for a given symbol.

        Args:
            symbol: Trading symbol to analyze
            **kwargs: Additional analysis parameters

        Returns:
            AgentAnalysis with recommendation and reasoning
        """
        pass

    @abstractmethod
    def create_argument(self, context: Dict[str, Any]) -> AgentArgument:
        """Create an argument for the debate phase.

        Args:
            context: Context including other agents' analyses

        Returns:
            AgentArgument for portfolio committee debate
        """
        pass

    def validate_data_sources(self, data_sources: List[str]) -> bool:
        """Validate that required data sources are available.

        Args:
            data_sources: List of available data sources

        Returns:
            True if all required sources are available
        """
        required_sources = self.agent_config.get("required_data_sources", [])
        return all(source in data_sources for source in required_sources)

    def get_confidence_threshold(self) -> float:
        """Get the confidence threshold for this agent.

        Returns:
            Confidence threshold (0-100)
        """
        return self.agent_config.get("confidence_threshold", 70.0)

    def _create_base_analysis(
        self,
        symbol: str,
        recommendation: RecommendationType,
        confidence_score: float,
        reasoning: str,
        data_sources: List[str],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> AgentAnalysis:
        """Create a base AgentAnalysis object.

        Args:
            symbol: Trading symbol
            recommendation: Trading recommendation
            confidence_score: Confidence score (0-100)
            reasoning: Analysis reasoning
            data_sources: Data sources used
            metadata: Additional metadata

        Returns:
            AgentAnalysis object
        """
        return AgentAnalysis(
            agent_role=self.role,
            symbol=symbol,
            timestamp=datetime.now(),
            recommendation=recommendation,
            confidence_score=confidence_score,
            reasoning=reasoning,
            data_sources=data_sources,
            metadata=metadata or {},
        )
