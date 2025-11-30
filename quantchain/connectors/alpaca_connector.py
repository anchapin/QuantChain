"""Alpaca data connector for QuantChain."""

import os
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

try:
    import pandas as pd

    _PANDAS_AVAILABLE = True
except ImportError:
    _PANDAS_AVAILABLE = False

try:
    from alpaca.data import TimeFrame
    from alpaca.data.historical import (
        CryptoHistoricalDataClient,
        StockHistoricalDataClient,
    )
    from alpaca.trading.client import TradingClient
    from alpaca.trading.enums import AssetClass

    _ALPACA_AVAILABLE = True
except ImportError:
    _ALPACA_AVAILABLE = False

from quantchain.core.exceptions import (
    AuthenticationError,
    DataSourceError,
    SymbolNotFoundError,
)


class AlpacaDataConnector:
    """Connector for Alpaca data API."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        secret_key: Optional[str] = None,
        paper_trading: bool = True,
        symbol_limit: int = 100,
        retry_count: int = 3,
        retry_delay: float = 1.0,
    ):
        """
        Initialize Alpaca connector.

        Args:
            api_key: Alpaca API key
            secret_key: Alpaca secret key
            paper: Whether to use paper trading
            symbol_limit: Maximum symbols to cache
            retry_count: Number of retries for failed requests
            retry_delay: Delay between retries in seconds
        """
        # Get credentials from environment if not provided
        self.api_key = api_key or os.environ.get("ALPACA_API_KEY")
        self.secret_key = secret_key or os.environ.get("ALPACA_SECRET_KEY")
        self.paper_trading = paper_trading
        self.symbol_limit = symbol_limit
        self.retry_count = retry_count
        self.retry_delay = retry_delay

        # Initialize clients
        self.stock_client = None
        self.crypto_client = None
        self.trading_client = None
        self._symbol_cache: Dict[str, Any] = {}

        # Validate credentials
        if not self.api_key or not self.secret_key:
            raise AuthenticationError("Alpaca API credentials not provided")

        # Initialize clients if library is available
        if _ALPACA_AVAILABLE:
            self._initialize_clients()

    def _initialize_clients(self) -> None:
        """Initialize Alpaca clients."""
        try:
            self.stock_client = StockHistoricalDataClient(self.api_key, self.secret_key)
            self.crypto_client = CryptoHistoricalDataClient(
                self.api_key, self.secret_key
            )
            self.trading_client = TradingClient(
                self.api_key, self.secret_key, paper=self.paper_trading
            )
        except Exception as e:
            raise AuthenticationError(f"Failed to authenticate with Alpaca: {str(e)}")

    def _is_crypto_symbol(self, symbol: str) -> bool:
        """Check if a symbol is a cryptocurrency."""
        # Cryptocurrency symbols typically contain "/" or "-"
        return "/" in symbol or "-" in symbol

    def _normalize_crypto_symbol(self, symbol: str) -> str:
        """Normalize cryptocurrency symbol to Alpaca format."""
        # Convert "/" to "/" if needed (no change)
        # Convert "-" to "/"
        return symbol.replace("-", "/")

    def _convert_timeframe(self, timeframe: str) -> TimeFrame:
        """Convert timeframe string to Alpaca TimeFrame."""
        timeframe_map = {
            "1Min": TimeFrame.Minute,
            "5Min": TimeFrame.Minute,
            "15Min": TimeFrame.Minute,
            "1H": TimeFrame.Hour,
            "4H": TimeFrame.Hour,
            "1D": TimeFrame.Day,
        }

        if timeframe not in timeframe_map:
            raise ValueError(f"Timeframe {timeframe} not supported")

        return timeframe_map[timeframe]

    def _refresh_symbol_cache(self) -> None:
        """Refresh the symbol cache from Alpaca."""
        if not _ALPACA_AVAILABLE or not self.trading_client:
            self._symbol_cache = {}
            return

        try:
            # Get all assets from Alpaca
            assets = self.trading_client.get_all_assets()

            # Update cache
            for asset in assets:
                if hasattr(asset, "symbol") and hasattr(asset, "asset_class"):
                    self._symbol_cache[asset.symbol] = {
                        "market": (
                            "equity"
                            if asset.asset_class == AssetClass.US_EQUITY
                            else "crypto"
                        )
                    }

            # Limit cache size
            if len(self._symbol_cache) > self.symbol_limit:
                self._symbol_cache = dict(
                    list(self._symbol_cache.items())[: self.symbol_limit]
                )

        except Exception as e:
            # Log error but continue with empty cache
            self._symbol_cache = {}

    def get_historical_data(
        self,
        symbol: str,
        timeframe: str,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        limit: Optional[int] = None,
    ) -> pd.DataFrame:
        """
        Get historical OHLCV data for a symbol.

        Args:
            symbol: Trading symbol
            timeframe: Timeframe for data (1Min, 5Min, 15Min, 1H, 4H, 1D)
            start: Start date for data
            end: End date for data
            limit: Maximum number of bars to return

        Returns:
            Pandas DataFrame with OHLCV data
        """
        if not _ALPACA_AVAILABLE:
            raise DataSourceError("Alpaca library not installed")

        # Normalize crypto symbols
        is_crypto = self._is_crypto_symbol(symbol)
        if is_crypto:
            symbol = self._normalize_crypto_symbol(symbol)

        # Convert timeframe
        try:
            tf = self._convert_timeframe(timeframe)
        except ValueError as e:
            raise ValueError(str(e))

        # Refresh symbol cache if needed
        if not self._symbol_cache:
            self._refresh_symbol_cache()

        # Check if symbol exists
        if symbol not in self._symbol_cache:
            raise SymbolNotFoundError(f"Symbol {symbol} not found")

        # Set default dates if not provided
        if not end:
            end = datetime.now()
        if not start:
            if timeframe in ["1Min", "5Min", "15Min"]:
                # For intraday, get last 7 days
                start = end - timedelta(days=7)
            else:
                # For daily and hourly, get last year
                start = end - timedelta(days=365)

        # Retry mechanism
        for attempt in range(self.retry_count):
            try:
                if is_crypto:
                    if self.crypto_client is None:
                        raise DataSourceError("Crypto client not initialized")
                    bars = self.crypto_client.get_crypto_bars(
                        symbol, tf, start=start, end=end, limit=limit
                    )
                else:
                    if self.stock_client is None:
                        raise DataSourceError("Stock client not initialized")
                    bars = self.stock_client.get_stock_bars(
                        symbol, tf, start=start, end=end, limit=limit
                    )

                if not bars or symbol not in bars:
                    raise SymbolNotFoundError(f"No data found for symbol {symbol}")

                # Convert to DataFrame
                if not _PANDAS_AVAILABLE:
                    raise DataSourceError("pandas is required for data handling")

                df = bars.df if hasattr(bars, "df") else pd.DataFrame()
                return df

            except Exception as e:
                if attempt == self.retry_count - 1:
                    raise DataSourceError(f"Failed to get data for {symbol}: {str(e)}")

                time.sleep(self.retry_delay)

        # Return empty DataFrame if all retries fail
        return pd.DataFrame()

    def get_real_time_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get real-time quote data for a symbol.

        Args:
            symbol: Trading symbol

        Returns:
            Dictionary with price data
        """
        if not _ALPACA_AVAILABLE:
            raise DataSourceError("Alpaca library not installed")

        # Normalize crypto symbols
        is_crypto = self._is_crypto_symbol(symbol)
        if is_crypto:
            symbol = self._normalize_crypto_symbol(symbol)

        # Refresh symbol cache if needed
        if not self._symbol_cache:
            self._refresh_symbol_cache()

        # Check if symbol exists
        if symbol not in self._symbol_cache:
            raise SymbolNotFoundError(f"Symbol {symbol} not found")

        # Retry mechanism
        for attempt in range(self.retry_count):
            try:
                if is_crypto:
                    if self.crypto_client is None:
                        raise DataSourceError("Crypto client not initialized")
                    quotes = self.crypto_client.get_crypto_latest_quote(symbol)
                else:
                    if self.stock_client is None:
                        raise DataSourceError("Stock client not initialized")
                    quotes = self.stock_client.get_stock_latest_quote(symbol)

                if not quotes or symbol not in quotes:
                    raise SymbolNotFoundError(f"No quote data for symbol {symbol}")

                quote = quotes[symbol]

                # Format response
                data = {
                    "symbol": symbol,
                    "bid": quote.bid_price,
                    "ask": quote.ask_price,
                    "price": (quote.bid_price + quote.ask_price)
                    / 2,  # Mid-price for stocks
                    "timestamp": quote.timestamp,
                }

                # For crypto, use ask price (bid/ask may have large spread)
                if is_crypto:
                    data["price"] = quote.ask_price

                return data

            except Exception as e:
                if attempt == self.retry_count - 1:
                    raise DataSourceError(f"Failed to get quote for {symbol}: {str(e)}")

                time.sleep(self.retry_delay)

        # Return None if all retries fail
        return None

    def get_quote(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed quote information for a symbol.

        Args:
            symbol: Trading symbol

        Returns:
            Dictionary with detailed quote information
        """
        # Get real-time data
        data = self.get_real_time_data(symbol)
        if data is None:
            return None

        # Add additional fields
        data.update(
            {
                "last_price": data["price"],
                "bid_size": getattr(data, "bid_size", 0),
                "ask_size": getattr(data, "ask_size", 0),
            }
        )

        return data

    def get_available_symbols(
        self, market: Optional[str] = None, limit: Optional[int] = None
    ) -> List[str]:
        """
        Get list of available trading symbols.

        Args:
            market: Filter by market ('equity' or 'crypto')
            limit: Limit number of results

        Returns:
            List of symbol strings
        """
        # Refresh symbol cache if needed
        if not self._symbol_cache:
            self._refresh_symbol_cache()

        # Filter by market
        if market:
            symbols = [
                symbol
                for symbol, info in self._symbol_cache.items()
                if info.get("market") == market
            ]
        else:
            symbols = list(self._symbol_cache.keys())

        # Apply limit
        if limit:
            symbols = symbols[:limit]

        return symbols

    def get_symbol_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a symbol.

        Args:
            symbol: Trading symbol

        Returns:
            Dictionary with symbol information
        """
        # Refresh symbol cache if needed
        if not self._symbol_cache:
            self._refresh_symbol_cache()

        # Check if symbol exists
        if symbol not in self._symbol_cache:
            raise SymbolNotFoundError(f"Symbol {symbol} not found")

        # Get basic info from cache
        info = self._symbol_cache[symbol].copy() if symbol in self._symbol_cache else {}

        # Add symbol itself
        info["symbol"] = symbol

        # Add additional fields
        info.update(
            {
                "name": info.get("name", symbol),
                "market": info.get("market"),
                "currency": "USD",  # Default currency
                "price_precision": 2,  # Default precision
                "size_precision": 0,  # Default precision
                "tradable": True,  # Assume tradable
                "fractionable": info.get("fractionable", False),
            }
        )

        return info

    def is_market_open(self, market: Optional[str] = None) -> bool:
        """
        Check if market is open.

        Args:
            market: Market to check ('equity' or 'crypto')
                      If None, checks equity market

        Returns:
            True if market is open, False otherwise
        """
        if market == "crypto":
            # Crypto markets are 24/7
            return True

        # For equity market, check with Alpaca
        if not _ALPACA_AVAILABLE or not self.trading_client:
            raise DataSourceError("Alpaca library not available")

        try:
            clock = self.trading_client.get_clock()
            return clock.is_open if hasattr(clock, "is_open") else True
        except Exception as e:
            raise DataSourceError(f"Failed to get market status: {str(e)}")
