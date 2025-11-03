"""Dexscreener data connector for DEX token data."""

import requests
import pandas as pd
import logging
from typing import List, Dict, Optional, Any, cast
from datetime import datetime, timezone
import time
from urllib.parse import urljoin

from .base_interface import DataFeedInterface
from ..core.exceptions import DataSourceError, SymbolNotFoundError
from ..core.retry import RetryHandler


class DexscreenerDataConnector(DataFeedInterface):
    """Dexscreener data connector for DEX token pairs."""

    BASE_URL = "https://api.dexscreener.com/latest/"

    # Supported timeframes (Dexscreener doesn't provide historical data, only current)
    SUPPORTED_TIMEFRAMES = ["1Min", "5Min", "15Min", "1H", "4H", "1D"]

    def __init__(self, api_key: Optional[str] = None, **kwargs: Any) -> None:
        """Initialize Dexscreener data connector.

        Args:
            api_key: Optional API key (Dexscreener doesn't require auth for basic data)
            **kwargs: Additional configuration
                - timeout: Request timeout in seconds (default: 30)
                - max_retries: Maximum number of retries (default: 3)
        """
        super().__init__(api_key or "", api_secret=None, **kwargs)

        self.api_key = api_key
        self.timeout = kwargs.get("timeout", 30)
        self.max_retries = kwargs.get("max_retries", 3)
        self.session = requests.Session()
        self.logger = logging.getLogger(__name__)
        self._retry_handler = RetryHandler(
            max_retries=self.max_retries,
            base_delay=1.0,
            backoff_factor=2.0,
            logger=self.logger,
        )

        # Cache for token data
        self._token_cache: Dict[str, Dict[str, Any]] = {}
        self._cache_timestamp: Optional[float] = None
        self._cache_ttl = 300  # 5 minutes (Dexscreener data updates frequently)

    def _make_request(
        self, endpoint: str, params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make HTTP request to Dexscreener API with retry logic."""
        url = urljoin(self.BASE_URL, endpoint)

        def _request() -> Dict[str, Any]:
            response = self.session.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            return response.json()  # type: ignore[no-any-return]

        return self._retry_handler.execute(
            _request, exceptions=(requests.exceptions.RequestException,)
        )

    def _normalize_pair_address(self, symbol: str) -> str:
        """Extract pair address from symbol format like 'TOKEN/USD:ADDRESS'."""
        if ":" in symbol:
            return symbol.split(":")[-1]
        return symbol

    def _refresh_token_cache(self) -> None:
        """Refresh the token cache with trending pairs."""
        now = time.time()
        if (
            self._cache_timestamp is None
            or (now - self._cache_timestamp) > self._cache_ttl
        ):
            try:
                # Get trending pairs from Dexscreener
                data = self._make_request("dex/tokens")  # type: ignore[no-any-return]

                self._token_cache = {}
                if "pairs" in data:
                    for pair in data["pairs"][:100]:  # Limit to top 100 for cache
                        # Use pair address as key, but also store symbol info
                        pair_address = pair.get("pairAddress", "")
                        if pair_address:
                            self._token_cache[pair_address] = pair

                self._cache_timestamp = now

            except Exception as e:
                # Don't fail completely if cache refresh fails
                self.logger.warning(f"Failed to refresh token cache: {str(e)}")

    def _find_pair_by_symbol(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Find pair data by symbol or address."""
        # First try direct pair address lookup
        pair_address = self._normalize_pair_address(symbol)

        # Check cache first
        if pair_address in self._token_cache:
            return self._token_cache[pair_address]

        # Try API lookup for specific pair
        try:
            # type: ignore[no-any-return]
            data = self._make_request(f"dex/pairs/{pair_address}")
            if "pairs" in data and data["pairs"]:
                # type: ignore[no-any-return]
                pair = data["pairs"][0]
                self._token_cache[pair_address] = pair
                return cast(Optional[Dict[str, Any]], pair)
        except DataSourceError:
            pass

        # Search by token symbols if direct lookup fails
        try:
            self._refresh_token_cache()
            # Look for pairs containing the symbol
            for pair_addr, pair_data in self._token_cache.items():
                base_token = pair_data.get("baseToken", {}).get("symbol", "").upper()
                quote_token = pair_data.get("quoteToken", {}).get("symbol", "").upper()
                if (
                    symbol.upper() in [base_token, quote_token]
                    or symbol.upper() == f"{base_token}/{quote_token}"
                ):
                    return pair_data
        except Exception:
            pass

        return None

    def get_historical_data(
        self,
        symbol: str,
        timeframe: str,
        start_date: datetime,
        end_date: Optional[datetime] = None,
        limit: Optional[int] = None,
    ) -> pd.DataFrame:
        """Fetch historical price data for a token pair.

        Note: Dexscreener doesn't provide extensive historical data.
        This method returns current data formatted as a single-row DataFrame.
        """
        if timeframe not in self.SUPPORTED_TIMEFRAMES:
            raise ValueError(
                f"Timeframe {timeframe} not supported. "
                f"Supported: {self.SUPPORTED_TIMEFRAMES}"
            )

        try:
            pair_data = self._find_pair_by_symbol(symbol)
            if not pair_data:
                raise SymbolNotFoundError(f"Token pair not found: {symbol}")

            # Dexscreener only provides current price data, not historical
            # Create a single-row DataFrame with current data
            current_price = float(pair_data.get("priceUsd", 0))
            volume_24h = float(pair_data.get("volume", {}).get("h24", 0))

            # Use current timestamp
            timestamp = datetime.now(timezone.utc)

            # For historical requests, we can only provide current data
            # In a real implementation, integrate with another historical data source
            record = {
                "timestamp": timestamp,
                "open": current_price,
                "high": current_price,
                "low": current_price,
                "close": current_price,
                "volume": volume_24h,
            }

            df = pd.DataFrame([record])
            return df

        except SymbolNotFoundError:
            raise
        except Exception as e:
            raise DataSourceError(
                f"Failed to fetch historical data for {symbol}: {str(e)}"
            )

    def get_real_time_data(self, symbol: str) -> Dict[str, Any]:
        """Fetch real-time price data for a token pair."""
        try:
            pair_data = self._find_pair_by_symbol(symbol)
            if not pair_data:
                raise SymbolNotFoundError(f"Token pair not found: {symbol}")

            return {
                "timestamp": datetime.now(timezone.utc),
                "price": float(pair_data.get("priceUsd", 0)),
                "bid": float(
                    pair_data.get("priceUsd", 0)
                ),  # Dexscreener doesn't provide bid/ask
                "ask": float(pair_data.get("priceUsd", 0)),
                "volume": float(pair_data.get("volume", {}).get("h24", 0)),
            }

        except SymbolNotFoundError:
            raise
        except Exception as e:
            raise DataSourceError(
                f"Failed to fetch real-time data for {symbol}: {str(e)}"
            )

    def get_quote(self, symbol: str) -> Dict[str, Any]:
        """Get current quote for a token pair."""
        try:
            pair_data = self._find_pair_by_symbol(symbol)
            if not pair_data:
                raise SymbolNotFoundError(f"Token pair not found: {symbol}")

            price = float(pair_data.get("priceUsd", 0))
            volume_24h = float(pair_data.get("volume", {}).get("h24", 0))

            return {
                "symbol": symbol,
                "timestamp": datetime.now(timezone.utc),
                "bid_price": price,
                "ask_price": price,
                "bid_size": volume_24h / 2,  # Estimate sizes
                "ask_size": volume_24h / 2,
                "last_price": price,
                "last_size": volume_24h,
            }

        except SymbolNotFoundError:
            raise
        except Exception as e:
            raise DataSourceError(f"Failed to fetch quote for {symbol}: {str(e)}")

    def get_available_symbols(self, market: Optional[str] = None) -> List[str]:
        """Get list of available token pairs."""
        try:
            self._refresh_token_cache()

            symbols = []
            for pair_addr, pair_data in self._token_cache.items():
                base_symbol = pair_data.get("baseToken", {}).get("symbol", "")
                quote_symbol = pair_data.get("quoteToken", {}).get("symbol", "")
                if base_symbol and quote_symbol:
                    symbol = f"{base_symbol}/{quote_symbol}:{pair_addr}"
                    symbols.append(symbol)

            return symbols[:100]  # Limit results

        except Exception as e:
            raise DataSourceError(f"Failed to fetch available symbols: {str(e)}")

    def get_symbol_info(self, symbol: str) -> Dict[str, Any]:
        """Get detailed information about a token pair."""
        try:
            pair_data = self._find_pair_by_symbol(symbol)
            if not pair_data:
                raise SymbolNotFoundError(f"Token pair not found: {symbol}")

            base_token = pair_data.get("baseToken", {})
            quote_token = pair_data.get("quoteToken", {})

            return {
                "symbol": symbol,
                "name": (
                    f"{base_token.get('name', 'Unknown')} / "
                    f"{quote_token.get('name', 'Unknown')}"
                ),
                "market": "crypto",
                "currency": "USD",
                "min_order_size": 0.000001,  # Very small for crypto
                "max_order_size": None,
                "price_precision": 6,  # Most crypto pairs have 6+ decimal precision
                "size_precision": 8,
                "base_token_address": base_token.get("address"),
                "quote_token_address": quote_token.get("address"),
                "dex_id": pair_data.get("dexId"),
                "liquidity_usd": float(pair_data.get("liquidity", {}).get("usd", 0)),
                "fdv": float(pair_data.get("fdv", 0)),  # Fully diluted valuation
                "market_cap": float(pair_data.get("marketCap", 0)),
            }

        except SymbolNotFoundError:
            raise
        except Exception as e:
            raise DataSourceError(f"Failed to fetch symbol info for {symbol}: {str(e)}")

    def is_market_open(self, market: Optional[str] = None) -> bool:
        """Check if the crypto market is open (always true for DEX)."""
        # DEX markets are always open
        return True

    def get_trending_pairs(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get trending token pairs (Dexscreener-specific method)."""
        try:
            data = self._make_request("dex/tokens")  # type: ignore[no-any-return]
            pairs = data.get("pairs", [])[:limit]

            trending = []
            for pair in pairs:
                trending.append(
                    {
                        "symbol": (
                            f"{pair.get('baseToken', {}).get('symbol', '')}/"
                            f"{pair.get('quoteToken', {}).get('symbol', '')}:"
                            f"{pair.get('pairAddress', '')}"
                        ),
                        "price": float(pair.get("priceUsd", 0)),
                        "volume_24h": float(pair.get("volume", {}).get("h24", 0)),
                        "liquidity": float(pair.get("liquidity", {}).get("usd", 0)),
                        "price_change_24h": float(
                            pair.get("priceChange", {}).get("h24", 0)
                        ),
                        "dex": pair.get("dexId", ""),
                        "pair_address": pair.get("pairAddress", ""),
                    }
                )

            return trending

        except Exception as e:
            raise DataSourceError(f"Failed to fetch trending pairs: {str(e)}")

    def search_pairs(self, query: str) -> List[Dict[str, Any]]:
        """Search for token pairs by token symbol or name."""
        try:
            # type: ignore[no-any-return]
            data = self._make_request("dex/search", {"q": query})
            pairs = data.get("pairs", [])

            results = []
            for pair in pairs:
                results.append(
                    {
                        "symbol": (
                            f"{pair.get('baseToken', {}).get('symbol', '')}/"
                            f"{pair.get('quoteToken', {}).get('symbol', '')}:"
                            f"{pair.get('pairAddress', '')}"
                        ),
                        "price": float(pair.get("priceUsd", 0)),
                        "volume_24h": float(pair.get("volume", {}).get("h24", 0)),
                        "liquidity": float(pair.get("liquidity", {}).get("usd", 0)),
                        "dex": pair.get("dexId", ""),
                        "pair_address": pair.get("pairAddress", ""),
                    }
                )

            return results

        except Exception as e:
            raise DataSourceError(f"Failed to search pairs for '{query}': {str(e)}")
