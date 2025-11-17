"""Agent implementations for QuantChain trading strategies."""

from . import zoo
from .base import (
    AgentAnalysis,
    AgentArgument,
    AgentRole,
    BaseSpecializedAgent,
    ConsensusResult,
    RecommendationType,
)
from .chart_reader_agent import ChartReaderAgent, ChartReaderAgentConfig
from .fundamentals_analyst import FundamentalsAnalystAgent
from .portfolio_committee import PortfolioCommitteeAgent
from .risk_manager import RiskManagerAgent
from .sentiment_expert import SentimentExpertAgent
from .smart_contract_auditor import (
    SmartContractAuditorAgent,
    SmartContractAuditorConfig,
)
from .technical_analyst import TechnicalAnalystAgent

__all__ = [
    "zoo",
    # Base classes and enums
    "AgentAnalysis",
    "AgentArgument",
    "AgentRole",
    "BaseSpecializedAgent",
    "ConsensusResult",
    "RecommendationType",
    # Individual agents
    "ChartReaderAgent",
    "ChartReaderAgentConfig",
    "FundamentalsAnalystAgent",
    "PortfolioCommitteeAgent",
    "RiskManagerAgent",
    "SentimentExpertAgent",
    "SmartContractAuditorAgent",
    "SmartContractAuditorConfig",
    "TechnicalAnalystAgent",
]
