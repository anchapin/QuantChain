"""Base interface for data feed connectors."""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional

import pandas as pd


class DataFeedInterface(ABC):
    """Abstract base class for all data feed connectors."""

    @abstractmethod
    def __init__(
        self, api_key: str, api_secret: Optional[str] = None, **kwargs: Any
    ) -> None:
        """Initialize the data feed connector.

        Args:
            api_key: API key for authentication
            api_secret: Optional API secret for authentication
            **kwargs: Additional provider-specific configuration
        """
        # Store the parameters to avoid empty abstract method body
        self._api_key = api_key
        self._api_secret = api_secret
        self._kwargs = kwargs

    @abstractmethod
    def get_historical_data(
        self,
        symbol: str,
        timeframe: str,
        start_date: datetime,
        end_date: Optional[datetime] = None,
        limit: Optional[int] = None,
    ) -> pd.DataFrame:
        """Fetch historical price data for a symbol.

        Args:
            symbol: Trading symbol (e.g., 'AAPL', 'BTC-USD', 'ETH/USDT')
            timeframe: Timeframe string (e.g., '1Min', '5Min', '1H', '1D')
            start_date: Start date for data retrieval
            end_date: End date for data retrieval (defaults to now)
            limit: Maximum number of records to return

        Returns:
            DataFrame with columns: timestamp, open, high, low, close, volume

        Raises:
            DataSourceError: If data cannot be fetched
            ValueError: If parameters are invalid
        """

    @abstractmethod
    def get_real_time_data(self, symbol: str) -> Dict[str, Any]:
        """Fetch real-time price data for a symbol.

        Args:
            symbol: Trading symbol

        Returns:
            Dict containing current price data with keys:
            - timestamp: Current timestamp
            - price: Current price
            - bid: Best bid price (if available)
            - ask: Best ask price (if available)
            - volume: Recent volume

        Raises:
            DataSourceError: If data cannot be fetched
        """

    @abstractmethod
    def get_quote(self, symbol: str) -> Dict[str, Any]:
        """Get current quote for a symbol.

        Args:
            symbol: Trading symbol

        Returns:
            Dict containing quote data with keys:
            - symbol: Trading symbol
            - timestamp: Quote timestamp
            - bid_price: Bid price
            - ask_price: Ask price
            - bid_size: Bid size
            - ask_size: Ask size
            - last_price: Last traded price
            - last_size: Last traded size

        Raises:
            DataSourceError: If quote cannot be fetched
        """

    @abstractmethod
    def get_available_symbols(self, market: Optional[str] = None) -> List[str]:
        """Get list of available symbols for trading.

        Args:
            market: Optional market filter (e.g., 'equity', 'crypto', 'forex')

        Returns:
            List of available trading symbols

        Raises:
            DataSourceError: If symbols cannot be fetched
        """

    @abstractmethod
    def get_symbol_info(self, symbol: str) -> Dict[str, Any]:
        """Get detailed information about a symbol.

        Args:
            symbol: Trading symbol

        Returns:
            Dict containing symbol information with keys:
            - symbol: Trading symbol
            - name: Full name/description
            - market: Market type (equity, crypto, forex, etc.)
            - currency: Base currency
            - min_order_size: Minimum order size
            - max_order_size: Maximum order size
            - price_precision: Number of decimal places for price
            - size_precision: Number of decimal places for size

        Raises:
            DataSourceError: If symbol info cannot be fetched
            ValueError: If symbol is not found
        """

    @abstractmethod
    def is_market_open(self, market: Optional[str] = None) -> bool:
        """Check if the market is currently open for trading.

        Args:
            market: Optional specific market to check

        Returns:
            True if market is open, False otherwise

        Raises:
            DataSourceError: If market status cannot be determined
        """
