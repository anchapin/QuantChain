"""Dexscreener data connector for DEX token data."""

import requests
import pandas as pd
import logging
from typing import List, Dict, Optional, Any, cast
from datetime import datetime, timezone, timedelta
import time
from urllib.parse import urljoin

from .base_interface import DataFeedInterface
from ..core.exceptions import DataSourceError, SymbolNotFoundError
from ..core.retry import RetryHandler


class DexscreenerDataConnector(DataFeedInterface):
    """Dexscreener data connector for DEX token pairs.

    ⚠️ **IMPORTANT**: Dexscreener API provides only current/most recent market data.
    It does not support historical price data. For true historical analysis,
    consider integrating with additional data sources or using alternative providers.

    Features:
    - Real-time DEX token pair prices
    - 24-hour volume and liquidity data
    - Trending pairs discovery
    - Multi-chain DEX support (Uniswap, SushiSwap, etc.)
    - Symbol search functionality

    Supported timeframes are limited to: 1Min, 5Min, 15Min, 1H, 4H, 1D
    However, all timeframes return the same current data.
    """

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
                - symbol_limit: Maximum number of symbols to return in
                  get_available_symbols (default: 100)
        """
        super().__init__(api_key or "", api_secret=None, **kwargs)

        self.api_key = api_key
        self.timeout = kwargs.get("timeout", 30)
        self.max_retries = kwargs.get("max_retries", 3)
        self.symbol_limit = kwargs.get("symbol_limit", 100)
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
            result = response.json()
            return result  # type: ignore[no-any-return]

        result = self._retry_handler.execute(
            _request, exceptions=(requests.exceptions.RequestException,)
        )
        return result  # type: ignore[no-any-return]

    def _normalize_pair_address(self, symbol: str) -> str:
        """Extract pair address from symbol format like 'TOKEN/USD:ADDRESS'."""
        return symbol.split(":")[-1] if ":" in symbol else symbol

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
            if (pairs := data.get("pairs")) and pairs:
                # type: ignore[no-any-return]
                pair = pairs[0]
                self._token_cache[pair_address] = pair
                return cast(Optional[Dict[str, Any]], pair)
        except DataSourceError:
            pass

        # Search by token symbols if direct lookup fails
        try:
            self._refresh_token_cache()
            symbol_upper = symbol.upper()
            # Look for pairs containing the symbol
            for pair_data in self._token_cache.values():
                base_token = pair_data.get("baseToken", {}).get("symbol", "").upper()
                quote_token = pair_data.get("quoteToken", {}).get("symbol", "").upper()
                if (
                    symbol_upper in [base_token, quote_token]
                    or symbol_upper == f"{base_token}/{quote_token}"
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

        ⚠️ **IMPORTANT LIMITATION**: Dexscreener only provides current/most recent
        price data, not true historical data. This method returns current data
        formatted as a single-row DataFrame regardless of the requested time range.

        For historical analysis, consider using:
        - Time-weighted average price data from multiple snapshots
        - Integration with other historical data sources
        - Alternative DEX data providers with historical capabilities

        Args:
            symbol: Token pair symbol (e.g., 'WETH/USDC' or '0x123...')
            timeframe: Time interval (ignored, only current data returned)
            start_date: Start date for historical data (ignored)
            end_date: End date for historical data (optional, ignored)
            limit: Number of records to return (ignored, always returns 1)

        Returns:
            DataFrame with a single row containing current price data:
            - timestamp: Current UTC timestamp
            - open/high/low/close: Current price (all same value)
            - volume: 24-hour trading volume

        Raises:
            ValueError: If timeframe is not supported
            SymbolNotFoundError: If token pair is not found
            DataSourceError: If API request fails
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
            df = pd.DataFrame(
                [
                    {
                        "timestamp": timestamp,
                        "open": current_price,
                        "high": current_price,
                        "low": current_price,
                        "close": current_price,
                        "volume": volume_24h,
                    }
                ]
            )
            return df

        except SymbolNotFoundError:
            raise
        except Exception as e:
            raise DataSourceError(
                f"Failed to fetch historical data for {symbol}: {str(e)}"
            ) from e

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
            ) from e

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

    def get_available_symbols(
        self, market: Optional[str] = None, limit: Optional[int] = None
    ) -> List[str]:
        """Get list of available token pairs.

        Args:
            market: Optional market filter (ignored for Dexscreener)
            limit: Optional limit override (defaults to self.symbol_limit)

        Returns:
            List of available token pair symbols
        """
        try:
            self._refresh_token_cache()

            symbols = []
            for pair_addr, pair_data in self._token_cache.items():
                base_symbol = pair_data.get("baseToken", {}).get("symbol", "")
                quote_symbol = pair_data.get("quoteToken", {}).get("symbol", "")
                if base_symbol and quote_symbol:
                    symbol = f"{base_symbol}/{quote_symbol}:{pair_addr}"
                    symbols.append(symbol)

            # Use provided limit or default to symbol_limit
            result_limit = limit if limit is not None else self.symbol_limit
            return symbols[:result_limit]

        except Exception as e:
            raise DataSourceError(f"Failed to fetch available symbols: {str(e)}") from e

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
            raise DataSourceError(
                f"Failed to fetch symbol info for {symbol}: {str(e)}"
            ) from e

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
            raise DataSourceError(f"Failed to fetch trending pairs: {str(e)}") from e

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
            raise DataSourceError(
                f"Failed to search pairs for '{query}': {str(e)}"
            ) from e

    def get_new_token_pairs(self, time_window: str = "1h") -> List[Dict[str, Any]]:
        """Fetch newly created token pairs within the specified time window.

        Args:
            time_window: Time window to look back (e.g., '1h', '24h', '7d')

        Returns:
            List of new token pair dictionaries with basic metrics

        Raises:
            DataSourceError: If API request fails
        """
        try:
            # Convert time window to hours for filtering
            time_window_hours = self._parse_time_window(time_window)

            # Get trending pairs
            # (Dexscreener doesn't have a direct "new pairs" endpoint)
            # We'll use trending pairs and filter by creation time
            trending_pairs = self.get_trending_pairs(limit=200)

            new_pairs = []
            cutoff_time = datetime.now(timezone.utc) - timedelta(
                hours=time_window_hours
            )

            for pair in trending_pairs:
                # Extract pair address and get detailed info
                pair_address = pair.get("pair_address", "")
                if not pair_address:
                    continue

                try:
                    # Get detailed pair info
                    data = self._make_request(f"dex/pairs/{pair_address}")
                    if not data.get("pairs"):
                        continue

                    pair_detail = data["pairs"][0]

                    # Check if pair was created within time window
                    # Dexscreener doesn't provide creation timestamp,
                    # so we'll use a heuristic
                    # based on liquidity and volume patterns
                    # (new pairs typically have low liquidity initially)
                    liquidity = float(pair_detail.get("liquidity", {}).get("usd", 0))
                    volume_24h = float(pair_detail.get("volume", {}).get("h24", 0))

                    # Heuristic: Consider pairs "new" if they have low liquidity
                    # (< $50k) and reasonable volume (indicating recent activity)
                    if liquidity < 50000 and volume_24h > 1000:
                        base_token = pair_detail.get("baseToken", {})
                        quote_token = pair_detail.get("quoteToken", {})

                        new_pair = {
                            "address": pair_address,
                            "symbol": base_token.get("symbol", ""),
                            "name": base_token.get("name", ""),
                            "liquidity": liquidity,
                            "volume_24h": volume_24h,
                            "created_at": cutoff_time,  # Approximate creation time
                            "dex": pair_detail.get("dexId", ""),
                            "base_token_address": base_token.get("address", ""),
                            "quote_token_address": quote_token.get("address", ""),
                        }
                        new_pairs.append(new_pair)

                except Exception as e:
                    # Skip pairs that fail to load details
                    self.logger.debug(
                        f"Failed to get details for pair {pair_address}: {str(e)}"
                    )
                    continue

            # Sort by volume (most active first)
            new_pairs.sort(key=lambda x: x["volume_24h"], reverse=True)

            return new_pairs[:50]  # Return top 50 new pairs

        except Exception as e:
            raise DataSourceError(f"Failed to fetch new token pairs: {str(e)}") from e

    def _parse_time_window(self, time_window: str) -> float:
        """Parse time window string to hours.

        Args:
            time_window: Time window string (e.g., '1h', '24h', '7d')

        Returns:
            Time window in hours
        """
        if time_window.endswith("h"):
            return float(time_window[:-1])
        elif time_window.endswith("d"):
            return float(time_window[:-1]) * 24
        elif time_window.endswith("m"):
            return float(time_window[:-1]) * 24 * 30  # Approximate
        else:
            # Default to 1 hour
            return 1.0
