"""QuantChain: A financial framework for building quantitative trading agents."""

__version__ = "0.1.0"
__author__ = "QuantChain Team"
__email__ = "team@quantchain.dev"

from . import agents, backtesting, connectors, core, tools

__all__ = ["agents", "tools", "connectors", "backtesting", "core"]
