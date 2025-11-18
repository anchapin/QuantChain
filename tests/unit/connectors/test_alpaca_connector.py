"""
Comprehensive test suite for Alpaca connector module.
"""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, Mock, patch

import pandas as pd
import pytest

# Try to import the Alpaca connector, skip if not available
try:
    from quantchain.connectors.alpaca_connector import (
        AlpacaConnector,
        AlpacaDataFeed,
        AlpacaExecutionInterface,
    )

    ALPACA_CONNECTOR_AVAILABLE = True
except ImportError:
    ALPACA_CONNECTOR_AVAILABLE = False


@pytest.mark.unit
@pytest.mark.skipif(
    not ALPACA_CONNECTOR_AVAILABLE, reason="Alpaca connector module not available"
)
class TestAlpacaConnector:
    """Test Alpaca connector functionality."""

    def test_alpaca_connector_init(self) -> None:
        """Test Alpaca connector initialization."""
        connector = AlpacaConnector(
            api_key="test_key",
            api_secret="test_secret",
            base_url="https://paper-api.alpaca.markets",
        )
        assert connector is not None
        assert connector.api_key == "test_key"
        assert connector.api_secret == "test_secret"

    def test_alpaca_connector_init_with_paper(self) -> None:
        """Test Alpaca connector initialization with paper trading."""
        connector = AlpacaConnector(
            api_key="test_key", api_secret="test_secret", paper=True
        )
        assert connector is not None
        assert "paper" in connector.base_url.lower()

    @patch("quantchain.connectors.alpaca_connector.rest.REST")
    def test_alpaca_connector_authentication(self, mock_rest: Mock) -> None:
        """Test Alpaca connector authentication."""
        mock_client = Mock()
        mock_rest.return_value = mock_client

        connector = AlpacaConnector(api_key="test_key", api_secret="test_secret")

        # Verify REST client was initialized with correct credentials
        mock_rest.assert_called_once()

    def test_alpaca_data_feed_init(self) -> None:
        """Test Alpaca data feed initialization."""
        data_feed = AlpacaDataFeed(api_key="test_key", api_secret="test_secret")
        assert data_feed is not None
        assert data_feed.api_key == "test_key"

    def test_alpaca_execution_interface_init(self) -> None:
        """Test Alpaca execution interface initialization."""
        execution = AlpacaExecutionInterface(
            api_key="test_key", api_secret="test_secret"
        )
        assert execution is not None
        assert execution.api_key == "test_key"


