"""Agent implementations for QuantChain trading strategies."""

from .chart_reader_agent import ChartReaderAgent, ChartReaderAgentConfig
from .memecoin_vibe_trader import MemecoinVibeTrader, MemecoinVibeTraderConfig
from .smart_contract_auditor import SmartContractAuditorAgent, SmartContractAuditorConfig

__all__ = [
    "zoo",
    "ChartReaderAgent",
    "ChartReaderAgentConfig",
    "MemecoinVibeTrader",
    "MemecoinVibeTraderConfig",
    "SmartContractAuditorAgent",
    "SmartContractAuditorConfig",
]
