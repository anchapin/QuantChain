"""Tests for Dexscreener data connector."""

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone
import pandas as pd
import requests

from quantchain.connectors.dexscreener_connector import DexscreenerDataConnector
from quantchain.core.exceptions import DataSourceError, SymbolNotFoundError


class TestDexscreenerDataConnector:
    """Test suite for DexscreenerDataConnector."""

    @pytest.fixture
    def connector(self) -> None:
        """Create a test connector instance."""
        return DexscreenerDataConnector()

    @pytest.fixture
    def sample_pair_data(self) -> None:
        """Sample pair data from Dexscreener API."""
        return {
            "pairAddress": "0x1234567890abcdef",
            "baseToken": {
                "symbol": "WETH",
                "name": "Wrapped Ether",
                "address": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
            },
            "quoteToken": {
                "symbol": "USDC",
                "name": "USD Coin",
                "address": "0xA0b86a33E6441e88C5F2712C3E9b74AeE3e6d6f5",
            },
            "priceUsd": "2500.50",
            "volume": {"h24": "1000000.0"},
            "liquidity": {"usd": "5000000.0"},
            "fdv": "2500000000.0",
            "marketCap": "2400000000.0",
            "dexId": "uniswap",
        }

    def test_initialization(self, connector: DexscreenerDataConnector) -> None:
        """Test successful initialization."""
        assert connector.api_key is None
        assert connector.timeout == 30
        assert connector.max_retries == 3

    def test_make_request_success(self, connector: DexscreenerDataConnector) -> None:
        """Test successful API request."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"pairs": []}

        with patch.object(
            connector.session, "get", return_value=mock_response
        ) as mock_get:
            result = connector._make_request("dex/tokens")

            mock_get.assert_called_once()
            assert result == {"pairs": []}

    def test_make_request_retry_on_failure(
        self, connector: DexscreenerDataConnector
    ) -> None:
        """Test request retry on failure."""
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = (
            requests.exceptions.RequestException("Network error")
        )

        with patch.object(connector.session, "get", return_value=mock_response):
            with pytest.raises(DataSourceError):
                connector._make_request("dex/tokens")

    def test_normalize_pair_address(self, connector: DexscreenerDataConnector) -> None:
        """Test pair address normalization."""
        assert connector._normalize_pair_address("WETH/USDC:0x123") == "0x123"
        assert connector._normalize_pair_address("0x123") == "0x123"

    def test_find_pair_by_symbol_direct_address(
        self, connector: DexscreenerDataConnector, sample_pair_data
    ) -> None:
        """Test finding pair by direct address."""
        connector._token_cache = {"0x1234567890abcdef": sample_pair_data}

        result = connector._find_pair_by_symbol("0x1234567890abcdef")
        assert result == sample_pair_data

    def test_find_pair_by_symbol_api_lookup(
        self, connector: DexscreenerDataConnector, sample_pair_data
    ) -> None:
        """Test finding pair via API lookup."""
        with patch.object(connector, "_make_request") as mock_request:
            mock_request.return_value = {"pairs": [sample_pair_data]}

            result = connector._find_pair_by_symbol("0x1234567890abcdef")

            assert result == sample_pair_data
            mock_request.assert_called_with("dex/pairs/0x1234567890abcdef")

    def test_find_pair_by_symbol_not_found(
        self, connector: DexscreenerDataConnector
    ) -> None:
        """Test pair not found."""
        with patch.object(
            connector, "_make_request", side_effect=DataSourceError("Not found")
        ):
            result = connector._find_pair_by_symbol("INVALID")
            assert result is None

    def test_get_historical_data(
        self, connector: DexscreenerDataConnector, sample_pair_data
    ) -> None:
        """Test historical data retrieval (returns current data)."""
        start_date = datetime(2024, 1, 1, tzinfo=timezone.utc)

        with patch.object(
            connector, "_find_pair_by_symbol", return_value=sample_pair_data
        ):
            df = connector.get_historical_data("WETH/USDC", "1D", start_date)

            assert isinstance(df, pd.DataFrame)
            assert len(df) == 1
            assert df.iloc[0]["close"] == 2500.50
            assert df.iloc[0]["volume"] == 1000000.0

    def test_get_historical_data_invalid_timeframe(
        self, connector: DexscreenerDataConnector
    ) -> None:
        """Test historical data with invalid timeframe."""
        start_date = datetime(2024, 1, 1, tzinfo=timezone.utc)

        with pytest.raises(ValueError):
            connector.get_historical_data("WETH/USDC", "1Y", start_date)

    def test_get_historical_data_symbol_not_found(
        self, connector: DexscreenerDataConnector
    ) -> None:
        """Test historical data for non-existent symbol."""
        start_date = datetime(2024, 1, 1, tzinfo=timezone.utc)

        with patch.object(connector, "_find_pair_by_symbol", return_value=None):
            with pytest.raises(SymbolNotFoundError):
                connector.get_historical_data("INVALID", "1D", start_date)

    def test_get_real_time_data(
        self, connector: DexscreenerDataConnector, sample_pair_data
    ) -> None:
        """Test real-time data retrieval."""
        with patch.object(
            connector, "_find_pair_by_symbol", return_value=sample_pair_data
        ):
            data = connector.get_real_time_data("WETH/USDC")

            assert data["price"] == 2500.50
            assert data["bid"] == 2500.50  # Dexscreener doesn't provide bid/ask
            assert data["ask"] == 2500.50
            assert data["volume"] == 1000000.0
            assert isinstance(data["timestamp"], datetime)

    def test_get_real_time_data_symbol_not_found(
        self, connector: DexscreenerDataConnector, sample_pair_data
    ) -> None:
        """Test real-time data for non-existent symbol."""
        with patch.object(connector, "_find_pair_by_symbol", return_value=None):
            with pytest.raises(SymbolNotFoundError):
                connector.get_real_time_data("INVALID")

    def test_get_quote(
        self, connector: DexscreenerDataConnector, sample_pair_data
    ) -> None:
        """Test quote retrieval."""
        with patch.object(
            connector, "_find_pair_by_symbol", return_value=sample_pair_data
        ):
            quote = connector.get_quote("WETH/USDC")

            assert quote["symbol"] == "WETH/USDC"
            assert quote["bid_price"] == 2500.50
            assert quote["ask_price"] == 2500.50
            assert quote["last_price"] == 2500.50
            assert quote["last_size"] == 1000000.0

    def test_get_available_symbols(
        self, connector: DexscreenerDataConnector, sample_pair_data
    ) -> None:
        """Test getting available symbols."""
        connector._token_cache = {"0x123": sample_pair_data}

        symbols = connector.get_available_symbols()

        assert len(symbols) == 1
        assert "WETH/USDC:0x123" in symbols

    def test_get_symbol_info(
        self, connector: DexscreenerDataConnector, sample_pair_data
    ) -> None:
        """Test getting symbol information."""
        with patch.object(
            connector, "_find_pair_by_symbol", return_value=sample_pair_data
        ):
            info = connector.get_symbol_info("WETH/USDC")

            assert info["symbol"] == "WETH/USDC"
            assert info["name"] == "Wrapped Ether / USD Coin"
            assert info["market"] == "crypto"
            assert info["currency"] == "USD"
            assert info["price_precision"] == 6
            assert info["size_precision"] == 8
            assert info["liquidity_usd"] == 5000000.0
            assert info["fdv"] == 2500000000.0

    def test_get_symbol_info_not_found(
        self, connector: DexscreenerDataConnector
    ) -> None:
        """Test symbol info for non-existent symbol."""
        with patch.object(connector, "_find_pair_by_symbol", return_value=None):
            with pytest.raises(SymbolNotFoundError):
                connector.get_symbol_info("INVALID")

    def test_is_market_open(self, connector: DexscreenerDataConnector) -> None:
        """Test market open check (always true for DEX)."""
        assert connector.is_market_open() is True
        assert connector.is_market_open("crypto") is True

    def test_get_trending_pairs(self, connector: DexscreenerDataConnector) -> None:
        """Test getting trending pairs."""
        mock_pairs = [
            {
                "pairAddress": "0x123",
                "baseToken": {"symbol": "WETH"},
                "quoteToken": {"symbol": "USDC"},
                "priceUsd": "2500.0",
                "volume": {"h24": "1000000.0"},
                "liquidity": {"usd": "5000000.0"},
                "dexId": "uniswap",
            }
        ]

        with patch.object(connector, "_make_request") as mock_request:
            mock_request.return_value = {"pairs": mock_pairs}

            trending = connector.get_trending_pairs(limit=1)

            assert len(trending) == 1
            assert trending[0]["symbol"] == "WETH/USDC:0x123"
            assert trending[0]["price"] == 2500.0
            assert trending[0]["volume_24h"] == 1000000.0

    def test_search_pairs(self, connector: DexscreenerDataConnector) -> None:
        """Test pair search functionality."""
        mock_pairs = [
            {
                "pairAddress": "0x123",
                "baseToken": {"symbol": "WETH"},
                "quoteToken": {"symbol": "USDC"},
                "priceUsd": "2500.0",
                "volume": {"h24": "1000000.0"},
                "liquidity": {"usd": "5000000.0"},
                "dexId": "uniswap",
            }
        ]

        with patch.object(connector, "_make_request") as mock_request:
            mock_request.return_value = {"pairs": mock_pairs}

            results = connector.search_pairs("WETH")

            assert len(results) == 1
            assert results[0]["symbol"] == "WETH/USDC:0x123"
            assert results[0]["price"] == 2500.0

    def test_refresh_token_cache(self, connector: DexscreenerDataConnector) -> None:
        """Test token cache refresh."""
        mock_pairs = [
            {
                "pairAddress": "0x123",
                "baseToken": {"symbol": "WETH"},
                "quoteToken": {"symbol": "USDC"},
                "priceUsd": "2500.0",
            }
        ]

        with patch.object(connector, "_make_request") as mock_request:
            mock_request.return_value = {"pairs": mock_pairs}

            connector._refresh_token_cache()

            assert "0x123" in connector._token_cache
            assert connector._token_cache["0x123"]["priceUsd"] == "2500.0"

    def test_refresh_token_cache_error_handling(
        self, connector: DexscreenerDataConnector
    ) -> None:
        """Test token cache refresh error handling."""
        with patch.object(
            connector, "_make_request", side_effect=Exception("API Error")
        ):
            # Should not raise exception, just log warning
            connector._refresh_token_cache()

            # Cache should remain empty or unchanged
            assert isinstance(connector._token_cache, dict)

    def test_custom_initialization_params(self) -> None:
        """Test custom initialization parameters."""
        connector = DexscreenerDataConnector(timeout=60, max_retries=5)

        assert connector.timeout == 60
        assert connector.max_retries == 5
