"""Comprehensive tests for Dexscreener data connector."""

from unittest.mock import Mock, patch

import pytest
import requests

from quantchain.connectors.dexscreener_connector import DexscreenerDataConnector
from quantchain.core.exceptions import DataSourceError


class TestDexscreenerDataConnector:
    """Test Dexscreener data connector functionality."""

    @pytest.fixture
    def connector(self):
        """Create a Dexscreener connector instance for testing."""
        return DexscreenerDataConnector(retry_count=2, retry_delay=0.1)

    @pytest.fixture
    def mock_response(self):
        """Create a mock API response."""
        return {
            "pairs": [
                {
                    "chainId": "ethereum",
                    "dexId": "uniswap",
                    "url": "https://example.com/pair/123",
                    "pairAddress": "0x1234567890123456789012345678901234567890",
                    "baseToken": {
                        "address": "0xabcdefabcdefabcdefabcdefabcdefabcdefabcd",
                        "name": "Test Token",
                        "symbol": "TEST",
                    },
                    "quoteToken": {
                        "address": "0x1111111111111111111111111111111111111111",
                        "name": "WETH",
                        "symbol": "WETH",
                    },
                    "priceNative": "0.001",
                    "priceUsd": "0.003",
                    "liquidity": {"usd": 1000000},
                }
            ]
        }

    @pytest.mark.unit
    def test_connector_init_default(self, connector):
        """Test connector initialization with default parameters."""
        assert connector.retry_count == 2
        assert connector.retry_delay == 0.1
        assert connector.base_url == "https://api.dexscreener.com/latest/dex"

    @pytest.mark.unit
    def test_connector_init_custom_params(self):
        """Test connector initialization with custom parameters."""
        connector = DexscreenerDataConnector(retry_count=5, retry_delay=2.0)
        assert connector.retry_count == 5
        assert connector.retry_delay == 2.0
        assert connector.base_url == "https://api.dexscreener.com/latest/dex"

    @pytest.mark.unit
    @patch("quantchain.connectors.dexscreener_connector.requests.get")
    def test_make_request_success(self, mock_get, connector):
        """Test successful API request."""
        mock_response = Mock()
        mock_response.json.return_value = {"success": True}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = connector._make_request("test", {"param": "value"})

        mock_get.assert_called_once_with(
            "https://api.dexscreener.com/latest/dex/test", params={"param": "value"}
        )
        assert result == {"success": True}

    @pytest.mark.unit
    @patch("quantchain.connectors.dexscreener_connector.requests.get")
    @patch("time.sleep")
    def test_make_request_retry_success(self, mock_sleep, mock_get, connector):
        """Test API request that succeeds on retry."""
        # First call fails, second succeeds
        mock_get.side_effect = [
            requests.exceptions.ConnectionError("Connection failed"),
            Mock(json=lambda: {"success": True}, raise_for_status=lambda: None),
        ]

        result = connector._make_request("test", {"param": "value"})

        assert mock_get.call_count == 2
        mock_sleep.assert_called_once_with(0.1)
        assert result == {"success": True}

    @pytest.mark.unit
    @patch("quantchain.connectors.dexscreener_connector.requests.get")
    @patch("time.sleep")
    def test_make_request_max_retries_exceeded(self, mock_sleep, mock_get, connector):
        """Test API request that fails after all retries."""
        mock_get.side_effect = requests.exceptions.ConnectionError("Connection failed")

        with pytest.raises(
            DataSourceError, match="Failed to fetch data from Dexscreener"
        ):
            connector._make_request("test", {"param": "value"})

        assert mock_get.call_count == 2
        assert mock_sleep.call_count == 1

    @pytest.mark.unit
    @patch("quantchain.connectors.dexscreener_connector.requests.get")
    def test_make_request_http_error(self, mock_get, connector):
        """Test API request that returns HTTP error."""
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(
            "404 Not Found"
        )
        mock_get.return_value = mock_response

        with pytest.raises(
            DataSourceError, match="Failed to fetch data from Dexscreener"
        ):
            connector._make_request("test", {"param": "value"})

    @pytest.mark.unit
    @patch("quantchain.connectors.dexscreener_connector.requests.get")
    def test_make_request_json_error(self, mock_get, connector):
        """Test API request that returns invalid JSON."""
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_get.return_value = mock_response

        with pytest.raises(
            DataSourceError, match="Failed to fetch data from Dexscreener"
        ):
            connector._make_request("test", {"param": "value"})

    @pytest.mark.unit
    @patch.object(DexscreenerDataConnector, "_make_request")
    def test_get_token_info(self, mock_request, connector):
        """Test getting token information."""
        mock_request.return_value = {
            "token": {"address": "0x123...", "name": "Test Token"}
        }

        result = connector.get_token_info("0x1234567890123456789012345678901234567890")

        mock_request.assert_called_once_with(
            "tokens", {"address": "0x1234567890123456789012345678901234567890"}
        )
        assert result == {"token": {"address": "0x123...", "name": "Test Token"}}

    @pytest.mark.unit
    @patch.object(DexscreenerDataConnector, "_make_request")
    def test_get_token_price_default_chain(self, mock_request, connector):
        """Test getting token price with default chain."""
        mock_request.return_value = {"price": {"usd": "1.23", "native": "0.0005"}}

        result = connector.get_token_price("0x1234567890123456789012345678901234567890")

        mock_request.assert_called_once_with(
            "token/price",
            {
                "address": "0x1234567890123456789012345678901234567890",
                "chainId": "ethereum",
            },
        )
        assert result == {"price": {"usd": "1.23", "native": "0.0005"}}

    @pytest.mark.unit
    @patch.object(DexscreenerDataConnector, "_make_request")
    def test_get_token_price_custom_chain(self, mock_request, connector):
        """Test getting token price with custom chain."""
        mock_request.return_value = {"price": {"usd": "1.23", "native": "0.0005"}}

        result = connector.get_token_price(
            "0x1234567890123456789012345678901234567890", "bsc"
        )

        mock_request.assert_called_once_with(
            "token/price",
            {"address": "0x1234567890123456789012345678901234567890", "chainId": "bsc"},
        )
        assert result == {"price": {"usd": "1.23", "native": "0.0005"}}

    @pytest.mark.unit
    @patch.object(DexscreenerDataConnector, "_make_request")
    def test_search_tokens(self, mock_request, connector):
        """Test searching for tokens."""
        mock_request.return_value = {
            "results": [{"name": "Test Token", "symbol": "TEST"}]
        }

        result = connector.search_tokens("Test", limit=5)

        mock_request.assert_called_once_with("tokens/search", {"q": "Test", "limit": 5})
        assert result == [{"name": "Test Token", "symbol": "TEST"}]

    @pytest.mark.unit
    @patch.object(DexscreenerDataConnector, "_make_request")
    def test_search_tokens_no_results(self, mock_request, connector):
        """Test searching for tokens with no results."""
        mock_request.return_value = {"results": []}

        result = connector.search_tokens("NonExistentToken")

        assert result == []

    @pytest.mark.unit
    @patch.object(DexscreenerDataConnector, "_make_request")
    def test_search_tokens_missing_results_key(self, mock_request, connector):
        """Test searching for tokens when results key is missing."""
        mock_request.return_value = {"error": "No results"}

        result = connector.search_tokens("Test")

        assert result == []

    @pytest.mark.unit
    @patch.object(DexscreenerDataConnector, "_make_request")
    def test_get_pairs_for_token(self, mock_request, connector):
        """Test getting pairs for a token."""
        mock_request.return_value = {
            "pairs": [{"pair": "TEST/ETH"}, {"pair": "TEST/USDT"}]
        }

        result = connector.get_pairs_for_token(
            "0x1234567890123456789012345678901234567890"
        )

        mock_request.assert_called_once_with(
            "pairs",
            {
                "address": "0x1234567890123456789012345678901234567890",
                "chainId": "ethereum",
            },
        )
        assert result == [{"pair": "TEST/ETH"}, {"pair": "TEST/USDT"}]

    @pytest.mark.unit
    @patch.object(DexscreenerDataConnector, "_make_request")
    def test_get_pairs_for_token_custom_chain(self, mock_request, connector):
        """Test getting pairs for a token with custom chain."""
        mock_request.return_value = {"pairs": [{"pair": "TEST/BNB"}]}

        result = connector.get_pairs_for_token(
            "0x1234567890123456789012345678901234567890", "bsc"
        )

        mock_request.assert_called_once_with(
            "pairs",
            {"address": "0x1234567890123456789012345678901234567890", "chainId": "bsc"},
        )
        assert result == [{"pair": "TEST/BNB"}]

    @pytest.mark.unit
    @patch.object(DexscreenerDataConnector, "_make_request")
    def test_get_pair_info(self, mock_request, connector):
        """Test getting specific pair information."""
        mock_request.return_value = {
            "pair": {"address": "0x123...", "liquidity": 1000000}
        }

        result = connector.get_pair_info(
            "ethereum",
            "0x1111111111111111111111111111111111111111",
            "0x2222222222222222222222222222222222222222",
        )

        mock_request.assert_called_once_with(
            "pair",
            {
                "chainId": "ethereum",
                "baseTokenAddress": "0x1111111111111111111111111111111111111111",
                "quoteTokenAddress": "0x2222222222222222222222222222222222222222",
            },
        )
        assert result == {"pair": {"address": "0x123...", "liquidity": 1000000}}

    @pytest.mark.unit
    @patch.object(DexscreenerDataConnector, "_make_request")
    def test_get_historical_data(self, mock_request, connector):
        """Test getting historical price data."""
        mock_request.return_value = {
            "candles": [
                {
                    "timestamp": 1640995200,
                    "open": 1.0,
                    "high": 1.1,
                    "low": 0.9,
                    "close": 1.05,
                    "volume": 1000000,
                },
                {
                    "timestamp": 1641081600,
                    "open": 1.05,
                    "high": 1.2,
                    "low": 1.0,
                    "close": 1.15,
                    "volume": 1200000,
                },
            ]
        }

        result = connector.get_historical_data(
            "ethereum",
            "0x1111111111111111111111111111111111111111",
            "0x2222222222222222222222222222222222222222",
            timeframe="1h",
            limit=50,
        )

        mock_request.assert_called_once_with(
            "candles",
            {
                "chainId": "ethereum",
                "baseTokenAddress": "0x1111111111111111111111111111111111111111",
                "quoteTokenAddress": "0x2222222222222222222222222222222222222222",
                "interval": "1h",
                "limit": 50,
            },
        )
        assert len(result) == 2
        assert result[0]["timestamp"] == 1640995200
        assert result[0]["open"] == 1.0

    @pytest.mark.unit
    @patch.object(DexscreenerDataConnector, "_make_request")
    def test_get_historical_data_defaults(self, mock_request, connector):
        """Test getting historical data with default parameters."""
        mock_request.return_value = {"candles": []}

        connector.get_historical_data(
            "ethereum",
            "0x1111111111111111111111111111111111111111",
            "0x2222222222222222222222222222222222222222",
        )

        # Check that default parameters were used
        mock_request.assert_called_once()
        args, kwargs = mock_request.call_args
        assert args[0] == "candles"
        params = args[1]  # Parameters are passed as positional argument
        assert params["interval"] == "1h"
        assert params["limit"] == 100

    @pytest.mark.unit
    @patch.object(DexscreenerDataConnector, "_make_request")
    def test_get_new_token_pairs_minimal(self, mock_request, connector):
        """Test getting new token pairs with minimal parameters."""
        mock_request.return_value = {
            "tokens": [
                {"address": "0x111...", "name": "New Token 1", "age": 3600},
                {"address": "0x222...", "name": "New Token 2", "age": 7200},
            ]
        }

        result = connector.get_new_token_pairs()

        mock_request.assert_called_once_with(
            "tokens/new",
            {"chainId": "ethereum", "sort": "age", "order": "desc", "limit": 100},
        )
        assert len(result) == 2
        assert result[0]["name"] == "New Token 1"

    @pytest.mark.unit
    @patch.object(DexscreenerDataConnector, "_make_request")
    def test_get_new_token_pairs_all_filters(self, mock_request, connector):
        """Test getting new token pairs with all filters."""
        mock_request.return_value = {"tokens": []}

        connector.get_new_token_pairs(
            chain_id="bsc",
            min_liquidity=50000.0,
            min_volume=100000.0,
            sort_by="volume",
            order="asc",
            limit=20,
        )

        mock_request.assert_called_once_with(
            "tokens/new",
            {
                "chainId": "bsc",
                "sort": "volume",
                "order": "asc",
                "limit": 20,
                "minLiquidity": 50000.0,
                "minVolume24h": 100000.0,
            },
        )

    @pytest.mark.unit
    @patch.object(DexscreenerDataConnector, "_make_request")
    def test_get_new_token_pairs_optional_filters(self, mock_request, connector):
        """Test getting new token pairs with only some optional filters."""
        mock_request.return_value = {"tokens": []}

        connector.get_new_token_pairs(min_liquidity=25000.0)

        mock_request.assert_called_once_with(
            "tokens/new",
            {
                "chainId": "ethereum",
                "sort": "age",
                "order": "desc",
                "limit": 100,
                "minLiquidity": 25000.0,
            },
        )

    @pytest.mark.unit
    @patch.object(DexscreenerDataConnector, "_make_request")
    def test_get_trending_pairs(self, mock_request, connector):
        """Test getting trending pairs."""
        mock_request.return_value = {
            "pairs": [
                {"address": "0x111...", "name": "Hot Pair 1", "volume24h": 5000000},
                {"address": "0x222...", "name": "Hot Pair 2", "volume24h": 3000000},
            ]
        }

        result = connector.get_trending_pairs("bsc", limit=25)

        mock_request.assert_called_once_with(
            "trending/pairs", {"chainId": "bsc", "limit": 25}
        )
        assert len(result) == 2
        assert result[0]["name"] == "Hot Pair 1"

    @pytest.mark.unit
    @patch.object(DexscreenerDataConnector, "_make_request")
    def test_get_trending_pairs_defaults(self, mock_request, connector):
        """Test getting trending pairs with default parameters."""
        mock_request.return_value = {"pairs": []}

        connector.get_trending_pairs()

        mock_request.assert_called_once_with(
            "trending/pairs", {"chainId": "ethereum", "limit": 100}
        )

    @pytest.mark.unit
    def test_api_endpoints_consistency(self, connector):
        """Test that all public methods use consistent endpoint patterns."""
        # This test ensures all methods follow the same URL building pattern
        base_url = connector.base_url

        # Test that _make_request properly builds URLs
        with patch.object(connector, "_make_request") as mock_request:
            mock_request.return_value = {}

            # Test a few methods to ensure consistent URL building
            connector.get_token_info("0x123")
            connector.get_token_price("0x123")
            connector.search_tokens("test")

            # All should call _make_request with proper endpoints
            assert mock_request.call_count == 3
            calls = [call[0][0] for call in mock_request.call_args_list]
            assert calls == ["tokens", "token/price", "tokens/search"]


class TestDexscreenerDataConnectorIntegration:
    """Integration tests for Dexscreener connector (if needed)."""

    @pytest.mark.unit
    @pytest.mark.slow
    def test_real_api_call_skip(self):
        """Integration test - skipped by default to avoid external API calls."""
        pytest.skip("Integration test - uncomment to test against real API")

        # Uncomment the following code to test against real API:
        # connector = DexscreenerDataConnector(retry_count=1, retry_delay=0.5)
        # try:
        #     result = connector.search_tokens("ETH", limit=1)
        #     assert isinstance(result, list)
        # except DataSourceError:
        #     pytest.skip("API unavailable")