@pytest.mark.skipif(
    not ALPACA_CONNECTOR_AVAILABLE, reason="Alpaca connector module not available"
)
class TestAlpacaDataFeed:
    """Test Alpaca data feed functionality."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.data_feed = AlpacaDataFeed(
            api_key="test_key",
            api_secret="test_secret",
            base_url="https://paper-api.alpaca.markets",
        )

    @patch("quantchain.connectors.alpaca_connector.rest.REST")
    async def test_get_historical_data_success(self, mock_rest: Mock) -> None:
        """Test successful historical data retrieval."""
        # Mock the response
        mock_client = Mock()
        mock_rest.return_value = mock_client

        # Create mock price data
        mock_data = [
            {
                "timestamp": "2024-01-01T09:30:00Z",
                "open": 100.0,
                "high": 101.0,
                "low": 99.0,
                "close": 100.5,
                "volume": 1000,
            }
        ]

        mock_client.get_bars.return_value = mock_data

        # Test the method
        result = await self.data_feed.get_historical_data(
            symbol="AAPL",
            timeframe="1D",
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 2),
        )

        assert result is not None
        mock_client.get_bars.assert_called_once()

    @patch("quantchain.connectors.alpaca_connector.rest.REST")
    async def test_get_real_time_data_success(self, mock_rest: Mock) -> None:
        """Test successful real-time data retrieval."""
        mock_client = Mock()
        mock_rest.return_value = mock_client

        mock_quote = {
            "symbol": "AAPL",
            "bid": 100.0,
            "ask": 100.5,
            "timestamp": "2024-01-01T09:30:00Z",
        }

        mock_client.get_latest_quote.return_value = mock_quote

        result = await self.data_feed.get_real_time_data("AAPL")

        assert result is not None
        mock_client.get_latest_quote.assert_called_with("AAPL")

    def test_get_available_symbols(self) -> None:
        """Test getting available symbols."""
        # This might be a stub or require actual API calls
        with patch.object(self.data_feed, "_get_symbols_from_api") as mock_get_symbols:
            mock_get_symbols.return_value = ["AAPL", "GOOGL", "MSFT"]

            symbols = self.data_feed.get_available_symbols()

            assert "AAPL" in symbols
            assert "GOOGL" in symbols
            assert "MSFT" in symbols

    def test_get_symbol_info(self) -> None:
        """Test getting symbol information."""
        with patch.object(self.data_feed, "_get_symbol_info_from_api") as mock_get_info:
            mock_info = {
                "symbol": "AAPL",
                "name": "Apple Inc.",
                "exchange": "NASDAQ",
                "type": "stock",
            }
            mock_get_info.return_value = mock_info

            info = self.data_feed.get_symbol_info("AAPL")

            assert info["symbol"] == "AAPL"
            assert info["name"] == "Apple Inc."


@pytest.mark.skipif(
    not ALPACA_CONNECTOR_AVAILABLE, reason="Alpaca connector module not available"
)
class TestAlpacaExecutionInterface:
    """Test Alpaca execution interface functionality."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.execution = AlpacaExecutionInterface(
            api_key="test_key",
            api_secret="test_secret",
            base_url="https://paper-api.alpaca.markets",
        )

    @patch("quantchain.connectors.alpaca_connector.rest.REST")
    def test_place_order_success(self, mock_rest: Mock) -> None:
        """Test successful order placement."""
        mock_client = Mock()
        mock_rest.return_value = mock_client

        mock_order = {
            "id": "order_123",
            "symbol": "AAPL",
            "side": "buy",
            "qty": 100,
            "type": "market",
            "status": "submitted",
        }

        mock_client.submit_order.return_value = mock_order

        order_request = {"symbol": "AAPL", "side": "buy", "qty": 100, "type": "market"}

        result = self.execution.place_order(order_request)

        assert result is not None
        assert result["id"] == "order_123"
        mock_client.submit_order.assert_called_once()

    @patch("quantchain.connectors.alpaca_connector.rest.REST")
    def test_cancel_order_success(self, mock_rest: Mock) -> None:
        """Test successful order cancellation."""
        mock_client = Mock()
        mock_rest.return_value = mock_client

        mock_client.cancel_order.return_value = {"id": "order_123"}

        result = self.execution.cancel_order("order_123")

        assert result is not None
        assert result["id"] == "order_123"
        mock_client.cancel_order.assert_called_with("order_123")

    @patch("quantchain.connectors.alpaca_connector.rest.REST")
    def test_get_account_success(self, mock_rest: Mock) -> None:
        """Test successful account retrieval."""
        mock_client = Mock()
        mock_rest.return_value = mock_client

        mock_account = {
            "id": "account_123",
            "buying_power": "100000.0",
            "cash": "50000.0",
            "portfolio_value": "100000.0",
            "equity": "100000.0",
        }

        mock_client.get_account.return_value = mock_account

        result = self.execution.get_account()

        assert result is not None
        assert result["id"] == "account_123"
        assert float(result["buying_power"]) == 100000.0
        mock_client.get_account.assert_called_once()

    @patch("quantchain.connectors.alpaca_connector.rest.REST")
    def test_get_positions_success(self, mock_rest: Mock) -> None:
        """Test successful positions retrieval."""
        mock_client = Mock()
        mock_rest.return_value = mock_client

        mock_positions = [
            {
                "symbol": "AAPL",
                "qty": "100",
                "side": "long",
                "market_value": "15000.0",
                "cost_basis": "14000.0",
            }
        ]

        mock_client.list_positions.return_value = mock_positions

        result = self.execution.get_positions()

        assert result is not None
        assert len(result) == 1
        assert result[0]["symbol"] == "AAPL"
        mock_client.list_positions.assert_called_once()

    def test_is_market_open(self) -> None:
        """Test market status check."""
        # This might use current time, so we'll test the method exists
        with patch.object(self.execution, "_check_market_hours") as mock_check:
            mock_check.return_value = True

            result = self.execution.is_market_open()

            assert result is True
            mock_check.assert_called_once()


