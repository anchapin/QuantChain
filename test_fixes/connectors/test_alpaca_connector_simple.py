"""Simple tests for Alpaca connector to improve coverage."""

from datetime import datetime
from unittest.mock import Mock, patch

import pytest

try:
    from quantchain.connectors.alpaca_connector import AlpacaDataConnector

    ALPACA_AVAILABLE = True
except ImportError as e:
    ALPACA_AVAILABLE = False
    print(f"Import error: {e}")

pytestmark = pytest.mark.skipif(
    not ALPACA_AVAILABLE, reason="Alpaca connector not available"
)


class TestAlpacaDataConnector:
    """Tests for Alpaca Data Connector."""

    @pytest.fixture
    def config(self):
        """Create test configuration."""
        return {
            "api_key": "test_key",
            "secret_key": "test_secret",
            "base_url": "https://paper-api.alpaca.markets",
        }

    def test_connector_initialization(self, config):
        """Test connector initialization."""
        if ALPACA_AVAILABLE:
            connector = AlpacaDataConnector(config)
            assert connector is not None
            assert hasattr(connector, "config")

    def test_get_historical_data(self, config):
        """Test historical data retrieval."""
        if ALPACA_AVAILABLE:
            connector = AlpacaDataConnector(config)

            # Mock the actual API call
            with patch.object(connector, "_make_request") as mock_request:
                # Setup mock to return sample data
                mock_request.return_value = {
                    "symbol": "AAPL",
                    "data": [
                        {
                            "t": "2023-01-01T16:00:00Z",
                            "o": 100.0,
                            "h": 105.0,
                            "l": 95.0,
                            "c": 102.0,
                            "v": 1000000,
                        }
                    ],
                }

                # Call the method
                data = connector.get_historical_data(
                    symbol="AAPL",
                    start_date=datetime(2023, 1, 1),
                    end_date=datetime(2023, 1, 2),
                )

                # Check the result
                assert data is not None
                assert len(data) > 0

    def test_get_market_data(self, config):
        """Test market data retrieval."""
        if ALPACA_AVAILABLE:
            connector = AlpacaDataConnector(config)

            # Mock the actual API call
            with patch.object(connector, "_make_request") as mock_request:
                # Setup mock to return sample data
                mock_request.return_value = {
                    "data": [
                        {
                            "symbol": "AAPL",
                            "name": "Apple Inc.",
                            "exchange": "NASDAQ",
                            "asset_class": "us_equity",
                        }
                    ]
                }

                # Call the method
                data = connector.get_market_data()

                # Check the result
                assert data is not None
                assert len(data) > 0

    def test_error_handling(self, config):
        """Test error handling."""
        if ALPACA_AVAILABLE:
            connector = AlpacaDataConnector(config)

            # Mock the actual API call to raise an exception
            with patch.object(connector, "_make_request") as mock_request:
                # Setup mock to raise an exception
                mock_request.side_effect = Exception("API error")

                # Check that the method handles the error
                with pytest.raises(Exception):
                    connector.get_historical_data(
                        symbol="AAPL",
                        start_date=datetime(2023, 1, 1),
                        end_date=datetime(2023, 1, 2),
                    )
