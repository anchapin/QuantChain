"""Data connectors for various financial data sources."""

# Python 3.9 compatibility: Add optional dependency guards
ALPACA_AVAILABLE = False
try:
    from alpaca.data import (
        HistoricalCryptoData,
        StockDataStream,
        StockTradeApi,
    )
    from alpaca.trading.client import Client as AlpacaTradingClient
    from alpaca import TradingStream
    ALPACA_AVAILABLE = True
except ImportError:
    pass

# Similar guards for other optional dependencies
IB_ASYNC_AVAILABLE = False
try:
    import ib_async
    IB_ASYNC_AVAILABLE = True
except ImportError:
    pass

LANGGRAPH_AVAILABLE = False
try:
    from langgraph.graph import StateGraph, END
    LANGGRAPH_AVAILABLE = True
except ImportError:
    pass

from .alpaca_connector import AlpacaDataConnector
from .alpaca_execution import AlpacaExecutionConnector
from .alpha_vantage_connector import AlphaVantageDataConnector
from .base_interface import DataFeedInterface
from .ccxt_connector import CCXTDataConnector
from .dexscreener_connector import DexscreenerDataConnector
from .ib_execution import IBExecutionConnector
from .polygon_connector import PolygonDataConnector

__all__ = [
    "DataFeedInterface",
    "AlpacaDataConnector",
    "AlpacaExecutionConnector",
    "AlphaVantageDataConnector",
    "CCXTDataConnector",
    "DexscreenerDataConnector",
    "IBExecutionConnector",
    "PolygonDataConnector",
]
