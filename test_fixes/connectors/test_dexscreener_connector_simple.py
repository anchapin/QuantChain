"""Simple tests for DexScreener connector to improve coverage."""

from datetime import datetime
from unittest.mock import Mock, patch

import pytest

try:
    from quantchain.connectors.dexscreener_connector import DexScreenerDataConnector

    DEXSCREENER_AVAILABLE = True
except ImportError as e:
    DEXSCREENER_AVAILABLE = False
    print(f"Import error: {e}")

pytestmark = pytest.mark.skipif(
    not DEXSCREENER_AVAILABLE, reason="DexScreener connector not available"
)


class TestDexScreenerDataConnector:
    """Tests for DexScreener Data Connector."""

    @pytest.fixture
    def config(self):
        """Create test configuration."""
        return {
            "api_key": "test_key",
            "base_url": "https://api.dexscreener.com/latest/dex",
        }

    def test_connector_initialization(self, config):
        """Test connector initialization."""
        if DEXSCREENER_AVAILABLE:
            connector = DexScreenerDataConnector(config)
            assert connector is not None
            assert hasattr(connector, "config")

    def test_get_token_info(self, config):
        """Test getting token information."""
        if DEXSCREENER_AVAILABLE:
            connector = DexScreenerDataConnector(config)

            # Mock the actual API call
            with patch.object(connector, "_make_request") as mock_request:
                # Setup mock to return sample data
                mock_request.return_value = {
                    "pairs": [
                        {
                            "chainId": "ethereum",
                            "dexId": "uniswap",
                            "url": "https://www.uniswap.org",
                            "pairAddress": "0x123",
                            "baseToken": {
                                "address": "0x456",
                                "name": "Wrapped Ether",
                                "symbol": "WETH",
                            },
                            "quoteToken": {
                                "address": "0x789",
                                "name": "USD Coin",
                                "symbol": "USDC",
                            },
                        }
                    ]
                }

                # Call method
                result = connector.get_token_info("WETH", "ethereum")

                # Check result
                assert result is not None
                assert len(result) > 0
                assert result[0]["baseToken"]["symbol"] == "WETH"
                mock_request.assert_called_once()

    def test_get_token_price_history(self, config):
        """Test getting token price history."""
        if DEXSCREENER_AVAILABLE:
            connector = DexScreenerDataConnector(config)

            # Mock the actual API call
            with patch.object(connector, "_make_request") as mock_request:
                # Setup mock to return sample data
                mock_request.return_value = {
                    "prices": [
                        {"price": "3000.50", "timestamp": 1641024000},
                        {"price": "3050.75", "timestamp": 1641110400},
                        {"price": "3100.25", "timestamp": 1641196800},
                    ]
                }

                # Call method
                result = connector.get_token_price_history(
                    "0x123",
                    "ethereum",
                    start_date=datetime(2023, 1, 1),
                    end_date=datetime(2023, 1, 3),
                )

                # Check result
                assert result is not None
                assert len(result) > 0
                assert result[0]["price"] == "3000.50"
                mock_request.assert_called_once()

    def test_error_handling(self, config):
        """Test error handling."""
        if DEXSCREENER_AVAILABLE:
            connector = DexScreenerDataConnector(config)

            # Mock the actual API call to raise an exception
            with patch.object(connector, "_make_request") as mock_request:
                # Setup mock to raise an exception
                mock_request.side_effect = Exception("API error")

                # Check that method handles the error
                with pytest.raises(Exception):
                    connector.get_token_info("WETH", "ethereum")

    def test_search_pairs(self, config):
        """Test searching for token pairs."""
        if DEXSCREENER_AVAILABLE:
            connector = DexScreenerDataConnector(config)

            # Mock the actual API call
            with patch.object(connector, "_make_request") as mock_request:
                # Setup mock to return sample data
                mock_request.return_value = {
                    "pairs": [
                        {
                            "chainId": "ethereum",
                            "dexId": "uniswap",
                            "url": "https://www.uniswap.org",
                            "pairAddress": "0x123",
                            "baseToken": {
                                "address": "0x456",
                                "name": "Wrapped Ether",
                                "symbol": "WETH",
                            },
                            "quoteToken": {
                                "address": "0x789",
                                "name": "USD Coin",
                                "symbol": "USDC",
                            },
                        }
                    ]
                }

                # Call method
                result = connector.search_pairs("WETH", "ethereum")

                # Check result
                assert result is not None
                assert len(result) > 0
                mock_request.assert_called_once()
