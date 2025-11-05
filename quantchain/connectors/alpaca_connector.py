"""Alpaca data connector for equity and crypto data."""

import pandas as pd
from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime, timezone
import time
from alpaca.data import (
    CryptoHistoricalDataClient,
    StockHistoricalDataClient,
    TimeFrame,
    TimeFrameUnit,
)
from alpaca.data.requests import (
    CryptoBarsRequest,
    StockBarsRequest,
    CryptoLatestQuoteRequest,
    StockLatestQuoteRequest,
)
from alpaca.data.enums import DataFeed
from alpaca.trading import TradingClient
from alpaca.trading.requests import GetAssetsRequest
from alpaca.trading.enums import AssetClass

from .base_interface import DataFeedInterface
from ..core.exceptions import (
    DataSourceError,
    AuthenticationError,
    RateLimitError,
    SymbolNotFoundError,
)


class AlpacaDataConnector(DataFeedInterface):
    """Alpaca data connector supporting both equity and crypto markets."""

    # Timeframe mapping from standard format to Alpaca TimeFrame objects
    TIMEFRAME_MAPPING = {
        "1Min": TimeFrame.Minute,
        "5Min": TimeFrame(5, TimeFrameUnit.Minute),
        "15Min": TimeFrame(15, TimeFrameUnit.Minute),
        "1H": TimeFrame.Hour,
        "4H": TimeFrame(4, TimeFrameUnit.Hour),  # 4 hour timeframe
        "1D": TimeFrame.Day,
        "1W": TimeFrame.Week,
        "1M": TimeFrame.Month,
    }

    def __init__(self, api_key: str, api_secret: str, **kwargs: Any) -> None:
        """Initialize Alpaca data connector.

        Args:
            api_key: Alpaca API key
            api_secret: Alpaca API secret
            **kwargs: Additional configuration
                - use_paper: Whether to use paper trading (default: True)
                - crypto_feed: Data feed for crypto (default: 'iex' for free tier)
                - symbol_limit: Maximum number of symbols to return in
                  get_available_symbols (default: None, no limit)
                - cache_ttl: Symbol cache time-to-live in seconds (default: 3600)
        """
        super().__init__(api_key, api_secret, **kwargs)

        self.api_key = api_key
        self.api_secret = api_secret
        self.use_paper = kwargs.get("use_paper", True)
        self.crypto_feed = kwargs.get("crypto_feed", DataFeed.IEX)
        self.symbol_limit = kwargs.get("symbol_limit", None)
        self._cache_ttl = kwargs.get("cache_ttl", 3600)  # 1 hour default

        try:
            # Initialize clients
            self.stock_client = StockHistoricalDataClient(api_key, api_secret)
            self.crypto_client = CryptoHistoricalDataClient(api_key, api_secret)
            self.trading_client = TradingClient(
                api_key, api_secret, paper=self.use_paper
            )

            # Cache for symbol information
            self._symbol_cache: Dict[str, Dict[str, Any]] = {}
            self._cache_timestamp: Optional[float] = None

        except Exception as e:
            raise AuthenticationError(
                f"Failed to authenticate with Alpaca: {str(e)}"
            ) from e

    def _is_crypto_symbol(self, symbol: str) -> bool:
        """Check if symbol is a crypto pair."""
        return "-" in symbol or "/" in symbol

    def _normalize_crypto_symbol(self, symbol: str) -> str:
        """Normalize crypto symbol to Alpaca format (e.g., 'BTC/USD' -> 'BTC/USD')."""
        return symbol.replace("-", "/") if "-" in symbol else symbol

    def _convert_timeframe(self, timeframe: str) -> TimeFrame:
        """Convert standard timeframe to Alpaca TimeFrame object."""
        if timeframe not in self.TIMEFRAME_MAPPING:
            raise ValueError(
                f"Timeframe {timeframe} not supported. "
                f"Supported: {list(self.TIMEFRAME_MAPPING.keys())}"
            )
        return self.TIMEFRAME_MAPPING[timeframe]  # type: ignore[no-any-return]

    def _refresh_symbol_cache(self) -> None:
        """Refresh the symbol cache if needed."""
        now = time.time()
        if (
            self._cache_timestamp is None
            or (now - self._cache_timestamp) > self._cache_ttl
        ):
            try:
                # Get all assets
                assets_request = GetAssetsRequest(asset_class=None)
                assets = self.trading_client.get_all_assets(assets_request)

                self._symbol_cache = {}
                for asset in assets:
                    # Ensure we're working with Asset objects, not strings
                    if hasattr(asset, "symbol") and hasattr(asset, "asset_class"):
                        # type: ignore[union-attr]
                        asset_name = getattr(asset, "name", asset.symbol)
                        self._symbol_cache[asset.symbol] = {
                            "symbol": asset.symbol,
                            "name": asset_name or asset.symbol,
                            "market": (
                                "crypto"
                                if asset.asset_class == AssetClass.CRYPTO
                                else "equity"
                            ),
                            "currency": "USD",  # Alpaca primarily deals in USD
                            "min_order_size": getattr(asset, "min_order_size", None)
                            or 1,
                            "max_order_size": getattr(asset, "max_order_size", None),
                            "price_precision": (
                                2 if asset.asset_class == AssetClass.US_EQUITY else 4
                            ),
                            "size_precision": (
                                0 if asset.asset_class == AssetClass.US_EQUITY else 8
                            ),
                            "tradable": getattr(asset, "tradable", False),
                            "fractionable": getattr(asset, "fractionable", False)
                            or False,
                        }

                self._cache_timestamp = now

            except Exception as e:
                # Check for rate limit indicators in error message
                error_msg = str(e).lower()
                if (
                    "rate limit" in error_msg
                    or "429" in error_msg
                    or "too many requests" in error_msg
                ):
                    raise RateLimitError(
                        "Rate limit exceeded while refreshing symbol cache"
                    ) from e
                raise DataSourceError(
                    f"Failed to refresh symbol cache: {str(e)}"
                ) from e

    def invalidate_symbol_cache(self) -> None:
        """Manually invalidate the symbol cache to force refresh on next access."""
        self._cache_timestamp = None
        self._symbol_cache.clear()

    def get_historical_data(
        self,
        symbol: str,
        timeframe: str,
        start_date: datetime,
        end_date: Optional[datetime] = None,
        limit: Optional[int] = None,
    ) -> pd.DataFrame:
        """Fetch historical price data for a symbol."""
        try:
            alpaca_timeframe = self._convert_timeframe(timeframe)

            if end_date is None:
                end_date = datetime.now(timezone.utc)

            # Ensure timezone awareness
            if start_date.tzinfo is None:
                start_date = start_date.replace(tzinfo=timezone.utc)
            if end_date.tzinfo is None:
                end_date = end_date.replace(tzinfo=timezone.utc)

            if self._is_crypto_symbol(symbol):
                # Crypto data
                normalized_symbol = self._normalize_crypto_symbol(symbol)
                crypto_request = CryptoBarsRequest(
                    symbol_or_symbols=[normalized_symbol],
                    timeframe=alpaca_timeframe,
                    start=start_date,
                    end=end_date,
                    limit=limit,
                )
                bars = self.crypto_client.get_crypto_bars(crypto_request)
                data = bars[normalized_symbol] if normalized_symbol in bars else []

            else:
                # Equity data
                stock_request = StockBarsRequest(
                    symbol_or_symbols=[symbol],
                    timeframe=alpaca_timeframe,
                    start=start_date,
                    end=end_date,
                    limit=limit,
                    feed=DataFeed.IEX,
                )
                bars = self.stock_client.get_stock_bars(stock_request)
                data = bars[symbol] if symbol in bars else []

            if not data:
                raise SymbolNotFoundError(f"No data found for symbol: {symbol}")

            # Convert to DataFrame
            records = []
            for bar in data:
                records.append(
                    {
                        "timestamp": bar.timestamp,
                        "open": float(bar.open),
                        "high": float(bar.high),
                        "low": float(bar.low),
                        "close": float(bar.close),
                        "volume": int(bar.volume),
                    }
                )

            df = pd.DataFrame(records)
            df["timestamp"] = pd.to_datetime(df["timestamp"])
            df = df.sort_values("timestamp").reset_index(drop=True)

            return df

        except Exception as e:
            if isinstance(e, (SymbolNotFoundError, ValueError)):
                raise
            # Check for rate limit indicators in error message
            error_msg = str(e).lower()
            if (
                "rate limit" in error_msg
                or "429" in error_msg
                or "too many requests" in error_msg
            ):
                raise RateLimitError(
                    f"Rate limit exceeded while fetching historical data for {symbol}"
                ) from e
            raise DataSourceError(
                f"Failed to fetch historical data for {symbol}: {str(e)}"
            ) from e

    def _get_quote_data(self, symbol: str, is_crypto: bool) -> Tuple[Any, str]:
        """Get quote data for a symbol, handling both crypto and equity."""
        try:
            if is_crypto:
                # Crypto latest quote
                normalized_symbol = self._normalize_crypto_symbol(symbol)
                crypto_request = CryptoLatestQuoteRequest(
                    symbol_or_symbols=[normalized_symbol]
                )
                quotes = self.crypto_client.get_crypto_latest_quote(crypto_request)

                if normalized_symbol not in quotes:
                    raise SymbolNotFoundError(f"Crypto symbol not found: {symbol}")

                return quotes[normalized_symbol], "crypto"
            else:
                # Equity latest quote
                stock_request = StockLatestQuoteRequest(symbol_or_symbols=[symbol])
                quotes = self.stock_client.get_stock_latest_quote(stock_request)

                if symbol not in quotes:
                    raise SymbolNotFoundError(f"Equity symbol not found: {symbol}")

                return quotes[symbol], "equity"
        except Exception as e:
            if isinstance(e, SymbolNotFoundError):
                raise
            # Check for rate limit indicators in error message
            error_msg = str(e).lower()
            if (
                "rate limit" in error_msg
                or "429" in error_msg
                or "too many requests" in error_msg
            ):
                raise RateLimitError(
                    f"Rate limit exceeded while fetching quote data for {symbol}"
                ) from e
            raise DataSourceError(
                f"Failed to fetch quote data for {symbol}: {str(e)}"
            ) from e

    def get_real_time_data(self, symbol: str) -> Dict[str, Any]:
        """Fetch real-time price data for a symbol."""
        quote, market_type = self._get_quote_data(
            symbol, self._is_crypto_symbol(symbol)
        )

        if market_type == "crypto":
            return {
                "timestamp": quote.timestamp,
                "price": float(quote.ask_price),
                "bid": float(quote.bid_price),
                "ask": float(quote.ask_price),
                "volume": 0,  # Crypto quotes don't include volume
            }
        else:  # equity
            return {
                "timestamp": quote.timestamp,
                "price": float((quote.bid_price + quote.ask_price) / 2),
                "bid": float(quote.bid_price),
                "ask": float(quote.ask_price),
                "volume": 0,  # Latest quote doesn't include volume
            }

    def get_quote(self, symbol: str) -> Dict[str, Any]:
        """Get current quote for a symbol."""
        quote, market_type = self._get_quote_data(
            symbol, self._is_crypto_symbol(symbol)
        )

        base_data = {
            "symbol": symbol,
            "timestamp": quote.timestamp,
            "bid_price": float(quote.bid_price),
            "ask_price": float(quote.ask_price),
            "bid_size": float(quote.bid_size),
            "ask_size": float(quote.ask_size),
        }

        if market_type == "crypto":
            base_data.update(
                {
                    "last_price": float(
                        quote.ask_price
                    ),  # Use ask as last price for crypto
                    "last_size": float(quote.ask_size),
                }
            )
        else:  # equity
            base_data.update(
                {
                    "last_price": (float(quote.bid_price) + float(quote.ask_price)) / 2,
                    "last_size": min(float(quote.bid_size), float(quote.ask_size)),
                }
            )

        return base_data

    def get_available_symbols(
        self, market: Optional[str] = None, limit: Optional[int] = None
    ) -> List[str]:
        """Get list of available symbols for trading.

        Args:
            market: Optional market filter ('crypto', 'equity', or None for all)
            limit: Optional limit override (defaults to self.symbol_limit or no limit)

        Returns:
            List of available symbols
        """
        try:
            self._refresh_symbol_cache()

            if market is None:
                symbols = list(self._symbol_cache.keys())
            elif market.lower() == "crypto":
                symbols = [
                    s
                    for s, info in self._symbol_cache.items()
                    if info["market"] == "crypto"
                ]
            elif market.lower() == "equity":
                symbols = [
                    s
                    for s, info in self._symbol_cache.items()
                    if info["market"] == "equity"
                ]
            else:
                return []

            # Apply limit if specified
            if limit is not None:
                symbols = symbols[:limit]
            elif self.symbol_limit is not None:
                symbols = symbols[: self.symbol_limit]

            return symbols

        except Exception as e:
            raise DataSourceError(f"Failed to fetch available symbols: {str(e)}") from e

    def get_symbol_info(self, symbol: str) -> Dict[str, Any]:
        """Get detailed information about a symbol."""
        try:
            self._refresh_symbol_cache()

            if symbol not in self._symbol_cache:
                raise SymbolNotFoundError(f"Symbol not found: {symbol}")

            return self._symbol_cache[symbol].copy()

        except SymbolNotFoundError:
            raise
        except Exception as e:
            raise DataSourceError(
                f"Failed to fetch symbol info for {symbol}: {str(e)}"
            ) from e

    def is_market_open(self, market: Optional[str] = None) -> bool:
        """Check if the market is currently open for trading."""
        try:
            # Check for crypto market first (no API call needed)
            if market and market.lower() == "crypto":
                # Crypto markets are always open
                return True

            # Alpaca provides market clock information
            clock = self.trading_client.get_clock()

            # For equities or no specific market, use the market clock
            # Handle both Clock object and dict response
            if hasattr(clock, "is_open"):
                return clock.is_open  # type: ignore[no-any-return]
            elif isinstance(clock, dict) and "is_open" in clock:
                return clock["is_open"]  # type: ignore[no-any-return]
            else:
                return False

        except Exception as e:
            raise DataSourceError(f"Failed to check market status: {str(e)}") from e
