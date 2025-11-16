"""Comprehensive tests for Dexscreener data connector to improve test coverage."""

import json
import time
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock, Mock, patch

import pytest
import requests

from quantchain.connectors.dexscreener_connector import DexscreenerDataConnector
from quantchain.core.exceptions import (
    AuthenticationError,
    DataSourceError,
    SymbolNotFoundError,
)


@pytest.mark.unit
class TestDexscreenerDataConnector:
    """Test suite for DexscreenerDataConnector."""

    @pytest.fixture
    def connector(self) -> DexscreenerDataConnector:
        """Create a test connector instance."""
        return DexscreenerDataConnector()

    @pytest.fixture
    def sample_token_info(self) -> dict:
        """Sample token info from Dexscreener API."""
        return {
            "tokens": [
                {
                    "address": "0x1234567890abcdef",
                    "name": "Wrapped Ether",
                    "symbol": "WETH",
                    "decimals": 18,
                    "logoURI": "https://example.com/logo.png",
                }
            ]
        }

    @pytest.fixture
    def sample_pair_info(self) -> dict:
        """Sample pair info from Dexscreener API."""
        return {
            "pair": {
                "chainId": "ethereum",
                "dexId": "uniswap",
                "url": "https://uniswap.io/pairs/0x123",
                "pairAddress": "0x1234567890abcdef",
                "baseToken": {
                    "address": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
                    "name": "Wrapped Ether",
                    "symbol": "WETH",
                },
                "quoteToken": {
                    "address": "0xA0b86a33E6441e88C5F2712C3E9b74AeE3e6d6f5",
                    "name": "USD Coin",
                    "symbol": "USDC",
                },
                "priceNative": "0.0004",
                "priceUsd": "2500.50",
                "volume": {"h24": "1000000.0", "h6h": "500000.0", "h1h": "100000.0"},
                "liquidity": {
                    "usd": "5000000.0",
                    "base": "2000.0",
                    "quote": "5000000.0",
                },
                "fdv": "2500000000.0",
                "marketCap": "2400000000.0",
            }
        }

    @pytest.fixture
    def sample_historical_data(self) -> dict:
        """Sample historical data from Dexscreener API."""
        return {
            "candles": [
                {
                    "timestamp": "2024-01-01T00:00:00Z",
                    "open": "2500.0",
                    "high": "2550.0",
                    "low": "2480.0",
                    "close": "2520.0",
                    "volume": "100000.0",
                },
                {
                    "timestamp": "2024-01-01T01:00:00Z",
                    "open": "2520.0",
                    "high": "2580.0",
                    "low": "2500.0",
                    "close": "2560.0",
                    "volume": "120000.0",
                },
            ]
        }

    @pytest.fixture
    def sample_new_tokens(self) -> dict:
        """Sample new tokens from Dexscreener API."""
        return {
            "tokens": [
                {
                    "address": "0x1234567890abcdef",
                    "name": "Test Token",
                    "symbol": "TEST",
                    "pairAddress": "0xabcdef1234567890",
                    "baseToken": {"symbol": "TEST", "name": "Test Token"},
                    "quoteToken": {"symbol": "ETH", "name": "Ethereum"},
                    "priceUsd": "0.50",
                    "volume": {"h24": "100000.0"},
                    "liquidity": {"usd": "500000.0"},
                    "createdAt": "2024-01-01T00:00:00Z",
                }
            ]
        }

    @pytest.fixture
    def sample_trending_pairs(self) -> dict:
        """Sample trending pairs from Dexscreener API."""
        return {
            "pairs": [
                {
                    "chainId": "ethereum",
                    "dexId": "uniswap",
                    "pairAddress": "0x1234567890abcdef",
                    "baseToken": {"symbol": "WETH", "name": "Wrapped Ether"},
                    "quoteToken": {"symbol": "USDC", "name": "USD Coin"},
                    "priceUsd": "2500.50",
                    "volume": {"h24": "1000000.0"},
                    "liquidity": {"usd": "5000000.0"},
                }
            ]
        }

    def test_initialization(self, connector: DexscreenerDataConnector) -> None:
        """Test successful initialization."""
        assert connector.retry_count == 3
        assert connector.retry_delay == 1.0
        assert connector.base_url == "https://api.dexscreener.com/latest/dex"

    def test_custom_initialization_params(self) -> None:
        """Test custom initialization parameters."""
        connector = DexscreenerDataConnector(retry_count=5, retry_delay=2.0)
        assert connector.retry_count == 5
        assert connector.retry_delay == 2.0

    @patch("quantchain.connectors.dexscreener_connector.requests.get")
    def test_make_request_success(
        self, mock_get, connector: DexscreenerDataConnector
    ) -> None:
        """Test successful API request."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"data": "test"}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = connector._make_request("test/endpoint", {"param": "value"})

        assert result == {"data": "test"}
        mock_get.assert_called_once_with(
            "https://api.dexscreener.com/latest/dex/test/endpoint",
            params={"param": "value"},
        )

    @patch("quantchain.connectors.dexscreener_connector.requests.get")
    @patch("time.sleep")
    def test_make_request_retry_on_failure(
        self, mock_sleep, mock_get, connector: DexscreenerDataConnector
    ) -> None:
        """Test request retry on failure."""
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = (
            requests.exceptions.RequestException("Network error")
        )
        mock_get.return_value = mock_response

        with pytest.raises(
            DataSourceError, match="Failed to fetch data from Dexscreener"
        ):
            connector._make_request("test/endpoint", {})

        # Should have attempted 3 times
        assert mock_get.call_count == 3
        # Should have slept twice between retries
        assert mock_sleep.call_count == 2

    @patch("quantchain.connectors.dexscreener_connector.requests.get")
    def test_get_token_info(
        self, mock_get, connector: DexscreenerDataConnector, sample_token_info: dict
    ) -> None:
        """Test get_token_info method."""
        mock_response = MagicMock()
        mock_response.json.return_value = sample_token_info
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = connector.get_token_info("0x1234567890abcdef")

        assert result == sample_token_info
        mock_get.assert_called_once_with(
            "https://api.dexscreener.com/latest/dex/tokens",
            params={"address": "0x1234567890abcdef"},
        )

    @patch("quantchain.connectors.dexscreener_connector.requests.get")
    def test_get_token_price_with_chain_id(
        self, mock_get, connector: DexscreenerDataConnector
    ) -> None:
        """Test get_token_price with chain_id parameter."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"price": "2500.50"}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = connector.get_token_price("0x1234567890abcdef", chain_id="ethereum")

        assert result == {"price": "2500.50"}
        mock_get.assert_called_once_with(
            "https://api.dexscreener.com/latest/dex/token/price",
            params={"address": "0x1234567890abcdef", "chainId": "ethereum"},
        )

    @patch("quantchain.connectors.dexscreener_connector.requests.get")
    def test_get_token_price_without_chain_id(
        self, mock_get, connector: DexscreenerDataConnector
    ) -> None:
        """Test get_token_price without chain_id parameter."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"price": "2500.50"}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = connector.get_token_price("0x1234567890abcdef")

        assert result == {"price": "2500.50"}
        mock_get.assert_called_once_with(
            "https://api.dexscreener.com/latest/dex/token/price",
            params={"address": "0x1234567890abcdef", "chainId": "ethereum"},
        )

    @patch("quantchain.connectors.dexscreener_connector.requests.get")
    def test_search_tokens(self, mock_get, connector: DexscreenerDataConnector) -> None:
        """Test searching tokens."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "tokens": [{"symbol": "WETH"}, {"symbol": "WBTC"}]
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = connector.search_tokens("ETH", limit=10)

        # search_tokens returns the entire response from the API
        # In our mock, this is the entire response dict
        assert result == {"tokens": [{"symbol": "WETH"}, {"symbol": "WBTC"}]}
        mock_get.assert_called_once_with(
            "https://api.dexscreener.com/latest/dex/tokens/search",
            params={"q": "ETH", "limit": 10},
        )

    @patch("quantchain.connectors.dexscreener_connector.requests.get")
    def test_get_pairs_for_token(
        self, mock_get, connector: DexscreenerDataConnector
    ) -> None:
        """Test get_pairs_for_token method."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "pairs": [{"pairAddress": "0x123"}, {"pairAddress": "0x456"}]
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = connector.get_pairs_for_token(
            "0x1234567890abcdef", chain_id="ethereum"
        )

        assert result == [{"pairAddress": "0x123"}, {"pairAddress": "0x456"}]
        mock_get.assert_called_once_with(
            "https://api.dexscreener.com/latest/dex/pairs",
            params={"address": "0x1234567890abcdef", "chainId": "ethereum"},
        )

    @patch("quantchain.connectors.dexscreener_connector.requests.get")
    def test_get_pair_info(
        self, mock_get, connector: DexscreenerDataConnector, sample_pair_info: dict
    ) -> None:
        """Test get_pair_info method."""
        mock_response = MagicMock()
        mock_response.json.return_value = sample_pair_info
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = connector.get_pair_info("ethereum", "0x123", "0x456")

        assert result == sample_pair_info
        mock_get.assert_called_once_with(
            "https://api.dexscreener.com/latest/dex/pair",
            params={
                "chainId": "ethereum",
                "baseTokenAddress": "0x123",
                "quoteTokenAddress": "0x456",
            },
        )

    @patch("quantchain.connectors.dexscreener_connector.requests.get")
    def test_get_historical_data(
        self,
        mock_get,
        connector: DexscreenerDataConnector,
        sample_historical_data: dict,
    ) -> None:
        """Test get_historical_data method."""
        mock_response = MagicMock()
        mock_response.json.return_value = sample_historical_data
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = connector.get_historical_data(
            "ethereum", "0x123", "0x456", timeframe="1h", limit=100
        )

        assert result == [
            {
                "timestamp": "2024-01-01T00:00:00Z",
                "open": "2500.0",
                "high": "2550.0",
                "low": "2480.0",
                "close": "2520.0",
                "volume": "100000.0",
            },
            {
                "timestamp": "2024-01-01T01:00:00Z",
                "open": "2520.0",
                "high": "2580.0",
                "low": "2500.0",
                "close": "2560.0",
                "volume": "120000.0",
            },
        ]
        mock_get.assert_called_once_with(
            "https://api.dexscreener.com/latest/dex/candles",
            params={
                "chainId": "ethereum",
                "baseTokenAddress": "0x123",
                "quoteTokenAddress": "0x456",
                "interval": "1h",
                "limit": 100,
            },
        )

    @patch("quantchain.connectors.dexscreener_connector.requests.get")
    def test_get_historical_data_empty_response(
        self, mock_get, connector: DexscreenerDataConnector
    ) -> None:
        """Test get_historical_data with empty response."""
        mock_response = MagicMock()
        mock_response.json.return_value = {}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = connector.get_historical_data("ethereum", "0x123", "0x456")

        assert result == []
        mock_get.assert_called_once_with(
            "https://api.dexscreener.com/latest/dex/candles",
            params={
                "chainId": "ethereum",
                "baseTokenAddress": "0x123",
                "quoteTokenAddress": "0x456",
                "interval": "1h",
                "limit": 100,
            },
        )

    @patch("quantchain.connectors.dexscreener_connector.requests.get")
    def test_get_new_token_pairs_with_filters(
        self, mock_get, connector: DexscreenerDataConnector, sample_new_tokens: dict
    ) -> None:
        """Test get_new_token_pairs with filters."""
        mock_response = MagicMock()
        mock_response.json.return_value = sample_new_tokens
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = connector.get_new_token_pairs(
            chain_id="ethereum",
            min_liquidity=100000.0,
            min_volume=50000.0,
            sort_by="volume",
            order="desc",
            limit=50,
        )

        assert result == [
            {
                "address": "0x1234567890abcdef",
                "name": "Test Token",
                "symbol": "TEST",
                "pairAddress": "0xabcdef1234567890",
                "baseToken": {"symbol": "TEST", "name": "Test Token"},
                "quoteToken": {"symbol": "ETH", "name": "Ethereum"},
                "priceUsd": "0.50",
                "volume": {"h24": "100000.0"},
                "liquidity": {"usd": "500000.0"},
                "createdAt": "2024-01-01T00:00:00Z",
            }
        ]
        mock_get.assert_called_once_with(
            "https://api.dexscreener.com/latest/dex/tokens/new",
            params={
                "chainId": "ethereum",
                "sort": "volume",
                "order": "desc",
                "limit": 50,
                "minLiquidity": 100000.0,
                "minVolume24h": 50000.0,
            },
        )

    @patch("quantchain.connectors.dexscreener_connector.requests.get")
    def test_get_new_token_pairs_without_filters(
        self, mock_get, connector: DexscreenerDataConnector
    ) -> None:
        """Test get_new_token_pairs without filters."""
        mock_response = MagicMock()
        mock_response.json.return_value = {}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = connector.get_new_token_pairs()

        assert result == []
        mock_get.assert_called_once_with(
            "https://api.dexscreener.com/latest/dex/tokens/new",
            params={
                "chainId": "ethereum",
                "sort": "age",
                "order": "desc",
                "limit": 100,
            },
        )

    @patch("quantchain.connectors.dexscreener_connector.requests.get")
    def test_get_new_token_pairs_empty_response(
        self, mock_get, connector: DexscreenerDataConnector
    ) -> None:
        """Test get_new_token_pairs with empty response."""
        mock_response = MagicMock()
        mock_response.json.return_value = {}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = connector.get_new_token_pairs()

        assert result == []

    @patch("quantchain.connectors.dexscreener_connector.requests.get")
    def test_get_trending_pairs(
        self, mock_get, connector: DexscreenerDataConnector, sample_trending_pairs: dict
    ) -> None:
        """Test get_trending_pairs method."""
        mock_response = MagicMock()
        mock_response.json.return_value = sample_trending_pairs
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = connector.get_trending_pairs(chain_id="ethereum", limit=50)

        assert result == [
            {
                "chainId": "ethereum",
                "dexId": "uniswap",
                "pairAddress": "0x1234567890abcdef",
                "baseToken": {"symbol": "WETH", "name": "Wrapped Ether"},
                "quoteToken": {"symbol": "USDC", "name": "USD Coin"},
                "priceUsd": "2500.50",
                "volume": {"h24": "1000000.0"},
                "liquidity": {"usd": "5000000.0"},
            }
        ]
        mock_get.assert_called_once_with(
            "https://api.dexscreener.com/latest/dex/trending/pairs",
            params={"chainId": "ethereum", "limit": 50},
        )

    @patch("quantchain.connectors.dexscreener_connector.requests.get")
    def test_get_trending_pairs_empty_response(
        self, mock_get, connector: DexscreenerDataConnector
    ) -> None:
        """Test get_trending_pairs with empty response."""
        mock_response = MagicMock()
        mock_response.json.return_value = {}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = connector.get_trending_pairs()

        assert result == []

    @patch("quantchain.connectors.dexscreener_connector.requests.get")
    def test_get_trending_pairs_zero_limit(
        self, mock_get, connector: DexscreenerDataConnector
    ) -> None:
        """Test get_trending_pairs with zero limit."""
        mock_response = MagicMock()
        mock_response.json.return_value = {}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = connector.get_trending_pairs(limit=0)

        assert result == []

    def test_different_timeframes(self, connector: DexscreenerDataConnector) -> None:
        """Test that different timeframes are accepted."""
        with patch.object(connector, "_make_request") as mock_request:
            mock_request.return_value = {"candles": []}

            # Test valid timeframes
            for timeframe in ["1m", "5m", "15m", "1h", "4h", "1d"]:
                connector.get_historical_data(
                    "ethereum", "0x123", "0x456", timeframe=timeframe
                )
                mock_request.assert_called()
                args, kwargs = mock_request.call_args
                assert args[0] == "candles"
                assert args[1]["interval"] == timeframe

    def test_different_sort_options(self, connector: DexscreenerDataConnector) -> None:
        """Test that different sort options are accepted."""
        with patch.object(connector, "_make_request") as mock_request:
            mock_request.return_value = {"tokens": []}

            # Test valid sort options
            for sort_by in ["age", "liquidity", "volume24h"]:
                connector.get_new_token_pairs(sort_by=sort_by)
                mock_request.assert_called()
                args, kwargs = mock_request.call_args
                assert args[0] == "tokens/new"
                assert args[1]["sort"] == sort_by

    def test_different_order_options(self, connector: DexscreenerDataConnector) -> None:
        """Test that different order options are accepted."""
        with patch.object(connector, "_make_request") as mock_request:
            mock_request.return_value = {"tokens": []}

            # Test valid order options
            for order in ["asc", "desc"]:
                connector.get_new_token_pairs(order=order)
                mock_request.assert_called()
                args, kwargs = mock_request.call_args
                assert args[0] == "tokens/new"
                assert args[1]["order"] == order

    @patch("quantchain.connectors.dexscreener_connector.requests.get")
    def test_request_exception_handling(
        self, mock_get, connector: DexscreenerDataConnector
    ) -> None:
        """Test that request exceptions are properly handled."""
        mock_get.side_effect = requests.exceptions.ConnectionError("Connection failed")

        with pytest.raises(
            DataSourceError, match="Failed to fetch data from Dexscreener"
        ):
            connector.get_token_info("0x123")

    @patch("quantchain.connectors.dexscreener_connector.requests.get")
    def test_json_exception_handling(
        self, mock_get, connector: DexscreenerDataConnector
    ) -> None:
        """Test that JSON exceptions are properly handled."""
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)
        mock_get.return_value = mock_response

        with pytest.raises(
            DataSourceError, match="Failed to fetch data from Dexscreener"
        ):
            connector.get_token_info("0x123")

    def test_empty_string_parameters(self, connector: DexscreenerDataConnector) -> None:
        """Test behavior with empty string parameters."""
        with patch.object(connector, "_make_request") as mock_request:
            mock_request.return_value = {"tokens": []}

            # Empty address should still make a request
            connector.get_token_info("")
            mock_request.assert_called()
            args, kwargs = mock_request.call_args
            assert args[0] == "tokens"
            assert args[1]["address"] == ""

            # Empty query should still make a request
            connector.search_tokens("")
            mock_request.assert_called()
            args, kwargs = mock_request.call_args
            assert args[0] == "tokens/search"
            assert args[1]["q"] == ""

    def test_negative_parameters(self, connector: DexscreenerDataConnector) -> None:
        """Test behavior with negative parameters."""
        with patch.object(connector, "_make_request") as mock_request:
            mock_request.return_value = {"tokens": []}

            # Negative limit should still be passed to the API
            connector.get_new_token_pairs(limit=-1)
            mock_request.assert_called()
            args, kwargs = mock_request.call_args
            assert args[0] == "tokens/new"
            assert args[1]["limit"] == -1

            # Negative liquidity threshold should still be passed
            connector.get_new_token_pairs(min_liquidity=-1000.0)
            mock_request.assert_called()
            args, kwargs = mock_request.call_args
            assert args[0] == "tokens/new"
            assert args[1]["minLiquidity"] == -1000.0

            # Negative volume threshold should still be passed
            connector.get_new_token_pairs(min_volume=-2000.0)
            mock_request.assert_called()
            args, kwargs = mock_request.call_args
            assert args[0] == "tokens/new"
            assert args[1]["minVolume24h"] == -2000.0

    @patch("quantchain.connectors.dexscreener_connector.requests.get")
    def test_large_number_of_requests(
        self, mock_get, connector: DexscreenerDataConnector
    ) -> None:
        """Test handling of a large number of requests."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "tokens": [{"symbol": f"TOKEN{i}"} for i in range(1000)]
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        # Request a large number of tokens
        result = connector.search_tokens("ETH", limit=1000)

        # The mock data returns 1000 tokens as specified in the mock
        assert len(result["tokens"]) == 1000
        mock_get.assert_called_once_with(
            "https://api.dexscreener.com/latest/dex/tokens/search",
            params={"q": "ETH", "limit": 1000},
        )

    @patch("quantchain.connectors.dexscreener_connector.requests.get")
    def test_special_characters_in_address(
        self, mock_get, connector: DexscreenerDataConnector
    ) -> None:
        """Test handling of special characters in token addresses."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"price": "2500.50"}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        # Address with special characters should be properly encoded
        connector.get_token_price("0x123+special&address")
        mock_get.assert_called_once()
        args, kwargs = mock_get.call_args
        assert args[0] == "https://api.dexscreener.com/latest/dex/token/price"
        assert kwargs["params"]["address"] == "0x123+special&address"

    def test_none_parameters(self, connector: DexscreenerDataConnector) -> None:
        """Test behavior with None parameters."""
        with patch.object(connector, "_make_request") as mock_request:
            mock_request.return_value = {"tokens": []}

            # None chain_id should be excluded from params
            connector.get_token_price("0x123", chain_id=None)
            mock_request.assert_called()
            args, kwargs = mock_request.call_args
            assert args[0] == "token/price"
            assert args[1]["address"] == "0x123"
            assert "chainId" not in args[1]

            # None liquidity threshold should be excluded
            connector.get_new_token_pairs(min_liquidity=None)
            mock_request.assert_called()
            args, kwargs = mock_request.call_args
            assert args[0] == "tokens/new"
            assert "minLiquidity" not in args[1]

            # None volume threshold should be excluded
            connector.get_new_token_pairs(min_volume=None)
            mock_request.assert_called()
            args, kwargs = mock_request.call_args
            assert args[0] == "tokens/new"
            assert "minVolume24h" not in args[1]