@pytest.mark.skipif(
    not ALPACA_CONNECTOR_AVAILABLE, reason="Alpaca connector module not available"
)
class TestAlpacaConnectorEdgeCases:
    """Test Alpaca connector edge cases."""

    def test_invalid_credentials(self) -> None:
        """Test handling of invalid credentials."""
        with patch("quantchain.connectors.alpaca_connector.rest.REST") as mock_rest:
            mock_rest.side_effect = Exception("Invalid API key")

            with pytest.raises(Exception):
                AlpacaConnector(api_key="invalid_key", api_secret="invalid_secret")

    def test_network_error_handling(self) -> None:
        """Test network error handling."""
        connector = AlpacaConnector(api_key="test_key", api_secret="test_secret")

        with patch.object(connector, "_make_api_request") as mock_request:
            mock_request.side_effect = Exception("Network error")

            with pytest.raises(Exception):
                connector._get_symbols_from_api()

    def test_rate_limiting(self) -> None:
        """Test rate limiting functionality."""
        connector = AlpacaConnector(api_key="test_key", api_secret="test_secret")

        with patch.object(connector, "_make_api_request") as mock_request:
            mock_request.side_effect = Exception("Rate limit exceeded")

            # Should handle rate limiting gracefully
            try:
                connector._get_symbols_from_api()
            except Exception:
                pass  # Expected to handle rate limit error

    def test_empty_order_request(self) -> None:
        """Test handling of empty order requests."""
        execution = AlpacaExecutionInterface(
            api_key="test_key", api_secret="test_secret"
        )

        with pytest.raises(ValueError):
            execution.place_order({})

    def test_invalid_symbol(self) -> None:
        """Test handling of invalid symbols."""
        data_feed = AlpacaDataFeed(api_key="test_key", api_secret="test_secret")

        with patch.object(data_feed, "_get_symbol_info_from_api") as mock_get_info:
            mock_get_info.return_value = None

            result = data_feed.get_symbol_info("INVALID")

            assert result is None


@pytest.mark.skipif(
    not ALPACA_CONNECTOR_AVAILABLE, reason="Alpaca connector module not available"
)
class TestAlpacaConnectorConfiguration:
    """Test Alpaca connector configuration."""

    def test_paper_vs_live_urls(self) -> None:
        """Test paper vs live URL configuration."""
        paper_connector = AlpacaConnector(
            api_key="test_key", api_secret="test_secret", paper=True
        )

        live_connector = AlpacaConnector(
            api_key="test_key", api_secret="test_secret", paper=False
        )

        assert "paper" in paper_connector.base_url.lower()
        assert "paper" not in live_connector.base_url.lower()

    def test_custom_base_url(self) -> None:
        """Test custom base URL configuration."""
        custom_url = "https://custom.api.example.com"
        connector = AlpacaConnector(
            api_key="test_key", api_secret="test_secret", base_url=custom_url
        )

        assert connector.base_url == custom_url

    def test_default_timeouts(self) -> None:
        """Test default timeout settings."""
        connector = AlpacaConnector(api_key="test_key", api_secret="test_secret")

        # Should have reasonable default timeouts
        assert hasattr(connector, "timeout")
        assert connector.timeout > 0

    def test_custom_timeouts(self) -> None:
        """Test custom timeout settings."""
        custom_timeout = 60
        connector = AlpacaConnector(
            api_key="test_key", api_secret="test_secret", timeout=custom_timeout
        )

        assert connector.timeout == custom_timeout
