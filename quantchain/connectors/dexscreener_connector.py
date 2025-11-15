"""Dexscreener data connector for QuantChain."""

import os
import time
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union, Any
from enum import Enum

from quantchain.core.exceptions import (
    AuthenticationError,
    DataSourceError,
    SymbolNotFoundError,
)


class DexscreenerDataConnector:
    """Connector for Dexscreener API."""

    def __init__(
        self,
        retry_count: int = 3,
        retry_delay: float = 1.0,
    ):
        """
        Initialize Dexscreener connector.

        Args:
            retry_count: Number of retries for failed requests
            retry_delay: Delay between retries in seconds
        """
        self.retry_count = retry_count
        self.retry_delay = retry_delay
        self.base_url = "https://api.dexscreener.com/latest/dex"

    def _make_request(self, endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Make a request to Dexscreener API with retry logic."""
        url = f"{self.base_url}/{endpoint}"

        for attempt in range(self.retry_count):
            try:
                response = requests.get(url, params=params)
                response.raise_for_status()
                return response.json()
            except Exception as e:
                if attempt == self.retry_count - 1:
                    raise DataSourceError(f"Failed to fetch data from Dexscreener: {str(e)}")
                time.sleep(self.retry_delay)

        return {}  # This line shouldn't be reached

    def get_token_info(self, address: str) -> Dict[str, Any]:
        """
        Get information about a token by its contract address.

        Args:
            address: Contract address of the token

        Returns:
            Dictionary with token information
        """
        return self._make_request("tokens", {"address": address})

    def get_token_price(self, address: str, chain_id: str = "ethereum") -> Dict[str, Any]:
        """
        Get current price of a token.

        Args:
            address: Contract address of the token
            chain_id: Blockchain ID (default: ethereum)

        Returns:
            Dictionary with price information
        """
        params = {"address": address}
        if chain_id:
            params["chainId"] = chain_id

        return self._make_request("token/price", params)

    def search_tokens(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search for tokens matching a query.

        Args:
            query: Search query string
            limit: Maximum number of results to return

        Returns:
            List of matching tokens
        """
        return self._make_request("tokens/search", {"q": query, "limit": limit})

    def get_pairs_for_token(self, address: str, chain_id: str = "ethereum") -> List[Dict[str, Any]]:
        """
        Get all trading pairs for a token.

        Args:
            address: Contract address of the token
            chain_id: Blockchain ID (default: ethereum)

        Returns:
            List of trading pairs
        """
        params = {"address": address}
        if chain_id:
            params["chainId"] = chain_id

        result = self._make_request("pairs", params)
        return result.get("pairs", [])

    def get_pair_info(self, chain_id: str, base_token_address: str, quote_token_address: str) -> Dict[str, Any]:
        """
        Get information about a specific trading pair.

        Args:
            chain_id: Blockchain ID
            base_token_address: Address of the base token
            quote_token_address: Address of the quote token

        Returns:
            Dictionary with pair information
        """
        return self._make_request(
            "pair",
            {"chainId": chain_id, "baseTokenAddress": base_token_address, "quoteTokenAddress": quote_token_address}
        )

    def get_historical_data(
        self,
        chain_id: str,
        base_token_address: str,
        quote_token_address: str,
        timeframe: str = "1h",
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Get historical price data for a trading pair.

        Args:
            chain_id: Blockchain ID
            base_token_address: Address of the base token
            quote_token_address: Address of the quote token
            timeframe: Timeframe for data (1m, 5m, 15m, 1h, 4h, 1d)
            limit: Maximum number of data points to return

        Returns:
            List of OHLCV data points
        """
        params = {
            "chainId": chain_id,
            "baseTokenAddress": base_token_address,
            "quoteTokenAddress": quote_token_address,
            "interval": timeframe,
            "limit": limit
        }

        result = self._make_request("candles", params)
        return result.get("candles", [])

    def get_new_token_pairs(
        self,
        chain_id: str = "ethereum",
        min_liquidity: Optional[float] = None,
        min_volume: Optional[float] = None,
        sort_by: str = "age",  # Options: age, liquidity, volume24h
        order: str = "desc",  # Options: asc, desc
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Get new token pairs based on criteria.

        Args:
            chain_id: Blockchain ID (default: ethereum)
            min_liquidity: Minimum liquidity threshold
            min_volume: Minimum 24h volume threshold
            sort_by: Field to sort by
            order: Sort order (asc/desc)
            limit: Maximum number of results

        Returns:
            List of new token pairs
        """
        params = {
            "chainId": chain_id,
            "sort": sort_by,
            "order": order,
            "limit": limit
        }

        if min_liquidity is not None:
            params["minLiquidity"] = min_liquidity
        if min_volume is not None:
            params["minVolume24h"] = min_volume

        result = self._make_request("tokens/new", params)
        return result.get("tokens", [])

    def get_trending_pairs(
        self,
        chain_id: str = "ethereum",
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Get currently trending token pairs.

        Args:
            chain_id: Blockchain ID (default: ethereum)
            limit: Maximum number of results

        Returns:
            List of trending token pairs
        """
        params = {
            "chainId": chain_id,
            "limit": limit
        }

        result = self._make_request("trending/pairs", params)
        return result.get("pairs", [])
