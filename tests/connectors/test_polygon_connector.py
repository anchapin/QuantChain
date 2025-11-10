"""Tests for Polygon.io data connector."""

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from quantchain.connectors.polygon_connector import PolygonDataConnector
from quantchain.core.exceptions import (
    AuthenticationError,
    DataSourceError,
    RateLimitError,
    SymbolNotFoundError,
)


@pytest.mark.unit
class TestPolygonDataConnector:
    """Test suite for PolygonDataConnector."""

    @pytest.fixture
    def connector(self) -> PolygonDataConnector:
        """Create a test connector instance."""
        return PolygonDataConnector("MOCK_API_KEY_FOR_TESTS")

    @pytest.fixture
    def sample_equity_bar(self) -> MagicMock:
        """Sample equity bar data."""
        bar = MagicMock()
        bar.timestamp = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        bar.open = 150.0
        bar.high = 155.0
        bar.low = 149.0
        bar.close = 153.0
        bar.volume = 1000000
        bar.vwap = 152.5
        return bar

    @pytest.fixture
    def sample_forex_bar(self) -> MagicMock:
        """Sample forex bar data."""
        bar = MagicMock()
        bar.timestamp = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        bar.open = 1.0850
        bar.high = 1.0860
        bar.low = 1.0840
        bar.close = 1.0855
        bar.volume = 100000
        bar.vwap = 1.0852
        return bar

    @pytest.fixture
    def sample_trade(self) -> MagicMock:
        """Sample trade data."""
        trade = MagicMock()
        trade.price = 153.25
        trade.size = 100
        trade.timestamp = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        return trade

    @pytest.fixture
    def sample_quote(self) -> MagicMock:
        """Sample quote data."""
        quote = MagicMock()
        quote.bid_price = 152.75
        quote.ask_price = 153.25
        quote.bid_size = 200
        quote.ask_size = 300
        quote.timestamp = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        return quote

    @pytest.fixture
    def sample_ticker(self) -> MagicMock:
        """Sample ticker data."""
        ticker = MagicMock()
        ticker.ticker = "AAPL"
        ticker.name = "Apple Inc."
        ticker.market = "stocks"
        ticker.currency_name = "USD"
        ticker.primary_exchange = "NASDAQ"
        return ticker

    def test_initialization_success(self) -> None:
        """Test successful initialization."""
        with patch("quantchain.connectors.polygon_connector.RESTClient") as mock_client:
            connector = PolygonDataConnector("MOCK_API_KEY")
            assert connector.api_key == "MOCK_API_KEY"
            assert connector.adjusted is True
            assert connector.cache_ttl == 3600
            assert connector.limit == 5000
            mock_client.assert_called_once_with(api_key="MOCK_API_KEY")

    def test_initialization_auth_failure(self) -> None:
        """Test initialization failure due to auth error."""
        with patch(
            "quantchain.connectors.polygon_connector.RESTClient",
            side_effect=Exception("Invalid API key"),
        ):
            with pytest.raises(AuthenticationError):
                PolygonDataConnector("BAD_MOCK_KEY")

    def test_is_forex_symbol(self, connector: PolygonDataConnector) -> None:
        """Test forex symbol detection."""
        assert connector._is_forex_symbol("C:EURUSD") is True
        assert connector._is_forex_symbol("C:GBPJPY") is True
        assert (
            connector._is_forex_symbol("EUR/USD") is False
        )  # EUR/USD is not a Polygon forex format
        assert connector._is_forex_symbol("AAPL") is False

    def test_normalize_forex_symbol(self, connector: PolygonDataConnector) -> None:
        """Test forex symbol normalization."""
        assert connector._normalize_forex_symbol("C:EURUSD") == "C:EURUSD"
        assert connector._normalize_forex_symbol("EUR/USD") == "C:EURUSD"
        assert connector._normalize_forex_symbol("EURUSD") == "C:EURUSD"

    def test_convert_timeframe(self, connector: PolygonDataConnector) -> None:
        """Test timeframe conversion."""
        assert connector._convert_timeframe("1Min") == (1, "minute")
        assert connector._convert_timeframe("5Min") == (5, "minute")
        assert connector._convert_timeframe("1H") == (1, "hour")
        assert connector._convert_timeframe("1D") == (1, "day")
        assert connector._convert_timeframe("1W") == (1, "week")
        assert connector._convert_timeframe("1M") == (1, "month")

        with pytest.raises(ValueError):
            connector._convert_timeframe("invalid")

    def test_get_historical_data_equity(
        self, connector: PolygonDataConnector, sample_equity_bar: MagicMock
    ) -> None:
        """Test historical data retrieval for equities."""
        start_date = datetime(2024, 1, 1, tzinfo=timezone.utc)
        end_date = datetime(2024, 1, 2, tzinfo=timezone.utc)

        with patch.object(connector.client, "list_aggs") as mock_list_aggs:
            mock_list_aggs.return_value: list[float] = [sample_equity_bar]

            df = connector.get_historical_data("AAPL", "1D", start_date, end_date)

            assert isinstance(df, pd.DataFrame)
            assert len(df) == 1
            assert df.iloc[0]["close"] == 153.0
            assert df.iloc[0]["volume"] == 1000000
            mock_list_aggs.assert_called_once()

    def test_get_historical_data_forex(
        self, connector: PolygonDataConnector, sample_forex_bar: MagicMock
    ) -> None:
        """Test historical data retrieval for forex."""
        start_date = datetime(2024, 1, 1, tzinfo=timezone.utc)
        end_date = datetime(2024, 1, 2, tzinfo=timezone.utc)

        with patch.object(connector.client, "list_aggs") as mock_list_aggs:
            mock_list_aggs.return_value: list[float] = [sample_forex_bar]

            df = connector.get_historical_data("C:EURUSD", "1H", start_date, end_date)

            assert isinstance(df, pd.DataFrame)
            assert len(df) == 1
            assert df.iloc[0]["close"] == 1.0855
            mock_list_aggs.assert_called_once()

    def test_get_historical_data_symbol_not_found(
        self, connector: PolygonDataConnector
    ) -> None:
        """Test historical data retrieval for non-existent symbol."""
        start_date = datetime(2024, 1, 1, tzinfo=timezone.utc)
        end_date = datetime(2024, 1, 2, tzinfo=timezone.utc)

        with patch.object(connector.client, "list_aggs") as mock_list_aggs:
            mock_list_aggs.return_value: list[float] = []

            with pytest.raises(SymbolNotFoundError):
                connector.get_historical_data("INVALID", "1D", start_date, end_date)

    def test_get_historical_data_invalid_timeframe(
        self, connector: PolygonDataConnector
    ) -> None:
        """Test historical data retrieval with invalid timeframe."""
        start_date = datetime(2024, 1, 1, tzinfo=timezone.utc)

        with pytest.raises(ValueError):
            connector.get_historical_data("AAPL", "invalid", start_date)

    def test_get_historical_data_rate_limit(
        self, connector: PolygonDataConnector
    ) -> None:
        """Test rate limit handling."""
        start_date = datetime(2024, 1, 1, tzinfo=timezone.utc)
        end_date = datetime(2024, 1, 2, tzinfo=timezone.utc)

        with patch.object(connector.client, "list_aggs") as mock_list_aggs:
            mock_list_aggs.side_effect = Exception("429 - Rate limit exceeded")

            with pytest.raises(RateLimitError):
                connector.get_historical_data("AAPL", "1D", start_date, end_date)

    def test_get_real_time_data_equity(
        self,
        connector: PolygonDataConnector,
        sample_trade: MagicMock,
        sample_quote: MagicMock,
    ) -> None:
        """Test real-time data retrieval for equities."""
        with patch.object(
            connector.client, "get_last_trade"
        ) as mock_trade, patch.object(connector.client, "get_last_quote") as mock_quote:
            mock_trade.return_value = sample_trade
            mock_quote.return_value = sample_quote

            data = connector.get_real_time_data("AAPL")

            assert isinstance(data, dict)
            assert "timestamp" in data
            assert "price" in data
            assert "bid" in data
            assert "ask" in data
            assert data["price"] == 153.25

    def test_get_real_time_data_forex(self, connector: PolygonDataConnector) -> None:
        """Test real-time data retrieval for forex."""
        mock_forex_quote = MagicMock()
        mock_forex_quote.bid = 1.0850
        mock_forex_quote.ask = 1.0860
        mock_forex_quote.timestamp = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

        with patch.object(
            connector.client, "get_real_time_currency_conversion"
        ) as mock_fx:
            mock_fx.return_value = mock_forex_quote

            data = connector.get_real_time_data("C:EURUSD")

            assert isinstance(data, dict)
            assert "timestamp" in data
            assert "bid" in data
            assert "ask" in data
            assert data["bid"] == 1.0850

    def test_get_real_time_data_missing_symbol(
        self, connector: PolygonDataConnector
    ) -> None:
        """Test real-time data retrieval for missing symbol."""
        with patch.object(connector.client, "get_last_trade") as mock_trade:
            mock_trade.side_effect = Exception("Not found")

            with pytest.raises(SymbolNotFoundError):
                connector.get_real_time_data("INVALID")

    def test_get_quote_equity(
        self, connector: PolygonDataConnector, sample_quote: MagicMock
    ) -> None:
        """Test quote retrieval for equities."""
        with patch.object(connector.client, "get_last_quote") as mock_quote:
            mock_quote.return_value = sample_quote

            quote = connector.get_quote("AAPL")

            assert isinstance(quote, dict)
            assert quote["symbol"] == "AAPL"
            assert "bid_price" in quote
            assert "ask_price" in quote
            assert quote["bid_price"] == 152.75
            assert quote["ask_price"] == 153.25

    def test_get_quote_forex(self, connector: PolygonDataConnector) -> None:
        """Test quote retrieval for forex."""
        mock_forex_quote = MagicMock()
        mock_forex_quote.bid = 1.0850
        mock_forex_quote.ask = 1.0860
        mock_forex_quote.timestamp = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

        with patch.object(
            connector.client, "get_real_time_currency_conversion"
        ) as mock_fx:
            mock_fx.return_value = mock_forex_quote

            quote = connector.get_quote("C:EURUSD")

            assert isinstance(quote, dict)
            assert quote["symbol"] == "C:EURUSD"
            assert quote["bid_price"] == 1.0850
            assert quote["ask_price"] == 1.0860

    def test_get_quote_missing_symbol(self, connector: PolygonDataConnector) -> None:
        """Test quote retrieval for missing symbol."""
        with patch.object(connector.client, "get_last_quote") as mock_quote:
            mock_quote.side_effect = Exception("Not found")

            with pytest.raises(SymbolNotFoundError):
                connector.get_quote("INVALID")

    def test_get_available_symbols_all(
        self, connector: PolygonDataConnector, sample_ticker: MagicMock
    ) -> None:
        """Test getting all available symbols."""
        with patch.object(connector, "_refresh_symbol_cache"):
            connector._symbol_cache = {"AAPL": sample_ticker}

            symbols = connector.get_available_symbols()

            assert isinstance(symbols, list)
            assert "AAPL" in symbols

    def test_get_available_symbols_equity_filter(
        self, connector: PolygonDataConnector, sample_ticker: MagicMock
    ) -> None:
        """Test getting symbols with equity filter."""
        sample_ticker.market = "stocks"

        with patch.object(connector, "_refresh_symbol_cache"):
            # Set cache after mocking _refresh_symbol_cache to prevent it from
            # being cleared
            connector._symbol_cache = {"AAPL": sample_ticker}

            symbols = connector.get_available_symbols("equity")

            assert isinstance(symbols, list)
            assert "AAPL" in symbols

    def test_get_available_symbols_forex_filter(
        self, connector: PolygonDataConnector
    ) -> None:
        """Test getting symbols with forex filter."""
        forex_ticker = MagicMock()
        forex_ticker.market = "fx"
        forex_ticker.ticker = "C:EURUSD"

        with patch.object(connector, "_refresh_symbol_cache"):
            # Set cache after mocking _refresh_symbol_cache to prevent it from
            # being cleared
            connector._symbol_cache = {"C:EURUSD": forex_ticker}

            symbols = connector.get_available_symbols("forex")

            assert isinstance(symbols, list)
            assert "C:EURUSD" in symbols

    def test_get_available_symbols_with_limit(
        self, connector: PolygonDataConnector, sample_ticker: MagicMock
    ) -> None:
        """Test getting symbols with limit."""
        with patch.object(connector, "_refresh_symbol_cache"):
            connector._symbol_cache = {"AAPL": sample_ticker, "GOOGL": sample_ticker}

            symbols = connector.get_available_symbols(limit=1)

            assert isinstance(symbols, list)
            assert len(symbols) <= 1

    def test_get_symbol_info_equity(
        self, connector: PolygonDataConnector, sample_ticker: MagicMock
    ) -> None:
        """Test getting symbol info for equity."""
        with patch.object(connector, "_refresh_symbol_cache"):
            connector._symbol_cache = {"AAPL": sample_ticker}

            info = connector.get_symbol_info("AAPL")

            assert isinstance(info, dict)
            assert info["symbol"] == "AAPL"
            assert info["name"] == "Apple Inc."
            assert info["market"] == "equity"

    def test_get_symbol_info_forex(self, connector: PolygonDataConnector) -> None:
        """Test getting symbol info for forex."""
        forex_ticker = MagicMock()
        forex_ticker.ticker = "C:EURUSD"
        forex_ticker.name = "EUR/USD"
        forex_ticker.market = "fx"
        forex_ticker.currency_name = "USD"

        with patch.object(connector, "_refresh_symbol_cache"):
            connector._symbol_cache = {"C:EURUSD": forex_ticker}

            info = connector.get_symbol_info("C:EURUSD")

            assert isinstance(info, dict)
            assert info["symbol"] == "C:EURUSD"
            assert info["market"] == "forex"

    def test_get_symbol_info_not_found(self, connector: PolygonDataConnector) -> None:
        """Test getting symbol info for non-existent symbol."""
        with patch.object(connector, "_refresh_symbol_cache"):
            connector._symbol_cache = {}
            connector._skip_api_calls_for_tests = True  # Skip API call for this test

            with pytest.raises(SymbolNotFoundError):
                connector.get_symbol_info("INVALID")

    def test_get_symbol_info_cache_hit(
        self, connector: PolygonDataConnector, sample_ticker: MagicMock
    ) -> None:
        """Test symbol info cache hit."""
        connector._skip_api_calls_for_tests = True  # Skip API calls for this test

        with patch.object(connector, "_refresh_symbol_cache"):
            # Set cache after mocking _refresh_symbol_cache to prevent it from
            # being cleared
            connector._symbol_cache = {"AAPL": sample_ticker}

            # First call should use cache
            info1 = connector.get_symbol_info("AAPL")
            assert info1["symbol"] == "AAPL"

            # Second call should also use cache without refreshing
            info2 = connector.get_symbol_info("AAPL")
            assert info2["symbol"] == "AAPL"

    def test_is_market_open_true(self, connector: PolygonDataConnector) -> None:
        """Test market status when open."""
        mock_status = MagicMock()
        mock_status.market = "open"

        with patch.object(connector.client, "get_market_status") as mock_get_status:
            mock_get_status.return_value = mock_status

            is_open = connector.is_market_open()

            assert is_open is True

    def test_is_market_open_false(self, connector: PolygonDataConnector) -> None:
        """Test market status when closed."""
        mock_status = MagicMock()
        mock_status.market = "closed"

        with patch.object(connector.client, "get_market_status") as mock_get_status:
            mock_get_status.return_value = mock_status

            is_open = connector.is_market_open()

            assert is_open is False

    def test_is_market_open_forex(self, connector: PolygonDataConnector) -> None:
        """Test forex market status (always open)."""
        is_open = connector.is_market_open("forex")
        assert is_open is True

    def test_is_market_open_error(self, connector: PolygonDataConnector) -> None:
        """Test market status with API error."""
        with patch.object(connector.client, "get_market_status") as mock_get_status:
            mock_get_status.side_effect = Exception("API Error")

            with pytest.raises(DataSourceError):
                connector.is_market_open()

    def test_refresh_symbol_cache(
        self, connector: PolygonDataConnector, sample_ticker: MagicMock
    ) -> None:
        """Test symbol cache refresh."""
        with patch.object(connector.client, "list_tickers") as mock_list_tickers:
            mock_list_tickers.return_value: list[float] = [sample_ticker]

            connector._refresh_symbol_cache()

            assert "AAPL" in connector._symbol_cache

    def test_cache_expiration(
        self, connector: PolygonDataConnector, sample_ticker: MagicMock
    ) -> None:
        """Test cache expiration."""
        # Set cache timestamp to past
        import time

        connector._cache_timestamp = time.time() - 7200  # 2 hours ago

        with patch.object(connector.client, "list_tickers") as mock_list_tickers:
            mock_list_tickers.return_value: list[float] = [sample_ticker]

            connector._refresh_symbol_cache()

            # Should be called twice: once for stocks, once for fx
            assert mock_list_tickers.call_count == 2
            mock_list_tickers.assert_any_call(market="stocks", active=True)
            mock_list_tickers.assert_any_call(market="fx", active=True)

    def test_invalidate_cache(self, connector: PolygonDataConnector) -> None:
        """Test cache invalidation."""
        connector._symbol_cache = {"AAPL": "data"}
        connector._cache_timestamp = 123456789

        connector.invalidate_cache()

        assert len(connector._symbol_cache) == 0
        assert connector._cache_timestamp is None

    def test_authentication_error_handling(self) -> None:
        """Test authentication error handling during init."""
        with patch(
            "quantchain.connectors.polygon_connector.RESTClient",
            side_effect=Exception("Authentication failed"),
        ):
            with pytest.raises(AuthenticationError):
                PolygonDataConnector("INVALID_MOCK_KEY")

    def test_rate_limit_detection(self, connector: PolygonDataConnector) -> None:
        """Test rate limit detection."""
        with patch.object(connector.client, "list_aggs") as mock_list_aggs:
            # Test various rate limit error messages
            error_messages = [
                "429 - Rate limit exceeded",
                "Too many requests",
                "Rate limit exceeded",
            ]

            for error_msg in error_messages:
                mock_list_aggs.side_effect = Exception(error_msg)
                start_date = datetime(2024, 1, 1, tzinfo=timezone.utc)

                with pytest.raises(RateLimitError):
                    connector.get_historical_data("AAPL", "1D", start_date)

    def test_network_error_handling(self, connector: PolygonDataConnector) -> None:
        """Test network error handling."""
        with patch.object(connector.client, "list_aggs") as mock_list_aggs:
            mock_list_aggs.side_effect = Exception("Network timeout")

            start_date = datetime(2024, 1, 1, tzinfo=timezone.utc)

            with pytest.raises(DataSourceError):
                connector.get_historical_data("AAPL", "1D", start_date)

    def test_invalid_response_handling(self, connector: PolygonDataConnector) -> None:
        """Test invalid response handling."""
        with patch.object(connector.client, "list_aggs") as mock_list_aggs:
            # Return an object without expected attributes
            invalid_bar = MagicMock()
            del invalid_bar.timestamp  # Remove required attribute

            mock_list_aggs.return_value: list[float] = [invalid_bar]

            start_date = datetime(2024, 1, 1, tzinfo=timezone.utc)

            # Should handle the error gracefully
            with pytest.raises(DataSourceError):
                connector.get_historical_data("AAPL", "1D", start_date)

    def test_custom_cache_ttl(self) -> None:
        """Test custom cache TTL configuration."""
        with patch("quantchain.connectors.polygon_connector.RESTClient"):
            connector = PolygonDataConnector("MOCK_API_KEY", cache_ttl=1800)
            assert connector.cache_ttl == 1800

    def test_custom_adjusted_flag(self) -> None:
        """Test custom adjusted flag configuration."""
        with patch("quantchain.connectors.polygon_connector.RESTClient"):
            connector = PolygonDataConnector("MOCK_API_KEY", adjusted=False)
            assert connector.adjusted is False

    def test_custom_limit(self) -> None:
        """Test custom limit configuration."""
        with patch("quantchain.connectors.polygon_connector.RESTClient"):
            connector = PolygonDataConnector("MOCK_API_KEY", limit=1000)
            assert connector.limit == 1000
